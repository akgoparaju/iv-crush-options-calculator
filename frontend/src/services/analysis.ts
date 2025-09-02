import { apiClient } from './api'
import { 
  AnalysisRequest, 
  AnalysisResponse, 
  HealthResponse,
  ErrorResponse 
} from '@/types/api'

/**
 * Analysis service - handles all options analysis API calls
 */
export class AnalysisService {
  
  /**
   * Perform comprehensive options analysis
   */
  async analyzeSymbol(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      const response = await apiClient.post<AnalysisResponse>('/api/analyze', request)
      
      // Type guard to ensure we got a successful response
      if ('success' in response && response.success) {
        return response
      }
      
      // If we got an error response, throw it
      throw response as ErrorResponse
      
    } catch (error) {
      console.error('Analysis failed:', error)
      throw error
    }
  }

  /**
   * Quick analysis with URL parameters
   */
  async quickAnalyze(
    symbol: string, 
    options: {
      includeEarnings?: boolean
      includeTrades?: boolean
      useDemo?: boolean
    } = {}
  ): Promise<AnalysisResponse> {
    try {
      const params = {
        include_earnings: options.includeEarnings || false,
        include_trades: options.includeTrades || false,
        use_demo: options.useDemo || false
      }
      
      const response = await apiClient.get<AnalysisResponse>(
        `/api/analyze/${symbol}`,
        params
      )
      
      if ('success' in response && response.success) {
        return response
      }
      
      throw response as ErrorResponse
      
    } catch (error) {
      console.error('Quick analysis failed:', error)
      throw error
    }
  }

  /**
   * Get basic symbol information
   */
  async getBasicSymbolInfo(symbol: string) {
    try {
      const response = await apiClient.get(`/api/symbols/${symbol}/basic`)
      return response
      
    } catch (error) {
      console.error('Failed to get symbol info:', error)
      throw error
    }
  }

  /**
   * Validate symbol before analysis
   */
  async validateSymbol(symbol: string): Promise<boolean> {
    try {
      await this.getBasicSymbolInfo(symbol)
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Get analysis history (future feature)
   */
  async getAnalysisHistory(symbol?: string) {
    // Placeholder for future implementation
    console.log('Analysis history not yet implemented')
    return []
  }

  /**
   * Cancel ongoing analysis (future feature)
   */
  async cancelAnalysis(analysisId: string) {
    // Placeholder for future implementation
    console.log('Analysis cancellation not yet implemented')
    return { success: true }
  }
}

/**
 * Health service - handles health check API calls
 */
export class HealthService {
  
  /**
   * Basic health check
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await apiClient.get<HealthResponse>('/api/health')
      return response as HealthResponse
      
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }

  /**
   * Detailed health check with system information
   */
  async checkDetailedHealth(includeDependencies = false): Promise<HealthResponse> {
    try {
      const response = await apiClient.post<HealthResponse>('/api/health/detailed', {
        include_details: true,
        check_dependencies: includeDependencies
      })
      
      return response as HealthResponse
      
    } catch (error) {
      console.error('Detailed health check failed:', error)
      throw error
    }
  }

  /**
   * Check if API is ready
   */
  async checkReadiness(): Promise<boolean> {
    try {
      await apiClient.get('/api/health/ready')
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Check if API is alive
   */
  async checkLiveness(): Promise<boolean> {
    try {
      await apiClient.get('/api/health/live')
      return true
    } catch (error) {
      return false
    }
  }
}

/**
 * Cache service - handles cache management API calls
 */
export class CacheService {
  
  /**
   * Get cache statistics
   */
  async getCacheStats() {
    try {
      const response = await apiClient.post('/api/cache', {
        action: 'stats'
      })
      return response
      
    } catch (error) {
      console.error('Failed to get cache stats:', error)
      throw error
    }
  }

  /**
   * Clear cache for a symbol
   */
  async clearSymbolCache(symbol: string) {
    try {
      const response = await apiClient.post('/api/cache', {
        action: 'clear',
        symbol: symbol
      })
      return response
      
    } catch (error) {
      console.error('Failed to clear symbol cache:', error)
      throw error
    }
  }

  /**
   * Clear all cache
   */
  async clearAllCache() {
    try {
      const response = await apiClient.post('/api/cache', {
        action: 'flush'
      })
      return response
      
    } catch (error) {
      console.error('Failed to clear all cache:', error)
      throw error
    }
  }
}

// Create and export service instances
export const analysisService = new AnalysisService()
export const healthService = new HealthService()
export const cacheService = new CacheService()

// Services are already exported above with their class declarations