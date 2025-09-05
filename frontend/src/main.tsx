import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './App.css'
import { ThemeProvider } from './contexts/ThemeContext'

// Автоматическая установка API ключа для демонстрации
const setupApiKey = () => {
  const existingKey = localStorage.getItem('api_key');
  if (!existingKey) {
    // Устанавливаем демонстрационный API ключ
    localStorage.setItem('api_key', '690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb');
    console.log('🔑 API ключ автоматически установлен для демонстрации');
  }
};

// Устанавливаем API ключ при загрузке приложения
setupApiKey();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)
