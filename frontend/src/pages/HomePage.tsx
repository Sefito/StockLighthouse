/**
 * Home page with search functionality
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  CircularProgress,
  Button,
} from '@mui/material';
import { SearchBar } from '../components/SearchBar';
import { searchStocks } from '../services/api';
import type { Stock } from '../types';

export function HomePage() {
  const [popularStocks, setPopularStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPopular = async () => {
      try {
        const stocks = await searchStocks('');
        setPopularStocks(stocks.slice(0, 10));
      } catch (error) {
        console.error('Failed to load popular stocks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPopular();
  }, []);

  const formatMarketCap = (value: number | null) => {
    if (value === null) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    return `$${(value / 1e6).toFixed(2)}M`;
  };

  return (
    <Container maxWidth="lg" data-testid="home-page">
      <Box sx={{ py: 6 }}>
        {/* Hero Section */}
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography variant="h1" gutterBottom sx={{ color: 'primary.main' }}>
            StockLighthouse
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Explore stock data and sector analysis
          </Typography>
        </Box>

        {/* Search Section */}
        <Box sx={{ mb: 6, maxWidth: '600px', mx: 'auto' }}>
          <SearchBar />
        </Box>

        {/* Popular Stocks Section */}
        <Box sx={{ mb: 6 }}>
          <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
            Popular Stocks
          </Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3} data-testid="stock-list">
              {popularStocks.map((stock) => (
                <Grid key={stock.symbol} size={{ xs: 12, sm: 6, md: 4 }}>
                  <Card
                    sx={{
                      height: '100%',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 6,
                      },
                    }}
                    data-testid={`stock-card-${stock.symbol}`}
                  >
                    <CardActionArea
                      onClick={() => navigate(`/stock/${stock.symbol}`)}
                      sx={{ height: '100%' }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 2,
                          }}
                        >
                          <Typography variant="h6" component="h3">
                            {stock.symbol}
                          </Typography>
                          {stock.price && (
                            <Typography variant="h6" color="primary">
                              ${stock.price.toFixed(2)}
                            </Typography>
                          )}
                        </Box>

                        <Box sx={{ mb: 2 }}>
                          {stock.sector && (
                            <Typography variant="body2" color="text.secondary">
                              {stock.sector}
                            </Typography>
                          )}
                          {stock.market_cap && (
                            <Typography variant="body2" color="text.secondary">
                              {formatMarketCap(stock.market_cap)}
                            </Typography>
                          )}
                        </Box>

                        {stock.change_pct !== null && (
                          <Typography
                            variant="body2"
                            fontWeight="600"
                            sx={{
                              color: stock.change_pct >= 0 ? 'success.main' : 'error.main',
                            }}
                          >
                            {stock.change_pct >= 0 ? '+' : ''}
                            {stock.change_pct.toFixed(2)}%
                          </Typography>
                        )}
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>

        {/* Quick Links Section */}
        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/sectors')}
            sx={{ textTransform: 'none', px: 4 }}
          >
            View Sector Dashboard →
          </Button>
        </Box>
      </Box>
    </Container>
  );
}
