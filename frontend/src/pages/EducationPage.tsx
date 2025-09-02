import React from 'react';
import EducationDashboard from '../components/education/EducationDashboard';

const EducationPage: React.FC = () => {
  const handleContentSelect = (contentId: string) => {
    // Navigate to content details or open content viewer
    console.log('Selected content:', contentId);
    // You could implement navigation here:
    // navigate(`/education/content/${contentId}`);
    // Or open a modal with content details
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <EducationDashboard onContentSelect={handleContentSelect} />
      </div>
    </div>
  );
};

export default EducationPage;