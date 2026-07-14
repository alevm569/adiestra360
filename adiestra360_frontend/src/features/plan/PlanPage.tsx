import { Link, Navigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon, masteredExerciseIds, isSuperado } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Ring } from "@/components/Ring"
import { BottomNav } from "@/components/BottomNav"
import { Button } from "@/components/ui/button"
import { useDogStore } from "@/stores/dogStore"
import { useDashboard } from "@/features/dashboard/api"
import { useRecommendationHistory } from "@/features/recommendations/api"
import type { PlanExerciseItem } from "@/types"

const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "short" })
  } catch {
    return ""
  }
}

function statusOf(e: PlanExerciseItem, masteredIds: Set<string>) {
  if (isSuperado(e, masteredIds))
    return { label: "Superado", tone: "bg-primary-soft text-primary-deep", icon: "check_circle", fill: true }
  if (e.active)
    return {
      label: "En progreso",
      tone: "bg-amber-soft text-amber-deep",
      icon: reinforcementIcon(e.reinforcement_type?.name),
      fill: false,
    }
  return { label: "Pendiente", tone: "bg-muted text-muted-foreground", icon: "lock", fill: false }
}

export function PlanPage() {
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError } = useDashboard(activeDogId)
  const history = useRecommendationHistory(activeDogId)
  const plan = data?.plan

  if (!activeDogId) return <Navigate to="/" replace />

  const masteredIds = masteredExerciseIds(data?.exercise_progress)
  const all = plan?.exercises ?? []
  const levelExercises = all.filter(
    (e) => e.exercise.level_name === plan?.current_level_name
  )
  const list = (levelExercises.length ? levelExercises : all).sort(
    (a, b) => (a.order_number ?? 0) - (b.order_number ?? 0)
  )
  const dominated = list.filter((e) => isSuperado(e, masteredIds)).length

  return (
    <div className="flex h-dvh flex-col">
      <div className="flex-1 overflow-y-auto px-5 pt-safe">
        <div className="py-3">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
            Plan activo
          </span>
          <div className="mt-0.5 flex items-center justify-between">
            <h1 className="text-2xl font-bold">{plan?.current_level_name ?? "Tu plan"}</h1>
            {plan?.active && (
              <span className="rounded-full bg-primary-soft px-2.5 py-1 text-[10px] font-extrabold text-primary-deep">
                Activo
              </span>
            )}
          </div>
        </div>

        {isLoading && (
          <div className="grid place-items-center py-20 text-muted-foreground">
            <Icon name="progress_activity" className="animate-spin text-3xl" />
          </div>
        )}

        {(isError || (!isLoading && !plan)) && (
          <p className="rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-muted-foreground">
            Aún no hay un plan activo para tu perro.
          </p>
        )}

        {plan && list.length > 0 && (
          <>
            {/* Resumen de progreso */}
            <div className="mb-5 flex items-center gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm">
              <Ring percent={Math.round((dominated / list.length) * 100)} size={62} thickness={7}>
                <b className="font-display text-sm">
                  {dominated}/{list.length}
                </b>
              </Ring>
              <div className="flex-1">
                <b className="block font-display text-sm">
                  {dominated === list.length
                    ? "¡Nivel completado!"
                    : dominated > 0
                      ? "Vas muy bien"
                      : "Empieza tu plan"}
                </b>
                <p className="mt-0.5 text-xs font-bold text-muted-foreground">
                  {dominated} de {list.length} ejercicios dominados en este nivel
                </p>
              </div>
            </div>

            <div className="mb-2.5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
              Ejercicios del plan
            </div>

            {list.map((e) => {
              const st = statusOf(e, masteredIds)
              return (
                <Link
                  key={e.id}
                  to={`/ejercicio/${e.exercise.id}`}
                  className={cn(
                    "mb-2.5 flex items-center gap-3 rounded-2xl border border-border bg-card p-3",
                    !e.active && !isSuperado(e, masteredIds) && "opacity-60"
                  )}
                >
                  <span className="grid size-6 flex-none place-items-center rounded-lg bg-muted font-display text-xs font-extrabold text-muted-foreground">
                    {e.order_number ?? "·"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <b className="block text-sm">{cap(e.exercise.name)}</b>
                    <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-extrabold text-muted-foreground">
                      <Icon name={reinforcementIcon(e.reinforcement_type?.name)} className="text-xs" />
                      {e.reinforcement_type?.name ?? "—"}
                    </span>
                  </div>
                  <span className={cn("rounded-full px-2.5 py-1 text-[10px] font-extrabold", st.tone)}>
                    {st.label}
                  </span>
                  <Icon name="chevron_right" className="text-lg text-muted-foreground" />
                </Link>
              )
            })}

            <Button
              asChild
              className="my-4 h-12 w-full rounded-xl text-base font-extrabold"
            >
              <Link to="/sesion">
                <Icon name="track_changes" className="text-xl" />
                Registrar sesión de hoy
              </Link>
            </Button>
          </>
        )}

        {/* Historial de consejos de la IA */}
        {history.data && history.data.length > 0 && (
          <div className="mb-6">
            <div className="mb-2.5 flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
              <Icon name="lightbulb" fill className="text-sm text-coral" />
              Consejos de la IA
            </div>
            {history.data.map((r) => (
              <div key={r.id} className="mb-2.5 rounded-2xl border border-border bg-card p-3.5">
                <div className="flex items-center justify-between gap-2">
                  <b className="font-display text-sm text-coral-deep">
                    Cambiar a {cap(r.recommended_strategy_name)}
                  </b>
                  <small className="flex-none text-[10px] font-extrabold text-muted-foreground">
                    {formatDate(r.created_at)}
                  </small>
                </div>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">
                  Antes: {r.previous_strategy_name}. {r.reason}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <BottomNav active="plan" />
    </div>
  )
}
