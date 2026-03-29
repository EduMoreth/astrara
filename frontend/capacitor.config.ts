import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'online.astrara.app',
  appName: 'Astrara',
  webDir: 'out',
  server: {
    // In production, the app loads from local files (static export).
    // The backend API is called directly from the frontend code (NEXT_PUBLIC_API_URL).
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#0A0A12',
      showSpinner: false,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0A0A12',
    },
  },
};

export default config;
