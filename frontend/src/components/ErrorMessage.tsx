import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="flex items-center space-x-2 text-red-600 mb-4">
        <AlertCircle className="h-8 w-8" />
        <span className="text-lg font-medium">Ошибка</span>
      </div>
      <p className="text-gray-600 text-center mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-siem-primary text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-siem-primary focus:ring-offset-2"
        >
          Попробовать снова
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
