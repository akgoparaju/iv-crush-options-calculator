import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { ScreeningCriteria, ScreeningFilter, ScreeningField, FilterOperator } from '../../types/screening';
import { X, Plus, Play, Save } from 'lucide-react';

interface ScreeningFiltersProps {
  onClose: () => void;
  onRunScreening: (criteria: ScreeningCriteria) => void;
  isRunning: boolean;
}

const ScreeningFilters: React.FC<ScreeningFiltersProps> = ({
  onClose,
  onRunScreening,
  isRunning,
}) => {
  const [screeningName, setScreeningName] = useState('');
  const [filters, setFilters] = useState<ScreeningFilter[]>([]);
  const [activeTab, setActiveTab] = useState<'basic' | 'options' | 'technical'>('basic');

  const fieldOptions: Record<string, ScreeningField[]> = {
    basic: ['symbol', 'price', 'marketCap', 'volume', 'avgVolume', 'sector', 'industry'],
    options: ['impliedVolatility', 'historicalVolatility', 'ivRank', 'ivPercentile', 'optionsVolume', 'putCallRatio', 'earningsDate', 'daysToEarnings'],
    technical: ['rsi', 'macd', 'bollinger', 'support', 'resistance', 'trend', 'pe', 'eps', 'beta'],
  };

  const operatorOptions: { value: FilterOperator; label: string }[] = [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Not Equals' },
    { value: 'greater_than', label: 'Greater Than' },
    { value: 'greater_than_or_equal', label: 'Greater Than or Equal' },
    { value: 'less_than', label: 'Less Than' },
    { value: 'less_than_or_equal', label: 'Less Than or Equal' },
    { value: 'between', label: 'Between' },
    { value: 'in', label: 'In List' },
    { value: 'contains', label: 'Contains' },
  ];

  const addFilter = () => {
    const newFilter: ScreeningFilter = {
      field: fieldOptions[activeTab][0],
      operator: 'greater_than',
      value: '',
      logicalOperator: filters.length > 0 ? 'AND' : undefined,
    };
    setFilters([...filters, newFilter]);
  };

  const updateFilter = (index: number, updates: Partial<ScreeningFilter>) => {
    const updatedFilters = filters.map((filter, i) =>
      i === index ? { ...filter, ...updates } : filter
    );
    setFilters(updatedFilters);
  };

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index));
  };

  const handleRunScreening = () => {
    const criteria: ScreeningCriteria = {
      id: '',
      name: screeningName || 'Custom Screen',
      description: 'Custom screening criteria',
      filters,
      sorting: [{ field: 'score' as ScreeningField, direction: 'desc', priority: 1 }],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isPublic: false,
    };

    onRunScreening(criteria);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const getFieldLabel = (field: ScreeningField): string => {
    return field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const tabs = [
    { id: 'basic', name: 'Basic', description: 'Price, volume, market cap' },
    { id: 'options', name: 'Options', description: 'IV, Greeks, earnings' },
    { id: 'technical', name: 'Technical', description: 'Indicators, fundamentals' },
  ] as const;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Create Custom Screen</h2>
            <p className="text-sm text-slate-600">Build your own stock screening criteria</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="p-2"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Tab Navigation */}
          <div className="w-48 border-r border-slate-200 p-4">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700 border border-primary-200'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium">{tab.name}</div>
                  <div className="text-xs text-slate-500 mt-1">{tab.description}</div>
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-6">
              {/* Screening Name */}
              <div>
                <Input
                  label="Screening Name"
                  placeholder="e.g., High IV Earnings Plays"
                  value={screeningName}
                  onChange={(e) => setScreeningName(e.target.value)}
                />
              </div>

              {/* Filters */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-slate-900">
                    Filters ({activeTab} criteria)
                  </h3>
                  <Button
                    onClick={addFilter}
                    size="sm"
                    variant="outline"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Filter
                  </Button>
                </div>

                {filters.length === 0 ? (
                  <div className="text-center py-8 border-2 border-dashed border-slate-300 rounded-lg">
                    <p className="text-slate-600 mb-4">No filters added yet</p>
                    <Button onClick={addFilter} size="sm">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Your First Filter
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filters.map((filter, index) => (
                      <Card key={index} className="p-4">
                        <div className="flex items-center space-x-4">
                          {index > 0 && (
                            <div className="flex-shrink-0">
                              <select
                                value={filter.logicalOperator || 'AND'}
                                onChange={(e) => updateFilter(index, { 
                                  logicalOperator: e.target.value as 'AND' | 'OR' 
                                })}
                                className="text-sm border border-slate-300 rounded px-2 py-1"
                              >
                                <option value="AND">AND</option>
                                <option value="OR">OR</option>
                              </select>
                            </div>
                          )}
                          
                          <div className="flex-1 grid grid-cols-4 gap-4">
                            {/* Field */}
                            <div>
                              <select
                                value={filter.field}
                                onChange={(e) => updateFilter(index, { 
                                  field: e.target.value as ScreeningField 
                                })}
                                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
                              >
                                {fieldOptions[activeTab].map((field) => (
                                  <option key={field} value={field}>
                                    {getFieldLabel(field)}
                                  </option>
                                ))}
                              </select>
                            </div>

                            {/* Operator */}
                            <div>
                              <select
                                value={filter.operator}
                                onChange={(e) => updateFilter(index, { 
                                  operator: e.target.value as FilterOperator 
                                })}
                                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
                              >
                                {operatorOptions.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </div>

                            {/* Value */}
                            <div>
                              {filter.operator === 'between' ? (
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="text"
                                    placeholder="Min"
                                    value={Array.isArray(filter.value) ? filter.value[0] || '' : ''}
                                    onChange={(e) => {
                                      const currentValue = Array.isArray(filter.value) ? filter.value : ['', ''];
                                      updateFilter(index, { 
                                        value: [e.target.value, currentValue[1] || ''] 
                                      });
                                    }}
                                    className="w-full text-sm border border-slate-300 rounded px-3 py-2"
                                  />
                                  <input
                                    type="text"
                                    placeholder="Max"
                                    value={Array.isArray(filter.value) ? filter.value[1] || '' : ''}
                                    onChange={(e) => {
                                      const currentValue = Array.isArray(filter.value) ? filter.value : ['', ''];
                                      updateFilter(index, { 
                                        value: [currentValue[0] || '', e.target.value] 
                                      });
                                    }}
                                    className="w-full text-sm border border-slate-300 rounded px-3 py-2"
                                  />
                                </div>
                              ) : (
                                <input
                                  type="text"
                                  placeholder="Value"
                                  value={Array.isArray(filter.value) ? filter.value.join(',') : filter.value}
                                  onChange={(e) => updateFilter(index, { value: e.target.value })}
                                  className="w-full text-sm border border-slate-300 rounded px-3 py-2"
                                />
                              )}
                            </div>

                            {/* Remove */}
                            <div>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removeFilter(index)}
                                className="p-1 text-red-600 hover:bg-red-50"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Quick Filter Templates */}
              <div>
                <h4 className="font-medium text-slate-900 mb-3">Quick Templates</h4>
                <div className="flex flex-wrap gap-2">
                  {activeTab === 'basic' && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'price', operator: 'greater_than', value: '10' },
                            { field: 'volume', operator: 'greater_than', value: '1000000', logicalOperator: 'AND' },
                          ]);
                        }}
                      >
                        Liquid Stocks ($10+, 1M+ volume)
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'marketCap', operator: 'greater_than', value: '1000000000' },
                            { field: 'price', operator: 'between', value: ['20', '200'] },
                          ]);
                        }}
                      >
                        Large Cap ($20-200)
                      </Button>
                    </>
                  )}
                  {activeTab === 'options' && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'impliedVolatility', operator: 'greater_than', value: '0.5' },
                            { field: 'ivRank', operator: 'greater_than', value: '75', logicalOperator: 'AND' },
                          ]);
                        }}
                      >
                        High IV ({'>'}50%, IV Rank {'>'} 75)
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'daysToEarnings', operator: 'between', value: ['0', '7'] },
                            { field: 'optionsVolume', operator: 'greater_than', value: '10000', logicalOperator: 'AND' },
                          ]);
                        }}
                      >
                        Earnings This Week
                      </Button>
                    </>
                  )}
                  {activeTab === 'technical' && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'rsi', operator: 'less_than', value: '30' },
                          ]);
                        }}
                      >
                        Oversold (RSI {'<'} 30)
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFilters([
                            { field: 'pe', operator: 'between', value: ['10', '20'] },
                            { field: 'beta', operator: 'less_than', value: '1.5', logicalOperator: 'AND' },
                          ]);
                        }}
                      >
                        Value Stocks (PE 10-20, Beta {'<'} 1.5)
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-200">
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {filters.length} filter{filters.length !== 1 ? 's' : ''}
            </Badge>
            {filters.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters([])}
              >
                Clear All
              </Button>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              disabled={filters.length === 0}
            >
              <Save className="w-4 h-4 mr-2" />
              Save Screen
            </Button>
            <Button
              onClick={handleRunScreening}
              loading={isRunning}
              disabled={filters.length === 0 || isRunning}
            >
              <Play className="w-4 h-4 mr-2" />
              Run Screen
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ScreeningFilters;