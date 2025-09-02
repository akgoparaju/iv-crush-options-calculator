import { useState, useEffect, useCallback } from 'react'

export interface PWAInstallPrompt {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export interface PWAStatus {
  isInstalled: boolean
  isInstallable: boolean
  isOnline: boolean
  installPrompt: PWAInstallPrompt | null
  isServiceWorkerSupported: boolean
  isServiceWorkerRegistered: boolean
  hasUpdate: boolean
}

export interface PWAActions {
  install: () => Promise<boolean>
  checkForUpdates: () => Promise<void>
  skipWaiting: () => void
  enableNotifications: () => Promise<boolean>
  disableNotifications: () => Promise<void>
  subscribeToNotifications: () => Promise<PushSubscription | null>
}

export const usePWA = (): [PWAStatus, PWAActions] => {
  const [pwaStatus, setPwaStatus] = useState<PWAStatus>({
    isInstalled: false,
    isInstallable: false,
    isOnline: navigator.onLine,
    installPrompt: null,
    isServiceWorkerSupported: 'serviceWorker' in navigator,
    isServiceWorkerRegistered: false,
    hasUpdate: false
  })

  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [serviceWorkerRegistration, setServiceWorkerRegistration] = useState<ServiceWorkerRegistration | null>(null)

  // Check if app is installed
  const checkInstallStatus = useCallback(() => {
    const isInstalled = 
      window.matchMedia && 
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true ||
      document.referrer.includes('android-app://')

    setPwaStatus(prev => ({ ...prev, isInstalled }))
  }, [])

  // Register service worker
  const registerServiceWorker = useCallback(async () => {
    if (!pwaStatus.isServiceWorkerSupported) return

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })

      setServiceWorkerRegistration(registration)
      setPwaStatus(prev => ({ ...prev, isServiceWorkerRegistered: true }))

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed') {
              if (navigator.serviceWorker.controller) {
                // New version available
                setPwaStatus(prev => ({ ...prev, hasUpdate: true }))
              }
            }
          })
        }
      })

      console.log('ServiceWorker registered successfully')
    } catch (error) {
      console.error('ServiceWorker registration failed:', error)
    }
  }, [pwaStatus.isServiceWorkerSupported])

  // Install app
  const install = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) return false

    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      
      setDeferredPrompt(null)
      setPwaStatus(prev => ({ 
        ...prev, 
        isInstallable: false,
        installPrompt: null
      }))

      return outcome === 'accepted'
    } catch (error) {
      console.error('Install failed:', error)
      return false
    }
  }, [deferredPrompt])

  // Check for updates
  const checkForUpdates = useCallback(async (): Promise<void> => {
    if (serviceWorkerRegistration) {
      await serviceWorkerRegistration.update()
    }
  }, [serviceWorkerRegistration])

  // Skip waiting and activate new service worker
  const skipWaiting = useCallback(() => {
    if (serviceWorkerRegistration?.waiting) {
      serviceWorkerRegistration.waiting.postMessage({ type: 'SKIP_WAITING' })
      window.location.reload()
    }
  }, [serviceWorkerRegistration])

  // Enable notifications
  const enableNotifications = useCallback(async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications')
      return false
    }

    if (Notification.permission === 'granted') {
      return true
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    }

    return false
  }, [])

  // Disable notifications
  const disableNotifications = useCallback(async (): Promise<void> => {
    if (serviceWorkerRegistration) {
      const subscription = await serviceWorkerRegistration.pushManager.getSubscription()
      if (subscription) {
        await subscription.unsubscribe()
      }
    }
  }, [serviceWorkerRegistration])

  // Subscribe to push notifications
  const subscribeToNotifications = useCallback(async (): Promise<PushSubscription | null> => {
    if (!serviceWorkerRegistration || !await enableNotifications()) {
      return null
    }

    try {
      const subscription = await serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(
          // Replace with your VAPID public key
          process.env.REACT_APP_VAPID_PUBLIC_KEY || 'BMfQzhxqnwwlEr0X5QR1k2UBqjrz5E6GzB_M-fEUq3fJqJe2zF8YvJ2tB9RqQ1xJ8e5EQc1Gf5r5Z8x7Y3Q4J9w'
        )
      })

      // Send subscription to server
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription)
      })

      return subscription
    } catch (error) {
      console.error('Push subscription failed:', error)
      return null
    }
  }, [serviceWorkerRegistration, enableNotifications])

  // Effect to handle install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setPwaStatus(prev => ({ 
        ...prev, 
        isInstallable: true,
        installPrompt: e as any
      }))
    }

    const handleAppInstalled = () => {
      console.log('PWA was installed')
      setDeferredPrompt(null)
      setPwaStatus(prev => ({ 
        ...prev, 
        isInstalled: true,
        isInstallable: false,
        installPrompt: null
      }))
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  // Effect to handle online/offline status
  useEffect(() => {
    const handleOnline = () => setPwaStatus(prev => ({ ...prev, isOnline: true }))
    const handleOffline = () => setPwaStatus(prev => ({ ...prev, isOnline: false }))

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Initialize
  useEffect(() => {
    checkInstallStatus()
    registerServiceWorker()
  }, [checkInstallStatus, registerServiceWorker])

  const actions: PWAActions = {
    install,
    checkForUpdates,
    skipWaiting,
    enableNotifications,
    disableNotifications,
    subscribeToNotifications
  }

  return [pwaStatus, actions]
}

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String: string): Uint8Array {
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

export default usePWA