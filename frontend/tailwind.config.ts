import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#030303',
        foreground: '#f7f7f7',
        border: 'rgba(255, 255, 255, 0.08)',
        glass: {
          DEFAULT: 'rgba(10, 10, 10, 0.6)',
          hover: 'rgba(255, 255, 255, 0.03)',
          border: 'rgba(255, 255, 255, 0.05)',
        },
        persian: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          turquoise: '#00e5ff',
          blue: '#1e3a8a',
          indigo: '#4f46e5',
        },
        hologram: {
          teal: 'rgba(0, 240, 255, 0.15)',
          blue: 'rgba(0, 80, 255, 0.15)',
          magenta: 'rgba(255, 0, 128, 0.15)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'hologram': '0 0 25px rgba(0, 240, 255, 0.25)',
        'glass-sm': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 0 1px 0 rgba(255, 255, 255, 0.1)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'hologram-glow': 'hologramGlow 3s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        hologramGlow: {
          '0%': { boxShadow: '0 0 15px rgba(0, 240, 255, 0.15), inset 0 0 5px rgba(0, 240, 255, 0.05)' },
          '100%': { boxShadow: '0 0 30px rgba(0, 240, 255, 0.4), inset 0 0 15px rgba(0, 240, 255, 0.15)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        }
      }
    },
  },
  plugins: [],
};

export default config;
