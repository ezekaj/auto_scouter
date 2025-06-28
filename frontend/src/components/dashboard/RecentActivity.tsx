import React from 'react'
import { Clock, Car, AlertTriangle, Eye } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatRelativeTime } from '@/lib/utils'
import { useDashboardStats } from '@/hooks/useDashboard'

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'vehicle_match':
      return Car
    case 'alert_created':
      return AlertTriangle
    case 'vehicle_viewed':
      return Eye
    case 'alert_triggered':
      return AlertTriangle
    default:
      return Clock
  }
}

const getActivityBadge = (type: string) => {
  switch (type) {
    case 'vehicle_match':
      return { text: 'Match', variant: 'success' as const }
    case 'alert_created':
      return { text: 'Alert', variant: 'default' as const }
    case 'vehicle_viewed':
      return { text: 'Viewed', variant: 'secondary' as const }
    case 'alert_triggered':
      return { text: 'Triggered', variant: 'warning' as const }
    default:
      return { text: 'Activity', variant: 'secondary' as const }
  }
}

export const RecentActivity: React.FC = () => {
  const { data: dashboardStats, isLoading, error } = useDashboardStats()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start space-x-3 p-3">
                <div className="w-8 h-8 bg-muted animate-pulse rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 w-32 bg-muted animate-pulse rounded mb-2"></div>
                  <div className="h-3 w-48 bg-muted animate-pulse rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !dashboardStats?.recentActivity) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            No recent activity available
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {dashboardStats.recentActivity.map((activity) => {
            const Icon = getActivityIcon(activity.type)
            const badge = getActivityBadge(activity.type)
            return (
              <div
                key={activity.id}
                className="flex items-start space-x-3 p-3 rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
              >
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-foreground">
                      {activity.title}
                    </p>
                    <Badge variant={badge.variant} className="text-xs">
                      {badge.text}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatRelativeTime(new Date(activity.timestamp))}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
