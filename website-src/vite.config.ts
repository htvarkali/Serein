import { fileURLToPath } from "node:url"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// The whole public site is this React app. GitHub Pages publishes website/ as-is,
// so the build is written there and committed. Static files (videos, images, data)
// live in public/ and are copied unchanged.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Relative URLs: the site is served from a subpath on GitHub Pages.
  base: "./",
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: {
    outDir: "../website",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200,
  },
})
