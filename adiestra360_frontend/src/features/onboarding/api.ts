import { useMutation, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  CreateDogPayload,
  CreateDogResponse,
  QuizQuestion,
} from "@/types"

/** Obtiene las 11 preguntas de la encuesta inicial. */
export function useQuiz() {
  return useQuery({
    queryKey: ["quiz"],
    queryFn: async () => {
      const { data } = await api.get<QuizQuestion[]>("/auth/quiz/")
      return data
    },
    staleTime: Infinity, // las preguntas no cambian durante la sesión
  })
}

/**
 * Crea el perro + procesa la encuesta. El backend genera el plan
 * automáticamente y devuelve el dog + plan_id.
 */
export function useCreateDog() {
  return useMutation({
    mutationFn: async (payload: CreateDogPayload) => {
      const { data } = await api.post<CreateDogResponse>("/dogs/create/", payload)
      return data
    },
  })
}
