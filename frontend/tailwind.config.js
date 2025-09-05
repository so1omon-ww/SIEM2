/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'siem-primary': '#1e40af',
        'siem-secondary': '#64748b',
        'siem-danger': '#dc2626',
        'siem-warning': '#f59e0b',
        'siem-success': '#16a34a',
        'siem-info': '#0ea5e9'
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
