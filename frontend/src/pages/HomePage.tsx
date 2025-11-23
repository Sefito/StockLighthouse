/**
 * Home page with search functionality
 */
import { useState, useEffect } from 'react';
import { SearchBar } from '../components/SearchBar';
import { searchStocks } from '../services/api';
import { useNavigate } from 'react-router-dom';
import type { Stock } from '../types';
import './HomePage.css';

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
    <div className="home-page" data-testid="home-page">
      <div className="hero">
        <h1>StockLighthouse</h1>
        <p>Explore stock data and sector analysis</p>
      </div>

      <div className="search-section">
        <SearchBar />
      </div>

      <div className="popular-stocks">
        <h2>Popular Stocks</h2>
        {loading ? (
          <div className="loading">Loading stocks...</div>
        ) : (
          <div className="stock-grid" data-testid="stock-list">
            {popularStocks.map((stock) => (
              <div
                key={stock.symbol}
                className="stock-card"
                onClick={() => navigate(`/stock/${stock.symbol}`)}
                data-testid={`stock-card-${stock.symbol}`}
              >
                <div className="stock-header">
                  <h3>{stock.symbol}</h3>
                  {stock.price && (
                    <div className="stock-price">${stock.price.toFixed(2)}</div>
                  )}
                </div>
                <div className="stock-info">
                  {stock.sector && (
                    <div className="stock-sector">{stock.sector}</div>
                  )}
                  {stock.market_cap && (
                    <div className="stock-market-cap">
                      {formatMarketCap(stock.market_cap)}
                    </div>
                  )}
                </div>
                {stock.change_pct !== null && (
                  <div className={`stock-change ${stock.change_pct >= 0 ? 'positive' : 'negative'}`}>
                    {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="quick-links">
        <button onClick={() => navigate('/sectors')} className="sector-link-btn">
          View Sector Dashboard →
        </button>
      </div>
    </div>
  );
}
