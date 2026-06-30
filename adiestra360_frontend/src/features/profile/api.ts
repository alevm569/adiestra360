import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { UserAchievementsResponse, UserStats } from "@/types"

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
