import React, { useState } from 'react'
import { ArrowLeft, Heart, Share2, MapPin, Calendar, Gauge, Fuel, Settings, ExternalLink, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useVehicle } from '@/hooks/useVehicles'


interface VehicleDetailProps {
  vehicleId: string
  onBack: () => void
}

export const VehicleDetail: React.FC<VehicleDetailProps> = ({ vehicleId, onBack }) => {

  const [isFavorited, setIsFavorited] = useState(false)

  // Fetch vehicle data from API
  const { data: vehicle, isLoading, error } = useVehicle(vehicleId)

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading vehicle details...</p>
        </div>
      </div>
    )
  }

  if (error || !vehicle) {
    return (
      <div className="max-w-7xl mx-auto p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load vehicle details</p>
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Search
          </Button>
        </div>
      </div>
    )
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
    }).format(price)
  }

  const formatMileage = (mileage: number) => {
    return new Intl.NumberFormat('en-US').format(mileage)
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack} className="flex items-center">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Search
        </Button>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFavorited(!isFavorited)}
          >
            <Heart className={`h-4 w-4 mr-2 ${isFavorited ? 'fill-red-500 text-red-500' : ''}`} />
            {isFavorited ? 'Saved' : 'Save'}
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Images and Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Image Gallery */}
          <Card>
            <CardContent className="p-0">
              <div className="relative">
                <img
                  src={vehicle.imageUrl || '/placeholder-car.jpg'}
                  alt={`${vehicle.make} ${vehicle.model}`}
                  className="w-full h-96 object-cover rounded-t-lg"
                />
              </div>
            </CardContent>
          </Card>

          {/* Vehicle Details Tabs */}
          <Card>
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="features">Features</TabsTrigger>
                <TabsTrigger value="history">History</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="text-sm">Year: {vehicle.year}</span>
                    </div>
                    <div className="flex items-center">
                      <Gauge className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="text-sm">Mileage: {vehicle.mileage ? formatMileage(vehicle.mileage) : 'N/A'} miles</span>
                    </div>
                    <div className="flex items-center">
                      <Fuel className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="text-sm">Fuel: {vehicle.fuelType}</span>
                    </div>
                    <div className="flex items-center">
                      <Settings className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="text-sm">Transmission: {vehicle.transmission}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="text-sm">
                      <span className="font-medium">Body Type:</span> {vehicle.bodyType}
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Source:</span> {vehicle.source}
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Location:</span> {vehicle.location}
                    </div>
                  </div>
                </div>
                <div className="mt-6">
                  <h4 className="font-medium mb-2">Vehicle URL</h4>
                  <a href={vehicle.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                    View Original Listing
                  </a>
                </div>
              </TabsContent>
              
              <TabsContent value="features" className="p-6">
                <div className="text-sm text-muted-foreground">
                  Features information not available in current data structure.
                </div>
              </TabsContent>
              
              <TabsContent value="history" className="p-6">
                <div className="space-y-4">
                  <div className="text-sm">
                    <span className="font-medium">Scraped At:</span> {new Date(vehicle.scrapedAt).toLocaleDateString()}
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Source:</span> {vehicle.source}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Additional history information not available in current data structure.
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </Card>
        </div>

        {/* Right Column - Price and Contact */}
        <div className="space-y-6">
          {/* Price Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl font-bold">
                {vehicle.price ? formatPrice(vehicle.price) : 'Price not available'}
              </CardTitle>
              <div className="flex items-center text-muted-foreground">
                <MapPin className="h-4 w-4 mr-1" />
                <span className="text-sm">{vehicle.location}</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm">
                <span className="font-medium">Source:</span> {vehicle.source}
              </div>

              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={() => window.open(vehicle.url, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Original Listing
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                Create Alert for Similar
              </Button>
              <Button variant="outline" className="w-full justify-start">
                Schedule Test Drive
              </Button>
              <Button variant="outline" className="w-full justify-start">
                Get Financing Quote
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
