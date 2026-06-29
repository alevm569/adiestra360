import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { ActivePlan } from "@/types"

interface ApplyArgs {
  plan: ActivePlan
  /** Refuerzo actual a reemplazar (previous_strategy de la recomendación) */
  prevStrategyId: string
  /** Refuerzo sugerido (recommended_strategy) */
  newStrategyId: string
}

/**
 * Aplica la recomendación de la IA: cambia el refuerzo de los ejercicios
 * activos que usan el refuerzo anterior por el recomendado.
 */
export function useApplyRecommendation(dogId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ plan, prevStrategyId, newStrategyId }: ApplyArgs) => {
      const targets = plan.exercises.filter(
        (e) => e.active && e.reinforcement_type?.id === prevStrategyId
      )
      for (const t of targets) {
        await api.put(
          `/training/plan/${dogId}/exercise/${t.id}/reinforcement/`,
          { reinforcement_type_id: newStrategyId }
        )
      }
      return targets.length
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard", dogId] })
      qc.invalidateQueries({ queryKey: ["plan", dogId] })
    },
  })
}
