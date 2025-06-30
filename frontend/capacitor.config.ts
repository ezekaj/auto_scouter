import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.vehiclescout.app',
  appName: 'Vehicle Scout',
  webDir: 'dist',
  server: {
    androidScheme: 'https'
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
    }
  }
};

export default config;
