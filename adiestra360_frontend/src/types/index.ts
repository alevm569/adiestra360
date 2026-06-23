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
