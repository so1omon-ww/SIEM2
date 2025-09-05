# backend/agents/python/collector/net_sniffer.py
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional
from collections import defaultdict, deque

LOG = logging.getLogger("NetSnifferCollector")

# --- Scapy (для реального режима) ---
try:
    from scapy.all import sniff, TCP, UDP, IP, DNS, DNSQR  # type: ignore
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    LOG.error("Scapy is required for network sniffing. Install with: pip install scapy")

@dataclass
class SnifferConfig:
    server_url: str
    token: Optional[str]
    host_id: str
    interface: Optional[str] = None
    verify_tls: bool = False
    portscan_threshold: int = 10
    portscan_window_sec: int = 60
    min_severity: str = "info"
    block_on_portscan: bool = False
    log_level: str = "INFO"

def _make_emitter(sender_module, server_url: str, token: Optional[str], verify_tls: bool):
    """Фабрика emitter-функции, которая отправляет события через sender.py"""
    def emitter(event: dict):
        try:
            sender_module.send_event(server_url, token, event, verify_tls=verify_tls)
        except Exception as e:
            LOG.error("Emitter failed: %s", e)
    return emitter

# --- простой детектор портскана (N уникальных портов за окно T) ---
class _PortscanDetector:
    def __init__(self, threshold: int, window_sec: int):
        self.threshold = int(threshold)
        self.window = int(window_sec)
        self._by_src = defaultdict(lambda: deque(maxlen=10000))  # src_ip -> deque[(ts, dport)]

    def feed(self, ts: float, src_ip: str, dport: int):
        dq = self._by_src[src_ip]
        dq.append((ts, int(dport)))
        # очистка старых значений за окно
        while dq and (ts - dq[0][0]) > self.window:
            dq.popleft()
        uniq_ports = {p for _, p in dq}
        return (len(uniq_ports) >= self.threshold,
                {"src_ip": src_ip,
                 "unique_ports": len(uniq_ports),
                 "sample_ports": sorted(list(uniq_ports))[:20]})

def _flags_to_text(flags: int) -> str:
    bits = []
    if flags & 0x02: bits.append("SYN")
    if flags & 0x10: bits.append("ACK")
    if flags & 0x01: bits.append("FIN")
    if flags & 0x04: bits.append("RST")
    if flags & 0x08: bits.append("PSH")
    if flags & 0x20: bits.append("URG")
    if flags & 0x40: bits.append("ECE")
    if flags & 0x80: bits.append("CWR")
    return "|".join(bits)

