export interface NotificationPermission {
  granted: boolean
  denied: boolean
  prompt: boolean
}

export interface PushNotificationData {
  title: string
  body: string
  icon?: string
  badge?: string
  tag?: string
  data?: any
  actions?: NotificationAction[]
  requireInteraction?: boolean
  silent?: boolean
  vibrate?: number[]
}

export interface NotificationSubscription {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
  userId?: string
  preferences: NotificationPreferences
}

export interface NotificationPreferences {
  earnings: boolean
  opportunities: boolean
  alerts: boolean
  updates: boolean
  marketing: boolean
}

export interface NotificationService {
  checkSupport: () => boolean
  getPermissionStatus: () => NotificationPermission
  requestPermission: () => Promise<boolean>
  subscribe: (preferences: NotificationPreferences) => Promise<PushSubscription | null>
  unsubscribe: () => Promise<boolean>
  updatePreferences: (preferences: NotificationPreferences) => Promise<boolean>
  sendLocalNotification: (data: PushNotificationData) => Promise<void>
  scheduleNotification: (data: PushNotificationData, delay: number) => Promise<void>
  clearAllNotifications: () => void
}

class PushNotificationManager implements NotificationService {
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null
  private vapidPublicKey = process.env.REACT_APP_VAPID_PUBLIC_KEY || 
    'BMfQzhxqnwwlEr0X5QR1k2UBqjrz5E6GzB_M-fEUq3fJqJe2zF8YvJ2tB9RqQ1xJ8e5EQc1Gf5r5Z8x7Y3Q4J9w'

  constructor() {
    this.initServiceWorker()
  }

