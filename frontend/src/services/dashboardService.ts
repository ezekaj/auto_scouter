import { api } from '@/lib/api'
import { vehicleAPI } from '@/lib/supabase'

export interface DashboardStats {
  activeAlerts: number
  newMatches: number
  unreadNotifications: number
  vehiclesViewed: number
  recentActivity: RecentActivity[]
}

export interface RecentActivity {
  id: number
  type: 'vehicle_match' | 'alert_created' | 'vehicle_viewed' | 'alert_triggered'
  title: string
  description: string
  timestamp: string
  vehicleId?: string
  alertId?: string
}

export class DashboardService {
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      // Use Supabase stats endpoint
      const response = await vehicleAPI.getStats()
      return {
        activeAlerts: response.total_alerts || 0,
        newMatches: 0, // Will be calculated from recent notifications
        unreadNotifications: 0, // Will be fetched separately
        vehiclesViewed: response.total_vehicles || 0,
        recentActivity: []
      }
    } catch (error) {
      console.error('Error getting dashboard stats:', error)
      // Return fallback data
      return {
        activeAlerts: 0,
        newMatches: 0,
        unreadNotifications: 0,
        vehiclesViewed: 0,
        recentActivity: []
      }
    }
  }

  async getVehicleStats(): Promise<any> {
    try {
      const response = await api.get('/cars/stats/summary')
      return response.data
    } catch (error) {
      console.error('Error getting vehicle stats:', error)
      return {
        total: 0,
        averagePrice: 0,
        priceRange: { min: 0, max: 0 },
        popularMakes: []
      }
    }
  }

  async getSystemHealth(): Promise<any> {
    try {
      const response = await api.get('/dashboard/system-health')
      return response.data
    } catch (error) {
      console.error('Error getting system health:', error)
      return {
        status: 'unknown',
        components: {},
        uptime: 0
      }
    }
  }

  async getAnalytics(): Promise<any> {
    try {
      const response = await api.get('/dashboard/analytics')
      return response.data
    } catch (error) {
      console.error('Error getting analytics:', error)
      return {
        scraping_stats: {},
        vehicle_trends: {},
        alert_performance: {}
      }
    }
  }

  async getMonitoringDashboard(): Promise<any> {
    try {
      const response = await api.get('/monitoring/dashboard')
      return response.data
    } catch (error) {
      console.error('Error getting monitoring dashboard:', error)
      return {
        system_metrics: {},
        scraping_health: {},
        alert_stats: {}
      }
    }
  }
}

export const dashboardService = new DashboardService()
