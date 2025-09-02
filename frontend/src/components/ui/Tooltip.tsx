import React, { useState, useRef } from 'react'
import { createPortal } from 'react-dom'

interface TooltipProps {
  content: React.ReactNode
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
  className?: string
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 300,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({})
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect()
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop
        
        let tooltipPosition: React.CSSProperties = {
          position: 'absolute',
          zIndex: 9999
        }

        switch (position) {
          case 'top':
            tooltipPosition = {
              ...tooltipPosition,
              left: rect.left + scrollLeft + rect.width / 2,
              top: rect.top + scrollTop - 8,
              transform: 'translateX(-50%) translateY(-100%)'
            }
            break
          case 'bottom':
            tooltipPosition = {
              ...tooltipPosition,
              left: rect.left + scrollLeft + rect.width / 2,
              top: rect.bottom + scrollTop + 8,
              transform: 'translateX(-50%)'
            }
            break
          case 'left':
            tooltipPosition = {
              ...tooltipPosition,
              left: rect.left + scrollLeft - 8,
              top: rect.top + scrollTop + rect.height / 2,
              transform: 'translateX(-100%) translateY(-50%)'
            }
            break
          case 'right':
            tooltipPosition = {
              ...tooltipPosition,
              left: rect.right + scrollLeft + 8,
              top: rect.top + scrollTop + rect.height / 2,
              transform: 'translateY(-50%)'
            }
            break
        }

        setTooltipStyle(tooltipPosition)
        setIsVisible(true)
      }
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  const tooltipClasses = `
    px-2 py-1 text-xs font-medium text-white bg-slate-900 rounded shadow-lg
    max-w-xs break-words whitespace-normal
    ${className}
  `

  const arrowClasses = {
    top: 'absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900',
    bottom: 'absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-slate-900',
    left: 'absolute left-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-l-4 border-transparent border-l-slate-900',
    right: 'absolute right-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-slate-900'
  }

  return (
    <>
      <div
        ref={triggerRef}
        className="inline-flex cursor-help"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        {children}
      </div>
      
      {isVisible && content && createPortal(
        <div
          ref={tooltipRef}
          className={tooltipClasses}
          style={tooltipStyle}
          role="tooltip"
        >
          {content}
          <div className={arrowClasses[position]} />
        </div>,
        document.body
      )}
    </>
  )
}

export default Tooltip