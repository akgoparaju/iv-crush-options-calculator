import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import usePWA, { PWAStatus, PWAActions } from '../hooks/usePWA'
import { offlineDataService } from '../services/offlineData'
import { notificationService, NotificationPreferences } from '../services/notifications'

interface PWAContextValue {
  // PWA Status and Actions
  pwaStatus: PWAStatus
  pwaActions: PWAActions
  
  // Offline Data
  isOfflineMode: boolean
  offlineDataAvailable: boolean
  syncPendingCount: number
  
  // Notifications
  notificationsEnabled: boolean
  notificationPreferences: NotificationPreferences | null
  
  // Actions
  enableOfflineMode: () => Promise<void>
  disableOfflineMode: () => Promise<void>
  syncOfflineData: () => Promise<void>
  updateNotificationPreferences: (preferences: NotificationPreferences) => Promise<void>
  sendTestNotification: () => Promise<void>
  
  // Performance
  performanceMetrics: PerformanceMetrics
  updatePerformanceMetrics: () => void
}

interface PerformanceMetrics {
  loadTime: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  cumulativeLayoutShift: number
  firstInputDelay: number
  cacheHitRate: number
  offlineRequests: number
}

interface PWAProviderProps {
  children: ReactNode
}

const PWAContext = createContext<PWAContextValue | null>(null)

export const PWAProvider: React.FC<PWAProviderProps> = ({ children }) => {
  const [pwaStatus, pwaActions] = usePWA()
  
  // Offline state
  const [isOfflineMode, setIsOfflineMode] = useState(!navigator.onLine)
  const [offlineDataAvailable, setOfflineDataAvailable] = useState(false)
  const [syncPendingCount, setSyncPendingCount] = useState(0)
  
  // Notification state
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [notificationPreferences, setNotificationPreferences] = useState<NotificationPreferences | null>(null)
  
  // Performance state
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    loadTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    cumulativeLayoutShift: 0,
    firstInputDelay: 0,
    cacheHitRate: 0,
    offlineRequests: 0
  })

  // Initialize offline data and check status
  useEffect(() => {
    const initializeOfflineFeatures = async () => {
      try {
        // Check if offline data is available
        const symbols = offlineDataService.getSymbols()
        setOfflineDataAvailable(symbols.length > 0)
        
        // Load notification preferences
        const savedPreferences = localStorage.getItem('notification-preferences')
        if (savedPreferences) {
          const preferences = JSON.parse(savedPreferences) as NotificationPreferences
          setNotificationPreferences(preferences)
        }
        
        // Check notification status
        const permission = notificationService.getPermissionStatus()
        setNotificationsEnabled(permission.granted)
        
        // Initialize performance monitoring
        updatePerformanceMetrics()
      } catch (error) {
        console.error('Failed to initialize offline features:', error)
      }
    }

    initializeOfflineFeatures()
  }, [])

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = async () => {
      setIsOfflineMode(false)
      // Sync any pending data when coming back online
      if (pwaStatus.isServiceWorkerRegistered) {
        await syncOfflineData()
      }
    }

    const handleOffline = () => {
      setIsOfflineMode(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [pwaStatus.isServiceWorkerRegistered])

  // Enable offline mode
  const enableOfflineMode = async (): Promise<void> => {
    try {
      // Preload some demo data for offline use
      const popularSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
      for (const symbol of popularSymbols) {
        await offlineDataService.getAnalysis(symbol)
      }
      
      setOfflineDataAvailable(true)
      console.log('Offline mode enabled with demo data')
    } catch (error) {
      console.error('Failed to enable offline mode:', error)
    }
  }

  // Disable offline mode
  const disableOfflineMode = async (): Promise<void> => {
    try {
      await offlineDataService.clearCache()
      setOfflineDataAvailable(false)
      console.log('Offline mode disabled and cache cleared')
    } catch (error) {
      console.error('Failed to disable offline mode:', error)
    }
  }

  // Sync offline data
  const syncOfflineData = async (): Promise<void> => {
    if (!navigator.onLine) return

    try {
      await offlineDataService.syncPendingData()
      setSyncPendingCount(0)
      console.log('Offline data synced successfully')
    } catch (error) {
      console.error('Failed to sync offline data:', error)
    }
  }

  // Update notification preferences
  const updateNotificationPreferences = async (preferences: NotificationPreferences): Promise<void> => {
    try {
      const success = await notificationService.updatePreferences(preferences)
      if (success) {
        setNotificationPreferences(preferences)
        setNotificationsEnabled(true)
      }
    } catch (error) {
      console.error('Failed to update notification preferences:', error)
    }
  }

  // Send test notification
  const sendTestNotification = async (): Promise<void> => {
    try {
      await notificationService.sendLocalNotification({
        title: 'Options Calculator Test',
        body: 'Notifications are working! You\'ll receive alerts for trading opportunities and earnings.',
        tag: 'test-notification',
        requireInteraction: false,
        data: { type: 'test' }
      })
    } catch (error) {
      console.error('Failed to send test notification:', error)
    }
  }

  // Update performance metrics
  const updatePerformanceMetrics = (): void => {
    if ('performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const paint = performance.getEntriesByType('paint')
      
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint')
      
      setPerformanceMetrics(prev => ({
        ...prev,
        loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
        firstContentfulPaint: fcp ? fcp.startTime : 0,
        largestContentfulPaint: 0, // Would need LCP observer
        cumulativeLayoutShift: 0, // Would need CLS observer
        firstInputDelay: 0 // Would need FID observer
      }))

      // Web Vitals would be better implemented with the web-vitals library
      // but this provides basic metrics for now
    }
  }

  // Performance observer for Core Web Vitals (simplified)
  useEffect(() => {
    if ('PerformanceObserver' in window) {
      try {
        // Largest Contentful Paint
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1]
          setPerformanceMetrics(prev => ({
            ...prev,
            largestContentfulPaint: lastEntry.startTime
          }))
        })
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })

        // First Input Delay
        const fidObserver = new PerformanceObserver((list) => {
          const firstInput = list.getEntries()[0]
          setPerformanceMetrics(prev => ({
            ...prev,
            firstInputDelay: firstInput.processingStart - firstInput.startTime
          }))
        })
        fidObserver.observe({ entryTypes: ['first-input'] })

        return () => {
          lcpObserver.disconnect()
          fidObserver.disconnect()
        }
      } catch (error) {
        console.warn('Performance observers not fully supported:', error)
      }
    }
  }, [])

  const contextValue: PWAContextValue = {
    // PWA Status and Actions
    pwaStatus,
    pwaActions,
    
    // Offline Data
    isOfflineMode,
    offlineDataAvailable,
    syncPendingCount,
    
    // Notifications
    notificationsEnabled,
    notificationPreferences,
    
    // Actions
    enableOfflineMode,
    disableOfflineMode,
    syncOfflineData,
    updateNotificationPreferences,
    sendTestNotification,
    
    // Performance
    performanceMetrics,
    updatePerformanceMetrics
  }

  return (
    <PWAContext.Provider value={contextValue}>
      {children}
    </PWAContext.Provider>
  )
}

export const usePWAContext = (): PWAContextValue => {
  const context = useContext(PWAContext)
  if (!context) {
    throw new Error('usePWAContext must be used within a PWAProvider')
  }
  return context
}

export default PWAContext