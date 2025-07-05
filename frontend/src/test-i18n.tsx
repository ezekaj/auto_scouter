import React from 'react';
import { useTranslation } from 'react-i18next';
import './i18n';

const TestI18n: React.FC = () => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>i18n Test</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <button onClick={() => changeLanguage('sq')} style={{ marginRight: '10px' }}>
          Albanian (Shqip)
        </button>
        <button onClick={() => changeLanguage('it')}>
          Italian (Italiano)
        </button>
      </div>

      <div>
        <p><strong>Current Language:</strong> {i18n.language}</p>
        <p><strong>Common.loading:</strong> {t('common.loading')}</p>
        <p><strong>Auth.login:</strong> {t('auth.login')}</p>
        <p><strong>Navigation.vehicles:</strong> {t('navigation.vehicles')}</p>
        <p><strong>Dashboard.welcome:</strong> {t('dashboard.welcome')}</p>
      </div>
    </div>
  );
};

export default TestI18n;