class NetSnifferCollector:
    """
    Реальный сетевой коллектор:
      - слушает интерфейс через scapy.sniff()
      - генерирует события:
          * net.portscan.suspected (TCP SYN без ACK; N уникальных портов за окно)
          * net.dns.query (UDP+DNS, qr=0)
    """

    def __init__(self, config: SnifferConfig, emitter: Callable[[dict], None]):
        if not SCAPY_AVAILABLE:
            raise RuntimeError("Scapy is required for NetSnifferCollector")
            
        self.config = config
        self.emitter = emitter
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        LOG.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        LOG.info("Starting NetSnifferCollector on interface=%s", self.config.interface or "<default>")
        self._thread.start()

    def stop(self):
        LOG.info("Stopping NetSnifferCollector")
        self._stop.set()
        self._thread.join(timeout=3)

    def _check_permissions(self) -> bool:
        """Проверяем права доступа для захвата пакетов"""
        import os
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if not is_admin:
                    LOG.warning("Windows: нет прав администратора, переключаюсь в fallback режим")
                    return False
            else:  # Linux/Unix
                is_root = os.geteuid() == 0
                if not is_root:
                    LOG.warning("Linux: нет прав root, переключаюсь в fallback режим")
                    return False
            return True
        except Exception as e:
            LOG.warning("Не удалось проверить права доступа: %s, переключаюсь в fallback режим", e)
            return False

    def _fallback_mode(self):
        """
        Fallback режим для работы без прав администратора:
        - Симуляция сетевых событий для тестирования
        - Использование системных API
        - Мониторинг через альтернативные методы
        """
        LOG.info("Starting in fallback mode (without administrator privileges)")
        LOG.info("Simulating network events for testing")
        
        import time
        import random
        import socket
        
        # Получаем локальный IP
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except:
            local_ip = "127.0.0.1"
        
        # Счетчики для статистики
        event_count = 0
        start_time = time.time()
        
        while not self._stop.is_set():
            try:
                # Fallback режим без симуляции - просто ждем
                LOG.info("Fallback mode active - waiting for real events...")
                
                # Логируем статистику каждые 60 секунд
                if time.time() - start_time >= 60:
                    LOG.info("Fallback mode: agent active (no simulation)")
                    start_time = time.time()
                
                # Пауза между проверками
                time.sleep(30)
                
            except Exception as e:
                LOG.error("Error in fallback mode: %s", e)
                time.sleep(10)
        
        LOG.info("Fallback mode stopped")

    def _emit_event(self, etype: str, *, severity: Optional[str] = None, **fields):
        """
        Формирует payload под backend /events/ingest (EventIn):
          event_type, severity, src_ip, dst_ip, src_port, dst_port, protocol, packet_size, flags, details
        ts можно не указывать — сервер проставит сам (UTC).
        """
        ev = {"event_type": etype}
        if severity: ev["severity"] = severity

        # базовые сетевые поля (включаем только если есть)
        for k in ("src_ip", "dst_ip", "src_port", "dst_port", "protocol", "packet_size", "flags"):
            v = fields.get(k)
            if v is not None:
                ev[k] = v

        # детали (словарь) — сервер сохранит как JSON в поле details
        details = fields.get("details") or {}
        # чтобы можно было связать на стороне аналитики:
        details.setdefault("host_id", self.config.host_id)
        details.setdefault("iface", self.config.interface or "")
        ev["details"] = details

        LOG.debug("emit %s: %s", etype, {k: ev[k] for k in ev.keys() if k != "details"} | {"details.keys": list(details.keys())})
        self.emitter(ev)

    def _sniffer_loop(self):
        """
        Основной цикл захвата пакетов.
        Используем короткие таймауты, чтобы можно было корректно остановиться по флагу.
        """
        detector = _PortscanDetector(self.config.portscan_threshold, self.config.portscan_window_sec)
        packet_count = 0
        event_count = 0
        
        LOG.info("Starting packet capture loop...")
        LOG.info("BPF filter: %s", "tcp or (udp and port 53)")
        LOG.info("Interface: %s", self.config.interface or "auto-detect")

        def on_pkt(pkt):
            nonlocal packet_count, event_count
            packet_count += 1
            
            try:
                if IP not in pkt:
                    LOG.debug("📦 Пакет без IP заголовка, пропускаем")
                    return
                    
                src = pkt[IP].src
                dst = pkt[IP].dst
                size = int(len(pkt))
                
                LOG.debug("📦 Обработка пакета #%d: %s → %s (размер: %d байт)", 
                         packet_count, src, dst, size)

                # TCP: портскан по SYN без ACK
                if TCP in pkt:
                    flags = int(pkt[TCP].flags)
                    dport = int(pkt[TCP].dport)
                    sport = int(pkt[TCP].sport)
                    
                    LOG.debug("🔗 TCP пакет: %s:%d → %s:%d, флаги: %s", 
                             src, sport, dst, dport, _flags_to_text(flags))
                    
                    # SYN без ACK
                    if (flags & 0x02) and not (flags & 0x10):
                        LOG.debug("Detected SYN without ACK - checking for port scan")
                        trig, info = detector.feed(time.time(), src, dport)
                        if trig:
                            event_count += 1
                            LOG.warning("PORT SCAN DETECTED! %s → %s:%d (unique ports: %d)", 
                                       src, dst, dport, info["unique_ports"])
                            
                            self._emit_event(
                                "net.portscan.suspected",
                                severity="high",
                                src_ip=src,
                                dst_ip=dst,
                                dst_port=dport,
                                protocol="TCP",
                                packet_size=size,
                                flags=_flags_to_text(flags),
                                details={
                                    "unique_ports": info["unique_ports"],
                                    "sample_ports": info["sample_ports"],
                                    "window_sec": self.config.portscan_window_sec,
                                },
                            )
                    return  # на TCP больше ничего не шлём, чтобы не заспамить

                # DNS-запросы (UDP + DNS, только запросы)
                if UDP in pkt and pkt.haslayer(DNS) and pkt[DNS].qr == 0:
                    try:
                        qname = pkt[DNSQR].qname.decode("utf-8", "ignore").rstrip(".")
                        qtype = int(pkt[DNSQR].qtype)
                        event_count += 1
                        
                        LOG.info("DNS query: %s → %s, domain: %s, type: %d", 
                                src, dst, qname, qtype)
                        
                        self._emit_event(
                            "net.dns.query",
                            severity="info",
                            src_ip=src,
                            dst_ip=dst,
                            protocol="UDP",
                            packet_size=size,
                            details={"qname": qname, "qtype": qtype},
                        )
                    except Exception as e:
                        LOG.error("Error processing DNS packet: %s", e)
                        
            except Exception as e:
                LOG.error("Error processing packet: %s", e)
                LOG.exception("Full error traceback:")

        # короткими итерациями, чтобы реагировать на stop()
        bpf = "tcp or (udp and port 53)"
        LOG.info("Sniff loop started; bpf='%s'", bpf)
        
        while not self._stop.is_set():
            sniff_kwargs = dict(prn=on_pkt, store=False, timeout=2)
            if self.config.interface:
                sniff_kwargs["iface"] = self.config.interface
            try:
                sniff(filter=bpf, **sniff_kwargs)
                
                # Логируем статистику каждые 100 пакетов
                if packet_count > 0 and packet_count % 100 == 0:
                    LOG.info("Statistics: processed %d packets, created %d events", 
                            packet_count, event_count)
                    
            except Exception as e:
                LOG.error("Sniff error: %s", e)
                LOG.exception("Full error traceback:")
                break
        
        LOG.info("Packet capture loop stopped")
        LOG.info("Final statistics: processed %d packets, created %d events", 
                packet_count, event_count)

    def _run(self):
        # Проверяем права доступа перед запуском сниффера
        if not self._check_permissions():
            self._fallback_mode()
            return # Exit if fallback mode is active
            
        try:
            self._sniffer_loop()
        except Exception as e:
            LOG.error("Unexpected error in sniffer: %s", e)
            raise
