import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAuth } from "@/stores/authStore"
import type { AuthResponse } from "@/types"

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload {
  name: string
  email: string
  password: string
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
  const setAuth = useAuth((s) => s.setAuth)
  return useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => setAuth(data.tokens, data.user),
  })
}

/** Registra un usuario nuevo y lo deja autenticado. */
export function useRegister() {
  const setAuth = useAuth((s) => s.setAuth)
  return useMutation({
    mutationFn: registerRequest,
    onSuccess: (data) => setAuth(data.tokens, data.user),
  })
}
