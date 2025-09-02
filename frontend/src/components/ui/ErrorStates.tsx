import React from 'react'
import { 
  AlertCircle, 
  AlertTriangle, 
  WifiOff, 
  Server, 
  RefreshCw, 
  ArrowLeft,
  Bug,
  Clock,
  Shield,
  Zap
} from 'lucide-react'
import { Button } from './Button'
import { Card } from './Card'

interface ErrorStateProps {
  title: string
  message: string
  type?: 'error' | 'warning' | 'network' | 'server' | 'timeout' | 'validation' | 'security'
  actionLabel?: string
  onAction?: () => void
  secondaryActionLabel?: string
  onSecondaryAction?: () => void
  className?: string
  compact?: boolean
}

const ERROR_ICONS = {
  error: <AlertCircle className="h-8 w-8 text-danger-600" />,
  warning: <AlertTriangle className="h-8 w-8 text-warning-600" />,
  network: <WifiOff className="h-8 w-8 text-slate-600" />,
  server: <Server className="h-8 w-8 text-danger-600" />,
  timeout: <Clock className="h-8 w-8 text-warning-600" />,
  validation: <Bug className="h-8 w-8 text-warning-600" />,
  security: <Shield className="h-8 w-8 text-danger-600" />
}

const ERROR_COLORS = {
  error: 'bg-danger-50 border-danger-200',
  warning: 'bg-warning-50 border-warning-200',
  network: 'bg-slate-50 border-slate-200',
  server: 'bg-danger-50 border-danger-200',
  timeout: 'bg-warning-50 border-warning-200',
  validation: 'bg-warning-50 border-warning-200',
  security: 'bg-danger-50 border-danger-200'
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  type = 'error',
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className = '',
  compact = false
}) => {
  const containerClass = compact 
    ? "p-4 rounded-lg border-2" 
    : "min-h-[300px] flex items-center justify-center p-6"
  
  const cardClass = compact 
    ? "" 
    : "max-w-md w-full p-8 text-center"

  return (
    <div className={`${containerClass} ${ERROR_COLORS[type]} ${className}`}>
      <Card className={cardClass}>
        <div className={compact ? 'flex items-start space-x-3' : 'text-center'}>
          <div className={compact ? 'flex-shrink-0 mt-0.5' : 'mx-auto flex items-center justify-center mb-4'}>
            {ERROR_ICONS[type]}
          </div>
          
          <div className={compact ? 'flex-1 min-w-0' : ''}>
            <h3 className={`font-semibold text-slate-900 ${compact ? 'text-base mb-1' : 'text-lg mb-2'}`}>
              {title}
            </h3>
            
            <p className={`text-slate-600 ${compact ? 'text-sm' : 'text-sm mb-6'}`}>
              {message}
            </p>

            {(actionLabel || secondaryActionLabel) && (
              <div className={`flex gap-3 ${compact ? 'mt-3 justify-end' : 'justify-center'}`}>
                {secondaryActionLabel && onSecondaryAction && (
                  <Button
                    onClick={onSecondaryAction}
                    variant="outline"
                    size={compact ? 'sm' : 'md'}
                  >
                    {secondaryActionLabel}
                  </Button>
                )}
                
                {actionLabel && onAction && (
                  <Button
                    onClick={onAction}
                    variant="primary"
                    size={compact ? 'sm' : 'md'}
                  >
                    {actionLabel}
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}

// Specific error components for common scenarios
export const NetworkError: React.FC<{
  onRetry?: () => void
  onGoOffline?: () => void
  compact?: boolean
}> = ({ onRetry, onGoOffline, compact = false }) => (
  <ErrorState
    type="network"
    title="Connection Lost"
    message="Unable to connect to the server. Please check your internet connection and try again."
    actionLabel="Retry"
    onAction={onRetry}
    secondaryActionLabel={onGoOffline ? "Work Offline" : undefined}
    onSecondaryAction={onGoOffline}
    compact={compact}
  />
)

export const ServerError: React.FC<{
  onRetry?: () => void
  onReportIssue?: () => void
  compact?: boolean
  errorCode?: string
}> = ({ onRetry, onReportIssue, compact = false, errorCode }) => (
  <ErrorState
    type="server"
    title="Server Error"
    message={`Something went wrong on our end. ${errorCode ? `Error ${errorCode}` : 'Our team has been notified.'}`}
    actionLabel="Try Again"
    onAction={onRetry}
    secondaryActionLabel={onReportIssue ? "Report Issue" : undefined}
    onSecondaryAction={onReportIssue}
    compact={compact}
  />
)

export const ValidationError: React.FC<{
  title?: string
  message: string
  onFix?: () => void
  compact?: boolean
}> = ({ title = "Invalid Data", message, onFix, compact = false }) => (
  <ErrorState
    type="validation"
    title={title}
    message={message}
    actionLabel={onFix ? "Fix Issues" : undefined}
    onAction={onFix}
    compact={compact}
  />
)

export const TimeoutError: React.FC<{
  onRetry?: () => void
  onCancel?: () => void
  compact?: boolean
}> = ({ onRetry, onCancel, compact = false }) => (
  <ErrorState
    type="timeout"
    title="Request Timeout"
    message="The operation is taking longer than expected. You can wait or try again later."
    actionLabel="Retry"
    onAction={onRetry}
    secondaryActionLabel={onCancel ? "Cancel" : undefined}
    onSecondaryAction={onCancel}
    compact={compact}
  />
)

export const SecurityError: React.FC<{
  onLogin?: () => void
  onGoBack?: () => void
  compact?: boolean
}> = ({ onLogin, onGoBack, compact = false }) => (
  <ErrorState
    type="security"
    title="Access Denied"
    message="You don't have permission to access this resource. Please check your credentials."
    actionLabel={onLogin ? "Login" : undefined}
    onAction={onLogin}
    secondaryActionLabel={onGoBack ? "Go Back" : undefined}
    onSecondaryAction={onGoBack}
    compact={compact}
  />
)

// Loading state with timeout handling
interface LoadingWithTimeoutProps {
  message?: string
  timeout?: number
  onTimeout?: () => void
  children?: React.ReactNode
}

export const LoadingWithTimeout: React.FC<LoadingWithTimeoutProps> = ({
  message = "Loading...",
  timeout = 30000, // 30 seconds default
  onTimeout,
  children
}) => {
  const [hasTimedOut, setHasTimedOut] = React.useState(false)

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setHasTimedOut(true)
      onTimeout?.()
    }, timeout)

    return () => clearTimeout(timer)
  }, [timeout, onTimeout])

  if (hasTimedOut) {
    return (
      <TimeoutError
        onRetry={() => {
          setHasTimedOut(false)
          // Reset timeout timer
        }}
      />
    )
  }

  return children || (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center space-y-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="text-sm text-slate-600">{message}</p>
      </div>
    </div>
  )
}

// Retry wrapper for automatic retry logic
interface RetryWrapperProps {
  maxRetries?: number
  retryDelay?: number
  onRetry: () => Promise<void>
  children: (retry: () => void, retryCount: number, isRetrying: boolean) => React.ReactNode
}

export const RetryWrapper: React.FC<RetryWrapperProps> = ({
  maxRetries = 3,
  retryDelay = 1000,
  onRetry,
  children
}) => {
  const [retryCount, setRetryCount] = React.useState(0)
  const [isRetrying, setIsRetrying] = React.useState(false)

  const handleRetry = async () => {
    if (retryCount >= maxRetries || isRetrying) return

    setIsRetrying(true)
    
    try {
      await new Promise(resolve => setTimeout(resolve, retryDelay))
      await onRetry()
    } catch (error) {
      setRetryCount(prev => prev + 1)
    } finally {
      setIsRetrying(false)
    }
  }

  return (
    <>
      {children(handleRetry, retryCount, isRetrying)}
    </>
  )
}

export default ErrorState