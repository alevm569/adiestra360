import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Wordmark } from "@/components/Brandmark"
import { Icon } from "@/components/Icon"
import { Ring } from "@/components/Ring"
import { BottomNav } from "@/components/BottomNav"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/stores/authStore"
import { useDogStore } from "@/stores/dogStore"
import { useDashboard } from "./api"
import type { DashboardResponse, PlanExerciseItem } from "@/types"

const cap = (s?: string | null) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : ""

const REINFORCEMENT_ICON: Record<string, string> = {
  pelota: "sports_baseball",
  comida: "restaurant",
  caricias: "front_hand",
}
const reinforcementIcon = (name?: string) =>
  name ? REINFORCEMENT_ICON[name.toLowerCase()] ?? "redeem" : "redeem"

export function DashboardPage() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError, refetch } = useDashboard(activeDogId)

  // Aún no hay perro: invitar al onboarding.
  if (!activeDogId) {
    return (
      <div className="min-h-safe px-5 pt-safe pb-safe">
        <TopBar onLogout={logout} />
        <div className="mt-8 rounded-2xl border border-border bg-card p-6 text-center shadow-sm">
          <div className="mx-auto mb-3 flex size-14 items-center justify-center rounded-2xl bg-coral-soft text-coral-deep">
            <Icon name="pets" fill className="text-3xl" />
          </div>
          <p className="mb-4 text-sm font-semibold text-muted-foreground">
            Aún no registras a tu perro. Crea su perfil y la IA armará su plan.
          </p>
          <Button asChild className="h-12 w-full rounded-xl text-base font-extrabold">
            <Link to="/onboarding/dog">
              Crear perfil de mi perro
              <Icon name="arrow_forward" className="text-xl" />
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-dvh flex-col">
      <div className="flex-1 overflow-y-auto px-5 pt-safe">
        <TopBar onLogout={logout} />

        <div className="mt-1 mb-4">
          <p className="text-sm font-extrabold text-muted-foreground">
            Hola, {user?.name ?? "entrenador"}
          </p>
          <h1 className="mt-0.5 text-2xl font-bold">Hoy toca entrenar</h1>
        </div>

        {isLoading && (
          <div className="grid place-items-center py-20 text-muted-foreground">
            <Icon name="progress_activity" className="animate-spin text-3xl" />
          </div>
        )}

        {isError && (
          <div className="rounded-2xl border border-border bg-card p-6 text-center">
            <p className="mb-3 text-sm font-semibold text-destructive">
              No pudimos cargar el dashboard.
            </p>
            <Button variant="outline" onClick={() => refetch()} className="rounded-xl">
              Reintentar
            </Button>
          </div>
        )}

        {data && <DashboardContent data={data} />}
      </div>

      <BottomNav active="home" />
    </div>
  )
}

function TopBar({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="flex items-center justify-between py-3">
      <Wordmark size={34} />
      <Button variant="ghost" size="icon" onClick={onLogout} aria-label="Cerrar sesión">
        <Icon name="logout" className="text-xl" />
      </Button>
    </div>
  )
}

