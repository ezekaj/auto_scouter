import React from 'react'
import { X, Calendar, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface NotificationFilters {
  type?: string | null
  status?: string | null
  isRead?: boolean | null
  dateFrom?: string | null
  dateTo?: string | null
}

interface NotificationFiltersProps {
  filters: NotificationFilters
  onFiltersChange: (filters: NotificationFilters) => void
  onClose: () => void
}

const notificationTypes = [
  { value: 'new_match', label: 'New Match' },
  { value: 'price_drop', label: 'Price Drop' },
  { value: 'alert_triggered', label: 'Alert Triggered' },
  { value: 'system', label: 'System' },
]

const readStatuses = [
  { value: true, label: 'Read' },
  { value: false, label: 'Unread' },
]

export const NotificationFilters: React.FC<NotificationFiltersProps> = ({
  filters,
  onFiltersChange,
  onClose,
}) => {
  const updateFilter = (key: keyof NotificationFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const clearFilters = () => {
    onFiltersChange({
      type: null,
      status: null,
      isRead: null,
      dateFrom: null,
      dateTo: null,
    })
  }

  const hasActiveFilters = Object.values(filters).some(value => value !== null && value !== undefined)

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center">
            <Filter className="mr-2 h-4 w-4" />
            Filter Notifications
          </CardTitle>
          <div className="flex space-x-2">
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear All
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Notification Type */}
        <div>
          <label className="text-sm font-medium mb-2 block">Notification Type</label>
          <div className="flex flex-wrap gap-2">
            {notificationTypes.map((type) => (
              <Badge
                key={type.value}
                variant={filters.type === type.value ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => updateFilter('type', filters.type === type.value ? null : type.value)}
              >
                {type.label}
              </Badge>
            ))}
          </div>
        </div>

        {/* Read Status */}
        <div>
          <label className="text-sm font-medium mb-2 block">Read Status</label>
          <div className="flex flex-wrap gap-2">
            {readStatuses.map((status) => (
              <Badge
                key={status.value.toString()}
                variant={filters.isRead === status.value ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => updateFilter('isRead', filters.isRead === status.value ? null : status.value)}
              >
                {status.label}
              </Badge>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div>
          <label className="text-sm font-medium mb-2 block flex items-center">
            <Calendar className="mr-1 h-4 w-4" />
            Date Range
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">From</label>
              <Input
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => updateFilter('dateFrom', e.target.value || null)}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">To</label>
              <Input
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => updateFilter('dateTo', e.target.value || null)}
              />
            </div>
          </div>
        </div>

        {/* Priority Filter */}
        <div>
          <label className="text-sm font-medium mb-2 block">Priority</label>
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={filters.status === 'high' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => updateFilter('status', filters.status === 'high' ? null : 'high')}
            >
              High Priority
            </Badge>
            <Badge
              variant={filters.status === 'medium' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => updateFilter('status', filters.status === 'medium' ? null : 'medium')}
            >
              Medium Priority
            </Badge>
            <Badge
              variant={filters.status === 'low' ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => updateFilter('status', filters.status === 'low' ? null : 'low')}
            >
              Low Priority
            </Badge>
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-2 border-t">
            <p className="text-sm text-muted-foreground mb-2">Active Filters:</p>
            <div className="flex flex-wrap gap-1">
              {filters.type && (
                <Badge variant="secondary" className="text-xs">
                  Type: {notificationTypes.find(t => t.value === filters.type)?.label}
                </Badge>
              )}
              {filters.isRead !== null && (
                <Badge variant="secondary" className="text-xs">
                  Status: {filters.isRead ? 'Read' : 'Unread'}
                </Badge>
              )}
              {filters.dateFrom && (
                <Badge variant="secondary" className="text-xs">
                  From: {filters.dateFrom}
                </Badge>
              )}
              {filters.dateTo && (
                <Badge variant="secondary" className="text-xs">
                  To: {filters.dateTo}
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary" className="text-xs">
                  Priority: {filters.status}
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
