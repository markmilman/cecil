/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Cecil design tokens
        primary: {
          DEFAULT: '#0f172a', // slate-900
        },
        accent: {
          DEFAULT: '#4f46e5', // indigo-600
          hover: '#4338ca', // indigo-700
        },
        success: {
          DEFAULT: '#10b981', // emerald-500
        },
        danger: {
          DEFAULT: '#ef4444', // red-500
        },
        muted: {
          DEFAULT: '#64748b', // slate-500
        },
      },
    },
  },
  plugins: [],
};
