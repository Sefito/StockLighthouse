/**
 * Sector heatmap component using tiles
 */
import { useNavigate } from 'react-router-dom';
import type { SectorSummary } from '../types';
import './SectorHeatmap.css';

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
    <div className="sector-heatmap" data-testid="sector-heatmap">
      {sectors.map((sector) => (
        <div
          key={sector.sector}
          className="sector-tile"
          style={{ 
            backgroundColor: getPEColor(sector.median_pe),
            borderColor: getPEColor(sector.median_pe),
          }}
          onClick={() => navigate(`/sector/${encodeURIComponent(sector.sector)}`)}
          data-testid={`sector-tile-${sector.sector}`}
        >
          <div className="tile-header">
            <h3>{sector.sector}</h3>
            <div className="tile-count">{sector.count} stocks</div>
          </div>
          <div className="tile-metrics">
            <div className="tile-metric">
              <div className="metric-label">Median P/E</div>
              <div className="metric-value">
                {sector.median_pe ? sector.median_pe.toFixed(2) : 'N/A'}
              </div>
            </div>
            <div className="tile-metric">
              <div className="metric-label">Median Market Cap</div>
              <div className="metric-value">
                {formatMarketCap(sector.median_market_cap)}
              </div>
            </div>
            <div className="tile-metric">
              <div className="metric-label">Weighted P/E</div>
              <div className="metric-value">
                {sector.weighted_avg_pe ? sector.weighted_avg_pe.toFixed(2) : 'N/A'}
              </div>
            </div>
          </div>
          <div className="tile-footer">
            <div className="top-tickers">
              Top: {sector.top_tickers.slice(0, 3).map(t => t.symbol).join(', ')}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
