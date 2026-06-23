import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "@/stores/authStore"

/** Bloquea rutas privadas: si no hay sesión, manda al login. */
export function ProtectedRoute() {
  const isAuthenticated = useAuth((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Outlet />
}
