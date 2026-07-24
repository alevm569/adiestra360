import { useState } from "react"
import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { BottomNav } from "@/components/BottomNav"
import { Button } from "@/components/ui/button"
import { ProgressRulesSheet } from "@/features/help/ProgressRules"
import { useAuth } from "@/stores/authStore"
import { useUserStats, useUserAchievements } from "./api"
import type { UserStats } from "@/types"

const LEVEL_FLOOR: Record<string, number> = {
  Principiante: 0,
  Intermedio: 100,
  Avanzado: 300,
}

export function ProfilePage() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)
  const stats = useUserStats()
  const achievements = useUserAchievements()
  const [rulesOpen, setRulesOpen] = useState(false)

  return (
    <div className="flex h-dvh flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-5 pt-safe">
        <div className="flex items-center justify-between py-3">
          <h2 className="text-xl font-bold">Mi perfil</h2>
          <span className="grid size-9 place-items-center rounded-xl border border-border bg-card text-muted-foreground">
            <Icon name="settings" className="text-xl" />
          </span>
        </div>

        {/* Identidad */}
        <div className="mb-5 text-center">
          <div className="mx-auto mb-2.5 grid size-24 place-items-center rounded-full border-[3px] border-card bg-linear-to-br from-primary to-primary-deep text-white shadow-sm">
            <Icon name="person" fill className="text-5xl" />
          </div>
          <h2 className="font-display text-xl font-bold">{user?.name ?? "Entrenador"}</h2>
          <p className="text-xs font-bold text-muted-foreground">{user?.email}</p>
        </div>

        {/* Stats */}
        {stats.data && <StatsRow stats={stats.data} />}

        {/* Progreso de nivel */}
        {stats.data && <LevelCard stats={stats.data} />}

        {/* Logros */}
        <div className="mb-2.5 mt-5 flex items-center justify-between">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
            Mis logros
          </span>
          {achievements.data && (
            <small className="text-xs font-extrabold text-muted-foreground">
              {achievements.data.total_earned} / {achievements.data.total_available}
            </small>
          )}
        </div>

        {achievements.isLoading && (
          <div className="grid place-items-center py-6 text-muted-foreground">
            <Icon name="progress_activity" className="animate-spin text-2xl" />
          </div>
        )}

        {achievements.data && (
          <div className="grid grid-cols-3 gap-2.5">
            {achievements.data.earned.map((e) => (
              <Badge key={e.id} name={e.achievement.name} earned />
            ))}
            {achievements.data.pending.map((p) => (
              <Badge key={p.id} name={p.name} earned={false} />
            ))}
          </div>
        )}

        {/* Menú */}
        <div className="mt-6 mb-4">
          <MenuItem icon="pets" label="Mis perros" to="/perros" />
          <MenuItem icon="history" label="Historial de sesiones" to="/historial" />
          <MenuItem
            icon="help"
            label="Cómo funciona el progreso"
            onClick={() => setRulesOpen(true)}
          />
          <MenuItem icon="edit" label="Editar perfil" to="/perfil/editar" />
          <MenuItem
            icon="rate_review"
            label="Cuestionario de usabilidad"
            to="/validacion/encuesta"
          />
          {user?.is_metrics_admin && (
            <MenuItem
              icon="analytics"
              label="Panel de validación"
              to="/validacion/metricas"
            />
          )}
          <MenuItem icon="logout" label="Cerrar sesión" danger onClick={logout} />
        </div>
      </div>

      {rulesOpen && <ProgressRulesSheet onClose={() => setRulesOpen(false)} />}

      <BottomNav active="profile" />
    </div>
  )
}

function StatsRow({ stats }: { stats: UserStats }) {
  const items = [
    { value: stats.streak.current, label: "Racha" },
    { value: stats.total_xp, label: "XP" },
    { value: stats.achievements_earned, label: "Logros" },
  ]
  return (
    <div className="flex items-center rounded-2xl border border-border bg-card p-3.5 shadow-sm">
      {items.map((it, i) => (
        <div key={it.label} className="flex flex-1 items-center">
          {i > 0 && <div className="h-8 w-px bg-border" />}
          <div className="flex-1 text-center">
            <b className="block font-display text-xl">{it.value}</b>
            <small className="text-[10px] font-extrabold text-muted-foreground">
              {it.label}
            </small>
          </div>
        </div>
      ))}
    </div>
  )
}

function LevelCard({ stats }: { stats: UserStats }) {
  const floor = LEVEL_FLOOR[stats.user_level] ?? 0
  const ceil = stats.next_level_xp
  const fraction = ceil ? Math.min(1, (stats.total_xp - floor) / (ceil - floor)) : 1

  return (
    <div className="mt-3 rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-display text-sm font-bold">Nivel {stats.user_level}</span>
        <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-extrabold text-primary-deep">
          {stats.total_xp} XP
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-primary-soft">
        <div
          className="h-full rounded-full bg-linear-to-r from-primary to-primary-deep"
          style={{ width: `${Math.round(fraction * 100)}%` }}
        />
      </div>
      <p className="mt-1.5 text-[10px] font-extrabold text-muted-foreground">
        {ceil
          ? `Te faltan ${stats.xp_to_next_level} XP para el siguiente nivel`
          : "¡Nivel máximo alcanzado!"}
      </p>
    </div>
  )
}

function Badge({ name, earned }: { name: string; earned: boolean }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-3 text-center",
        !earned && "opacity-50"
      )}
    >
      <div
        className={cn(
          "mx-auto mb-1.5 grid size-10 place-items-center rounded-full",
          earned ? "bg-amber-soft text-amber-deep" : "bg-muted text-muted-foreground"
        )}
      >
        <Icon name={earned ? "trophy" : "lock"} fill={earned} className="text-xl" />
      </div>
      <small className="block text-[9.5px] font-extrabold text-muted-foreground">{name}</small>
    </div>
  )
}

function MenuItem({
  icon,
  label,
  danger,
  to,
  onClick,
}: {
  icon: string
  label: string
  danger?: boolean
  to?: string
  onClick?: () => void
}) {
  const inner = (
    <>
      <span
        className={cn(
          "grid size-9 flex-none place-items-center rounded-xl",
          danger ? "bg-coral-soft text-coral" : "bg-primary-soft text-primary-deep"
        )}
      >
        <Icon name={icon} className="text-lg" />
      </span>
      {label}
      <Icon name="chevron_right" className="ml-auto text-xl text-muted-foreground" />
    </>
  )
  const className =
    "flex w-full items-center gap-3 border-b border-border py-3.5 text-left text-sm font-bold"

  if (to) {
    return (
      <Link to={to} className={className}>
        {inner}
      </Link>
    )
  }
  return (
    <button type="button" onClick={onClick} className={className}>
      {inner}
    </button>
  )
}
