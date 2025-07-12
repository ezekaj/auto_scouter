import React, { useState, useEffect } from 'react';
import { Bell, Check, X, Settings, Filter, MoreVertical } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useNotifications } from '@/hooks/useNotifications';
import { NotificationItem } from './NotificationItem';
import { NotificationFilters } from './NotificationFilters';
import { NotificationPreferences } from './NotificationPreferences';

interface NotificationCenterProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen = true, onClose = () => {} }) => {
  const [activeTab, setActiveTab] = useState('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [filters, setFilters] = useState<{
    type: string | null;
    status: string | null;
    isRead: boolean | null;
    dateFrom: string | null;
    dateTo: string | null;
  }>({
    type: null,
    status: null,
    isRead: null,
    dateFrom: null,
    dateTo: null
  });

  // Use the notification hook
  const {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    fetchNotifications
  } = useNotifications()

  useEffect(() => {
    if (isOpen) {
      fetchNotifications(filters)
    }
  }, [isOpen, activeTab, filters, fetchNotifications]);

  const handleMarkAllRead = () => {
    markAllAsRead()
  };

  const handleNotificationAction = (id: number, action: 'read' | 'delete') => {
    if (action === 'read') {
      markAsRead(Number(id))
    } else if (action === 'delete') {
      deleteNotification(Number(id))
    }
  };

  const filteredNotifications = notifications.filter(notification => {
    if (activeTab === 'unread' && notification.is_read) return false;
    if (activeTab === 'alerts' && !notification.alert_id) return false;
    if (activeTab === 'system' && notification.alert_id) return false;
    return true;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-end">
      <div className="bg-white w-96 h-full shadow-xl overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold">Notifications</h2>
              {unreadCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {unreadCount}
                </Badge>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="h-4 w-4" />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleMarkAllRead}>
                    <Check className="h-4 w-4 mr-2" />
                    Mark all as read
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setShowPreferences(true)}>
                    <Settings className="h-4 w-4 mr-2" />
                    Preferences
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4">
              <NotificationFilters
                filters={filters}
                onFiltersChange={(newFilters) => setFilters({
                  type: newFilters.type ?? null,
                  status: newFilters.status ?? null,
                  isRead: newFilters.isRead ?? null,
                  dateFrom: newFilters.dateFrom ?? null,
                  dateTo: newFilters.dateTo ?? null,
                })}
                onClose={() => setShowFilters(false)}
              />
            </div>
          )}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="grid w-full grid-cols-4 border-b">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">
              Unread
              {unreadCount > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {unreadCount}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
            <TabsTrigger value="system">System</TabsTrigger>
          </TabsList>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="p-4 text-center">
                <Bell className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p className="text-muted-foreground">No notifications available</p>
                <p className="text-sm text-muted-foreground mt-1">Notifications will appear when alerts are triggered</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => fetchNotifications(filters)}
                >
                  Retry
                </Button>
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <Bell className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No notifications</p>
                <p className="text-sm">You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {filteredNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onAction={handleNotificationAction}
                  />
                ))}
              </div>
            )}
          </div>
        </Tabs>

        {/* Preferences Modal */}
        {showPreferences && (
          <NotificationPreferences
            isOpen={showPreferences}
            onClose={() => setShowPreferences(false)}
          />
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;
