import { api } from '@/lib/api'

export interface Alert {
  id: number
  user_id?: number
  name: string
  description?: string
  make?: string
  model?: string
  min_price?: number
  max_price?: number
  min_year?: number
  max_year?: number
  max_mileage?: number
  fuel_type?: string
  transmission?: string
  body_type?: string
  city?: string
  region?: string
  location_radius?: number
  min_engine_power?: number
  max_engine_power?: number
  condition?: string
  is_active: boolean
  notification_frequency: string
  last_triggered?: string
  trigger_count: number
  max_notifications_per_day: number
  created_at: string
  updated_at?: string
}

export interface AlertCreateData {
  name: string
  description?: string
  make?: string
  model?: string
  min_price?: number
  max_price?: number
  min_year?: number
  max_year?: number
  max_mileage?: number
  fuel_type?: string
  transmission?: string
  body_type?: string
  city?: string
  region?: string
  location_radius?: number
  min_engine_power?: number
  max_engine_power?: number
  condition?: string
  is_active?: boolean
  notification_frequency?: string
  max_notifications_per_day?: number
}

export interface AlertMatch {
  matchPercentage: number
  vehicle: any
  matchDetails: any
  isMatch: boolean
}

export class AlertService {
  async getAlerts(): Promise<Alert[]> {
    try {
      const response = await api.get('/alerts/')
      return response.data || []
    } catch (error) {
      console.error('Error getting alerts:', error)
      return []
    }
  }

  async getAlert(id: number): Promise<Alert> {
    try {
      const response = await api.get(`/alerts/${id}`)
      return response.data
    } catch (error) {
      console.error('Error getting alert:', error)
      throw error
    }
  }

  async createAlert(data: AlertCreateData): Promise<Alert> {
    try {
      const response = await api.post('/alerts/', data)
      return response.data
    } catch (error) {
      console.error('Error creating alert:', error)
      throw error
    }
  }

  async updateAlert(id: number, data: Partial<AlertCreateData>): Promise<Alert> {
    try {
      const response = await api.put(`/alerts/${id}`, data)
      return response.data
    } catch (error) {
      console.error('Error updating alert:', error)
      throw error
    }
  }

  async deleteAlert(id: number): Promise<void> {
    try {
      await api.delete(`/alerts/${id}`)
    } catch (error) {
      console.error('Error deleting alert:', error)
      throw error
    }
  }

  async toggleAlert(id: number): Promise<Alert> {
    try {
      const response = await api.post(`/alerts/${id}/toggle`)
      return response.data
    } catch (error) {
      console.error('Error toggling alert:', error)
      throw error
    }
  }

  async testAlert(id: number): Promise<any> {
    try {
      const response = await api.post(`/alerts/${id}/test`)
      return response.data
    } catch (error) {
      console.error('Error testing alert:', error)
      throw error
    }
  }

  async getAlertStats(id: number): Promise<any> {
    try {
      const response = await api.get(`/alerts/${id}/stats`)
      return response.data
    } catch (error) {
      console.error('Error getting alert stats:', error)
      return {}
    }
  }

  async getAlertsSummary(): Promise<any> {
    try {
      const response = await api.get('/alerts/stats/summary')
      return response.data
    } catch (error) {
      console.error('Error getting alerts summary:', error)
      return {
        total_alerts: 0,
        active_alerts: 0,
        total_matches: 0,
        recent_matches: 0
      }
    }
  }

  async checkAlert(id: number): Promise<{ alert: Alert; matches: AlertMatch[]; totalMatches: number }> {
    try {
      const response = await api.post(`/alerts/${id}/test`)
      return response.data
    } catch (error) {
      console.error('Error checking alert:', error)
      throw error
    }
  }

}

export const alertService = new AlertService()
