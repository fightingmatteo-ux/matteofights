/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0B0B0D",
        panel: "#101013",
        panel2: "#16161A",
        line: "#26262C",
        "line-soft": "#1C1C21",
        ink: "#F0EFED",
        "ink-dim": "#A8A7A3",
        muted: "#6C6C73",
        red: "#C82020",
        "red-hi": "#E03030",
        gold: "#C49040",
        green: "#5E9E72",
      },
      fontFamily: {
        display: ['"Bebas Neue"', "ui-sans-serif", "sans-serif"],
        sans: ["Archivo", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        eyebrow: "0.28em",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(18px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.35", transform: "scale(0.82)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        rise: "rise 0.8s cubic-bezier(0.16,1,0.3,1) both",
        scan: "scan 5.5s linear infinite",
        pulseDot: "pulseDot 1.8s ease-in-out infinite",
        shimmer: "shimmer 1.4s infinite",
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.16,1,0.3,1)",
      },
    },
  },
  plugins: [],
};
