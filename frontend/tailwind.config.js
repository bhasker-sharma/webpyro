/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#64748b',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
      animation: {
        'alarm-blink': 'alarm-blink 1.5s ease-in-out infinite',
      },
      keyframes: {
        'alarm-blink': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 20px rgba(239, 68, 68, 0.8), 0 0 40px rgba(239, 68, 68, 0.4)',
          },
          '50%': {
            opacity: '0.7',
            boxShadow: '0 0 10px rgba(239, 68, 68, 0.4), 0 0 20px rgba(239, 68, 68, 0.2)',
          },
        },
      },
    },
  },
  plugins: [],
}