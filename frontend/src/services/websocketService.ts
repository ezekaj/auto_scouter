import { config } from '@/config/production'

export interface WebSocketMessage {
  type: string
  data: any
}

export interface NotificationData {
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

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private listeners: Map<string, Set<Function>> = new Map()
  private isConnecting = false
  private shouldReconnect = true

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        // Wait for current connection attempt
        const checkConnection = () => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            resolve()
          } else if (!this.isConnecting) {
            reject(new Error('Connection failed'))
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
        return
      }

      this.isConnecting = true

      try {
        // Connecting to WebSocket
        this.ws = new WebSocket(config.wsBaseUrl)

        this.ws.onopen = () => {
          // WebSocket connected
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.emit('connected', null)
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          // WebSocket disconnected
          this.isConnecting = false
          this.ws = null
          this.emit('disconnected', { code: event.code, reason: event.reason })

          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnecting = false
          this.emit('error', error)
          reject(error)
        }

      } catch (error) {
        this.isConnecting = false
        console.error('Failed to create WebSocket connection:', error)
        reject(error)
      }
    })
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private scheduleReconnect() {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    // Scheduling reconnect attempt
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch(error => {
          console.error('Reconnect failed:', error)
        })
      }
    }, delay)
  }

  private handleMessage(message: WebSocketMessage) {
    // WebSocket message received
    
    switch (message.type) {
      case 'new_notification':
        this.handleNewNotification(message.data)
        break
      case 'notification_read':
        this.emit('notification_read', message.data)
        break
      case 'all_notifications_read':
        this.emit('all_notifications_read', message.data)
        break
      case 'notification_deleted':
        this.emit('notification_deleted', message.data)
        break
      case 'browser_notification':
        this.showBrowserNotification(message.data)
        break
      case 'initial_notifications':
        this.emit('initial_notifications', message.data)
        break
      case 'pong':
        // Handle ping/pong for connection health
        break
      default:
        this.emit(message.type, message.data)
    }
  }

  private handleNewNotification(notification: NotificationData) {
    this.emit('new_notification', notification)
    
    // Show browser notification for high priority notifications
    if (notification.priority === 'high') {
      this.showBrowserNotification({
        title: notification.title,
        message: notification.message,
        icon: '/icons/car-notification.png',
        tag: notification.type,
        data: notification.data
      })
    }
  }

  private showBrowserNotification(data: any) {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(data.title, {
        body: data.message,
        icon: data.icon,
        tag: data.tag,
        data: data.data,
        requireInteraction: true
      })

      notification.onclick = () => {
        window.focus()
        notification.close()
        
        // Navigate to relevant page based on notification type
        if (data.data?.vehicle?.url) {
          window.open(data.data.vehicle.url, '_blank')
        }
      }

      // Auto-close after 10 seconds
      setTimeout(() => {
        notification.close()
      }, 10000)
    }
  }

  send(message: WebSocketMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback: Function) {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.delete(callback)
    }
  }

  private emit(event: string, data: any) {
    const eventListeners = this.listeners.get(event)
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('Error in WebSocket event callback:', error)
        }
      })
    }
  }

  // Utility methods
  markNotificationAsRead(notificationId: string) {
    this.send({
      type: 'mark_read',
      data: { notificationId }
    })
  }

  markAllNotificationsAsRead() {
    this.send({
      type: 'mark_all_read',
      data: {}
    })
  }

  ping() {
    this.send({
      type: 'ping',
      data: {}
    })
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting'
      case WebSocket.OPEN: return 'connected'
      case WebSocket.CLOSING: return 'closing'
      case WebSocket.CLOSED: return 'disconnected'
      default: return 'unknown'
    }
  }
}

// Create singleton instance
export const websocketService = new WebSocketService()

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission().then(permission => {
    // Notification permission handled
  })
}
