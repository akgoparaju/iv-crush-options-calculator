// Market screening service for API integration
import { apiClient } from './api';
import {
  ScreeningCriteria,
  ScreeningRequest,
  ScreeningResponse,
  ScreeningTemplate,
  ScreeningCategory,
  ScreeningResult,
  MarketOverview,
  Watchlist,
  WatchlistItem,
  CreateWatchlistRequest,
  UpdateWatchlistRequest,
  SaveScreeningCriteriaRequest,
  UpdateScreeningCriteriaRequest,
  ScreeningChartData,
  AlertCondition,
} from '../types/screening';

export class ScreeningService {
  private baseUrl = '/screening';

  // Market Screening
  async runScreening(request: ScreeningRequest): Promise<ScreeningResponse> {
    const response = await apiClient.post(`${this.baseUrl}/run`, request);
    return response.data;
  }

  async getScreeningTemplates(category?: ScreeningCategory): Promise<ScreeningTemplate[]> {
    const params = category ? `?category=${category}` : '';
    const response = await apiClient.get(`${this.baseUrl}/templates${params}`);
    return response.data.templates;
  }

  async getScreeningTemplate(templateId: string): Promise<ScreeningTemplate> {
    const response = await apiClient.get(`${this.baseUrl}/templates/${templateId}`);
    return response.data.template;
  }

  async getPopularScreenings(limit = 10): Promise<ScreeningTemplate[]> {
    const response = await apiClient.get(`${this.baseUrl}/templates/popular?limit=${limit}`);
    return response.data.templates;
  }

  // Screening Criteria Management
  async saveScreeningCriteria(request: SaveScreeningCriteriaRequest): Promise<ScreeningCriteria> {
    const response = await apiClient.post(`${this.baseUrl}/criteria`, request);
    return response.data.criteria;
  }

  async updateScreeningCriteria(request: UpdateScreeningCriteriaRequest): Promise<ScreeningCriteria> {
    const response = await apiClient.put(`${this.baseUrl}/criteria/${request.id}`, request);
    return response.data.criteria;
  }

