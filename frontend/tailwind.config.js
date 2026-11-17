/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0B1019',
          50: '#F4F0E8',
          100: '#344255',
          200: '#95A1B2',
          300: '#C0C7D0',
          400: '#151E2B',
          500: '#0B1019',
          600: '#080C13',
          700: '#06090F',
          800: '#04070B',
          900: '#020406',
        },
        ivory: {
          DEFAULT: '#0B1019',
          50: '#1C2736',
          100: '#151E2B',
          200: '#F4F0E8',
          300: '#2A3747',
          400: '#354456',
        },
        emerald: {
          DEFAULT: '#55C99A',
          50: '#122C28',
          100: '#1E5948',
          200: '#8BE0BC',
          300: '#6BD5A8',
          400: '#55C99A',
          500: '#3DAF83',
          600: '#2B8A68',
        },
        champagne: {
          DEFAULT: '#D4B477',
          50: '#302817',
          100: '#5A4822',
          200: '#E7D29A',
          300: '#DEBF81',
          400: '#D4B477',
          500: '#BC9957',
          600: '#9F7D41',
        },
        loss: '#C0392B',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
      },
    },
  },
  plugins: [],
};
