/*
 * Screening Dashboard Component for Phase 5.3
 * Market screening and alert management interface
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  CircularProgress,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as RunIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  NotificationsActive as AlertIcon,
  Assessment as AnalyticsIcon
} from '@mui/icons-material';

// Types
interface Screen {
  id: string;
  name: string;
  description?: string;
  criteria: ScreeningCriteria[];
  frequency: string;
  is_active: boolean;
  alert_threshold: number;
  last_run?: string;
  results_count: number;
}

interface ScreeningCriteria {
  criteria: string;
  operator: string;
  value: number | number[];
  weight: number;
}

interface ScreeningResult {
  symbol: string;
  current_price: number;
  score: number;
  rank: string;
  criteria_scores: Record<string, number>;
  timestamp: string;
}

interface Alert {
  id: string;
  screen_id: string;
  alert_types: string[];
  conditions: Record<string, any>;
  is_active: boolean;
  last_triggered?: string;
  trigger_count: number;
}

const ScreeningDashboard: React.FC = () => {
  // State management
  const [screens, setScreens] = useState<Screen[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [results, setResults] = useState<Record<string, ScreeningResult[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Dialog states
  const [createScreenOpen, setCreateScreenOpen] = useState(false);
  const [runScreenOpen, setRunScreenOpen] = useState(false);
  const [selectedScreen, setSelectedScreen] = useState<string | null>(null);
  
  // Form states
  const [newScreenData, setNewScreenData] = useState({
    name: '',
    description: '',
    frequency: 'hourly',
    alert_threshold: 5
  });

  // Load initial data
  useEffect(() => {
    loadScreens();
    loadAlerts();
  }, []);

  const loadScreens = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/screening/screens', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setScreens(data);
      } else {
        setError('Failed to load screens');
      }
    } catch (err) {
      setError('Error loading screens');
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await fetch('/api/screening/alerts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Error loading alerts:', err);
    }
  };

  const loadScreenResults = async (screenId: string) => {
    try {
      const response = await fetch(`/api/screening/screens/${screenId}/results`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setResults(prev => ({ ...prev, [screenId]: data }));
      }
    } catch (err) {
      console.error('Error loading screen results:', err);
    }
  };

  const createScreen = async () => {
    try {
      setLoading(true);
      
      // Basic criteria for demo - in production would have a criteria builder
      const basicCriteria = [
        {
          criteria: 'iv_percentile',
          operator: '>=',
          value: 60,
          weight: 2.0
        },
        {
          criteria: 'volume',
          operator: '>=',
          value: 1000000,
          weight: 1.0
        }
      ];

      const response = await fetch('/api/screening/screens', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          ...newScreenData,
          criteria: basicCriteria
        })
      });

      if (response.ok) {
        setSuccess('Screen created successfully');
        setCreateScreenOpen(false);
        setNewScreenData({ name: '', description: '', frequency: 'hourly', alert_threshold: 5 });
        loadScreens();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create screen');
      }
    } catch (err) {
      setError('Error creating screen');
    } finally {
      setLoading(false);
    }
  };

  const runScreen = async (screenId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/screening/screens/${screenId}/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(`Screen completed: Found ${data.opportunities_found} opportunities`);
        loadScreens();
        loadScreenResults(screenId);
      } else {
        setError('Failed to run screen');
      }
    } catch (err) {
      setError('Error running screen');
    } finally {
      setLoading(false);
    }
  };

  const toggleScreenActive = async (screenId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/screening/screens/${screenId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ is_active: isActive })
      });

      if (response.ok) {
        setSuccess(`Screen ${isActive ? 'activated' : 'deactivated'}`);
        loadScreens();
      } else {
        setError('Failed to update screen');
      }
    } catch (err) {
      setError('Error updating screen');
    }
  };

  const getRankColor = (rank: string) => {
    switch (rank.toLowerCase()) {
      case 'excellent': return 'success';
      case 'good': return 'info';
      case 'fair': return 'warning';
      case 'poor': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Market Screening Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateScreenOpen(true)}
        >
          Create Screen
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Active Screens
              </Typography>
              <Typography variant="h3">
                {screens.filter(s => s.is_active).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Total Opportunities
              </Typography>
              <Typography variant="h3">
                {screens.reduce((sum, s) => sum + s.results_count, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Active Alerts
              </Typography>
              <Typography variant="h3">
                {alerts.filter(a => a.is_active).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Alerts Triggered
              </Typography>
              <Typography variant="h3">
                {alerts.reduce((sum, a) => sum + a.trigger_count, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Screens Table */}
      <Paper sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ p: 2 }}>
          Your Screens
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Last Run</TableCell>
                <TableCell>Opportunities</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {screens.map((screen) => (
                <TableRow key={screen.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{screen.name}</Typography>
                      {screen.description && (
                        <Typography variant="body2" color="textSecondary">
                          {screen.description}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={screen.is_active ? 'Active' : 'Inactive'}
                      color={screen.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{screen.frequency}</TableCell>
                  <TableCell>
                    {screen.last_run ? new Date(screen.last_run).toLocaleString() : 'Never'}
                  </TableCell>
                  <TableCell>{screen.results_count}</TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => runScreen(screen.id)}
                      color="primary"
                      title="Run Screen"
                    >
                      <RunIcon />
                    </IconButton>
                    <IconButton
                      onClick={() => loadScreenResults(screen.id)}
                      color="info"
                      title="View Results"
                    >
                      <TrendingUpIcon />
                    </IconButton>
                    <IconButton
                      onClick={() => toggleScreenActive(screen.id, !screen.is_active)}
                      color={screen.is_active ? 'warning' : 'success'}
                      title={screen.is_active ? 'Deactivate' : 'Activate'}
                    >
                      <AlertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Recent Results */}
      {Object.entries(results).map(([screenId, screenResults]) => {
        const screen = screens.find(s => s.id === screenId);
        if (!screen || screenResults.length === 0) return null;

        return (
          <Paper key={screenId} sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ p: 2 }}>
              Results for {screen.name}
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Rank</TableCell>
                    <TableCell>Timestamp</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {screenResults.slice(0, 10).map((result, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="subtitle2">{result.symbol}</Typography>
                      </TableCell>
                      <TableCell>${result.current_price.toFixed(2)}</TableCell>
                      <TableCell>{result.score.toFixed(1)}/100</TableCell>
                      <TableCell>
                        <Chip
                          label={result.rank.charAt(0).toUpperCase() + result.rank.slice(1)}
                          color={getRankColor(result.rank) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(result.timestamp).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        );
      })}

      {/* Create Screen Dialog */}
      <Dialog open={createScreenOpen} onClose={() => setCreateScreenOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Screen</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Screen Name"
                value={newScreenData.name}
                onChange={(e) => setNewScreenData({ ...newScreenData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Description"
                value={newScreenData.description}
                onChange={(e) => setNewScreenData({ ...newScreenData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Frequency</InputLabel>
                <Select
                  value={newScreenData.frequency}
                  onChange={(e) => setNewScreenData({ ...newScreenData, frequency: e.target.value })}
                >
                  <MenuItem value="every_5_min">Every 5 minutes</MenuItem>
                  <MenuItem value="every_15_min">Every 15 minutes</MenuItem>
                  <MenuItem value="every_30_min">Every 30 minutes</MenuItem>
                  <MenuItem value="hourly">Hourly</MenuItem>
                  <MenuItem value="daily">Daily</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Alert Threshold"
                value={newScreenData.alert_threshold}
                onChange={(e) => setNewScreenData({ ...newScreenData, alert_threshold: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                This screen will use default criteria (IV Percentile ≥ 60% and Volume ≥ 1M).
                Advanced criteria builder will be available in a future update.
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateScreenOpen(false)}>Cancel</Button>
          <Button 
            onClick={createScreen} 
            variant="contained" 
            disabled={!newScreenData.name || loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notifications */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ScreeningDashboard;