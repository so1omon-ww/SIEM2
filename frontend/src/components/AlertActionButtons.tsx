import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Ban, 
  Clock, 
  WifiOff, 
  RefreshCw, 
  Trash2, 
  Bell, 
  FileText,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { alertActionsApi } from '../services/api';

interface AlertActionButtonsProps {
  alertType: string;
  sourceIp?: string;
  targetIp?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  onActionExecuted?: (action: string, result: any) => void;
}

interface ActionConfig {
  action_type: string;
  enabled: boolean;
  auto_execute: boolean;
  ttl_minutes: number;
  parameters: Record<string, any>;
  conditions: string[];
}

interface AttackPattern {
  description: string;
  signs: string[];
  countermeasures: string[];
}

const AlertActionButtons: React.FC<AlertActionButtonsProps> = ({
  alertType,
  sourceIp,
  targetIp,
  severity,
  confidence,
  onActionExecuted
}) => {
  const [actionConfigs, setActionConfigs] = useState<ActionConfig[]>([]);
  const [attackPattern, setAttackPattern] = useState<AttackPattern | null>(null);
  const [loading, setLoading] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);

  useEffect(() => {
    fetchActionConfigs();
    fetchAttackPattern();
  }, [alertType]);

  const fetchActionConfigs = async () => {
    try {
      const data = await alertActionsApi.getActionConfigs();
      setActionConfigs(data[alertType] || []);
    } catch (error) {
      console.error('Error fetching action configs:', error);
    }
  };

  const fetchAttackPattern = async () => {
    try {
      const data = await alertActionsApi.getRecommendations(alertType);
      setAttackPattern(data);
    } catch (error) {
      console.error('Error fetching attack pattern:', error);
    }
  };

  const executeAction = async (actionType: string) => {
    setLoading(true);
    try {
      const result = await alertActionsApi.processAlert({
        alert_type: alertType,
        source_ip: sourceIp,
        target_ip: targetIp,
        severity: severity,
        confidence: confidence
      });
      
      if (onActionExecuted) {
        onActionExecuted(actionType, result);
      }
    } catch (error) {
      console.error('Error executing action:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'block_ip':
        return <Ban className="w-4 h-4" />;
      case 'rate_limit':
        return <Clock className="w-4 h-4" />;
      case 'isolate_host':
        return <WifiOff className="w-4 h-4" />;
      case 'restart_service':
        return <RefreshCw className="w-4 h-4" />;
      case 'flush_cache':
        return <Trash2 className="w-4 h-4" />;
      case 'notify_admin':
        return <Bell className="w-4 h-4" />;
      case 'log_event':
        return <FileText className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const getActionLabel = (actionType: string) => {
    switch (actionType) {
      case 'block_ip':
        return 'Заблокировать IP';
      case 'rate_limit':
        return 'Ограничить скорость';
      case 'isolate_host':
        return 'Изолировать хост';
      case 'restart_service':
        return 'Перезапустить сервис';
      case 'flush_cache':
        return 'Очистить кеш';
      case 'notify_admin':
        return 'Уведомить админа';
      case 'log_event':
        return 'Записать в лог';
      default:
        return actionType;
    }
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    if (confidence >= 0.5) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      {/* Информация об алерте */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Алерт: {alertType.replace(/_/g, ' ').toUpperCase()}
          </h3>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(severity)}`}>
              {severity.toUpperCase()}
            </span>
            <span className={`text-sm font-medium ${getConfidenceColor(confidence)}`}>
              Уверенность: {Math.round(confidence * 100)}%
            </span>
          </div>
        </div>
        
        <div className="text-sm text-gray-600 space-y-1">
          {sourceIp && <p><strong>Источник:</strong> {sourceIp}</p>}
          {targetIp && <p><strong>Цель:</strong> {targetIp}</p>}
        </div>
      </div>

      {/* Кнопки действий */}
      <div className="space-y-3">
        <h4 className="text-md font-medium text-gray-900">Доступные действия:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {actionConfigs.map((config, index) => (
            <button
              key={index}
              onClick={() => executeAction(config.action_type)}
              disabled={!config.enabled || loading}
              className={`
                flex items-center space-x-2 px-4 py-3 rounded-lg border transition-colors
                ${config.enabled 
                  ? 'bg-white border-gray-300 hover:bg-gray-50 hover:border-gray-400' 
                  : 'bg-gray-100 border-gray-200 cursor-not-allowed'
                }
                ${loading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {getActionIcon(config.action_type)}
              <div className="text-left">
                <div className="font-medium text-sm">
                  {getActionLabel(config.action_type)}
                </div>
                <div className="text-xs text-gray-500">
                  TTL: {config.ttl_minutes} мин
                  {config.auto_execute && (
                    <span className="ml-2 text-green-600">• Авто</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Рекомендации по противодействию */}
      {attackPattern && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-md font-medium text-gray-900">
              Рекомендации по противодействию
            </h4>
            <button
              onClick={() => setShowRecommendations(!showRecommendations)}
              className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>{showRecommendations ? 'Скрыть' : 'Показать'}</span>
            </button>
          </div>

          {showRecommendations && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
              <div>
                <h5 className="font-medium text-blue-900 mb-2">Описание атаки:</h5>
                <p className="text-blue-800 text-sm">{attackPattern.description}</p>
              </div>

              <div>
                <h5 className="font-medium text-blue-900 mb-2">Признаки атаки:</h5>
                <ul className="text-blue-800 text-sm space-y-1">
                  {attackPattern.signs.map((sign, index) => (
                    <li key={index} className="flex items-start">
                      <XCircle className="w-3 h-3 mt-0.5 mr-2 text-red-500 flex-shrink-0" />
                      {sign}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h5 className="font-medium text-blue-900 mb-2">Меры противодействия:</h5>
                <ul className="text-blue-800 text-sm space-y-1">
                  {attackPattern.countermeasures.map((measure, index) => (
                    <li key={index} className="flex items-start">
                      <CheckCircle className="w-3 h-3 mt-0.5 mr-2 text-green-500 flex-shrink-0" />
                      {measure}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Статус выполнения */}
      {loading && (
        <div className="flex items-center justify-center py-4">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600 mr-2" />
          <span className="text-blue-600">Выполнение действия...</span>
        </div>
      )}
    </div>
  );
};

export default AlertActionButtons;