import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  priority: number;
  is_read: boolean;
  alert_id?: number;
  created_at: string;
  content_data?: any;
}

interface NotificationFilters {
  type?: string | null;
  status?: string | null;
  isRead?: boolean | null;
  dateFrom?: string | null;
  dateTo?: string | null;
  page?: number;
  pageSize?: number;
}

interface NotificationStats {
  total_notifications: number;
  unread_notifications: number;
  notifications_by_type: Record<string, number>;
  notifications_by_status: Record<string, number>;
  period_days: number;
}

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });

  const fetchNotifications = useCallback(async (filters: NotificationFilters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (filters.type) params.append('notification_type', filters.type);
      if (filters.status) params.append('status', filters.status);
      if (filters.isRead !== undefined && filters.isRead !== null) params.append('is_read', filters.isRead.toString());
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.pageSize) params.append('page_size', filters.pageSize.toString());

      const response = await api.get(`/notifications/?${params.toString()}`);
      
      setNotifications(response.data.notifications);
      setPagination(response.data.pagination);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchUnreadNotifications = useCallback(async (limit: number = 50) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/notifications/unread?limit=${limit}`);
      setNotifications(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch unread notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      await api.get('/notifications/unread?limit=1');
      // This is a simple way to get count - in production you'd want a dedicated endpoint
      const fullResponse = await api.get('/notifications/unread?limit=1000');
      setUnreadCount(fullResponse.data.length);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  }, []);

  const markAsRead = useCallback(async (notificationId: number) => {
    try {
      await api.patch(`/notifications/${notificationId}/read`);
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          notification.id === notificationId 
            ? { ...notification, is_read: true }
            : notification
        )
      );
      
      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to mark notification as read');
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.patch('/notifications/mark-all-read');
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => ({ ...notification, is_read: true }))
      );
      
      setUnreadCount(0);
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to mark all notifications as read');
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId: number) => {
    try {
      await api.delete(`/notifications/${notificationId}`);
      
      // Update local state
      const deletedNotification = notifications.find(n => n.id === notificationId);
      setNotifications(prev => prev.filter(notification => notification.id !== notificationId));
      
      // Update unread count if the deleted notification was unread
      if (deletedNotification && !deletedNotification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to delete notification');
    }
  }, [notifications]);

  const resendNotification = useCallback(async (notificationId: number) => {
    try {
      await api.post(`/notifications/${notificationId}/resend`);
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to resend notification');
    }
  }, []);

  const getNotificationStats = useCallback(async (days: number = 30): Promise<NotificationStats> => {
    try {
      const response = await api.get(`/notifications/stats?days=${days}`);
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to fetch notification stats');
    }
  }, []);

  const sendTestNotification = useCallback(async (type: string = 'email') => {
    try {
      const response = await api.post('/notifications/test', {
        notification_type: type
      });
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to send test notification');
    }
  }, []);

  // Auto-refresh unread count periodically
  useEffect(() => {
    fetchUnreadCount();
    
    const interval = setInterval(fetchUnreadCount, 30000); // Every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // WebSocket connection for real-time notifications (optional)
  useEffect(() => {
    // WebSocket implementation for real-time notifications
    if (import.meta.env.VITE_ENABLE_WEBSOCKET !== 'false') {
      try {
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/notifications';
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected for notifications');
        };

        ws.onmessage = (event) => {
          try {
            const notification = JSON.parse(event.data);
            setNotifications(prev => [notification, ...prev]);
            setUnreadCount(prev => prev + 1);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket connection closed');
        };

        return () => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        };
      } catch (error) {
        console.error('Failed to establish WebSocket connection:', error);
      }
    }
  }, []);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    pagination,
    fetchNotifications,
    fetchUnreadNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    resendNotification,
    getNotificationStats,
    sendTestNotification
  };
};
