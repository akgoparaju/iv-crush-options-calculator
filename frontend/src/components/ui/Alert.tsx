import React from 'react'
import { AlertTriangle, CheckCircle, Info, X, XCircle } from 'lucide-react'
import { clsx } from 'clsx'

interface AlertProps {
  children: React.ReactNode
  variant?: 'info' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md' | 'lg'
  dismissible?: boolean
  onDismiss?: () => void
  icon?: boolean
  title?: string
  className?: string
}

export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  size = 'md',
  dismissible = false,
  onDismiss,
  icon = true,
  title,
  className,
  ...props
}) => {
  const variantStyles = {
    info: {
      container: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: 'text-blue-500',
      title: 'text-blue-800',
      IconComponent: Info
    },
    success: {
      container: 'bg-green-50 border-green-200 text-green-800',
      icon: 'text-green-500',
      title: 'text-green-800',
      IconComponent: CheckCircle
    },
    warning: {
      container: 'bg-amber-50 border-amber-200 text-amber-800',
      icon: 'text-amber-500',
      title: 'text-amber-800',
      IconComponent: AlertTriangle
    },
    error: {
      container: 'bg-red-50 border-red-200 text-red-800',
      icon: 'text-red-500',
      title: 'text-red-800',
      IconComponent: XCircle
    }
  }

  const sizeStyles = {
    sm: {
      container: 'p-2 text-sm',
      icon: 'w-4 h-4',
      dismissButton: 'w-4 h-4'
    },
    md: {
      container: 'p-3 text-sm',
      icon: 'w-5 h-5',
      dismissButton: 'w-5 h-5'
    },
    lg: {
      container: 'p-4 text-base',
      icon: 'w-6 h-6',
      dismissButton: 'w-6 h-6'
    }
  }

  const currentVariant = variantStyles[variant]
  const currentSize = sizeStyles[size]
  const IconComponent = currentVariant.IconComponent

  return (
    <div
      className={clsx(
        'relative border rounded-lg',
        currentVariant.container,
        currentSize.container,
        className
      )}
      role="alert"
      {...props}
    >
      <div className="flex items-start">
        {icon && (
          <IconComponent
            className={clsx(
              'flex-shrink-0 mt-0.5 mr-3',
              currentVariant.icon,
              currentSize.icon
            )}
          />
        )}
        
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={clsx(
              'font-medium mb-1',
              currentVariant.title
            )}>
              {title}
            </h4>
          )}
          
          <div className="prose prose-sm max-w-none">
            {children}
          </div>
        </div>

        {dismissible && (
          <button
            type="button"
            onClick={onDismiss}
            className={clsx(
              'flex-shrink-0 ml-3 p-1 rounded-md transition-colors duration-200',
              currentVariant.icon,
              'hover:bg-black hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent focus:ring-current'
            )}
            aria-label="Dismiss alert"
          >
            <X className={currentSize.dismissButton} />
          </button>
        )}
      </div>
    </div>
  )
}

// Alert variants as separate components
export const InfoAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert variant="info" {...props} />
)

export const SuccessAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert variant="success" {...props} />
)

export const WarningAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert variant="warning" {...props} />
)

export const ErrorAlert: React.FC<Omit<AlertProps, 'variant'>> = (props) => (
  <Alert variant="error" {...props} />
)

export default Alert