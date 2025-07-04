import { api } from '@/lib/api'

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  data: any
  isRead: boolean
  createdAt: string
  priority: 'low' | 'medium' | 'high'
  actions: Array<{
    type: string
    label: string
    url: string
  }>
}

export interface NotificationResponse {
  notifications: Notification[]
  unreadCount: number
  total: number
}
export class NotificationService {
  async getNotifications(params: {
    limit?: number
    offset?: number
    type?: string
  } = {}): Promise<NotificationResponse> {
    try {
      const response = await api.get('/notifications/', { params })
      return {
        notifications: response.data.notifications || [],
        unreadCount: response.data.unread_count || 0,
        total: response.data.total || 0
      }
    } catch (error) {
      console.error('Error getting notifications:', error)
      return {
        notifications: [],
        unreadCount: 0,
        total: 0
      }
    }
  }

  async markAsRead(id: string): Promise<void> {
    try {
      await api.patch(`/notifications/${id}/read`)
    } catch (error) {
      console.error('Error marking notification as read:', error)
      throw error
    }
  }

  async markAllAsRead(): Promise<void> {
    try {
      await api.patch('/notifications/mark-all-read')
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      throw error
    }
  }

  async deleteNotification(id: string): Promise<void> {
    try {
      await api.delete(`/notifications/${id}`)
    } catch (error) {
      console.error('Error deleting notification:', error)
      throw error
    }
  }

  async getNotificationStats(): Promise<any> {
    try {
      const response = await api.get('/notifications/stats')
      return response.data
    } catch (error) {
      console.error('Error getting notification stats:', error)
      return {
        total: 0,
        unread: 0,
        by_type: {},
        by_priority: {}
      }
    }
  }

  // Utility methods
  getNotificationIcon(type: string): string {
    switch (type) {
      case 'alert_match':
        return '🎯'
      case 'system':
        return '⚙️'
      case 'scraper':
        return '🔍'
      case 'price_change':
        return '💰'
      case 'new_listing':
        return '🆕'
      default:
        return 'ℹ️'
    }
  }

  formatNotificationTime(createdAt: string): string {
    const now = new Date()
    const created = new Date(createdAt)
    const diffInMinutes = Math.floor((now.getTime() - created.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`

    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}h ago`

    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 7) return `${diffInDays}d ago`

    return created.toLocaleDateString()
  }
}


export const notificationService = new NotificationService()
