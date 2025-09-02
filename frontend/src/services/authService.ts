/**
 * Authentication Service for Phase 5.1
 * Frontend service for JWT-based authentication
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { TokenStorage } from '../utils/tokenStorage'

// =====================================================================================
// Types and Interfaces
// =====================================================================================

export interface UserProfile {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  confirm_password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
  user: UserProfile
}

export interface AuthResponse {
  success: boolean
  message: string
  user?: UserProfile
  token?: TokenResponse
}

export interface PasswordResetResponse {
  success: boolean
  message: string
  email?: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface PasswordResetRequest {
  token: string
  new_password: string
  confirm_password: string
}

// =====================================================================================
// Authentication Service Class
// =====================================================================================

export class AuthService {
  private api: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    
    // Create axios instance
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Setup interceptors
    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = TokenStorage.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - Handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        // If 401 and not already retrying, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = TokenStorage.getRefreshToken()
            if (refreshToken) {
              const response = await axios.post(
                `${this.baseURL}/auth/refresh`,
                {},
                {
                  headers: {
                    Authorization: `Bearer ${refreshToken}`
                  }
                }
              )

              const { access_token, refresh_token } = response.data
              TokenStorage.setTokens(access_token, refresh_token || refreshToken)

              // Retry original request with new token
              originalRequest.headers.Authorization = `Bearer ${access_token}`
              return this.api(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            TokenStorage.clearTokens()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  // =====================================================================================
  // Authentication Methods
  // =====================================================================================

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.api.post('/auth/login', credentials)
      return response.data
    } catch (error: any) {
      throw this.handleError(error, 'Login failed')
    }
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.api.post('/auth/register', data)
      return response.data
    } catch (error: any) {
      throw this.handleError(error, 'Registration failed')
    }
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout')
    } catch (error) {
      // Log error but don't throw - we want to clear local state regardless
      console.error('Logout API call failed:', error)
    } finally {
      TokenStorage.clearTokens()
    }
  }

  async refreshToken(): Promise<TokenResponse | null> {
    try {
      const refreshToken = TokenStorage.getRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response: AxiosResponse<TokenResponse> = await axios.post(
        `${this.baseURL}/auth/refresh`,
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`
          }
        }
      )

      return response.data
    } catch (error: any) {
      console.error('Token refresh failed:', error)
      return null
    }
  }

  // =====================================================================================
  // Profile Management
  // =====================================================================================

  async getProfile(): Promise<UserProfile | null> {
    try {
      const response: AxiosResponse<UserProfile> = await this.api.get('/auth/profile')
      return response.data
    } catch (error) {
      console.error('Failed to get user profile:', error)
      return null
    }
  }

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile | null> {
    try {
      const response: AxiosResponse<UserProfile> = await this.api.put('/auth/profile', data)
      return response.data
    } catch (error: any) {
      throw this.handleError(error, 'Profile update failed')
    }
  }

  async changePassword(data: PasswordChangeRequest): Promise<boolean> {
    try {
      const response = await this.api.post('/auth/change-password', data)
      return response.data.success || true
    } catch (error: any) {
      throw this.handleError(error, 'Password change failed')
    }
  }

  // =====================================================================================
  // Password Reset
  // =====================================================================================

  async forgotPassword(email: string): Promise<boolean> {
    try {
      const response: AxiosResponse<PasswordResetResponse> = await this.api.post('/auth/forgot-password', { email })
      return response.data.success
    } catch (error: any) {
      throw this.handleError(error, 'Password reset request failed')
    }
  }

  async resetPassword(data: PasswordResetRequest): Promise<boolean> {
    try {
      const response = await this.api.post('/auth/reset-password', data)
      return response.data.success || true
    } catch (error: any) {
      throw this.handleError(error, 'Password reset failed')
    }
  }

  // =====================================================================================
  // Account Management
  // =====================================================================================

  async deleteAccount(): Promise<boolean> {
    try {
      const response = await this.api.delete('/auth/account')
      return response.data.success || true
    } catch (error: any) {
      throw this.handleError(error, 'Account deletion failed')
    }
  }

  // =====================================================================================
  // Utility Methods
  // =====================================================================================

  isAuthenticated(): boolean {
    const token = TokenStorage.getAccessToken()
    if (!token) return false

    try {
      // Simple JWT payload decode to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp > currentTime
    } catch {
      return false
    }
  }

  getCurrentUser(): UserProfile | null {
    const token = TokenStorage.getAccessToken()
    if (!token) return null

    try {
      // Decode JWT to get user info
      const payload = JSON.parse(atob(token.split('.')[1]))
      return {
        id: payload.user_id,
        email: payload.sub,
        username: payload.username,
        is_active: true,
        created_at: '',
        updated_at: ''
      }
    } catch {
      return null
    }
  }

  private handleError(error: any, defaultMessage: string): Error {
    const message = error?.response?.data?.detail || 
                   error?.response?.data?.message || 
                   error?.message || 
                   defaultMessage

    // Log full error for debugging
    console.error('AuthService error:', {
      message,
      status: error?.response?.status,
      data: error?.response?.data,
      error
    })

    return new Error(message)
  }
}

// Export singleton instance
export const authService = new AuthService()
export default authService