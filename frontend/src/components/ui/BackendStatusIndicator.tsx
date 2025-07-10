/**
 * Backend Status Indicator Component
 * Shows the current backend connectivity status
 */

import React from 'react'
import { AlertCircle, CheckCircle, WifiOff } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useBackendStatus } from '@/utils/backendStatus'

export const BackendStatusIndicator: React.FC = () => {
  const status = useBackendStatus()

  if (status.isOnline) {
    return (
      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
        <CheckCircle className="w-3 h-3 mr-1" />
        Backend Online
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
      <AlertCircle className="w-3 h-3 mr-1" />
      Demo Mode
    </Badge>
  )
}

export const BackendStatusBanner: React.FC = () => {
  const status = useBackendStatus()

  if (status.isOnline) {
    return null // Don't show banner when backend is online
  }

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <WifiOff className="h-5 w-5 text-yellow-400" />
        </div>
        <div className="ml-3">
          <p className="text-sm text-yellow-700">
            <strong>Demo Mode:</strong> Backend is not connected. Using sample data for demonstration.
            {status.error && (
              <span className="block text-xs mt-1 text-yellow-600">
                Error: {status.error}
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}

export default BackendStatusIndicator
