import React, { useState } from 'react'
import { Search, Trash2, Star, Clock } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { formatRelativeTime } from '@/lib/utils'

interface SavedSearch {
  id: string
  name: string
  searchTerm?: string
  filters: any
  resultsCount: number
  createdAt: Date
  lastUsed: Date
  isFavorite: boolean
}

interface SavedSearchesProps {
  isOpen: boolean
  onClose: () => void
  onLoadSearch: (search: SavedSearch) => void
}

// Mock data
const mockSavedSearches: SavedSearch[] = [
  {
    id: '1',
    name: 'BMW 3 Series Under €25k',
    searchTerm: 'BMW 3 Series',
    filters: { make: 'BMW', model: '3 Series', maxPrice: 25000 },
    resultsCount: 47,
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    lastUsed: new Date(Date.now() - 2 * 60 * 60 * 1000),
    isFavorite: true,
  },
  {
    id: '2',
    name: 'Diesel Cars in Munich',
    searchTerm: '',
    filters: { fuelType: ['Diesel'], location: 'Munich', radius: 50 },
    resultsCount: 156,
    createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
    lastUsed: new Date(Date.now() - 24 * 60 * 60 * 1000),
    isFavorite: false,
  },
  {
    id: '3',
    name: 'Electric Vehicles 2020+',
    searchTerm: '',
    filters: { fuelType: ['Electric'], minYear: 2020 },
    resultsCount: 89,
    createdAt: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000),
    lastUsed: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    isFavorite: true,
  },
  {
    id: '4',
    name: 'Luxury SUVs',
    searchTerm: '',
    filters: { 
      bodyType: ['SUV'], 
      make: ['BMW', 'Mercedes-Benz', 'Audi'], 
      minPrice: 40000 
    },
    resultsCount: 23,
    createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    lastUsed: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    isFavorite: false,
  },
]

export const SavedSearches: React.FC<SavedSearchesProps> = ({
  isOpen,
  onClose,
  onLoadSearch,
}) => {
  const [searches, setSearches] = useState(mockSavedSearches)

  const toggleFavorite = (searchId: string) => {
    setSearches(prev =>
      prev.map(search =>
        search.id === searchId
          ? { ...search, isFavorite: !search.isFavorite }
          : search
      )
    )
  }

  const deleteSearch = (searchId: string) => {
    setSearches(prev => prev.filter(search => search.id !== searchId))
  }

  const loadSearch = (search: SavedSearch) => {
    // Update last used timestamp
    setSearches(prev =>
      prev.map(s =>
        s.id === search.id
          ? { ...s, lastUsed: new Date() }
          : s
      )
    )
    onLoadSearch(search)
  }

  const getFilterSummary = (filters: any): string => {
    const parts: string[] = []
    
    if (filters.make) parts.push(filters.make)
    if (filters.model) parts.push(filters.model)
    if (filters.minPrice || filters.maxPrice) {
      const priceRange = `€${filters.minPrice || 0}${filters.maxPrice ? ` - €${filters.maxPrice}` : '+'}`
      parts.push(priceRange)
    }
    if (filters.minYear || filters.maxYear) {
      const yearRange = `${filters.minYear || ''}${filters.maxYear ? ` - ${filters.maxYear}` : '+'}`
      parts.push(yearRange)
    }
    if (filters.fuelType?.length) {
      parts.push(filters.fuelType.join(', '))
    }
    if (filters.location) {
      parts.push(`📍 ${filters.location}`)
    }
    
    return parts.slice(0, 3).join(' • ') + (parts.length > 3 ? '...' : '')
  }

  const favoriteSearches = searches.filter(s => s.isFavorite)
  const recentSearches = searches
    .filter(s => !s.isFavorite)
    .sort((a, b) => b.lastUsed.getTime() - a.lastUsed.getTime())

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Search className="mr-2 h-5 w-5" />
            Saved Searches
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Favorite Searches */}
          {favoriteSearches.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Star className="mr-2 h-4 w-4 text-yellow-500" />
                Favorites
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {favoriteSearches.map((search) => (
                  <Card key={search.id} className="card-hover cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium truncate">{search.name}</h4>
                            <Badge variant="secondary" className="text-xs">
                              {search.resultsCount}
                            </Badge>
                          </div>
                          
                          {search.searchTerm && (
                            <p className="text-sm text-muted-foreground mb-1">
                              "{search.searchTerm}"
                            </p>
                          )}
                          
                          <p className="text-xs text-muted-foreground mb-2 truncate">
                            {getFilterSummary(search.filters)}
                          </p>
                          
                          <div className="flex items-center text-xs text-muted-foreground">
                            <Clock className="mr-1 h-3 w-3" />
                            Last used {formatRelativeTime(search.lastUsed)}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-1 ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              toggleFavorite(search.id)
                            }}
                          >
                            <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteSearch(search.id)
                            }}
                          >
                            <Trash2 className="h-3 w-3 text-red-500" />
                          </Button>
                        </div>
                      </div>
                      
                      <Button
                        className="w-full mt-3"
                        onClick={() => loadSearch(search)}
                      >
                        Load Search
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Recent Searches */}
          {recentSearches.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Clock className="mr-2 h-4 w-4" />
                Recent Searches
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recentSearches.map((search) => (
                  <Card key={search.id} className="card-hover cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium truncate">{search.name}</h4>
                            <Badge variant="secondary" className="text-xs">
                              {search.resultsCount}
                            </Badge>
                          </div>
                          
                          {search.searchTerm && (
                            <p className="text-sm text-muted-foreground mb-1">
                              "{search.searchTerm}"
                            </p>
                          )}
                          
                          <p className="text-xs text-muted-foreground mb-2 truncate">
                            {getFilterSummary(search.filters)}
                          </p>
                          
                          <div className="flex items-center text-xs text-muted-foreground">
                            <Clock className="mr-1 h-3 w-3" />
                            Last used {formatRelativeTime(search.lastUsed)}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-1 ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              toggleFavorite(search.id)
                            }}
                          >
                            <Star className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteSearch(search.id)
                            }}
                          >
                            <Trash2 className="h-3 w-3 text-red-500" />
                          </Button>
                        </div>
                      </div>
                      
                      <Button
                        variant="outline"
                        className="w-full mt-3"
                        onClick={() => loadSearch(search)}
                      >
                        Load Search
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {searches.length === 0 && (
            <div className="text-center py-8">
              <Search className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No saved searches</h3>
              <p className="text-muted-foreground">
                Save your searches to quickly access them later
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
