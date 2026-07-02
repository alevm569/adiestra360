import { Preferences } from "@capacitor/preferences"
import type { StateStorage } from "zustand/middleware"

/**
 * Almacenamiento para zustand persist usando Capacitor Preferences.
 * En nativo usa el almacenamiento seguro del sistema; en web cae a
 * localStorage automáticamente. Es asíncrono, por eso la app espera la
 * hidratación antes de renderizar (ver App.tsx).
 */
export const capacitorStorage: StateStorage = {
  getItem: async (name) => {
    const { value } = await Preferences.get({ key: name })
    return value ?? null
  },
  setItem: async (name, value) => {
    await Preferences.set({ key: name, value })
  },
  removeItem: async (name) => {
    await Preferences.remove({ key: name })
  },
}
