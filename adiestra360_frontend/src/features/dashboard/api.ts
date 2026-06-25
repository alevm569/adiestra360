import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { DashboardResponse } from "@/types"

/** Dashboard unificado del perro: plan + stats + racha + logros. */
export function useDashboard(dogId: string | null) {
  return useQuery({
    queryKey: ["dashboard", dogId],
    queryFn: async () => {
      const { data } = await api.get<DashboardResponse>(
        `/gamification/dashboard/${dogId}/`
      )
      return data
    },
    enabled: !!dogId,
  })
}
