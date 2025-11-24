/**
 * Sector heatmap component using tiles
 */
import { useNavigate } from 'react-router-dom';
import { 
  Grid,
  Card, 
  CardContent, 
  CardActionArea, 
  Typography, 
  Box, 
  Chip 
} from '@mui/material';
import type { SectorSummary } from '../types';

interface SectorHeatmapProps {
  sectors: SectorSummary[];
}

export function SectorHeatmap({ sectors }: SectorHeatmapProps) {
  const navigate = useNavigate();

  const formatMarketCap = (value: number | null) => {
    if (value === null) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    return `$${(value / 1e6).toFixed(1)}M`;
  };

  const getPEColor = (pe: number | null) => {
    if (pe === null) return '#e0e0e0';
    if (pe < 15) return '#10b981';
    if (pe < 25) return '#fbbf24';
    if (pe < 35) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <Grid container spacing={3} data-testid="sector-heatmap">
      {sectors.map((sector) => (
        <Grid key={sector.sector} size={{ xs: 12, sm: 6, md: 4 }}>
          <Card
            sx={{
              height: '100%',
              backgroundColor: getPEColor(sector.median_pe),
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 6,
              },
            }}
            data-testid={`sector-tile-${sector.sector}`}
          >
            <CardActionArea
              onClick={() => navigate(`/sector/${encodeURIComponent(sector.sector)}`)}
              sx={{ height: '100%' }}
            >
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" component="h3" gutterBottom>
                    {sector.sector}
                  </Typography>
                  <Chip
                    label={`${sector.count} stocks`}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      color: 'white',
                    }}
                  />
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box>
                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                      Median P/E
                    </Typography>
                    <Typography variant="body1" fontWeight="600">
                      {sector.median_pe ? sector.median_pe.toFixed(2) : 'N/A'}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                      Median Market Cap
                    </Typography>
                    <Typography variant="body1" fontWeight="600">
                      {formatMarketCap(sector.median_market_cap)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                      Weighted P/E
                    </Typography>
                    <Typography variant="body1" fontWeight="600">
                      {sector.weighted_avg_pe ? sector.weighted_avg_pe.toFixed(2) : 'N/A'}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.2)' }}>
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>
                    Top: {sector.top_tickers.slice(0, 3).map(t => t.symbol).join(', ')}
                  </Typography>
                </Box>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
