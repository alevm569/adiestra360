import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Dog } from "@/types"

/** Lista los perros del usuario autenticado. */
export function useDogs() {
  return useQuery({
    queryKey: ["dogs"],
    queryFn: async () => {
      const { data } = await api.get<Dog[]>("/dogs/")
      return data
    },
  })
}
