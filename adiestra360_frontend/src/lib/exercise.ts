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

/** Resultado de un ejercicio según los criterios de avance marcados. */
export type SessionResult = "reforzar" | "bien" | "excelente"

/**
 * Deriva el resultado de un ejercicio a partir del checklist de criterios.
 * Los criterios vienen ordenados por relevancia: el #0 (más relevante) es la
 * "compuerta". Con `n` criterios y `k` marcados:
 *  - Excelente: todos marcados (k = n).
 *  - Va bien: cumple el #0 pero no todos → va por buen camino.
 *  - Reforzar: falla el #0 (el más importante) → necesita más práctica.
 * Sin criterios cargados, se considera "bien" (no bloquea el registro).
 */
export function criteriaResult(total: number, checked: Set<number>): SessionResult {
  if (total <= 0) return "bien"
  if (checked.size >= total) return "excelente"
  return checked.has(0) ? "bien" : "reforzar"
}

/** Meta visual (etiqueta, icono, tono) de cada resultado. */
export const RESULT_META: Record<
  SessionResult,
  { label: string; icon: string; tone: string }
> = {
  reforzar: { label: "Reforzar", icon: "replay", tone: "bg-coral-soft text-coral-deep" },
  bien: { label: "Va bien", icon: "trending_up", tone: "bg-amber-soft text-amber-deep" },
  excelente: {
    label: "Excelente",
    icon: "check_circle",
    tone: "bg-primary-soft text-primary-deep",
  },
}
