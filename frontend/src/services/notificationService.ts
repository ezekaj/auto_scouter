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
      const response = await api.get('/notifications', { params })
      return response.data
    } catch (error) {
      console.error('Error getting notifications:', error)
      throw error
    }
  }

  async markAsRead(id: string): Promise<void> {
    try {
      await api.put(`/notifications/${id}/read`)
    } catch (error) {
      console.error('Error marking notification as read:', error)
      throw error
    }
  }

  async markAllAsRead(): Promise<void> {
    try {
      await api.put('/notifications/read-all')
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

}


export const notificationService = new NotificationService()
