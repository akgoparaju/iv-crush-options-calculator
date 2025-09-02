import React from 'react'
import { clsx } from 'clsx'
import { CheckCircle, XCircle, AlertTriangle, Info, Clock } from 'lucide-react'

interface StatusIndicatorProps {
  status: 'success' | 'error' | 'warning' | 'info' | 'pending'
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  children: React.ReactNode
  className?: string
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = 'md',
  showIcon = true,
  children,
  className
}) => {
  const statusConfig = {
    success: {
      bgColor: 'bg-success-100',
      textColor: 'text-success-800',
      iconColor: 'text-success-600',
      icon: CheckCircle
    },
    error: {
      bgColor: 'bg-danger-100',
      textColor: 'text-danger-800',
      iconColor: 'text-danger-600',
      icon: XCircle
    },
    warning: {
      bgColor: 'bg-warning-100',
      textColor: 'text-warning-800',
      iconColor: 'text-warning-600',
      icon: AlertTriangle
    },
    info: {
      bgColor: 'bg-primary-100',
      textColor: 'text-primary-800',
      iconColor: 'text-primary-600',
      icon: Info
    },
    pending: {
      bgColor: 'bg-slate-100',
      textColor: 'text-slate-800',
      iconColor: 'text-slate-600',
      icon: Clock
    }
  }
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base'
  }
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }
  
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <span className={clsx(
      "inline-flex items-center rounded-full font-medium",
      config.bgColor,
      config.textColor,
      sizeClasses[size],
      className
    )}>
      {showIcon && (
        <Icon className={clsx(iconSizes[size], config.iconColor, "mr-1")} />
      )}
      {children}
    </span>
  )
}

// Predefined status indicators for common use cases
export const SuccessIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="success" {...props} />
)

export const ErrorIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="error" {...props} />
)

export const WarningIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="warning" {...props} />
)

export const InfoIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="info" {...props} />
)

export const PendingIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator status="pending" {...props} />
)

export { StatusIndicator }