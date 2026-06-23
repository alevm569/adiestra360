import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios"
import { useAuth } from "@/stores/authStore"

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"

export const api = axios.create({
  baseURL: BASE_URL,
})

// Cliente "limpio" sin interceptores, solo para renovar el token
// (evita un bucle infinito de refresh si el propio refresh diera 401).
const refreshClient = axios.create({ baseURL: BASE_URL })

// --- Request: inyecta el access token en cada petición ---
api.interceptors.request.use((config) => {
  const access = useAuth.getState().access
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

// --- Response: ante un 401, intenta renovar el access con el refresh ---
interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refresh = useAuth.getState().refresh
  if (!refresh) throw new Error("No refresh token")

  const { data } = await refreshClient.post<{ access: string }>(
    "/auth/token/refresh/",
    { refresh }
  )
  useAuth.getState().setAccess(data.access)
  return data.access
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryableRequest | undefined

    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true
      try {
        // Si ya hay un refresh en curso, reutilízalo (evita varias llamadas).
        refreshPromise = refreshPromise ?? refreshAccessToken()
        const newAccess = await refreshPromise
        refreshPromise = null

        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)
      } catch (refreshError) {
        refreshPromise = null
        useAuth.getState().logout()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
