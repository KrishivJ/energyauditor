/** Design tokens from the build brief §1 ("instrument panel" aesthetic). */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0c1116", // deep background
        panel: "#121b24", // panel surface
        hairline: "#22323f", // hairline borders
        amber: "#f4b740", // energy / occupied / daytime
        cool: "#5b8fc7", // night / off-days
        waste: "#e8743b", // waste
        save: "#57b894", // savings
        muted: "#7c93a3", // secondary text
      },
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
