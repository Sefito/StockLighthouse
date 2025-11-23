/**
 * Search bar component with auto-suggest
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchStocks } from '../services/api';
import type { Stock } from '../types';
import './SearchBar.css';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Stock[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (query.length === 0) {
        setResults([]);
        setIsOpen(false);
        return;
      }

      setLoading(true);
      try {
        const stocks = await searchStocks(query);
        setResults(stocks);
        setIsOpen(stocks.length > 0);
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(fetchResults, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (symbol: string) => {
    setQuery('');
    setIsOpen(false);
    navigate(`/stock/${symbol}`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (results.length > 0) {
      handleSelect(results[0].symbol);
    }
  };

  return (
    <div className="search-bar" ref={dropdownRef}>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          className="search-input"
          placeholder="Search stocks by symbol, sector, or industry..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          data-testid="search-input"
        />
      </form>

      {isOpen && (
        <div className="search-results" data-testid="search-results">
          {loading ? (
            <div className="search-result-item loading">Searching...</div>
          ) : (
            results.map((stock) => (
              <div
                key={stock.symbol}
                className="search-result-item"
                onClick={() => handleSelect(stock.symbol)}
                data-testid={`search-result-${stock.symbol}`}
              >
                <div className="result-symbol">{stock.symbol}</div>
                <div className="result-info">
                  {stock.sector && <span className="result-sector">{stock.sector}</span>}
                  {stock.price && (
                    <span className="result-price">
                      ${stock.price.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
