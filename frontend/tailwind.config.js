/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#0a0a0f",
          800: "#12121a",
          700: "#1a1a25",
          600: "#222233",
        },
        accent: {
          purple: "#8b5cf6",
          pink: "#ec4899",
          blue: "#3b82f6",
          cyan: "#06b6d4",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(139,92,246,0.3)" },
          "100%": { boxShadow: "0 0 20px rgba(139,92,246,0.6)" },
        },
      },
    },
  },
  plugins: [],
};
