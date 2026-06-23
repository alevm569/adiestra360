import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { AuthTokens, User } from "@/types"

interface AuthState {
  access: string | null
  refresh: string | null
  user: User | null
  isAuthenticated: boolean
  setAuth: (tokens: AuthTokens, user: User) => void
  setAccess: (access: string) => void
  logout: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      isAuthenticated: false,
      setAuth: (tokens, user) =>
        set({
          access: tokens.access,
          refresh: tokens.refresh,
          user,
          isAuthenticated: true,
        }),
      setAccess: (access) => set({ access }),
      logout: () =>
        set({
          access: null,
          refresh: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "adiestra-auth",
      // Solo persistimos lo necesario en localStorage.
      partialize: (s) => ({
        access: s.access,
        refresh: s.refresh,
        user: s.user,
        isAuthenticated: s.isAuthenticated,
      }),
    }
  )
)
