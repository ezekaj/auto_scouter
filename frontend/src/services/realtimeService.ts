import { api } from '@/lib/api'

export interface RealtimeNotification {
  id: string
  type: 'vehicle_match' | 'system_status' | 'scraping_update' | 'alert_triggered'
  title: string
  message: string
  data?: any
  timestamp: string
  read: boolean
}

export interface SystemStatusUpdate {
  status: string
  components: {
    api: string
    database: string
    redis: string
    celery: string
    notification_system: string
  }
  scraping_active: boolean
  last_scrape: string | null
  next_scrape: string | null
}

export interface VehicleMatchUpdate {
  alert_id: number
  alert_name: string
  vehicle_id: string
  vehicle: {
    make: string
    model: string
    year: number
    price: number
    location: string
    url: string
  }
  match_score: number
  timestamp: string
}

export class RealtimeService {
  private eventSources: Map<string, EventSource> = new Map()
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  // Server-Sent Events (SSE) connections
  subscribeToNotifications(callback: (notification: RealtimeNotification) => void): () => void {
    return this.createSSEConnection('/realtime/sse/notifications', 'notifications', callback)
  }

  subscribeToSystemStatus(callback: (status: SystemStatusUpdate) => void): () => void {
    return this.createSSEConnection('/realtime/sse/system-status', 'system-status', callback)
  }

  subscribeToVehicleMatches(callback: (match: VehicleMatchUpdate) => void): () => void {
    return this.createSSEConnection('/realtime/sse/vehicle-matches', 'vehicle-matches', callback)
  }

  private createSSEConnection(endpoint: string, key: string, callback: (data: any) => void): () => void {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
    const url = `${baseURL}${endpoint}`
    
    // Close existing connection if any
    this.closeConnection(key)

    const eventSource = new EventSource(url)
    this.eventSources.set(key, eventSource)

    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set())
    }
    this.listeners.get(key)!.add(callback)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        callback(data)
      } catch (error) {
        console.error('Error parsing SSE data:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error(`SSE connection error for ${key}:`, error)
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (this.eventSources.has(key)) {
          this.createSSEConnection(endpoint, key, callback)
        }
      }, 5000)
    }

    // Return cleanup function
    return () => {
      this.listeners.get(key)?.delete(callback)
      if (this.listeners.get(key)?.size === 0) {
        this.closeConnection(key)
      }
    }
  }

  private closeConnection(key: string): void {
    const eventSource = this.eventSources.get(key)
    if (eventSource) {
      eventSource.close()
      this.eventSources.delete(key)
    }
    this.listeners.delete(key)
  }

  // Cleanup all connections
  cleanup(): void {
    for (const [key] of this.eventSources) {
      this.closeConnection(key)
    }
  }

  // Notification management
  async getNotifications(): Promise<RealtimeNotification[]> {
    try {
      const response = await api.get('/notifications/')
      return response.data || []
    } catch (error) {
      console.error('Error getting notifications:', error)
      return []
    }
  }

  async getUnreadNotifications(): Promise<RealtimeNotification[]> {
    try {
      const response = await api.get('/notifications/unread')
      return response.data || []
    } catch (error) {
      console.error('Error getting unread notifications:', error)
      return []
    }
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    try {
      await api.post(`/notifications/${notificationId}/mark-read`)
    } catch (error) {
      console.error('Error marking notification as read:', error)
      throw error
    }
  }

  async markAllNotificationsRead(): Promise<void> {
    try {
      await api.post('/notifications/mark-all-read')
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      throw error
    }
  }

  // System monitoring
  async getSystemMetrics(): Promise<any> {
    try {
      const response = await api.get('/monitoring/system/metrics')
      return response.data
    } catch (error) {
      console.error('Error getting system metrics:', error)
      return {}
    }
  }

  async getScrapingAnalytics(): Promise<any> {
    try {
      const response = await api.get('/monitoring/analytics/scraping')
      return response.data
    } catch (error) {
      console.error('Error getting scraping analytics:', error)
      return {}
    }
  }

  async getVehicleAnalytics(): Promise<any> {
    try {
      const response = await api.get('/monitoring/analytics/vehicles')
      return response.data
    } catch (error) {
      console.error('Error getting vehicle analytics:', error)
      return {}
    }
  }

  async getAlertAnalytics(): Promise<any> {
    try {
      const response = await api.get('/monitoring/analytics/alerts')
      return response.data
    } catch (error) {
      console.error('Error getting alert analytics:', error)
      return {}
    }
  }

  // Test connections
  async testNotificationSystem(): Promise<any> {
    try {
      const response = await api.post('/notifications/test')
      return response.data
    } catch (error) {
      console.error('Error testing notification system:', error)
      throw error
    }
  }
}

export const realtimeService = new RealtimeService()

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    realtimeService.cleanup()
  })
}
