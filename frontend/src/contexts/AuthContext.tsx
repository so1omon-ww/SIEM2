import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest, RegisterRequest, AuthContextType } from '../types';
import { authApi } from '../services/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Проверяем сохраненный токен при загрузке
    const token = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('user');
    const savedApiKey = localStorage.getItem('api_key');

    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        
        if (savedApiKey) {
          setApiKey(savedApiKey);
        } else {
          // Если нет сохраненного API ключа, попробуем загрузить существующий
          loadExistingApiKey(userData.username);
        }
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('api_key');
      }
    }
    setIsLoading(false);
  }, []);

  const loadExistingApiKey = async (username: string) => {
    try {
      const response = await authApi.getCurrentApiKey(username);
      // Если получили API ключ, сохраняем его
      if (response.token) {
        localStorage.setItem('api_key', response.token);
        setApiKey(response.token);
        console.log('API key loaded successfully');
      }
    } catch (error) {
      // API ключ не найден - попробуем сгенерировать новый
      console.log('No existing API key found, generating new one...');
      try {
        const newKeyResponse = await authApi.generateApiKey(username);
        if (newKeyResponse.token) {
          localStorage.setItem('api_key', newKeyResponse.token);
          setApiKey(newKeyResponse.token);
          console.log('New API key generated successfully');
        }
      } catch (genError) {
        console.error('Failed to generate API key:', genError);
      }
    }
  };

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials);
      localStorage.setItem('auth_token', response.access_token);
      
      // Создаем базовый объект пользователя (в реальном проекте эти данные должны приходить с сервера)
      const userData: User = {
        id: 1, // В реальном проекте это должно приходить с сервера
        username: credentials.username,
        role: 'user',
        created_at: new Date().toISOString()
      };
      
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      // Загружаем API ключ после успешного входа
      try {
        await loadExistingApiKey(credentials.username);
      } catch (error) {
        console.error('Failed to load API key:', error);
        // Продолжаем работу даже если не удалось загрузить API ключ
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (data: RegisterRequest) => {
    try {
      const response = await authApi.register(data);
      
      // Если сервер вернул API ключ, сохраняем его
      if (response.api_key) {
        localStorage.setItem('api_key', response.api_key);
        setApiKey(response.api_key);
        console.log('API key received from registration:', response.api_key);
      }
      
      // Автоматически логинимся после регистрации
      await login(data);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const generateApiKey = async (): Promise<string> => {
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    try {
      const response = await authApi.generateApiKey(user.username);
      localStorage.setItem('api_key', response.token);
      setApiKey(response.token);
      return response.token;
    } catch (error) {
      console.error('API key generation error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    localStorage.removeItem('api_key');
    setUser(null);
    setApiKey(null);
  };

  const value: AuthContextType = {
    user,
    apiKey,
    login,
    register,
    logout,
    generateApiKey,
    isAuthenticated: !!user
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};