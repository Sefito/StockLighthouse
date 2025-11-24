/**
 * Search bar component with auto-suggest
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Autocomplete, TextField, Box, Typography, CircularProgress } from '@mui/material';
import { searchStocks } from '../services/api';
import type { Stock } from '../types';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResults = async () => {
      if (query.length === 0) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const stocks = await searchStocks(query);
        setResults(stocks);
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

  const handleSelect = (_event: React.SyntheticEvent, value: string | Stock | null) => {
    if (value && typeof value !== 'string') {
      setQuery('');
      navigate(`/stock/${value.symbol}`);
    }
  };

  return (
    <Autocomplete
      freeSolo
      options={results}
      loading={loading}
      inputValue={query}
      onInputChange={(_event, newValue) => setQuery(newValue)}
      onChange={handleSelect}
      getOptionLabel={(option) => typeof option === 'string' ? option : option.symbol}
      renderOption={(props, option) => (
        <Box
          component="li"
          {...props}
          key={option.symbol}
          data-testid={`search-result-${option.symbol}`}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            <Typography variant="body1" fontWeight="600">
              {option.symbol}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              {option.sector && (
                <Typography variant="body2" color="text.secondary">
                  {option.sector}
                </Typography>
              )}
              {option.price && (
                <Typography variant="body2" color="primary">
                  ${option.price.toFixed(2)}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search stocks by symbol, sector, or industry..."
          variant="outlined"
          fullWidth
          data-testid="search-input"
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      data-testid="search-results"
    />
  );
}
