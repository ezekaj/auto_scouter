/**
 * Backend Status Checker and Fallback System
 * Handles backend connectivity and provides fallback data when backend is unavailable
 */

import React from 'react'
import { api } from '@/lib/api'

export interface BackendStatus {
  isOnline: boolean
  lastChecked: Date
  error?: string
  version?: string
  environment?: string
}

class BackendStatusManager {
  private static instance: BackendStatusManager
  private status: BackendStatus = {
    isOnline: false,
    lastChecked: new Date()
  }
  private checkInterval: NodeJS.Timeout | null = null
  private listeners: ((status: BackendStatus) => void)[] = []

  static getInstance(): BackendStatusManager {
    if (!BackendStatusManager.instance) {
      BackendStatusManager.instance = new BackendStatusManager()
    }
    return BackendStatusManager.instance
  }

  async checkBackendStatus(): Promise<BackendStatus> {
    try {
      console.log('Checking backend status...')
      const response = await api.get('/health', { timeout: 5000 })
      
      this.status = {
        isOnline: true,
        lastChecked: new Date(),
        version: response.data.version,
        environment: response.data.environment
      }
      
      console.log('Backend is online:', this.status)
    } catch (error: any) {
      console.warn('Backend is offline:', error.message)
      this.status = {
        isOnline: false,
        lastChecked: new Date(),
        error: error.message
      }
    }

    // Notify listeners
    this.listeners.forEach(listener => listener(this.status))
    return this.status
  }

  getStatus(): BackendStatus {
    return this.status
  }

  onStatusChange(callback: (status: BackendStatus) => void) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback)
    }
  }

  startPeriodicCheck(intervalMs: number = 30000) {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
    }

    // Initial check
    this.checkBackendStatus()

    // Periodic checks
    this.checkInterval = setInterval(() => {
      this.checkBackendStatus()
    }, intervalMs)
  }

  stopPeriodicCheck() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
      this.checkInterval = null
    }
  }
}

// Fallback data for when backend is unavailable
export const fallbackData = {
  alerts: [
    {
      id: 1,
      name: "BMW 3 Series Alert",
      description: "Looking for a BMW 3 Series under €25,000",
      make: "BMW",
      model: "3 Series",
      max_price: 25000,
      min_year: 2018,
      is_active: true,
      notification_frequency: "daily",
      trigger_count: 0,
      max_notifications_per_day: 5,
      created_at: new Date().toISOString(),
      user_id: 1
    },
    {
      id: 2,
      name: "Electric Vehicle Alert",
      description: "Any electric vehicle in good condition",
      fuel_type: "Electric",
      condition: "good",
      is_active: false,
      notification_frequency: "immediate",
      trigger_count: 3,
      max_notifications_per_day: 10,
      created_at: new Date(Date.now() - 86400000).toISOString(),
      user_id: 1
    }
  ],
  vehicles: [
    {
      id: 1,
      make: "BMW",
      model: "3 Series",
      year: 2019,
      price: 22000,
      mileage: 45000,
      fuel_type: "Gasoline",
      transmission: "Automatic",
      location: "Tirana",
      image_url: "/placeholder-car.jpg",
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      make: "Tesla",
      model: "Model 3",
      year: 2021,
      price: 35000,
      mileage: 15000,
      fuel_type: "Electric",
      transmission: "Automatic",
      location: "Durres",
      image_url: "/placeholder-car.jpg",
      created_at: new Date().toISOString()
    }
  ]
}

// Enhanced API wrapper with fallback
export const apiWithFallback = {
  async get(url: string, config?: any) {
    const backendStatus = BackendStatusManager.getInstance().getStatus()
    
    if (!backendStatus.isOnline) {
      console.warn('Backend offline, using fallback data for:', url)
      return this.getFallbackResponse(url)
    }

    try {
      return await api.get(url, config)
    } catch (error) {
      console.warn('API call failed, using fallback data for:', url, error)
      return this.getFallbackResponse(url)
    }
  },

  async post(url: string, data?: any, config?: any) {
    const backendStatus = BackendStatusManager.getInstance().getStatus()
    
    if (!backendStatus.isOnline) {
      console.warn('Backend offline, simulating POST for:', url)
      return this.simulatePostResponse(url, data)
    }

    try {
      return await api.post(url, data, config)
    } catch (error) {
      console.warn('API POST failed, simulating response for:', url, error)
      return this.simulatePostResponse(url, data)
    }
  },

  getFallbackResponse(url: string) {
    if (url.includes('/alerts')) {
      return {
        data: {
          alerts: fallbackData.alerts,
          pagination: {
            page: 1,
            pageSize: 20,
            totalCount: fallbackData.alerts.length,
            totalPages: 1,
            hasNext: false,
            hasPrev: false
          }
        }
      }
    }

    if (url.includes('/vehicles') || url.includes('/automotive/vehicles')) {
      return {
        data: fallbackData.vehicles
      }
    }

    return { data: [] }
  },

  simulatePostResponse(url: string, data: any) {
    if (url.includes('/alerts')) {
      const newAlert = {
        id: Date.now(),
        ...data,
        user_id: 1,
        is_active: true,
        trigger_count: 0,
        created_at: new Date().toISOString()
      }
      
      fallbackData.alerts.push(newAlert)
      
      return {
        data: newAlert
      }
    }

    return { data: { success: true, message: 'Simulated response' } }
  }
}

// React hook for backend status
export const useBackendStatus = () => {
  const [status, setStatus] = React.useState<BackendStatus>(() => 
    BackendStatusManager.getInstance().getStatus()
  )

  React.useEffect(() => {
    const manager = BackendStatusManager.getInstance()
    const unsubscribe = manager.onStatusChange(setStatus)
    
    // Start periodic checking
    manager.startPeriodicCheck()
    
    return () => {
      unsubscribe()
      manager.stopPeriodicCheck()
    }
  }, [])

  return status
}

export default BackendStatusManager
