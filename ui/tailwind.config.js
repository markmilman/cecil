/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Text semantic tokens (theme-aware via CSS custom properties)
        primary: {
          DEFAULT: 'var(--text-primary)',
        },
        muted: {
          DEFAULT: 'var(--text-secondary)',
        },
        faint: 'var(--text-faint)',
        // Brand colors
        accent: {
          DEFAULT: 'var(--primary-color)',
          hover: 'var(--primary-hover)',
          light: 'var(--primary-light)',
        },
        success: {
          DEFAULT: 'var(--success-color)',
          bg: 'var(--success-bg)',
        },
        danger: {
          DEFAULT: 'var(--danger-color)',
          bg: 'var(--danger-bg)',
        },
        // Surface colors
        card: 'var(--bg-card)',
        subtle: 'var(--bg-subtle)',
        skeleton: 'var(--bg-skeleton)',
      },
      borderColor: {
        DEFAULT: 'var(--border-color)',
      },
      outlineColor: {
        accent: 'var(--primary-color)',
      },
    },
  },
  plugins: [],
};
