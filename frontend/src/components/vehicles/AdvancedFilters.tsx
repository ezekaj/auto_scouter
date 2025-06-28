import React, { useState } from 'react'
import { X, MapPin, DollarSign, Calendar, Gauge, Fuel, Settings, Car } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

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

interface AdvancedFiltersProps {
  filters: SearchFilters
  onFiltersChange: (filters: Partial<SearchFilters>) => void
  onClose: () => void
}

const popularMakes = [
  'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Porsche', 'Ford',
  'Toyota', 'Honda', 'Nissan', 'Hyundai', 'Kia', 'Mazda'
]

const fuelTypes = ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid', 'LPG', 'CNG']
const transmissions = ['Manual', 'Automatic', 'CVT', 'Semi-automatic']
const bodyTypes = ['Sedan', 'Hatchback', 'SUV', 'Wagon', 'Coupe', 'Convertible', 'Pickup', 'Van']
const conditions = ['New', 'Used', 'Certified Pre-owned', 'Demo']

export const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onClose,
}) => {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setLocalFilters(prev => ({ ...prev, [key]: value }))
  }

  const toggleArrayFilter = (key: keyof SearchFilters, value: string) => {
    const currentArray = (localFilters[key] as string[]) || []
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateFilter(key, newArray)
  }

  const applyFilters = () => {
    onFiltersChange(localFilters)
    onClose()
  }

  const clearFilters = () => {
    setLocalFilters({})
    onFiltersChange({})
  }

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Advanced Filters</CardTitle>
          <div className="flex space-x-2">
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear All
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic">Basic</TabsTrigger>
            <TabsTrigger value="specs">Specs</TabsTrigger>
            <TabsTrigger value="location">Location</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-6 mt-6">
            {/* Make & Model */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Make</label>
                  <Input
                    placeholder="Any make"
                    value={localFilters.make || ''}
                    onChange={(e) => updateFilter('make', e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Model</label>
                  <Input
                    placeholder="Any model"
                    value={localFilters.model || ''}
                    onChange={(e) => updateFilter('model', e.target.value)}
                  />
                </div>
              </div>

              {/* Popular Makes */}
              <div>
                <label className="text-sm font-medium mb-2 block">Popular Makes</label>
                <div className="flex flex-wrap gap-2">
                  {popularMakes.map((make) => (
                    <Badge
                      key={make}
                      variant={localFilters.make === make ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => updateFilter('make', localFilters.make === make ? '' : make)}
                    >
                      {make}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            {/* Price Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <DollarSign className="mr-1 h-4 w-4" />
                Price Range (EUR)
              </label>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  type="number"
                  placeholder="Min price"
                  value={localFilters.minPrice || ''}
                  onChange={(e) => updateFilter('minPrice', parseInt(e.target.value) || undefined)}
                />
                <Input
                  type="number"
                  placeholder="Max price"
                  value={localFilters.maxPrice || ''}
                  onChange={(e) => updateFilter('maxPrice', parseInt(e.target.value) || undefined)}
                />
              </div>
            </div>

            {/* Year Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Calendar className="mr-1 h-4 w-4" />
                Year Range
              </label>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  type="number"
                  placeholder="From year"
                  value={localFilters.minYear || ''}
                  onChange={(e) => updateFilter('minYear', parseInt(e.target.value) || undefined)}
                />
                <Input
                  type="number"
                  placeholder="To year"
                  value={localFilters.maxYear || ''}
                  onChange={(e) => updateFilter('maxYear', parseInt(e.target.value) || undefined)}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="specs" className="space-y-6 mt-6">
            {/* Mileage */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Gauge className="mr-1 h-4 w-4" />
                Maximum Mileage (km)
              </label>
              <Input
                type="number"
                placeholder="Max mileage"
                value={localFilters.maxMileage || ''}
                onChange={(e) => updateFilter('maxMileage', parseInt(e.target.value) || undefined)}
              />
            </div>

            {/* Fuel Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Fuel className="mr-1 h-4 w-4" />
                Fuel Type
              </label>
              <div className="flex flex-wrap gap-2">
                {fuelTypes.map((fuel) => (
                  <Badge
                    key={fuel}
                    variant={(localFilters.fuelType || []).includes(fuel) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => toggleArrayFilter('fuelType', fuel)}
                  >
                    {fuel}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Transmission */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Settings className="mr-1 h-4 w-4" />
                Transmission
              </label>
              <div className="flex flex-wrap gap-2">
                {transmissions.map((trans) => (
                  <Badge
                    key={trans}
                    variant={(localFilters.transmission || []).includes(trans) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => toggleArrayFilter('transmission', trans)}
                  >
                    {trans}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Body Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <Car className="mr-1 h-4 w-4" />
                Body Type
              </label>
              <div className="flex flex-wrap gap-2">
                {bodyTypes.map((body) => (
                  <Badge
                    key={body}
                    variant={(localFilters.bodyType || []).includes(body) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => toggleArrayFilter('bodyType', body)}
                  >
                    {body}
                  </Badge>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="location" className="space-y-6 mt-6">
            {/* Location */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center">
                <MapPin className="mr-1 h-4 w-4" />
                Location
              </label>
              <Input
                placeholder="City, region, or postal code"
                value={localFilters.location || ''}
                onChange={(e) => updateFilter('location', e.target.value)}
              />
            </div>

            {/* Search Radius */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Search Radius (km)</label>
              <select
                value={localFilters.radius || ''}
                onChange={(e) => updateFilter('radius', parseInt(e.target.value) || undefined)}
                className="w-full border rounded px-3 py-2"
              >
                <option value="">Any distance</option>
                <option value="25">25 km</option>
                <option value="50">50 km</option>
                <option value="100">100 km</option>
                <option value="200">200 km</option>
                <option value="500">500 km</option>
              </select>
            </div>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6 mt-6">
            {/* Condition */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Condition</label>
              <div className="flex flex-wrap gap-2">
                {conditions.map((condition) => (
                  <Badge
                    key={condition}
                    variant={localFilters.condition === condition ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => updateFilter('condition', localFilters.condition === condition ? '' : condition)}
                  >
                    {condition}
                  </Badge>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Apply Filters Button */}
        <div className="flex justify-end space-x-2 mt-6 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={applyFilters} className="auto-scouter-gradient">
            Apply Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
