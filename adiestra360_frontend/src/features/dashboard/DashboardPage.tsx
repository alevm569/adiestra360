import { useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon, masteredExerciseIds, isSuperado } from "@/lib/exercise"
import { Wordmark } from "@/components/Brandmark"
import { Icon } from "@/components/Icon"
import { Ring } from "@/components/Ring"
import { BottomNav } from "@/components/BottomNav"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/stores/authStore"
import { useDogStore } from "@/stores/dogStore"
import { useDogs } from "@/features/dogs/api"
import { useDashboard } from "./api"
import { useApplyRecommendation } from "@/features/recommendations/api"
import type {
  ActivePlan,
  ActiveRecommendation,
  DashboardResponse,
  ExerciseProgress,
  PlanExerciseItem,
  SessionStats,
} from "@/types"

export function DashboardPage() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError, refetch } = useDashboard(activeDogId)

  // Sin perro activo local: resolver contra el backend (0 / 1 / varios).
  if (!activeDogId) return <DogResolver onLogout={logout} />

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

        {data && <DashboardContent data={data} dogId={activeDogId} />}
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

/**
 * Cuando no hay perro activo local (p. ej. login en otro dispositivo),
 * resuelve contra el backend:
 *  - 0 perros  → invita a crear el perfil
 *  - 1 perro   → lo selecciona y muestra el dashboard
 *  - 2+ perros → lleva al listado para elegir con cuál empezar
 */
