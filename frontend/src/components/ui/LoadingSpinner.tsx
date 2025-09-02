import React from 'react'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  message?: string
  overlay?: boolean
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  message,
  overlay = false
}) => {
  const sizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }

  const spinner = (
    <div className={clsx(
      "flex items-center justify-center",
      overlay && "min-h-[200px]",
      className
    )}>
      <div className="flex flex-col items-center space-y-2">
        <Loader2 className={clsx(
          "animate-spin text-primary-600",
          sizeClasses[size]
        )} />
        {message && (
          <p className="text-sm text-slate-600 font-medium">
            {message}
          </p>
        )}
      </div>
    </div>
  )

  if (overlay) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-strong p-6">
          {spinner}
        </div>
      </div>
    )
  }

  return spinner
}

// Skeleton loader for content placeholders
interface SkeletonProps {
  className?: string
  rows?: number
  showAvatar?: boolean
}

const Skeleton: React.FC<SkeletonProps> = ({ 
  className, 
  rows = 3, 
  showAvatar = false 
}) => {
  return (
    <div className={clsx("animate-pulse", className)}>
      <div className="flex items-start space-x-4">
        {showAvatar && (
          <div className="rounded-full bg-slate-200 h-10 w-10" />
        )}
        <div className="flex-1 space-y-3">
          {Array.from({ length: rows }).map((_, index) => (
            <div key={index} className="space-y-3">
              <div className="h-4 bg-slate-200 rounded" />
              {index === rows - 1 && (
                <div className="h-4 bg-slate-200 rounded w-2/3" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Chart skeleton for chart loading states
const ChartSkeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={clsx("animate-pulse bg-slate-100 rounded-lg", className)}>
      <div className="h-64 flex items-end justify-around p-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <div
            key={index}
            className="bg-slate-200 rounded-t"
            style={{
              height: `${Math.random() * 150 + 50}px`,
              width: '20px'
            }}
          />
        ))}
      </div>
    </div>
  )
}

// Progress bar for long-running operations
interface ProgressBarProps {
  progress: number
  message?: string
  className?: string
}

const ProgressBar: React.FC<ProgressBarProps> = ({ 
  progress, 
  message, 
  className 
}) => {
  return (
    <div className={clsx("w-full", className)}>
      <div className="flex justify-between text-sm text-slate-600 mb-1">
        <span>{message || 'Loading...'}</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>
    </div>
  )
}

export { LoadingSpinner, Skeleton, ChartSkeleton, ProgressBar }