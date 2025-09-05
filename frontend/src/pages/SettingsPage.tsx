import React from 'react';
import { Settings, Moon, Sun, Bell, Shield, Database, Network, User, Key, Info } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const SettingsPage: React.FC = () => {
  const { darkMode, toggleDarkMode } = useTheme();

  const settingsSections = [
    {
      title: 'Внешний вид',
      icon: darkMode ? Sun : Moon,
      items: [
        {
          label: 'Темная тема',
          description: 'Переключить между светлой и темной темой',
          action: (
            <button
              onClick={toggleDarkMode}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                darkMode ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  darkMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          )
        }
      ]
    },
    {
      title: 'Уведомления',
      icon: Bell,
      items: [
        {
          label: 'Email уведомления',
          description: 'Получать уведомления на email о критических событиях',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
            </button>
          )
        },
        {
          label: 'Push уведомления',
          description: 'Получать push уведомления в браузере',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
            </button>
          )
        }
      ]
    },
    {
      title: 'Безопасность',
      icon: Shield,
      items: [
        {
          label: 'Двухфакторная аутентификация',
          description: 'Дополнительная защита аккаунта',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
            </button>
          )
        },
        {
          label: 'Автоматический выход',
          description: 'Выход из системы через 30 минут неактивности',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
            </button>
          )
        }
      ]
    },
    {
      title: 'Система',
      icon: Database,
      items: [
        {
          label: 'Автообновление данных',
          description: 'Автоматическое обновление данных каждые 30 секунд',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
            </button>
          )
        },
        {
          label: 'Сохранение логов',
          description: 'Сохранять логи событий на 90 дней',
          action: (
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
            </button>
          )
        }
      ]
    }
  ];

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className={`text-3xl font-bold flex items-center ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            <Settings className="h-8 w-8 mr-3 text-blue-500" />
            Настройки
          </h1>
          <p className={`mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            Управление настройками системы безопасности
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-6">
          {settingsSections.map((section, sectionIndex) => (
            <div
              key={sectionIndex}
              className={`rounded-2xl p-6 shadow-xl border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'
              }`}
            >
              <div className="flex items-center mb-6">
                <div className={`p-3 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 shadow-lg`}>
                  <section.icon className="h-6 w-6 text-white" />
                </div>
                <h2 className={`text-xl font-bold ml-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {section.title}
                </h2>
              </div>

              <div className="space-y-4">
                {section.items.map((item, itemIndex) => (
                  <div
                    key={itemIndex}
                    className={`flex items-center justify-between p-4 rounded-lg ${
                      darkMode ? 'bg-gray-700' : 'bg-gray-50'
                    }`}
                  >
                    <div className="flex-1">
                      <h3 className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {item.label}
                      </h3>
                      <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                        {item.description}
                      </p>
                    </div>
                    <div className="ml-4">
                      {item.action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className={`mt-8 p-6 rounded-2xl border ${
          darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'
        }`}>
          <h3 className={`text-lg font-semibold mb-4 flex items-center ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            <Info className="h-5 w-5 mr-2 text-blue-500" />
            Информация о системе
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Версия системы
              </p>
              <p className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                SIEM v1.0.0
              </p>
            </div>
            <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Последнее обновление
              </p>
              <p className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {new Date().toLocaleDateString('ru-RU')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
