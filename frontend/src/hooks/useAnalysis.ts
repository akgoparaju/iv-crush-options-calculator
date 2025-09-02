import { useMutation, useQuery } from '@tanstack/react-query'
import { analysisService, healthService } from '@/services/analysis'
import { AnalysisRequest, AnalysisResponse, HealthResponse } from '@/types/api'

/**
 * React Query hook for symbol analysis
 */
export const useAnalysis = () => {
  return useMutation<AnalysisResponse, Error, AnalysisRequest>({
    mutationFn: async (request: AnalysisRequest) => {
      return await analysisService.analyzeSymbol(request)
    },
    onError: (error) => {
      console.error('Analysis failed:', error)
    }
  })
}

/**
 * React Query hook for quick symbol analysis
 */
export const useQuickAnalysis = () => {
  return useMutation<AnalysisResponse, Error, {
    symbol: string
    options?: {
      includeEarnings?: boolean
      includeTrades?: boolean
      useDemo?: boolean
    }
  }>({
    mutationFn: async ({ symbol, options }) => {
      return await analysisService.quickAnalyze(symbol, options)
    },
    onError: (error) => {
      console.error('Quick analysis failed:', error)
    }
  })
}

/**
 * React Query hook for health check
 */
export const useHealthCheck = () => {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: async () => {
      return await healthService.checkHealth()
    },
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    staleTime: 10000 // Consider data stale after 10 seconds
  })
}

/**
 * React Query hook for API readiness check
 */
export const useApiReadiness = () => {
  return useQuery<boolean, Error>({
    queryKey: ['api-ready'],
    queryFn: async () => {
      return await healthService.checkReadiness()
    },
    refetchInterval: 10000, // Check every 10 seconds
    retry: 5,
    staleTime: 5000
  })
}

/**
 * React Query hook for symbol validation
 */
export const useSymbolValidation = (symbol: string) => {
  return useQuery<boolean, Error>({
    queryKey: ['symbol-validation', symbol],
    queryFn: async () => {
      if (!symbol || symbol.length === 0) return false
      return await analysisService.validateSymbol(symbol.toUpperCase())
    },
    enabled: !!symbol && symbol.length > 0,
    staleTime: 300000, // Symbol validity is stable for 5 minutes
    retry: 2
  })
}

/**
 * Hook for getting basic symbol information
 */
export const useSymbolInfo = (symbol: string) => {
  return useQuery({
    queryKey: ['symbol-info', symbol],
    queryFn: async () => {
      if (!symbol || symbol.length === 0) return null
      return await analysisService.getBasicSymbolInfo(symbol.toUpperCase())
    },
    enabled: !!symbol && symbol.length > 0,
    staleTime: 60000, // Symbol info is stable for 1 minute
    retry: 2
  })
}