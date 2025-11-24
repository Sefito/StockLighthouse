import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { HomePage } from './pages/HomePage';
import { StockDetailPage } from './pages/StockDetailPage';
import { SectorDashboard } from './pages/SectorDashboard';
import { theme } from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/stock/:symbol" element={<StockDetailPage />} />
          <Route path="/sectors" element={<SectorDashboard />} />
          <Route path="/sector/:sectorName" element={<SectorDashboard />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
