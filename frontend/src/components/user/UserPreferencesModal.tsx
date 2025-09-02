import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { userService } from '../../services/userService';
import { UserPreferences, UpdatePreferencesRequest } from '../../types/user';
import { X, Save, RotateCcw } from 'lucide-react';

const preferencesSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']),
  currency: z.enum(['USD', 'EUR', 'GBP', 'CAD']),
  dateFormat: z.enum(['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']),
  timeFormat: z.enum(['12h', '24h']),
  defaultRiskPerTrade: z.number().min(0.001).max(0.1),
  maxPositionSize: z.number().min(0.01).max(1),
  defaultExpirationDTE: z.number().min(1).max(365),
  riskTolerance: z.enum(['conservative', 'moderate', 'aggressive']),
  compactMode: z.boolean(),
  showAdvancedMetrics: z.boolean(),
  enablePaperTrading: z.boolean(),
  autoClosePositions: z.boolean(),
  // Notification preferences
  emailMarketAlerts: z.boolean(),
  emailPortfolioUpdates: z.boolean(),
  emailTradeExecutions: z.boolean(),
  emailSystemUpdates: z.boolean(),
  emailWeeklyReports: z.boolean(),
  browserNotifications: z.boolean(),
  browserMarketAlerts: z.boolean(),
  browserPortfolioUpdates: z.boolean(),
  browserTradeExecutions: z.boolean(),
  // Privacy preferences
  profileVisibility: z.enum(['public', 'private']),
  shareAnalytics: z.boolean(),
  allowCookies: z.boolean(),
  marketingEmails: z.boolean(),
});

type PreferencesFormData = z.infer<typeof preferencesSchema>;

interface UserPreferencesModalProps {
  preferences: UserPreferences;
  onClose: () => void;
}

