/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E5F8C',
          light: '#2B7BBF',
          dark: '#0F3D5C',
        },
        secondary: {
          DEFAULT: '#2D7A4F',
          light: '#38A169',
        },
        accent: '#C05621',
        danger: '#C53030',
        warning: '#D69E2E',
        success: '#2D7A4F',
        background: '#F8FAFC',
        surface: '#FFFFFF',
        text: {
          primary: '#1A202C',
          secondary: '#4A5568',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Sarabun', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
