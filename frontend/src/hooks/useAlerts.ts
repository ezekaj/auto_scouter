import { useState, useCallback } from 'react';
import { api } from '@/lib/api';

interface Alert {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  make?: string;
  model?: string;
  min_price?: number;
  max_price?: number;
  min_year?: number;
  max_year?: number;
  max_mileage?: number;
  fuel_type?: string;
  transmission?: string;
  body_type?: string;
  city?: string;
  region?: string;
  location_radius?: number;
  min_engine_power?: number;
  max_engine_power?: number;
  condition?: string;
  is_active: boolean;
  notification_frequency: string;
  last_triggered?: string;
  trigger_count: number;
  max_notifications_per_day: number;
  created_at: string;
  updated_at?: string;
}

interface AlertFilters {
  is_active?: boolean;
  page?: number;
  pageSize?: number;
}

interface AlertTestRequest {
  test_days?: number;
  max_listings?: number;
  create_notifications?: boolean;
}

interface AlertTestResponse {
  alert_id: number;
  test_period_days: number;
  listings_tested: number;
  matches_found: number;
  matches: any[];
  would_trigger: boolean;
}

interface AlertStats {
  alert_id: number;
  alert_name: string;
  is_active: boolean;
  created_at: string;
  last_triggered?: string;
  trigger_count: number;
  notifications_in_period: number;
  recent_notifications: any[];
  period_days: number;
}

export const useAlerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  });

  const fetchAlerts = useCallback(async (filters: AlertFilters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString());
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.pageSize) params.append('page_size', filters.pageSize.toString());

      const response = await api.get(`/alerts/?${params.toString()}`);

      setAlerts(response.data.alerts);
      setPagination(response.data.pagination);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  const getAlert = useCallback(async (alertId: number): Promise<Alert> => {
    try {
      const response = await api.get(`/alerts/${alertId}`);
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to fetch alert');
    }
  }, []);

  const createAlert = useCallback(async (alertData: Partial<Alert>): Promise<Alert> => {
    try {
      const response = await api.post('/alerts/', alertData);
      const newAlert = response.data;
      
      // Update local state
      setAlerts(prev => [newAlert, ...prev]);
      
      return newAlert;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to create alert');
    }
  }, []);

  const updateAlert = useCallback(async (alertId: number, alertData: Partial<Alert>): Promise<Alert> => {
    try {
      const response = await api.put(`/alerts/${alertId}`, alertData);
      const updatedAlert = response.data;
      
      // Update local state
      setAlerts(prev => 
        prev.map(alert => 
          alert.id === alertId ? updatedAlert : alert
        )
      );
      
      return updatedAlert;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to update alert');
    }
  }, []);

  const deleteAlert = useCallback(async (alertId: number) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      
      // Update local state
      setAlerts(prev => prev.filter(alert => alert.id !== alertId));
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to delete alert');
    }
  }, []);

  const toggleAlert = useCallback(async (alertId: number) => {
    try {
      const response = await api.post(`/alerts/${alertId}/toggle`);
      
      // Update local state
      setAlerts(prev => 
        prev.map(alert => 
          alert.id === alertId 
            ? { ...alert, is_active: response.data.is_active }
            : alert
        )
      );
      
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to toggle alert');
    }
  }, []);

  const testAlert = useCallback(async (
    alertId: number, 
    testRequest: AlertTestRequest = {}
  ): Promise<AlertTestResponse> => {
    try {
      const response = await api.post(`/alerts/${alertId}/test`, testRequest);
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to test alert');
    }
  }, []);

  const getAlertStats = useCallback(async (
    alertId: number, 
    days: number = 30
  ): Promise<AlertStats> => {
    try {
      const response = await api.get(`/alerts/${alertId}/stats?days=${days}`);
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to fetch alert stats');
    }
  }, []);

  const duplicateAlert = useCallback(async (alertId: number): Promise<Alert> => {
    try {
      // Get the original alert
      const originalAlert = await getAlert(alertId);
      
      // Create a copy with modified name
      const duplicateData = {
        ...originalAlert,
        name: `${originalAlert.name} (Copy)`,
        is_active: false // Start inactive
      };
      
      // Remove fields that shouldn't be copied
      const { id, created_at, updated_at, last_triggered, trigger_count, ...cleanData } = duplicateData;

      return await createAlert(cleanData);

    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to duplicate alert');
    }
  }, [getAlert, createAlert]);

  const bulkToggleAlerts = useCallback(async (alertIds: number[]) => {
    try {
      const promises = alertIds.map(id => 
        api.post(`/alerts/${id}/toggle`).then(response => ({
          id,
          is_active: response.data.is_active
        }))
      );
      
      const results = await Promise.all(promises);
      
      // Update local state
      setAlerts(prev => 
        prev.map(alert => {
          const result = results.find(r => r.id === alert.id);
          return result ? { ...alert, is_active: result.is_active } : alert;
        })
      );
      
      return results;
    } catch (err: any) {
      throw new Error('Failed to bulk toggle alerts');
    }
  }, []);

  const bulkDeleteAlerts = useCallback(async (alertIds: number[]) => {
    try {
      const promises = alertIds.map(id => api.delete(`/alerts/${id}`));
      await Promise.all(promises);
      
      // Update local state
      setAlerts(prev => prev.filter(alert => !alertIds.includes(alert.id)));
    } catch (err: any) {
      throw new Error('Failed to bulk delete alerts');
    }
  }, []);

  const exportAlerts = useCallback(async (format: 'json' | 'csv' | 'excel' = 'json') => {
    try {
      const response = await api.get(`/alerts/export?format=${format}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `alerts.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      throw new Error('Failed to export alerts');
    }
  }, []);

  const importAlerts = useCallback(async (alertsData: Partial<Alert>[], overwriteExisting: boolean = false) => {
    try {
      const response = await api.post('/alerts/import', {
        alerts: alertsData,
        overwrite_existing: overwriteExisting
      });
      
      // Refresh alerts list
      await fetchAlerts();
      
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to import alerts');
    }
  }, [fetchAlerts]);

  return {
    alerts,
    loading,
    error,
    pagination,
    fetchAlerts,
    getAlert,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleAlert,
    testAlert,
    getAlertStats,
    duplicateAlert,
    bulkToggleAlerts,
    bulkDeleteAlerts,
    exportAlerts,
    importAlerts
  };
};