function DogResolver({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate()
  const setActiveDog = useDogStore((s) => s.setActiveDog)
  const { data: dogs, isLoading, isError } = useDogs()

  useEffect(() => {
    if (!dogs) return
    if (dogs.length === 1) setActiveDog(dogs[0].id)
    else if (dogs.length > 1) navigate("/perros", { replace: true })
  }, [dogs, navigate, setActiveDog])

  const showSpinner = isLoading || (dogs && dogs.length >= 1)

  return (
    <div className="min-h-safe px-5 pt-safe pb-safe">
      <TopBar onLogout={onLogout} />

      {showSpinner && (
        <div className="grid place-items-center py-20 text-muted-foreground">
          <Icon name="progress_activity" className="animate-spin text-3xl" />
        </div>
      )}

      {isError && (
        <p className="mt-8 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-destructive">
          No pudimos cargar tus perros. Revisa tu conexión.
        </p>
      )}

      {dogs && dogs.length === 0 && (
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
      )}
    </div>
  )
}

/** Estado de un ejercicio según su progreso real en las sesiones. */
function exerciseState(e: PlanExerciseItem, progress?: ExerciseProgress) {
  const mastered = e.dominated || progress?.mastered
  if (mastered)
    return {
      label: "Superado",
      tone: "bg-primary-soft text-primary-deep",
      icon: "check_circle",
      fill: true,
      done: true,
    }
  if (!progress || progress.total_sessions === 0)
    return {
      label: "Empezar",
      tone: "bg-amber-soft text-amber-deep",
      icon: reinforcementIcon(e.reinforcement_type?.name),
      fill: false,
      done: false,
    }
  if (progress.success_rate >= 50)
    return {
      label: "Continuar",
      tone: "bg-amber-soft text-amber-deep",
      icon: "trending_up",
      fill: false,
      done: false,
    }
  return {
    label: "Repasar",
    tone: "bg-coral-soft text-coral-deep",
    icon: "replay",
    fill: false,
    done: false,
  }
}

function DashboardContent({
  data,
  dogId,
}: {
  data: DashboardResponse
  dogId: string
}) {
  const { dog, plan, exercise_progress, gamification, stats } = data

  const progressById = new Map(exercise_progress.map((p) => [p.exercise_id, p]))
  const masteredIds = masteredExerciseIds(exercise_progress)

  const activeExercises = (plan?.exercises ?? [])
    .filter((e) => e.active)
    .sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  // Lo que falta hoy: activos y NO superados (repasar / continuar / empezar).
  const pending = activeExercises.filter((e) => !isSuperado(e, masteredIds))
  const doneCount = activeExercises.filter((e) => isSuperado(e, masteredIds)).length
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
            <small className="text-[9px] font-extrabold text-muted-foreground">{percent}%</small>
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
            {doneCount}/{activeExercises.length} superados · {gamification.total_xp} XP
          </p>
        </div>
      </div>

      {/* Racha */}
      <div className="mb-4 flex items-center gap-3 rounded-2xl bg-amber-soft p-3 px-4">
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

      {/* Desempeño (rendimiento del entrenamiento) */}
      {stats.total_sessions > 0 && <PerformanceCard stats={stats} />}

      {/* Recomendación de la IA */}
      {data.active_recommendation && plan && (
        <RecommendationCard
          rec={data.active_recommendation}
          plan={plan}
          masteredIds={masteredIds}
          dogId={dogId}
        />
      )}

      {/* Ejercicios de hoy (solo pendientes) */}
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
          Ejercicios de hoy
        </span>
        <small className="text-xs font-extrabold text-muted-foreground">
          {pending.length} pendientes
        </small>
      </div>

      {pending.length === 0 ? (
        <p className="rounded-2xl border border-border bg-card p-4 text-center text-sm font-semibold text-muted-foreground">
          {activeExercises.length === 0
            ? "Tu plan aún no tiene ejercicios activos."
            : "¡Todo al día! No tienes ejercicios pendientes hoy. 🎉"}
        </p>
      ) : (
        pending.map((e) => {
          const st = exerciseState(e, progressById.get(e.exercise.id))
          const rowClass =
            "mb-2.5 flex items-center gap-3 rounded-2xl border border-border bg-card p-3"
          const inner = (
            <>
              <div className={cn("grid size-9 flex-none place-items-center rounded-xl", st.tone)}>
                <Icon name={st.icon} fill={st.fill} className="text-xl" />
              </div>
              <div className="min-w-0 flex-1">
                <b className="block text-sm">{cap(e.exercise.name)}</b>
                <small className="text-[11px] font-bold text-muted-foreground">
                  Refuerzo: {e.reinforcement_type?.name ?? "—"}
                </small>
              </div>
              <span className={cn("rounded-full px-2.5 py-1 text-[10px] font-extrabold", st.tone)}>
                {st.label}
              </span>
            </>
          )
          // Tocar un ejercicio abre su tutorial (cómo enseñarlo); desde ahí
          // se registra la sesión. Los superados no aparecen en "pending".
          return st.done ? (
            <div key={e.id} className={rowClass}>
              {inner}
            </div>
          ) : (
            <Link key={e.id} to={`/ejercicio/${e.exercise.id}`} className={rowClass}>
              {inner}
            </Link>
          )
        })
      )}

      {/* Registrar la sesión del día (acceso directo, sin pasar por el tutorial) */}
      {pending.length > 0 && (
        <Button
          asChild
          className="mt-3 h-12 w-full rounded-xl text-base font-extrabold"
        >
          <Link to="/sesion">
            <Icon name="check_circle" className="text-xl" />
            Registrar sesión de hoy
          </Link>
        </Button>
      )}

      {/* Logros */}
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
            <div key={i} className="rounded-2xl border border-border bg-card p-3 text-center">
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

function PerformanceCard({ stats }: { stats: SessionStats }) {
  const tiles = [
    {
      icon: "check_circle",
      value: `${Math.round(stats.success_rate)}%`,
      label: "Éxito",
      tone: "text-primary-deep",
    },
    {
      icon: "timer",
      value: stats.avg_response_time != null ? `${stats.avg_response_time}s` : "—",
      label: "Respuesta",
      tone: "text-sky-deep",
    },
    {
      icon: "history",
      value: String(stats.total_sessions),
      label: "Sesiones",
      tone: "text-amber-deep",
    },
  ]
  return (
    <div className="mb-4 rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
        Desempeño
      </div>
      <div className="flex items-center">
        {tiles.map((t, i) => (
          <div key={t.label} className="flex flex-1 items-center">
            {i > 0 && <div className="h-9 w-px bg-border" />}
            <div className="flex-1 text-center">
              <Icon name={t.icon} fill className={cn("text-xl", t.tone)} />
              <b className="mt-0.5 block font-display text-lg leading-none">{t.value}</b>
              <small className="text-[10px] font-extrabold text-muted-foreground">
                {t.label}
              </small>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function RecommendationCard({
  rec,
  plan,
  masteredIds,
  dogId,
}: {
  rec: ActiveRecommendation
  plan: ActivePlan
  masteredIds: Set<string>
  dogId: string
}) {
  const apply = useApplyRecommendation(dogId)

  // Solo los ejercicios activos que usan el refuerzo actual y NO están
  // superados (los que en verdad están costando).
  const targetIds = plan.exercises
    .filter(
      (e) =>
        e.active &&
        e.reinforcement_type?.id === rec.previous_strategy &&
        !isSuperado(e, masteredIds)
    )
    .map((e) => e.id)

  return (
    <div className="mb-4 rounded-2xl border border-coral-soft bg-coral-soft/50 p-4">
      <div className="mb-1 flex items-center gap-2 font-display text-sm font-extrabold text-coral-deep">
        <Icon name="lightbulb" fill className="text-lg" />
        La IA tiene una sugerencia
      </div>
      <p className="text-sm font-semibold">
        Prueba el refuerzo <b>{rec.recommended_strategy_name}</b> en vez de{" "}
        {rec.previous_strategy_name}.
      </p>
      {rec.reason && (
        <p className="mt-1 text-xs font-semibold text-muted-foreground">{rec.reason}</p>
      )}
      <Button
        onClick={() =>
          apply.mutate({ targetIds, newStrategyId: rec.recommended_strategy })
        }
        disabled={apply.isPending || targetIds.length === 0}
        className="mt-3 h-10 w-full rounded-xl bg-linear-to-br from-coral to-coral-deep text-sm font-extrabold"
      >
        {apply.isPending ? "Aplicando…" : `Cambiar a ${rec.recommended_strategy_name}`}
      </Button>
    </div>
  )
}
