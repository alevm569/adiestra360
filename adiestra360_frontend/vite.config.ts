import path from "path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { VitePWA } from "vite-plugin-pwa"

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      // El SW se registra a mano en main.tsx (y NO dentro de Capacitor nativo).
      injectRegister: false,
      registerType: "autoUpdate",
      // Se generan sw.js + manifest.webmanifest en el build web (dist/).
      // En el build híbrido (Capacitor) el SW nunca se registra, así que
      // no interfiere con la app nativa aunque el archivo exista en dist/.
      includeAssets: [
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
      ],
      manifest: {
        name: "Adiestra360",
        short_name: "Adiestra360",
        description:
          "Adiestramiento canino gamificado: plan, sesiones y recomendaciones inteligentes.",
        lang: "es",
        dir: "ltr",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#ffffff",
        theme_color: "#1f7d52",
        categories: ["lifestyle", "education", "sports"],
        icons: [
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "pwa-maskable-192x192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "maskable",
          },
          {
            src: "pwa-maskable-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        // Precache del shell (JS/CSS/HTML) + iconos, y fallback offline al SPA.
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        navigateFallback: "/index.html",
        // No cachear las llamadas al backend con el fallback del SPA.
        navigateFallbackDenylist: [/^\/api/],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        runtimeCaching: [
          {
            // Fotos de las técnicas (public/tecnicas/*): cache-first, larga vida.
            urlPattern: ({ url }) => url.pathname.startsWith("/tecnicas/"),
            handler: "CacheFirst",
            options: {
              cacheName: "tecnicas-img",
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30,
              },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Google Fonts (hoja de estilos): stale-while-revalidate.
            urlPattern: ({ url }) => url.origin === "https://fonts.googleapis.com",
            handler: "StaleWhileRevalidate",
            options: { cacheName: "google-fonts-styles" },
          },
          {
            // Google Fonts (archivos woff2): cache-first, larga vida.
            urlPattern: ({ url }) => url.origin === "https://fonts.gstatic.com",
            handler: "CacheFirst",
            options: {
              cacheName: "google-fonts-files",
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        // No activar el SW en `npm run dev` para no cachear en desarrollo.
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
