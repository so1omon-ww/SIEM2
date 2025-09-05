import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, CheckCircle, XCircle, Eye, Shield } from 'lucide-react';
import { Alert } from '../types';
import { alertsApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await alertsApi.getRecentAlerts(100);
      setAlerts(response.items || []);
    } catch (err) {
      setError('Не удалось загрузить алерты. Проверьте подключение к серверу.');
      console.error('Error loading alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await alertsApi.acknowledgeAlert(alertId);
      // Обновляем состояние алерта локально
      setAlerts(alerts.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  useEffect(() => {
    loadAlerts();
    
    // Автообновление каждые 15 секунд для алертов
    const interval = setInterval(loadAlerts, 15000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-700 bg-red-100 border-red-200';
      case 'high': return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-blue-700 bg-blue-100 border-blue-200';
      case 'info': return 'text-gray-700 bg-gray-100 border-gray-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return <XCircle className="h-5 w-5 text-red-600" />;
      case 'high': return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'medium': return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'low': return <Shield className="h-5 w-5 text-blue-600" />;
      case 'info': return <Shield className="h-5 w-5 text-gray-600" />;
      default: return <Shield className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU');
  };

  const getUnacknowledgedCount = () => {
    return alerts.filter(alert => !alert.acknowledged).length;
  };

  if (loading) {
    return <LoadingSpinner text="Загрузка алертов..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadAlerts} />;
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Заголовок */}
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900 flex items-center">
            <AlertTriangle className="h-8 w-8 mr-3 text-siem-danger" />
            Алерты безопасности
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Предупреждения о событиях безопасности ({alerts.length} алертов, {getUnacknowledgedCount()} не подтверждены)
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={loadAlerts}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-siem-primary px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-siem-primary focus:ring-offset-2"
          >
            Обновить
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {['critical', 'high', 'medium', 'low'].map(severity => {
          const count = alerts.filter(alert => alert.severity === severity).length;
          return (
            <div key={severity} className={`overflow-hidden rounded-lg px-4 py-5 shadow border ${getSeverityColor(severity)}`}>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {getSeverityIcon(severity)}
                </div>
                <div className="ml-3 w-0 flex-1">
                  <dl>
                    <dt className="truncate text-sm font-medium capitalize">{severity}</dt>
                    <dd className="text-lg font-semibold">{count}</dd>
                  </dl>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Список алертов */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Время
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Важность
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Источник
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Описание
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Статус
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {alerts.map((alert) => (
                    <tr key={alert.id} className={`hover:bg-gray-50 ${!alert.acknowledged ? 'bg-red-50' : ''}`}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-2 text-gray-400" />
                          {formatTimestamp(alert.ts)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getSeverityIcon(alert.severity)}
                          <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(alert.severity)}`}>
                            {alert.severity}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {alert.source}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {alert.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {alert.acknowledged ? (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full text-green-700 bg-green-100">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Подтверждён
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full text-red-700 bg-red-100">
                            <XCircle className="h-3 w-3 mr-1" />
                            Новый
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedAlert(alert)}
                            className="text-siem-primary hover:text-blue-900 inline-flex items-center"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Подробнее
                          </button>
                          {!alert.acknowledged && (
                            <button
                              onClick={() => handleAcknowledgeAlert(alert.id)}
                              className="text-green-600 hover:text-green-900 inline-flex items-center"
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Подтвердить
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {alerts.length === 0 && (
        <div className="text-center py-12">
          <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Нет алертов</h3>
          <p className="mt-1 text-sm text-gray-500">Алерты появятся здесь при обнаружении событий безопасности.</p>
        </div>
      )}

      {/* Модальное окно с деталями алерта */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  {getSeverityIcon(selectedAlert.severity)}
                  <span className="ml-2">Алерт #{selectedAlert.id}</span>
                </h3>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Время создания</label>
                    <p className="mt-1 text-sm text-gray-900">{formatTimestamp(selectedAlert.ts)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Важность</label>
                    <div className="mt-1 flex items-center">
                      {getSeverityIcon(selectedAlert.severity)}
                      <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(selectedAlert.severity)}`}>
                        {selectedAlert.severity}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Источник</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedAlert.source}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Статус</label>
                    <div className="mt-1">
                      {selectedAlert.acknowledged ? (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full text-green-700 bg-green-100">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Подтверждён
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full text-red-700 bg-red-100">
                          <XCircle className="h-3 w-3 mr-1" />
                          Новый
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Описание</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded-md">{selectedAlert.description}</p>
                </div>
                
                {selectedAlert.metadata && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Метаданные</label>
                    <pre className="mt-1 text-xs text-gray-900 bg-gray-50 p-3 rounded-md overflow-x-auto">
                      {JSON.stringify(selectedAlert.metadata, null, 2)}
                    </pre>
                  </div>
                )}

                {!selectedAlert.acknowledged && (
                  <div className="flex justify-end">
                    <button
                      onClick={() => {
                        handleAcknowledgeAlert(selectedAlert.id);
                        setSelectedAlert({ ...selectedAlert, acknowledged: true });
                      }}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Подтвердить алерт
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsPage;
