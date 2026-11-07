/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#06090e",
          surface: "rgba(11, 17, 29, 0.75)",
          card: "rgba(13, 21, 37, 0.70)",
          border: "rgba(255, 255, 255, 0.07)",
          borderLight: "rgba(255, 255, 255, 0.12)",
        },
        brand: {
          yellow: "#e2f163", // Yellow-lime pill accent in screenshot
          cyan: "#0ea5e9",
          low: "#10b981",
          mid: "#f59e0b",
          high: "#ef4444",
        }
      },
      fontFamily: {
        sans: ["'Be Vietnam Pro'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
}
