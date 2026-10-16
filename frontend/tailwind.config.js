/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          950: '#0b0f14',
          900: '#111822',
          850: '#172230',
          800: '#1e2c3e',
          700: '#2b3f58',
          600: '#405c7f',
          500: '#5c7fa8',
          accent: '#00d2ff',
          warning: '#f59e0b',
          danger: '#ef4444',
          success: '#10b981',
        }
      }
    },
  },
  plugins: [],
}
