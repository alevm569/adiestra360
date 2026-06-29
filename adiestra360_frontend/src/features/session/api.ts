import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Achievement } from "@/types"

/** Una entrada de sesión por ejercicio (lo que pide POST /sessions/<dog>/create/). */
export interface SessionInput {
  exercise: string
  reinforcement_type: string
  success: boolean
  notes?: string
}

interface SessionResult {
  xp_earned: number
  total_xp: number
  streak: { current: number; longest: number }
  new_achievements: Achievement[]
}

/** Resumen agregado de registrar varios ejercicios en una sesión. */
export interface SessionSummary {
  xpEarned: number
  totalXp: number
  newAchievements: Achievement[]
  count: number
}

/**
 * Registra varios ejercicios del día. El backend procesa uno por POST y
 * actualiza la racha en cada uno, por eso se mandan en secuencia.
 */
export function useCreateSessions(dogId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (inputs: SessionInput[]): Promise<SessionSummary> => {
      let xpEarned = 0
      let totalXp = 0
      const newAchievements: Achievement[] = []

      for (const input of inputs) {
        const { data } = await api.post<SessionResult>(
          `/sessions/${dogId}/create/`,
          input
        )
        xpEarned += data.xp_earned
        totalXp = data.total_xp
        newAchievements.push(...data.new_achievements)
      }

      return { xpEarned, totalXp, newAchievements, count: inputs.length }
    },
    onSuccess: () => {
      // El dashboard y el plan dependen de las sesiones: refrescarlos.
      qc.invalidateQueries({ queryKey: ["dashboard", dogId] })
      qc.invalidateQueries({ queryKey: ["plan", dogId] })
    },
  })
}
