import React from 'react'
import { clsx } from 'clsx'

interface CardProps {
  title?: string
  subtitle?: string
  status?: 'success' | 'warning' | 'error' | 'info'
  children: React.ReactNode
  collapsible?: boolean
  defaultExpanded?: boolean
  actions?: React.ReactNode
  className?: string
}

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  status,
  children,
  collapsible = false,
  defaultExpanded = true,
  actions,
  className
}) => {
  const [expanded, setExpanded] = React.useState(defaultExpanded)
  
  const statusClasses = {
    success: 'border-success-200 bg-success-50/30',
    warning: 'border-warning-200 bg-warning-50/30',
    error: 'border-danger-200 bg-danger-50/30',
    info: 'border-primary-200 bg-primary-50/30'
  }
  
  const statusIcons = {
    success: '✅',
    warning: '⚠️', 
    error: '❌',
    info: 'ℹ️'
  }

  return (
    <div className={clsx(
      "rounded-lg border shadow-soft bg-white",
      status ? statusClasses[status] : "border-slate-200",
      className
    )}>
      {(title || subtitle || actions || collapsible) && (
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {title && (
              <div className="flex items-center space-x-2">
                {status && <span className="text-lg">{statusIcons[status]}</span>}
                <h3 className="text-lg font-semibold text-slate-900 truncate">
                  {title}
                </h3>
              </div>
            )}
            {subtitle && (
              <p className="text-sm text-slate-600 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            {actions}
            {collapsible && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="p-1 text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded"
                aria-label={expanded ? "Collapse" : "Expand"}
              >
                <svg
                  className={clsx("h-5 w-5 transform transition-transform", {
                    "rotate-180": expanded
                  })}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}
      
      {(!collapsible || expanded) && (
        <div className="px-6 py-4">
          {children}
        </div>
      )}
    </div>
  )
}

// Card sub-components for better organization
interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={clsx("px-6 py-4 border-b border-slate-200", className)}>
    {children}
  </div>
)

interface CardContentProps {
  children: React.ReactNode
  className?: string
}

const CardContent: React.FC<CardContentProps> = ({ children, className }) => (
  <div className={clsx("px-6 py-4", className)}>
    {children}
  </div>
)

interface CardFooterProps {
  children: React.ReactNode
  className?: string
}

const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => (
  <div className={clsx("px-6 py-4 border-t border-slate-200 bg-slate-50/50", className)}>
    {children}
  </div>
)

export { Card, CardHeader, CardContent, CardFooter }