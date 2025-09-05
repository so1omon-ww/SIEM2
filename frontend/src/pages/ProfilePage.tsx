import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Monitor, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Wifi, 
  Shield, 
  Settings,
  Save,
  RefreshCw
} from 'lucide-react';
import { systemApi } from '../services/api';

interface DeviceInfo {
  id: number;
  hostname: string;
  os: string;
  version: string;
  ip: string;
  status: string;
  lastSeen: string;
  collectors: string[];
  metrics: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    network_percent: number;
    memory_total_gb: number;
    disk_total_gb: number;
  };
}

const ProfilePage: React.FC = () => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState<Partial<DeviceInfo>>({});

  useEffect(() => {
    fetchDeviceInfo();
    
    // Автообновление каждые 30 секунд
    const interval = setInterval(() => {
      fetchDeviceInfo();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDeviceInfo = async () => {
    try {
      setLoading(true);
      console.log('Fetching device info...');
      const deviceInfo = await systemApi.getDeviceInfo();
      console.log('Device info received:', deviceInfo);
      setDeviceInfo(deviceInfo);
      setFormData(deviceInfo);
    } catch (error) {
      console.error('Error fetching device info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      // Здесь можно добавить API для обновления информации об устройстве
      await new Promise(resolve => setTimeout(resolve, 1000)); // Имитация сохранения
      setEditing(false);
      await fetchDeviceInfo();
    } catch (error) {
      console.error('Error saving device info:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof DeviceInfo, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Загрузка информации об устройстве...</p>
        </div>
      </div>
    );
  }

  if (!deviceInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Monitor className="h-16 w-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Устройство не найдено</h2>
          <p className="text-gray-600">Не удалось загрузить информацию об устройстве</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Профиль устройства</h1>
              <p className="mt-2 text-gray-600">Управление характеристиками вашего компьютера</p>
            </div>
            <div className="flex space-x-3">
              {editing ? (
                <>
                  <button
                    onClick={() => setEditing(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {saving ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Сохранить
                      </>
                    )}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Редактировать
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Device Overview */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <div className="flex items-center mb-6">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Monitor className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <h2 className="text-xl font-semibold text-gray-900">Основная информация</h2>
                  <p className="text-gray-600">Характеристики вашего устройства</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Имя устройства
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.hostname || ''}
                      onChange={(e) => handleInputChange('hostname', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-gray-900 font-medium">{deviceInfo?.hostname || 'Неизвестно'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IP адрес
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.ip || ''}
                      onChange={(e) => handleInputChange('ip', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-gray-900 font-medium">{deviceInfo?.ip || 'Неизвестно'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Операционная система
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.os || ''}
                      onChange={(e) => handleInputChange('os', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-gray-900 font-medium">{deviceInfo?.os || 'Неизвестно'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Версия агента
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.version || ''}
                      onChange={(e) => handleInputChange('version', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-gray-900 font-medium">{deviceInfo?.version || 'Неизвестно'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Статус
                  </label>
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-2 ${
                      deviceInfo?.status === 'online' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className={`font-medium ${
                      deviceInfo?.status === 'online' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {deviceInfo?.status === 'online' ? 'Онлайн' : 'Офлайн'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Последняя активность
                  </label>
                  <p className="text-gray-900 font-medium">
                    {deviceInfo?.lastSeen ? new Date(deviceInfo.lastSeen).toLocaleString('ru-RU') : 'Неизвестно'}
                  </p>
                </div>
              </div>
            </motion.div>

            {/* System Resources */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <div className="flex items-center mb-6">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Cpu className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <h2 className="text-xl font-semibold text-gray-900">Системные ресурсы</h2>
                  <p className="text-gray-600">Текущее состояние системы</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <Cpu className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-700">CPU</p>
                    <p className="text-2xl font-bold text-blue-600">{deviceInfo?.metrics?.cpu_percent || 0}%</p>
                  </div>
                </div>

                <div className="text-center">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <MemoryStick className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-700">Память</p>
                    <p className="text-2xl font-bold text-green-600">{deviceInfo?.metrics?.memory_percent || 0}%</p>
                  </div>
                </div>

                <div className="text-center">
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <HardDrive className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-700">Диск</p>
                    <p className="text-2xl font-bold text-yellow-600">{deviceInfo?.metrics?.disk_percent || 0}%</p>
                  </div>
                </div>

                <div className="text-center">
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <Wifi className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm font-medium text-gray-700">Сеть</p>
                    <p className="text-2xl font-bold text-purple-600">{deviceInfo?.metrics?.network_percent || 0}%</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Collectors */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <div className="flex items-center mb-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Shield className="h-5 w-5 text-purple-600" />
                </div>
                <h3 className="ml-3 text-lg font-semibold text-gray-900">Коллекторы</h3>
              </div>

              <div className="space-y-3">
                {(deviceInfo?.collectors || []).map((collector, index) => (
                  <div key={index} className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-3" />
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {collector.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
              
              <div className="space-y-3">
                <button
                  onClick={() => {
                    console.log('Manual refresh triggered');
                    fetchDeviceInfo();
                  }}
                  className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Обновить данные
                </button>

                <button
                  onClick={() => setEditing(!editing)}
                  className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  {editing ? 'Отменить редактирование' : 'Редактировать профиль'}
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