function DashboardContent({ data }: { data: DashboardResponse }) {
  const { dog, plan, exercise_progress, gamification } = data

  const activeExercises = (plan?.exercises ?? [])
    .filter((e) => e.active)
    .sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  const masteredIds = new Set(
    exercise_progress.filter((p) => p.mastered).map((p) => p.exercise_id)
  )
  const isDone = (e: PlanExerciseItem) =>
    e.dominated || masteredIds.has(e.exercise.id)

  const doneCount = activeExercises.filter(isDone).length
  const percent = activeExercises.length
    ? Math.round((doneCount / activeExercises.length) * 100)
    : 0

  const streak = gamification.streak.current
  const level = dog.training_level ?? 1
  const achievements = gamification.recent_achievements.slice(0, 3)

  return (
    <div className="pb-4">
      {/* Tarjeta del perro */}
      <div className="mb-3 flex items-center gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm">
        <Ring percent={percent} size={76}>
          <div>
            <b className="block font-display text-lg leading-none">Nv {level}</b>
            <small className="text-[9px] font-extrabold text-muted-foreground">
              {percent}%
            </small>
          </div>
        </Ring>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between">
            <b className="truncate font-display text-lg">{dog.name}</b>
            <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-extrabold text-primary-deep">
              {gamification.user_level}
            </span>
          </div>
          <p className="mb-2 truncate text-xs font-bold text-muted-foreground">
            {[cap(dog.breed), dog.energy_level && `energía ${dog.energy_level}`]
              .filter(Boolean)
              .join(" · ")}
          </p>
          <div className="h-2 overflow-hidden rounded-full bg-primary-soft">
            <div
              className="h-full rounded-full bg-linear-to-r from-primary to-primary-deep"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="mt-1.5 text-[10px] font-extrabold text-muted-foreground">
            {doneCount}/{activeExercises.length} dominados · {gamification.total_xp} XP
          </p>
        </div>
      </div>

      {/* Racha */}
      <div className="mb-5 flex items-center gap-3 rounded-2xl bg-linear-to-br from-amber-soft to-amber-soft p-3 px-4">
        <div className="grid size-10 place-items-center rounded-xl bg-card/60 text-coral">
          <Icon name="local_fire_department" fill className="text-2xl" />
        </div>
        <div className="flex-1">
          <b className="block font-display text-base">
            {streak > 0 ? `Racha de ${streak} días` : "Empieza tu racha hoy"}
          </b>
          <span className="text-xs font-extrabold text-muted-foreground">
            Récord: {gamification.streak.longest} días
          </span>
        </div>
      </div>

      {/* Ejercicios de hoy */}
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
          Ejercicios de hoy
        </span>
        <small className="text-xs font-extrabold text-muted-foreground">
          {doneCount} / {activeExercises.length}
        </small>
      </div>

      {activeExercises.length === 0 ? (
        <p className="rounded-2xl border border-border bg-card p-4 text-center text-sm font-semibold text-muted-foreground">
          Tu plan aún no tiene ejercicios activos.
        </p>
      ) : (
        activeExercises.map((e) => {
          const done = isDone(e)
          return (
            <div
              key={e.id}
              className="mb-2.5 flex items-center gap-3 rounded-2xl border border-border bg-card p-3"
            >
              <div
                className={cn(
                  "grid size-9 flex-none place-items-center rounded-xl",
                  done
                    ? "bg-primary-soft text-primary-deep"
                    : "bg-amber-soft text-amber-deep"
                )}
              >
                <Icon
                  name={done ? "check_circle" : reinforcementIcon(e.reinforcement_type?.name)}
                  fill={done}
                  className="text-xl"
                />
              </div>
              <div className="min-w-0 flex-1">
                <b className="block text-sm">{cap(e.exercise.name)}</b>
                <small className="text-[11px] font-bold text-muted-foreground">
                  Refuerzo: {e.reinforcement_type?.name ?? "—"}
                </small>
              </div>
              <span
                className={cn(
                  "rounded-full px-2.5 py-1 text-[10px] font-extrabold",
                  done
                    ? "bg-primary-soft text-primary-deep"
                    : "bg-amber text-amber-deep"
                )}
              >
                {done ? "Listo" : "Seguir"}
              </span>
            </div>
          )
        })
      )}

      {/* Logros recientes */}
      <div className="mb-2.5 mt-5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
        Logros recientes
      </div>
      {achievements.length === 0 ? (
        <p className="rounded-2xl border border-border bg-card p-4 text-center text-sm font-semibold text-muted-foreground">
          Aún sin logros — ¡completa tu primera sesión!
        </p>
      ) : (
        <div className="grid grid-cols-3 gap-2.5">
          {achievements.map((a, i) => (
            <div
              key={i}
              className="rounded-2xl border border-border bg-card p-3 text-center"
            >
              <div className="mx-auto mb-1.5 grid size-10 place-items-center rounded-full bg-amber-soft text-amber-deep">
                <Icon name="trophy" fill className="text-xl" />
              </div>
              <small className="block text-[9.5px] font-extrabold text-muted-foreground">
                {a.name}
              </small>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
