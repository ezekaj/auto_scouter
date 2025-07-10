import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.vehiclescout.app',
  appName: 'Vehicle Scout',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // Allow cleartext traffic for development
    cleartext: true,
    // Configure allowed navigation for Render deployment
    allowNavigation: [
      'https://vehiclescout.app',
      'https://auto-scouter-backend.onrender.com',
      'https://*.onrender.com',
      'http://localhost:8000',
      'http://127.0.0.1:8000',
      'http://localhost:5173',
      'http://127.0.0.1:5173'
    ]
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#000000',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      androidSpinnerStyle: 'large',
      iosSpinnerStyle: 'small',
      spinnerColor: '#ffffff',
      splashFullScreen: true,
      splashImmersive: true
    },
    StatusBar: {
      style: 'dark',
      backgroundColor: '#000000'
    },
    Keyboard: {
      resize: 'body',
      style: 'dark',
      resizeOnFullScreen: true
    },
    App: {
      launchUrl: 'https://vehiclescout.app'
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert']
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon_config_sample',
      iconColor: '#488AFF',
      sound: 'beep.wav'
    },
    Camera: {
      permissions: ['camera', 'photos']
    },
    Geolocation: {
      permissions: ['location']
    }
  }
};

export default config;
