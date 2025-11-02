/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        emerald: {
          500: '#40b6ac',
          600: '#319890',
        },
        gray: {
          800: 'rgba(255, 255, 255, 0.1)',
          900: '#1a1a1a',
        },
      },
      borderColor: {
        DEFAULT: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
  plugins: [],
}