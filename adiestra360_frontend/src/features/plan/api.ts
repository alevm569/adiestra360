import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { ActivePlan } from "@/types"

/** Plan activo del perro con sus ejercicios (refuerzo, orden, dominado, activo). */
export function useActivePlan(dogId: string | null) {
  return useQuery({
    queryKey: ["plan", dogId],
    queryFn: async () => {
      const { data } = await api.get<ActivePlan>(`/training/plan/${dogId}/`)
      return data
    },
    enabled: !!dogId,
  })
}
