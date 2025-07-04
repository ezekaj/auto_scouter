import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'

// Import services
import { vehicleService } from '@/services/vehicleService'
import { alertService } from '@/services/alertService'
import { savedSearchService } from '@/services/savedSearchService'
import { notificationService } from '@/services/notificationService'

// Import hooks
import { useVehicles } from '@/hooks/useVehicles'
import { useAlerts } from '@/hooks/useAlertsQuery'
import { useSavedSearches } from '@/hooks/useSavedSearches'
import { useNotifications } from '@/hooks/useNotifications'

// Import components
import { VehicleDetail } from '@/components/vehicles/VehicleDetail'
import { SavedSearches } from '@/components/vehicles/SavedSearches'
import { NotificationCenter } from '@/components/notifications/NotificationCenter'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Service Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Vehicle Service Integration', () => {
    it('should fetch vehicles with correct API endpoints', async () => {
      const mockVehicles = [
        {
          id: 1,
          make: 'BMW',
          model: 'X5',
          year: 2023,
          price: 45000,
          city: 'Milano',
          listing_url: 'https://example.com/listing/1'
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({
        data: { vehicles: mockVehicles, total: 1 }
      })

      const result = await vehicleService.getVehicles()
      
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/vehicles/', {
        params: { page: 1, limit: 20 }
      })
      expect(result.vehicles).toEqual(mockVehicles)
    })

    it('should perform advanced search with correct parameters', async () => {
      const searchFilters = {
        make: 'BMW',
        model: 'X5',
        year_min: 2020,
        year_max: 2023,
        price_min: 30000,
        price_max: 60000
      }

      mockedAxios.post.mockResolvedValueOnce({
        data: { vehicles: [], total: 0 }
      })

      await vehicleService.advancedSearch(searchFilters)
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/vehicles/search/', searchFilters)
    })
  })

  describe('Alert Service Integration', () => {
    it('should create alert with correct data structure', async () => {
      const alertData = {
        name: 'BMW X5 Alert',
        criteria: {
          make: 'BMW',
          model: 'X5',
          price_max: 50000
        },
        is_active: true
      }

      const mockAlert = { id: 1, ...alertData }
      mockedAxios.post.mockResolvedValueOnce({ data: mockAlert })

      const result = await alertService.createAlert(alertData)
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/alerts/', alertData)
      expect(result).toEqual(mockAlert)
    })

    it('should toggle alert status correctly', async () => {
      const mockAlert = { id: 1, is_active: false }
      mockedAxios.patch.mockResolvedValueOnce({ data: mockAlert })

      const result = await alertService.toggleAlert(1)
      
      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/alerts/1/toggle/')
      expect(result.is_active).toBe(false)
    })
  })

  describe('Saved Search Service Integration', () => {
    it('should create saved search with proper field mapping', async () => {
      const searchData = {
        name: 'My BMW Search',
        search_term: 'BMW X5',
        filters: {
          make: 'BMW',
          model: 'X5'
        },
        is_favorite: false
      }

      const mockSavedSearch = { id: 'search-1', ...searchData }
      mockedAxios.post.mockResolvedValueOnce({ data: mockSavedSearch })

      const result = await savedSearchService.createSavedSearch(searchData)
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/saved-searches/', searchData)
      expect(result).toEqual(mockSavedSearch)
    })

    it('should format search filters correctly', () => {
      const filters = {
        make: 'BMW',
        model: 'X5',
        year_min: 2020,
        year_max: 2023,
        price_max: 50000
      }

      const formatted = savedSearchService.formatSearchFilters(filters)
      
      expect(formatted).toContain('BMW X5')
      expect(formatted).toContain('2020-2023')
      expect(formatted).toContain('€50,000')
    })
  })

  describe('Notification Service Integration', () => {
    it('should fetch notifications with correct parameters', async () => {
      const mockNotifications = [
        {
          id: 1,
          title: 'New Vehicle Match',
          message: 'Found a BMW X5 matching your criteria',
          notification_type: 'alert',
          is_read: false,
          created_at: '2023-12-01T10:00:00Z'
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({
        data: { notifications: mockNotifications, total: 1 }
      })

      const result = await notificationService.getNotifications()
      
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/notifications/', {
        params: { page: 1, limit: 20 }
      })
      expect(result.notifications).toEqual(mockNotifications)
    })

    it('should mark notification as read with correct endpoint', async () => {
      const mockNotification = { id: 1, is_read: true }
      mockedAxios.patch.mockResolvedValueOnce({ data: mockNotification })

      const result = await notificationService.markAsRead('1')
      
      expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/notifications/1/read/')
      expect(result.is_read).toBe(true)
    })
  })

  describe('Component Integration', () => {
    it('should render SavedSearches component with real data', async () => {
      const mockSavedSearches = [
        {
          id: 'search-1',
          name: 'BMW Search',
          search_term: 'BMW X5',
          results_count: 5,
          is_favorite: true,
          last_used: '2023-12-01T10:00:00Z',
          created_at: '2023-11-01T10:00:00Z'
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({
        data: mockSavedSearches
      })

      render(
        <TestWrapper>
          <SavedSearches isOpen={true} onClose={() => {}} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('BMW Search')).toBeInTheDocument()
      })
    })

    it('should handle notification actions correctly', async () => {
      const mockNotifications = [
        {
          id: 1,
          title: 'Test Notification',
          message: 'Test message',
          notification_type: 'alert',
          priority: 2,
          is_read: false,
          created_at: '2023-12-01T10:00:00Z'
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({
        data: { notifications: mockNotifications, total: 1 }
      })

      mockedAxios.patch.mockResolvedValueOnce({
        data: { ...mockNotifications[0], is_read: true }
      })

      render(
        <TestWrapper>
          <NotificationCenter isOpen={true} onClose={() => {}} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Test Notification')).toBeInTheDocument()
      })

      // Click mark as read button
      const markReadButton = screen.getByRole('button', { name: /mark as read/i })
      fireEvent.click(markReadButton)

      await waitFor(() => {
        expect(mockedAxios.patch).toHaveBeenCalledWith('/api/v1/notifications/1/read/')
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      await expect(vehicleService.getVehicles()).rejects.toThrow('Network error')
    })

    it('should handle validation errors in saved searches', () => {
      const invalidSearchData = {
        name: '', // Empty name should be invalid
        search_term: '',
        filters: {}
      }

      const validation = savedSearchService.validateSearchData(invalidSearchData)
      
      expect(validation.isValid).toBe(false)
      expect(validation.errors).toContain('Name is required')
    })
  })

  describe('Data Transformation', () => {
    it('should transform backend data correctly for frontend consumption', async () => {
      const backendVehicle = {
        id: 1,
        make: 'BMW',
        model: 'X5',
        year: 2023,
        price: 45000,
        listing_url: 'https://example.com/listing/1',
        created_at: '2023-12-01T10:00:00Z'
      }

      mockedAxios.get.mockResolvedValueOnce({
        data: { vehicles: [backendVehicle], total: 1 }
      })

      const result = await vehicleService.getVehicles()
      const vehicle = result.vehicles[0]
      
      // Verify data structure matches frontend expectations
      expect(vehicle).toHaveProperty('id')
      expect(vehicle).toHaveProperty('make')
      expect(vehicle).toHaveProperty('model')
      expect(vehicle).toHaveProperty('year')
      expect(vehicle).toHaveProperty('price')
      expect(vehicle).toHaveProperty('listing_url')
    })
  })
})
