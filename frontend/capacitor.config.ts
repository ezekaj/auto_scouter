import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.autoscouter.supabase',
  appName: 'Auto Scouter',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // Allow cleartext traffic for development
    cleartext: false,
    // Configure allowed navigation for Supabase deployment
    allowNavigation: [
      'https://rwonkzncpzirokqnuoyx.supabase.co',
      'https://*.supabase.co',
      'https://carmarket.ayvens.com',
      'http://localhost:5173',
      'http://127.0.0.1:5173',
      'http://127.0.0.1:54321'
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
      // Remove launchUrl to use local app bundle instead of external URL
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
