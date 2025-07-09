/**
 * Local Storage Service - Single-User Preferences Management
 *
 * This service manages user preferences and personal data locally instead of
 * using cloud-based user accounts. Perfect for single-user applications.
 */

export interface UserPreferences {
  // Display preferences
  theme: 'light' | 'dark' | 'system'
  language: string
  currency: string
  
  // Search preferences
  defaultSearchRadius: number
  preferredMakes: string[]
  preferredFuelTypes: string[]
  maxPriceRange: number
  
  // Notification preferences
  enableNotifications: boolean
  notificationSound: boolean
  emailNotifications: boolean
  pushNotifications: boolean
  
  // Dashboard preferences
  dashboardLayout: 'grid' | 'list'
  showRecentSearches: boolean
  showSavedAlerts: boolean
  
  // Privacy preferences
  saveSearchHistory: boolean
  autoDeleteOldData: boolean
  dataRetentionDays: number
}

export interface SavedSearch {
  id: string
  name: string
  filters: {
    make?: string
    model?: string
    minPrice?: number
    maxPrice?: number
    year?: number
    fuelType?: string
    transmission?: string
    city?: string
  }
  createdAt: string
  lastUsed: string
  useCount: number
}

export interface FavoriteVehicle {
  id: string
  vehicleId: number
  title: string
  make: string
  model: string
  year: number
  price: number
  imageUrl?: string
  savedAt: string
  notes?: string
}

const STORAGE_KEYS = {
  PREFERENCES: 'vehicle_scout_preferences',
  SAVED_SEARCHES: 'vehicle_scout_saved_searches',
  FAVORITES: 'vehicle_scout_favorites',
  SEARCH_HISTORY: 'vehicle_scout_search_history',
  ALERT_SETTINGS: 'vehicle_scout_alert_settings'
} as const

class LocalStorageService {
  private defaultPreferences: UserPreferences = {
    theme: 'system',
    language: 'en',
    currency: 'EUR',
    defaultSearchRadius: 50,
    preferredMakes: [],
    preferredFuelTypes: [],
    maxPriceRange: 50000,
    enableNotifications: true,
    notificationSound: true,
    emailNotifications: false,
    pushNotifications: true,
    dashboardLayout: 'grid',
    showRecentSearches: true,
    showSavedAlerts: true,
    saveSearchHistory: true,
    autoDeleteOldData: true,
    dataRetentionDays: 90
  }

