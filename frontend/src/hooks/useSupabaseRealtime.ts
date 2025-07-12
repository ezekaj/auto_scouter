import { useEffect, useState, useCallback } from 'react'
import { supabaseRealtimeService, RealtimeNotification, VehicleUpdate } from '@/services/supabaseRealtimeService'

// Hook for vehicle updates
export const useVehicleUpdates = () => {
  const [vehicles, setVehicles] = useState<VehicleUpdate[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('🔌 Setting up vehicle updates subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToVehicleUpdates((vehicle) => {
      console.log('🚗 New vehicle received:', vehicle)
      setVehicles(prev => [vehicle, ...prev.slice(0, 49)]) // Keep last 50 vehicles
    })

    return () => {
      console.log('🔌 Cleaning up vehicle updates subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [])

  const clearVehicles = useCallback(() => {
    setVehicles([])
  }, [])

  return {
    vehicles,
    isConnected,
    clearVehicles
  }
}

// Hook for alert notifications
export const useAlertNotifications = () => {
  const [notifications, setNotifications] = useState<RealtimeNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('🔔 Setting up alert notifications subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToAlertNotifications((notification) => {
      console.log('🔔 New notification received:', notification)
      setNotifications(prev => [notification, ...prev.slice(0, 99)]) // Keep last 100 notifications
      
      if (!notification.read) {
        setUnreadCount(prev => prev + 1)
      }

      // Show browser notification if permission granted
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/icon-192x192.png',
          tag: notification.id,
          requireInteraction: true
        })
      }
    })

    return () => {
      console.log('🔔 Cleaning up alert notifications subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [])

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev => 
      prev.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      )
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    setUnreadCount(0)
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    clearNotifications
  }
}

// Hook for price changes
export const usePriceChanges = () => {
  const [priceChanges, setPriceChanges] = useState<any[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('💰 Setting up price changes subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToPriceChanges((priceChange) => {
      console.log('💰 Price change received:', priceChange)
      setPriceChanges(prev => [priceChange, ...prev.slice(0, 49)]) // Keep last 50 price changes
    })

    return () => {
      console.log('💰 Cleaning up price changes subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [])

  const clearPriceChanges = useCallback(() => {
    setPriceChanges([])
  }, [])

  return {
    priceChanges,
    isConnected,
    clearPriceChanges
  }
}

// Hook for scraping sessions
export const useScrapingSessions = () => {
  const [sessions, setSessions] = useState<any[]>([])
  const [currentSession, setCurrentSession] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('🔍 Setting up scraping sessions subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToScrapingSessions((session) => {
      console.log('🔍 Scraping session update:', session)
      
      setSessions(prev => {
        const existingIndex = prev.findIndex(s => s.id === session.id)
        if (existingIndex >= 0) {
          // Update existing session
          const updated = [...prev]
          updated[existingIndex] = session
          return updated
        } else {
          // Add new session
          return [session, ...prev.slice(0, 19)] // Keep last 20 sessions
        }
      })

      // Update current session if it's running
      if (session.status === 'running') {
        setCurrentSession(session)
      } else if (currentSession?.id === session.id) {
        setCurrentSession(null)
      }
    })

    return () => {
      console.log('🔍 Cleaning up scraping sessions subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [currentSession])

  const clearSessions = useCallback(() => {
    setSessions([])
    setCurrentSession(null)
  }, [])

  return {
    sessions,
    currentSession,
    isConnected,
    clearSessions
  }
}

// Hook for favorites
export const useFavorites = () => {
  const [favorites, setFavorites] = useState<any[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('⭐ Setting up favorites subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToFavorites((favorite) => {
      console.log('⭐ Favorites update:', favorite)
      
      // Handle different event types
      if (favorite.eventType === 'DELETE') {
        setFavorites(prev => prev.filter(f => f.id !== favorite.old?.id))
      } else {
        setFavorites(prev => {
          const existingIndex = prev.findIndex(f => f.id === favorite.id)
          if (existingIndex >= 0) {
            // Update existing favorite
            const updated = [...prev]
            updated[existingIndex] = favorite
            return updated
          } else {
            // Add new favorite
            return [favorite, ...prev]
          }
        })
      }
    })

    return () => {
      console.log('⭐ Cleaning up favorites subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [])

  const clearFavorites = useCallback(() => {
    setFavorites([])
  }, [])

  return {
    favorites,
    isConnected,
    clearFavorites
  }
}

// Hook for alerts
export const useAlerts = () => {
  const [alerts, setAlerts] = useState<any[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    console.log('🚨 Setting up alerts subscription')
    setIsConnected(true)

    const unsubscribe = supabaseRealtimeService.subscribeToAlerts((alert) => {
      console.log('🚨 Alert update:', alert)
      
      // Handle different event types
      if (alert.eventType === 'DELETE') {
        setAlerts(prev => prev.filter(a => a.id !== alert.old?.id))
      } else {
        setAlerts(prev => {
          const existingIndex = prev.findIndex(a => a.id === alert.id)
          if (existingIndex >= 0) {
            // Update existing alert
            const updated = [...prev]
            updated[existingIndex] = alert
            return updated
          } else {
            // Add new alert
            return [alert, ...prev]
          }
        })
      }
    })

    return () => {
      console.log('🚨 Cleaning up alerts subscription')
      setIsConnected(false)
      unsubscribe()
    }
  }, [])

  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  return {
    alerts,
    isConnected,
    clearAlerts
  }
}

// Combined hook for all real-time features
export const useSupabaseRealtime = () => {
  const vehicleUpdates = useVehicleUpdates()
  const alertNotifications = useAlertNotifications()
  const priceChanges = usePriceChanges()
  const scrapingSessions = useScrapingSessions()
  const favorites = useFavorites()
  const alerts = useAlerts()

  const isConnected = vehicleUpdates.isConnected || 
                     alertNotifications.isConnected || 
                     priceChanges.isConnected || 
                     scrapingSessions.isConnected ||
                     favorites.isConnected ||
                     alerts.isConnected

  const cleanup = useCallback(() => {
    vehicleUpdates.clearVehicles()
    alertNotifications.clearNotifications()
    priceChanges.clearPriceChanges()
    scrapingSessions.clearSessions()
    favorites.clearFavorites()
    alerts.clearAlerts()
    supabaseRealtimeService.cleanup()
  }, [
    vehicleUpdates.clearVehicles,
    alertNotifications.clearNotifications,
    priceChanges.clearPriceChanges,
    scrapingSessions.clearSessions,
    favorites.clearFavorites,
    alerts.clearAlerts
  ])

  return {
    vehicleUpdates,
    alertNotifications,
    priceChanges,
    scrapingSessions,
    favorites,
    alerts,
    isConnected,
    cleanup
  }
}
