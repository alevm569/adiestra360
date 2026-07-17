// Tipos que reflejan los modelos del backend Django.
// OJO: todos los IDs son UUID (string), no números.

export interface User {
  id: string
  email: string
  name: string
}

export interface UserStreak {
  current_streak: number
  longest_streak: number
  last_activity_date: string | null
}

export interface AuthTokens {
  access: string
  refresh: string
}

// Respuesta de POST /auth/login/ y /auth/register/
export interface AuthResponse {
  user: User
  streak?: UserStreak | null
  tokens: AuthTokens
}

export interface Dog {
  id: string
  user: string
  name: string
  breed: string | null
  age_months: number | null
  weight: string | null // DecimalField llega como string en DRF
  energy_level: string | null
  training_level: number | null
  created_at: string
}

export interface TrainingLevel {
  id: string
  name: string
  description: string | null
}

export interface Exercise {
  id: string
  level: string
  name: string
  description: string | null
  difficulty: number | null
  estimated_duration: number | null
}

export interface TrainingPlan {
  id: string
  dog: string
  current_level: string | null
  active: boolean
  created_at: string
}

export interface TrainingPlanExercise {
  id: string
  training_plan: string
  exercise: string
  reinforcement_type: string
  order_number: number | null
  dominated: boolean
  active: boolean
}

export interface QuizQuestion {
  id: number
  category: string
  question: string
  options: string[]
  exercise_related?: string
  reinforcement_related?: string
  experience_related?: string
}

/** Respuesta a una pregunta del quiz (lo que espera el backend). */
export interface QuizAnswer {
  id: number
  answer: string
  exercise_related?: string | null
  reinforcement_related?: string | null
  experience_related?: string | null
}

/** Datos del perro que se capturan en el onboarding. */
export interface DogDraft {
  name: string
  breed: string
  age_months: number | null
  weight: number | null
  energy_level: "bajo" | "medio" | "alto"
}

/** Body de POST /dogs/create/ */
export interface CreateDogPayload {
  dog: DogDraft
  quiz_answers: QuizAnswer[]
}

/** Respuesta de POST /dogs/create/ (crea perro + plan). */
export interface CreateDogResponse {
  dog: Dog
  training_level: number
  experience_level: string
  initial_reinforcement: string
  dominated_exercises: string[]
  plan_id: string
  message: string
}

// ---- Plan activo / dashboard (respuestas anidadas reales) ----
export interface PlanExerciseItem {
  id: string
  exercise: {
    id: string
    name: string
    description: string | null
    difficulty: number | null
    estimated_duration: number | null
    level: string
    level_name: string
  }
  reinforcement_type: { id: string; name: string }
  order_number: number | null
  dominated: boolean
  active: boolean
}

export interface ActivePlan {
  id: string
  dog: string
  current_level: string | null
  current_level_name: string
  active: boolean
  created_at: string
  exercises: PlanExerciseItem[]
}

export interface SessionStats {
  total_sessions: number
  success_rate: number
  avg_response_time: number | null
  last_session: string | null
}

export interface ExerciseProgress {
  exercise_id: string
  exercise_name: string
  total_sessions: number
  success_rate: number
  mastered: boolean
}

export interface Achievement {
  name: string
  xp_reward: number
  earned_at: string
}

export interface Gamification {
  total_xp: number
  user_level: string
  streak: { current: number; longest: number }
  recent_achievements: Achievement[]
}

/** Respuesta de GET /gamification/dashboard/<dog_id>/ */
export interface DashboardResponse {
  dog: {
    id: string
    name: string
    breed: string | null
    training_level: number | null
    energy_level: string | null
  }
  plan: ActivePlan | null
  stats: SessionStats
  exercise_progress: ExerciseProgress[]
  gamification: Gamification
  active_recommendation: ActiveRecommendation | null
}

// ---- Técnicas (cómo enseñar cada ejercicio) ----

/** Variante equivalente de un paso (p. ej. con golosina en vez de la cadena). */
export interface StepAlternative {
  title: string
  text: string
  image: string | null
  /** Cuándo conviene usarla. */
  when: string
}

export interface TechniqueStep {
  order: number
  title: string
  text: string
  image: string | null
  alternative?: StepAlternative | null
}

export interface CommonError {
  error: string
  correccion: string
}

/** Tutorial completo de un ejercicio (de la teoría). */
export interface Technique {
  code: string | null
  objetivo: string | null
  prerrequisito: string | null
  duracion: string | null
  frecuencia: string | null
  competencias: string[]
  materiales: string[]
  reglas: string[]
  steps: TechniqueStep[]
  errores_comunes: CommonError[]
  criterio_avanzar: string[]
}

export interface ExerciseTechniqueResponse {
  exercise: {
    id: string
    name: string
    description: string | null
    difficulty: number | null
    estimated_duration: number | null
  }
  motivation: string
  recommended_reinforcement: string | null
  /** Si conviene destacar la variante alternativa para este perro. */
  suggest_alternative: boolean
  alternative_reason: string | null
  technique: Technique | null
}

// ---- Perfil / gamificación ----
export interface UserStats {
  total_xp: number
  user_level: string
  next_level_xp: number | null
  xp_to_next_level: number
  streak: { current: number; longest: number }
  achievements_earned: number
}

export interface AchievementDetail {
  id: string
  name: string
  description: string | null
  xp_reward: number | null
}

export interface EarnedAchievement {
  id: string
  achievement: AchievementDetail
  earned_at: string
}

export interface UserAchievementsResponse {
  earned: EarnedAchievement[]
  pending: AchievementDetail[]
  total_earned: number
  total_available: number
}

/** Recomendación de la IA para cambiar el refuerzo (cuando el perro va < 50%). */
export interface ActiveRecommendation {
  id: string
  dog: string
  previous_strategy: string
  previous_strategy_name: string
  recommended_strategy: string
  recommended_strategy_name: string
  reason: string
  created_at: string
}
