/**
 * KPI Table component to display stock metrics
 */
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Typography,
  Box,
} from '@mui/material';
import type { Stock } from '../types';

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

  const getChangeColor = (value: number | null) => {
    if (value === null) return 'text.primary';
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.primary';
  };

  const rows = [
    { label: 'Symbol', value: stock.symbol },
    { 
      label: 'Current Price', 
      value: stock.price !== null ? `$${formatNumber(stock.price)}` : 'N/A' 
    },
    { 
      label: 'Previous Close', 
      value: stock.previous_close !== null ? `$${formatNumber(stock.previous_close)}` : 'N/A' 
    },
    { 
      label: 'Change %', 
      value: stock.change_pct !== null ? `${formatNumber(stock.change_pct)}%` : 'N/A',
      color: getChangeColor(stock.change_pct),
    },
    { label: 'Market Cap', value: formatMarketCap(stock.market_cap) },
    { label: 'P/E Ratio', value: formatNumber(stock.pe_ratio) },
    { label: 'P/B Ratio', value: formatNumber(stock.pb_ratio) },
    { label: 'Dividend Yield', value: formatPercent(stock.dividend_yield) },
    { label: 'Sector', value: stock.sector || 'N/A' },
    { label: 'Industry', value: stock.industry || 'N/A' },
    { label: 'Exchange', value: stock.exchange || 'N/A' },
    { label: 'Currency', value: stock.currency || 'N/A' },
  ];

  return (
    <Box data-testid="kpi-table">
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Key Performance Indicators
      </Typography>
      <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Table>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.label}>
                <TableCell component="th" scope="row" sx={{ fontWeight: 600, width: '40%' }}>
                  {row.label}
                </TableCell>
                <TableCell 
                  align="right"
                  sx={{ 
                    color: row.color || 'text.primary',
                    fontWeight: row.color ? 600 : 400,
                  }}
                >
                  {row.value}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
