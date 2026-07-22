import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  SurveyData,
  SurveyResponse,
  SurveySubmission,
  ValidationMetrics,
} from "@/types"

/** Preguntas SUS + escala + la respuesta previa del usuario (o null). */
export function useSurvey() {
  return useQuery({
    queryKey: ["validation-survey"],
    queryFn: async () => {
      const { data } = await api.get<SurveyData>("/validation/survey/")
      return data
    },
  })
}

/** Envía (o actualiza) la respuesta SUS del usuario. */
export function useSubmitSurvey() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: SurveySubmission) => {
      const { data } = await api.post<SurveyResponse>(
        "/validation/survey/",
        payload
      )
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["validation-survey"] })
    },
  })
}

/** Métricas agregadas de la validación (solo emails en la allowlist). */
export function useValidationMetrics() {
  return useQuery({
    queryKey: ["validation-metrics"],
    queryFn: async () => {
      const { data } = await api.get<ValidationMetrics>("/validation/metrics/")
      return data
    },
  })
}
