import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ApiResponse, ApiConfig, ErrorResponse } from '@/types/api'

// API Configuration
const defaultConfig: ApiConfig = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retries: 3
}

class ApiClient {
  private client: AxiosInstance
  private config: ApiConfig

  constructor(config: ApiConfig = defaultConfig) {
    this.config = config
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp to prevent caching issues
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now()
          }
        }

        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('❌ API Request Error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`)
        return response
      },
      async (error) => {
        const originalRequest = error.config
        
        // Handle network errors
        if (!error.response) {
          console.error('❌ Network Error:', error.message)
          return Promise.reject({
            success: false,
            error: 'network_error',
            message: 'Unable to connect to the analysis server. Please check your connection and try again.',
            timestamp: new Date().toISOString()
          } as ErrorResponse)
        }

        // Handle HTTP errors
        const status = error.response.status
        const errorData = error.response.data

        console.error(`❌ API Error: ${status} ${originalRequest.url}`, errorData)

        // Retry logic for 5xx errors (but not for 404s, 400s etc)
        if (status >= 500 && originalRequest._retryCount < this.config.retries) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1
          
          console.log(`🔄 Retrying request (${originalRequest._retryCount}/${this.config.retries})`)
          
          // Exponential backoff
          const delay = Math.pow(2, originalRequest._retryCount) * 1000
          await new Promise(resolve => setTimeout(resolve, delay))
          
          return this.client(originalRequest)
        }

        // Transform error to our standard format
        const standardError: ErrorResponse = {
          success: false,
          error: errorData?.error || `http_${status}`,
          message: errorData?.message || error.message || 'An unexpected error occurred',
          details: errorData?.details,
          timestamp: new Date().toISOString()
        }

        return Promise.reject(standardError)
      }
    )
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.request(config)
      return response.data
    } catch (error) {
      throw error // Error is already transformed by interceptor
    }
  }

  // GET request
  async get<T>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'GET',
      url,
      params
    })
  }

  // POST request
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'POST',
      url,
      data,
      ...config
    })
  }

  // PUT request
  async put<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'PUT',
      url,
      data
    })
  }

  // DELETE request
  async delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>({
      method: 'DELETE',
      url
    })
  }

  // Health check
  async healthCheck() {
    return this.get('/api/health')
  }

  // Get API info
  async getApiInfo() {
    return this.get('/api')
  }

  // Update base URL (useful for environment switching)
  updateBaseURL(baseURL: string) {
    this.config.baseURL = baseURL
    this.client.defaults.baseURL = baseURL
  }

  // Get current configuration
  getConfig() {
    return { ...this.config }
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient()

// Export the class for testing or custom instances
export { ApiClient }
export type { ApiConfig }