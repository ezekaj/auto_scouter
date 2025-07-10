import React, { Suspense, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { config } from '@/config/production'
import { errorHandler } from '@/utils/errorHandler'
import { MobileUtils } from '@/utils/mobile'
import { nativeService } from '@/services/nativeService'
import { initializeMobileEvents } from '@/utils/mobileEvents'
import './i18n' // Initialize i18n

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { Layout } from '@/components/layout/Layout'


// Lazy load components for better performance
const Dashboard = React.lazy(() => import('@/components/dashboard/Dashboard').then(m => ({ default: m.Dashboard })))
const EnhancedDashboard = React.lazy(() => import('@/components/dashboard/EnhancedDashboard'))

const VehicleSearch = React.lazy(() => import('@/components/vehicles/VehicleSearch').then(m => ({ default: m.VehicleSearch })))
const VehicleDetail = React.lazy(() => import('@/components/vehicles/VehicleDetail').then(m => ({ default: m.VehicleDetail })))
const AlertManager = React.lazy(() => import('@/components/alerts/AlertManager').then(m => ({ default: m.AlertManager })))
const NotificationCenter = React.lazy(() => import('@/components/notifications/NotificationCenter').then(m => ({ default: m.NotificationCenter })))



// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('Initializing app...')

        // Initialize native features
        await nativeService.initialize()
        console.log('Native service initialized')

        // Initialize mobile features
        await MobileUtils.initializeApp()
        console.log('Mobile utils initialized')

        // Initialize mobile event handling
        initializeMobileEvents()
        console.log('Mobile events initialized')

        // Initialize production configuration
        if (config.isProduction) {
          console.log('Production mode - logging app start')
          // Log application start
          errorHandler.logUserAction('app_start', {
            version: config.appVersion,
            environment: config.environment,
            platform: nativeService.isNative() ? 'mobile' : 'web',
            appInfo: nativeService.getAppInfo(),
          })
        }

        console.log('App initialization complete')
      } catch (error) {
        console.error('App initialization failed:', error)
      }
    }

    initializeApp()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary fallback={
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Vehicle Scout</h1>
            <p className="text-gray-600">Application failed to load. Please check your connection and try again.</p>
          </div>
        </div>
      }>
        <Router>
        <Suspense fallback={
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p>Loading Vehicle Scout...</p>
            </div>
          </div>
        }>
          <Routes>
            {/* Default route - direct access to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Application routes - no authentication required */}
            <Route path="/dashboard" element={
              <Layout>
                <Dashboard />
              </Layout>
            } />
            <Route path="/enhanced" element={
              <Layout>
                <EnhancedDashboard />
              </Layout>
            } />

            <Route path="/search" element={
              <Layout>
                <VehicleSearch />
              </Layout>
            } />
            <Route path="/vehicle/:id" element={
              <Layout>
                <VehicleDetail vehicleId="" onBack={() => window.history.back()} />
              </Layout>
            } />
            <Route path="/alerts" element={
              <Layout>
                <AlertManager />
              </Layout>
            } />
            <Route path="/notifications" element={
              <Layout>
                <NotificationCenter />
              </Layout>
            } />

            {/* Additional routes for mobile navigation */}
            <Route path="/saved" element={
              <Layout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold mb-4">Saved Vehicles</h1>
                  <p className="text-muted-foreground">Your saved vehicles will appear here.</p>
                </div>
              </Layout>
            } />

            <Route path="/analytics" element={
              <Layout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold mb-4">Analytics</h1>
                  <p className="text-muted-foreground">Vehicle search analytics and insights.</p>
                </div>
              </Layout>
            } />

            <Route path="/settings" element={
              <Layout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold mb-4">Settings</h1>
                  <p className="text-muted-foreground">App settings and preferences.</p>
                </div>
              </Layout>
            } />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
