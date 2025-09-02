import React from 'react'
import { clsx } from 'clsx'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  success?: string
  helpText?: string
  icon?: React.ReactNode
  fullWidth?: boolean
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  success,
  helpText,
  icon,
  fullWidth = true,
  className,
  id,
  name,
  ...props
}, ref) => {
  // Generate a unique ID if none provided
  const inputId = id || `input-${name || Math.random().toString(36).slice(2, 9)}`
  
  const inputClasses = clsx(
    "block rounded-md border bg-white px-3 py-2 text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:ring-1",
    {
      "w-full": fullWidth,
      "border-slate-300 focus:border-primary-500 focus:ring-primary-500": !error && !success,
      "border-danger-300 focus:border-danger-500 focus:ring-danger-500": error,
      "border-success-300 focus:border-success-500 focus:ring-success-500": success && !error,
      "pl-10": icon
    },
    className
  )

  return (
    <div className={clsx("space-y-1", !fullWidth && "inline-block")}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
          {label}
          {props.required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            {icon}
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          className={inputClasses}
          {...props}
        />
      </div>
      
      {error && (
        <p className="text-sm text-danger-600" role="alert">
          {error}
        </p>
      )}
      
      {success && !error && (
        <p className="text-sm text-success-600">
          {success}
        </p>
      )}
      
      {helpText && !error && !success && (
        <p className="text-sm text-slate-500">
          {helpText}
        </p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export { Input }