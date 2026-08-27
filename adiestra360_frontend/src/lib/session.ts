import { queryClient } from "@/lib/queryClient"
import { useAuth } from "@/stores/authStore"
import { useDogStore } from "@/stores/dogStore"
import type { AuthTokens, User } from "@/types"

/**
 * Cierre de sesión único de la app.
 *
 * Además de borrar los tokens hay que tirar la caché de React Query: vive en
 * memoria y no está atada a la cuenta, así que sin esto la siguiente sesión en
 * el mismo dispositivo veía los perros y el dashboard del usuario anterior
 * mientras la caché seguía "fresca".
 *
 * La selección de perro no se borra: va firmada con el dueño (ver dogStore),
 * de modo que otra cuenta la ignora y la misma cuenta la recupera.
 */
export function signOut() {
  useAuth.getState().logout()
  queryClient.clear()
}

/** Abre sesión: descarta lo cacheado de la sesión anterior y guarda la nueva. */
export function startSession(tokens: AuthTokens, user: User) {
  const previous = useAuth.getState().user
  queryClient.clear()
  // Cuenta distinta: la selección guardada ya no aplica (el guard la ignora,
  // pero así tampoco queda el id del perro ajeno en el dispositivo).
  if (previous && previous.id !== user.id) {
    useDogStore.getState().clearActiveDog()
  }
  useAuth.getState().setAuth(tokens, user)
}
