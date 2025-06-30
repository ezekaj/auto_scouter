import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { SplashScreen } from '@capacitor/splash-screen';
import { Keyboard } from '@capacitor/keyboard';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

export class MobileUtils {
  static isNative(): boolean {
    return Capacitor.isNativePlatform();
  }

  static isAndroid(): boolean {
    return Capacitor.getPlatform() === 'android';
  }

  static isIOS(): boolean {
    return Capacitor.getPlatform() === 'ios';
  }

  static async initializeApp(): Promise<void> {
    if (!this.isNative()) return;

    try {
      // Configure status bar
      await StatusBar.setStyle({ style: Style.Dark });
      await StatusBar.setBackgroundColor({ color: '#000000' });

      // Hide splash screen after app is ready
      await SplashScreen.hide();

      // Configure keyboard behavior
      if (this.isAndroid()) {
        Keyboard.addListener('keyboardWillShow', () => {
          document.body.classList.add('keyboard-open');
        });

        Keyboard.addListener('keyboardWillHide', () => {
          document.body.classList.remove('keyboard-open');
        });
      }
    } catch (error) {
      console.warn('Mobile initialization failed:', error);
    }
  }

  static async provideFeedback(type: 'light' | 'medium' | 'heavy' = 'light'): Promise<void> {
    if (!this.isNative()) return;

    try {
      const impactStyle = type === 'light' ? ImpactStyle.Light : 
                         type === 'medium' ? ImpactStyle.Medium : 
                         ImpactStyle.Heavy;
      
      await Haptics.impact({ style: impactStyle });
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  static async setStatusBarColor(color: string, isDark: boolean = true): Promise<void> {
    if (!this.isNative()) return;

    try {
      await StatusBar.setBackgroundColor({ color });
      await StatusBar.setStyle({ style: isDark ? Style.Dark : Style.Light });
    } catch (error) {
      console.warn('Status bar configuration failed:', error);
    }
  }

  static getViewportHeight(): string {
    if (this.isNative()) {
      return '100vh';
    }
    return '100dvh'; // Dynamic viewport height for web
  }

  static addTouchClass(element: HTMLElement): void {
    element.classList.add('touch-target');
  }

  static isTouchDevice(): boolean {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }
}
