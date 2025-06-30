import { Capacitor } from '@capacitor/core';
import { App, AppInfo } from '@capacitor/app';
import { StatusBar, Style } from '@capacitor/status-bar';
import { SplashScreen } from '@capacitor/splash-screen';
import { Keyboard } from '@capacitor/keyboard';
import { Haptics, ImpactStyle, NotificationType } from '@capacitor/haptics';

export class NativeService {
  private static instance: NativeService;
  private appInfo: AppInfo | null = null;

  private constructor() {}

  static getInstance(): NativeService {
    if (!NativeService.instance) {
      NativeService.instance = new NativeService();
    }
    return NativeService.instance;
  }

  async initialize(): Promise<void> {
    if (!Capacitor.isNativePlatform()) {
      console.log('Running in web mode, native features disabled');
      return;
    }

    try {
      // Get app info
      this.appInfo = await App.getInfo();
      console.log('App initialized:', this.appInfo);

      // Configure status bar
      await this.configureStatusBar();

      // Setup keyboard listeners
      await this.setupKeyboardListeners();

      // Setup app state listeners
      await this.setupAppStateListeners();

      // Hide splash screen
      await SplashScreen.hide();

      console.log('Native features initialized successfully');
    } catch (error) {
      console.error('Failed to initialize native features:', error);
    }
  }

  private async configureStatusBar(): Promise<void> {
    try {
      await StatusBar.setStyle({ style: Style.Dark });
      await StatusBar.setBackgroundColor({ color: '#000000' });
    } catch (error) {
      console.warn('Status bar configuration failed:', error);
    }
  }

  private async setupKeyboardListeners(): Promise<void> {
    try {
      Keyboard.addListener('keyboardWillShow', (info) => {
        document.body.classList.add('keyboard-open');
        document.body.style.setProperty('--keyboard-height', `${info.keyboardHeight}px`);
      });

      Keyboard.addListener('keyboardWillHide', () => {
        document.body.classList.remove('keyboard-open');
        document.body.style.removeProperty('--keyboard-height');
      });
    } catch (error) {
      console.warn('Keyboard listener setup failed:', error);
    }
  }

  private async setupAppStateListeners(): Promise<void> {
    try {
      App.addListener('appStateChange', ({ isActive }) => {
        console.log('App state changed. Is active:', isActive);
        if (isActive) {
          // App became active
          this.onAppResume();
        } else {
          // App went to background
          this.onAppPause();
        }
      });

      App.addListener('backButton', ({ canGoBack }) => {
        if (canGoBack) {
          window.history.back();
        } else {
          App.exitApp();
        }
      });
    } catch (error) {
      console.warn('App state listener setup failed:', error);
    }
  }

  private onAppResume(): void {
    // Refresh data when app becomes active
    window.dispatchEvent(new CustomEvent('app-resume'));
  }

  private onAppPause(): void {
    // Save state when app goes to background
    window.dispatchEvent(new CustomEvent('app-pause'));
  }

  async provideFeedback(type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' = 'light'): Promise<void> {
    if (!Capacitor.isNativePlatform()) return;

    try {
      switch (type) {
        case 'light':
          await Haptics.impact({ style: ImpactStyle.Light });
          break;
        case 'medium':
          await Haptics.impact({ style: ImpactStyle.Medium });
          break;
        case 'heavy':
          await Haptics.impact({ style: ImpactStyle.Heavy });
          break;
        case 'success':
          await Haptics.notification({ type: NotificationType.Success });
          break;
        case 'warning':
          await Haptics.notification({ type: NotificationType.Warning });
          break;
        case 'error':
          await Haptics.notification({ type: NotificationType.Error });
          break;
      }
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async setStatusBarColor(color: string, isDark: boolean = true): Promise<void> {
    if (!Capacitor.isNativePlatform()) return;

    try {
      await StatusBar.setBackgroundColor({ color });
      await StatusBar.setStyle({ style: isDark ? Style.Dark : Style.Light });
    } catch (error) {
      console.warn('Status bar color change failed:', error);
    }
  }

  getAppInfo(): AppInfo | null {
    return this.appInfo;
  }

  isNative(): boolean {
    return Capacitor.isNativePlatform();
  }

  getPlatform(): string {
    return Capacitor.getPlatform();
  }

  async exitApp(): Promise<void> {
    if (!Capacitor.isNativePlatform()) return;
    
    try {
      await App.exitApp();
    } catch (error) {
      console.warn('Exit app failed:', error);
    }
  }
}

// Export singleton instance
export const nativeService = NativeService.getInstance();
