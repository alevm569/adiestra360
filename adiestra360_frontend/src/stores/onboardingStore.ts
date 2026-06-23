import { create } from "zustand"
import type { DogDraft, QuizAnswer } from "@/types"

/**
 * Borrador del onboarding: acumula los datos del perro y las respuestas
 * de la encuesta entre pasos. Al final se mandan juntos a POST /dogs/create/.
 * No se persiste: si recargas, el onboarding empieza de nuevo.
 */
interface OnboardingState {
  dog: DogDraft | null
  answers: QuizAnswer[]
  setDog: (dog: DogDraft) => void
  setAnswers: (answers: QuizAnswer[]) => void
  reset: () => void
}

export const useOnboarding = create<OnboardingState>((set) => ({
  dog: null,
  answers: [],
  setDog: (dog) => set({ dog }),
  setAnswers: (answers) => set({ answers }),
  reset: () => set({ dog: null, answers: [] }),
}))
