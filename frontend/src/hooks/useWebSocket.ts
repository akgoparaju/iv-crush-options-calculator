import { useState, useEffect, useCallback, useRef } from 'react'
import { webSocketService, PriceUpdate, MarketStatus } from '@/services/websocket'

/**
 * Hook for managing WebSocket connection status
 */
export const useWebSocketConnection = () => {
  const [status, setStatus] = useState<string>('disconnected')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const unsubscribe = webSocketService.onStatusChange((newStatus) => {
      setStatus(newStatus)
      if (newStatus === 'error') {
        setError('Connection error occurred')
      } else {
        setError(null)
      }
    })

    return unsubscribe
  }, [])

  const connect = useCallback(async () => {
    try {
      await webSocketService.connect()
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    }
  }, [])

  const disconnect = useCallback(() => {
    webSocketService.disconnect()
  }, [])

  return {
    status,
    error,
    connect,
    disconnect,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    hasError: status === 'error'
  }
}

/**
 * Hook for subscribing to real-time price updates for a specific symbol
 */
export const usePriceUpdates = (symbol: string | null, enabled: boolean = true) => {
  const [priceData, setPriceData] = useState<PriceUpdate | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!symbol || !enabled) {
      setPriceData(null)
      setLastUpdate(null)
      setError(null)
      return
    }

    let unsubscribe: (() => void) | null = null

    const startSubscription = async () => {
      try {
        unsubscribe = webSocketService.subscribeToSymbol(symbol, (data: PriceUpdate) => {
          setPriceData(data)
          setLastUpdate(new Date())
          setError(null)
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Subscription failed')
      }
    }

    startSubscription()

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [symbol, enabled])

  return {
    priceData,
    lastUpdate,
    error,
    isStale: lastUpdate ? Date.now() - lastUpdate.getTime() > 60000 : true // 1 minute staleness
  }
}

/**
 * Hook for subscribing to market status updates
 */
export const useMarketStatus = (enabled: boolean = true) => {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled) {
      setMarketStatus(null)
      setError(null)
      return
    }

    let unsubscribe: (() => void) | null = null

    const startSubscription = async () => {
      try {
        unsubscribe = webSocketService.subscribeToMarketStatus((data: MarketStatus) => {
          setMarketStatus(data)
          setError(null)
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Market status subscription failed')
      }
    }

    startSubscription()

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [enabled])

  return {
    marketStatus,
    error,
    isMarketOpen: marketStatus?.isOpen ?? null
  }
}

/**
 * Hook for auto-refreshing stale data
 */
export const useAutoRefresh = (
  refreshCallback: () => void,
  intervalMs: number = 300000, // 5 minutes default
  enabled: boolean = true
) => {
  const callbackRef = useRef(refreshCallback)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = refreshCallback
  }, [refreshCallback])

  useEffect(() => {
    if (!enabled) return

    const interval = setInterval(() => {
      callbackRef.current()
      setLastRefresh(new Date())
    }, intervalMs)

    return () => clearInterval(interval)
  }, [intervalMs, enabled])

  const manualRefresh = useCallback(() => {
    callbackRef.current()
    setLastRefresh(new Date())
  }, [])

  return {
    lastRefresh,
    manualRefresh
  }
}

/**
 * Comprehensive WebSocket hook combining connection, price updates, and market status
 */
export const useRealTimeData = (symbol: string | null, options: {
  enablePriceUpdates?: boolean
  enableMarketStatus?: boolean
  autoRefreshInterval?: number
} = {}) => {
  const {
    enablePriceUpdates = true,
    enableMarketStatus = true,
    autoRefreshInterval = 300000
  } = options

  const connection = useWebSocketConnection()
  const priceUpdates = usePriceUpdates(symbol, enablePriceUpdates)
  const marketStatus = useMarketStatus(enableMarketStatus)

  // Auto-refresh fallback for when WebSocket is not connected
  const { lastRefresh, manualRefresh } = useAutoRefresh(() => {
    if (!connection.isConnected && symbol) {
      // Could trigger a REST API call here as fallback
      console.log('Auto-refresh triggered for', symbol)
    }
  }, autoRefreshInterval, !connection.isConnected)

  return {
    // Connection status
    connection,
    
    // Price data
    priceData: priceUpdates.priceData,
    priceError: priceUpdates.error,
    isPriceStale: priceUpdates.isStale,
    
    // Market status
    marketStatus: marketStatus.marketStatus,
    marketError: marketStatus.error,
    isMarketOpen: marketStatus.isMarketOpen,
    
    // Auto-refresh
    lastRefresh,
    manualRefresh,
    
    // Overall status
    isRealTime: connection.isConnected && !priceUpdates.error,
    hasAnyError: !!connection.error || !!priceUpdates.error || !!marketStatus.error
  }
}

export default useRealTimeData