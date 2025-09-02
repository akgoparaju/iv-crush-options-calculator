import React from 'react'
import { clsx } from 'clsx'
import { ChevronDown } from 'lucide-react'

interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label?: string
  options: SelectOption[]
  error?: string
  success?: string
  helpText?: string
  fullWidth?: boolean
  placeholder?: string
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  options,
  error,
  success,
  helpText,
  fullWidth = true,
  placeholder,
  className,
  id,
  name,
  ...props
}, ref) => {
  // Generate a unique ID if none provided
  const selectId = id || `select-${name || Math.random().toString(36).slice(2, 9)}`
  
  const selectClasses = clsx(
    "block rounded-md border bg-white px-3 py-2 pr-10 text-sm shadow-sm focus:outline-none focus:ring-1 appearance-none",
    {
      "w-full": fullWidth,
      "border-slate-300 focus:border-primary-500 focus:ring-primary-500": !error && !success,
      "border-danger-300 focus:border-danger-500 focus:ring-danger-500": error,
      "border-success-300 focus:border-success-500 focus:ring-success-500": success && !error
    },
    className
  )

  return (
    <div className={clsx("space-y-1", !fullWidth && "inline-block")}>
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-slate-700">
          {label}
          {props.required && <span className="text-danger-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          className={selectClasses}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <ChevronDown className="h-4 w-4 text-slate-400" />
        </div>
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

Select.displayName = 'Select'

export { Select }
export type { SelectOption }