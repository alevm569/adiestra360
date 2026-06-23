import type { CapacitorConfig } from "@capacitor/cli"

const config: CapacitorConfig = {
  appId: "com.adiestra360.app",
  appName: "Adiestra360",
  webDir: "dist",
  // En Android, durante desarrollo contra un backend en HTTP (no HTTPS),
  // habilita tráfico en claro. En producción usa HTTPS y quítalo.
  android: {
    allowMixedContent: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      backgroundColor: "#1f7d52",
      showSpinner: false,
    },
  },
}

export default config
