/**
 * Price history chart component using Plotly
 */
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, CircularProgress, Alert, Card, CardContent } from '@mui/material';
import { getStockHistory } from '../services/api';
import type { HistoryData } from '../types';

interface PriceChartProps {
  symbol: string;
}

export function PriceChart({ symbol }: PriceChartProps) {
  const [data, setData] = useState<HistoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const history = await getStockHistory(symbol);
        setData(history);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load price history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [symbol]);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.dates.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No price history available</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="price-chart">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Price History (30 Days)
        </Typography>
        <Box>
          {/* eslint-disable @typescript-eslint/no-explicit-any */}
          <Plot
            data={[
              {
                x: data.dates,
                y: data.prices,
                type: 'scatter',
                mode: 'lines',
                line: { color: '#4a90e2', width: 2 },
              } as any,
            ]}
            layout={{
              autosize: true,
              margin: { l: 50, r: 20, t: 20, b: 40 },
              xaxis: { 
                title: 'Date' as any,
                showgrid: true,
                gridcolor: '#f0f0f0',
              },
              yaxis: { 
                title: 'Price ($)' as any,
                showgrid: true,
                gridcolor: '#f0f0f0',
              },
              hovermode: 'x unified',
              paper_bgcolor: 'white',
              plot_bgcolor: 'white',
            } as any}
            config={{ 
              responsive: true,
              displayModeBar: false,
            }}
            style={{ width: '100%', height: '400px' }}
          />
          {/* eslint-enable @typescript-eslint/no-explicit-any */}
        </Box>
      </CardContent>
    </Card>
  );
}
