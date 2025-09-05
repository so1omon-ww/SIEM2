import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Shield, Activity, AlertTriangle, BarChart3, Settings, Menu, X, LogOut, Key, Moon, Sun, Network, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, apiKey } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();

  const menuItems = [
    { path: '/dashboard', icon: BarChart3, label: 'Панель управления' },
    { path: '/events', icon: Activity, label: 'События' },
    { path: '/alerts', icon: AlertTriangle, label: 'Алерты' },
    { path: '/alert-actions', icon: Shield, label: 'Действия по алертам' },
    { path: '/traffic', icon: Activity, label: 'Трафик' },
    { path: '/network', icon: Network, label: 'Сеть' },
    { path: '/repos', icon: Shield, label: 'Репозитории' },
    { path: '/api-keys', icon: Key, label: 'API Ключи' },
    { path: '/profile', icon: User, label: 'Профиль' },
    { path: '/settings', icon: Settings, label: 'Настройки' },
  ];

  // Компонент для отображения информации о пользователе
  const UserInfo = ({ isMobile = false, onClose = () => {} }) => (
    <div className={`flex-shrink-0 flex border-t p-4 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
      <div className="flex-shrink-0 w-full">
        <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{user?.username}</p>
        {apiKey && (
          <p className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            <Key className="h-3 w-3 mr-1" />
            API ключ активен
          </p>
        )}
        <div className="mt-2 space-y-2">
          <button
            onClick={toggleDarkMode}
            className={`w-full flex items-center px-2 py-2 text-sm rounded-md transition-colors ${
              darkMode 
                ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            {darkMode ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
            {darkMode ? 'Светлая тема' : 'Темная тема'}
          </button>
          <button
            onClick={() => {
              handleLogout();
              if (isMobile) onClose();
            }}
            className={`w-full flex items-center px-2 py-2 text-sm rounded-md transition-colors ${
              darkMode 
                ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Выйти
          </button>
        </div>
      </div>
    </div>
  );

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className={`min-h-screen flex ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Sidebar для десктопа */}
      <div className="hidden lg:flex lg:flex-shrink-0 lg:w-64">
        <div className="flex flex-col w-full">
          <div className={`flex-1 flex flex-col min-h-0 border-r ${darkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'}`}>
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <button 
                  onClick={() => navigate('/home')}
                  className="flex items-center hover:opacity-80 transition-opacity"
                >
                  <Shield className="h-8 w-8 text-blue-600" />
                  <span className={`ml-2 text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>SIEM System</span>
                </button>
              </div>
              <nav className="mt-8 flex-1 px-2 space-y-1">
                {menuItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`${
                        isActive
                          ? 'bg-blue-100 text-blue-900 border-r-2 border-blue-600'
                          : darkMode 
                            ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      } group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full transition-colors duration-200`}
                    >
                      <item.icon
                        className={`${
                          isActive ? 'text-blue-500' : darkMode 
                            ? 'text-gray-400 group-hover:text-gray-300'
                            : 'text-gray-400 group-hover:text-gray-500'
                        } mr-3 h-5 w-5`}
                      />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>
            <UserInfo />
          </div>
        </div>
      </div>

      {/* Мобильный sidebar */}
      {isSidebarOpen && (
        <div className="lg:hidden">
          <div className="fixed inset-0 flex z-40">
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setIsSidebarOpen(false)} />
            <div className={`relative flex-1 flex flex-col max-w-xs w-full ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="absolute top-0 right-0 -mr-12 pt-2">
                <button
                  className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                  onClick={() => setIsSidebarOpen(false)}
                >
                  <X className="h-6 w-6 text-white" />
                </button>
              </div>
              <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                <div className="flex-shrink-0 flex items-center px-4">
                  <button 
                    onClick={() => {
                      navigate('/home');
                      setIsSidebarOpen(false);
                    }}
                    className="flex items-center hover:opacity-80 transition-opacity"
                  >
                    <Shield className="h-8 w-8 text-blue-600" />
                    <span className={`ml-2 text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>SIEM System</span>
                  </button>
                </div>
                <nav className="mt-8 px-2 space-y-1">
                  {menuItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <button
                        key={item.path}
                        onClick={() => {
                          navigate(item.path);
                          setIsSidebarOpen(false);
                        }}
                        className={`${
                          isActive
                            ? 'bg-blue-100 text-blue-900'
                            : darkMode 
                              ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
                              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group flex items-center px-2 py-2 text-base font-medium rounded-md w-full`}
                      >
                        <item.icon
                          className={`${
                            isActive ? 'text-blue-500' : darkMode 
                              ? 'text-gray-400 group-hover:text-gray-300'
                              : 'text-gray-400 group-hover:text-gray-500'
                          } mr-4 h-6 w-6`}
                        />
                        {item.label}
                      </button>
                    );
                  })}
                </nav>
              </div>
              <UserInfo isMobile={true} onClose={() => setIsSidebarOpen(false)} />
            </div>
          </div>
        </div>
      )}

      {/* Основное содержимое */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        <div className="lg:hidden">
          <div className={`flex items-center justify-between border-b px-4 py-3 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <div className="flex items-center">
              <button
                className={`${darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-600'}`}
                onClick={() => setIsSidebarOpen(true)}
              >
                <Menu className="h-6 w-6" />
              </button>
              <button 
                onClick={() => navigate('/home')}
                className="flex items-center hover:opacity-80 transition-opacity ml-3"
              >
                <Shield className="h-6 w-6 text-blue-600" />
                <span className={`ml-2 text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>SIEM System</span>
              </button>
            </div>
            <button
              onClick={toggleDarkMode}
              className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
            >
              {darkMode ? <Sun className="h-5 w-5 text-yellow-500" /> : <Moon className="h-5 w-5 text-gray-600" />}
            </button>
          </div>
        </div>
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;