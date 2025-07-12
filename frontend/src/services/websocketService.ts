// WebSocket service disabled - using Supabase real-time instead

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
  private listeners: Map<string, Set<Function>> = new Map()

  connect(): Promise<void> {
    console.log('WebSocket service disabled - using Supabase real-time')
    return Promise.resolve()
  }

  disconnect() {
    console.log('WebSocket disconnect called - using Supabase real-time')
  }

  send(message: WebSocketMessage) {
    console.log('WebSocket send called - using Supabase real-time', message)
  }

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



  static getInstance(): WebSocketService {
    return new WebSocketService()
  }
}

export const websocketService = WebSocketService.getInstance()
