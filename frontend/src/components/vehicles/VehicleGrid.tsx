import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, ExternalLink, MapPin, Calendar, Gauge, Fuel } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatPrice, formatNumber } from '@/lib/utils'
import { useVehicles } from '@/hooks/useVehicles'

interface VehicleGridProps {
  viewMode: 'grid' | 'list'
  searchTerm: string
  filters?: any
}

export const VehicleGrid: React.FC<VehicleGridProps> = ({ viewMode, searchTerm, filters }) => {
  const [favorites, setFavorites] = useState<Set<string>>(new Set())

  // Use the API hook to fetch vehicles
  const { data: vehicleData, isLoading, error } = useVehicles({
    make: filters?.make,
    model: filters?.model,
    priceMin: filters?.minPrice,
    priceMax: filters?.maxPrice,
    yearMin: filters?.minYear,
    yearMax: filters?.maxYear,
    maxMileage: filters?.maxMileage,
    fuelType: filters?.fuelType?.[0],
    transmission: filters?.transmission?.[0],
    bodyType: filters?.bodyType?.[0],
    limit: 20
  })

  // Filter vehicles based on search term
  const filteredVehicles = React.useMemo(() => {
    if (!vehicleData?.vehicles) return []

    if (!searchTerm) return vehicleData.vehicles

    return vehicleData.vehicles.filter(vehicle =>
      `${vehicle.make} ${vehicle.model}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      vehicle.location.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [vehicleData?.vehicles, searchTerm])

  const toggleFavorite = (vehicleId: string) => {
    setFavorites(prev => {
      const newFavorites = new Set(prev)
      if (newFavorites.has(vehicleId)) {
        newFavorites.delete(vehicleId)
      } else {
        newFavorites.add(vehicleId)
      }
      return newFavorites
    })
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading vehicles...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load vehicles</p>
          <p className="text-sm text-muted-foreground">Please try again later</p>
        </div>
      </div>
    )
  }

  // Empty state
  if (!filteredVehicles.length) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-muted-foreground mb-2">No vehicles found</p>
          <p className="text-sm text-muted-foreground">Try adjusting your search criteria</p>
        </div>
      </div>
    )
  }

  if (viewMode === 'list') {
    return (
      <div className="space-y-4" role="list" aria-label="Vehicle listings">
        {filteredVehicles.map((vehicle) => (
          <Card key={vehicle.id} className="card-hover" role="listitem">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-20 h-16 bg-muted rounded-lg flex items-center justify-center" aria-hidden="true">
                    <span className="text-xs text-muted-foreground">No Image</span>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold">{vehicle.make} {vehicle.model}</h3>
                      {vehicle.scrapedAt && new Date(vehicle.scrapedAt) > new Date(Date.now() - 24 * 60 * 60 * 1000) && <Badge variant="success">New</Badge>}
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center">
                        <Calendar className="mr-1 h-3 w-3" aria-hidden="true" />
                        <span className="sr-only">Year: </span>{vehicle.year}
                      </span>
                      <span className="flex items-center">
                        <Gauge className="mr-1 h-3 w-3" aria-hidden="true" />
                        <span className="sr-only">Mileage: </span>{formatNumber(vehicle.mileage || 0)} km
                      </span>
                      <span className="flex items-center">
                        <Fuel className="mr-1 h-3 w-3" aria-hidden="true" />
                        <span className="sr-only">Fuel type: </span>{vehicle.fuelType}
                      </span>
                      <span className="flex items-center">
                        <MapPin className="mr-1 h-3 w-3" aria-hidden="true" />
                        <span className="sr-only">Location: </span>{vehicle.location}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold">{formatPrice(vehicle.price || 0)}</div>
                    <div className="text-sm text-muted-foreground">{vehicle.transmission}</div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => toggleFavorite(vehicle.id)}
                      aria-label={favorites.has(vehicle.id) ? `Remove ${vehicle.make} ${vehicle.model} from favorites` : `Add ${vehicle.make} ${vehicle.model} to favorites`}
                    >
                      <Heart
                        className={`h-4 w-4 ${
                          favorites.has(vehicle.id) ? 'fill-red-500 text-red-500' : ''
                        }`}
                        aria-hidden="true"
                      />
                    </Button>
                    <Link to={`/vehicle/${vehicle.id}`}>
                      <Button variant="outline" size="sm" aria-label={`View details for ${vehicle.make} ${vehicle.model}`}>
                        <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4" role="grid" aria-label="Vehicle listings">
      {filteredVehicles.map((vehicle) => (
        <Card key={vehicle.id} className="card-hover" role="gridcell">
          <CardContent className="p-4">
            <div className="space-y-3">
              {/* Image placeholder */}
              <div className="w-full h-48 bg-muted rounded-lg flex items-center justify-center" aria-hidden="true">
                <span className="text-muted-foreground">No Image Available</span>
              </div>

              {/* Vehicle info */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">
                    {vehicle.make} {vehicle.model}
                  </h3>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => toggleFavorite(vehicle.id)}
                  >
                    <Heart
                      className={`h-4 w-4 ${
                        favorites.has(vehicle.id) ? 'fill-red-500 text-red-500' : ''
                      }`}
                    />
                  </Button>
                </div>

                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="outline">{vehicle.year}</Badge>
                  <Badge variant="outline">{vehicle.transmission}</Badge>
                  {vehicle.scrapedAt && new Date(vehicle.scrapedAt) > new Date(Date.now() - 24 * 60 * 60 * 1000) && <Badge variant="success">New</Badge>}
                </div>

                <div className="grid grid-cols-2 gap-2 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center">
                    <Gauge className="mr-1 h-3 w-3" />
                    {formatNumber(vehicle.mileage || 0)} km
                  </span>
                  <span className="flex items-center">
                    <Fuel className="mr-1 h-3 w-3" />
                    {vehicle.fuelType}
                  </span>
                  <span className="flex items-center col-span-2">
                    <MapPin className="mr-1 h-3 w-3" />
                    {vehicle.location}
                  </span>
                </div>
              </div>

              {/* Price and action */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="text-2xl font-bold">{formatPrice(vehicle.price || 0)}</div>
                <Link to={`/vehicle/${vehicle.id}`}>
                  <Button variant="outline" size="sm">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    View Details
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
