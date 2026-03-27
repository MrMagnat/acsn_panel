/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './app.vue',
    './pages/**/*.{vue,js,ts}',
    './layouts/**/*.{vue,js,ts}',
    './components/**/*.{vue,js,ts}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#f0f4ff',
          100: '#dde6ff',
          500: '#4f6ef7',
          600: '#3b55e6',
          700: '#2e44cc',
        },
        surface: '#f8fafc',
      },
    },
  },
  plugins: [],
}
