import React from 'react'
import { Wifi, WifiOff, Download, Bell, BellOff, RefreshCw } from 'lucide-react'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import usePWA from '../../hooks/usePWA'

interface PWAStatusProps {
  className?: string
  showDetails?: boolean
  variant?: 'badge' | 'indicator' | 'full'
}

const PWAStatus: React.FC<PWAStatusProps> = ({
  className = '',
  showDetails = false,
  variant = 'badge'
}) => {
  const [pwaStatus, pwaActions] = usePWA()

  const handleUpdate = () => {
    if (pwaStatus.hasUpdate) {
      pwaActions.skipWaiting()
    } else {
      pwaActions.checkForUpdates()
    }
  }

  const handleNotifications = async () => {
    try {
      const success = await pwaActions.enableNotifications()
      if (success) {
        await pwaActions.subscribeToNotifications()
      }
    } catch (error) {
      console.error('Notification setup failed:', error)
    }
  }

  if (variant === 'badge') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Badge 
          variant={pwaStatus.isOnline ? 'success' : 'warning'}
          className="flex items-center space-x-1"
        >
          {pwaStatus.isOnline ? (
            <Wifi className="h-3 w-3" />
          ) : (
            <WifiOff className="h-3 w-3" />
          )}
          <span>{pwaStatus.isOnline ? 'Online' : 'Offline'}</span>
        </Badge>
        
        {pwaStatus.isInstalled && (
          <Badge variant="primary" className="flex items-center space-x-1">
            <Download className="h-3 w-3" />
            <span>PWA</span>
          </Badge>
        )}
        
        {pwaStatus.hasUpdate && (
          <Badge variant="warning" className="flex items-center space-x-1 cursor-pointer" onClick={handleUpdate}>
            <RefreshCw className="h-3 w-3" />
            <span>Update</span>
          </Badge>
        )}
      </div>
    )
  }

  if (variant === 'indicator') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="flex items-center space-x-1">
          <div className={`w-2 h-2 rounded-full ${
            pwaStatus.isOnline ? 'bg-green-500' : 'bg-yellow-500'
          }`} />
          <span className="text-xs text-slate-600">
            {pwaStatus.isOnline ? 'Online' : 'Offline Mode'}
          </span>
        </div>
        
        {pwaStatus.hasUpdate && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleUpdate}
            className="text-xs p-1 h-auto"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
        )}
      </div>
    )
  }

  // Full variant with details
  return (
    <div className={`bg-slate-50 border border-slate-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-900">App Status</h3>
        <div className="flex items-center space-x-2">
          {pwaStatus.isOnline ? (
            <Wifi className="h-4 w-4 text-green-600" />
          ) : (
            <WifiOff className="h-4 w-4 text-yellow-600" />
          )}
        </div>
      </div>

      <div className="space-y-3">
        {/* Connection Status */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Connection</span>
          <Badge variant={pwaStatus.isOnline ? 'success' : 'warning'}>
            {pwaStatus.isOnline ? 'Online' : 'Offline'}
          </Badge>
        </div>

        {/* Installation Status */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Installation</span>
          <Badge variant={pwaStatus.isInstalled ? 'success' : 'secondary'}>
            {pwaStatus.isInstalled ? 'Installed' : 'Browser'}
          </Badge>
        </div>

        {/* Service Worker Status */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Service Worker</span>
          <Badge variant={pwaStatus.isServiceWorkerRegistered ? 'success' : 'secondary'}>
            {pwaStatus.isServiceWorkerRegistered ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Update Status */}
        {pwaStatus.hasUpdate && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Update Available</span>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpdate}
              className="text-xs"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Update
            </Button>
          </div>
        )}

        {/* Notifications */}
        {showDetails && pwaStatus.isServiceWorkerRegistered && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Notifications</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleNotifications}
              className="text-xs flex items-center space-x-1"
            >
              <Bell className="h-3 w-3" />
              <span>Enable</span>
            </Button>
          </div>
        )}

        {/* Offline Features */}
        {!pwaStatus.isOnline && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="flex items-start space-x-2">
              <WifiOff className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div className="text-xs text-yellow-800">
                <p className="font-medium">Offline Mode Active</p>
                <p className="mt-1">Limited features with demo data available</p>
              </div>
            </div>
          </div>
        )}

        {/* PWA Features */}
        {showDetails && pwaStatus.isInstalled && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
            <div className="flex items-start space-x-2">
              <Download className="h-4 w-4 text-blue-600 mt-0.5" />
              <div className="text-xs text-blue-800">
                <p className="font-medium">PWA Features Active</p>
                <ul className="mt-1 space-y-1 list-disc list-inside">
                  <li>Offline access with caching</li>
                  <li>Native app experience</li>
                  <li>Background updates</li>
                  <li>Push notifications</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PWAStatus