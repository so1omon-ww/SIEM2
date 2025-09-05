import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Key, Copy, CheckCircle, Plus, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const ApiKeysPage: React.FC = () => {
  const { user, apiKey, generateApiKey } = useAuth();
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleCopyApiKey = async () => {
    if (!apiKey) return;
    
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy API key:', error);
    }
  };

  const handleGenerateNewKey = async () => {
    setIsGenerating(true);
    try {
      await generateApiKey();
    } catch (error) {
      console.error('Failed to generate API key:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">API Ключи</h1>
          <p className="mt-2 text-gray-600">
            Управление API ключами для подключения агентов к SIEM системе
          </p>
        </div>

        {/* Текущий API ключ */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Текущий API ключ</h2>
          </div>
          <div className="px-6 py-4">
            {apiKey ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Key className="inline h-4 w-4 mr-2" />
                    API ключ
                  </label>
                  <div className="flex">
                    <input
                      type="text"
                      value={apiKey}
                      readOnly
                      className="flex-1 border border-gray-300 rounded-l-md px-3 py-2 bg-gray-50 text-gray-900 font-mono text-sm"
                    />
                    <button
                      onClick={handleCopyApiKey}
                      className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 transition-colors flex items-center"
                    >
                      {copied ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">
                    Как использовать API ключ:
                  </h3>
                  <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                    <li>Скопируйте API ключ выше</li>
                    <li>Откройте конфигурационный файл вашего агента</li>
                    <li>Найдите параметр <code className="bg-blue-100 px-1 rounded">api_key</code></li>
                    <li>Вставьте скопированный ключ в значение параметра</li>
                    <li>Сохраните файл и перезапустите агента</li>
                  </ol>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                  <h3 className="text-sm font-medium text-yellow-900 mb-2">
                    Important information:
                  </h3>
                  <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
                    <li>Храните API ключ в безопасном месте</li>
                    <li>Не передавайте ключ третьим лицам</li>
                    <li>При компрометации ключа сразу сгенерируйте новый</li>
                    <li>После генерации нового ключа старый становится недействительным</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Key className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  API ключ не найден
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Сгенерируйте новый API ключ для подключения агентов
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Действия */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Действия</h2>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleGenerateNewKey}
                disabled={isGenerating}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <Plus className="h-4 w-4 mr-2" />
                )}
                {apiKey ? 'Сгенерировать новый ключ' : 'Сгенерировать API ключ'}
              </motion.button>
              
              {apiKey && (
                <p className="text-sm text-gray-500">
                  При генерации нового ключа текущий ключ станет недействительным.
                  Убедитесь, что обновили конфигурацию всех агентов.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Примеры конфигурации */}
        <div className="bg-white shadow rounded-lg mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Примеры конфигурации агентов</h2>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Python агент (config.yaml)</h3>
                <pre className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm font-mono overflow-x-auto">
{`server:
  url: "http://your-server:8000"
  api_key: "${apiKey || 'YOUR_API_KEY_HERE'}"

agent:
  id: "agent-001"
  hostname: "production-server"
  
collector:
  enabled: true
  interval: 30`}
                </pre>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Переменные окружения</h3>
                <pre className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm font-mono overflow-x-auto">
{`SIEM_API_KEY=${apiKey || 'YOUR_API_KEY_HERE'}
SIEM_SERVER_URL=http://your-server:8000
AGENT_ID=agent-001`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiKeysPage;