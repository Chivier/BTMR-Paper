import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation(['pages']);

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
          {t('home.title')}
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          {t('home.subtitle')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        <div className="card">
          <div className="card-content py-2">
            <h3 className="text-lg font-semibold mb-2">{t('home.processPapers.title')}</h3>
            <p className="text-gray-600 mb-4">
              {t('home.processPapers.description')}
            </p>
            <button 
              className="btn-primary btn-md"
              onClick={handleGetStarted}
            >
              {t('home.processPapers.button')}
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-content py-2">
            <h3 className="text-lg font-semibold mb-2">{t('home.viewPapers.title')}</h3>
            <p className="text-gray-600 mb-4">
              {t('home.viewPapers.description')}
            </p>
            <button 
              className="btn-outline btn-md"
              onClick={handleBrowsePapers}
            >
              {t('home.viewPapers.button')}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