  async deleteScreeningCriteria(criteriaId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/criteria/${criteriaId}`);
  }

  async getUserScreeningCriteria(): Promise<ScreeningCriteria[]> {
    const response = await apiClient.get(`${this.baseUrl}/criteria`);
    return response.data.criteria;
  }

  async getScreeningCriteria(criteriaId: string): Promise<ScreeningCriteria> {
    const response = await apiClient.get(`${this.baseUrl}/criteria/${criteriaId}`);
    return response.data.criteria;
  }

  // Market Overview
  async getMarketOverview(): Promise<MarketOverview> {
    const response = await apiClient.get(`${this.baseUrl}/market/overview`);
    return response.data;
  }

  async getSectorPerformance(): Promise<MarketOverview['sectors']> {
    const response = await apiClient.get(`${this.baseUrl}/market/sectors`);
    return response.data.sectors;
  }

  async getEarningsCalendar(days = 7): Promise<MarketOverview['earnings']> {
    const response = await apiClient.get(`${this.baseUrl}/market/earnings?days=${days}`);
    return response.data.earnings;
  }

  async getTopMovers(type: 'gainers' | 'losers' | 'active' = 'gainers', limit = 20): Promise<ScreeningResult[]> {
    const response = await apiClient.get(`${this.baseUrl}/market/movers/${type}?limit=${limit}`);
    return response.data.results;
  }

  // Individual Symbol Analysis
  async getSymbolAnalysis(symbol: string): Promise<ScreeningResult> {
    const response = await apiClient.get(`${this.baseUrl}/symbol/${symbol}`);
    return response.data.result;
  }

  async getSymbolStrategies(symbol: string, strategyTypes?: string[]): Promise<ScreeningResult['strategies']> {
    const params = new URLSearchParams();
    if (strategyTypes) {
      strategyTypes.forEach(type => params.append('strategy', type));
    }
    
    const response = await apiClient.get(`${this.baseUrl}/symbol/${symbol}/strategies?${params.toString()}`);
    return response.data.strategies;
  }

  async compareSymbols(symbols: string[]): Promise<ScreeningResult[]> {
    const response = await apiClient.post(`${this.baseUrl}/compare`, { symbols });
    return response.data.results;
  }

  // Watchlists
  async getWatchlists(): Promise<Watchlist[]> {
    const response = await apiClient.get(`${this.baseUrl}/watchlists`);
    return response.data.watchlists;
  }

  async getWatchlist(watchlistId: string): Promise<{ watchlist: Watchlist; items: WatchlistItem[] }> {
    const response = await apiClient.get(`${this.baseUrl}/watchlists/${watchlistId}`);
    return response.data;
  }

  async createWatchlist(request: CreateWatchlistRequest): Promise<Watchlist> {
    const response = await apiClient.post(`${this.baseUrl}/watchlists`, request);
    return response.data.watchlist;
  }

  async updateWatchlist(request: UpdateWatchlistRequest): Promise<Watchlist> {
    const response = await apiClient.put(`${this.baseUrl}/watchlists/${request.id}`, request);
    return response.data.watchlist;
  }

  async deleteWatchlist(watchlistId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/watchlists/${watchlistId}`);
  }

  async addSymbolToWatchlist(watchlistId: string, symbol: string, notes?: string): Promise<WatchlistItem> {
    const response = await apiClient.post(`${this.baseUrl}/watchlists/${watchlistId}/symbols`, {
      symbol,
      notes,
    });
    return response.data.item;
  }

  async removeSymbolFromWatchlist(watchlistId: string, symbol: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/watchlists/${watchlistId}/symbols/${symbol}`);
  }

  async updateWatchlistItem(watchlistId: string, symbol: string, notes?: string): Promise<WatchlistItem> {
    const response = await apiClient.put(`${this.baseUrl}/watchlists/${watchlistId}/symbols/${symbol}`, {
      notes,
    });
    return response.data.item;
  }

  // Alerts
  async createAlert(
    watchlistId: string, 
    symbol: string, 
    condition: AlertCondition
  ): Promise<WatchlistItem['alerts'][0]> {
    const response = await apiClient.post(`${this.baseUrl}/watchlists/${watchlistId}/symbols/${symbol}/alerts`, {
      condition,
    });
    return response.data.alert;
  }

  async updateAlert(alertId: string, condition: AlertCondition): Promise<WatchlistItem['alerts'][0]> {
    const response = await apiClient.put(`${this.baseUrl}/alerts/${alertId}`, { condition });
    return response.data.alert;
  }

  async toggleAlert(alertId: string, isActive: boolean): Promise<WatchlistItem['alerts'][0]> {
    const response = await apiClient.patch(`${this.baseUrl}/alerts/${alertId}`, { isActive });
    return response.data.alert;
  }

  async deleteAlert(alertId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/alerts/${alertId}`);
  }

  async getTriggeredAlerts(): Promise<WatchlistItem['alerts']> {
    const response = await apiClient.get(`${this.baseUrl}/alerts/triggered`);
    return response.data.alerts;
  }

  // Historical Data & Analytics
  async getScreeningHistory(criteriaId: string, days = 30): Promise<ScreeningChartData> {
    const response = await apiClient.get(`${this.baseUrl}/criteria/${criteriaId}/history?days=${days}`);
    return response.data;
  }

  async getScreeningPerformance(criteriaId: string, timeframe = '1M'): Promise<{
    returns: Array<{ date: string; return: number; benchmark: number }>;
    summary: {
      totalReturn: number;
      benchmarkReturn: number;
      winRate: number;
      sharpeRatio: number;
      maxDrawdown: number;
    };
  }> {
    const response = await apiClient.get(`${this.baseUrl}/criteria/${criteriaId}/performance?timeframe=${timeframe}`);
    return response.data;
  }

  async getMarketStatistics(): Promise<{
    totalSymbols: number;
    activeScreenings: number;
    avgImpliedVolatility: number;
    sectorsTracked: number;
    earningsThisWeek: number;
    mostActiveSymbol: string;
    mostScreenedStrategy: string;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/market/statistics`);
    return response.data.statistics;
  }

  // Screening Insights
  async getScreeningInsights(timeframe = '7D'): Promise<{
    insights: Array<{
      type: 'trend' | 'anomaly' | 'opportunity' | 'warning';
      title: string;
      description: string;
      confidence: number;
      symbols?: string[];
      data?: any;
    }>;
    recommendations: Array<{
      action: 'watch' | 'analyze' | 'trade' | 'avoid';
      symbol: string;
      strategy?: string;
      reasoning: string;
      priority: 'high' | 'medium' | 'low';
    }>;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/insights?timeframe=${timeframe}`);
    return response.data;
  }

  // Export/Import
  async exportScreeningResults(criteriaId: string, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/criteria/${criteriaId}/export?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async exportWatchlist(watchlistId: string, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/watchlists/${watchlistId}/export?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async importWatchlist(file: File): Promise<Watchlist> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(`${this.baseUrl}/watchlists/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.watchlist;
  }

  // Real-time Updates
  async subscribeToScreeningUpdates(criteriaId: string, callback: (results: ScreeningResult[]) => void): Promise<() => void> {
    // In a real implementation, this would set up a WebSocket or Server-Sent Events connection
    // For now, we'll simulate with polling
    const pollInterval = setInterval(async () => {
      try {
        const response = await this.runScreening({
          criteria: await this.getScreeningCriteria(criteriaId),
          limit: 100,
        });
        callback(response.results);
      } catch (error) {
        console.error('Error polling screening updates:', error);
      }
    }, 30000); // Poll every 30 seconds

    // Return unsubscribe function
    return () => clearInterval(pollInterval);
  }

  async subscribeToMarketUpdates(callback: (overview: MarketOverview) => void): Promise<() => void> {
    const pollInterval = setInterval(async () => {
      try {
        const overview = await this.getMarketOverview();
        callback(overview);
      } catch (error) {
        console.error('Error polling market updates:', error);
      }
    }, 60000); // Poll every minute

    return () => clearInterval(pollInterval);
  }
}

// Export singleton instance
export const screeningService = new ScreeningService();