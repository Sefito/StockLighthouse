/**
 * Price history chart component using Plotly
 */
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getStockHistory } from '../services/api';
import type { HistoryData } from '../types';
import './PriceChart.css';

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
    return <div className="chart-loading">Loading price history...</div>;
  }

  if (error) {
    return <div className="chart-error">Error: {error}</div>;
  }

  if (!data || data.dates.length === 0) {
    return <div className="chart-error">No price history available</div>;
  }

  return (
    <div className="price-chart" data-testid="price-chart">
      <h3>Price History (30 Days)</h3>
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
    </div>
  );
}
