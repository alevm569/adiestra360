import { QueryClient } from "@tanstack/react-query"

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 min: evita refetch agresivo
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