const UserPreferencesModal: React.FC<UserPreferencesModalProps> = ({
  preferences,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'display' | 'trading' | 'notifications' | 'privacy'>('display');
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
  } = useForm<PreferencesFormData>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      theme: preferences.theme,
      currency: preferences.display.currency,
      dateFormat: preferences.display.dateFormat,
      timeFormat: preferences.display.timeFormat,
      defaultRiskPerTrade: preferences.trading.defaultRiskPerTrade,
      maxPositionSize: preferences.trading.maxPositionSize,
      defaultExpirationDTE: preferences.trading.defaultExpirationDTE,
      riskTolerance: preferences.trading.riskTolerance,
      compactMode: preferences.display.compactMode,
      showAdvancedMetrics: preferences.display.showAdvancedMetrics,
      enablePaperTrading: preferences.trading.enablePaperTrading,
      autoClosePositions: preferences.trading.autoClosePositions,
      emailMarketAlerts: preferences.notifications.email.marketAlerts,
      emailPortfolioUpdates: preferences.notifications.email.portfolioUpdates,
      emailTradeExecutions: preferences.notifications.email.tradeExecutions,
      emailSystemUpdates: preferences.notifications.email.systemUpdates,
      emailWeeklyReports: preferences.notifications.email.weeklyReports,
      browserNotifications: preferences.notifications.browser.enabled,
      browserMarketAlerts: preferences.notifications.browser.marketAlerts,
      browserPortfolioUpdates: preferences.notifications.browser.portfolioUpdates,
      browserTradeExecutions: preferences.notifications.browser.tradeExecutions,
      profileVisibility: preferences.privacy.profileVisibility,
      shareAnalytics: preferences.privacy.shareAnalytics,
      allowCookies: preferences.privacy.allowCookies,
      marketingEmails: preferences.privacy.marketingEmails,
    },
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: (data: UpdatePreferencesRequest) => userService.updatePreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      onClose();
    },
  });

  const resetPreferencesMutation = useMutation({
    mutationFn: () => userService.resetPreferences(),
    onSuccess: (data) => {
      queryClient.setQueryData(['user-profile'], (old: any) => ({
        ...old,
        preferences: data,
      }));
      reset();
      onClose();
    },
  });

  const handleFormSubmit = (data: PreferencesFormData) => {
    const updateData: UpdatePreferencesRequest = {
      theme: data.theme,
      display: {
        currency: data.currency,
        dateFormat: data.dateFormat,
        timeFormat: data.timeFormat,
        compactMode: data.compactMode,
        showAdvancedMetrics: data.showAdvancedMetrics,
        chartTheme: preferences.display.chartTheme, // Keep existing
      },
      trading: {
        defaultRiskPerTrade: data.defaultRiskPerTrade,
        maxPositionSize: data.maxPositionSize,
        defaultExpirationDTE: data.defaultExpirationDTE,
        riskTolerance: data.riskTolerance,
        enablePaperTrading: data.enablePaperTrading,
        autoClosePositions: data.autoClosePositions,
        preferredStrategies: preferences.trading.preferredStrategies, // Keep existing
      },
      notifications: {
        email: {
          marketAlerts: data.emailMarketAlerts,
          portfolioUpdates: data.emailPortfolioUpdates,
          tradeExecutions: data.emailTradeExecutions,
          systemUpdates: data.emailSystemUpdates,
          weeklyReports: data.emailWeeklyReports,
        },
        browser: {
          enabled: data.browserNotifications,
          marketAlerts: data.browserMarketAlerts,
          portfolioUpdates: data.browserPortfolioUpdates,
          tradeExecutions: data.browserTradeExecutions,
        },
      },
      privacy: {
        profileVisibility: data.profileVisibility,
        shareAnalytics: data.shareAnalytics,
        allowCookies: data.allowCookies,
        marketingEmails: data.marketingEmails,
      },
    };

    updatePreferencesMutation.mutate(updateData);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const tabs = [
    { id: 'display', name: 'Display', description: 'Theme and display preferences' },
    { id: 'trading', name: 'Trading', description: 'Default trading settings' },
    { id: 'notifications', name: 'Notifications', description: 'Alert and notification settings' },
    { id: 'privacy', name: 'Privacy', description: 'Privacy and data sharing' },
  ] as const;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold text-slate-900">User Preferences</h2>
            <p className="text-sm text-slate-600">Customize your trading experience</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="p-2"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Tab Navigation */}
          <div className="w-64 border-r border-slate-200 p-6">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700 border border-primary-200'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium">{tab.name}</div>
                  <div className="text-xs text-slate-500 mt-1">{tab.description}</div>
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6">
              {activeTab === 'display' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Display Settings</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Theme
                        </label>
                        <select
                          {...register('theme')}
                          className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="light">Light</option>
                          <option value="dark">Dark</option>
                          <option value="system">System</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Currency
                        </label>
                        <select
                          {...register('currency')}
                          className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="USD">USD ($)</option>
                          <option value="EUR">EUR (€)</option>
                          <option value="GBP">GBP (£)</option>
                          <option value="CAD">CAD (C$)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Date Format
                        </label>
                        <select
                          {...register('dateFormat')}
                          className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                          <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                          <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Time Format
                        </label>
                        <select
                          {...register('timeFormat')}
                          className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="12h">12 Hour (AM/PM)</option>
                          <option value="24h">24 Hour</option>
                        </select>
                      </div>
                    </div>

                    <div className="mt-6 space-y-4">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="compactMode"
                          {...register('compactMode')}
                          className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                        />
                        <label htmlFor="compactMode" className="ml-3 text-sm text-slate-700">
                          Enable compact mode for tables and lists
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="showAdvancedMetrics"
                          {...register('showAdvancedMetrics')}
                          className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                        />
                        <label htmlFor="showAdvancedMetrics" className="ml-3 text-sm text-slate-700">
                          Show advanced trading metrics and Greeks
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trading' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Trading Defaults</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <Input
                          label="Default Risk Per Trade (%)"
                          type="number"
                          step="0.001"
                          min="0.1"
                          max="10"
                          {...register('defaultRiskPerTrade', { valueAsNumber: true })}
                          error={errors.defaultRiskPerTrade?.message}
                          required
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Percentage of account to risk per trade (0.1% - 10%)
                        </p>
                      </div>

                      <div>
                        <Input
                          label="Maximum Position Size (%)"
                          type="number"
                          step="0.01"
                          min="1"
                          max="100"
                          {...register('maxPositionSize', { valueAsNumber: true })}
                          error={errors.maxPositionSize?.message}
                          required
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Maximum percentage of account for single position (1% - 100%)
                        </p>
                      </div>

                      <div>
                        <Input
                          label="Default Expiration (DTE)"
                          type="number"
                          min="1"
                          max="365"
                          {...register('defaultExpirationDTE', { valueAsNumber: true })}
                          error={errors.defaultExpirationDTE?.message}
                          required
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Preferred days to expiration for options trades
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Risk Tolerance
                        </label>
                        <select
                          {...register('riskTolerance')}
                          className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="conservative">Conservative</option>
                          <option value="moderate">Moderate</option>
                          <option value="aggressive">Aggressive</option>
                        </select>
                      </div>
                    </div>

                    <div className="mt-6 space-y-4">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="enablePaperTrading"
                          {...register('enablePaperTrading')}
                          className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                        />
                        <label htmlFor="enablePaperTrading" className="ml-3 text-sm text-slate-700">
                          Enable paper trading mode by default
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="autoClosePositions"
                          {...register('autoClosePositions')}
                          className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                        />
                        <label htmlFor="autoClosePositions" className="ml-3 text-sm text-slate-700">
                          Automatically close positions at 50% profit target
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Email Notifications</h3>
                    <div className="space-y-4">
                      {[
                        { key: 'emailMarketAlerts', label: 'Market alerts and opportunities', description: 'Notifications about market events and trading opportunities' },
                        { key: 'emailPortfolioUpdates', label: 'Portfolio updates', description: 'Daily summaries of your portfolio performance' },
                        { key: 'emailTradeExecutions', label: 'Trade executions', description: 'Confirmations when trades are executed' },
                        { key: 'emailSystemUpdates', label: 'System updates', description: 'Important updates and maintenance notifications' },
                        { key: 'emailWeeklyReports', label: 'Weekly reports', description: 'Comprehensive weekly performance reports' },
                      ].map((item) => (
                        <div key={item.key} className="flex items-start space-x-3">
                          <input
                            type="checkbox"
                            id={item.key}
                            {...register(item.key as keyof PreferencesFormData)}
                            className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2 mt-1"
                          />
                          <div>
                            <label htmlFor={item.key} className="text-sm font-medium text-slate-700">
                              {item.label}
                            </label>
                            <p className="text-xs text-slate-500">{item.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Browser Notifications</h3>
                    <div className="space-y-4">
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          id="browserNotifications"
                          {...register('browserNotifications')}
                          className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2 mt-1"
                        />
                        <div>
                          <label htmlFor="browserNotifications" className="text-sm font-medium text-slate-700">
                            Enable browser notifications
                          </label>
                          <p className="text-xs text-slate-500">Allow push notifications in your browser</p>
                        </div>
                      </div>

                      {watch('browserNotifications') && (
                        <div className="ml-7 space-y-3 border-l-2 border-slate-200 pl-4">
                          {[
                            { key: 'browserMarketAlerts', label: 'Market alerts' },
                            { key: 'browserPortfolioUpdates', label: 'Portfolio updates' },
                            { key: 'browserTradeExecutions', label: 'Trade executions' },
                          ].map((item) => (
                            <div key={item.key} className="flex items-center">
                              <input
                                type="checkbox"
                                id={item.key}
                                {...register(item.key as keyof PreferencesFormData)}
                                className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                              />
                              <label htmlFor={item.key} className="ml-3 text-sm text-slate-700">
                                {item.label}
                              </label>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'privacy' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-slate-900 mb-4">Privacy Settings</h3>
                    
                    <div className="space-y-6">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          Profile Visibility
                        </label>
                        <select
                          {...register('profileVisibility')}
                          className="block w-full max-w-xs px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="public">Public</option>
                          <option value="private">Private</option>
                        </select>
                        <p className="text-xs text-slate-500 mt-1">
                          Control who can see your profile information
                        </p>
                      </div>

                      <div className="space-y-4">
                        {[
                          { key: 'shareAnalytics', label: 'Share anonymous analytics', description: 'Help us improve the platform by sharing anonymous usage data' },
                          { key: 'allowCookies', label: 'Allow cookies', description: 'Enable cookies for enhanced user experience' },
                          { key: 'marketingEmails', label: 'Marketing communications', description: 'Receive updates about new features and promotions' },
                        ].map((item) => (
                          <div key={item.key} className="flex items-start space-x-3">
                            <input
                              type="checkbox"
                              id={item.key}
                              {...register(item.key as keyof PreferencesFormData)}
                              className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2 mt-1"
                            />
                            <div>
                              <label htmlFor={item.key} className="text-sm font-medium text-slate-700">
                                {item.label}
                              </label>
                              <p className="text-xs text-slate-500">{item.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Form Actions */}
              <div className="flex items-center justify-between pt-6 border-t border-slate-200 mt-8">
                <div className="flex items-center space-x-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => resetPreferencesMutation.mutate()}
                    disabled={resetPreferencesMutation.isPending}
                    loading={resetPreferencesMutation.isPending}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset to Defaults
                  </Button>
                  {isDirty && (
                    <Badge variant="warning" className="text-xs">
                      Unsaved changes
                    </Badge>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onClose}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    loading={updatePreferencesMutation.isPending}
                    disabled={updatePreferencesMutation.isPending || !isDirty}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Preferences
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default UserPreferencesModal;