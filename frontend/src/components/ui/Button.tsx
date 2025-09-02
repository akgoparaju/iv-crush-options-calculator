import React from 'react'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  fullWidth?: boolean
  icon?: React.ReactNode
  children: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  icon,
  className,
  disabled,
  children,
  ...props
}, ref) => {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
  
  const variantClasses = {
    primary: "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500",
    secondary: "bg-slate-200 text-slate-900 hover:bg-slate-300 focus-visible:ring-slate-500",
    success: "bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500",
    danger: "bg-danger-600 text-white hover:bg-danger-700 focus-visible:ring-danger-500",
    ghost: "bg-transparent text-slate-600 hover:bg-slate-100 focus-visible:ring-slate-500"
  }
  
  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base", 
    lg: "px-6 py-3 text-lg"
  }

  return (
    <button
      ref={ref}
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
      ) : icon ? (
        <span className="mr-2">{icon}</span>
      ) : null}
      <span>{children}</span>
    </button>
  )
})

Button.displayName = 'Button'

export { Button }