import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
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

/** Actualiza la foto de un perro (data URL, o null para quitarla). */
export function useUpdateDogPhoto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, photo }: { id: string; photo: string | null }) => {
      const { data } = await api.put<Dog>(`/dogs/${id}/update/`, { photo })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dogs"] }),
  })
}
