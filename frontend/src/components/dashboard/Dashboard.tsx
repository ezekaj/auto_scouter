import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, Grid, List, Plus, AlertTriangle, Car, Bell, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'



export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showFilters, setShowFilters] = useState(false)

  // Add debug logging
  React.useEffect(() => {
    console.log('Dashboard component mounted')
  }, [])

  // Navigation handlers
  const handleCreateAlert = () => {
    console.log('Navigating to alerts page')
    navigate('/alerts')
  }

  const handleAdvancedSearch = () => {
    console.log('Navigating to search page')
    navigate('/search')
  }

  const handleSavedSearches = () => {
    console.log('Navigating to saved vehicles')
    navigate('/saved')
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Welcome back, Petrit!</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Here's what's happening with your vehicle search and alerts.
          </p>
        </div>
        <Button
          className="auto-scouter-gradient w-full sm:w-auto"
          aria-label="Create a new vehicle alert"
          onClick={handleCreateAlert}
        >
          <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
          <span className="sm:inline">Create Alert</span>
        </Button>
      </header>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Alerts
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Monitoring vehicle matches</p>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              New Matches
            </CardTitle>
            <Car className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">This week</p>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Notifications
            </CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-muted-foreground">Unread notifications</p>
          </CardContent>
        </Card>
        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Vehicles Viewed
            </CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <main className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column - Vehicle Listings */}
        <section className="xl:col-span-2 space-y-6" aria-labelledby="vehicle-matches-heading">
          {/* Search and Filters */}
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle id="vehicle-matches-heading" className="text-lg">Recent Vehicle Matches</CardTitle>
                <div className="flex items-center space-x-2" role="group" aria-label="View mode selection">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                    aria-label="Grid view"
                    aria-pressed={viewMode === 'grid'}
                  >
                    <Grid className="h-4 w-4" aria-hidden="true" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                    aria-label="List view"
                    aria-pressed={viewMode === 'list'}
                  >
                    <List className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search Bar */}
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" aria-hidden="true" />
                  <Input
                    placeholder="Search vehicles..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                    aria-label="Search vehicles by make, model, or other criteria"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className="w-full sm:w-auto"
                  aria-expanded={showFilters}
                  aria-controls="vehicle-filters"
                  aria-label={showFilters ? 'Hide filters' : 'Show filters'}
                >
                  <Filter className="mr-2 h-4 w-4" aria-hidden="true" />
                  <span>Filters</span>
                </Button>
              </div>

              {/* Quick Filters */}
              {showFilters && (
                <div id="vehicle-filters" className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">Filters will be available here</p>
                </div>
              )}

              {/* Vehicle Grid/List */}
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="card-hover">
                    <CardContent className="p-4">
                      <h3 className="font-semibold mb-2">Sample Vehicle 1</h3>
                      <p className="text-sm text-muted-foreground">BMW X5 2020 - €45,000</p>
                    </CardContent>
                  </Card>
                  <Card className="card-hover">
                    <CardContent className="p-4">
                      <h3 className="font-semibold mb-2">Sample Vehicle 2</h3>
                      <p className="text-sm text-muted-foreground">Audi A4 2019 - €35,000</p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Right Column - Sidebar Content */}
        <aside className="space-y-6" aria-label="Dashboard sidebar">
          {/* Alerts Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">No active alerts at the moment</p>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">No recent activity</p>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="outline"
                className="w-full justify-start"
                aria-label="Create a new vehicle alert"
                onClick={handleCreateAlert}
              >
                <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                Create New Alert
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                aria-label="Open advanced vehicle search"
                onClick={handleAdvancedSearch}
              >
                <Search className="mr-2 h-4 w-4" aria-hidden="true" />
                Advanced Search
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                aria-label="View saved vehicle searches"
                onClick={handleSavedSearches}
              >
                <Filter className="mr-2 h-4 w-4" aria-hidden="true" />
                Saved Searches
              </Button>
            </CardContent>
          </Card>
        </aside>
      </main>
    </div>
  )
}
