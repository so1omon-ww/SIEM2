import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  Clock, 
  Ban, 
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react';
import AlertActionButtons from '../components/AlertActionButtons';
import { alertActionsApi } from '../services/api';

interface Alert {
  id: string;
  alert_type: string;
  source_ip: string;
  target_ip: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  timestamp: string;
  status: 'active' | 'resolved' | 'investigating';
  description: string;
}

interface ActionHistory {
  action: string;
  status: string;
  details?: string;
  timestamp: string;
  error?: string;
}

const AlertActionsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [actionHistory, setActionHistory] = useState<ActionHistory[]>([]);
  const [activeBlocks, setActiveBlocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchAlerts();
    fetchActionHistory();
    fetchActiveBlocks();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/alerts/recent?limit=100');
      const data = await response.json();
      
      if (data.items && Array.isArray(data.items)) {
        const alerts: Alert[] = data.items.map((alert: any) => ({
          id: alert.id.toString(),
          alert_type: alert.alert_type || 'unknown',
          source_ip: alert.source_ip || 'unknown',
          target_ip: alert.target_ip || 'unknown',
          severity: alert.severity || 'medium',
          confidence: alert.confidence || 0.5,
          timestamp: alert.timestamp || new Date().toISOString(),
          status: alert.status || 'active',
          description: alert.description || alert.message || 'Без описания'
        }));
        setAlerts(alerts);
      } else {
        setAlerts([]);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchActionHistory = async () => {
    try {
      const data = await alertActionsApi.getActionHistory();
      setActionHistory(data);
    } catch (error) {
      console.error('Error fetching action history:', error);
    }
  };

  const fetchActiveBlocks = async () => {
    try {
      const data = await alertActionsApi.getActiveBlocks();
      setActiveBlocks(data.active_blocks || []);
    } catch (error) {
      console.error('Error fetching active blocks:', error);
    }
  };

  const handleActionExecuted = (action: string, result: any) => {
    console.log('Action executed:', action, result);
    // Обновляем историю действий
    fetchActionHistory();
    // Обновляем активные блокировки
    fetchActiveBlocks();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-red-600 bg-red-100';
      case 'investigating':
        return 'text-yellow-600 bg-yellow-100';
      case 'resolved':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getActionStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-600" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Загрузка алертов...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Управление алертами</h1>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {showHistory ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            <span>{showHistory ? 'Скрыть историю' : 'Показать историю'}</span>
          </button>
          <button
            onClick={() => {
              fetchAlerts();
              fetchActionHistory();
              fetchActiveBlocks();
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Обновить</span>
          </button>
        </div>
      </div>

      {/* Активные блокировки */}
      {activeBlocks.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-900 mb-3 flex items-center">
            <Ban className="w-5 h-5 mr-2" />
            Активные блокировки IP
          </h3>
          <div className="space-y-2">
            {activeBlocks.map((block, index) => (
              <div key={index} className="flex items-center justify-between bg-white p-3 rounded border">
                <div>
                  <span className="font-medium text-gray-900">{block.ip}</span>
                  <span className="ml-2 text-sm text-gray-600">
                    Истекает через {block.remaining_minutes} мин
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(block.expires_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Список алертов */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Активные алерты</h2>
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>Нет активных алертов</p>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div key={alert.id} className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {alert.alert_type.replace(/_/g, ' ').toUpperCase()}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                        {alert.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-2">{alert.description}</p>
                    <div className="text-sm text-gray-500">
                      <p><strong>Источник:</strong> {alert.source_ip}</p>
                      <p><strong>Цель:</strong> {alert.target_ip}</p>
                      <p><strong>Уверенность:</strong> {Math.round(alert.confidence * 100)}%</p>
                      <p><strong>Время:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedAlert(alert)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    Действия
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Модальное окно с действиями */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Действия по алерту
              </h2>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            
            <AlertActionButtons
              alertType={selectedAlert.alert_type}
              sourceIp={selectedAlert.source_ip}
              targetIp={selectedAlert.target_ip}
              severity={selectedAlert.severity}
              confidence={selectedAlert.confidence}
              onActionExecuted={handleActionExecuted}
            />
          </div>
        </div>
      )}

      {/* История действий */}
      {showHistory && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">История действий</h2>
          {actionHistory.length === 0 ? (
            <p className="text-gray-500 text-center py-4">История действий пуста</p>
          ) : (
            <div className="space-y-3">
              {actionHistory.map((action, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getActionStatusIcon(action.status)}
                    <div>
                      <span className="font-medium text-gray-900">{action.action}</span>
                      {action.details && (
                        <p className="text-sm text-gray-600">{action.details}</p>
                      )}
                      {action.error && (
                        <p className="text-sm text-red-600">{action.error}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(action.timestamp).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AlertActionsPage;