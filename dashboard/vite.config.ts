import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" keeps the build portable — works at any path on Vercel/Netlify/static hosts.
export default defineConfig({
  base: "./",
  plugins: [react()],
});
