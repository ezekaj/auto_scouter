import { createClient, SupabaseClient, RealtimeChannel } from '@supabase/supabase-js'

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export interface RealtimeNotification {
  id: string
  type: 'vehicle_match' | 'system_status' | 'scraping_update' | 'alert_triggered' | 'new_vehicle'
  title: string
  message: string
  data?: any
  timestamp: string
  read: boolean
}

export interface VehicleUpdate {
  id: number
  make: string
  model: string
  year?: number
  price?: number
  mileage?: number
  city?: string
  source_website: string
  created_at: string
  updated_at: string
}

export interface AlertMatch {
  alert_id: number
  vehicle_id: number
  match_score: number
  vehicle: VehicleUpdate
  alert: {
    id: number
    name: string
    criteria: any
  }
}

export class SupabaseRealtimeService {
  private supabase: SupabaseClient
  private channels: Map<string, RealtimeChannel> = new Map()
  private listeners: Map<string, Set<(data: any) => void>> = new Map()

  constructor() {
    this.supabase = createClient(supabaseUrl, supabaseAnonKey, {
      realtime: {
        params: {
          eventsPerSecond: 10
        }
      }
    })
  }

  // Subscribe to new vehicle listings
  subscribeToVehicleUpdates(callback: (vehicle: VehicleUpdate) => void): () => void {
    const channelName = 'vehicle_listings'
    
    // Remove existing channel if any
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'vehicle_listings'
        },
        (payload) => {
          console.log('🚗 New vehicle added:', payload.new)
          callback(payload.new as VehicleUpdate)
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'vehicle_listings'
        },
        (payload) => {
          console.log('🔄 Vehicle updated:', payload.new)
          callback(payload.new as VehicleUpdate)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Subscribe to alert notifications
  subscribeToAlertNotifications(callback: (notification: RealtimeNotification) => void): () => void {
    const channelName = 'notifications'
    
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications'
        },
        (payload) => {
          console.log('🔔 New notification:', payload.new)
          const notification: RealtimeNotification = {
            id: payload.new.id,
            type: payload.new.type || 'alert_triggered',
            title: payload.new.title || 'New Alert',
            message: payload.new.message || 'You have a new alert match',
            data: payload.new.data,
            timestamp: payload.new.created_at,
            read: payload.new.is_read || false
          }
          callback(notification)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Subscribe to price changes
  subscribeToPriceChanges(callback: (priceChange: any) => void): () => void {
    const channelName = 'price_history'
    
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'price_history'
        },
        (payload) => {
          console.log('💰 Price change detected:', payload.new)
          callback(payload.new)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Subscribe to scraping sessions
  subscribeToScrapingSessions(callback: (session: any) => void): () => void {
    const channelName = 'scraping_sessions'
    
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'scraping_sessions'
        },
        (payload) => {
          console.log('🔍 Scraping session update:', payload)
          callback(payload.new || payload.old)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Subscribe to favorites changes
  subscribeToFavorites(callback: (favorite: any) => void): () => void {
    const channelName = 'favorites'
    
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'favorites'
        },
        (payload) => {
          console.log('⭐ Favorites update:', payload)
          callback(payload.new || payload.old)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Subscribe to alerts changes
  subscribeToAlerts(callback: (alert: any) => void): () => void {
    const channelName = 'alerts'
    
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'alerts'
        },
        (payload) => {
          console.log('🚨 Alert update:', payload)
          callback(payload.new || payload.old)
        }
      )
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Broadcast custom events
  broadcastEvent(channel: string, event: string, payload: any): void {
    const channelInstance = this.channels.get(channel) || this.supabase.channel(channel)
    channelInstance.send({
      type: 'broadcast',
      event: event,
      payload: payload
    })
  }

  // Listen to broadcast events
  subscribeToBroadcast(channelName: string, event: string, callback: (payload: any) => void): () => void {
    this.unsubscribeFromChannel(channelName)

    const channel = this.supabase
      .channel(channelName)
      .on('broadcast', { event }, (payload) => {
        console.log(`📡 Broadcast received on ${channelName}:${event}:`, payload)
        callback(payload)
      })
      .subscribe()

    this.channels.set(channelName, channel)

    return () => this.unsubscribeFromChannel(channelName)
  }

  // Unsubscribe from a specific channel
  private unsubscribeFromChannel(channelName: string): void {
    const channel = this.channels.get(channelName)
    if (channel) {
      this.supabase.removeChannel(channel)
      this.channels.delete(channelName)
    }
  }

  // Cleanup all subscriptions
  cleanup(): void {
    console.log('🧹 Cleaning up Supabase real-time subscriptions')
    for (const [, channel] of this.channels) {
      this.supabase.removeChannel(channel)
    }
    this.channels.clear()
    this.listeners.clear()
  }

  // Get Supabase client for direct operations
  getClient(): SupabaseClient {
    return this.supabase
  }

  // Check connection status
  getConnectionStatus(): string {
    // Supabase doesn't expose connection status directly
    // We can check if we have active channels
    return this.channels.size > 0 ? 'connected' : 'disconnected'
  }
}

// Create singleton instance
export const supabaseRealtimeService = new SupabaseRealtimeService()

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    supabaseRealtimeService.cleanup()
  })
}
