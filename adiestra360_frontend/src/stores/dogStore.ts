import { create } from "zustand"
import { persist } from "zustand/middleware"

/**
 * Perro activo: qué perro se muestra en el dashboard/plan.
 * Se persiste para que al reabrir la app recuerde la selección.
 */
interface DogState {
  activeDogId: string | null
  setActiveDog: (id: string) => void
  clearActiveDog: () => void
}

export const useDogStore = create<DogState>()(
  persist(
    (set) => ({
      activeDogId: null,
      setActiveDog: (id) => set({ activeDogId: id }),
      clearActiveDog: () => set({ activeDogId: null }),
    }),
    { name: "adiestra-active-dog" }
  )
)
