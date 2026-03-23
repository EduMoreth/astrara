import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cosmos: '#0A0A0F',
        surface: {
          DEFAULT: '#12121A',
          2: '#1A1A28',
        },
        gold: '#C9A96E',
        violet: '#7B5EA7',
        stardust: '#F0EDE8',
        muted: '#8B8A9B',
        'glow-gold': 'rgba(201, 169, 110, 0.15)',
        'glow-violet': 'rgba(123, 94, 167, 0.15)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Cormorant Garamond', 'serif'],
      },
      boxShadow: {
        'glow-gold': '0 0 40px rgba(201,169,110,0.2)',
        'glow-violet': '0 0 40px rgba(123,94,167,0.2)',
      },
      borderRadius: {
        '2xl': '20px',
      },
    },
  },
  plugins: [],
}

export default config
