import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import { Capacitor } from "@capacitor/core"
import { queryClient } from "@/lib/queryClient"
import App from "./App"
import "./index.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)

// Service worker: solo en la PWA web. Dentro del contenedor Capacitor
// (Android/iOS) la app ya corre nativa y el SW no debe registrarse.
if (!Capacitor.isNativePlatform()) {
  import("virtual:pwa-register")
    .then(({ registerSW }) => {
      registerSW({ immediate: true })
    })
    .catch(() => {
      /* En dev el módulo virtual puede no existir; se ignora. */
    })
}
