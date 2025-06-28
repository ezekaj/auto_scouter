import React, { useState } from 'react'
import { ArrowLeft, Heart, Share2, MapPin, Calendar, Gauge, Fuel, Settings, Phone, Mail, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface VehicleDetailProps {
  vehicleId: string
  onBack: () => void
}

interface Vehicle {
  id: string
  make: string
  model: string
  year: number
  price: number
  mileage: number
  fuelType: string
  transmission: string
  bodyType: string
  color: string
  location: string
  dealer: string
  description: string
  features: string[]
  images: string[]
  vin: string
  engineSize: string
  doors: number
  seats: number
  isNew: boolean
  listingUrl: string
  contactPhone?: string
  contactEmail?: string
}

// Mock data - in real app this would come from API
const mockVehicle: Vehicle = {
  id: '1',
  make: 'BMW',
  model: '3 Series',
  year: 2022,
  price: 35000,
  mileage: 15000,
  fuelType: 'Gasoline',
  transmission: 'Automatic',
  bodyType: 'Sedan',
  color: 'Alpine White',
  location: 'San Francisco, CA',
  dealer: 'BMW of San Francisco',
  description: 'Excellent condition BMW 3 Series with premium package. One owner, clean title, full service history.',
  features: ['Premium Package', 'Navigation System', 'Leather Seats', 'Sunroof', 'Heated Seats', 'Backup Camera'],
  images: ['/api/placeholder/800/600', '/api/placeholder/800/600', '/api/placeholder/800/600'],
  vin: 'WBA8E9G50HNU12345',
  engineSize: '2.0L Turbo',
  doors: 4,
  seats: 5,
  isNew: false,
  listingUrl: 'https://example.com/vehicle/1',
  contactPhone: '(555) 123-4567',
  contactEmail: 'sales@bmwsf.com'
}

export const VehicleDetail: React.FC<VehicleDetailProps> = ({ vehicleId, onBack }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [isFavorited, setIsFavorited] = useState(false)

  // In real app, fetch vehicle data based on vehicleId
  // For now, using mock data regardless of vehicleId
  const vehicle = mockVehicle

  // Suppress unused parameter warning - vehicleId will be used when API is connected
  console.log('Vehicle ID:', vehicleId)

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
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
                  src={vehicle.images[currentImageIndex]}
                  alt={`${vehicle.make} ${vehicle.model}`}
                  className="w-full h-96 object-cover rounded-t-lg"
                />
                {vehicle.isNew && (
                  <Badge className="absolute top-4 left-4 bg-green-500">
                    New
                  </Badge>
                )}
              </div>
              {vehicle.images.length > 1 && (
                <div className="flex space-x-2 p-4">
                  {vehicle.images.map((image, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`w-20 h-16 rounded border-2 overflow-hidden ${
                        index === currentImageIndex ? 'border-blue-500' : 'border-gray-200'
                      }`}
                    >
                      <img
                        src={image}
                        alt={`View ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              )}
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
                      <span className="text-sm">Mileage: {formatMileage(vehicle.mileage)} miles</span>
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
                      <span className="font-medium">Color:</span> {vehicle.color}
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Engine:</span> {vehicle.engineSize}
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Doors:</span> {vehicle.doors}
                    </div>
                  </div>
                </div>
                <div className="mt-6">
                  <h4 className="font-medium mb-2">Description</h4>
                  <p className="text-sm text-muted-foreground">{vehicle.description}</p>
                </div>
              </TabsContent>
              
              <TabsContent value="features" className="p-6">
                <div className="grid grid-cols-2 gap-2">
                  {vehicle.features.map((feature, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="history" className="p-6">
                <div className="space-y-4">
                  <div className="text-sm">
                    <span className="font-medium">VIN:</span> {vehicle.vin}
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Title:</span> Clean
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Accidents:</span> None reported
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Service Records:</span> Available
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
                {formatPrice(vehicle.price)}
              </CardTitle>
              <div className="flex items-center text-muted-foreground">
                <MapPin className="h-4 w-4 mr-1" />
                <span className="text-sm">{vehicle.location}</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm">
                <span className="font-medium">Dealer:</span> {vehicle.dealer}
              </div>
              
              <div className="space-y-2">
                {vehicle.contactPhone && (
                  <Button variant="outline" className="w-full justify-start">
                    <Phone className="h-4 w-4 mr-2" />
                    {vehicle.contactPhone}
                  </Button>
                )}
                {vehicle.contactEmail && (
                  <Button variant="outline" className="w-full justify-start">
                    <Mail className="h-4 w-4 mr-2" />
                    Contact Dealer
                  </Button>
                )}
                <Button className="w-full">
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
