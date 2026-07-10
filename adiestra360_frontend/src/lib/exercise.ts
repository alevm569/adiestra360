import type { ExerciseProgress, PlanExerciseItem } from "@/types"

/** Capitaliza la primera letra (los nombres del backend vienen en minúscula). */
export const cap = (s?: string | null) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : ""

const REINFORCEMENT_ICON: Record<string, string> = {
  pelota: "sports_baseball",
  comida: "restaurant",
  caricias: "front_hand",
}

/** Icono Material según el tipo de refuerzo. */
export const reinforcementIcon = (name?: string) =>
  name ? REINFORCEMENT_ICON[name.toLowerCase()] ?? "redeem" : "redeem"

/** IDs de ejercicios (base) dominados por sesiones, según exercise_progress. */
export const masteredExerciseIds = (progress?: ExerciseProgress[]) =>
  new Set((progress ?? []).filter((p) => p.mastered).map((p) => p.exercise_id))

/**
 * Un ejercicio está "superado" si lo detectó la encuesta (dominated) o si se
 * dominó entrenando (mastered en exercise_progress).
 */
export const isSuperado = (e: PlanExerciseItem, masteredIds: Set<string>) =>
  e.dominated || masteredIds.has(e.exercise.id)
