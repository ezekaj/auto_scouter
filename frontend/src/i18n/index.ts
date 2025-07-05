import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import albanianTranslations from './locales/sq.json';
import italianTranslations from './locales/it.json';

const resources = {
  sq: {
    translation: albanianTranslations
  },
  it: {
    translation: italianTranslations
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'sq', // Default to Albanian
    lng: 'sq', // Default language
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React already does escaping
    },

    react: {
      useSuspense: false,
    },
  });

export default i18n;
