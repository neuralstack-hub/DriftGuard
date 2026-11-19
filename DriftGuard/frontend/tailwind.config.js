/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        slatebg: "#0b1120",
        cardbg: "#111827",
        bordercol: "#1f2937",
      },
    },
  },
  plugins: [],
};
