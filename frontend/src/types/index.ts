// Типы для событий
export interface Event {
  id: number;
  ts: string;
  event_type: string;
  severity: string;
  agent_id?: number;
  host_id?: string;
  src_ip?: string;
  dst_ip?: string;
  src_port?: number;
  dst_port?: number;
  protocol?: string;
  packet_size?: number;
  flags?: string;
  details?: Record<string, any>;
}

// Типы для алертов
export interface Alert {
  id: number;
  ts: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  source: string;
  description: string;
  acknowledged: boolean;
  event_id?: number;
  agent_id?: number;
  alert_type?: string;
  metadata?: Record<string, any>;
}

// Типы для API ответов
export interface ApiResponse<T> {
  items: T[];
  count?: number;
  total?: number;
}

// Типы для статуса анализатора
export interface AnalyzerStatus {
  is_integrated: boolean;
  integration_start_time: string;
  analyzer_status: {
    is_running: boolean;
    processed_events_count: number;
    triggered_rules_count: number;
    generated_alerts_count: number;
    event_cache_size: number;
    last_rule_reload: string;
    config: Record<string, any>;
  };
  config: Record<string, any>;
}

// Типы для аутентификации
export interface User {
  id: number;
  username: string;
  role: 'user' | 'admin';
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  expires_at: string;
}

export interface ApiKey {
  token: string;
  created_at: string;
}

export interface AuthContextType {
  user: User | null;
  apiKey: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  generateApiKey: () => Promise<string>;
  isAuthenticated: boolean;
}