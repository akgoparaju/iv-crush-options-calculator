/**
 * Authentication Context for Phase 5.1
 * JWT-based authentication state management
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { AuthService, UserProfile, LoginCredentials, RegisterData } from '../services/authService'
import { TokenStorage } from '../utils/tokenStorage'

interface AuthContextValue {
  // Authentication state
  user: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Authentication actions
  login: (credentials: LoginCredentials) => Promise<boolean>
  register: (data: RegisterData) => Promise<boolean>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  
  // Profile management
  updateProfile: (data: Partial<UserProfile>) => Promise<boolean>
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>
  
  // Password reset
  forgotPassword: (email: string) => Promise<boolean>
  resetPassword: (token: string, newPassword: string) => Promise<boolean>
  
  // Utility functions
  clearError: () => void
}

interface AuthProviderProps {
  children: ReactNode
}

const AuthContext = createContext<AuthContextValue | null>(null)

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const authService = new AuthService()
  const isAuthenticated = !!user

  // Initialize authentication state
  useEffect(() => {
    initializeAuth()
  }, [])

  // Set up token refresh interval
  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(async () => {
        await refreshToken()
      }, 25 * 60 * 1000) // Refresh every 25 minutes (5 minutes before expiry)

      return () => clearInterval(interval)
    }
  }, [isAuthenticated])

  const initializeAuth = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const token = TokenStorage.getAccessToken()
      if (!token) {
        setIsLoading(false)
        return
      }

      // Verify token and get user profile
      const profile = await authService.getProfile()
      if (profile) {
        setUser(profile)
      } else {
        // Token invalid, clear storage
        TokenStorage.clearTokens()
      }
    } catch (err) {
      console.error('Auth initialization error:', err)
      TokenStorage.clearTokens()
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const result = await authService.login(credentials)
      if (result.success && result.user && result.token) {
        // Store tokens
        TokenStorage.setTokens(result.token.access_token, result.token.refresh_token)
        
        // Set user state
        setUser(result.user)
        
        return true
      } else {
        setError(result.message || 'Login failed')
        return false
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Login failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const result = await authService.register(data)
      if (result.success && result.user && result.token) {
        // Store tokens
        TokenStorage.setTokens(result.token.access_token, result.token.refresh_token)
        
        // Set user state
        setUser(result.user)
        
        return true
      } else {
        setError(result.message || 'Registration failed')
        return false
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Registration failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true)
      
      // Call logout endpoint
      await authService.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      // Always clear local state regardless of API call result
      TokenStorage.clearTokens()
      setUser(null)
      setError(null)
      setIsLoading(false)
    }
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()
      if (!refreshTokenValue) {
        return false
      }

      const result = await authService.refreshToken()
      if (result && result.access_token) {
        // Update tokens
        TokenStorage.setTokens(result.access_token, result.refresh_token || refreshTokenValue)
        
        // Update user if provided
        if (result.user) {
          setUser(result.user)
        }
        
        return true
      } else {
        // Refresh failed, logout
        await logout()
        return false
      }
    } catch (err) {
      console.error('Token refresh error:', err)
      await logout()
      return false
    }
  }

  const updateProfile = async (data: Partial<UserProfile>): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const updatedUser = await authService.updateProfile(data)
      if (updatedUser) {
        setUser(updatedUser)
        return true
      }
      
      return false
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Profile update failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const success = await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: newPassword
      })
      
      if (!success) {
        setError('Password change failed')
      }
      
      return success
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Password change failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const forgotPassword = async (email: string): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const success = await authService.forgotPassword(email)
      return success
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Password reset request failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const resetPassword = async (token: string, newPassword: string): Promise<boolean> => {
    try {
      setIsLoading(true)
      setError(null)
      
      const success = await authService.resetPassword({
        token,
        new_password: newPassword,
        confirm_password: newPassword
      })
      
      if (!success) {
        setError('Password reset failed')
      }
      
      return success
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Password reset failed'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  const contextValue: AuthContextValue = {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    
    // Actions
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    forgotPassword,
    resetPassword,
    clearError
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext