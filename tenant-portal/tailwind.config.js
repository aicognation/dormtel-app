/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#1B2A6B',
          'navy-dark': '#0F1B4A',
          gold: '#FFD600',
          'gold-light': '#FFF3B0',
        },
      },
    },
  },
  plugins: [],
}
