import React from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'default' | 'info' | 'success' | 'warning' | 'danger' | 'conservative' | 'moderate' | 'aggressive'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  children,
  className
}) => {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-full"
  
  const variantClasses = {
    default: 'bg-slate-100 text-slate-700',
    info: 'bg-primary-100 text-primary-800',
    success: 'bg-success-100 text-success-800',
    warning: 'bg-warning-100 text-warning-800',
    danger: 'bg-danger-100 text-danger-800',
    conservative: 'bg-success-100 text-success-800',
    moderate: 'bg-warning-100 text-warning-800',
    aggressive: 'bg-danger-100 text-danger-800'
  }
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  }

  return (
    <span className={clsx(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      className
    )}>
      {children}
    </span>
  )
}

export default Badge