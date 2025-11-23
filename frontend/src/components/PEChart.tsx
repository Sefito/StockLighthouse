/**
 * P/E Distribution chart component using Plotly
 */
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getPEDistribution } from '../services/api';
import type { PEDistribution } from '../types';
import './PEChart.css';

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
    return <div className="chart-loading">Loading P/E distribution...</div>;
  }

  if (error) {
    return <div className="chart-error">Error: {error}</div>;
  }

  if (!data || data.pe_ratios.length === 0) {
    return <div className="chart-error">No P/E distribution data available</div>;
  }

  // Highlight current stock
  const colors = data.symbols.map(s => 
    s === symbol ? '#ef4444' : '#4a90e2'
  );

  return (
    <div className="pe-chart" data-testid="pe-chart">
      <h3>P/E Ratio Distribution in {data.sector || 'Sector'}</h3>
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
    </div>
  );
}
