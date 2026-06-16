/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#1B2A6B',
          'navy-light': '#2A3F8F',
          'navy-dark': '#111D4E',
          gold: '#FFD600',
          'gold-light': '#FFF3B0',
          'gold-dark': '#C9A800',
        }
      }
    },
  },
  plugins: [],
};
