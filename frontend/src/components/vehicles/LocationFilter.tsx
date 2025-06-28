import React, { useState } from 'react'
import { MapPin, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface LocationFilterProps {
  onLocationChange: (location: string, radius: number) => void
  initialLocation?: string
  initialRadius?: number
}

export const LocationFilter: React.FC<LocationFilterProps> = ({
  onLocationChange,
  initialLocation = '',
  initialRadius = 25
}) => {
  const [location, setLocation] = useState(initialLocation)
  const [radius, setRadius] = useState(initialRadius)

  const handleApply = () => {
    onLocationChange(location, radius)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <MapPin className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Location</span>
      </div>
      
      <div className="space-y-3">
        <div>
          <label htmlFor="location" className="text-sm text-muted-foreground">
            City, State or ZIP Code
          </label>
          <Input
            id="location"
            type="text"
            placeholder="Enter location..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="mt-1"
          />
        </div>
        
        <div>
          <label htmlFor="radius" className="text-sm text-muted-foreground">
            Search Radius: {radius} miles
          </label>
          <input
            id="radius"
            type="range"
            min="5"
            max="100"
            step="5"
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value))}
            className="w-full mt-1"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>5 mi</span>
            <span>100 mi</span>
          </div>
        </div>
        
        <Button onClick={handleApply} className="w-full">
          <Search className="h-4 w-4 mr-2" />
          Apply Location Filter
        </Button>
      </div>
    </div>
  )
}
