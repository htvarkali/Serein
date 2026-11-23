import { fileURLToPath } from "node:url"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// Builds one entry script (plus lazy chart chunks) and one stylesheet into the static site. GitHub Pages
// publishes website/ as-is, so the built files are committed.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Relative URLs: the site is served from a subpath on GitHub Pages.
  base: "./",
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: {
    outDir: "../website/assets/islands",
    emptyOutDir: true,
    rollupOptions: {
      input: "src/main.tsx",
      output: {
        entryFileNames: "islands.js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "islands[extname]",
      },
    },
  },
})
