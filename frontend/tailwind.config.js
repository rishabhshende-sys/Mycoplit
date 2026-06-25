/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08111f",
        panel: "rgba(15, 23, 42, 0.72)",
        line: "rgba(148, 163, 184, 0.18)"
      },
      boxShadow: {
        glass: "0 18px 60px rgba(0,0,0,0.35)"
      }
    },
  },
  plugins: [],
};
