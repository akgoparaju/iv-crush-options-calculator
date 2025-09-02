/**
 * WebSocket service for real-time market data updates
 */

export interface PriceUpdate {
  symbol: string
  price: number
  change: number
  changePercent: number
  timestamp: string
  source: string
}

export interface MarketStatus {
  isOpen: boolean
  nextOpen?: string
  nextClose?: string
  timezone: string
}

export interface WebSocketMessage {
  type: 'price_update' | 'market_status' | 'analysis_update' | 'error'
  data: PriceUpdate | MarketStatus | any
  timestamp: string
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private subscribers = new Map<string, Set<(data: any) => void>>()
  private connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected'
  private statusCallbacks = new Set<(status: string) => void>()

  constructor(private url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.connectionStatus = 'connecting'
      this.notifyStatusChange()

      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('🔌 WebSocket connected')
          this.connectionStatus = 'connected'
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.notifyStatusChange()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason)
          this.connectionStatus = 'disconnected'
          this.stopHeartbeat()
          this.notifyStatusChange()
          
          // Attempt to reconnect if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (error) => {
          console.error('🔌 WebSocket error:', error)
          this.connectionStatus = 'error'
          this.notifyStatusChange()
          reject(error)
        }

      } catch (error) {
        this.connectionStatus = 'error'
        this.notifyStatusChange()
        reject(error)
      }
    })
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.stopHeartbeat()
    this.subscribers.clear()
    this.statusCallbacks.clear()
  }

  subscribe(type: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(type)) {
      this.subscribers.set(type, new Set())
    }
    
    this.subscribers.get(type)!.add(callback)
    
    // Auto-connect if not connected
    if (this.connectionStatus === 'disconnected') {
      this.connect().catch(console.error)
    }

    // Return unsubscribe function
    return () => {
      const typeSubscribers = this.subscribers.get(type)
      if (typeSubscribers) {
        typeSubscribers.delete(callback)
        if (typeSubscribers.size === 0) {
          this.subscribers.delete(type)
        }
      }
      
      // Disconnect if no more subscribers
      if (this.subscribers.size === 0) {
        this.disconnect()
      }
    }
  }

  subscribeToSymbol(symbol: string, callback: (data: PriceUpdate) => void): () => void {
    // Send subscription message to server
    this.send({
      type: 'subscribe',
      data: { symbol: symbol.toUpperCase() }
    })

    return this.subscribe(`price_${symbol.toUpperCase()}`, callback)
  }

  subscribeToMarketStatus(callback: (data: MarketStatus) => void): () => void {
    return this.subscribe('market_status', callback)
  }

  onStatusChange(callback: (status: string) => void): () => void {
    this.statusCallbacks.add(callback)
    
    // Call immediately with current status
    callback(this.connectionStatus)
    
    return () => {
      this.statusCallbacks.delete(callback)
    }
  }

  getConnectionStatus(): string {
    return this.connectionStatus
  }

  private send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'price_update':
        const priceData = message.data as PriceUpdate
        const subscribers = this.subscribers.get(`price_${priceData.symbol}`)
        if (subscribers) {
          subscribers.forEach(callback => callback(priceData))
        }
        break

      case 'market_status':
        const statusSubscribers = this.subscribers.get('market_status')
        if (statusSubscribers) {
          statusSubscribers.forEach(callback => callback(message.data))
        }
        break

      case 'analysis_update':
        // Handle analysis updates (for future use)
        break

      case 'error':
        console.error('WebSocket server error:', message.data)
        break

      default:
        console.warn('Unknown message type:', message.type)
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000)
    
    console.log(`🔌 Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)
    
    setTimeout(() => {
      if (this.connectionStatus !== 'connected') {
        this.connect().catch(console.error)
      }
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
      }
    }, 30000) // Ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private notifyStatusChange(): void {
    this.statusCallbacks.forEach(callback => callback(this.connectionStatus))
  }
}

// Create singleton instance
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
export const webSocketService = new WebSocketService(wsUrl)

export default webSocketService