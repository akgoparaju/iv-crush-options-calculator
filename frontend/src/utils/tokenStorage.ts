/**
 * Token Storage Utility for Phase 5.1
 * Secure localStorage management for JWT tokens
 */

// =====================================================================================
// Constants
// =====================================================================================

const ACCESS_TOKEN_KEY = 'options_trader_access_token'
const REFRESH_TOKEN_KEY = 'options_trader_refresh_token'
const USER_KEY = 'options_trader_user'

// =====================================================================================
// Token Storage Class
// =====================================================================================

export class TokenStorage {
  // =====================================================================================
  // Token Management
  // =====================================================================================

  static setTokens(accessToken: string, refreshToken?: string): void {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
      
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
      }
      
      // Set token expiration check
      this.scheduleTokenExpiration(accessToken)
      
    } catch (error) {
      console.error('Error storing tokens:', error)
    }
  }

  static getAccessToken(): string | null {
    try {
      const token = localStorage.getItem(ACCESS_TOKEN_KEY)
      
      // Check if token is expired
      if (token && this.isTokenExpired(token)) {
        this.clearTokens()
        return null
      }
      
      return token
    } catch (error) {
      console.error('Error retrieving access token:', error)
      return null
    }
  }

  static getRefreshToken(): string | null {
    try {
      const token = localStorage.getItem(REFRESH_TOKEN_KEY)
      
      // Check if refresh token is expired
      if (token && this.isTokenExpired(token)) {
        this.clearTokens()
        return null
      }
      
      return token
    } catch (error) {
      console.error('Error retrieving refresh token:', error)
      return null
    }
  }

  static clearTokens(): void {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      
      // Clear any scheduled expiration checks
      this.clearTokenExpiration()
      
    } catch (error) {
      console.error('Error clearing tokens:', error)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    
    return !!(accessToken || refreshToken)
  }

  // =====================================================================================
  // Token Validation
  // =====================================================================================

  static isTokenExpired(token: string): boolean {
    try {
      // Decode JWT payload
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      
      // Check if token is expired (with 30 second buffer)
      return payload.exp < (currentTime + 30)
    } catch (error) {
      console.error('Error checking token expiration:', error)
      return true // Assume expired if we can't parse
    }
  }

  static getTokenExpirationTime(token: string): Date | null {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return new Date(payload.exp * 1000)
    } catch (error) {
      console.error('Error getting token expiration time:', error)
      return null
    }
  }

  static getTokenPayload(token: string): any | null {
    try {
      return JSON.parse(atob(token.split('.')[1]))
    } catch (error) {
      console.error('Error parsing token payload:', error)
      return null
    }
  }

  // =====================================================================================
  // User Data Management
  // =====================================================================================

  static setUserData(user: any): void {
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } catch (error) {
      console.error('Error storing user data:', error)
    }
  }

  static getUserData(): any | null {
    try {
      const userData = localStorage.getItem(USER_KEY)
      return userData ? JSON.parse(userData) : null
    } catch (error) {
      console.error('Error retrieving user data:', error)
      return null
    }
  }

  static clearUserData(): void {
    try {
      localStorage.removeItem(USER_KEY)
    } catch (error) {
      console.error('Error clearing user data:', error)
    }
  }

  // =====================================================================================
  // Token Expiration Management
  // =====================================================================================

  private static expirationTimer: number | null = null

  private static scheduleTokenExpiration(token: string): void {
    // Clear any existing timer
    this.clearTokenExpiration()
    
    try {
      const expirationTime = this.getTokenExpirationTime(token)
      if (!expirationTime) return
      
      const currentTime = new Date()
      const timeUntilExpiry = expirationTime.getTime() - currentTime.getTime()
      
      // Schedule cleanup 1 minute before expiration
      const cleanupTime = Math.max(timeUntilExpiry - 60000, 1000)
      
      this.expirationTimer = window.setTimeout(() => {
        console.log('Token expired, clearing storage')
        this.clearTokens()
        
        // Optionally dispatch custom event for token expiration
        window.dispatchEvent(new CustomEvent('tokenExpired'))
      }, cleanupTime)
      
    } catch (error) {
      console.error('Error scheduling token expiration:', error)
    }
  }

  private static clearTokenExpiration(): void {
    if (this.expirationTimer) {
      clearTimeout(this.expirationTimer)
      this.expirationTimer = null
    }
  }

  // =====================================================================================
  // Security Utilities
  // =====================================================================================

  static isStorageAvailable(): boolean {
    try {
      const test = '__storage_test__'
      localStorage.setItem(test, test)
      localStorage.removeItem(test)
      return true
    } catch {
      return false
    }
  }

  static getTokenInfo(token: string): { isValid: boolean; expiresAt?: Date; userId?: string; email?: string } {
    try {
      if (this.isTokenExpired(token)) {
        return { isValid: false }
      }
      
      const payload = this.getTokenPayload(token)
      if (!payload) {
        return { isValid: false }
      }
      
      return {
        isValid: true,
        expiresAt: new Date(payload.exp * 1000),
        userId: payload.user_id,
        email: payload.sub
      }
    } catch (error) {
      console.error('Error getting token info:', error)
      return { isValid: false }
    }
  }

  // =====================================================================================
  // Development Utilities
  // =====================================================================================

  static debugTokens(): void {
    if (process.env.NODE_ENV !== 'development') return
    
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    
    console.group('🔐 Token Debug Info')
    
    if (accessToken) {
      const accessInfo = this.getTokenInfo(accessToken)
      console.log('Access Token:', {
        ...accessInfo,
        token: `${accessToken.substring(0, 20)}...`
      })
    } else {
      console.log('Access Token: None')
    }
    
    if (refreshToken) {
      const refreshInfo = this.getTokenInfo(refreshToken)
      console.log('Refresh Token:', {
        ...refreshInfo,
        token: `${refreshToken.substring(0, 20)}...`
      })
    } else {
      console.log('Refresh Token: None')
    }
    
    console.groupEnd()
  }

  // =====================================================================================
  // Migration Utilities (for future token format changes)
  // =====================================================================================

  static migrateTokenStorage(): void {
    // Placeholder for future token storage migrations
    // This would handle upgrades from older token storage formats
    try {
      const version = localStorage.getItem('token_storage_version')
      
      // If no version, this is a new installation
      if (!version) {
        localStorage.setItem('token_storage_version', '1.0.0')
        return
      }
      
      // Handle future migrations here
      // if (version === '1.0.0') {
      //   // Migrate to 1.1.0
      // }
      
    } catch (error) {
      console.error('Token storage migration error:', error)
    }
  }
}

// Initialize migration on load
TokenStorage.migrateTokenStorage()

export default TokenStorage