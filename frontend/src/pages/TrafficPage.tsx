import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Network, 
  Play, 
  Pause, 
  Square, 
  Filter, 
  Download, 
  Search,
  Eye,
  AlertCircle,
  Clock,
  Globe,
  Shield,
  Activity,
  ChevronDown,
  ChevronRight,
  Wifi,
  Server,
  Database
} from 'lucide-react';

interface PacketInfo {
  id: number;
  timestamp: string;
  src_ip: string;
  dst_ip: string;
  src_port?: number;
  dst_port?: number;
  protocol: string;
  length: number;
  info: string;
  flags?: string[];
  payload_preview?: string;
  severity: 'info' | 'warning' | 'danger';
}

const TrafficPage: React.FC = () => {
  const [packets, setPackets] = useState<PacketInfo[]>([]);
  const [filteredPackets, setFilteredPackets] = useState<PacketInfo[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [selectedPacket, setSelectedPacket] = useState<PacketInfo | null>(null);
  const [filters, setFilters] = useState({
    protocol: '',
    srcIp: '',
    dstIp: '',
    port: '',
    search: ''
  });
  const [stats, setStats] = useState({
    totalPackets: 0,
    tcpPackets: 0,
    udpPackets: 0,
    httpPackets: 0,
    dnsPackets: 0,
    bytesTotal: 0
  });
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const packetsStartRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Загрузка реальных пакетов из API
  const loadPackets = useCallback(async () => {
    try {
      const response = await fetch('/api/traffic/packets?limit=100');
      const data = await response.json();
      
      if (data.packets && Array.isArray(data.packets)) {
        const packetInfos: PacketInfo[] = data.packets.map((packet: any) => ({
          id: packet.id || Date.now() + Math.random(),
          timestamp: packet.timestamp || new Date().toISOString(),
          src_ip: packet.src_ip || 'unknown',
          dst_ip: packet.dst_ip || 'unknown',
          src_port: packet.src_port || 0,
          dst_port: packet.dst_port || 0,
          protocol: packet.protocol || 'unknown',
          length: packet.length || 0,
          info: packet.info || packet.details || 'No info',
          severity: packet.severity || 'info',
          flags: packet.flags || undefined,
          payload_preview: packet.payload_preview || ''
        }));
        setPackets(packetInfos);
        setFilteredPackets(packetInfos);
      }
    } catch (error) {
      console.error('Error loading packets:', error);
    }
  }, []);

  // Запуск/остановка захвата
  const toggleCapture = useCallback(async () => {
    if (isCapturing) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsCapturing(false);
      // Остановить захват на backend
      try {
        await fetch('/api/traffic/capture/stop', { method: 'POST' });
      } catch (error) {
        console.error('Error stopping capture:', error);
      }
    } else {
      setIsCapturing(true);
      // Запустить захват на backend
      try {
        await fetch('/api/traffic/capture/start', { method: 'POST' });
      } catch (error) {
        console.error('Error starting capture:', error);
      }
      
      // Периодически загружать новые пакеты
      intervalRef.current = setInterval(async () => {
        await loadPackets();
      }, 2000); // Загружаем каждые 2 секунды
    }
  }, [isCapturing, loadPackets]);

  // Очистка пакетов
  const clearPackets = useCallback(() => {
    setPackets([]);
    setFilteredPackets([]);
    setSelectedPacket(null);
    setStats({
      totalPackets: 0,
      tcpPackets: 0,
      udpPackets: 0,
      httpPackets: 0,
      dnsPackets: 0,
      bytesTotal: 0
    });
  }, []);

  // Фильтрация пакетов
  useEffect(() => {
    let filtered = packets;

    if (filters.protocol) {
      filtered = filtered.filter(p => p.protocol.toLowerCase().includes(filters.protocol.toLowerCase()));
    }
    if (filters.srcIp) {
      filtered = filtered.filter(p => p.src_ip.includes(filters.srcIp));
    }
    if (filters.dstIp) {
      filtered = filtered.filter(p => p.dst_ip.includes(filters.dstIp));
    }
    if (filters.port) {
      filtered = filtered.filter(p => 
        p.src_port?.toString().includes(filters.port) || 
        p.dst_port?.toString().includes(filters.port)
      );
    }
    if (filters.search) {
      filtered = filtered.filter(p => 
        p.info.toLowerCase().includes(filters.search.toLowerCase()) ||
        p.src_ip.includes(filters.search) ||
        p.dst_ip.includes(filters.search)
      );
    }

    setFilteredPackets(filtered);
  }, [packets, filters]);

  // Обновление статистики
  useEffect(() => {
    const newStats = {
      totalPackets: packets.length,
      tcpPackets: packets.filter(p => p.protocol === 'TCP').length,
      udpPackets: packets.filter(p => p.protocol === 'UDP').length,
      httpPackets: packets.filter(p => p.protocol === 'HTTP' || p.protocol === 'HTTPS').length,
      dnsPackets: packets.filter(p => p.protocol === 'DNS').length,
      bytesTotal: packets.reduce((sum, p) => sum + p.length, 0)
    };
    setStats(newStats);
  }, [packets]);

  // Автопрокрутка к началу списка (к новым пакетам)
  useEffect(() => {
    if (autoScroll && packetsStartRef.current) {
      packetsStartRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [packets, autoScroll]);

  // Загрузка пакетов при монтировании
  useEffect(() => {
    loadPackets();
  }, [loadPackets]);

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'danger': return 'bg-red-50 border-l-4 border-red-500 text-red-900';
      case 'warning': return 'bg-yellow-50 border-l-4 border-yellow-500 text-yellow-900';
      default: return 'bg-white hover:bg-gray-50';
    }
  };

  const getProtocolColor = (protocol: string) => {
    switch (protocol) {
      case 'HTTP': return 'bg-green-100 text-green-800';
      case 'HTTPS': return 'bg-green-200 text-green-900';
      case 'TCP': return 'bg-blue-100 text-blue-800';
      case 'UDP': return 'bg-purple-100 text-purple-800';
      case 'DNS': return 'bg-orange-100 text-orange-800';
      case 'ICMP': return 'bg-gray-100 text-gray-800';
      case 'ARP': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center">
            <Network className="h-10 w-10 mr-4 text-blue-600" />
            Монитор трафика
            <span className="ml-4 text-sm font-normal text-gray-600">
              {isCapturing ? (
                <span className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  Захват активен
                </span>
              ) : (
                <span className="flex items-center text-gray-500">
                  <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                  Захват остановлен
                </span>
              )}
            </span>
          </h1>
          <p className="text-gray-600 text-lg">
            Мониторинг сетевого трафика в реальном времени • Анализ пакетов • Обнаружение угроз
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 mb-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Capture Controls */}
            <div className="flex items-center space-x-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleCapture}
                className={`flex items-center px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                  isCapturing 
                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg' 
                    : 'bg-green-500 hover:bg-green-600 text-white shadow-lg'
                }`}
              >
                {isCapturing ? (
                  <>
                    <Pause className="h-5 w-5 mr-2" />
                    Остановить
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    Начать захват
                  </>
                )}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={clearPackets}
                className="flex items-center px-4 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-xl font-semibold transition-all duration-300"
              >
                <Square className="h-5 w-5 mr-2" />
                Очистить
              </motion.button>
            </div>

            {/* Stats */}
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center">
                <Activity className="h-4 w-4 mr-1 text-blue-600" />
                <span className="font-semibold">{stats.totalPackets}</span>
                <span className="text-gray-600 ml-1">пакетов</span>
              </div>
              <div className="flex items-center">
                <Database className="h-4 w-4 mr-1 text-green-600" />
                <span className="font-semibold">{(stats.bytesTotal / 1024).toFixed(1)}</span>
                <span className="text-gray-600 ml-1">KB</span>
              </div>
              <div className="flex items-center">
                <Server className="h-4 w-4 mr-1 text-purple-600" />
                <span className="font-semibold">{stats.tcpPackets}</span>
                <span className="text-gray-600 ml-1">TCP</span>
              </div>
            </div>

            {/* Auto-scroll toggle */}
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="sr-only"
              />
              <div className={`relative w-11 h-6 bg-gray-200 rounded-full transition-colors ${autoScroll ? 'bg-blue-600' : ''}`}>
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${autoScroll ? 'translate-x-5' : ''}`}></div>
              </div>
              <span className="ml-3 text-sm font-medium text-gray-700">Автопрокрутка</span>
            </label>
          </div>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 mb-6"
        >
          <div className="flex items-center mb-4">
            <Filter className="h-5 w-5 mr-2 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Фильтры</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Протокол</label>
              <select
                value={filters.protocol}
                onChange={(e) => setFilters(prev => ({ ...prev, protocol: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все</option>
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="HTTP">HTTP</option>
                <option value="HTTPS">HTTPS</option>
                <option value="DNS">DNS</option>
                <option value="ICMP">ICMP</option>
                <option value="ARP">ARP</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">IP источника</label>
              <input
                type="text"
                value={filters.srcIp}
                onChange={(e) => setFilters(prev => ({ ...prev, srcIp: e.target.value }))}
                placeholder="192.168.1.100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">IP назначения</label>
              <input
                type="text"
                value={filters.dstIp}
                onChange={(e) => setFilters(prev => ({ ...prev, dstIp: e.target.value }))}
                placeholder="8.8.8.8"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Порт</label>
              <input
                type="text"
                value={filters.port}
                onChange={(e) => setFilters(prev => ({ ...prev, port: e.target.value }))}
                placeholder="80, 443"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Поиск</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  placeholder="Поиск по содержимому"
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Packets Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Packets List */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden"
            >
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900">
                  Пакеты ({filteredPackets.length})
                </h3>
              </div>
              
              <div className="overflow-auto max-h-96 custom-scrollbar">
                {filteredPackets.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <Network className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>Нет пакетов для отображения</p>
                    <p className="text-sm">Начните захват для мониторинга трафика</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    <div ref={packetsStartRef} />
                    {filteredPackets.map((packet, index) => (
                      <motion.div
                        key={packet.id}
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.01, duration: 0.3 }}
                        onClick={() => setSelectedPacket(packet)}
                        className={`p-4 cursor-pointer transition-all duration-200 ${getSeverityColor(packet.severity)} ${
                          selectedPacket?.id === packet.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 min-w-0 flex-1">
                            <div className="flex-shrink-0">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getProtocolColor(packet.protocol)}`}>
                                {packet.protocol}
                              </span>
                            </div>
                            
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center text-sm">
                                <span className="font-medium text-gray-900">{packet.src_ip}</span>
                                {packet.src_port && <span className="text-gray-600">:{packet.src_port}</span>}
                                <ChevronRight className="h-4 w-4 mx-2 text-gray-400" />
                                <span className="font-medium text-gray-900">{packet.dst_ip}</span>
                                {packet.dst_port && <span className="text-gray-600">:{packet.dst_port}</span>}
                              </div>
                              <div className="mt-1 text-sm text-gray-600 truncate">
                                {packet.info}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>{packet.length}B</span>
                            <span>{new Date(packet.timestamp).toLocaleTimeString('ru-RU')}</span>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Packet Details */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="bg-white rounded-2xl shadow-lg border border-gray-100"
            >
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Eye className="h-5 w-5 mr-2" />
                  Детали пакета
                </h3>
              </div>
              
              <div className="p-4">
                {selectedPacket ? (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Основная информация</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Время:</span>
                          <span className="font-mono">{new Date(selectedPacket.timestamp).toLocaleString('ru-RU')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Протокол:</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getProtocolColor(selectedPacket.protocol)}`}>
                            {selectedPacket.protocol}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Размер:</span>
                          <span className="font-mono">{selectedPacket.length} байт</span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Сетевая информация</h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-600">Источник:</span>
                          <div className="font-mono bg-gray-50 p-2 rounded mt-1">
                            {selectedPacket.src_ip}{selectedPacket.src_port && `:${selectedPacket.src_port}`}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Назначение:</span>
                          <div className="font-mono bg-gray-50 p-2 rounded mt-1">
                            {selectedPacket.dst_ip}{selectedPacket.dst_port && `:${selectedPacket.dst_port}`}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {selectedPacket.flags && selectedPacket.flags.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">TCP Флаги</h4>
                        <div className="flex flex-wrap gap-1">
                          {selectedPacket.flags.map((flag, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                              {flag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Описание</h4>
                      <div className="text-sm bg-gray-50 p-3 rounded font-mono">
                        {selectedPacket.info}
                      </div>
                    </div>
                    
                    {selectedPacket.payload_preview && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Превью данных</h4>
                        <div className="text-xs bg-gray-900 text-green-400 p-3 rounded font-mono">
                          {selectedPacket.payload_preview}
                        </div>
                      </div>
                    )}
                    
                    {selectedPacket.severity !== 'info' && (
                      <div className={`p-3 rounded-lg ${
                        selectedPacket.severity === 'danger' ? 'bg-red-50 border border-red-200' : 'bg-yellow-50 border border-yellow-200'
                      }`}>
                        <div className="flex items-center">
                          <AlertCircle className={`h-5 w-5 mr-2 ${
                            selectedPacket.severity === 'danger' ? 'text-red-600' : 'text-yellow-600'
                          }`} />
                          <span className={`font-semibold ${
                            selectedPacket.severity === 'danger' ? 'text-red-800' : 'text-yellow-800'
                          }`}>
                            {selectedPacket.severity === 'danger' ? 'Опасность' : 'Предупреждение'}
                          </span>
                        </div>
                        <p className={`mt-1 text-sm ${
                          selectedPacket.severity === 'danger' ? 'text-red-700' : 'text-yellow-700'
                        }`}>
                          {selectedPacket.severity === 'danger' 
                            ? 'Обнаружена подозрительная активность'
                            : 'Пакет требует внимания'
                          }
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Eye className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>Выберите пакет для просмотра деталей</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrafficPage;
