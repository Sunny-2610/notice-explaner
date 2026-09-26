/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#7170FF',
        accent: '#7170FF',
        secondary: '#F7F8F8',
        tertiary: '#62666D',
        neutral: '#08090A',
        surface: '#0F1011',
        'on-surface': '#F7F8F8',
        'muted-surface': '#151617',
        border: '#FFFFFF14',
        'text-muted': '#62666D',
        success: '#2FB344',
        warning: '#F5C400',
        error: '#E5484D',
      },
      borderRadius: { sm: '4px', md: '8px', lg: '9px', xl: '12px', full: '9999px' },
      fontFamily: {
        sans: ['"Inter Variable"', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
