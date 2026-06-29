import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Achievement } from "@/types"

export type Rating = "dificil" | "bien" | "excelente"

/** Un ejercicio a registrar en la sesión. */
export interface TrainInput {
  exerciseId: string
  reinforcementTypeId: string
  exerciseName: string
  rating: Rating
}

/** Resultado por ejercicio tras crear sesión + evaluar progreso. */
export interface ExerciseOutcome {
  exerciseName: string
  rating: Rating
  success: boolean
  mastered: boolean
  leveledUp: boolean
  newLevel: string | null
  successRate: number
  totalSessions: number
}

export interface RecommendationSummary {
  recommendedName: string
  previousName: string
  reason: string
}

export interface TrainSummary {
  outcomes: ExerciseOutcome[]
  xpEarned: number
  totalXp: number
  newAchievements: Achievement[]
  recommendation: RecommendationSummary | null
}

interface CreateSessionResp {
  xp_earned: number
  total_xp: number
  new_achievements: Achievement[]
  exercise_stats: {
    success_rate: number
    avg_response_time: number | null
    total_sessions: number
  }
}

interface EvaluateResp {
  exercise_mastered: boolean
  level_upgraded: boolean
  new_level: string | null
}

interface AnalyzeResp {
  recommendation: {
    previous_strategy_name?: string
    recommended_strategy_name?: string
    reason?: string
  } | null
}

/**
 * Flujo completo por ejercicio:
 *  1) POST /sessions/<dog>/create/   → registra la sesión, da XP/racha/logros
 *  2) POST /training/plan/<dog>/evaluate/ → marca dominado / desbloquea / sube nivel
 * Al final, una vez:
 *  3) POST /recommendations/<dog>/analyze/ → sugiere cambiar refuerzo si va < 50%
 */
export function useTrainSession(dogId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({
      inputs,
      notes,
    }: {
      inputs: TrainInput[]
      notes?: string
    }): Promise<TrainSummary> => {
      const outcomes: ExerciseOutcome[] = []
      let xpEarned = 0
      let totalXp = 0
      const newAchievements: Achievement[] = []

      for (const input of inputs) {
        const success = input.rating !== "dificil"

        const { data: s } = await api.post<CreateSessionResp>(
          `/sessions/${dogId}/create/`,
          {
            exercise: input.exerciseId,
            reinforcement_type: input.reinforcementTypeId,
            success,
            notes: notes?.trim() || undefined,
          }
        )
        xpEarned += s.xp_earned
        totalXp = s.total_xp
        newAchievements.push(...s.new_achievements)

        const { data: ev } = await api.post<EvaluateResp>(
          `/training/plan/${dogId}/evaluate/`,
          { exercise_id: input.exerciseId }
        )

        outcomes.push({
          exerciseName: input.exerciseName,
          rating: input.rating,
          success,
          mastered: ev.exercise_mastered,
          leveledUp: ev.level_upgraded,
          newLevel: ev.new_level,
          successRate: s.exercise_stats.success_rate,
          totalSessions: s.exercise_stats.total_sessions,
        })
      }

      // La IA sugiere cambiar el refuerzo solo si el perro va < 50%.
      let recommendation: RecommendationSummary | null = null
      try {
        const { data: a } = await api.post<AnalyzeResp>(
          `/recommendations/${dogId}/analyze/`,
          {}
        )
        if (a.recommendation?.recommended_strategy_name) {
          recommendation = {
            recommendedName: a.recommendation.recommended_strategy_name,
            previousName: a.recommendation.previous_strategy_name ?? "",
            reason: a.recommendation.reason ?? "",
          }
        }
      } catch {
        // analyze es opcional; si falla, no rompemos la sesión.
      }

      return { outcomes, xpEarned, totalXp, newAchievements, recommendation }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard", dogId] })
      qc.invalidateQueries({ queryKey: ["plan", dogId] })
    },
  })
}
