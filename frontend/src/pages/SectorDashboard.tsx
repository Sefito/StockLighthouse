/**
 * Sector dashboard page with heatmap
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSectors } from '../services/api';
import { SectorHeatmap } from '../components/SectorHeatmap';
import type { SectorSummary } from '../types';
import './SectorDashboard.css';

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
      <div className="sector-dashboard">
        <div className="loading">Loading sectors...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sector-dashboard">
        <div className="error">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/')}>Go Home</button>
        </div>
      </div>
    );
  }

  // Calculate total stats
  const totalStocks = sectors.reduce((sum, s) => sum + s.count, 0);
  const avgPE = sectors
    .filter(s => s.median_pe !== null)
    .reduce((sum, s, _, arr) => sum + (s.median_pe || 0) / arr.length, 0);

  return (
    <div className="sector-dashboard" data-testid="sector-dashboard">
      <div className="dashboard-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← Home
        </button>
        <h1>Sector Dashboard</h1>
        <p className="dashboard-description">
          Explore market sectors with aggregated metrics and top performers
        </p>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-label">Total Sectors</div>
          <div className="stat-value">{sectors.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Stocks</div>
          <div className="stat-value">{totalStocks}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Average P/E</div>
          <div className="stat-value">{avgPE.toFixed(2)}</div>
        </div>
      </div>

      <div className="legend">
        <h3>P/E Ratio Color Legend</h3>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
            <span>&lt; 15 (Undervalued)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#fbbf24' }}></div>
            <span>15-25 (Fair)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>25-35 (Moderate)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
            <span>&gt; 35 (Overvalued)</span>
          </div>
        </div>
      </div>

      <SectorHeatmap sectors={sectors} />
    </div>
  );
}
