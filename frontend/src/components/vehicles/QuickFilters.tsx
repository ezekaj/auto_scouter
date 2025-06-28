import React, { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'


interface FilterState {
  priceRange: [number, number]
  makes: string[]
  yearRange: [number, number]
  fuelTypes: string[]
  transmissions: string[]
}

const popularMakes = ['BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Porsche', 'Ford']
const fuelTypes = ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'LPG']
const transmissions = ['Manual', 'Automatic']

export const QuickFilters: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    priceRange: [0, 100000],
    makes: [],
    yearRange: [2010, 2024],
    fuelTypes: [],
    transmissions: [],
  })

  const toggleMake = (make: string) => {
    setFilters(prev => ({
      ...prev,
      makes: prev.makes.includes(make)
        ? prev.makes.filter(m => m !== make)
        : [...prev.makes, make]
    }))
  }

  const toggleFuelType = (fuelType: string) => {
    setFilters(prev => ({
      ...prev,
      fuelTypes: prev.fuelTypes.includes(fuelType)
        ? prev.fuelTypes.filter(f => f !== fuelType)
        : [...prev.fuelTypes, fuelType]
    }))
  }

  const toggleTransmission = (transmission: string) => {
    setFilters(prev => ({
      ...prev,
      transmissions: prev.transmissions.includes(transmission)
        ? prev.transmissions.filter(t => t !== transmission)
        : [...prev.transmissions, transmission]
    }))
  }

  const clearFilters = () => {
    setFilters({
      priceRange: [0, 100000],
      makes: [],
      yearRange: [2010, 2024],
      fuelTypes: [],
      transmissions: [],
    })
  }

  const hasActiveFilters = 
    filters.makes.length > 0 || 
    filters.fuelTypes.length > 0 || 
    filters.transmissions.length > 0 ||
    filters.priceRange[0] > 0 ||
    filters.priceRange[1] < 100000 ||
    filters.yearRange[0] > 2010 ||
    filters.yearRange[1] < 2024

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Quick Filters</h3>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="mr-1 h-3 w-3" />
            Clear All
          </Button>
        )}
      </div>

      {/* Price Range */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Price Range</label>
        <div className="flex items-center space-x-2">
          <Input
            type="number"
            placeholder="Min"
            value={filters.priceRange[0] || ''}
            onChange={(e) => setFilters(prev => ({
              ...prev,
              priceRange: [parseInt(e.target.value) || 0, prev.priceRange[1]]
            }))}
            className="w-24"
          />
          <span className="text-muted-foreground">to</span>
          <Input
            type="number"
            placeholder="Max"
            value={filters.priceRange[1] || ''}
            onChange={(e) => setFilters(prev => ({
              ...prev,
              priceRange: [prev.priceRange[0], parseInt(e.target.value) || 100000]
            }))}
            className="w-24"
          />
          <span className="text-sm text-muted-foreground">EUR</span>
        </div>
      </div>

      {/* Year Range */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Year Range</label>
        <div className="flex items-center space-x-2">
          <Input
            type="number"
            placeholder="From"
            value={filters.yearRange[0] || ''}
            onChange={(e) => setFilters(prev => ({
              ...prev,
              yearRange: [parseInt(e.target.value) || 2010, prev.yearRange[1]]
            }))}
            className="w-20"
          />
          <span className="text-muted-foreground">to</span>
          <Input
            type="number"
            placeholder="To"
            value={filters.yearRange[1] || ''}
            onChange={(e) => setFilters(prev => ({
              ...prev,
              yearRange: [prev.yearRange[0], parseInt(e.target.value) || 2024]
            }))}
            className="w-20"
          />
        </div>
      </div>

      {/* Makes */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Popular Makes</label>
        <div className="flex flex-wrap gap-2">
          {popularMakes.map((make) => (
            <Badge
              key={make}
              variant={filters.makes.includes(make) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleMake(make)}
            >
              {make}
            </Badge>
          ))}
        </div>
      </div>

      {/* Fuel Types */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Fuel Type</label>
        <div className="flex flex-wrap gap-2">
          {fuelTypes.map((fuelType) => (
            <Badge
              key={fuelType}
              variant={filters.fuelTypes.includes(fuelType) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleFuelType(fuelType)}
            >
              {fuelType}
            </Badge>
          ))}
        </div>
      </div>

      {/* Transmission */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Transmission</label>
        <div className="flex flex-wrap gap-2">
          {transmissions.map((transmission) => (
            <Badge
              key={transmission}
              variant={filters.transmissions.includes(transmission) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleTransmission(transmission)}
            >
              {transmission}
            </Badge>
          ))}
        </div>
      </div>

      {/* Apply Filters Button */}
      <div className="pt-2">
        <Button className="w-full">
          Apply Filters
        </Button>
      </div>
    </div>
  )
}
