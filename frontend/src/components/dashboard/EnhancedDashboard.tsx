import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Car,
  TrendingUp,
  Clock,
  MapPin,
  Settings,
  RefreshCw,
  AlertCircle,
  Database,
  Activity,
  CheckCircle,
  XCircle,
  Bell
} from 'lucide-react';
import { vehicleService, Vehicle } from '@/services/vehicleService';
import { realtimeService, SystemStatusUpdate, RealtimeNotification } from '@/services/realtimeService';


interface SystemStatus {
  status: string;
  components: {
    api: string;
    database: string;
    redis: string;
    celery: string;
    notification_system: string;
  };
  version?: string;
  scraping_active?: boolean;
  last_scrape?: string | null;
  next_scrape?: string | null;
}

const EnhancedDashboard: React.FC = () => {
  const [recentVehicles, setRecentVehicles] = useState<Vehicle[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [scraperStatus, setScraperStatus] = useState<any>(null);
  const [healthCheck, setHealthCheck] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<RealtimeNotification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboardData();
    setupRealtimeConnections();

    // Set up periodic refresh
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds

    return () => {
      clearInterval(interval);
      realtimeService.cleanup();
    };
  }, []);

  const setupRealtimeConnections = () => {
    // Subscribe to system status updates
    const unsubscribeStatus = realtimeService.subscribeToSystemStatus((status: SystemStatusUpdate) => {
      setSystemStatus(prev => ({ ...prev, ...status }));
      setIsConnected(true);
      setLastUpdate(new Date());
    });

    // Subscribe to notifications
    const unsubscribeNotifications = realtimeService.subscribeToNotifications((notification: RealtimeNotification) => {
      setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10 notifications
      setLastUpdate(new Date());
    });

    // Subscribe to vehicle matches
    const unsubscribeMatches = realtimeService.subscribeToVehicleMatches((_match) => {
      // Refresh recent vehicles when new matches arrive
      vehicleService.getRecentVehicles(8).then(setRecentVehicles);
      setLastUpdate(new Date());
    });

    return () => {
      unsubscribeStatus();
      unsubscribeNotifications();
      unsubscribeMatches();
    };
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load data in parallel with enhanced backend APIs
      const [recent, _featured, stats, scraper, health, _dashboard, notifications, _metrics] = await Promise.allSettled([
        vehicleService.getRecentVehicles(8),
        vehicleService.getFeaturedVehicles(),
        vehicleService.getSystemStats(),
        vehicleService.getScraperStatus(),
        vehicleService.getHealthCheck(),
        vehicleService.getDashboardOverview(),
        realtimeService.getUnreadNotifications(),
        realtimeService.getSystemMetrics()
      ]);

      if (recent.status === 'fulfilled') {
        setRecentVehicles(recent.value);
      }
      // Featured vehicles functionality removed
      if (stats.status === 'fulfilled') {
        setSystemStatus(stats.value);
      }
      if (scraper.status === 'fulfilled') {
        setScraperStatus(scraper.value);
      }
      if (health.status === 'fulfilled') {
        setHealthCheck(health.value);
      }
      // Dashboard stats functionality removed
      if (notifications.status === 'fulfilled') {
        setNotifications(notifications.value);
      }
      // System metrics functionality removed

      setLastUpdate(new Date());

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  const handleTriggerScrape = async () => {
    try {
      await vehicleService.triggerScrape();
      // Refresh data after triggering scrape
      setTimeout(() => {
        loadDashboardData();
      }, 2000);
    } catch (err) {
      console.error('Error triggering scrape:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const formatPrice = (price: number | null): string => {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days}d ago`;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Vehicle Scout</h1>
            <div className="flex items-center gap-4 mt-1">
              <p className="text-gray-600">Live vehicle data from Italian dealerships</p>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Connected' : 'Disconnected'} • Last update: {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
            {error && (
              <div className="flex items-center mt-2 text-red-600">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {notifications.length > 0 && (
              <Button variant="outline" size="sm" className="relative">
                <Bell className="w-4 h-4 mr-2" />
                Notifications
                <Badge className="absolute -top-2 -right-2 px-1 min-w-[1.25rem] h-5">
                  {notifications.length}
                </Badge>
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleTriggerScrape}>
              <Car className="w-4 h-4 mr-2" />
              Update Data
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Status</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(healthCheck?.status)}
                <span className="text-2xl font-bold">
                  {healthCheck?.status || 'Unknown'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Version: {healthCheck?.version || 'N/A'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Database</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus?.components?.database || 'unknown')}
                <span className="text-2xl font-bold">
                  {systemStatus?.components?.database || 'Unknown'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Data storage system
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Scraper</CardTitle>
              <Car className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(scraperStatus?.scheduler?.status)}
                <span className="text-2xl font-bold">
                  {scraperStatus?.scheduler?.status || 'Unknown'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Auto data collection
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Vehicles</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{recentVehicles.length}</div>
              <p className="text-xs text-muted-foreground">
                Recently updated
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Vehicles */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Recently Updated Vehicles
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                <p>Loading vehicles...</p>
              </div>
            ) : recentVehicles.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {recentVehicles.map((vehicle) => (
                  <div key={vehicle.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-sm">{vehicle.make} {vehicle.model}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {vehicle.year}
                      </Badge>
                    </div>
                    <p className="text-lg font-bold text-green-600 mb-1">
                      {formatPrice(vehicle.price)}
                    </p>
                    <div className="flex items-center text-xs text-gray-500 mb-2">
                      <MapPin className="w-3 h-3 mr-1" />
                      {vehicle.location || 'Italy'}
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatRelativeTime(vehicle.scrapedAt)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Car className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No vehicles found. Try updating the data.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedDashboard;
