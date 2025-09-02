// User management type definitions for the Advanced Options Trading Calculator

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  avatarUrl?: string;
  phoneNumber?: string;
  timezone: string;
  createdAt: string;
  updatedAt: string;
  isEmailVerified: boolean;
  isActive: boolean;
  lastLoginAt?: string;
}

export interface UserPreferences {
  id: string;
  userId: string;
  theme: 'light' | 'dark' | 'system';
  notifications: NotificationSettings;
  trading: TradingPreferences;
  display: DisplayPreferences;
  privacy: PrivacySettings;
  updatedAt: string;
}

export interface NotificationSettings {
  email: {
    marketAlerts: boolean;
    portfolioUpdates: boolean;
    tradeExecutions: boolean;
    systemUpdates: boolean;
    weeklyReports: boolean;
  };
  browser: {
    enabled: boolean;
    marketAlerts: boolean;
    portfolioUpdates: boolean;
    tradeExecutions: boolean;
  };
}

export interface TradingPreferences {
  defaultRiskPerTrade: number;
  maxPositionSize: number;
  preferredStrategies: string[];
  autoClosePositions: boolean;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  defaultExpirationDTE: number;
  enablePaperTrading: boolean;
}

export interface DisplayPreferences {
  currency: 'USD' | 'EUR' | 'GBP' | 'CAD';
  dateFormat: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';
  timeFormat: '12h' | '24h';
  compactMode: boolean;
  showAdvancedMetrics: boolean;
  chartTheme: 'light' | 'dark';
}

export interface PrivacySettings {
  profileVisibility: 'public' | 'private';
  shareAnalytics: boolean;
  allowCookies: boolean;
  marketingEmails: boolean;
}

export interface AccountSettings {
  id: string;
  userId: string;
  brokerIntegrations: BrokerIntegration[];
  subscription: SubscriptionInfo;
  billingInfo: BillingInfo;
  securitySettings: SecuritySettings;
  updatedAt: string;
}

export interface BrokerIntegration {
  id: string;
  brokerName: string;
  accountId: string;
  isConnected: boolean;
  lastSyncAt?: string;
  permissions: string[];
  status: 'connected' | 'disconnected' | 'error' | 'pending';
}

export interface SubscriptionInfo {
  planType: 'free' | 'premium' | 'professional' | 'enterprise';
  status: 'active' | 'expired' | 'cancelled' | 'pending';
  startDate: string;
  endDate?: string;
  features: string[];
  usageLimits: {
    monthlyAnalyses: number;
    portfolios: number;
    alerts: number;
  };
  currentUsage: {
    monthlyAnalyses: number;
    portfolios: number;
    alerts: number;
  };
}

export interface BillingInfo {
  paymentMethod?: {
    type: 'card' | 'paypal' | 'bank';
    last4?: string;
    expiryMonth?: number;
    expiryYear?: number;
  };
  billingAddress?: {
    street: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  invoices: Invoice[];
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  issuedAt: string;
  dueAt: string;
  paidAt?: string;
}

export interface SecuritySettings {
  twoFactorEnabled: boolean;
  sessionTimeout: number; // minutes
  allowedIPs?: string[];
  loginNotifications: boolean;
  passwordLastChanged: string;
  backupCodes?: string[];
}

// Form Types
export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  displayName?: string;
  phoneNumber?: string;
  timezone?: string;
}

export interface UpdatePreferencesRequest {
  theme?: 'light' | 'dark' | 'system';
  notifications?: Partial<NotificationSettings>;
  trading?: Partial<TradingPreferences>;
  display?: Partial<DisplayPreferences>;
  privacy?: Partial<PrivacySettings>;
}

export interface UpdateSecurityRequest {
  currentPassword: string;
  newPassword?: string;
  twoFactorEnabled?: boolean;
  sessionTimeout?: number;
  loginNotifications?: boolean;
}

export interface ConnectBrokerRequest {
  brokerName: string;
  credentials: {
    apiKey?: string;
    apiSecret?: string;
    accountId?: string;
    [key: string]: any;
  };
  permissions: string[];
}

// API Response Types
export interface UserProfileResponse {
  profile: UserProfile;
  preferences: UserPreferences;
  accountSettings: AccountSettings;
}

export interface UserStatsResponse {
  totalAnalyses: number;
  totalTrades: number;
  totalPnL: number;
  winRate: number;
  avgHoldingPeriod: number;
  favoriteStrategies: Array<{
    strategy: string;
    count: number;
    winRate: number;
  }>;
  monthlyStats: Array<{
    month: string;
    analyses: number;
    trades: number;
    pnl: number;
  }>;
}

// Filter and Sort Types
export interface UserActivityFilter {
  dateRange?: {
    start: string;
    end: string;
  };
  activityType?: string[];
  status?: string[];
}

export interface UserActivitySort {
  field: 'timestamp' | 'type' | 'status';
  direction: 'asc' | 'desc';
}

export interface UserActivity {
  id: string;
  type: 'login' | 'analysis' | 'trade' | 'portfolio_update' | 'settings_change';
  description: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
  status: 'success' | 'failed' | 'pending';
  metadata?: Record<string, any>;
}

// Chart Data Types
export interface UserMetricsChart {
  timeline: Array<{
    date: string;
    analyses: number;
    trades: number;
    pnl: number;
  }>;
  summary: {
    totalAnalyses: number;
    totalTrades: number;
    totalPnL: number;
    bestMonth: string;
    worstMonth: string;
  };
}