// Production configuration for Auto Scouter Frontend

export const config = {
  // API Configuration - Updated for Supabase
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-api',
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL || 'https://rwonkzncpzirokqnuoyx.supabase.co',
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),

  // Application Configuration
  appName: import.meta.env.VITE_APP_NAME || 'Auto Scouter',
  appVersion: import.meta.env.VITE_APP_VERSION || '2.0.0',
  environment: import.meta.env.VITE_APP_ENVIRONMENT || 'production',

  // Feature Flags
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableErrorReporting: import.meta.env.VITE_ENABLE_ERROR_REPORTING === 'true',
  enablePerformanceMonitoring: import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true',

  // Security Configuration
  enableHttpsOnly: import.meta.env.VITE_ENABLE_HTTPS_ONLY === 'true',
  enableStrictCSP: import.meta.env.VITE_ENABLE_STRICT_CSP === 'true',

  // External Services
  googleAnalyticsId: import.meta.env.VITE_GOOGLE_ANALYTICS_ID,
  sentryDsn: import.meta.env.VITE_SENTRY_DSN,

  // Cache Configuration
  cacheVersion: import.meta.env.VITE_CACHE_VERSION || '1.0.0',

  // Build Information
  buildTimestamp: import.meta.env.VITE_BUILD_TIMESTAMP,
  gitCommit: import.meta.env.VITE_GIT_COMMIT,

  // Production-specific settings
  isProduction: import.meta.env.PROD,
  isDevelopment: import.meta.env.DEV,
}

// Validate required configuration
export const validateConfig = () => {
  const requiredVars = [
    'VITE_SUPABASE_URL',
    'VITE_SUPABASE_ANON_KEY',
  ]

  const missing = requiredVars.filter(varName => !import.meta.env[varName])

  if (missing.length > 0) {
    console.warn(`Missing environment variables: ${missing.join(', ')}`)
    // Don't throw error, just warn - app should still work
  }
}

// Initialize configuration validation in production
if (config.isProduction) {
  validateConfig()
}
