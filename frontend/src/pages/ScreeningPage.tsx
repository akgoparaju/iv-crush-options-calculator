import React from 'react';
import ScreeningDashboard from '../components/screening/ScreeningDashboard';

const ScreeningPage: React.FC = () => {
  const handleSymbolSelect = (symbol: string) => {
    // Navigate to charts page or open symbol details
    console.log('Selected symbol:', symbol);
    // You could implement navigation here:
    // navigate(`/charts?symbol=${symbol}`);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Market Screening</h1>
          <p className="text-slate-600 mt-2">
            Discover trading opportunities with advanced screening tools, market insights, and real-time data.
          </p>
        </div>
        
        <ScreeningDashboard onSymbolSelect={handleSymbolSelect} />
      </div>
    </div>
  );
};

export default ScreeningPage;