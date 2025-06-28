import React, { useState, useEffect } from 'react'
import { Save, TestTube } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface AlertFormData {
  name: string
  description?: string
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
  city?: string
  region?: string
  locationRadius?: number
  minEnginePower?: number
  maxEnginePower?: number
  condition?: string
  isActive: boolean
  notificationFrequency: string
  maxNotificationsPerDay: number
}

interface AlertFormProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: AlertFormData) => void
  initialData?: Partial<AlertFormData>
  mode: 'create' | 'edit'
}

const fuelTypes = ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid', 'LPG', 'CNG']
const transmissions = ['Manual', 'Automatic', 'CVT', 'Semi-automatic']
const bodyTypes = ['Sedan', 'Hatchback', 'SUV', 'Wagon', 'Coupe', 'Convertible', 'Pickup', 'Van']


export const AlertForm: React.FC<AlertFormProps> = ({
  isOpen,
  onClose,
  onSave,
  initialData = {},
  mode,
}) => {
  const [formData, setFormData] = useState<AlertFormData>({
    name: '',
    description: '',
    make: '',
    model: '',
    minPrice: undefined,
    maxPrice: undefined,
    minYear: undefined,
    maxYear: undefined,
    maxMileage: undefined,
    fuelType: [],
    transmission: [],
    bodyType: [],
    city: '',
    region: '',
    locationRadius: undefined,
    minEnginePower: undefined,
    maxEnginePower: undefined,
    condition: '',
    isActive: true,
    notificationFrequency: 'immediate',
    maxNotificationsPerDay: 5,
    ...initialData,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        description: '',
        make: '',
        model: '',
        minPrice: undefined,
        maxPrice: undefined,
        minYear: undefined,
        maxYear: undefined,
        maxMileage: undefined,
        fuelType: [],
        transmission: [],
        bodyType: [],
        city: '',
        region: '',
        locationRadius: undefined,
        minEnginePower: undefined,
        maxEnginePower: undefined,
        condition: '',
        isActive: true,
        notificationFrequency: 'immediate',
        maxNotificationsPerDay: 5,
        ...initialData,
      })
      setErrors({})
    }
  }, [isOpen, initialData])

  const updateField = (field: keyof AlertFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const toggleArrayField = (field: keyof AlertFormData, value: string) => {
    const currentArray = (formData[field] as string[]) || []
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    updateField(field, newArray)
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Alert name is required'
    }

    if (formData.minPrice && formData.maxPrice && formData.minPrice > formData.maxPrice) {
      newErrors.maxPrice = 'Max price must be greater than min price'
    }

    if (formData.minYear && formData.maxYear && formData.minYear > formData.maxYear) {
      newErrors.maxYear = 'Max year must be greater than min year'
    }

    if (formData.minEnginePower && formData.maxEnginePower && formData.minEnginePower > formData.maxEnginePower) {
      newErrors.maxEnginePower = 'Max power must be greater than min power'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = () => {
    if (validateForm()) {
      onSave(formData)
    }
  }

  const handleTest = () => {
    // Implementation for testing alert
    console.log('Testing alert with data:', formData)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Create New Alert' : 'Edit Alert'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Alert Name *
                  </label>
                  <Input
                    placeholder="e.g., BMW 3 Series Under €25k"
                    value={formData.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    className={errors.name ? 'border-red-500' : ''}
                  />
                  {errors.name && (
                    <p className="text-red-500 text-xs mt-1">{errors.name}</p>
                  )}
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Description
                  </label>
                  <Input
                    placeholder="Optional description"
                    value={formData.description}
                    onChange={(e) => updateField('description', e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Active</label>
                  <p className="text-xs text-muted-foreground">
                    Enable notifications for this alert
                  </p>
                </div>
                <Switch
                  checked={formData.isActive}
                  onCheckedChange={(checked) => updateField('isActive', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Vehicle Criteria */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Vehicle Criteria</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="specs">Specs</TabsTrigger>
                  <TabsTrigger value="location">Location</TabsTrigger>
                  <TabsTrigger value="notifications">Notifications</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4 mt-4">
                  {/* Make & Model */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Make</label>
                      <Input
                        placeholder="Any make"
                        value={formData.make}
                        onChange={(e) => updateField('make', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Model</label>
                      <Input
                        placeholder="Any model"
                        value={formData.model}
                        onChange={(e) => updateField('model', e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Price Range */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Price Range (EUR)</label>
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        type="number"
                        placeholder="Min price"
                        value={formData.minPrice || ''}
                        onChange={(e) => updateField('minPrice', parseInt(e.target.value) || undefined)}
                      />
                      <Input
                        type="number"
                        placeholder="Max price"
                        value={formData.maxPrice || ''}
                        onChange={(e) => updateField('maxPrice', parseInt(e.target.value) || undefined)}
                        className={errors.maxPrice ? 'border-red-500' : ''}
                      />
                    </div>
                    {errors.maxPrice && (
                      <p className="text-red-500 text-xs mt-1">{errors.maxPrice}</p>
                    )}
                  </div>

                  {/* Year Range */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Year Range</label>
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        type="number"
                        placeholder="From year"
                        value={formData.minYear || ''}
                        onChange={(e) => updateField('minYear', parseInt(e.target.value) || undefined)}
                      />
                      <Input
                        type="number"
                        placeholder="To year"
                        value={formData.maxYear || ''}
                        onChange={(e) => updateField('maxYear', parseInt(e.target.value) || undefined)}
                        className={errors.maxYear ? 'border-red-500' : ''}
                      />
                    </div>
                    {errors.maxYear && (
                      <p className="text-red-500 text-xs mt-1">{errors.maxYear}</p>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="specs" className="space-y-4 mt-4">
                  {/* Mileage */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Maximum Mileage (km)</label>
                    <Input
                      type="number"
                      placeholder="Max mileage"
                      value={formData.maxMileage || ''}
                      onChange={(e) => updateField('maxMileage', parseInt(e.target.value) || undefined)}
                    />
                  </div>

                  {/* Fuel Type */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Fuel Type</label>
                    <div className="flex flex-wrap gap-2">
                      {fuelTypes.map((fuel) => (
                        <Badge
                          key={fuel}
                          variant={(formData.fuelType || []).includes(fuel) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => toggleArrayField('fuelType', fuel)}
                        >
                          {fuel}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Transmission */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Transmission</label>
                    <div className="flex flex-wrap gap-2">
                      {transmissions.map((trans) => (
                        <Badge
                          key={trans}
                          variant={(formData.transmission || []).includes(trans) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => toggleArrayField('transmission', trans)}
                        >
                          {trans}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Body Type */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Body Type</label>
                    <div className="flex flex-wrap gap-2">
                      {bodyTypes.map((body) => (
                        <Badge
                          key={body}
                          variant={(formData.bodyType || []).includes(body) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => toggleArrayField('bodyType', body)}
                        >
                          {body}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="location" className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">City</label>
                      <Input
                        placeholder="e.g., Munich"
                        value={formData.city}
                        onChange={(e) => updateField('city', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Region</label>
                      <Input
                        placeholder="e.g., Bavaria"
                        value={formData.region}
                        onChange={(e) => updateField('region', e.target.value)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Search Radius (km)</label>
                    <select
                      value={formData.locationRadius || ''}
                      onChange={(e) => updateField('locationRadius', parseInt(e.target.value) || undefined)}
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

                <TabsContent value="notifications" className="space-y-4 mt-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Notification Frequency</label>
                    <select
                      value={formData.notificationFrequency}
                      onChange={(e) => updateField('notificationFrequency', e.target.value)}
                      className="w-full border rounded px-3 py-2"
                    >
                      <option value="immediate">Immediate</option>
                      <option value="daily">Daily Summary</option>
                      <option value="weekly">Weekly Summary</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Notifications Per Day</label>
                    <Input
                      type="number"
                      min="1"
                      max="50"
                      value={formData.maxNotificationsPerDay}
                      onChange={(e) => updateField('maxNotificationsPerDay', parseInt(e.target.value) || 5)}
                    />
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="outline" onClick={handleTest}>
              <TestTube className="mr-2 h-4 w-4" />
              Test Alert
            </Button>
            <Button onClick={handleSave} className="auto-scouter-gradient">
              <Save className="mr-2 h-4 w-4" />
              {mode === 'create' ? 'Create Alert' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
