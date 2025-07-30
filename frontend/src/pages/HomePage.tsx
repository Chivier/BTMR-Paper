import React from 'react';
import { useNavigate } from 'react-router-dom';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/process');
  };

  const handleBrowsePapers = () => {
    navigate('/papers');
  };


  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to BTMR
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Beautiful Text Mining Reader - Extract and summarize academic papers with AI
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        <div className="card">
          <div className="card-content py-5">
            <h3 className="text-lg font-semibold mb-2">Process Papers</h3>
            <p className="text-gray-600 mb-4">
              Upload or provide URLs to academic papers for AI-powered extraction and summarization.
            </p>
            <button 
              className="btn-primary btn-md"
              onClick={handleGetStarted}
            >
              Get Started
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-content py-5">
            <h3 className="text-lg font-semibold mb-2">View Papers</h3>
            <p className="text-gray-600 mb-4">
              Browse and manage your processed papers with search and filtering capabilities.
            </p>
            <button 
              className="btn-outline btn-md"
              onClick={handleBrowsePapers}
            >
              Browse Papers
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
