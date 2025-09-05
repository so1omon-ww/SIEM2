import React, { useState } from 'react';
import { Search, Wifi, Router, Server, Monitor, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { api } from '../services/api';

interface DiscoveredDevice {
  ip: string;
  hostname: string;
  type: string;
  status: string;
  response_time: number;
}

interface NetworkDiscoveryProps {
  onDevicesDiscovered: (devices: DiscoveredDevice[]) => void;
}

const NetworkDiscovery: React.FC<NetworkDiscoveryProps> = ({ onDevicesDiscovered }) => {
  const { darkMode } = useTheme();
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState<DiscoveredDevice[]>([]);
  const [networkRange, setNetworkRange] = useState('192.168.1.0/24');
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'completed' | 'error'>('idle');

  const handleNetworkScan = async () => {
    try {
      setIsScanning(true);
      setScanStatus('scanning');
      
      const response = await api.get('/network/network-scan', {
        params: { network_range: networkRange }
      });
      
      const discoveredDevices = response.data.discovered_devices || [];
      setScanResults(discoveredDevices);
      onDevicesDiscovered(discoveredDevices);
      setScanStatus('completed');
      
    } catch (error) {
      console.error('Ошибка сканирования сети:', error);
      setScanStatus('error');
    } finally {
      setIsScanning(false);
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'router': return <Router className="h-4 w-4" />;
      case 'switch': return <Wifi className="h-4 w-4" />;
      case 'server': return <Server className="h-4 w-4" />;
      case 'agent': return <Monitor className="h-4 w-4" />;
      default: return <Wifi className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-500';
      case 'offline': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className={`rounded-lg border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          Обнаружение устройств
        </h3>
        <Search className={`h-5 w-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
      </div>

      {/* Настройки сканирования */}
      <div className="mb-4">
        <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          Диапазон сети
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={networkRange}
            onChange={(e) => setNetworkRange(e.target.value)}
            className={`flex-1 px-3 py-2 border rounded-md ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-white' 
                : 'bg-white border-gray-300 text-gray-900'
            }`}
            placeholder="192.168.1.0/24"
          />
          <button
            onClick={handleNetworkScan}
            disabled={isScanning}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              isScanning
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isScanning ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              'Сканировать'
            )}
          </button>
        </div>
      </div>

      {/* Статус сканирования */}
      {scanStatus !== 'idle' && (
        <div className="mb-4">
          {scanStatus === 'scanning' && (
            <div className="flex items-center text-blue-500">
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              <span className="text-sm">Сканирование сети...</span>
            </div>
          )}
          {scanStatus === 'completed' && (
            <div className="flex items-center text-green-500">
              <CheckCircle className="h-4 w-4 mr-2" />
              <span className="text-sm">Сканирование завершено</span>
            </div>
          )}
          {scanStatus === 'error' && (
            <div className="flex items-center text-red-500">
              <AlertCircle className="h-4 w-4 mr-2" />
              <span className="text-sm">Ошибка сканирования</span>
            </div>
          )}
        </div>
      )}

      {/* Результаты сканирования */}
      {scanResults.length > 0 && (
        <div>
          <h4 className={`text-sm font-medium mb-3 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            Обнаруженные устройства ({scanResults.length})
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {scanResults.map((device, index) => (
              <div
                key={index}
                className={`flex items-center justify-between p-3 rounded-lg ${
                  darkMode ? 'bg-gray-700' : 'bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {getDeviceIcon(device.type)}
                  <div>
                    <p className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {device.hostname}
                    </p>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {device.ip}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {device.response_time}ms
                  </span>
                  {getStatusIcon(device.status)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Информация о типах устройств */}
      <div className="mt-4 pt-4 border-t border-gray-600">
        <h4 className={`text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          Типы устройств
        </h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center">
            <Router className="h-3 w-3 mr-1 text-yellow-500" />
            <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Роутер</span>
          </div>
          <div className="flex items-center">
            <Wifi className="h-3 w-3 mr-1 text-purple-500" />
            <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Коммутатор</span>
          </div>
          <div className="flex items-center">
            <Server className="h-3 w-3 mr-1 text-blue-500" />
            <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Сервер</span>
          </div>
          <div className="flex items-center">
            <Monitor className="h-3 w-3 mr-1 text-green-500" />
            <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Агент</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkDiscovery;
