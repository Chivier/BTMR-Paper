import React from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { useNotification } from '@/context/NotificationContext';

const Banner: React.FC = () => {
  const { notification, clearNotification } = useNotification();

  if (!notification) {
    return null;
  }

  const getIconAndStyles = (type: string) => {
    switch (type) {
      case 'error':
        return {
          icon: AlertCircle,
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-800',
          iconColor: 'text-red-400',
        };
      case 'success':
        return {
          icon: CheckCircle,
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
          iconColor: 'text-green-400',
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-400',
        };
      case 'info':
      default:
        return {
          icon: Info,
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-800',
          iconColor: 'text-blue-400',
        };
    }
  };

  const { icon: Icon, bgColor, borderColor, textColor, iconColor } = getIconAndStyles(notification.type);

  return (
    <div className={`rounded-md border ${bgColor} ${borderColor} p-4 mb-4`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={`h-5 w-5 ${iconColor}`} aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <p className={`text-sm ${textColor}`}>{notification.message}</p>
        </div>
        <div className="ml-auto pl-3">
          <div className="-mx-1.5 -my-1.5">
            <button
              type="button"
              className={`inline-flex rounded-md ${bgColor} p-1.5 ${textColor} hover:${bgColor} focus:outline-none focus:ring-2 focus:ring-offset-2`}
              onClick={clearNotification}
            >
              <span className="sr-only">Dismiss</span>
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Banner;
