import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { ExerciseTechniqueResponse } from "@/types"

/**
 * Cómo enseñar un ejercicio: método sugerido según la motivación del perro,
 * el otro método, y el refuerzo recomendado.
 */
export function useExerciseTechnique(
  exerciseId: string | undefined,
  dogId: string | null
) {
  return useQuery({
    queryKey: ["technique", exerciseId, dogId],
    queryFn: async () => {
      const { data } = await api.get<ExerciseTechniqueResponse>(
        `/training/exercise/${exerciseId}/technique/${dogId}/`
      )
      return data
    },
    enabled: !!exerciseId && !!dogId,
  })
}
