/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#135bec",
        "background-light": "#f6f6f8",
        "background-dark": "#101622"
      },
      fontFamily: {
        display: ["Inter", "sans-serif"]
      },
      borderRadius: {
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px"
      },
      animation: {
        "spin-slow": "spin 2s linear infinite",
        "bounce-dot": "bounce-dot 1.4s ease-in-out infinite",
        "fadeIn": "fadeIn 0.3s ease-out"
      },
      keyframes: {
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.5" },
          "40%": { transform: "scale(1)", opacity: "1" }
        },
        "fadeIn": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      }
    }
  },
  plugins: []
};
