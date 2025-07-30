import React, { createContext, useState, useContext, ReactNode, useCallback, useRef } from 'react';

interface Notification {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

interface NotificationContextType {
  notification: Notification | null;
  showNotification: (message: string, type: Notification['type']) => void;
  clearNotification: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notification, setNotification] = useState<Notification | null>(null);
  const timeoutRef = useRef<number | null>(null);

  const showNotification = useCallback((message: string, type: Notification['type']) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setNotification({ message, type });
    timeoutRef.current = setTimeout(() => {
      setNotification(null);
    }, 5000); // Auto-dismiss after 5 seconds
  }, []);

  const clearNotification = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setNotification(null);
  }, []);

  return (
    <NotificationContext.Provider value={{ notification, showNotification, clearNotification }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
