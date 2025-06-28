import React from 'react'
import { Loader2, Car } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  className?: string
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text = 'Loading...',
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div className={cn('flex items-center justify-center space-x-2', className)}>
      <Loader2 className={cn('animate-spin', sizeClasses[size])} />
      {text && <span className="text-muted-foreground">{text}</span>}
    </div>
  )
}

export const PageLoading: React.FC<{ text?: string }> = ({ text = 'Loading page...' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
      <div className="relative">
        <div className="auto-scouter-gradient w-16 h-16 rounded-full flex items-center justify-center animate-pulse">
          <Car className="w-8 h-8 text-white" />
        </div>
        <Loader2 className="absolute inset-0 w-16 h-16 animate-spin text-primary" />
      </div>
      <p className="text-lg font-medium">{text}</p>
      <p className="text-sm text-muted-foreground">Please wait while we load your content</p>
    </div>
  )
}

export const CardLoading: React.FC = () => {
  return (
    <div className="animate-pulse">
      <div className="bg-muted rounded-lg h-48 mb-4"></div>
      <div className="space-y-2">
        <div className="bg-muted rounded h-4 w-3/4"></div>
        <div className="bg-muted rounded h-4 w-1/2"></div>
        <div className="bg-muted rounded h-4 w-2/3"></div>
      </div>
    </div>
  )
}

export const TableLoading: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 4,
}) => {
  return (
    <div className="animate-pulse space-y-3">
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="bg-muted rounded h-4"></div>
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: cols }).map((_, colIndex) => (
            <div key={colIndex} className="bg-muted rounded h-4"></div>
          ))}
        </div>
      ))}
    </div>
  )
}

export const ListLoading: React.FC<{ items?: number }> = ({ items = 5 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: items }).map((_, index) => (
        <div key={index} className="animate-pulse flex items-center space-x-4">
          <div className="bg-muted rounded-full w-10 h-10"></div>
          <div className="flex-1 space-y-2">
            <div className="bg-muted rounded h-4 w-3/4"></div>
            <div className="bg-muted rounded h-3 w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

export const VehicleCardLoading: React.FC = () => {
  return (
    <div className="animate-pulse border rounded-lg p-4">
      {/* Image placeholder */}
      <div className="bg-muted rounded-lg h-48 mb-4"></div>
      
      {/* Content */}
      <div className="space-y-3">
        {/* Title */}
        <div className="bg-muted rounded h-5 w-3/4"></div>
        
        {/* Badges */}
        <div className="flex space-x-2">
          <div className="bg-muted rounded-full h-6 w-16"></div>
          <div className="bg-muted rounded-full h-6 w-20"></div>
        </div>
        
        {/* Details */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-muted rounded h-4 w-full"></div>
          <div className="bg-muted rounded h-4 w-full"></div>
          <div className="bg-muted rounded h-4 w-full"></div>
          <div className="bg-muted rounded h-4 w-full"></div>
        </div>
        
        {/* Price and button */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="bg-muted rounded h-6 w-24"></div>
          <div className="bg-muted rounded h-8 w-20"></div>
        </div>
      </div>
    </div>
  )
}

export const StatsCardLoading: React.FC = () => {
  return (
    <div className="animate-pulse border rounded-lg p-6">
      <div className="flex items-center justify-between mb-2">
        <div className="bg-muted rounded h-4 w-24"></div>
        <div className="bg-muted rounded-full w-4 h-4"></div>
      </div>
      <div className="bg-muted rounded h-8 w-16 mb-1"></div>
      <div className="bg-muted rounded h-3 w-20"></div>
    </div>
  )
}

export const ButtonLoading: React.FC<{
  size?: 'sm' | 'md' | 'lg'
  className?: string
}> = ({ size = 'md', className }) => {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  return (
    <Loader2 className={cn('animate-spin', sizeClasses[size], className)} />
  )
}

export const InlineLoading: React.FC<{
  text?: string
  size?: 'sm' | 'md'
}> = ({ text = 'Loading...', size = 'sm' }) => {
  return (
    <span className="inline-flex items-center space-x-1 text-muted-foreground">
      <Loader2 className={cn('animate-spin', size === 'sm' ? 'w-3 h-3' : 'w-4 h-4')} />
      <span className={size === 'sm' ? 'text-xs' : 'text-sm'}>{text}</span>
    </span>
  )
}

// Loading overlay for forms or sections
export const LoadingOverlay: React.FC<{
  isLoading: boolean
  text?: string
  children: React.ReactNode
}> = ({ isLoading, text = 'Loading...', children }) => {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10">
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="w-8 h-8 animate-spin" />
            <p className="text-sm font-medium">{text}</p>
          </div>
        </div>
      )}
    </div>
  )
}
