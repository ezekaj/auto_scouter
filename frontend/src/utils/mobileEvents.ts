/**
 * Mobile Event Utilities
 * Handles touch events and mobile-specific interactions
 */

import { Capacitor } from '@capacitor/core'

export class MobileEventHandler {
  private static instance: MobileEventHandler
  private isMobile: boolean
  private touchStartTime: number = 0
  private touchStartPos: { x: number; y: number } = { x: 0, y: 0 }

  constructor() {
    this.isMobile = Capacitor.isNativePlatform()
    this.initializeEventHandlers()
  }

  static getInstance(): MobileEventHandler {
    if (!MobileEventHandler.instance) {
      MobileEventHandler.instance = new MobileEventHandler()
    }
    return MobileEventHandler.instance
  }

  private initializeEventHandlers() {
    if (this.isMobile) {
      // Add global touch event handlers
      document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false })
      document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false })
      document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false })
      
      // Prevent default context menu
      document.addEventListener('contextmenu', (e) => e.preventDefault())
      
      // Handle back button
      document.addEventListener('backbutton', this.handleBackButton.bind(this), false)
    }
  }

  private handleTouchStart(event: TouchEvent) {
    this.touchStartTime = Date.now()
    const touch = event.touches[0]
    this.touchStartPos = { x: touch.clientX, y: touch.clientY }
  }

  private handleTouchEnd(event: TouchEvent) {
    const touchEndTime = Date.now()
    const touchDuration = touchEndTime - this.touchStartTime
    
    // If touch was very short, treat as tap
    if (touchDuration < 200) {
      this.simulateClick(event)
    }
  }

  private handleTouchMove(event: TouchEvent) {
    const touch = event.touches[0]
    const deltaX = Math.abs(touch.clientX - this.touchStartPos.x)
    const deltaY = Math.abs(touch.clientY - this.touchStartPos.y)
    
    // If significant movement, it's a scroll/swipe, not a tap
    if (deltaX > 10 || deltaY > 10) {
      // Allow default scroll behavior
      return
    }
  }

  private simulateClick(event: TouchEvent) {
    const touch = event.changedTouches[0]
    const target = document.elementFromPoint(touch.clientX, touch.clientY)
    
    if (target && this.isClickableElement(target)) {
      // Create and dispatch click event
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        clientX: touch.clientX,
        clientY: touch.clientY
      })
      
      target.dispatchEvent(clickEvent)
    }
  }

  private isClickableElement(element: Element): boolean {
    const clickableSelectors = [
      'button',
      'a',
      '[role="button"]',
      '[onclick]',
      'input[type="button"]',
      'input[type="submit"]',
      '.clickable',
      '[data-clickable]'
    ]
    
    return clickableSelectors.some(selector => 
      element.matches(selector) || element.closest(selector)
    )
  }

  private handleBackButton(event: Event) {
    event.preventDefault()
    // Handle back navigation
    if (window.history.length > 1) {
      window.history.back()
    }
  }

  // Utility method to make any element mobile-friendly
  public makeMobileFriendly(element: HTMLElement) {
    if (!this.isMobile) return

    element.style.touchAction = 'manipulation'
    // Use setProperty for webkit-specific styles
    element.style.setProperty('-webkit-tap-highlight-color', 'rgba(0, 0, 0, 0.1)')

    // Add mobile-friendly event listeners
    element.addEventListener('touchstart', () => {
      element.classList.add('touch-active')
    }, { passive: true })

    element.addEventListener('touchend', () => {
      element.classList.remove('touch-active')
    }, { passive: true })

    element.addEventListener('touchcancel', () => {
      element.classList.remove('touch-active')
    }, { passive: true })
  }

  // Check if running on mobile
  public isMobilePlatform(): boolean {
    return this.isMobile
  }

  // Get safe area insets for mobile
  public getSafeAreaInsets() {
    if (!this.isMobile) return { top: 0, bottom: 0, left: 0, right: 0 }
    
    const style = getComputedStyle(document.documentElement)
    return {
      top: parseInt(style.getPropertyValue('--safe-area-inset-top') || '0'),
      bottom: parseInt(style.getPropertyValue('--safe-area-inset-bottom') || '0'),
      left: parseInt(style.getPropertyValue('--safe-area-inset-left') || '0'),
      right: parseInt(style.getPropertyValue('--safe-area-inset-right') || '0')
    }
  }
}

// React hook for mobile events
export const useMobileEvents = () => {
  const mobileHandler = MobileEventHandler.getInstance()
  
  return {
    isMobile: mobileHandler.isMobilePlatform(),
    makeMobileFriendly: mobileHandler.makeMobileFriendly.bind(mobileHandler),
    getSafeAreaInsets: mobileHandler.getSafeAreaInsets.bind(mobileHandler)
  }
}

// Initialize mobile event handler
export const initializeMobileEvents = () => {
  MobileEventHandler.getInstance()
}

// CSS class for touch feedback
export const MOBILE_TOUCH_CLASSES = `
  .touch-active {
    opacity: 0.7;
    transform: scale(0.98);
    transition: all 0.1s ease;
  }
  
  .mobile-button {
    min-height: 44px;
    min-width: 44px;
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
  }
`
