import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"

type TabKey = "home" | "plan" | "session" | "profile"

interface Tab {
  key: TabKey
  icon: string
  label: string
  to?: string // sin `to` => aún no implementada (inerte)
}

const TABS: Tab[] = [
  { key: "home", icon: "home", label: "Inicio", to: "/" },
  { key: "plan", icon: "checklist", label: "Plan", to: "/plan" },
  { key: "session", icon: "track_changes", label: "Sesión", to: "/sesion" },
  { key: "profile", icon: "person", label: "Perfil", to: "/perfil" },
]

/** Barra de navegación inferior. Las pestañas sin ruta aún están inactivas. */
export function BottomNav({ active }: { active: TabKey }) {
  return (
    <nav
      className="flex items-center justify-around border-t border-border bg-card px-2 pt-2.5"
      style={{ paddingBottom: "calc(0.625rem + env(safe-area-inset-bottom))" }}
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active
        const cls = cn(
          "flex flex-col items-center gap-0.5 text-[10px] font-extrabold",
          isActive ? "text-primary-deep" : "text-muted-foreground",
          !tab.to && !isActive && "opacity-50"
        )
        const inner = (
          <>
            <Icon name={tab.icon} fill={isActive} className="text-2xl" />
            {tab.label}
          </>
        )
        return tab.to ? (
          <Link key={tab.key} to={tab.to} className={cls}>
            {inner}
          </Link>
        ) : (
          <span key={tab.key} className={cls} aria-disabled="true">
            {inner}
          </span>
        )
      })}
    </nav>
  )
}
