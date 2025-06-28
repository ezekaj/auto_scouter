import React from 'react'
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query'
import { vehicleService, VehicleSearchParams } from '@/services/vehicleService'
import { getErrorMessage } from '@/lib/api'

// Query keys
export const vehicleKeys = {
  all: ['vehicles'] as const,
  lists: () => [...vehicleKeys.all, 'list'] as const,
  list: (params: VehicleSearchParams) => [...vehicleKeys.lists(), params] as const,
  details: () => [...vehicleKeys.all, 'detail'] as const,
  detail: (id: string) => [...vehicleKeys.details(), id] as const,
  recent: () => [...vehicleKeys.all, 'recent'] as const,
  featured: () => [...vehicleKeys.all, 'featured'] as const,
  saved: () => [...vehicleKeys.all, 'saved'] as const,
  stats: () => [...vehicleKeys.all, 'stats'] as const,
  recommendations: () => [...vehicleKeys.all, 'recommendations'] as const,
  similar: (id: string) => [...vehicleKeys.all, 'similar', id] as const,
  filterOptions: () => [...vehicleKeys.all, 'filter-options'] as const,
}

// Hooks for vehicle data
export const useVehicles = (params: VehicleSearchParams = {}) => {
  return useQuery({
    queryKey: vehicleKeys.list(params),
    queryFn: () => vehicleService.searchVehicles(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useVehicle = (id: string) => {
  return useQuery({
    queryKey: vehicleKeys.detail(id),
    queryFn: () => vehicleService.getVehicle(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useRecentVehicles = (limit: number = 20) => {
  return useQuery({
    queryKey: [...vehicleKeys.recent(), limit],
    queryFn: () => vehicleService.getRecentVehicles(limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export const useFeaturedVehicles = () => {
  return useQuery({
    queryKey: vehicleKeys.featured(),
    queryFn: () => vehicleService.getFeaturedVehicles(),
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

export const useVehicleStats = () => {
  return useQuery({
    queryKey: vehicleKeys.stats(),
    queryFn: () => vehicleService.getVehicleStats(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

export const useSavedVehicles = () => {
  return useQuery({
    queryKey: vehicleKeys.saved(),
    queryFn: () => vehicleService.getSavedVehicles(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useSimilarVehicles = (vehicleId: string, limit: number = 5) => {
  return useQuery({
    queryKey: [...vehicleKeys.similar(vehicleId), limit],
    queryFn: () => vehicleService.getSimilarVehicles(vehicleId, limit),
    enabled: !!vehicleId,
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

export const useVehicleRecommendations = (userId?: string) => {
  return useQuery({
    queryKey: [...vehicleKeys.recommendations(), userId],
    queryFn: () => vehicleService.getRecommendations(userId),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useFilterOptions = () => {
  return useQuery({
    queryKey: vehicleKeys.filterOptions(),
    queryFn: () => vehicleService.getFilterOptions(),
    staleTime: 60 * 60 * 1000, // 1 hour
    gcTime: 2 * 60 * 60 * 1000, // 2 hours
  })
}

// Mutations for vehicle actions
export const useSaveVehicle = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (vehicleId: string) => vehicleService.saveVehicle(vehicleId),
    onSuccess: () => {
      // Invalidate saved vehicles query
      queryClient.invalidateQueries({ queryKey: vehicleKeys.saved() })
    },
    onError: (error) => {
      console.error('Failed to save vehicle:', getErrorMessage(error))
    },
  })
}

export const useUnsaveVehicle = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (vehicleId: string) => vehicleService.unsaveVehicle(vehicleId),
    onSuccess: () => {
      // Invalidate saved vehicles query
      queryClient.invalidateQueries({ queryKey: vehicleKeys.saved() })
    },
    onError: (error) => {
      console.error('Failed to unsave vehicle:', getErrorMessage(error))
    },
  })
}

export const useReportVehicle = () => {
  return useMutation({
    mutationFn: ({ vehicleId, reason, description }: {
      vehicleId: string
      reason: string
      description?: string
    }) => vehicleService.reportVehicle(vehicleId, reason, description),
    onError: (error) => {
      console.error('Failed to report vehicle:', getErrorMessage(error))
    },
  })
}

export const useAdvancedSearch = () => {
  return useMutation({
    mutationFn: (filters: VehicleSearchParams) => vehicleService.advancedSearch(filters),
    onError: (error) => {
      console.error('Advanced search failed:', getErrorMessage(error))
    },
  })
}

export const useExportVehicles = () => {
  return useMutation({
    mutationFn: ({ params, format }: {
      params: VehicleSearchParams
      format?: 'csv' | 'xlsx' | 'pdf'
    }) => vehicleService.exportSearchResults(params, format),
    onError: (error) => {
      console.error('Export failed:', getErrorMessage(error))
    },
  })
}

// Custom hook for vehicle search with debouncing
export const useVehicleSearch = (initialParams: VehicleSearchParams = {}) => {
  const [searchParams, setSearchParams] = React.useState(initialParams)
  const [debouncedParams, setDebouncedParams] = React.useState(initialParams)

  // Debounce search params
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedParams(searchParams)
    }, 500)

    return () => clearTimeout(timer)
  }, [searchParams])

  const query = useVehicles(debouncedParams)

  return {
    ...query,
    searchParams,
    setSearchParams,
    isSearching: searchParams !== debouncedParams || query.isFetching,
  }
}

// Custom hook for infinite scroll
export const useInfiniteVehicles = (params: VehicleSearchParams = {}) => {
  return useInfiniteQuery({
    queryKey: vehicleKeys.list(params),
    queryFn: ({ pageParam = 1 }) =>
      vehicleService.searchVehicles({ ...params, page: pageParam as number }),
    initialPageParam: 1,
    getNextPageParam: (lastPage: any) => {
      if (lastPage.pagination.hasNext) {
        return lastPage.pagination.page + 1
      }
      return undefined
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
