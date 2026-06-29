import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useDogStore } from "@/stores/dogStore"
import { useActivePlan } from "@/features/plan/api"
import { useCreateSessions, type SessionInput } from "./api"
import type { PlanExerciseItem } from "@/types"

type Rating = "dificil" | "bien" | "excelente"

const RATINGS: { value: Rating; icon: string; label: string }[] = [
  { value: "dificil", icon: "sentiment_dissatisfied", label: "Difícil" },
  { value: "bien", icon: "sentiment_satisfied", label: "Bien" },
  { value: "excelente", icon: "sentiment_very_satisfied", label: "Excelente" },
]

export function SessionPage() {
  const navigate = useNavigate()
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data: plan, isLoading } = useActivePlan(activeDogId)
  const createSessions = useCreateSessions(activeDogId)

  const [ratings, setRatings] = useState<Record<string, Rating>>({})
  const [notes, setNotes] = useState("")

  if (!activeDogId) return <Navigate to="/" replace />

  // Ejercicios a practicar hoy: activos y aún no dominados.
  const todo = (plan?.exercises ?? [])
    .filter((e) => e.active && !e.dominated)
    .sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  const ratedCount = Object.keys(ratings).length

  function save() {
    const inputs: SessionInput[] = todo
      .filter((e) => ratings[e.id])
      .map((e) => ({
        exercise: e.exercise.id,
        reinforcement_type: e.reinforcement_type.id,
        success: ratings[e.id] !== "dificil",
        notes: notes.trim() || undefined,
      }))
    if (inputs.length === 0) return
    createSessions.mutate(inputs)
  }

  // --- Pantalla de éxito ---
  if (createSessions.isSuccess) {
    const summary = createSessions.data
    return (
      <div className="grid min-h-safe place-items-center px-8 pb-safe pt-safe text-center">
        <div>
          <div className="mx-auto mb-5 grid size-24 place-items-center rounded-full bg-primary-soft text-primary-deep">
            <Icon name="celebration" fill className="text-5xl" />
          </div>
          <h1 className="text-2xl font-bold">¡Sesión registrada!</h1>
          <p className="mt-1 text-sm font-bold text-muted-foreground">
            {summary.count} {summary.count === 1 ? "ejercicio" : "ejercicios"} entrenados
          </p>

          <div className="mx-auto mt-5 inline-flex items-center gap-2 rounded-full bg-amber-soft px-4 py-2 font-display text-lg font-extrabold text-amber-deep">
            <Icon name="bolt" fill className="text-xl" />+{summary.xpEarned} XP
          </div>

          {summary.newAchievements.length > 0 && (
            <div className="mt-5 flex flex-col gap-2">
              {summary.newAchievements.map((a, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 rounded-2xl border border-border bg-card p-3 text-left"
                >
                  <div className="grid size-10 flex-none place-items-center rounded-full bg-amber-soft text-amber-deep">
                    <Icon name="trophy" fill className="text-xl" />
                  </div>
                  <div>
                    <small className="block text-[10px] font-extrabold uppercase tracking-wider text-amber-deep">
                      ¡Logro desbloqueado!
                    </small>
                    <b className="text-sm">{a.name}</b>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={() => navigate("/", { replace: true })}
            className="mt-7 h-12 w-full rounded-xl text-base font-extrabold"
          >
            Volver al inicio
            <Icon name="arrow_forward" className="text-xl" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-safe flex-col px-5 pb-safe">
      <div className="flex items-center gap-2.5 pt-safe">
        <button
          type="button"
          onClick={() => navigate("/")}
          aria-label="Cerrar"
          className="grid size-9 place-items-center rounded-xl border border-border bg-card"
        >
          <Icon name="close" className="text-xl" />
        </button>
        <h2 className="py-2 text-lg font-bold">Sesión de hoy</h2>
      </div>
      <p className="mb-4 text-sm font-semibold text-muted-foreground">
        Registra el resultado de cada ejercicio
      </p>

      {isLoading && (
        <div className="grid flex-1 place-items-center text-muted-foreground">
          <Icon name="progress_activity" className="animate-spin text-3xl" />
        </div>
      )}

      {!isLoading && todo.length === 0 && (
        <div className="grid flex-1 place-items-center px-6 text-center">
          <p className="text-sm font-semibold text-muted-foreground">
            No hay ejercicios pendientes por hoy. ¡Buen trabajo!
          </p>
        </div>
      )}

      {!isLoading && todo.length > 0 && (
        <>
          <div className="mb-2.5 flex items-center justify-between">
            <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
              Ejercicios de hoy
            </span>
            <small className="text-xs font-extrabold text-muted-foreground">
              {todo.length} pendientes
            </small>
          </div>

          {todo.map((e) => (
            <ExerciseRater
              key={e.id}
              item={e}
              rating={ratings[e.id]}
              onRate={(r) => setRatings((prev) => ({ ...prev, [e.id]: r }))}
            />
          ))}

          <label className="mt-2 flex flex-col gap-2">
            <span className="text-xs font-extrabold">Notas (opcional)</span>
            <textarea
              value={notes}
              onChange={(ev) => setNotes(ev.target.value)}
              rows={2}
              placeholder="Respondió mejor en el parque…"
              className="resize-none rounded-xl border border-border bg-card p-3 text-sm font-medium outline-none focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-primary-soft"
            />
          </label>

          {createSessions.isError && (
            <p className="mt-3 text-center text-sm font-semibold text-destructive">
              No pudimos guardar la sesión. Inténtalo de nuevo.
            </p>
          )}

          <Button
            onClick={save}
            disabled={ratedCount === 0 || createSessions.isPending}
            className="my-4 h-12 rounded-xl text-base font-extrabold"
          >
            {createSessions.isPending ? (
              "Guardando…"
            ) : (
              <>
                <Icon name="check" className="text-xl" />
                Guardar sesión
              </>
            )}
          </Button>
        </>
      )}
    </div>
  )
}

function ExerciseRater({
  item,
  rating,
  onRate,
}: {
  item: PlanExerciseItem
  rating?: Rating
  onRate: (r: Rating) => void
}) {
  return (
    <div className="mb-2.5 rounded-2xl border border-border bg-card p-3">
      <div className="mb-2.5 flex items-center gap-2.5">
        <div className="grid size-9 flex-none place-items-center rounded-xl bg-primary-soft text-primary-deep">
          <Icon name={reinforcementIcon(item.reinforcement_type?.name)} className="text-lg" />
        </div>
        <div className="min-w-0 flex-1">
          <b className="block text-sm">{cap(item.exercise.name)}</b>
          <small className="text-[11px] font-bold text-muted-foreground">
            Refuerzo: {item.reinforcement_type?.name ?? "—"}
          </small>
        </div>
      </div>
      <div className="flex gap-2">
        {RATINGS.map((r) => {
          const sel = rating === r.value
          return (
            <button
              key={r.value}
              type="button"
              onClick={() => onRate(r.value)}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 rounded-xl border-[1.5px] py-2.5 transition-colors",
                sel
                  ? "border-primary bg-primary-soft text-primary-deep"
                  : "border-border bg-card text-muted-foreground"
              )}
            >
              <Icon name={r.icon} fill={sel} className="text-2xl" />
              <span className="text-[10px] font-extrabold">{r.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
