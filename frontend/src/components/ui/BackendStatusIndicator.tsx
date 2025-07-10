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
    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
      <AlertCircle className="w-3 h-3 mr-1" />
      Backend Offline
    </Badge>
  )
}

export const BackendStatusBanner: React.FC = () => {
  const status = useBackendStatus()

  if (status.isOnline) {
    return null // Don't show banner when backend is online
  }

  return (
    <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <WifiOff className="h-5 w-5 text-red-400" />
        </div>
        <div className="ml-3">
          <p className="text-sm text-red-700">
            <strong>Connection Error:</strong> Unable to connect to backend service. Please check your internet connection and try again.
            {status.error && (
              <span className="block text-xs mt-1 text-red-600">
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
