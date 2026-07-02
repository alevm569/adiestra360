import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import { capacitorStorage } from "@/lib/capacitorStorage"
import type { AuthTokens, User } from "@/types"

interface AuthState {
  access: string | null
  refresh: string | null
  user: User | null
  isAuthenticated: boolean
  setAuth: (tokens: AuthTokens, user: User) => void
  setAccess: (access: string) => void
  setUser: (user: User) => void
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
      setUser: (user) => set({ user }),
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
      storage: createJSONStorage(() => capacitorStorage),
      partialize: (s) => ({
        access: s.access,
        refresh: s.refresh,
        user: s.user,
        isAuthenticated: s.isAuthenticated,
      }),
    }
  )
)
