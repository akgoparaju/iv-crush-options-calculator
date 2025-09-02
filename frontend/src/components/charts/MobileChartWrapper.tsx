import React, { useState, useEffect, useRef, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { MobileChartConfig } from '@/types/charts'
import { mobileChartConfig as defaultMobileConfig } from '@/utils/chartTheme'

interface MobileChartWrapperProps {
  children: React.ReactNode
  title: string
  config?: MobileChartConfig
  onSwipe?: (direction: 'left' | 'right') => void
}

export const MobileChartWrapper: React.FC<MobileChartWrapperProps> = ({
  children,
  title,
  config = {
    touchOptimized: true,
    minTouchTarget: defaultMobileConfig.minTouchTarget,
    pinchZoom: true,
    swipePan: true,
    stackOnMobile: true,
    simplifiedLayout: true
  },
  onSwipe
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(null)
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Touch event handlers
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!config.touchOptimized) return
    
    if (e.touches.length === 1) {
      setTouchStart({
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
      })
    }
  }, [config.touchOptimized])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!config.touchOptimized || !touchStart) return
    
    if (e.touches.length === 1 && config.swipePan) {
      const deltaX = e.touches[0].clientX - touchStart.x
      const deltaY = e.touches[0].clientY - touchStart.y
      
      // Update position for panning
      if (scale > 1) {
        setPosition(prev => ({
          x: prev.x + deltaX * 0.5,
          y: prev.y + deltaY * 0.5
        }))
      }
    } else if (e.touches.length === 2 && config.pinchZoom) {
      // Handle pinch zoom
      const touch1 = e.touches[0]
      const touch2 = e.touches[1]
      
      const distance = Math.sqrt(
        Math.pow(touch2.clientX - touch1.clientX, 2) +
        Math.pow(touch2.clientY - touch1.clientY, 2)
      )
      
      // Simple pinch zoom calculation
      const newScale = Math.min(Math.max(0.5, distance / 200), 3)
      setScale(newScale)
    }
  }, [config.touchOptimized, config.swipePan, config.pinchZoom, touchStart, scale])

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (!config.touchOptimized || !touchStart) return
    
    const deltaX = e.changedTouches[0].clientX - touchStart.x
    const deltaY = e.changedTouches[0].clientY - touchStart.y
    
    // Detect swipe gestures
    if (Math.abs(deltaX) > 50 && Math.abs(deltaY) < 30) {
      if (deltaX > 0 && onSwipe) {
        onSwipe('right')
      } else if (deltaX < 0 && onSwipe) {
        onSwipe('left')
      }
    }
    
    setTouchStart(null)
  }, [config.touchOptimized, touchStart, onSwipe])

  // Reset zoom and position
  const handleReset = () => {
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement && containerRef.current) {
      containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else if (document.exitFullscreen) {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  // Handle fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  // Mobile detection
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  // Apply simplified layout for mobile
  const chartStyle = config.simplifiedLayout && isMobile
    ? { padding: '8px', fontSize: '12px' }
    : {}

  return (
    <div
      ref={containerRef}
      className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{
        touchAction: config.touchOptimized ? 'none' : 'auto',
        userSelect: 'none'
      }}
    >
      {/* Mobile Controls Header */}
      <div className="flex items-center justify-between p-2 bg-slate-100 rounded-t-lg md:hidden">
        <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
        <div className="flex items-center space-x-1">
          {scale !== 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              style={{ minWidth: config.minTouchTarget, minHeight: config.minTouchTarget }}
            >
              Reset
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleFullscreen}
            style={{ minWidth: config.minTouchTarget, minHeight: config.minTouchTarget }}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Chart Content */}
      <div
        ref={contentRef}
        className={`${config.stackOnMobile && isMobile ? 'space-y-4' : ''}`}
        style={{
          transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
          transformOrigin: 'center',
          transition: touchStart ? 'none' : 'transform 0.3s ease',
          ...chartStyle
        }}
      >
        {children}
      </div>

      {/* Mobile Navigation Hints */}
      {config.touchOptimized && isMobile && !isFullscreen && (
        <div className="flex items-center justify-center p-2 text-xs text-slate-500 bg-slate-50 rounded-b-lg">
          <ChevronLeft className="h-3 w-3" />
          <span className="mx-2">Swipe to navigate • Pinch to zoom</span>
          <ChevronRight className="h-3 w-3" />
        </div>
      )}

      {/* Zoom Indicator */}
      {scale !== 1 && (
        <div className="absolute top-4 right-4 px-2 py-1 bg-black bg-opacity-50 text-white text-xs rounded">
          {Math.round(scale * 100)}%
        </div>
      )}
    </div>
  )
}

export default MobileChartWrapper