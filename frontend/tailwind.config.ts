import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#b45309",   // warm amber — matches a resort feel
          light: "#fef3c7",
          dark: "#78350f",
        },
      },
    },
  },
  plugins: [],
};

export default config;
