import { api } from '@/lib/api'

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
      const response = await api.get('/dashboard/stats')
      return response.data
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
      const response = await api.get('/cars/stats')
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
}

export const dashboardService = new DashboardService()
