import React, { useState, useEffect } from 'react';
import { Plus, Search, MoreVertical, Bell, BellOff, Edit, Trash2, TestTube } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAlerts } from '@/hooks/useAlerts';
import { Alert } from '@/services/alertService';
import { AlertForm } from './AlertForm';
import { AlertTestDialog } from './AlertTestDialog';

// Helper function to convert Alert to AlertFormData
const alertToFormData = (alert: Alert) => ({
  name: alert.name,
  description: alert.description,
  make: alert.make,
  model: alert.model,
  minPrice: alert.min_price,
  maxPrice: alert.max_price,
  minYear: alert.min_year,
  maxYear: alert.max_year,
  maxMileage: alert.max_mileage,
  fuelType: alert.fuel_type ? [alert.fuel_type] : undefined,
  transmission: alert.transmission ? [alert.transmission] : undefined,
  bodyType: alert.body_type ? [alert.body_type] : undefined,
  city: alert.city,
  region: alert.region,
  locationRadius: alert.location_radius,
  minEnginePower: alert.min_engine_power,
  maxEnginePower: alert.max_engine_power,
  condition: alert.condition,
  isActive: alert.is_active,
  notificationFrequency: alert.notification_frequency,
  maxNotificationsPerDay: alert.max_notifications_per_day,
});

export const AlertManager: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showActiveOnly, setShowActiveOnly] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);

  const {
    alerts,
    loading,
    error,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleAlert,
    testAlert,
    fetchAlerts
  } = useAlerts();

  useEffect(() => {
    fetchAlerts({ is_active: showActiveOnly ? true : undefined });
  }, [showActiveOnly]);

  const filteredAlerts = alerts.filter(alert =>
    alert.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    alert.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    alert.make?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    alert.model?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateAlert = async (alertData: any) => {
    try {
      await createAlert(alertData);
      setShowCreateForm(false);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to create alert:', error);
    }
  };

  const handleUpdateAlert = async (alertData: any) => {
    if (!selectedAlert) return;
    
    try {
      await updateAlert(selectedAlert.id, alertData);
      setShowEditForm(false);
      setSelectedAlert(null);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to update alert:', error);
    }
  };

  const handleDeleteAlert = async (alertId: number) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      try {
        await deleteAlert(alertId);
        fetchAlerts();
      } catch (error) {
        console.error('Failed to delete alert:', error);
      }
    }
  };

  const handleToggleAlert = async (alertId: number) => {
    try {
      await toggleAlert(alertId);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to toggle alert:', error);
    }
  };

  const handleTestAlert = (alert: any) => {
    setSelectedAlert(alert);
    setShowTestDialog(true);
  };

  const formatCriteria = (alert: any) => {
    const criteria = [];
    
    if (alert.make) criteria.push(`Make: ${alert.make}`);
    if (alert.model) criteria.push(`Model: ${alert.model}`);
    if (alert.min_price || alert.max_price) {
      const priceRange = [
        alert.min_price ? `€${alert.min_price.toLocaleString()}` : '',
        alert.max_price ? `€${alert.max_price.toLocaleString()}` : ''
      ].filter(Boolean).join(' - ');
      criteria.push(`Price: ${priceRange}`);
    }
    if (alert.min_year || alert.max_year) {
      const yearRange = [alert.min_year, alert.max_year].filter(Boolean).join(' - ');
      criteria.push(`Year: ${yearRange}`);
    }
    if (alert.max_mileage) criteria.push(`Max mileage: ${alert.max_mileage.toLocaleString()} km`);
    if (alert.fuel_type) criteria.push(`Fuel: ${alert.fuel_type}`);
    if (alert.transmission) criteria.push(`Transmission: ${alert.transmission}`);
    if (alert.city) criteria.push(`Location: ${alert.city}`);
    
    return criteria.slice(0, 3).join(', ') + (criteria.length > 3 ? '...' : '');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alert Management</h1>
          <p className="text-gray-600">Create and manage your vehicle alerts</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} aria-label="Create a new vehicle alert">
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          Create Alert
        </Button>
      </header>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
                <Input
                  placeholder="Search alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  aria-label="Search through your vehicle alerts"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                checked={showActiveOnly}
                onCheckedChange={setShowActiveOnly}
                id="active-only"
              />
              <label htmlFor="active-only" className="text-sm font-medium">
                Active only
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-red-600 mb-4">Failed to load alerts</p>
            <Button variant="outline" onClick={() => fetchAlerts()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : filteredAlerts.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Bell className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts found</h3>
            <p className="text-gray-600 mb-4">
              {searchTerm ? 'No alerts match your search criteria.' : 'Create your first alert to get started.'}
            </p>
            {!searchTerm && (
              <Button onClick={() => setShowCreateForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Alert
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredAlerts.map((alert) => (
            <Card key={alert.id} className={`${!alert.is_active ? 'opacity-60' : ''}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{alert.name}</h3>
                      <Badge variant={alert.is_active ? "default" : "secondary"}>
                        {alert.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      {alert.trigger_count > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {alert.trigger_count} matches
                        </Badge>
                      )}
                    </div>
                    
                    {alert.description && (
                      <p className="text-gray-600 mb-3">{alert.description}</p>
                    )}
                    
                    <div className="text-sm text-gray-500 mb-3">
                      <strong>Criteria:</strong> {formatCriteria(alert)}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-400">
                      <span>Created {new Date(alert.created_at).toLocaleDateString()}</span>
                      {alert.last_triggered && (
                        <span>Last triggered {new Date(alert.last_triggered).toLocaleDateString()}</span>
                      )}
                      <span>Frequency: {alert.notification_frequency}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleAlert(alert.id)}
                    >
                      {alert.is_active ? (
                        <BellOff className="h-4 w-4" />
                      ) : (
                        <Bell className="h-4 w-4" />
                      )}
                    </Button>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedAlert(alert);
                            setShowEditForm(true);
                          }}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleTestAlert(alert)}>
                          <TestTube className="h-4 w-4 mr-2" />
                          Test
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteAlert(alert.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Alert Dialog */}
      <Dialog open={showCreateForm} onOpenChange={setShowCreateForm}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Alert</DialogTitle>
          </DialogHeader>
          <AlertForm
            isOpen={showCreateForm}
            onClose={() => setShowCreateForm(false)}
            onSave={handleCreateAlert}
            mode="create"
          />
        </DialogContent>
      </Dialog>

      {/* Edit Alert Dialog */}
      <Dialog open={showEditForm} onOpenChange={setShowEditForm}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Alert</DialogTitle>
          </DialogHeader>
          <AlertForm
            isOpen={showEditForm}
            onClose={() => {
              setShowEditForm(false);
              setSelectedAlert(null);
            }}
            onSave={handleUpdateAlert}
            initialData={selectedAlert ? alertToFormData(selectedAlert) : undefined}
            mode="edit"
          />
        </DialogContent>
      </Dialog>

      {/* Test Alert Dialog */}
      {selectedAlert && (
        <AlertTestDialog
          alert={selectedAlert}
          isOpen={showTestDialog}
          onClose={() => {
            setShowTestDialog(false);
            setSelectedAlert(null);
          }}
          onTest={testAlert}
        />
      )}
    </div>
  );
};

export default AlertManager;
