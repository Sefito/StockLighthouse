/**
 * P/E Distribution chart component using Plotly
 */
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, CircularProgress, Alert, Card, CardContent } from '@mui/material';
import { getPEDistribution } from '../services/api';
import type { PEDistribution } from '../types';

interface PEChartProps {
  symbol: string;
}

export function PEChart({ symbol }: PEChartProps) {
  const [data, setData] = useState<PEDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPE = async () => {
      setLoading(true);
      setError(null);
      try {
        const peData = await getPEDistribution(symbol);
        setData(peData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load P/E distribution');
      } finally {
        setLoading(false);
      }
    };

    fetchPE();
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

  if (!data || data.pe_ratios.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No P/E distribution data available</Alert>
        </CardContent>
      </Card>
    );
  }

  // Highlight current stock
  const colors = data.symbols.map(s => 
    s === symbol ? '#ef4444' : '#4a90e2'
  );

  return (
    <Card data-testid="pe-chart">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          P/E Ratio Distribution in {data.sector || 'Sector'}
        </Typography>
        <Box>
          {/* eslint-disable @typescript-eslint/no-explicit-any */}
          <Plot
            data={[
              {
                x: data.symbols,
                y: data.pe_ratios,
                type: 'bar',
                marker: { color: colors },
              } as any,
            ]}
            layout={{
              autosize: true,
              margin: { l: 50, r: 20, t: 20, b: 80 },
              xaxis: { 
                title: 'Stock Symbol' as any,
                tickangle: -45,
                showgrid: false,
              },
              yaxis: { 
                title: 'P/E Ratio' as any,
                showgrid: true,
                gridcolor: '#f0f0f0',
              },
              hovermode: 'closest',
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
