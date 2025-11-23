/**
 * KPI Table component to display stock metrics
 */
import type { Stock } from '../types';
import './KPITable.css';

interface KPITableProps {
  stock: Stock;
}

export function KPITable({ stock }: KPITableProps) {
  const formatNumber = (value: number | null, decimals: number = 2) => {
    if (value === null) return 'N/A';
    return value.toFixed(decimals);
  };

  const formatMarketCap = (value: number | null) => {
    if (value === null) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(0)}`;
  };

  const formatPercent = (value: number | null) => {
    if (value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="kpi-table" data-testid="kpi-table">
      <h2>Key Performance Indicators</h2>
      <table>
        <tbody>
          <tr>
            <td className="kpi-label">Symbol</td>
            <td className="kpi-value">{stock.symbol}</td>
          </tr>
          <tr>
            <td className="kpi-label">Current Price</td>
            <td className="kpi-value">
              {stock.price !== null ? `$${formatNumber(stock.price)}` : 'N/A'}
            </td>
          </tr>
          <tr>
            <td className="kpi-label">Previous Close</td>
            <td className="kpi-value">
              {stock.previous_close !== null ? `$${formatNumber(stock.previous_close)}` : 'N/A'}
            </td>
          </tr>
          <tr>
            <td className="kpi-label">Change %</td>
            <td className={`kpi-value ${stock.change_pct && stock.change_pct > 0 ? 'positive' : stock.change_pct && stock.change_pct < 0 ? 'negative' : ''}`}>
              {stock.change_pct !== null ? `${formatNumber(stock.change_pct)}%` : 'N/A'}
            </td>
          </tr>
          <tr>
            <td className="kpi-label">Market Cap</td>
            <td className="kpi-value">{formatMarketCap(stock.market_cap)}</td>
          </tr>
          <tr>
            <td className="kpi-label">P/E Ratio</td>
            <td className="kpi-value">{formatNumber(stock.pe_ratio)}</td>
          </tr>
          <tr>
            <td className="kpi-label">P/B Ratio</td>
            <td className="kpi-value">{formatNumber(stock.pb_ratio)}</td>
          </tr>
          <tr>
            <td className="kpi-label">Dividend Yield</td>
            <td className="kpi-value">{formatPercent(stock.dividend_yield)}</td>
          </tr>
          <tr>
            <td className="kpi-label">Sector</td>
            <td className="kpi-value">{stock.sector || 'N/A'}</td>
          </tr>
          <tr>
            <td className="kpi-label">Industry</td>
            <td className="kpi-value">{stock.industry || 'N/A'}</td>
          </tr>
          <tr>
            <td className="kpi-label">Exchange</td>
            <td className="kpi-value">{stock.exchange || 'N/A'}</td>
          </tr>
          <tr>
            <td className="kpi-label">Currency</td>
            <td className="kpi-value">{stock.currency || 'N/A'}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
