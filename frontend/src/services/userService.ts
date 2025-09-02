// User service for API integration
import { apiClient } from './api';
import {
  UserProfile,
  UserPreferences,
  AccountSettings,
  UserProfileResponse,
  UserStatsResponse,
  UserActivity,
  UserActivityFilter,
  UserActivitySort,
  UpdateProfileRequest,
  UpdatePreferencesRequest,
  UpdateSecurityRequest,
  ConnectBrokerRequest,
  UserMetricsChart,
} from '../types/user';

export class UserService {
  private baseUrl = '/user';

  // Profile Management
  async getUserProfile(): Promise<UserProfileResponse> {
    const response = await apiClient.get(`${this.baseUrl}/profile`);
    return response.data;
  }

  async updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
    const response = await apiClient.put(`${this.baseUrl}/profile`, data);
    return response.data.profile;
  }

  async uploadAvatar(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append('avatar', file);
    
    const response = await apiClient.post(`${this.baseUrl}/profile/avatar`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.profile;
  }

  async deleteAvatar(): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/profile/avatar`);
  }

  // Preferences Management
  async getPreferences(): Promise<UserPreferences> {
    const response = await apiClient.get(`${this.baseUrl}/preferences`);
    return response.data.preferences;
  }

  async updatePreferences(data: UpdatePreferencesRequest): Promise<UserPreferences> {
    const response = await apiClient.put(`${this.baseUrl}/preferences`, data);
    return response.data.preferences;
  }

  async resetPreferences(): Promise<UserPreferences> {
    const response = await apiClient.post(`${this.baseUrl}/preferences/reset`);
    return response.data.preferences;
  }

  // Account Settings
  async getAccountSettings(): Promise<AccountSettings> {
    const response = await apiClient.get(`${this.baseUrl}/account`);
    return response.data.accountSettings;
  }

  async updateSecurity(data: UpdateSecurityRequest): Promise<AccountSettings> {
    const response = await apiClient.put(`${this.baseUrl}/account/security`, data);
    return response.data.accountSettings;
  }

  async enable2FA(): Promise<{ qrCode: string; secret: string; backupCodes: string[] }> {
    const response = await apiClient.post(`${this.baseUrl}/account/2fa/enable`);
    return response.data;
  }

  async verify2FA(token: string, secret: string): Promise<{ backupCodes: string[] }> {
    const response = await apiClient.post(`${this.baseUrl}/account/2fa/verify`, {
      token,
      secret,
    });
    return response.data;
  }

  async disable2FA(password: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/2fa/disable`, { password });
  }

  async generateBackupCodes(): Promise<string[]> {
    const response = await apiClient.post(`${this.baseUrl}/account/backup-codes/generate`);
    return response.data.backupCodes;
  }

  // Broker Integration
  async connectBroker(data: ConnectBrokerRequest) {
    const response = await apiClient.post(`${this.baseUrl}/brokers/connect`, data);
    return response.data;
  }

  async disconnectBroker(brokerId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/brokers/${brokerId}`);
  }

  async syncBrokerData(brokerId: string) {
    const response = await apiClient.post(`${this.baseUrl}/brokers/${brokerId}/sync`);
    return response.data;
  }

  async testBrokerConnection(brokerId: string) {
    const response = await apiClient.post(`${this.baseUrl}/brokers/${brokerId}/test`);
    return response.data;
  }

  // Activity & Analytics
  async getUserStats(timeframe?: '1M' | '3M' | '6M' | '1Y' | 'ALL'): Promise<UserStatsResponse> {
    const params = timeframe ? `?timeframe=${timeframe}` : '';
    const response = await apiClient.get(`${this.baseUrl}/stats${params}`);
    return response.data;
  }

  async getUserActivity(
    filter?: UserActivityFilter,
    sort?: UserActivitySort,
    page = 1,
    limit = 20
  ): Promise<{ activities: UserActivity[]; total: number; page: number; limit: number }> {
    const params = new URLSearchParams();
    
    if (filter) {
      if (filter.dateRange) {
        params.append('startDate', filter.dateRange.start);
        params.append('endDate', filter.dateRange.end);
      }
      if (filter.activityType) {
        filter.activityType.forEach(type => params.append('type', type));
      }
      if (filter.status) {
        filter.status.forEach(status => params.append('status', status));
      }
    }

    if (sort) {
      params.append('sortBy', sort.field);
      params.append('sortOrder', sort.direction);
    }

    params.append('page', page.toString());
    params.append('limit', limit.toString());

    const response = await apiClient.get(`${this.baseUrl}/activity?${params.toString()}`);
    return response.data;
  }

  async getUserMetricsChart(timeframe?: '1M' | '3M' | '6M' | '1Y'): Promise<UserMetricsChart> {
    const params = timeframe ? `?timeframe=${timeframe}` : '';
    const response = await apiClient.get(`${this.baseUrl}/metrics/chart${params}`);
    return response.data;
  }

  // Account Management
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/change-password`, {
      currentPassword,
      newPassword,
    });
  }

  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/reset-password`, { email });
  }

  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/reset-password/confirm`, {
      token,
      newPassword,
    });
  }

  async requestEmailVerification(): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/verify-email`);
  }

  async confirmEmailVerification(token: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/verify-email/confirm`, { token });
  }

  async deactivateAccount(password: string, reason?: string): Promise<void> {
    await apiClient.post(`${this.baseUrl}/account/deactivate`, { password, reason });
  }

  async deleteAccount(password: string, reason?: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/account`, {
      data: { password, reason },
    });
  }

  // Data Export
  async exportUserData(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/export?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Session Management
  async getSessions() {
    const response = await apiClient.get(`${this.baseUrl}/sessions`);
    return response.data.sessions;
  }

  async revokeSession(sessionId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/sessions/${sessionId}`);
  }

  async revokeAllSessions(): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/sessions`);
  }

  // Notification Management
  async getNotifications(unreadOnly = false, limit = 50) {
    const params = new URLSearchParams();
    if (unreadOnly) params.append('unreadOnly', 'true');
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`${this.baseUrl}/notifications?${params.toString()}`);
    return response.data;
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    await apiClient.put(`${this.baseUrl}/notifications/${notificationId}/read`);
  }

  async markAllNotificationsRead(): Promise<void> {
    await apiClient.put(`${this.baseUrl}/notifications/read-all`);
  }

  async deleteNotification(notificationId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/notifications/${notificationId}`);
  }

  // Subscription Management
  async getSubscriptionInfo() {
    const response = await apiClient.get(`${this.baseUrl}/subscription`);
    return response.data.subscription;
  }

  async upgradePlan(planType: string, paymentToken?: string) {
    const response = await apiClient.post(`${this.baseUrl}/subscription/upgrade`, {
      planType,
      paymentToken,
    });
    return response.data;
  }

  async cancelSubscription(reason?: string) {
    await apiClient.post(`${this.baseUrl}/subscription/cancel`, { reason });
  }

  async resumeSubscription() {
    const response = await apiClient.post(`${this.baseUrl}/subscription/resume`);
    return response.data;
  }

  async updatePaymentMethod(paymentToken: string) {
    const response = await apiClient.put(`${this.baseUrl}/subscription/payment-method`, {
      paymentToken,
    });
    return response.data;
  }

  async getInvoices(limit = 10) {
    const response = await apiClient.get(`${this.baseUrl}/subscription/invoices?limit=${limit}`);
    return response.data.invoices;
  }

  async downloadInvoice(invoiceId: string): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/subscription/invoices/${invoiceId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

// Export singleton instance
export const userService = new UserService();