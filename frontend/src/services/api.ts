import axios from 'axios';
import { Event, Alert, ApiResponse, AnalyzerStatus, LoginRequest, RegisterRequest, AuthResponse, ApiKey, ActionTypeInfo, ActionConfig, PendingAction, ActionHistory, ActiveBlock, AttackPattern, Recommendation } from '../types';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Интерцептор для автоматического добавления токена авторизации и API ключа
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Добавляем API ключ для всех запросов
    const apiKey = localStorage.getItem('api_key');
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// API для аутентификации
export const authApi = {
  // Регистрация пользователя
  register: async (data: RegisterRequest): Promise<{ ok: boolean; api_key?: string; message?: string }> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  // Вход в систему
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  // Получение API ключа пользователя
  getApiKey: async (username: string): Promise<ApiKey> => {
    const response = await api.get(`/auth/api-keys?username=${username}`);
    return response.data;
  },

  // Получение текущего API ключа (создает если нет)
  getCurrentApiKey: async (username: string): Promise<ApiKey> => {
    const response = await api.get(`/auth/api-keys/current?username=${username}`);
    return response.data;
  },

  // Генерация API ключа
  generateApiKey: async (username: string): Promise<ApiKey> => {
    const response = await api.post('/auth/api-keys', { username });
    return response.data;
  }
};

// API для событий
export const eventsApi = {
  // Получить последние события
  getRecentEvents: async (limit = 50): Promise<ApiResponse<Event>> => {
    const response = await api.get(`/events/recent?limit=${limit}`);
    return response.data;
  },

  // Получить событие по ID
  getEvent: async (id: number): Promise<Event> => {
    const response = await api.get(`/events/${id}`);
    return response.data;
  },

  // Отправить событие (для тестирования)
  sendEvent: async (event: Partial<Event>): Promise<{ ok: boolean; event_id: number }> => {
    const response = await api.post('/events/ingest', event);
    return response.data;
  },
};

// API для алертов
export const alertsApi = {
  // Получить последние алерты
  getRecentAlerts: async (limit = 50): Promise<ApiResponse<Alert>> => {
    const response = await api.get(`/alerts/recent?limit=${limit}`);
    return response.data;
  },

  // Получить алерт по ID
  getAlert: async (id: number): Promise<Alert> => {
    const response = await api.get(`/alerts/${id}`);
    return response.data;
  },

  // Подтвердить алерт
  acknowledgeAlert: async (id: number): Promise<{ ok: boolean }> => {
    const response = await api.post(`/alerts/${id}/acknowledge`);
    return response.data;
  },
};

// API для анализатора
export const analyzerApi = {
  // Получить статус анализатора
  getStatus: async (): Promise<AnalyzerStatus> => {
    const response = await api.get('/analyzer/status');
    return response.data;
  },

  // Перезагрузить правила
  reloadRules: async (): Promise<{ message: string }> => {
    const response = await api.post('/analyzer/rules/reload');
    return response.data;
  },

  // Получить список правил
  getRules: async (): Promise<{ total_rules: number; rules: any[] }> => {
    const response = await api.get('/analyzer/rules');
    return response.data;
  },
};

// API для сети и агентов
export const networkApi = {
  // Получить список агентов
  getAgents: async (): Promise<{
    data: Array<{
      id: string;
      name: string;
      ip: string;
      status: string;
      type: string;
      last_seen: string;
      version: string;
      os: string;
      collectors: string[];
    }>;
  }> => {
    const response = await api.get('/network/agents');
    return response.data;
  },

  // Получить список серверов
  getServers: async (): Promise<{
    data: Array<{
      id: string;
      name: string;
      ip: string;
      status: string;
      type: string;
      last_seen: string;
      services: string[];
    }>;
  }> => {
    const response = await api.get('/network/servers');
    return response.data;
  },

  // Получить топологию сети
  getNetworkTopology: async (): Promise<{
    nodes: any[];
    edges: any[];
    last_updated: string;
  }> => {
    const response = await api.get('/network/network-topology');
    return response.data;
  }
};

// API для трафика
export const trafficApi = {
  // Получить пакеты с фильтрацией
  getPackets: async (params?: {
    limit?: number;
    protocol?: string;
    src_ip?: string;
    dst_ip?: string;
    port?: number;
  }): Promise<{
    packets: any[];
    total: number;
    timestamp: string;
  }> => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.protocol) searchParams.append('protocol', params.protocol);
    if (params?.src_ip) searchParams.append('src_ip', params.src_ip);
    if (params?.dst_ip) searchParams.append('dst_ip', params.dst_ip);
    if (params?.port) searchParams.append('port', params.port.toString());
    
    const response = await api.get(`/traffic/packets?${searchParams.toString()}`);
    return response.data;
  },

  // Получить статистику трафика
  getStats: async (): Promise<{
    total_packets: number;
    tcp_packets: number;
    udp_packets: number;
    http_packets: number;
    https_packets: number;
    dns_packets: number;
    icmp_packets: number;
    bytes_total: number;
    packets_per_second: number;
    threats_detected: number;
    last_updated: string;
  }> => {
    const response = await api.get('/traffic/stats');
    return response.data;
  },

  // Получить распределение по протоколам
  getProtocolDistribution: async (): Promise<{
    protocols: Record<string, number>;
    timestamp: string;
  }> => {
    const response = await api.get('/traffic/protocols');
    return response.data;
  },

  // Начать захват пакетов
  startCapture: async (): Promise<{
    status: string;
    message: string;
    timestamp: string;
  }> => {
    const response = await api.post('/traffic/capture/start');
    return response.data;
  },

  // Остановить захват пакетов
  stopCapture: async (): Promise<{
    status: string;
    message: string;
    timestamp: string;
  }> => {
    const response = await api.post('/traffic/capture/stop');
    return response.data;
  },

  // Получить детали пакета
  getPacketDetails: async (id: number): Promise<any> => {
    const response = await api.get(`/traffic/packet/${id}`);
    return response.data;
  }
};

