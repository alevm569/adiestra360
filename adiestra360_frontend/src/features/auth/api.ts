import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { startSession } from "@/lib/session"
import type { AuthResponse } from "@/types"

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload {
  name: string
  email: string
  password: string
  /** Consentimiento informado (uso de datos para la tesis). Obligatorio. */
  research_consent: boolean
}

interface PasswordResetRequestPayload {
  email: string
}

interface PasswordResetConfirmPayload {
  email: string
  code: string
  new_password: string
}

/** Respuesta de POST /auth/password-reset/ (siempre genérica). */
interface PasswordResetRequestResponse {
  message: string
  expires_in_minutes: number
}

async function loginRequest(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/login/", payload)
  return data
}

async function registerRequest(payload: RegisterPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/register/", payload)
  return data
}

/** Inicia sesión y guarda tokens + usuario en el store de auth. */
export function useLogin() {
  return useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => startSession(data.tokens, data.user),
  })
}

/** Registra un usuario nuevo y lo deja autenticado. */
export function useRegister() {
  return useMutation({
    mutationFn: registerRequest,
    onSuccess: (data) => startSession(data.tokens, data.user),
  })
}

/** Paso 1 de la recuperación: pide el código de 6 dígitos por correo. */
export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: async (payload: PasswordResetRequestPayload) => {
      const { data } = await api.post<PasswordResetRequestResponse>(
        "/auth/password-reset/",
        payload
      )
      return data
    },
  })
}

/**
 * Paso 2: cambia la contraseña con el código. El backend devuelve tokens, así
 * que el usuario entra directo sin volver a escribir lo que acaba de crear.
 */
export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: async (payload: PasswordResetConfirmPayload) => {
      const { data } = await api.post<AuthResponse>(
        "/auth/password-reset/confirm/",
        payload
      )
      return data
    },
    onSuccess: (data) => startSession(data.tokens, data.user),
  })
}

/** Mensaje de error del backend (campo `error`) o uno genérico de respaldo. */
export function apiErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { error?: string } } })?.response
    ?.data?.error
  return detail || fallback
}
