/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        medibot: {
          bg: "#0f172a",
          panel: "#1e293b",
          border: "#334155",
          accent: "#3b82f6",
          success: "#10b981",
          danger: "#f59e0b",
          text: "#e2e8f0",
        },
      },
    },
  },
  plugins: [],
};
