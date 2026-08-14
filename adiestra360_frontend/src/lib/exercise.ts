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
 * Un ejercicio está "superado" cuando lo dice `exercise_progress.mastered`, que
 * el backend calcula con la regla de desbloqueo (`check_exercise_mastered`).
 *
 * OJO: `dominated` (lo que dijo la encuesta de alta) NO basta. La regla del
 * backend pide una sesión Excelente de confirmación incluso para los ejercicios
 * que el dueño marcó como sabidos, y `check_level_completed` la exige para
 * subir de nivel. Cuando aquí se daban por superados sin más, esos ejercicios
 * desaparecían de la sesión del día, nunca recibían su confirmación y el perro
 * se quedaba atascado en el nivel para siempre.
 */
export const isSuperado = (e: PlanExerciseItem, masteredIds: Set<string>) =>
  masteredIds.has(e.exercise.id)

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

/**
 * Resultado de una sesión ya guardada, reconstruido desde el checklist.
 * Misma regla que el backend (`session_is_excellent`): con todos los criterios
 * cumplidos es Excelente; si no, `success` decide entre "va bien" y "reforzar".
 * Las sesiones antiguas (sin checklist) se evalúan solo por `success`.
 */
export const storedSessionResult = (s: {
  success: boolean | null
  criteria_met: number | null
  criteria_total: number | null
}): SessionResult => {
  if (s.criteria_total && (s.criteria_met ?? 0) >= s.criteria_total) return "excelente"
  return s.success ? "bien" : "reforzar"
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
