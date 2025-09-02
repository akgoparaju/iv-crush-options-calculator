import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Badge } from '../ui/Badge';
import { userService } from '../../services/userService';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import {
  User,
  Settings,
  Activity,
  BarChart3,
  Shield,
  CreditCard,
  Bell,
  Download,
  Edit3,
  Eye,
  Calendar
} from 'lucide-react';

import UserProfileCard from './UserProfileCard';
import UserPreferencesModal from './UserPreferencesModal';
import SecuritySettingsModal from './SecuritySettingsModal';

interface UserDashboardProps {
  onEditProfile?: () => void;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ onEditProfile }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'security' | 'billing'>('overview');
  const [showPreferences, setShowPreferences] = useState(false);
  const [showSecurity, setShowSecurity] = useState(false);

  // Fetch user profile data
  const {
    data: userProfileData,
    isLoading: profileLoading,
    error: profileError,
  } = useQuery({
    queryKey: ['user-profile'],
    queryFn: userService.getUserProfile,
  });

  // Fetch user statistics
  const {
    data: userStats,
    isLoading: statsLoading,
  } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => userService.getUserStats('1Y'),
  });

  // Fetch user activity
  const {
    data: userActivity,
    isLoading: activityLoading,
  } = useQuery({
    queryKey: ['user-activity'],
    queryFn: () => userService.getUserActivity(undefined, { field: 'timestamp', direction: 'desc' }, 1, 10),
    enabled: activeTab === 'activity',
  });

  const handleExportData = async () => {
    try {
      const data = await userService.exportUserData('json');
      const url = window.URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `user-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  if (profileLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (profileError) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-500 mb-4">❌</div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            Failed to load user profile
          </h3>
          <p className="text-slate-600">
            There was an error loading your profile. Please try again.
          </p>
        </div>
      </Card>
    );
  }

  const { profile, preferences, accountSettings } = userProfileData!;

  const tabs = [
    { id: 'overview', name: 'Overview', icon: User },
    { id: 'activity', name: 'Activity', icon: Activity },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'billing', name: 'Billing', icon: CreditCard },
  ] as const;

  return (
    <div className="space-y-6">
      {/* User Profile Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Account Management</h1>
          <p className="text-slate-600">
            Manage your profile, preferences, and account settings
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={handleExportData}
            className="inline-flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Data
          </Button>
          <Button
            onClick={() => setShowPreferences(true)}
            className="inline-flex items-center"
          >
            <Settings className="w-4 h-4 mr-2" />
            Preferences
          </Button>
        </div>
      </div>

      {/* User Profile Card */}
      <UserProfileCard
        profile={profile}
        preferences={preferences}
        accountSettings={accountSettings}
        onEdit={onEditProfile}
      />

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center ${
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Account Statistics */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Account Statistics</h3>
            {statsLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : userStats ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-600">Total Analyses</p>
                    <p className="font-semibold text-slate-900 text-lg">
                      {userStats.totalAnalyses.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-600">Total Trades</p>
                    <p className="font-semibold text-slate-900 text-lg">
                      {userStats.totalTrades.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-600">Total P&L</p>
                    <p className={`font-semibold text-lg ${
                      userStats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(userStats.totalPnL)}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-600">Win Rate</p>
                    <p className="font-semibold text-slate-900 text-lg">
                      {formatPercentage(userStats.winRate)}
                    </p>
                  </div>
                </div>
                
                {userStats.favoriteStrategies.length > 0 && (
                  <div className="pt-4 border-t border-slate-200">
                    <p className="text-sm font-medium text-slate-900 mb-2">Favorite Strategies</p>
                    <div className="space-y-2">
                      {userStats.favoriteStrategies.slice(0, 3).map((strategy, index) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <span className="text-slate-600">{strategy.strategy}</span>
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline">{strategy.count} trades</Badge>
                            <Badge variant={strategy.winRate > 0.6 ? 'success' : 'secondary'}>
                              {formatPercentage(strategy.winRate)} win
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-600 text-sm">No statistics available</p>
            )}
          </Card>

          {/* Subscription Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Subscription</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 capitalize">
                    {accountSettings.subscription.planType} Plan
                  </p>
                  <p className="text-sm text-slate-600">
                    Status: <Badge 
                      variant={accountSettings.subscription.status === 'active' ? 'success' : 'secondary'}
                    >
                      {accountSettings.subscription.status}
                    </Badge>
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  <Edit3 className="w-4 h-4 mr-1" />
                  Manage
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-slate-600">Analyses</p>
                  <p className="font-medium">
                    {accountSettings.subscription.currentUsage.monthlyAnalyses} / {accountSettings.subscription.usageLimits.monthlyAnalyses}
                  </p>
                </div>
                <div>
                  <p className="text-slate-600">Portfolios</p>
                  <p className="font-medium">
                    {accountSettings.subscription.currentUsage.portfolios} / {accountSettings.subscription.usageLimits.portfolios}
                  </p>
                </div>
                <div>
                  <p className="text-slate-600">Alerts</p>
                  <p className="font-medium">
                    {accountSettings.subscription.currentUsage.alerts} / {accountSettings.subscription.usageLimits.alerts}
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-600">
                    {accountSettings.subscription.endDate ? 'Renews on' : 'Started on'}
                  </span>
                  <span className="font-medium">
                    {new Date(accountSettings.subscription.endDate || accountSettings.subscription.startDate).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Settings */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Settings</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-slate-500" />
                  <span className="text-sm text-slate-700">Email Notifications</span>
                </div>
                <Badge variant={preferences.notifications.email.marketAlerts ? 'success' : 'secondary'}>
                  {preferences.notifications.email.marketAlerts ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-slate-500" />
                  <span className="text-sm text-slate-700">Two-Factor Auth</span>
                </div>
                <Badge variant={accountSettings.securitySettings.twoFactorEnabled ? 'success' : 'warning'}>
                  {accountSettings.securitySettings.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Eye className="w-4 h-4 text-slate-500" />
                  <span className="text-sm text-slate-700">Theme</span>
                </div>
                <Badge variant="outline" className="capitalize">
                  {preferences.theme}
                </Badge>
              </div>

              <div className="pt-3 border-t border-slate-200">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSecurity(true)}
                  className="w-full"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Security Settings
                </Button>
              </div>
            </div>
          </Card>

          {/* Connected Brokers */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Connected Brokers</h3>
            {accountSettings.brokerIntegrations.length > 0 ? (
              <div className="space-y-3">
                {accountSettings.brokerIntegrations.map((broker) => (
                  <div key={broker.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{broker.brokerName}</p>
                      <p className="text-sm text-slate-600">
                        Account: {broker.accountId}
                      </p>
                      {broker.lastSyncAt && (
                        <p className="text-xs text-slate-500">
                          Last sync: {new Date(broker.lastSyncAt).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <Badge
                      variant={
                        broker.status === 'connected' ? 'success' :
                        broker.status === 'error' ? 'destructive' : 'secondary'
                      }
                    >
                      {broker.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-slate-600 text-sm mb-3">No brokers connected</p>
                <Button variant="outline" size="sm">
                  Connect Broker
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'activity' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
          {activityLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : userActivity && userActivity.activities.length > 0 ? (
            <div className="space-y-4">
              {userActivity.activities.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3 pb-4 border-b border-slate-100 last:border-b-0">
                  <div className="flex-shrink-0 mt-1">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.status === 'success' ? 'bg-green-500' :
                      activity.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-900">{activity.description}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <p className="text-xs text-slate-500">
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {activity.type}
                      </Badge>
                      {activity.status !== 'success' && (
                        <Badge
                          variant={activity.status === 'failed' ? 'destructive' : 'warning'}
                          className="text-xs"
                        >
                          {activity.status}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {userActivity.total > userActivity.activities.length && (
                <div className="text-center pt-4">
                  <Button variant="outline" size="sm">
                    View All Activity ({userActivity.total} total)
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-600 text-sm">No recent activity</p>
          )}
        </Card>
      )}

      {activeTab === 'security' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Security Overview</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">Two-Factor Authentication</span>
                <Badge variant={accountSettings.securitySettings.twoFactorEnabled ? 'success' : 'warning'}>
                  {accountSettings.securitySettings.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">Login Notifications</span>
                <Badge variant={accountSettings.securitySettings.loginNotifications ? 'success' : 'secondary'}>
                  {accountSettings.securitySettings.loginNotifications ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">Session Timeout</span>
                <Badge variant="outline">
                  {accountSettings.securitySettings.sessionTimeout} minutes
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-700">Password Changed</span>
                <span className="text-sm text-slate-600">
                  {new Date(accountSettings.securitySettings.passwordLastChanged).toLocaleDateString()}
                </span>
              </div>

              <div className="pt-4 border-t border-slate-200">
                <Button
                  variant="outline"
                  onClick={() => setShowSecurity(true)}
                  className="w-full"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Security Settings
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Current Plan</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 capitalize">
                    {accountSettings.subscription.planType} Plan
                  </p>
                  <p className="text-sm text-slate-600">
                    {accountSettings.subscription.endDate
                      ? `Renews ${new Date(accountSettings.subscription.endDate).toLocaleDateString()}`
                      : `Started ${new Date(accountSettings.subscription.startDate).toLocaleDateString()}`
                    }
                  </p>
                </div>
                <Badge variant={accountSettings.subscription.status === 'active' ? 'success' : 'secondary'}>
                  {accountSettings.subscription.status}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-slate-900">Features</h4>
                {accountSettings.subscription.features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                    <span className="text-sm text-slate-600">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-200">
                <div className="grid grid-cols-2 gap-4">
                  <Button variant="outline" size="sm">
                    Change Plan
                  </Button>
                  <Button variant="outline" size="sm">
                    Cancel Plan
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Payment Method</h3>
            {accountSettings.billingInfo.paymentMethod ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">
                      {accountSettings.billingInfo.paymentMethod.type.toUpperCase()} 
                      {accountSettings.billingInfo.paymentMethod.last4 && 
                        ` ****${accountSettings.billingInfo.paymentMethod.last4}`
                      }
                    </p>
                    {accountSettings.billingInfo.paymentMethod.expiryMonth && 
                     accountSettings.billingInfo.paymentMethod.expiryYear && (
                      <p className="text-sm text-slate-600">
                        Expires {accountSettings.billingInfo.paymentMethod.expiryMonth}/{accountSettings.billingInfo.paymentMethod.expiryYear}
                      </p>
                    )}
                  </div>
                  <CreditCard className="w-5 h-5 text-slate-400" />
                </div>
                <Button variant="outline" size="sm">
                  Update Payment Method
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-slate-600 text-sm mb-3">No payment method on file</p>
                <Button variant="outline" size="sm">
                  Add Payment Method
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Modals */}
      {showPreferences && (
        <UserPreferencesModal
          preferences={preferences}
          onClose={() => setShowPreferences(false)}
        />
      )}

      {showSecurity && (
        <SecuritySettingsModal
          securitySettings={accountSettings.securitySettings}
          onClose={() => setShowSecurity(false)}
        />
      )}
    </div>
  );
};

export default UserDashboard;