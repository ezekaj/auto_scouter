import React, { useState } from 'react'
import { Search, SlidersHorizontal, Grid, List, Save, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { VehicleGrid } from './VehicleGrid'
import { AdvancedFilters } from './AdvancedFilters'
import { SavedSearches } from './SavedSearches'
import { useVehicles } from '@/hooks/useVehicles'


interface SearchFilters {
  make?: string
  model?: string
  minPrice?: number
  maxPrice?: number
  minYear?: number
  maxYear?: number
  maxMileage?: number
  fuelType?: string[]
  transmission?: string[]
  bodyType?: string[]
  location?: string
  radius?: number
  condition?: string
}

export const VehicleSearch: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [showSavedSearches, setShowSavedSearches] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState('relevance')
  const [filters, setFilters] = useState<SearchFilters>({})

  // Use the vehicles hook to get real data and count
  const { data: vehicleData, isLoading, error } = useVehicles({
    make: filters.make,
    model: filters.model,
    priceMin: filters.minPrice,
    priceMax: filters.maxPrice,
    yearMin: filters.minYear,
    yearMax: filters.maxYear,
    maxMileage: filters.maxMileage,
    fuelType: filters.fuelType?.[0],
    transmission: filters.transmission?.[0],
    bodyType: filters.bodyType?.[0],
    sort: sortBy,
    limit: 50
  })

  const resultsCount = vehicleData?.total || 0

  const handleFilterChange = (newFilters: Partial<SearchFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }

  const clearAllFilters = () => {
    setFilters({})
    setSearchTerm('')
  }

  const saveCurrentSearch = () => {
    // Implementation for saving search
    console.log('Saving search:', { searchTerm, filters })
  }

  const exportResults = () => {
    // Implementation for exporting results
    console.log('Exporting results')
  }

  const activeFiltersCount = Object.values(filters).filter(value =>
    value !== undefined && value !== null && value !== '' &&
    (Array.isArray(value) ? value.length > 0 : true)
  ).length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Vehicle Search</h1>
          <p className="text-muted-foreground">
            Search through thousands of vehicles with advanced filtering options.
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => setShowSavedSearches(true)}>
            <Save className="mr-2 h-4 w-4" />
            Saved Searches
          </Button>
          <Button variant="outline" onClick={exportResults}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Search Vehicles</CardTitle>
            <div className="flex items-center space-x-2">
              {activeFiltersCount > 0 && (
                <Badge variant="secondary">
                  {activeFiltersCount} filter{activeFiltersCount !== 1 ? 's' : ''} active
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                Clear All
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Main Search */}
          <div className="flex space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by make, model, VIN, or keywords..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant={showAdvancedFilters ? "default" : "outline"}
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              Advanced Filters
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
            <Button variant="outline" onClick={saveCurrentSearch}>
              <Save className="mr-2 h-4 w-4" />
              Save Search
            </Button>
          </div>

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <AdvancedFilters
              filters={filters}
              onFiltersChange={handleFilterChange}
              onClose={() => setShowAdvancedFilters(false)}
            />
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Search Results</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {isLoading ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-3 w-3 border-b border-primary mr-2"></div>
                    Loading vehicles...
                  </span>
                ) : (
                  `${resultsCount.toLocaleString()} vehicles found`
                )}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Sort Options */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-sm border rounded px-3 py-1"
              >
                <option value="relevance">Sort by Relevance</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="year_new">Year: Newest First</option>
                <option value="year_old">Year: Oldest First</option>
                <option value="mileage_low">Mileage: Low to High</option>
                <option value="date_added">Recently Added</option>
              </select>

              {/* View Mode Toggle */}
              <div className="flex items-center space-x-1">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <p className="text-red-600 mb-2">Failed to load vehicles</p>
                <p className="text-sm text-muted-foreground mb-4">Please try again later</p>
                <Button variant="outline" onClick={() => window.location.reload()}>
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <VehicleGrid viewMode={viewMode} searchTerm={searchTerm} filters={filters} />
          )}
        </CardContent>
      </Card>

      {/* Saved Searches Modal */}
      {showSavedSearches && (
        <SavedSearches
          isOpen={showSavedSearches}
          onClose={() => setShowSavedSearches(false)}
          onLoadSearch={(search) => {
            setSearchTerm(search.searchTerm || '')
            setFilters(search.filters || {})
            setShowSavedSearches(false)
          }}
        />
      )}
    </div>
  )
}
