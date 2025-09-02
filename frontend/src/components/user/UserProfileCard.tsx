import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { UserProfile, UserPreferences, AccountSettings } from '../../types/user';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar,
  Edit3,
  Camera,
  Check,
  Clock
} from 'lucide-react';

interface UserProfileCardProps {
  profile: UserProfile;
  preferences: UserPreferences;
  accountSettings: AccountSettings;
  onEdit?: () => void;
}

const UserProfileCard: React.FC<UserProfileCardProps> = ({
  profile,
  preferences,
  accountSettings,
  onEdit,
}) => {
  const [imageError, setImageError] = useState(false);

  const getInitials = (firstName?: string, lastName?: string, displayName?: string) => {
    if (firstName && lastName) {
      return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
    }
    if (displayName) {
      const names = displayName.split(' ');
      if (names.length >= 2) {
        return `${names[0].charAt(0)}${names[names.length - 1].charAt(0)}`.toUpperCase();
      }
      return displayName.charAt(0).toUpperCase();
    }
    return profile.username.charAt(0).toUpperCase();
  };

  const formatLastLogin = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    if (diffInHours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  return (
    <Card className="p-6">
      <div className="flex items-start space-x-6">
        {/* Avatar Section */}
        <div className="flex-shrink-0 relative">
          <div className="w-20 h-20 rounded-full overflow-hidden bg-slate-200 flex items-center justify-center">
            {profile.avatarUrl && !imageError ? (
              <img
                src={profile.avatarUrl}
                alt={profile.displayName || profile.username}
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full bg-primary-100 flex items-center justify-center text-xl font-semibold text-primary-600">
                {getInitials(profile.firstName, profile.lastName, profile.displayName)}
              </div>
            )}
          </div>
          <button className="absolute -bottom-1 -right-1 p-1.5 bg-white rounded-full shadow-md border border-slate-200 hover:bg-slate-50 transition-colors">
            <Camera className="w-3 h-3 text-slate-600" />
          </button>
        </div>

        {/* Profile Information */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 truncate">
                {profile.displayName || `${profile.firstName} ${profile.lastName}`.trim() || profile.username}
              </h2>
              <p className="text-slate-600">@{profile.username}</p>
            </div>
            
            <div className="flex items-center space-x-3">
              {profile.isEmailVerified ? (
                <Badge variant="success" className="text-xs">
                  <Check className="w-3 h-3 mr-1" />
                  Verified
                </Badge>
              ) : (
                <Badge variant="warning" className="text-xs">
                  <Clock className="w-3 h-3 mr-1" />
                  Unverified
                </Badge>
              )}
              
              <Badge
                variant={profile.isActive ? 'success' : 'secondary'}
                className="text-xs"
              >
                {profile.isActive ? 'Active' : 'Inactive'}
              </Badge>
              
              {onEdit && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onEdit}
                  className="ml-3"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  Edit Profile
                </Button>
              )}
            </div>
          </div>

          {/* Contact Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4 text-slate-500" />
                <span className="text-slate-700">{profile.email}</span>
                {profile.isEmailVerified && (
                  <Check className="w-3 h-3 text-green-500" />
                )}
              </div>
              
              {profile.phoneNumber && (
                <div className="flex items-center space-x-2">
                  <Phone className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-700">{profile.phoneNumber}</span>
                </div>
              )}
              
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-slate-500" />
                <span className="text-slate-700">{profile.timezone}</span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-slate-500" />
                <span className="text-slate-700">
                  Joined {new Date(profile.createdAt).toLocaleDateString()}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-slate-500" />
                <span className="text-slate-700">
                  Last login: {formatLastLogin(profile.lastLoginAt)}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 flex items-center justify-center">
                  {preferences.theme === 'light' ? '☀️' : preferences.theme === 'dark' ? '🌙' : '🔄'}
                </div>
                <span className="text-slate-700 capitalize">
                  {preferences.theme} theme
                </span>
              </div>
            </div>
          </div>

          {/* Account Summary */}
          <div className="mt-4 pt-4 border-t border-slate-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-lg font-semibold text-slate-900">
                  {accountSettings.subscription.planType.charAt(0).toUpperCase() + 
                   accountSettings.subscription.planType.slice(1)}
                </p>
                <p className="text-xs text-slate-600">Plan</p>
              </div>
              
              <div>
                <p className="text-lg font-semibold text-slate-900">
                  {accountSettings.subscription.currentUsage.monthlyAnalyses}
                </p>
                <p className="text-xs text-slate-600">Analyses This Month</p>
              </div>
              
              <div>
                <p className="text-lg font-semibold text-slate-900">
                  {accountSettings.subscription.currentUsage.portfolios}
                </p>
                <p className="text-xs text-slate-600">Active Portfolios</p>
              </div>
              
              <div>
                <p className="text-lg font-semibold text-slate-900">
                  {accountSettings.brokerIntegrations.filter(b => b.isConnected).length}
                </p>
                <p className="text-xs text-slate-600">Connected Brokers</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default UserProfileCard;