  private async initServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.ready
      } catch (error) {
        console.error('Service worker initialization failed:', error)
      }
    }
  }

  checkSupport(): boolean {
    return (
      'serviceWorker' in navigator &&
      'PushManager' in window &&
      'Notification' in window
    )
  }

  getPermissionStatus(): NotificationPermission {
    if (!this.checkSupport()) {
      return { granted: false, denied: true, prompt: false }
    }

    const permission = Notification.permission
    return {
      granted: permission === 'granted',
      denied: permission === 'denied',
      prompt: permission === 'default'
    }
  }

  async requestPermission(): Promise<boolean> {
    if (!this.checkSupport()) return false

    try {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    } catch (error) {
      console.error('Permission request failed:', error)
      return false
    }
  }

  async subscribe(preferences: NotificationPreferences): Promise<PushSubscription | null> {
    if (!await this.requestPermission()) return null
    if (!this.serviceWorkerRegistration) {
      await this.initServiceWorker()
      if (!this.serviceWorkerRegistration) return null
    }

    try {
      // Check for existing subscription
      let subscription = await this.serviceWorkerRegistration.pushManager.getSubscription()
      
      if (!subscription) {
        // Create new subscription
        subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
        })
      }

      // Send subscription to server with preferences
      await this.sendSubscriptionToServer(subscription, preferences)
      
      // Store preferences locally
      localStorage.setItem('notification-preferences', JSON.stringify(preferences))
      
      return subscription
    } catch (error) {
      console.error('Push subscription failed:', error)
      return null
    }
  }

  async unsubscribe(): Promise<boolean> {
    if (!this.serviceWorkerRegistration) return false

    try {
      const subscription = await this.serviceWorkerRegistration.pushManager.getSubscription()
      
      if (subscription) {
        // Unsubscribe from push service
        const unsubscribed = await subscription.unsubscribe()
        
        if (unsubscribed) {
          // Notify server
          await this.removeSubscriptionFromServer(subscription)
          
          // Clear local preferences
          localStorage.removeItem('notification-preferences')
          
          return true
        }
      }
      
      return false
    } catch (error) {
      console.error('Unsubscribe failed:', error)
      return false
    }
  }

  async updatePreferences(preferences: NotificationPreferences): Promise<boolean> {
    if (!this.serviceWorkerRegistration) return false

    try {
      const subscription = await this.serviceWorkerRegistration.pushManager.getSubscription()
      
      if (subscription) {
        await this.sendSubscriptionToServer(subscription, preferences)
        localStorage.setItem('notification-preferences', JSON.stringify(preferences))
        return true
      }
      
      return false
    } catch (error) {
      console.error('Update preferences failed:', error)
      return false
    }
  }

  async sendLocalNotification(data: PushNotificationData): Promise<void> {
    if (!await this.requestPermission()) return

    try {
      const options: NotificationOptions = {
        body: data.body,
        icon: data.icon || '/icon-192x192.png',
        badge: data.badge || '/icon-72x72.png',
        tag: data.tag || 'options-calculator',
        data: data.data || {},
        requireInteraction: data.requireInteraction || false,
        silent: data.silent || false,
        vibrate: data.vibrate || [100, 50, 100],
        actions: data.actions || []
      }

      const notification = new Notification(data.title, options)
      
      // Auto-close after 5 seconds if not require interaction
      if (!data.requireInteraction) {
        setTimeout(() => notification.close(), 5000)
      }
    } catch (error) {
      console.error('Local notification failed:', error)
    }
  }

  async scheduleNotification(data: PushNotificationData, delay: number): Promise<void> {
    setTimeout(async () => {
      await this.sendLocalNotification(data)
    }, delay)
  }

  clearAllNotifications(): void {
    // Close all notifications with our tag
    if ('serviceWorker' in navigator && this.serviceWorkerRegistration) {
      this.serviceWorkerRegistration.getNotifications({ tag: 'options-calculator' })
        .then(notifications => {
          notifications.forEach(notification => notification.close())
        })
        .catch(error => console.error('Clear notifications failed:', error))
    }
  }

  // Helper methods

  private async sendSubscriptionToServer(
    subscription: PushSubscription, 
    preferences: NotificationPreferences
  ): Promise<void> {
    const subscriptionData: NotificationSubscription = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')!),
        auth: this.arrayBufferToBase64(subscription.getKey('auth')!)
      },
      userId: this.getUserId(),
      preferences
    }

    try {
      const response = await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(subscriptionData)
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to send subscription to server:', error)
      // Don't throw - allow local functionality to continue
    }
  }

  private async removeSubscriptionFromServer(subscription: PushSubscription): Promise<void> {
    try {
      await fetch('/api/notifications/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          userId: this.getUserId()
        })
      })
    } catch (error) {
      console.error('Failed to remove subscription from server:', error)
      // Don't throw - allow local unsubscribe to continue
    }
  }

  private getUserId(): string {
    // Get or generate unique user ID
    let userId = localStorage.getItem('user-id')
    if (!userId) {
      userId = this.generateUserId()
      localStorage.setItem('user-id', userId)
    }
    return userId
  }

  private generateUserId(): string {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    
    return outputArray
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer)
    const binary = bytes.reduce((acc, byte) => acc + String.fromCharCode(byte), '')
    return window.btoa(binary)
  }
}

// Predefined notification types for the options calculator
export const NotificationTypes = {
  EARNINGS_ALERT: {
    title: 'Earnings Alert',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    tag: 'earnings',
    requireInteraction: true,
    vibrate: [200, 100, 200]
  },
  
  OPPORTUNITY_FOUND: {
    title: 'Trading Opportunity',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    tag: 'opportunity',
    requireInteraction: true,
    vibrate: [100, 50, 100, 50, 100]
  },
  
  POSITION_ALERT: {
    title: 'Position Alert',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    tag: 'position',
    requireInteraction: false,
    vibrate: [100, 100, 100]
  },
  
  MARKET_UPDATE: {
    title: 'Market Update',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    tag: 'market',
    requireInteraction: false,
    vibrate: [100]
  }
}

// Export singleton instance
export const notificationService = new PushNotificationManager()

export default notificationService