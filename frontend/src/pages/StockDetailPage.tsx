/**
 * Stock detail page with KPI table and charts
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStockDetails } from '../services/api';
import { KPITable } from '../components/KPITable';
import { PriceChart } from '../components/PriceChart';
import { PEChart } from '../components/PEChart';
import type { Stock } from '../types';
import './StockDetailPage.css';

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
      <div className="stock-detail-page">
        <div className="loading">Loading stock details...</div>
      </div>
    );
  }

  if (error || !stock) {
    return (
      <div className="stock-detail-page">
        <div className="error">
          <h2>Error</h2>
          <p>{error || 'Stock not found'}</p>
          <button onClick={() => navigate('/')}>Go Home</button>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-detail-page" data-testid="stock-detail-page">
      <div className="page-header">
        <button onClick={() => navigate(-1)} className="back-button">
          ← Back
        </button>
        <div className="stock-title">
          <h1>{stock.symbol}</h1>
          {stock.industry && <p className="stock-industry">{stock.industry}</p>}
        </div>
      </div>

      <div className="content-grid">
        <div className="kpi-section">
          <KPITable stock={stock} />
        </div>

        <div className="charts-section">
          <PriceChart symbol={stock.symbol} />
          <PEChart symbol={stock.symbol} />
        </div>
      </div>

      {stock.sector && (
        <div className="sector-link">
          <button 
            onClick={() => navigate(`/sector/${encodeURIComponent(stock.sector!)}`)}
            className="sector-button"
          >
            View {stock.sector} Sector →
          </button>
        </div>
      )}
    </div>
  );
}
