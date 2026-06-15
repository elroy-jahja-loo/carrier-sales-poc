/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#0f172a",
        panelAlt: "#111827",
        accent: "#059669",
        warm: "#f59e0b",
        danger: "#ef4444",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"],
      },
      boxShadow: {
        soft: "0 8px 24px rgba(0, 0, 0, 0.18)",
      },
    },
  },
  plugins: [],
};
