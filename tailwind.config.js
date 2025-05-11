/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',  // Scans templates/ and subdirectories
    './base/templates/**/*.html',  // Scans base/templates/ if navbar.html is there
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}