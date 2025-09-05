import React, { useState, useEffect } from 'react';
import { Download, HardDrive, Box, CheckCircle, Shield, Monitor, Zap, Clock, RefreshCw } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { api } from '../services/api';

interface RepoItem {
  id: string;
  name: string;
  description: string;
  size_mb?: number;
  size_bytes?: number;
  download_url: string;
  version: string;
  platform: string;
  features: string[];
  icon: React.ReactNode;
  requirements: string[];
}

const ReposPage: React.FC = () => {
  const { darkMode } = useTheme();
  const [downloading, setDownloading] = useState<string | null>(null);
  const [items, setItems] = useState<RepoItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Загрузка списка репозиториев
  const fetchRepositories = async () => {
    try {
      setLoading(true);
      const response = await api.get('/repos/list');
      console.log('API response:', response.data);
      console.log('Response status:', response.status);
      
      // Проверяем, что response.data является массивом
      const data = Array.isArray(response.data) ? response.data : [];
      console.log('Processed data:', data);
      
      const repos = data.map((repo: any) => ({
        ...repo,
        icon: repo.platform.includes('Windows') 
          ? <Monitor className="h-6 w-6 text-blue-600" />
          : <Shield className="h-6 w-6 text-green-600" />
      }));
      console.log('Mapped repos:', repos);
      setItems(repos);
    } catch (error) {
      console.error('Error fetching repositories:', error);
      setItems([]); // Устанавливаем пустой массив в случае ошибки
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
  }, []);

  const handleDownload = async (item: RepoItem) => {
    setDownloading(item.id);
    try {
      // Используем API endpoint для скачивания
      const downloadUrl = item.download_url;
      console.log('Downloading from:', downloadUrl);
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Download error:', error);
    } finally {
      // Сбрасываем состояние загрузки через 2 секунды
      setTimeout(() => setDownloading(null), 2000);
    }
  };

  return (
    <div className={`space-y-6 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
      <div>
        <div className="flex justify-between items-start">
          <div>
            <h1 className={`text-3xl font-bold flex items-center ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              <HardDrive className="h-8 w-8 mr-3 text-blue-600" />
              Скачать агенты SIEM
            </h1>
            <p className={`mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Готовые к установке офлайн-пакеты агентов с автостартом и фоновой работой. Все зависимости включены.
            </p>
            <div className="mt-2 inline-flex items-center text-sm text-green-700 bg-green-50 border border-green-200 rounded px-2 py-1">
              <CheckCircle className="h-4 w-4 mr-1" />
              Доступно без выхода в интернет
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={fetchRepositories}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                darkMode 
                  ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>
        </div>
        
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-lg">Загрузка репозиториев...</span>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <HardDrive className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Репозитории не найдены
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Попробуйте обновить страницу
          </p>
          <button
            onClick={fetchRepositories}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Обновить
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {items.map((item) => (
          <div key={item.id} className={`rounded-xl border shadow-lg p-6 flex flex-col ${
            darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          }`}>
            {/* Заголовок */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                {item.icon}
                <div>
                  <h3 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {item.name}
                  </h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Версия {item.version} • {item.size_mb ? `≈ ${item.size_mb} MB` : 'Размер неизвестен'}
                  </p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                item.platform.includes('Windows') 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {item.platform}
              </div>
            </div>

            <p className={`text-sm mb-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              {item.description}
            </p>

            {/* Особенности */}
            <div className="mb-4">
              <h4 className={`font-semibold mb-2 flex items-center ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                <Zap className="h-4 w-4 mr-2 text-yellow-500" />
                Особенности
              </h4>
              <ul className="space-y-1">
                {item.features.map((feature, index) => (
                  <li key={index} className={`flex items-start text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    <CheckCircle className="h-3 w-3 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* Требования */}
            <div className="mb-6">
              <h4 className={`font-semibold mb-2 flex items-center ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                <Clock className="h-4 w-4 mr-2 text-blue-500" />
                Требования
              </h4>
              <ul className="space-y-1">
                {item.requirements.map((requirement, index) => (
                  <li key={index} className={`flex items-start text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    <Box className="h-3 w-3 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                    {requirement}
                  </li>
                ))}
              </ul>
            </div>

            {/* Кнопка скачивания */}
            <button
              onClick={() => handleDownload(item)}
              disabled={downloading === item.id}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              {downloading === item.id ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Скачивание...</span>
                </>
              ) : (
                <>
                  <Download className="h-5 w-5" />
                  <span>Скачать {item.name}</span>
                </>
              )}
            </button>
          </div>
        ))}
        </div>
      )}

      <div className="mt-8 space-y-6">
        {/* AstraLinux Docker Installation */}
        <div className={`border rounded-lg p-6 ${
          darkMode ? 'bg-gray-800 border-gray-700' : 'bg-blue-50 border-blue-200'
        }`}>
          <h4 className={`font-semibold mb-4 flex items-center ${
            darkMode ? 'text-white' : 'text-blue-900'
          }`}>
            <Shield className="h-5 w-5 mr-2 text-green-600" />
            Установка AstraLinux SIEM Agent v2.0.0 (Docker)
          </h4>
          <ol className={`list-decimal ml-6 text-sm space-y-2 ${
            darkMode ? 'text-gray-300' : 'text-blue-900'
          }`}>
            <li>Скачайте архив <code className="bg-gray-200 px-1 rounded">siem-astra-agent-v2.0.0-docker.zip</code> с этой страницы</li>
            <li>Скопируйте архив на AstraLinux машину</li>
            <li>Создайте каталог: <code className="bg-gray-200 px-1 rounded">sudo mkdir -p /opt/siem-astra-agent-docker</code></li>
            <li>Распакуйте: <code className="bg-gray-200 px-1 rounded">unzip siem-astra-agent-v2.0.0-docker.zip -d /opt/siem-astra-agent-docker</code></li>
            <li>Зайдите в каталог: <code className="bg-gray-200 px-1 rounded">cd /opt/siem-astra-agent-docker</code></li>
            <li>Отредактируйте <code className="bg-gray-200 px-1 rounded">config.yaml</code> (укажите API ключ и URL сервера)</li>
            <li>Отредактируйте <code className="bg-gray-200 px-1 rounded">docker-compose.yml</code> (укажите API ключ)</li>
            <li>Запустите установку: <code className="bg-gray-200 px-1 rounded">sudo ./install.sh</code></li>
            <li>Агент автоматически запустится в Docker контейнере</li>
          </ol>
          <div className={`mt-4 p-3 rounded text-sm ${
            darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
          }`}>
            <strong>Advantages v2.0.0:</strong> Fully offline, Docker container, all dependencies included, privileged system access
          </div>
        </div>

        {/* Windows Installation */}
        <div className={`border rounded-lg p-6 ${
          darkMode ? 'bg-gray-800 border-gray-700' : 'bg-green-50 border-green-200'
        }`}>
          <h4 className={`font-semibold mb-4 flex items-center ${
            darkMode ? 'text-white' : 'text-green-900'
          }`}>
            <Monitor className="h-5 w-5 mr-2 text-blue-600" />
            Установка Windows Privileged SIEM Agent v2.0.0
          </h4>
          <ol className={`list-decimal ml-6 text-sm space-y-2 ${
            darkMode ? 'text-gray-300' : 'text-green-900'
          }`}>
            <li>Скачайте архив <code className="bg-gray-200 px-1 rounded">siem-privileged-agent-windows-v2.0.0.zip</code> с этой страницы</li>
            <li>Распакуйте архив в любую папку (например, <code className="bg-gray-200 px-1 rounded">C:\SIEM-Agent</code>)</li>
            <li>Отредактируйте файл <code className="bg-gray-200 px-1 rounded">config.yaml</code>:</li>
            <ul className="list-disc ml-6 mt-1 space-y-1">
              <li>Замените <code className="bg-gray-200 px-1 rounded">your-siem-server:8000</code> на адрес вашего SIEM сервера</li>
              <li>Замените <code className="bg-gray-200 px-1 rounded">your_api_key_here</code> на ваш API ключ</li>
            </ul>
            <li>Запустите <strong>PowerShell от имени администратора</strong></li>
            <li>Перейдите в папку агента: <code className="bg-gray-200 px-1 rounded">cd C:\SIEM-Agent</code></li>
            <li>Выполните установку: <code className="bg-gray-200 px-1 rounded">.\install.ps1</code></li>
            <li>Агент будет установлен как служба Windows и запустится автоматически</li>
          </ol>
          <div className={`mt-4 p-3 rounded text-sm ${
            darkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800'
          }`}>
            <strong>Warning:</strong> Agent requires privileged access for monitoring Windows system events
          </div>
          <div className={`mt-2 p-3 rounded text-sm ${
            darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
          }`}>
            <strong>Advantages v2.0.0:</strong> Fully offline, Windows service installation, heartbeat monitoring, all dependencies included
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReposPage;


