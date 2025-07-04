import React, { useState, useEffect } from 'react'
import { Search, Trash2, Star, Clock, Loader2 } from 'lucide-react'
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
import { savedSearchService, SavedSearch } from '@/services/savedSearchService'

// SavedSearch interface is now imported from the service

interface SavedSearchesProps {
  isOpen: boolean
  onClose: () => void
  onLoadSearch: (search: SavedSearch) => void
}

export const SavedSearches: React.FC<SavedSearchesProps> = ({
  isOpen,
  onClose,
  onLoadSearch,
}) => {
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load saved searches when component opens
  useEffect(() => {
    if (isOpen) {
      loadSavedSearches()
    }
  }, [isOpen])

  const loadSavedSearches = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await savedSearchService.getSavedSearches()
      setSearches(data)
    } catch (err) {
      setError('Failed to load saved searches')
      console.error('Error loading saved searches:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleFavorite = async (searchId: string) => {
    try {
      const updatedSearch = await savedSearchService.toggleFavorite(searchId)
      setSearches(prev =>
        prev.map(search =>
          search.id === searchId ? updatedSearch : search
        )
      )
    } catch (err) {
      console.error('Error toggling favorite:', err)
    }
  }

  const deleteSearch = async (searchId: string) => {
    try {
      await savedSearchService.deleteSavedSearch(searchId)
      setSearches(prev => prev.filter(search => search.id !== searchId))
    } catch (err) {
      console.error('Error deleting search:', err)
    }
  }

  const loadSearch = async (search: SavedSearch) => {
    try {
      // Update last used timestamp on server
      await savedSearchService.updateLastUsed(search.id)

      // Update local state
      setSearches(prev =>
        prev.map(s =>
          s.id === search.id
            ? { ...s, last_used: new Date().toISOString() }
            : s
        )
      )

      onLoadSearch(search)
    } catch (err) {
      console.error('Error updating last used:', err)
      // Still load the search even if updating timestamp fails
      onLoadSearch(search)
    }
  }



  const favoriteSearches = searches.filter(s => s.is_favorite)
  const recentSearches = searches
    .filter(s => !s.is_favorite)
    .sort((a, b) => {
      const aTime = a.last_used ? new Date(a.last_used).getTime() : 0
      const bTime = b.last_used ? new Date(b.last_used).getTime() : 0
      return bTime - aTime
    })

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Search className="mr-2 h-5 w-5" />
              Saved Searches
            </DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading saved searches...</span>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (error) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Search className="mr-2 h-5 w-5" />
              Saved Searches
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadSavedSearches}>Try Again</Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

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
                              {search.results_count}
                            </Badge>
                          </div>

                          {search.search_term && (
                            <p className="text-sm text-muted-foreground mb-1">
                              "{search.search_term}"
                            </p>
                          )}

                          <p className="text-xs text-muted-foreground mb-2 truncate">
                            {savedSearchService.formatSearchFilters(search.filters)}
                          </p>

                          <div className="flex items-center text-xs text-muted-foreground">
                            <Clock className="mr-1 h-3 w-3" />
                            Last used {search.last_used ? formatRelativeTime(new Date(search.last_used)) : 'Never'}
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
                              {search.results_count}
                            </Badge>
                          </div>

                          {search.search_term && (
                            <p className="text-sm text-muted-foreground mb-1">
                              "{search.search_term}"
                            </p>
                          )}

                          <p className="text-xs text-muted-foreground mb-2 truncate">
                            {savedSearchService.formatSearchFilters(search.filters)}
                          </p>

                          <div className="flex items-center text-xs text-muted-foreground">
                            <Clock className="mr-1 h-3 w-3" />
                            Last used {search.last_used ? formatRelativeTime(new Date(search.last_used)) : 'Never'}
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
