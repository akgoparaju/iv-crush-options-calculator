import React, { useState, useEffect } from 'react'
import { Download, X, Smartphone, Monitor, Wifi, WifiOff } from 'lucide-react'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import usePWA from '../../hooks/usePWA'

interface InstallPromptProps {
  className?: string
  showAlways?: boolean
  variant?: 'banner' | 'card' | 'minimal'
}

const InstallPrompt: React.FC<InstallPromptProps> = ({ 
  className = '',
  showAlways = false,
  variant = 'banner'
}) => {
  const [pwaStatus, pwaActions] = usePWA()
  const [dismissed, setDismissed] = useState(false)
  const [installing, setInstalling] = useState(false)
  const [showFeatures, setShowFeatures] = useState(false)

  // Check if user has dismissed the prompt
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    if (dismissed && !showAlways) {
      setDismissed(true)
    }
  }, [showAlways])

  const handleInstall = async () => {
    setInstalling(true)
    try {
      const installed = await pwaActions.install()
      if (installed) {
        setDismissed(true)
        localStorage.setItem('pwa-install-dismissed', 'true')
      }
    } catch (error) {
      console.error('Installation failed:', error)
    }
    setInstalling(false)
  }

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('pwa-install-dismissed', 'true')
  }

  // Don't show if already installed, not installable, or dismissed
  if (pwaStatus.isInstalled || !pwaStatus.isInstallable || (dismissed && !showAlways)) {
    return null
  }

  if (variant === 'minimal') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Button
          variant="primary"
          size="sm"
          onClick={handleInstall}
          disabled={installing}
          className="flex items-center space-x-1"
        >
          <Download className="h-4 w-4" />
          <span>{installing ? 'Installing...' : 'Install App'}</span>
        </Button>
        {!showAlways && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    )
  }

  if (variant === 'card') {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-600">
              <Smartphone className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Install Options Calculator
              </h3>
              <p className="text-sm text-slate-600">
                Get native app experience with offline access
              </p>
            </div>
          </div>
          {!showAlways && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFeatures(!showFeatures)}
            className="text-primary-600 hover:text-primary-700 p-0"
          >
            {showFeatures ? 'Hide' : 'Show'} Features
          </Button>
          
          {showFeatures && (
            <div className="mt-3 space-y-2">
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <Monitor className="h-4 w-4 text-primary-600" />
                <span>Works like a native desktop/mobile app</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <WifiOff className="h-4 w-4 text-primary-600" />
                <span>Offline access with demo data</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <Wifi className="h-4 w-4 text-primary-600" />
                <span>Background updates and notifications</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <Download className="h-4 w-4 text-primary-600" />
                <span>No app store needed - install directly</span>
              </div>
            </div>
          )}
        </div>

        <div className="flex space-x-3">
          <Button
            variant="primary"
            onClick={handleInstall}
            disabled={installing}
            className="flex-1"
          >
            <Download className="h-4 w-4 mr-2" />
            {installing ? 'Installing...' : 'Install Now'}
          </Button>
          <Button
            variant="ghost"
            onClick={() => setShowFeatures(!showFeatures)}
            className="text-primary-600"
          >
            Learn More
          </Button>
        </div>
      </Card>
    )
  }

  // Default banner variant
  return (
    <div className={`bg-primary-50 border border-primary-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
            <Smartphone className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-primary-900">
              Install Options Calculator
            </p>
            <p className="text-xs text-primary-700">
              Get faster access and offline features
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleInstall}
            disabled={installing}
            className="flex items-center space-x-1"
          >
            <Download className="h-3 w-3" />
            <span>{installing ? 'Installing...' : 'Install'}</span>
          </Button>
          {!showAlways && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="text-primary-600 hover:text-primary-700"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export default InstallPrompt