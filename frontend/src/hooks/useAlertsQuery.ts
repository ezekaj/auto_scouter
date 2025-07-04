import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertService, AlertCreateData } from '@/services/alertService'

// Query keys
const ALERT_KEYS = {
  all: ['alerts'] as const,
  lists: () => [...ALERT_KEYS.all, 'list'] as const,
  list: (filters: any) => [...ALERT_KEYS.lists(), filters] as const,
  details: () => [...ALERT_KEYS.all, 'detail'] as const,
  detail: (id: number) => [...ALERT_KEYS.details(), id] as const,
  stats: () => [...ALERT_KEYS.all, 'stats'] as const,
  summary: () => [...ALERT_KEYS.stats(), 'summary'] as const,
}

// Hook for fetching all alerts
export function useAlerts(filters?: { is_active?: boolean }) {
  return useQuery({
    queryKey: ALERT_KEYS.list(filters),
    queryFn: () => alertService.getAlerts(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

// Hook for fetching a single alert
export function useAlert(id: number) {
  return useQuery({
    queryKey: ALERT_KEYS.detail(id),
    queryFn: () => alertService.getAlert(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook for alert summary stats
export function useAlertsSummary() {
  return useQuery({
    queryKey: ALERT_KEYS.summary(),
    queryFn: () => alertService.getAlertsSummary(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

// Hook for individual alert stats
export function useAlertStats(id: number) {
  return useQuery({
    queryKey: [...ALERT_KEYS.stats(), id],
    queryFn: () => alertService.getAlertStats(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook for creating an alert
export function useCreateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (alertData: AlertCreateData) => alertService.createAlert(alertData),
    onSuccess: () => {
      // Invalidate and refetch alerts
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.all })
    },
  })
}

// Hook for updating an alert
export function useUpdateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<AlertCreateData> }) => 
      alertService.updateAlert(id, data),
    onSuccess: (updatedAlert) => {
      // Update the specific alert in cache
      queryClient.setQueryData(
        ALERT_KEYS.detail(updatedAlert.id),
        updatedAlert
      )
      // Invalidate alerts list to refresh
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() })
    },
  })
}

// Hook for deleting an alert
export function useDeleteAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => alertService.deleteAlert(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ALERT_KEYS.detail(deletedId) })
      // Invalidate alerts list to refresh
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() })
    },
  })
}

// Hook for toggling alert active status
export function useToggleAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => alertService.toggleAlert(id),
    onSuccess: (updatedAlert) => {
      // Update the specific alert in cache
      queryClient.setQueryData(
        ALERT_KEYS.detail(updatedAlert.id),
        updatedAlert
      )
      // Invalidate alerts list to refresh
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() })
    },
  })
}

// Hook for testing an alert
export function useTestAlert() {
  return useMutation({
    mutationFn: (id: number) => alertService.testAlert(id),
  })
}

// Hook for checking alert matches
export function useCheckAlert() {
  return useMutation({
    mutationFn: (id: number) => alertService.checkAlert(id),
  })
}

// Hook for alert management actions
export function useAlertActions() {
  const createAlert = useCreateAlert()
  const updateAlert = useUpdateAlert()
  const deleteAlert = useDeleteAlert()
  const toggleAlert = useToggleAlert()
  const testAlert = useTestAlert()
  const checkAlert = useCheckAlert()

  return {
    createAlert: createAlert.mutate,
    updateAlert: updateAlert.mutate,
    deleteAlert: deleteAlert.mutate,
    toggleAlert: toggleAlert.mutate,
    testAlert: testAlert.mutate,
    checkAlert: checkAlert.mutate,
    isLoading: 
      createAlert.isPending || 
      updateAlert.isPending || 
      deleteAlert.isPending || 
      toggleAlert.isPending || 
      testAlert.isPending || 
      checkAlert.isPending,
    createError: createAlert.error,
    updateError: updateAlert.error,
    deleteError: deleteAlert.error,
    toggleError: toggleAlert.error,
    testError: testAlert.error,
    checkError: checkAlert.error,
  }
}

// Hook for active alerts only
export function useActiveAlerts() {
  const { data: alerts, ...rest } = useAlerts()
  
  const activeAlerts = alerts?.filter(alert => alert.is_active) || []
  
  return {
    data: activeAlerts,
    ...rest
  }
}

// Hook for inactive alerts only
export function useInactiveAlerts() {
  const { data: alerts, ...rest } = useAlerts()
  
  const inactiveAlerts = alerts?.filter(alert => !alert.is_active) || []
  
  return {
    data: inactiveAlerts,
    ...rest
  }
}

// Hook for alert filtering and sorting
export function useAlertFilters() {
  const [filters, setFilters] = React.useState({
    is_active: undefined as boolean | undefined,
    search: '',
    make: '',
    model: '',
  })

  const [sortBy, setSortBy] = React.useState<'name' | 'created_at' | 'last_triggered' | 'trigger_count'>('created_at')
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('desc')

  const updateFilter = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearFilters = () => {
    setFilters({
      is_active: undefined,
      search: '',
      make: '',
      model: '',
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

// Hook for alert statistics
export function useAlertMetrics() {
  const { data: summary } = useAlertsSummary()
  const { data: alerts } = useAlerts()

  const metrics = React.useMemo(() => {
    if (!alerts || !summary) return null

    const totalAlerts = alerts.length
    const activeAlerts = alerts.filter(a => a.is_active).length
    const inactiveAlerts = totalAlerts - activeAlerts
    const recentlyTriggered = alerts.filter(a => 
      a.last_triggered && 
      new Date(a.last_triggered) > new Date(Date.now() - 24 * 60 * 60 * 1000)
    ).length

    return {
      totalAlerts,
      activeAlerts,
      inactiveAlerts,
      recentlyTriggered,
      averageMatches: totalAlerts > 0 ? summary.total_matches / totalAlerts : 0,
      ...summary
    }
  }, [alerts, summary])

  return metrics
}

// Import React for useState and useMemo
import React from 'react'
