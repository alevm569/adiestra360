import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import { capacitorStorage } from "@/lib/capacitorStorage"
import { useAuth } from "@/stores/authStore"

/**
 * Perro activo: qué perro se muestra en el dashboard/plan.
 * Se persiste para que al reabrir la app recuerde la selección.
 *
 * La selección se guarda junto al dueño (`userId`): en un dispositivo
 * compartido, si entra otra cuenta el perro guardado deja de ser válido y
 * se ignora, en vez de pedirle al backend el perro de la sesión anterior
 * (que responde 404 y deja el dashboard vacío).
 */
interface DogState {
  /** Dueño de la selección; null en datos antiguos, previos al versionado. */
  userId: string | null
  activeDogId: string | null
  setActiveDog: (id: string) => void
  clearActiveDog: () => void
}

export const useDogStore = create<DogState>()(
  persist(
    (set) => ({
      userId: null,
      activeDogId: null,
      setActiveDog: (id) =>
        set({ activeDogId: id, userId: useAuth.getState().user?.id ?? null }),
      clearActiveDog: () => set({ activeDogId: null, userId: null }),
    }),
    {
      name: "adiestra-active-dog",
      storage: createJSONStorage(() => capacitorStorage),
      // v1 añade `userId`. Lo guardado con v0 no sabe de quién es, así que se
      // descarta: el DogResolver vuelve a elegir el perro que toque.
      version: 1,
      migrate: (_persisted, version) =>
        version === 0
          ? ({ userId: null, activeDogId: null } as Partial<DogState>)
          : (_persisted as Partial<DogState>),
    }
  )
)

/**
 * Perro activo válido para la sesión actual. Si la selección guardada es de
 * otra cuenta (o no tiene dueño), devuelve null para que la pantalla resuelva
 * el perro contra el backend.
 */
export function useActiveDogId(): string | null {
  const activeDogId = useDogStore((s) => s.activeDogId)
  const ownerId = useDogStore((s) => s.userId)
  const userId = useAuth((s) => s.user?.id ?? null)
  if (!activeDogId || !userId || ownerId !== userId) return null
  return activeDogId
}
