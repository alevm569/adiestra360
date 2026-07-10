import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"

interface ApplyArgs {
  /** IDs de los ejercicios del plan (TrainingPlanExercise) a cambiar */
  targetIds: string[]
  /** Refuerzo sugerido (recommended_strategy) */
  newStrategyId: string
}

/**
 * Aplica la recomendación de la IA: cambia el refuerzo SOLO de los ejercicios
 * indicados (los que están en problemas, no los ya superados).
 */
export function useApplyRecommendation(dogId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ targetIds, newStrategyId }: ApplyArgs) => {
      for (const id of targetIds) {
        await api.put(
          `/training/plan/${dogId}/exercise/${id}/reinforcement/`,
          { reinforcement_type_id: newStrategyId }
        )
      }
      return targetIds.length
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard", dogId] })
      qc.invalidateQueries({ queryKey: ["plan", dogId] })
    },
  })
}
