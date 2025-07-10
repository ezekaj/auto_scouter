import { api } from '@/lib/api'

export interface Vehicle {
  id: string
  title: string
  make: string
  model: string
  year: number | null
  price: number | null
  mileage: number | null
  fuelType: string
  transmission: string
  bodyType?: string
  location: string
  url: string
  imageUrl?: string
  scrapedAt: string
  source: string
}

export interface VehicleSearchParams {
  make?: string
  model?: string
  priceMin?: number
  priceMax?: number
  yearMin?: number
  yearMax?: number
  maxMileage?: number
  fuelType?: string
  transmission?: string
  bodyType?: string
  sort?: string
  page?: number
  limit?: number
}

export interface VehicleSearchResponse {
  vehicles: Vehicle[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

export class VehicleService {
  async searchVehicles(params: VehicleSearchParams = {}): Promise<VehicleSearchResponse> {
    try {
      const response = await api.get('/automotive/vehicles', { params })
      return response.data
    } catch (error) {
      console.error('Error searching vehicles:', error)
      throw error
    }
  }

  async getVehicle(id: string): Promise<Vehicle> {
    try {
      const response = await api.get(`/automotive/vehicles/${id}`)
      return response.data
    } catch (error) {
      console.error('Error getting vehicle:', error)
      throw error
    }
  }

  async getRecentVehicles(limit: number = 20): Promise<Vehicle[]> {
    try {
      const response = await api.get('/automotive/new-cars', {
        params: { limit }
      })
      return response.data || []
    } catch (error) {
      console.error('Error getting recent vehicles:', error)
      return []
    }
  }

  async getFeaturedVehicles(): Promise<Vehicle[]> {
    try {
      // Get recent vehicles with good prices as "featured"
      const response = await api.get('/automotive/vehicles', {
        params: {
          limit: 6,
          sort_by: 'price',
          sort_order: 'asc'
        }
      })
      return response.data.data || []
    } catch (error) {
      console.error('Error getting featured vehicles:', error)
      return []
    }
  }

  async getVehiclesByMake(make: string): Promise<Vehicle[]> {
    try {
      const response = await api.get('/automotive/vehicles', {
        params: {
          make,
          limit: 50
        }
      })
      return response.data.data || []
    } catch (error) {
      console.error('Error getting vehicles by make:', error)
      return []
    }
  }

  async getPopularMakes(): Promise<string[]> {
    try {
      const response = await api.get('/automotive/makes')
      return response.data || []
    } catch (error) {
      console.error('Error getting popular makes:', error)
      return []
    }
  }

  async getModelsByMake(make: string): Promise<string[]> {
    try {
      const response = await api.get('/automotive/models', {
        params: { make }
      })
      return response.data || []
    } catch (error) {
      console.error('Error getting models by make:', error)
      return []
    }
  }

  async triggerScrape(): Promise<void> {
    try {
      await api.post('/automotive/scraper/trigger')
    } catch (error) {
      console.error('Error triggering scrape:', error)
      throw error
    }
  }

  async getVehicleStats(): Promise<any> {
    try {
      const response = await api.get('/automotive/analytics')
      return response.data
    } catch (error) {
      console.error('Error getting vehicle stats:', error)
      throw error
    }
  }

  async getSavedVehicles(): Promise<Vehicle[]> {
    try {
      const response = await api.get('/cars/saved')
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting saved vehicles:', error)
      return []
    }
  }

  async getSimilarVehicles(vehicleId: string, limit: number = 5): Promise<Vehicle[]> {
    try {
      const response = await api.get(`/cars/${vehicleId}/similar`, {
        params: { limit }
      })
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting similar vehicles:', error)
      return []
    }
  }

  async getRecommendations(userId?: string): Promise<Vehicle[]> {
    try {
      const response = await api.get('/cars/recommendations', {
        params: userId ? { userId } : {}
      })
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting recommendations:', error)
      return []
    }
  }

  async getFilterOptions(): Promise<any> {
    try {
      const response = await api.get('/cars/filter-options')
      return response.data
    } catch (error) {
      console.error('Error getting filter options:', error)
      return {
        makes: await this.getPopularMakes(),
        fuelTypes: ['Gasoline', 'Diesel', 'Electric', 'Hybrid'],
        transmissions: ['Manual', 'Automatic'],
        bodyTypes: ['Sedan', 'SUV', 'Hatchback', 'Coupe', 'Wagon']
      }
    }
  }

  async saveVehicle(vehicleId: string): Promise<void> {
    try {
      await api.post(`/cars/${vehicleId}/save`)
    } catch (error) {
      console.error('Error saving vehicle:', error)
      throw error
    }
  }

  async unsaveVehicle(vehicleId: string): Promise<void> {
    try {
      await api.delete(`/cars/${vehicleId}/save`)
    } catch (error) {
      console.error('Error unsaving vehicle:', error)
      throw error
    }
  }

  async reportVehicle(vehicleId: string, reason: string, description?: string): Promise<void> {
    try {
      await api.post(`/cars/${vehicleId}/report`, {
        reason,
        description
      })
    } catch (error) {
      console.error('Error reporting vehicle:', error)
      throw error
    }
  }

  async advancedSearch(filters: VehicleSearchParams): Promise<VehicleSearchResponse> {
    try {
      const response = await api.get('/search/advanced', { params: filters })
      return response.data
    } catch (error) {
      console.error('Error performing advanced search:', error)
      throw error
    }
  }

  async exportSearchResults(params: VehicleSearchParams, format: 'csv' | 'xlsx' | 'pdf' = 'csv'): Promise<Blob> {
    try {
      const response = await api.get('/monitoring/export/data', {
        params: { ...params, format },
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Error exporting search results:', error)
      throw error
    }
  }

  async getSearchSuggestions(query: string): Promise<string[]> {
    try {
      const response = await api.get('/search/suggestions', {
        params: { q: query }
      })
      return response.data || []
    } catch (error) {
      console.error('Error getting search suggestions:', error)
      return []
    }
  }

  async getSearchFilters(): Promise<any> {
    try {
      const response = await api.get('/search/filters')
      return response.data
    } catch (error) {
      console.error('Error getting search filters:', error)
      return {
        makes: [],
        models: [],
        years: [],
        fuelTypes: [],
        transmissions: [],
        bodyTypes: []
      }
    }
  }

  async getSystemStats(): Promise<any> {
    try {
      const response = await api.get('/system/status')
      return response.data
    } catch (error) {
      console.error('Error getting system stats:', error)
      throw error
    }
  }

  async getScraperStatus(): Promise<any> {
    try {
      const response = await api.get('/automotive/scraper/status')
      return response.data
    } catch (error) {
      console.error('Error getting scraper status:', error)
      throw error
    }
  }

  async getScraperHealth(): Promise<any> {
    try {
      const response = await api.get('/automotive/scraper/health')
      return response.data
    } catch (error) {
      console.error('Error getting scraper health:', error)
      throw error
    }
  }

  async getHealthCheck(): Promise<any> {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      console.error('Error getting health check:', error)
      throw error
    }
  }

  // Enhanced methods for 24/7 backend integration
  async getDashboardOverview(): Promise<any> {
    try {
      const response = await api.get('/dashboard/overview')
      return response.data
    } catch (error) {
      console.error('Error getting dashboard overview:', error)
      return {
        total_vehicles: 0,
        recent_vehicles: 0,
        active_alerts: 0,
        new_matches: 0,
        scraping_status: 'unknown'
      }
    }
  }




  async getMultiSourceSessions(): Promise<any> {
    try {
      const response = await api.get('/automotive/multi-source-sessions')
      return response.data
    } catch (error) {
      console.error('Error getting multi-source sessions:', error)
      return []
    }
  }

  async triggerMultiSourceScrape(maxVehiclesPerSource: number = 50): Promise<any> {
    try {
      const response = await api.post('/automotive/scraper/multi-source', {
        max_vehicles_per_source: maxVehiclesPerSource
      })
      return response.data
    } catch (error) {
      console.error('Error triggering multi-source scrape:', error)
      throw error
    }
  }

  async getScraperLogs(): Promise<any> {
    try {
      const response = await api.get('/automotive/scraper/logs')
      return response.data
    } catch (error) {
      console.error('Error getting scraper logs:', error)
      return []
    }
  }

  async getAnalytics(): Promise<any> {
    try {
      const response = await api.get('/automotive/analytics')
      return response.data
    } catch (error) {
      console.error('Error getting analytics:', error)
      return {
        total_vehicles: 0,
        vehicles_by_source: {},
        price_distribution: {},
        popular_makes: []
      }
    }
  }
}

export const vehicleService = new VehicleService()
