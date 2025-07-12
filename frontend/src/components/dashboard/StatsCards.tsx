import React from 'react'
import { TrendingUp, TrendingDown, AlertTriangle, Car, Bell, Eye } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useDashboardStats } from '@/hooks/useDashboard'

export const StatsCards: React.FC = () => {
  const { data: dashboardStats, isLoading, error } = useDashboardStats()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="card-hover">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted animate-pulse rounded"></div>
              <div className="h-4 w-4 bg-muted animate-pulse rounded"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded mb-2"></div>
              <div className="h-3 w-24 bg-muted animate-pulse rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !dashboardStats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="card-hover">
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground text-sm">No dashboard statistics available</p>
            <p className="text-xs text-muted-foreground mt-1">Data will appear when the system is active</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const stats = [
    {
      title: 'Active Alerts',
      value: dashboardStats.activeAlerts.toString(),
      change: '+2',
      changeType: 'increase' as const,
      icon: AlertTriangle,
      description: 'Monitoring vehicle matches',
    },
    {
      title: 'New Matches',
      value: dashboardStats.newMatches.toString(),
      change: '+12',
      changeType: 'increase' as const,
      icon: Car,
      description: 'This week',
    },
    {
      title: 'Notifications',
      value: dashboardStats.unreadNotifications.toString(),
      change: '-5',
      changeType: 'decrease' as const,
      icon: Bell,
      description: 'Unread notifications',
    },
    {
      title: 'Vehicles Viewed',
      value: dashboardStats.vehiclesViewed.toString(),
      change: '+28',
      changeType: 'increase' as const,
      icon: Eye,
      description: 'Last 30 days',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title} className="card-hover">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">
                    {stat.description}
                  </p>
                </div>
                <Badge
                  variant={stat.changeType === 'increase' ? 'success' : 'warning'}
                  className="flex items-center space-x-1"
                >
                  {stat.changeType === 'increase' ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>{stat.change}</span>
                </Badge>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