// API для дашборда
export const dashboardApi = {
  // Получить статистику дашборда
  getStats: async (): Promise<{
    activeEvents: number;
    blockedThreats: number;
    criticalAlerts: number;
    protectedSystems: number;
    totalTraffic: number;
    uniqueIPs: number;
    activeConnections: number;
    systemHealth: number;
  }> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Получить типы угроз
  getThreatTypes: async (): Promise<Array<{
    name: string;
    value: number;
    color: string;
    trend: string;
  }>> => {
    const response = await api.get('/dashboard/threat-types');
    return response.data;
  },

  // Получить активность по времени
  getTimeActivity: async (): Promise<Array<{
    hour: string;
    events: number;
    threats: number;
    blocked: number;
  }>> => {
    const response = await api.get('/dashboard/time-activity');
    return response.data;
  },

  // Получить топ угроз
  getTopThreats: async (): Promise<Array<{
    id: number;
    type: string;
    count: number;
    severity: string;
    trend: string;
  }>> => {
    const response = await api.get('/dashboard/top-threats');
    return response.data;
  },

  // Получить последние события
  getRecentEvents: async (limit: number = 5): Promise<Array<{
    description: string;
    src_ip: string;
    timestamp: string;
    severity: string;
  }>> => {
    const response = await api.get(`/dashboard/recent-events?limit=${limit}`);
    return response.data;
  }
};

// API для системных метрик
export const systemApi = {
  // Получить системные метрики
  getMetrics: async (): Promise<{
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    network_percent: number;
  }> => {
    const response = await api.get('/system/metrics');
    return response.data;
  },

  // Получить информацию об устройстве
  getDeviceInfo: async (): Promise<{
    id: number;
    hostname: string;
    ip: string;
    status: string;
    type: string;
    last_seen: string;
    version: string;
    os: string;
    collectors: string[];
    metrics: {
      cpu_percent: number;
      memory_percent: number;
      disk_percent: number;
      network_percent: number;
      memory_total_gb: number;
      disk_total_gb: number;
    };
  }> => {
    const response = await api.get('/system/device-info');
    return response.data;
  }
};

import { Event, Alert, ApiResponse, AnalyzerStatus, LoginRequest, RegisterRequest, AuthResponse, ApiKey, ActionTypeInfo, ActionConfig, PendingAction, ActionHistory, ActiveBlock, AttackPattern, Recommendation } from '../types';

// ... (rest of the file is the same until alertActionsApi)

// API для действий по алертам
export const alertActionsApi = {
  // Обработка алерта
  processAlert: async (alertData: Alert): Promise<PendingAction[]> => {
    const response = await api.post('/alert-actions/process-alert', alertData);
    return response.data;
  },

  // Получить типы действий
  getActionTypes: async (): Promise<ActionTypeInfo> => {
    const response = await api.get('/alert-actions/action-types');
    return response.data;
  },

  // Получить конфигурации действий
  getActionConfigs: async (): Promise<Record<string, ActionConfig[]>> => {
    const response = await api.get('/alert-actions/action-configs');
    return response.data;
  },

  // Обновить конфигурации действий
  updateActionConfigs: async (alertType: string, configs: ActionConfig[]): Promise<{ message: string }> => {
    const response = await api.put(`/alert-actions/action-configs/${alertType}`, configs);
    return response.data;
  },

  // Получить ожидающие действия
  getPendingActions: async (): Promise<PendingAction[]> => {
    const response = await api.get('/alert-actions/pending-actions');
    return response.data;
  },

  // Подтвердить действие
  approveAction: async (actionId: string): Promise<{ message: string }> => {
    const response = await api.post(`/alert-actions/approve-action/${actionId}`);
    return response.data;
  },

  // Получить историю действий
  getActionHistory: async (limit: number = 100): Promise<ActionHistory[]> => {
    const response = await api.get(`/alert-actions/action-history?limit=${limit}`);
    return response.data;
  },

  // Получить активные блокировки
  getActiveBlocks: async (): Promise<{ active_blocks: ActiveBlock[] }> => {
    const response = await api.get('/alert-actions/active-blocks');
    return response.data;
  },

  // Разблокировать IP
  unblockIp: async (ip: string): Promise<{ message: string }> => {
    const response = await api.delete(`/alert-actions/unblock-ip/${ip}`);
    return response.data;
  },

  // Очистить истекшие блокировки
  cleanupExpiredBlocks: async (): Promise<{ message: string }> => {
    const response = await api.post('/alert-actions/cleanup-expired-blocks');
    return response.data;
  },

  // Получить паттерны атак
  getAttackPatterns: async (): Promise<Record<string, AttackPattern>> => {
    const response = await api.get('/alert-actions/attack-patterns');
    return response.data;
  },

  // Получить рекомендации для типа алерта
  getRecommendations: async (alertType: string): Promise<Recommendation> => {
    const response = await api.get(`/alert-actions/recommendations/${alertType}`);
    return response.data;
  }
};

export { api };
export default api;