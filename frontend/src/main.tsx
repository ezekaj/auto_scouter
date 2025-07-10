import React from 'react'
import ReactDOM from 'react-dom/client'
import { Capacitor } from '@capacitor/core'
import { StatusBar, Style } from '@capacitor/status-bar'
import { SplashScreen } from '@capacitor/splash-screen'
import App from './App.tsx'
import './index.css'

// Initialize Capacitor for mobile
const initializeCapacitor = async () => {
  if (Capacitor.isNativePlatform()) {
    // Configure status bar for mobile
    try {
      await StatusBar.setStyle({ style: Style.Dark })
      await StatusBar.setBackgroundColor({ color: '#000000' })
    } catch (error) {
      console.log('StatusBar not available:', error)
    }

    // Hide splash screen after app loads
    try {
      await SplashScreen.hide()
    } catch (error) {
      console.log('SplashScreen not available:', error)
    }

    // Add mobile-specific event listeners
    document.addEventListener('deviceready', () => {
      console.log('Capacitor device ready')
    })

    // Prevent context menu on long press (mobile)
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault()
    })

    // Improve touch responsiveness
    document.addEventListener('touchstart', () => {}, { passive: true })
  } else {
    // Register service worker for PWA functionality (web only)
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then((_registration) => {
            console.log('Service worker registered successfully')
          })
          .catch((_registrationError) => {
            console.log('Service worker registration failed')
          });
      });
    }
  }
}

// Initialize Capacitor and render app
initializeCapacitor().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
}).catch((error) => {
  console.error('Failed to initialize Capacitor:', error)
  // Render app anyway
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
})
