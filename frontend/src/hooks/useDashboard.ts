import { useQuery } from '@tanstack/react-query'
import { dashboardService } from '@/services/dashboardService'

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardService.getDashboardStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds for real-time updates
  })
}

export const useVehicleStats = () => {
  return useQuery({
    queryKey: ['vehicles', 'stats'],
    queryFn: () => dashboardService.getVehicleStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
