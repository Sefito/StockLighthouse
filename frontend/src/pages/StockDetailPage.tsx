/**
 * Stock detail page with KPI table and charts
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getStockDetails } from '../services/api';
import { KPITable } from '../components/KPITable';
import { PriceChart } from '../components/PriceChart';
import { PEChart } from '../components/PEChart';
import type { Stock } from '../types';

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const [stock, setStock] = useState<Stock | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;

    const fetchStock = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getStockDetails(symbol);
        setStock(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stock details');
      } finally {
        setLoading(false);
      }
    };

    fetchStock();
  }, [symbol]);

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !stock) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 6 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            {error || 'Stock not found'}
          </Alert>
          <Button variant="contained" onClick={() => navigate('/')}>
            Go Home
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" data-testid="stock-detail-page">
      <Box sx={{ py: 4 }}>
        {/* Page Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(-1)}
            sx={{ mb: 2 }}
          >
            Back
          </Button>
          <Typography variant="h3" gutterBottom>
            {stock.symbol}
          </Typography>
          {stock.industry && (
            <Typography variant="h6" color="text.secondary">
              {stock.industry}
            </Typography>
          )}
        </Box>

        {/* Content Grid */}
        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 5 }}>
            <KPITable stock={stock} />
          </Grid>

          <Grid size={{ xs: 12, md: 7 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <PriceChart symbol={stock.symbol} />
              <PEChart symbol={stock.symbol} />
            </Box>
          </Grid>
        </Grid>

        {/* Sector Link */}
        {stock.sector && (
          <Box sx={{ mt: 6, textAlign: 'center' }}>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate(`/sector/${encodeURIComponent(stock.sector!)}`)}
              sx={{ textTransform: 'none', px: 4 }}
            >
              View {stock.sector} Sector →
            </Button>
          </Box>
        )}
      </Box>
    </Container>
  );
}
