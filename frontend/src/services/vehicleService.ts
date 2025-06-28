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
      const response = await api.get('/cars', { params })
      return response.data
    } catch (error) {
      console.error('Error searching vehicles:', error)
      throw error
    }
  }

  async getVehicle(id: string): Promise<Vehicle> {
    try {
      const response = await api.get(`/cars/${id}`)
      return response.data
    } catch (error) {
      console.error('Error getting vehicle:', error)
      throw error
    }
  }

  async getRecentVehicles(limit: number = 20): Promise<Vehicle[]> {
    try {
      const response = await api.get('/cars', {
        params: {
          limit,
          sort: 'newest'
        }
      })
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting recent vehicles:', error)
      return []
    }
  }

  async getFeaturedVehicles(): Promise<Vehicle[]> {
    try {
      // Get recent vehicles with good prices as "featured"
      const response = await api.get('/cars', {
        params: {
          limit: 6,
          sort: 'price_asc'
        }
      })
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting featured vehicles:', error)
      return []
    }
  }

  async getVehiclesByMake(make: string): Promise<Vehicle[]> {
    try {
      const response = await api.get('/cars', {
        params: {
          make,
          limit: 50
        }
      })
      return response.data.vehicles || []
    } catch (error) {
      console.error('Error getting vehicles by make:', error)
      return []
    }
  }

  async getPopularMakes(): Promise<string[]> {
    try {
      // Return common Italian car makes based on Gruppo Auto Uno inventory
      return [
        'Volkswagen',
        'Peugeot',
        'Citroën',
        'Opel',
        'BMW',
        'Audi',
        'Mercedes-Benz',
        'Fiat',
        'Ford',
        'Renault',
        'Toyota',
        'Honda',
        'Jeep',
        'Mini'
      ]
    } catch (error) {
      console.error('Error getting popular makes:', error)
      return []
    }
  }

  async getModelsByMake(make: string): Promise<string[]> {
    try {
      // Get vehicles by make and extract unique models
      const vehicles = await this.getVehiclesByMake(make)
      const models = [...new Set(vehicles.map(v => v.model).filter(Boolean))]
      return models.sort()
    } catch (error) {
      console.error('Error getting models by make:', error)
      return []
    }
  }

  async triggerScrape(): Promise<void> {
    try {
      await api.post('/scrape')
    } catch (error) {
      console.error('Error triggering scrape:', error)
      throw error
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
      const response = await api.post('/cars/search', filters)
      return response.data
    } catch (error) {
      console.error('Error performing advanced search:', error)
      throw error
    }
  }

  async exportSearchResults(params: VehicleSearchParams, format: 'csv' | 'xlsx' | 'pdf' = 'csv'): Promise<Blob> {
    try {
      const response = await api.post('/cars/export', {
        ...params,
        format
      }, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Error exporting search results:', error)
      throw error
    }
  }

  async getSystemStats(): Promise<any> {
    try {
      const response = await api.get('/stats')
      return response.data
    } catch (error) {
      console.error('Error getting system stats:', error)
      throw error
    }
  }
}

export const vehicleService = new VehicleService()
