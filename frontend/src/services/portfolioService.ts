// Portfolio service for API integration
import { apiClient } from './api';
import {
  PortfolioSummary,
  PortfolioDetail,
  Position,
  CreatePortfolioRequest,
  UpdatePortfolioRequest,
  AddPositionRequest,
  ClosePositionRequest,
  PortfolioAnalytics,
  PortfolioFilter,
  PortfolioSort,
  PositionFilter,
  PositionSort,
} from '../types/portfolio';

export class PortfolioService {
  private baseUrl = '/portfolio';

  // Portfolio Management
  async getPortfolios(
    filter?: PortfolioFilter,
    sort?: PortfolioSort
  ): Promise<PortfolioSummary[]> {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else if (typeof value === 'object') {
            params.append(key, JSON.stringify(value));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    if (sort) {
      params.append('sortBy', sort.field);
      params.append('sortOrder', sort.direction);
    }

    const response = await apiClient.get(`${this.baseUrl}?${params.toString()}`);
    return response.data.portfolios || [];
  }

  async getPortfolioDetail(portfolioId: string): Promise<PortfolioDetail> {
    const response = await apiClient.get(`${this.baseUrl}/${portfolioId}`);
    return response.data.portfolio;
  }

  async createPortfolio(data: CreatePortfolioRequest): Promise<PortfolioSummary> {
    const response = await apiClient.post(this.baseUrl, data);
    return response.data.portfolio;
  }

  async updatePortfolio(
    portfolioId: string,
    data: UpdatePortfolioRequest
  ): Promise<PortfolioSummary> {
    const response = await apiClient.put(`${this.baseUrl}/${portfolioId}`, data);
    return response.data.portfolio;
  }

  async deletePortfolio(portfolioId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${portfolioId}`);
  }

  // Position Management
  async getPositions(
    portfolioId: string,
    filter?: PositionFilter,
    sort?: PositionSort
  ): Promise<Position[]> {
    const params = new URLSearchParams();
    
    if (filter) {
      Object.entries(filter).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else if (typeof value === 'object') {
            params.append(key, JSON.stringify(value));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    if (sort) {
      params.append('sortBy', sort.field);
      params.append('sortOrder', sort.direction);
    }

    const response = await apiClient.get(
      `${this.baseUrl}/${portfolioId}/positions?${params.toString()}`
    );
    return response.data.positions || [];
  }

  async addPosition(
    portfolioId: string,
    data: AddPositionRequest
  ): Promise<Position> {
    const response = await apiClient.post(
      `${this.baseUrl}/${portfolioId}/positions`,
      data
    );
    return response.data.position;
  }

  async updatePosition(
    portfolioId: string,
    positionId: string,
    data: Partial<AddPositionRequest>
  ): Promise<Position> {
    const response = await apiClient.put(
      `${this.baseUrl}/${portfolioId}/positions/${positionId}`,
      data
    );
    return response.data.position;
  }

  async closePosition(
    portfolioId: string,
    positionId: string,
    data: ClosePositionRequest
  ): Promise<Position> {
    const response = await apiClient.put(
      `${this.baseUrl}/${portfolioId}/positions/${positionId}/close`,
      data
    );
    return response.data.position;
  }

  async deletePosition(portfolioId: string, positionId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${portfolioId}/positions/${positionId}`);
  }

  // Analytics and Reporting
  async getPortfolioAnalytics(
    portfolioId: string,
    timeframe?: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'
  ): Promise<PortfolioAnalytics> {
    const params = timeframe ? `?timeframe=${timeframe}` : '';
    const response = await apiClient.get(
      `${this.baseUrl}/${portfolioId}/analytics${params}`
    );
    return response.data.analytics;
  }

  async exportPortfolio(
    portfolioId: string,
    format: 'pdf' | 'csv' | 'json' = 'pdf'
  ): Promise<Blob> {
    const response = await apiClient.get(
      `${this.baseUrl}/${portfolioId}/export?format=${format}`,
      { responseType: 'blob' }
    );
    return response.data;
  }

  // Portfolio Synchronization
  async syncPortfolio(portfolioId: string): Promise<PortfolioDetail> {
    const response = await apiClient.post(`${this.baseUrl}/${portfolioId}/sync`);
    return response.data.portfolio;
  }

  async syncAllPortfolios(): Promise<PortfolioSummary[]> {
    const response = await apiClient.post(`${this.baseUrl}/sync-all`);
    return response.data.portfolios;
  }

  // Risk Management
  async getRiskMetrics(portfolioId: string) {
    const response = await apiClient.get(`${this.baseUrl}/${portfolioId}/risk`);
    return response.data.riskMetrics;
  }

  async getPortfolioGreeks(portfolioId: string) {
    const response = await apiClient.get(`${this.baseUrl}/${portfolioId}/greeks`);
    return response.data.greeks;
  }

  // Performance Tracking
  async getPerformanceMetrics(portfolioId: string, period?: string) {
    const params = period ? `?period=${period}` : '';
    const response = await apiClient.get(
      `${this.baseUrl}/${portfolioId}/performance${params}`
    );
    return response.data.performance;
  }

  // Utility Methods
  async getAvailableStrategies(): Promise<string[]> {
    const response = await apiClient.get('/api/strategies');
    return response.data.strategies;
  }

  async validatePosition(data: AddPositionRequest): Promise<{
    isValid: boolean;
    errors?: string[];
    warnings?: string[];
  }> {
    const response = await apiClient.post('/api/validate-position', data);
    return response.data;
  }

  // Batch Operations
  async bulkCreatePositions(
    portfolioId: string,
    positions: AddPositionRequest[]
  ): Promise<Position[]> {
    const response = await apiClient.post(
      `${this.baseUrl}/${portfolioId}/positions/bulk`,
      { positions }
    );
    return response.data.positions;
  }

  async bulkClosePositions(
    portfolioId: string,
    positionIds: string[],
    closeData: ClosePositionRequest
  ): Promise<Position[]> {
    const response = await apiClient.put(
      `${this.baseUrl}/${portfolioId}/positions/bulk-close`,
      { positionIds, ...closeData }
    );
    return response.data.positions;
  }
}

// Export singleton instance
export const portfolioService = new PortfolioService();