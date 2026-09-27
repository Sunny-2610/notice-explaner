/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#FFFFFF',
        surface: '#F8F9FA',
        'surface-elevated': '#FFFFFF',
        border: '#E5E7EB',
        'text-primary': '#111827',
        'text-secondary': '#4B5563',
        'text-muted': '#6B7280',

        primary: '#613AF5',
        'primary-hover': '#4F2ED4',
        'primary-light': '#F3F0FF',

        success: '#16A34A',
        'success-bg': '#F0FDF4',
        'success-border': '#BBF7D0',
        warning: '#EA580C',
        'warning-bg': '#FFF7ED',
        'warning-border': '#FED7AA',
        error: '#DC2626',
        'error-bg': '#FEF2F2',
        'error-border': '#FECACA',

        'disclaimer-bg': '#FFFBEB',
        'disclaimer-border': '#FDE68A',
        'disclaimer-text': '#92400E',

        // Escalation's own visual identity — distinct from generic error.
        'escalate-bg': '#FEF2F2',
        'escalate-border': '#DC2626',
        'escalate-accent': '#7F1D1D',
      },
      borderRadius: { sm: '4px', md: '8px', lg: '12px', xl: '16px', '2xl': '24px', full: '9999px' },
      fontFamily: {
        sans: ['"Noto Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
