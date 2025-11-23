import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { StockDetailPage } from './pages/StockDetailPage';
import { SectorDashboard } from './pages/SectorDashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/stock/:symbol" element={<StockDetailPage />} />
          <Route path="/sectors" element={<SectorDashboard />} />
          <Route path="/sector/:sectorName" element={<SectorDashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
