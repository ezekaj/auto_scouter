import { api } from '@/lib/api'

export interface SavedSearch {
  id: string
  user_id?: string
  name: string
  description?: string
  search_term?: string
  filters: SearchFilters
  results_count: number
  created_at: string
  updated_at?: string
  last_used?: string
  is_favorite: boolean
  is_active: boolean
  notification_enabled: boolean
}

export interface SearchFilters {
  make?: string
  model?: string
  min_price?: number
  max_price?: number
  min_year?: number
  max_year?: number
  max_mileage?: number
  fuel_type?: string[]
  transmission?: string[]
  body_type?: string[]
  location?: string
  radius?: number
  condition?: string
  keywords?: string[]
}

export interface SavedSearchCreateData {
  name: string
  description?: string
  search_term?: string
  filters: SearchFilters
  is_favorite?: boolean
  notification_enabled?: boolean
}

export interface SavedSearchStats {
  total_searches: number
  favorite_searches: number
  active_searches: number
  total_results: number
  avg_results_per_search: number
}

export class SavedSearchService {
  // CRUD operations
  async getSavedSearches(): Promise<SavedSearch[]> {
    try {
      const response = await api.get('/search/saved')
      return response.data || []
    } catch (error) {
      console.error('Error getting saved searches:', error)
      return []
    }
  }

  async getSavedSearch(searchId: string): Promise<SavedSearch | null> {
    try {
      const response = await api.get(`/search/saved/${searchId}`)
      return response.data
    } catch (error) {
      console.error('Error getting saved search:', error)
      return null
    }
  }

  async createSavedSearch(searchData: SavedSearchCreateData): Promise<SavedSearch> {
    try {
      const response = await api.post('/search/saved', searchData)
      return response.data
    } catch (error) {
      console.error('Error creating saved search:', error)
      throw error
    }
  }

  async updateSavedSearch(searchId: string, searchData: Partial<SavedSearchCreateData>): Promise<SavedSearch> {
    try {
      const response = await api.put(`/search/saved/${searchId}`, searchData)
      return response.data
    } catch (error) {
      console.error('Error updating saved search:', error)
      throw error
    }
  }

  async deleteSavedSearch(searchId: string): Promise<void> {
    try {
      await api.delete(`/search/saved/${searchId}`)
    } catch (error) {
      console.error('Error deleting saved search:', error)
      throw error
    }
  }

  // Favorite management
  async toggleFavorite(searchId: string): Promise<SavedSearch> {
    try {
      const response = await api.post(`/search/saved/${searchId}/favorite`)
      return response.data
    } catch (error) {
      console.error('Error toggling favorite:', error)
      throw error
    }
  }

  // Search execution
  async executeSearch(searchId: string): Promise<any> {
    try {
      const response = await api.post(`/search/saved/${searchId}/execute`)
      
      // Update last_used timestamp
      await this.updateLastUsed(searchId)
      
      return response.data
    } catch (error) {
      console.error('Error executing saved search:', error)
      throw error
    }
  }

  async updateLastUsed(searchId: string): Promise<void> {
    try {
      await api.patch(`/search/saved/${searchId}/last-used`)
    } catch (error) {
      console.error('Error updating last used:', error)
      // Don't throw error for this non-critical operation
    }
  }

  // Statistics
  async getSavedSearchStats(): Promise<SavedSearchStats> {
    try {
      const response = await api.get('/search/saved/stats')
      return response.data
    } catch (error) {
      console.error('Error getting saved search stats:', error)
      return {
        total_searches: 0,
        favorite_searches: 0,
        active_searches: 0,
        total_results: 0,
        avg_results_per_search: 0
      }
    }
  }

  // Utility methods
  formatSearchFilters(filters: SearchFilters): string {
    const parts: string[] = []

    if (filters.make) parts.push(`Make: ${filters.make}`)
    if (filters.model) parts.push(`Model: ${filters.model}`)
    if (filters.min_price || filters.max_price) {
      const priceRange = [
        filters.min_price ? `€${filters.min_price.toLocaleString()}` : '',
        filters.max_price ? `€${filters.max_price.toLocaleString()}` : ''
      ].filter(Boolean).join(' - ')
      parts.push(`Price: ${priceRange}`)
    }
    if (filters.min_year || filters.max_year) {
      const yearRange = [filters.min_year, filters.max_year].filter(Boolean).join(' - ')
      parts.push(`Year: ${yearRange}`)
    }
    if (filters.max_mileage) parts.push(`Max Mileage: ${filters.max_mileage.toLocaleString()} km`)
    if (filters.fuel_type?.length) parts.push(`Fuel: ${filters.fuel_type.join(', ')}`)
    if (filters.transmission?.length) parts.push(`Transmission: ${filters.transmission.join(', ')}`)
    if (filters.body_type?.length) parts.push(`Body: ${filters.body_type.join(', ')}`)
    if (filters.location) parts.push(`Location: ${filters.location}`)
    if (filters.condition) parts.push(`Condition: ${filters.condition}`)

    return parts.join(' • ') || 'No specific filters'
  }

  validateSearchData(searchData: SavedSearchCreateData): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!searchData.name || searchData.name.trim().length === 0) {
      errors.push('Search name is required')
    }

    if (searchData.name && searchData.name.length > 100) {
      errors.push('Search name must be less than 100 characters')
    }

    if (!searchData.search_term && (!searchData.filters || Object.keys(searchData.filters).length === 0)) {
      errors.push('Either search term or filters must be provided')
    }

    if (searchData.filters?.min_price && searchData.filters?.max_price && 
        searchData.filters.min_price > searchData.filters.max_price) {
      errors.push('Minimum price cannot be greater than maximum price')
    }

    if (searchData.filters?.min_year && searchData.filters?.max_year && 
        searchData.filters.min_year > searchData.filters.max_year) {
      errors.push('Minimum year cannot be greater than maximum year')
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }

  // Search suggestions based on saved searches
  async getSearchSuggestions(query: string): Promise<string[]> {
    try {
      const savedSearches = await this.getSavedSearches()
      const suggestions = savedSearches
        .filter(search => 
          search.name.toLowerCase().includes(query.toLowerCase()) ||
          search.search_term?.toLowerCase().includes(query.toLowerCase())
        )
        .map(search => search.name)
        .slice(0, 5)
      
      return suggestions
    } catch (error) {
      console.error('Error getting search suggestions:', error)
      return []
    }
  }

  // Export saved searches
  async exportSavedSearches(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    try {
      const response = await api.get('/search/saved/export', {
        params: { format },
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Error exporting saved searches:', error)
      throw error
    }
  }

  // Import saved searches
  async importSavedSearches(file: File): Promise<{ imported: number; errors: string[] }> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/search/saved/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      return response.data
    } catch (error) {
      console.error('Error importing saved searches:', error)
      throw error
    }
  }
}

export const savedSearchService = new SavedSearchService()
