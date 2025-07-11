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

// No fallback data - production mode requires live backend

// Production API wrapper - no fallback, direct API calls only
export const productionApi = {
  async get(url: string, config?: any) {
    return await api.get(url, config)
  },

  async post(url: string, data?: any, config?: any) {
    return await api.post(url, data, config)
  },

  async put(url: string, data?: any, config?: any) {
    return await api.put(url, data, config)
  },

  async delete(url: string, config?: any) {
    return await api.delete(url, config)
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
