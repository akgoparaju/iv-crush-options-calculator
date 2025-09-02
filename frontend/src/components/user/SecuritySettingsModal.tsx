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
import { SecuritySettings, UpdateSecurityRequest } from '../../types/user';
import { X, Save, Shield, Key, Smartphone, AlertTriangle, Copy, Check } from 'lucide-react';

const securitySchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().optional(),
  confirmPassword: z.string().optional(),
  sessionTimeout: z.number().min(5).max(480),
  loginNotifications: z.boolean(),
}).refine((data) => {
  if (data.newPassword && data.newPassword !== data.confirmPassword) {
    return false;
  }
  return true;
}, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type SecurityFormData = z.infer<typeof securitySchema>;

interface SecuritySettingsModalProps {
  securitySettings: SecuritySettings;
  onClose: () => void;
}

const SecuritySettingsModal: React.FC<SecuritySettingsModalProps> = ({
  securitySettings,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'password' | '2fa' | 'sessions'>('password');
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [twoFactorToken, setTwoFactorToken] = useState('');
  const [copiedCode, setCopiedCode] = useState<string>('');

  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
  } = useForm<SecurityFormData>({
    resolver: zodResolver(securitySchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      sessionTimeout: securitySettings.sessionTimeout,
      loginNotifications: securitySettings.loginNotifications,
    },
  });

  const updateSecurityMutation = useMutation({
    mutationFn: (data: UpdateSecurityRequest) => userService.updateSecurity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      reset();
    },
  });

  const enable2FAMutation = useMutation({
    mutationFn: () => userService.enable2FA(),
    onSuccess: (data) => {
      setQrCode(data.qrCode);
      setSecret(data.secret);
      setShow2FASetup(true);
    },
  });

  const verify2FAMutation = useMutation({
    mutationFn: (token: string) => userService.verify2FA(token, secret),
    onSuccess: (data) => {
      setBackupCodes(data.backupCodes);
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      setShow2FASetup(false);
    },
  });

  const disable2FAMutation = useMutation({
    mutationFn: (password: string) => userService.disable2FA(password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    },
  });

  const generateBackupCodesMutation = useMutation({
    mutationFn: () => userService.generateBackupCodes(),
    onSuccess: (codes) => {
      setBackupCodes(codes);
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    },
  });

  const handleFormSubmit = (data: SecurityFormData) => {
    const updateData: UpdateSecurityRequest = {
      currentPassword: data.currentPassword,
      sessionTimeout: data.sessionTimeout,
      loginNotifications: data.loginNotifications,
    };

    if (data.newPassword && data.newPassword.length > 0) {
      updateData.newPassword = data.newPassword;
    }

    updateSecurityMutation.mutate(updateData);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(id);
      setTimeout(() => setCopiedCode(''), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const tabs = [
    { id: 'password', name: 'Password & Settings', icon: Key },
    { id: '2fa', name: 'Two-Factor Auth', icon: Smartphone },
    { id: 'sessions', name: 'Active Sessions', icon: Shield },
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
            <h2 className="text-xl font-bold text-slate-900">Security Settings</h2>
            <p className="text-sm text-slate-600">Manage your account security and authentication</p>
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
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors flex items-center space-x-3 ${
                      activeTab === tab.id
                        ? 'bg-primary-50 text-primary-700 border border-primary-200'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'password' && (
              <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Password & Security Settings</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <Input
                        label="Current Password"
                        type="password"
                        {...register('currentPassword')}
                        error={errors.currentPassword?.message}
                        required
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Input
                          label="New Password (optional)"
                          type="password"
                          {...register('newPassword')}
                          error={errors.newPassword?.message}
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Leave blank to keep current password
                        </p>
                      </div>

                      <div>
                        <Input
                          label="Confirm New Password"
                          type="password"
                          {...register('confirmPassword')}
                          error={errors.confirmPassword?.message}
                          disabled={!watch('newPassword')}
                        />
                      </div>
                    </div>

                    <div>
                      <Input
                        label="Session Timeout (minutes)"
                        type="number"
                        min="5"
                        max="480"
                        {...register('sessionTimeout', { valueAsNumber: true })}
                        error={errors.sessionTimeout?.message}
                        required
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        Sessions will expire after this many minutes of inactivity (5-480 minutes)
                      </p>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="loginNotifications"
                        {...register('loginNotifications')}
                        className="w-4 h-4 text-primary-600 bg-white border-slate-300 rounded focus:ring-primary-500 focus:ring-2"
                      />
                      <label htmlFor="loginNotifications" className="ml-3 text-sm text-slate-700">
                        Notify me of new login attempts
                      </label>
                    </div>
                  </div>

                  <div className="flex justify-end pt-4 border-t border-slate-200 mt-6">
                    <Button
                      type="submit"
                      loading={updateSecurityMutation.isPending}
                      disabled={updateSecurityMutation.isPending || !isDirty}
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Update Security Settings
                    </Button>
                  </div>
                </div>
              </form>
            )}

            {activeTab === '2fa' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Two-Factor Authentication</h3>
                  
                  {!securitySettings.twoFactorEnabled ? (
                    <div className="space-y-4">
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                          <div>
                            <h4 className="font-medium text-yellow-800">Two-Factor Authentication is disabled</h4>
                            <p className="text-sm text-yellow-700 mt-1">
                              Enable 2FA to add an extra layer of security to your account. You'll need an authenticator app like Google Authenticator or Authy.
                            </p>
                          </div>
                        </div>
                      </div>

                      {!show2FASetup ? (
                        <Button
                          onClick={() => enable2FAMutation.mutate()}
                          loading={enable2FAMutation.isPending}
                          className="inline-flex items-center"
                        >
                          <Shield className="w-4 h-4 mr-2" />
                          Enable Two-Factor Authentication
                        </Button>
                      ) : (
                        <Card className="p-6">
                          <h4 className="font-medium text-slate-900 mb-4">Set up Two-Factor Authentication</h4>
                          
                          <div className="space-y-4">
                            <div>
                              <p className="text-sm text-slate-600 mb-3">
                                1. Scan this QR code with your authenticator app:
                              </p>
                              {qrCode && (
                                <div className="bg-white p-4 border border-slate-200 rounded-lg inline-block">
                                  <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
                                </div>
                              )}
                            </div>

                            <div>
                              <p className="text-sm text-slate-600 mb-2">
                                2. Or manually enter this secret key:
                              </p>
                              <div className="bg-slate-50 p-3 rounded border font-mono text-sm break-all">
                                {secret}
                              </div>
                            </div>

                            <div>
                              <p className="text-sm text-slate-600 mb-2">
                                3. Enter the 6-digit code from your authenticator app:
                              </p>
                              <div className="flex items-center space-x-3">
                                <Input
                                  type="text"
                                  placeholder="000000"
                                  value={twoFactorToken}
                                  onChange={(e) => setTwoFactorToken(e.target.value)}
                                  className="max-w-xs"
                                  maxLength={6}
                                />
                                <Button
                                  onClick={() => verify2FAMutation.mutate(twoFactorToken)}
                                  loading={verify2FAMutation.isPending}
                                  disabled={twoFactorToken.length !== 6}
                                >
                                  Verify & Enable
                                </Button>
                              </div>
                            </div>
                          </div>
                        </Card>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <Shield className="w-5 h-5 text-green-600 mt-0.5" />
                          <div>
                            <h4 className="font-medium text-green-800">Two-Factor Authentication is enabled</h4>
                            <p className="text-sm text-green-700 mt-1">
                              Your account is protected with an additional layer of security.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Button
                          onClick={() => generateBackupCodesMutation.mutate()}
                          loading={generateBackupCodesMutation.isPending}
                          variant="outline"
                        >
                          Generate New Backup Codes
                        </Button>

                        <Button
                          onClick={() => {
                            const password = prompt('Enter your current password to disable 2FA:');
                            if (password) {
                              disable2FAMutation.mutate(password);
                            }
                          }}
                          loading={disable2FAMutation.isPending}
                          variant="outline"
                          className="text-red-600 border-red-300 hover:bg-red-50"
                        >
                          Disable Two-Factor Authentication
                        </Button>
                      </div>
                    </div>
                  )}

                  {backupCodes.length > 0 && (
                    <Card className="p-6 bg-slate-50">
                      <h4 className="font-medium text-slate-900 mb-4">Backup Codes</h4>
                      <p className="text-sm text-slate-600 mb-4">
                        Save these backup codes in a safe place. Each code can only be used once to access your account if you lose access to your authenticator.
                      </p>
                      <div className="grid grid-cols-2 gap-2">
                        {backupCodes.map((code, index) => (
                          <div key={index} className="flex items-center justify-between bg-white p-2 rounded border">
                            <span className="font-mono text-sm">{code}</span>
                            <button
                              onClick={() => copyToClipboard(code, `backup-${index}`)}
                              className="ml-2 p-1 text-slate-400 hover:text-slate-600"
                            >
                              {copiedCode === `backup-${index}` ? (
                                <Check className="w-4 h-4 text-green-500" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-sm text-yellow-800">
                          ⚠️ Keep these codes secure and private. Anyone with access to these codes can access your account.
                        </p>
                      </div>
                    </Card>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'sessions' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Active Sessions</h3>
                  
                  <div className="bg-slate-50 p-4 rounded-lg text-center">
                    <Shield className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                    <h4 className="font-medium text-slate-900 mb-2">Session Management</h4>
                    <p className="text-sm text-slate-600 mb-4">
                      View and manage your active sessions across different devices and browsers.
                    </p>
                    <p className="text-xs text-slate-500">
                      This feature will be available in a future update.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SecuritySettingsModal;