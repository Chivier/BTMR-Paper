import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// English translations
import enCommon from '../locales/en/common.json';
import enNavigation from '../locales/en/navigation.json';
import enPages from '../locales/en/pages.json';
import enValidation from '../locales/en/validation.json';

// Chinese translations
import zhCommon from '../locales/zh/common.json';
import zhNavigation from '../locales/zh/navigation.json';
import zhPages from '../locales/zh/pages.json';
import zhValidation from '../locales/zh/validation.json';

const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    pages: enPages,
    validation: enValidation,
  },
  zh: {
    common: zhCommon,
    navigation: zhNavigation,
    pages: zhPages,
    validation: zhValidation,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    
    // Language detection options
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Default namespace
    defaultNS: 'common',
    ns: ['common', 'navigation', 'pages', 'validation'],
  });

export default i18n;
