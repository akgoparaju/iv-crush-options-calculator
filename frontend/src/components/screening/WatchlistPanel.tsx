import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { Watchlist, WatchlistItem, CreateWatchlistRequest } from '../../types/screening';
import { screeningService } from '../../services/screeningService';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { 
  Plus, 
  Search, 
  Star, 
  TrendingUp, 
  TrendingDown, 
  Eye, 
  Edit3, 
  Trash2, 
  Bell, 
  BellOff,
  Download,
  Upload
} from 'lucide-react';

interface WatchlistPanelProps {
  onSymbolSelect?: (symbol: string) => void;
}

const WatchlistPanel: React.FC<WatchlistPanelProps> = ({ onSymbolSelect }) => {
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [newWatchlistDescription, setNewWatchlistDescription] = useState('');

  const queryClient = useQueryClient();

  const { data: watchlists, isLoading: watchlistsLoading } = useQuery({
    queryKey: ['watchlists'],
    queryFn: screeningService.getWatchlists,
  });

  const { data: watchlistData, isLoading: watchlistItemsLoading } = useQuery({
    queryKey: ['watchlist', selectedWatchlistId],
    queryFn: () => selectedWatchlistId ? screeningService.getWatchlist(selectedWatchlistId) : null,
    enabled: !!selectedWatchlistId,
  });

  const createWatchlistMutation = useMutation({
    mutationFn: (request: CreateWatchlistRequest) => screeningService.createWatchlist(request),
    onSuccess: (newWatchlist) => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
      setSelectedWatchlistId(newWatchlist.id);
      setIsCreating(false);
      setNewWatchlistName('');
      setNewWatchlistDescription('');
    },
  });

  const deleteWatchlistMutation = useMutation({
    mutationFn: (watchlistId: string) => screeningService.deleteWatchlist(watchlistId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] });
      setSelectedWatchlistId(null);
    },
  });

  const removeSymbolMutation = useMutation({
    mutationFn: ({ watchlistId, symbol }: { watchlistId: string; symbol: string }) =>
      screeningService.removeSymbolFromWatchlist(watchlistId, symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist', selectedWatchlistId] });
    },
  });

  // Select first watchlist by default
  useEffect(() => {
    if (watchlists && watchlists.length > 0 && !selectedWatchlistId) {
      setSelectedWatchlistId(watchlists[0].id);
    }
  }, [watchlists, selectedWatchlistId]);

  const filteredItems = watchlistData?.items?.filter(item =>
    item.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleCreateWatchlist = () => {
    if (newWatchlistName.trim()) {
      createWatchlistMutation.mutate({
        name: newWatchlistName.trim(),
        description: newWatchlistDescription.trim() || undefined,
        is_default: false,
      });
    }
  };

  const selectedWatchlist = watchlists?.find(w => w.id === selectedWatchlistId);

  if (watchlistsLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-12 bg-slate-200 rounded-lg"></div>
        <div className="animate-pulse h-64 bg-slate-200 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Watchlist Selection */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">My Watchlists</h3>
          <Button
            size="sm"
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New List
          </Button>
        </div>

        {/* Create New Watchlist Form */}
        {isCreating && (
          <div className="mb-4 p-4 bg-slate-50 rounded-lg border">
            <div className="space-y-3">
              <Input
                placeholder="Watchlist name"
                value={newWatchlistName}
                onChange={(e) => setNewWatchlistName(e.target.value)}
              />
              <Input
                placeholder="Description (optional)"
                value={newWatchlistDescription}
                onChange={(e) => setNewWatchlistDescription(e.target.value)}
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleCreateWatchlist}
                  loading={createWatchlistMutation.isPending}
                  disabled={!newWatchlistName.trim()}
                >
                  Create
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setIsCreating(false);
                    setNewWatchlistName('');
                    setNewWatchlistDescription('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Watchlist Tabs */}
        <div className="flex gap-2 flex-wrap">
          {watchlists?.map((watchlist) => (
            <Button
              key={watchlist.id}
              variant={selectedWatchlistId === watchlist.id ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setSelectedWatchlistId(watchlist.id)}
              className="flex items-center gap-2"
            >
              {watchlist.is_default && <Star className="w-3 h-3 text-yellow-500" />}
              {watchlist.name}
              <Badge variant="secondary" className="ml-1">
                {watchlist.symbol_count || 0}
              </Badge>
            </Button>
          ))}
        </div>
      </Card>

      {/* Selected Watchlist Content */}
      {selectedWatchlist && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-slate-900">{selectedWatchlist.name}</h3>
                {selectedWatchlist.is_default && <Star className="w-5 h-5 text-yellow-500" />}
              </div>
              {selectedWatchlist.description && (
                <p className="text-slate-600 mt-1">{selectedWatchlist.description}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                <span>{selectedWatchlist.symbol_count || 0} symbols</span>
                <span>Updated {new Date(selectedWatchlist.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Upload className="w-4 h-4 mr-2" />
                Import
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => deleteWatchlistMutation.mutate(selectedWatchlist.id)}
                loading={deleteWatchlistMutation.isPending}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6">
            <Input
              placeholder="Search symbols..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={Search}
            />
          </div>

          {/* Watchlist Items */}
          {watchlistItemsLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse h-16 bg-slate-200 rounded-lg"></div>
              ))}
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-slate-400 mb-4">
                <Star className="w-12 h-12 mx-auto" />
              </div>
              <h4 className="text-lg font-medium text-slate-900 mb-2">
                {searchQuery ? 'No symbols found' : 'No symbols in watchlist'}
              </h4>
              <p className="text-slate-600 mb-4">
                {searchQuery 
                  ? 'Try adjusting your search terms.' 
                  : 'Add symbols to start tracking them.'
                }
              </p>
              {!searchQuery && (
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Symbol
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredItems.map((item) => (
                <div
                  key={item.symbol}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-slate-900">{item.symbol}</span>
                          {item.change_percent !== undefined && (
                            <div className="flex items-center">
                              {item.change_percent >= 0 ? (
                                <TrendingUp className="w-3 h-3 text-green-500" />
                              ) : (
                                <TrendingDown className="w-3 h-3 text-red-500" />
                              )}
                            </div>
                          )}
                        </div>
                        {item.name && (
                          <div className="text-sm text-slate-500 truncate max-w-48">
                            {item.name}
                          </div>
                        )}
                        {item.notes && (
                          <div className="text-xs text-slate-600 mt-1 italic">
                            {item.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    {item.current_price !== undefined && (
                      <div className="text-right">
                        <div className="font-medium text-slate-900">
                          {formatCurrency(item.current_price)}
                        </div>
                        {item.change_percent !== undefined && (
                          <div className={`text-sm ${
                            item.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {item.change_percent >= 0 ? '+' : ''}{formatPercentage(item.change_percent)}
                          </div>
                        )}
                      </div>
                    )}

                    <div className="flex items-center space-x-2">
                      {item.alerts && item.alerts.length > 0 && (
                        <div className="flex items-center">
                          {item.alerts.some(alert => alert.is_active) ? (
                            <Bell className="w-4 h-4 text-blue-600" />
                          ) : (
                            <BellOff className="w-4 h-4 text-slate-400" />
                          )}
                          <Badge variant="outline" className="text-xs ml-1">
                            {item.alerts.length}
                          </Badge>
                        </div>
                      )}

                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onSymbolSelect?.(item.symbol)}
                        className="p-1"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="ghost"
                        className="p-1"
                      >
                        <Edit3 className="w-4 h-4" />
                      </Button>

                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeSymbolMutation.mutate({
                          watchlistId: selectedWatchlist.id,
                          symbol: item.symbol
                        })}
                        loading={removeSymbolMutation.isPending}
                        className="p-1 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default WatchlistPanel;