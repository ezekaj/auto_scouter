import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { savedSearchService, SavedSearchCreateData } from '@/services/savedSearchService'

// Query keys
const SAVED_SEARCH_KEYS = {
  all: ['savedSearches'] as const,
  lists: () => [...SAVED_SEARCH_KEYS.all, 'list'] as const,
  list: (filters: any) => [...SAVED_SEARCH_KEYS.lists(), filters] as const,
  details: () => [...SAVED_SEARCH_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...SAVED_SEARCH_KEYS.details(), id] as const,
  stats: () => [...SAVED_SEARCH_KEYS.all, 'stats'] as const,
  suggestions: () => [...SAVED_SEARCH_KEYS.all, 'suggestions'] as const,
}

// Hook for fetching all saved searches
export function useSavedSearches() {
  return useQuery({
    queryKey: SAVED_SEARCH_KEYS.list({}),
    queryFn: () => savedSearchService.getSavedSearches(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Hook for fetching a single saved search
export function useSavedSearch(id: string) {
  return useQuery({
    queryKey: SAVED_SEARCH_KEYS.detail(id),
    queryFn: () => savedSearchService.getSavedSearch(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Hook for saved search statistics
export function useSavedSearchStats() {
  return useQuery({
    queryKey: SAVED_SEARCH_KEYS.stats(),
    queryFn: () => savedSearchService.getSavedSearchStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook for search suggestions
export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: [...SAVED_SEARCH_KEYS.suggestions(), query],
    queryFn: () => savedSearchService.getSearchSuggestions(query),
    enabled: query.length > 2, // Only search when query is at least 3 characters
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Hook for creating a saved search
export function useCreateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (searchData: SavedSearchCreateData) => savedSearchService.createSavedSearch(searchData),
    onSuccess: () => {
      // Invalidate and refetch saved searches
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.all })
    },
  })
}

// Hook for updating a saved search
export function useUpdateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SavedSearchCreateData> }) => 
      savedSearchService.updateSavedSearch(id, data),
    onSuccess: (updatedSearch) => {
      // Update the specific search in cache
      queryClient.setQueryData(
        SAVED_SEARCH_KEYS.detail(updatedSearch.id),
        updatedSearch
      )
      // Invalidate searches list to refresh
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.lists() })
    },
  })
}

// Hook for deleting a saved search
export function useDeleteSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchService.deleteSavedSearch(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: SAVED_SEARCH_KEYS.detail(deletedId) })
      // Invalidate searches list to refresh
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.lists() })
    },
  })
}

// Hook for toggling favorite status
export function useToggleFavorite() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchService.toggleFavorite(id),
    onSuccess: (updatedSearch) => {
      // Update the specific search in cache
      queryClient.setQueryData(
        SAVED_SEARCH_KEYS.detail(updatedSearch.id),
        updatedSearch
      )
      // Invalidate searches list to refresh
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.lists() })
    },
  })
}

// Hook for executing a saved search
export function useExecuteSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchService.executeSearch(id),
    onSuccess: (_, searchId) => {
      // Update last used timestamp in cache
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.detail(searchId) })
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.lists() })
    },
  })
}

// Hook for exporting saved searches
export function useExportSavedSearches() {
  return useMutation({
    mutationFn: (format: 'json' | 'csv' = 'json') => savedSearchService.exportSavedSearches(format),
  })
}

// Hook for importing saved searches
export function useImportSavedSearches() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => savedSearchService.importSavedSearches(file),
    onSuccess: () => {
      // Refresh saved searches list
      queryClient.invalidateQueries({ queryKey: SAVED_SEARCH_KEYS.all })
    },
  })
}

// Hook for saved search management actions
export function useSavedSearchActions() {
  const createSearch = useCreateSavedSearch()
  const updateSearch = useUpdateSavedSearch()
  const deleteSearch = useDeleteSavedSearch()
  const toggleFavorite = useToggleFavorite()
  const executeSearch = useExecuteSavedSearch()
  const exportSearches = useExportSavedSearches()
  const importSearches = useImportSavedSearches()

  return {
    createSearch: createSearch.mutate,
    updateSearch: updateSearch.mutate,
    deleteSearch: deleteSearch.mutate,
    toggleFavorite: toggleFavorite.mutate,
    executeSearch: executeSearch.mutate,
    exportSearches: exportSearches.mutate,
    importSearches: importSearches.mutate,
    isLoading: 
      createSearch.isPending || 
      updateSearch.isPending || 
      deleteSearch.isPending || 
      toggleFavorite.isPending || 
      executeSearch.isPending || 
      exportSearches.isPending || 
      importSearches.isPending,
    createError: createSearch.error,
    updateError: updateSearch.error,
    deleteError: deleteSearch.error,
    toggleError: toggleFavorite.error,
    executeError: executeSearch.error,
    exportError: exportSearches.error,
    importError: importSearches.error,
  }
}

// Hook for favorite searches only
export function useFavoriteSavedSearches() {
  const { data: searches, ...rest } = useSavedSearches()
  
  const favoriteSearches = searches?.filter(search => search.is_favorite) || []
  
  return {
    data: favoriteSearches,
    ...rest
  }
}

// Hook for recent searches (non-favorites, sorted by last used)
export function useRecentSavedSearches(limit: number = 10) {
  const { data: searches, ...rest } = useSavedSearches()
  
  const recentSearches = React.useMemo(() => {
    if (!searches) return []
    
    return searches
      .filter(search => !search.is_favorite)
      .sort((a, b) => {
        const aTime = a.last_used ? new Date(a.last_used).getTime() : 0
        const bTime = b.last_used ? new Date(b.last_used).getTime() : 0
        return bTime - aTime
      })
      .slice(0, limit)
  }, [searches, limit])
  
  return {
    data: recentSearches,
    ...rest
  }
}

// Hook for saved search filtering and sorting
export function useSavedSearchFilters() {
  const [filters, setFilters] = React.useState({
    is_favorite: undefined as boolean | undefined,
    search: '',
    has_results: undefined as boolean | undefined,
  })

  const [sortBy, setSortBy] = React.useState<'name' | 'created_at' | 'last_used' | 'results_count'>('last_used')
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('desc')

  const updateFilter = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearFilters = () => {
    setFilters({
      is_favorite: undefined,
      search: '',
      has_results: undefined,
    })
  }

  return {
    filters,
    sortBy,
    sortOrder,
    updateFilter,
    setSortBy,
    setSortOrder,
    clearFilters,
  }
}

// Hook for saved search metrics
export function useSavedSearchMetrics() {
  const { data: stats } = useSavedSearchStats()
  const { data: searches } = useSavedSearches()

  const metrics = React.useMemo(() => {
    if (!searches || !stats) return null

    const totalSearches = searches.length
    const favoriteSearches = searches.filter(s => s.is_favorite).length
    const activeSearches = searches.filter(s => s.is_active).length
    const searchesWithResults = searches.filter(s => s.results_count > 0).length
    const recentlyUsed = searches.filter(s => 
      s.last_used && 
      new Date(s.last_used) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    ).length

    return {
      totalSearches,
      favoriteSearches,
      activeSearches,
      searchesWithResults,
      recentlyUsed,
      averageResults: totalSearches > 0 ? stats.total_results / totalSearches : 0,
      ...stats
    }
  }, [searches, stats])

  return metrics
}

// Hook for validating saved search data
export function useValidateSavedSearch() {
  return React.useCallback((searchData: SavedSearchCreateData) => {
    return savedSearchService.validateSearchData(searchData)
  }, [])
}
