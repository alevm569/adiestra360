import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { TrainingSessionRecord } from "@/types"

/** Historial completo de sesiones del perro, de la más reciente a la más antigua. */
export function useSessionHistory(dogId: string | null) {
  return useQuery({
    queryKey: ["sessions", dogId],
    queryFn: async () => {
      const { data } = await api.get<TrainingSessionRecord[]>(`/sessions/${dogId}/`)
      return data
    },
    enabled: !!dogId,
  })
}
