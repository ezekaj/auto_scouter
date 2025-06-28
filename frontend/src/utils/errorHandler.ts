// Production error handling utilities

interface ErrorInfo {
  message: string
  stack?: string
  componentStack?: string
  errorBoundary?: string
  timestamp: string
  userAgent: string
  url: string
  userId?: string
}

class ErrorHandler {
  private static instance: ErrorHandler
  private isProduction = import.meta.env.PROD
  private sentryDsn = import.meta.env.VITE_SENTRY_DSN

  private constructor() {
    this.setupGlobalErrorHandlers()
  }

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  private setupGlobalErrorHandlers() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError(new Error(event.reason), {
        type: 'unhandledrejection',
        reason: event.reason
      })
    })

    // Handle global JavaScript errors
    window.addEventListener('error', (event) => {
      this.logError(new Error(event.message), {
        type: 'javascript',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      })
    })
  }

  logError(error: Error, context?: Record<string, any>) {
    const errorInfo: ErrorInfo = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...context
    }

    if (this.isProduction) {
      // In production, send to error reporting service
      this.sendToErrorService(errorInfo)
    } else {
      // In development, log to console
      console.error('Error logged:', errorInfo)
    }
  }

  private async sendToErrorService(errorInfo: ErrorInfo) {
    try {
      // Send to Sentry or other error reporting service
      if (this.sentryDsn) {
        // Sentry integration would go here
        // For now, we'll use a generic endpoint
        await fetch('/api/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorInfo),
        })
      }
    } catch (err) {
      // Silently fail in production to avoid error loops
    }
  }

  logUserAction(action: string, details?: Record<string, any>) {
    if (this.isProduction && import.meta.env.VITE_ENABLE_ANALYTICS === 'true') {
      // Log user actions for analytics
      this.sendAnalyticsEvent('user_action', {
        action,
        ...details,
        timestamp: new Date().toISOString(),
      })
    }
  }

  private async sendAnalyticsEvent(_eventType: string, _data: Record<string, any>) {
    try {
      // Send to analytics service (Google Analytics, etc.)
      if (import.meta.env.VITE_GOOGLE_ANALYTICS_ID) {
        // Google Analytics integration would go here
        // console.log('Analytics event:', eventType, data)
      }
    } catch (err) {
      // Silently fail
    }
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance()

// Utility function for React Error Boundaries
export const logReactError = (error: Error, errorInfo: { componentStack: string }) => {
  errorHandler.logError(error, {
    type: 'react',
    componentStack: errorInfo.componentStack,
  })
}
