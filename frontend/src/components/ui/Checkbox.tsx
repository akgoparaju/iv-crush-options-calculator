import React from 'react'
import { Check } from 'lucide-react'
import { clsx } from 'clsx'

interface CheckboxProps {
  id?: string
  name?: string
  checked?: boolean
  onChange?: (checked: boolean) => void
  disabled?: boolean
  label?: string
  description?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
}

export const Checkbox: React.FC<CheckboxProps> = ({
  id,
  name,
  checked = false,
  onChange,
  disabled = false,
  label,
  description,
  className,
  size = 'md',
  variant = 'default',
  ...props
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!disabled && onChange) {
      onChange(e.target.checked)
    }
  }

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  }

  const iconSizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4'
  }

  const variantClasses = {
    default: {
      unchecked: 'border-slate-300 bg-white hover:border-slate-400',
      checked: 'border-slate-600 bg-slate-600 hover:border-slate-700 hover:bg-slate-700',
      disabled: 'border-slate-200 bg-slate-50 cursor-not-allowed'
    },
    primary: {
      unchecked: 'border-slate-300 bg-white hover:border-blue-400',
      checked: 'border-blue-600 bg-blue-600 hover:border-blue-700 hover:bg-blue-700',
      disabled: 'border-slate-200 bg-slate-50 cursor-not-allowed'
    },
    success: {
      unchecked: 'border-slate-300 bg-white hover:border-green-400',
      checked: 'border-green-600 bg-green-600 hover:border-green-700 hover:bg-green-700',
      disabled: 'border-slate-200 bg-slate-50 cursor-not-allowed'
    },
    warning: {
      unchecked: 'border-slate-300 bg-white hover:border-amber-400',
      checked: 'border-amber-600 bg-amber-600 hover:border-amber-700 hover:bg-amber-700',
      disabled: 'border-slate-200 bg-slate-50 cursor-not-allowed'
    },
    danger: {
      unchecked: 'border-slate-300 bg-white hover:border-red-400',
      checked: 'border-red-600 bg-red-600 hover:border-red-700 hover:bg-red-700',
      disabled: 'border-slate-200 bg-slate-50 cursor-not-allowed'
    }
  }

  const getVariantClasses = () => {
    if (disabled) return variantClasses[variant].disabled
    return checked ? variantClasses[variant].checked : variantClasses[variant].unchecked
  }

  return (
    <div className={clsx('flex items-start gap-2', className)}>
      <div className="relative flex items-center">
        <input
          type="checkbox"
          id={id}
          name={name}
          checked={checked}
          onChange={handleChange}
          disabled={disabled}
          className="sr-only"
          {...props}
        />
        <div
          className={clsx(
            'relative flex items-center justify-center border rounded transition-colors duration-200',
            sizeClasses[size],
            getVariantClasses(),
            disabled ? 'cursor-not-allowed' : 'cursor-pointer'
          )}
          onClick={() => !disabled && onChange?.(checked)}
        >
          {checked && (
            <Check 
              className={clsx(
                'text-white transition-opacity duration-200',
                iconSizeClasses[size]
              )} 
            />
          )}
        </div>
      </div>
      
      {(label || description) && (
        <div className="flex flex-col">
          {label && (
            <label 
              htmlFor={id}
              className={clsx(
                'text-sm font-medium leading-none cursor-pointer',
                disabled ? 'text-slate-400 cursor-not-allowed' : 'text-slate-700'
              )}
            >
              {label}
            </label>
          )}
          {description && (
            <p className={clsx(
              'text-xs mt-1',
              disabled ? 'text-slate-300' : 'text-slate-500'
            )}>
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default Checkbox