  // Preferences Management
  getPreferences(): UserPreferences {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.PREFERENCES)
      if (stored) {
        const parsed = JSON.parse(stored)
        return { ...this.defaultPreferences, ...parsed }
      }
    } catch (error) {
      console.error('Error loading preferences:', error)
    }
    return this.defaultPreferences
  }

  updatePreferences(updates: Partial<UserPreferences>): void {
    try {
      const current = this.getPreferences()
      const updated = { ...current, ...updates }
      localStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(updated))
    } catch (error) {
      console.error('Error saving preferences:', error)
    }
  }

  resetPreferences(): void {
    localStorage.removeItem(STORAGE_KEYS.PREFERENCES)
  }

  // Saved Searches Management
  getSavedSearches(): SavedSearch[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SAVED_SEARCHES)
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Error loading saved searches:', error)
      return []
    }
  }

  saveSearch(search: Omit<SavedSearch, 'id' | 'createdAt' | 'lastUsed' | 'useCount'>): void {
    try {
      const searches = this.getSavedSearches()
      const newSearch: SavedSearch = {
        ...search,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        lastUsed: new Date().toISOString(),
        useCount: 1
      }
      searches.push(newSearch)
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(searches))
    } catch (error) {
      console.error('Error saving search:', error)
    }
  }

  updateSearchUsage(searchId: string): void {
    try {
      const searches = this.getSavedSearches()
      const search = searches.find(s => s.id === searchId)
      if (search) {
        search.lastUsed = new Date().toISOString()
        search.useCount += 1
        localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(searches))
      }
    } catch (error) {
      console.error('Error updating search usage:', error)
    }
  }

  deleteSavedSearch(searchId: string): void {
    try {
      const searches = this.getSavedSearches().filter(s => s.id !== searchId)
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(searches))
    } catch (error) {
      console.error('Error deleting saved search:', error)
    }
  }

  // Favorite Vehicles Management
  getFavoriteVehicles(): FavoriteVehicle[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.FAVORITES)
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Error loading favorites:', error)
      return []
    }
  }

  addToFavorites(vehicle: Omit<FavoriteVehicle, 'id' | 'savedAt'>): void {
    try {
      const favorites = this.getFavoriteVehicles()
      
      // Check if already favorited
      if (favorites.some(f => f.vehicleId === vehicle.vehicleId)) {
        return
      }

      const newFavorite: FavoriteVehicle = {
        ...vehicle,
        id: Date.now().toString(),
        savedAt: new Date().toISOString()
      }
      
      favorites.push(newFavorite)
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites))
    } catch (error) {
      console.error('Error adding to favorites:', error)
    }
  }

  removeFromFavorites(vehicleId: number): void {
    try {
      const favorites = this.getFavoriteVehicles().filter(f => f.vehicleId !== vehicleId)
      localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites))
    } catch (error) {
      console.error('Error removing from favorites:', error)
    }
  }

  isFavorite(vehicleId: number): boolean {
    return this.getFavoriteVehicles().some(f => f.vehicleId === vehicleId)
  }

  updateFavoriteNotes(vehicleId: number, notes: string): void {
    try {
      const favorites = this.getFavoriteVehicles()
      const favorite = favorites.find(f => f.vehicleId === vehicleId)
      if (favorite) {
        favorite.notes = notes
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites))
      }
    } catch (error) {
      console.error('Error updating favorite notes:', error)
    }
  }

  // Search History Management
  getSearchHistory(): Array<{ query: string, timestamp: string }> {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SEARCH_HISTORY)
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Error loading search history:', error)
      return []
    }
  }

  addToSearchHistory(query: string): void {
    if (!this.getPreferences().saveSearchHistory) return

    try {
      const history = this.getSearchHistory()
      const newEntry = { query, timestamp: new Date().toISOString() }
      
      // Remove duplicate if exists
      const filtered = history.filter(h => h.query !== query)
      
      // Add to beginning and limit to 50 entries
      filtered.unshift(newEntry)
      const limited = filtered.slice(0, 50)
      
      localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(limited))
    } catch (error) {
      console.error('Error adding to search history:', error)
    }
  }

  clearSearchHistory(): void {
    localStorage.removeItem(STORAGE_KEYS.SEARCH_HISTORY)
  }

  // Data Management
  clearAllData(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
  }

  exportData(): string {
    const data = {
      preferences: this.getPreferences(),
      savedSearches: this.getSavedSearches(),
      favorites: this.getFavoriteVehicles(),
      searchHistory: this.getSearchHistory(),
      exportedAt: new Date().toISOString()
    }
    return JSON.stringify(data, null, 2)
  }

  importData(jsonData: string): boolean {
    try {
      const data = JSON.parse(jsonData)
      
      if (data.preferences) {
        localStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(data.preferences))
      }
      if (data.savedSearches) {
        localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(data.savedSearches))
      }
      if (data.favorites) {
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(data.favorites))
      }
      if (data.searchHistory) {
        localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(data.searchHistory))
      }
      
      return true
    } catch (error) {
      console.error('Error importing data:', error)
      return false
    }
  }

  // Auto cleanup old data
  cleanupOldData(): void {
    const preferences = this.getPreferences()
    if (!preferences.autoDeleteOldData) return

    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - preferences.dataRetentionDays)
    const cutoffTime = cutoffDate.toISOString()

    try {
      // Clean search history
      const history = this.getSearchHistory().filter(h => h.timestamp > cutoffTime)
      localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(history))

      // Clean old saved searches (keep if used recently)
      const searches = this.getSavedSearches().filter(s => s.lastUsed > cutoffTime)
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(searches))
    } catch (error) {
      console.error('Error cleaning up old data:', error)
    }
  }
}

export const localStorageService = new LocalStorageService()

// Auto cleanup on service initialization
localStorageService.cleanupOldData()
