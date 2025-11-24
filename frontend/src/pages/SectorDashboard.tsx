/**
 * Sector dashboard page with heatmap
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getSectors } from '../services/api';
import { SectorHeatmap } from '../components/SectorHeatmap';
import type { SectorSummary } from '../types';

export function SectorDashboard() {
  const [sectors, setSectors] = useState<SectorSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSectors = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getSectors();
        setSectors(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sectors');
      } finally {
        setLoading(false);
      }
    };

    fetchSectors();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 6 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
          <Button variant="contained" onClick={() => navigate('/')}>
            Go Home
          </Button>
        </Box>
      </Container>
    );
  }

  // Calculate total stats
  const totalStocks = sectors.reduce((sum, s) => sum + s.count, 0);
  const avgPE = sectors
    .filter(s => s.median_pe !== null)
    .reduce((sum, s, _, arr) => sum + (s.median_pe || 0) / arr.length, 0);

  return (
    <Container maxWidth="lg" data-testid="sector-dashboard">
      <Box sx={{ py: 4 }}>
        {/* Dashboard Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/')}
            sx={{ mb: 2 }}
          >
            Home
          </Button>
          <Typography variant="h3" gutterBottom>
            Sector Dashboard
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Explore market sectors with aggregated metrics and top performers
          </Typography>
        </Box>

        {/* Dashboard Stats */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Total Sectors
                </Typography>
                <Typography variant="h3" color="primary">
                  {sectors.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Total Stocks
                </Typography>
                <Typography variant="h3" color="primary">
                  {totalStocks}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Average P/E
                </Typography>
                <Typography variant="h3" color="primary">
                  {avgPE.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Legend */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              P/E Ratio Color Legend
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: '#10b981',
                      borderRadius: 1,
                    }}
                  />
                  <Typography variant="body2">&lt; 15 (Undervalued)</Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: '#fbbf24',
                      borderRadius: 1,
                    }}
                  />
                  <Typography variant="body2">15-25 (Fair)</Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: '#f59e0b',
                      borderRadius: 1,
                    }}
                  />
                  <Typography variant="body2">25-35 (Moderate)</Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: '#ef4444',
                      borderRadius: 1,
                    }}
                  />
                  <Typography variant="body2">&gt; 35 (Overvalued)</Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Sector Heatmap */}
        <SectorHeatmap sectors={sectors} />
      </Box>
    </Container>
  );
}
