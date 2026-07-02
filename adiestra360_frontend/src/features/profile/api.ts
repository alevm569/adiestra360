import { useMutation, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAuth } from "@/stores/authStore"
import type { User, UserAchievementsResponse, UserStats } from "@/types"

/** XP total, nivel del usuario, progreso al siguiente nivel y racha. */
export function useUserStats() {
  return useQuery({
    queryKey: ["user-stats"],
    queryFn: async () => {
      const { data } = await api.get<UserStats>("/gamification/stats/")
      return data
    },
  })
}

/** Logros ganados y pendientes del usuario. */
export function useUserAchievements() {
  return useQuery({
    queryKey: ["user-achievements"],
    queryFn: async () => {
      const { data } = await api.get<UserAchievementsResponse>(
        "/gamification/my-achievements/"
      )
      return data
    },
  })
}

/** Edita el perfil (nombre) y actualiza el usuario en el store de auth. */
export function useUpdateProfile() {
  const setUser = useAuth((s) => s.setUser)
  return useMutation({
    mutationFn: async (payload: { name: string }) => {
      const { data } = await api.put<User>("/auth/profile/update/", payload)
      return data
    },
    onSuccess: (user) => setUser(user),
  })
}
