import React from 'react'
import { Plus, Eye } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'

interface Alert {
  id: string
  name: string
  criteria: string
  matches: number
  isActive: boolean
  lastTriggered?: Date
}

const mockAlerts: Alert[] = [
  {
    id: '1',
    name: 'BMW 3 Series',
    criteria: 'Under €25,000, 2015+',
    matches: 12,
    isActive: true,
    lastTriggered: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
  },
  {
    id: '2',
    name: 'Audi A4 Diesel',
    criteria: 'Diesel, Manual, €20-30k',
    matches: 8,
    isActive: true,
    lastTriggered: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
  },
  {
    id: '3',
    name: 'Mercedes C-Class',
    criteria: 'Automatic, <80k km',
    matches: 5,
    isActive: false,
  },
  {
    id: '4',
    name: 'VW Golf GTI',
    criteria: 'Manual, 2018+',
    matches: 15,
    isActive: true,
    lastTriggered: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
  },
]

export const AlertsSummary: React.FC = () => {
  const activeAlerts = mockAlerts.filter(alert => alert.isActive)
  const totalMatches = mockAlerts.reduce((sum, alert) => sum + alert.matches, 0)

  const toggleAlert = (alertId: string) => {
    // In a real app, this would make an API call
    console.log('Toggle alert:', alertId)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">My Alerts</CardTitle>
          <Button size="sm" className="auto-scouter-gradient">
            <Plus className="mr-1 h-3 w-3" />
            New
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold text-primary">{activeAlerts.length}</div>
            <div className="text-xs text-muted-foreground">Active Alerts</div>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{totalMatches}</div>
            <div className="text-xs text-muted-foreground">Total Matches</div>
          </div>
        </div>

        {/* Alert List */}
        <div className="space-y-3">
          {mockAlerts.slice(0, 4).map((alert) => (
            <div
              key={alert.id}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h4 className="font-medium text-sm truncate">{alert.name}</h4>
                  <Badge variant={alert.isActive ? 'success' : 'secondary'} className="text-xs">
                    {alert.matches}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground truncate">
                  {alert.criteria}
                </p>
                {alert.lastTriggered && (
                  <p className="text-xs text-muted-foreground">
                    Last: {alert.lastTriggered.toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={alert.isActive}
                  onCheckedChange={() => toggleAlert(alert.id)}
                />
              </div>
            </div>
          ))}
        </div>

        {/* View All Button */}
        <Button variant="outline" className="w-full">
          <Eye className="mr-2 h-4 w-4" />
          View All Alerts
        </Button>
      </CardContent>
    </Card>
  )
}
