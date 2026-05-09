import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Geist Sans", "system-ui", "sans-serif"],
        mono: ["Roboto Mono", "monospace"],
      },
      colors: {
        // nabha-solar palette
        "pure-white": "#FFFFFF",
        "light-gray": "#F9FAFB",
        "deep-black": "#000000",
        "dark-gray": "#4B5563",
        "border-gray": "#E5E7EB",
        // FSI Zone colors
        fsi: {
          green: "#22c55e",
          yellow: "#eab308",
          red: "#ef4444",
        },
        // NDVI Health colors
        ndvi: {
          healthy: "#16a34a",
          moderate: "#ca8a04",
          degraded: "#ea580c",
          critical: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};

export default config;
