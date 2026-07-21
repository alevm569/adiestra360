import { useState } from "react"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import {
  cap,
  reinforcementIcon,
  masteredExerciseIds,
  isSuperado,
  criteriaResult,
  RESULT_META,
} from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useDogStore } from "@/stores/dogStore"
import { useDashboard } from "@/features/dashboard/api"
import {
  useTrainSession,
  type TrainInput,
  type ExerciseOutcome,
  type TrainSummary,
} from "./api"
import type { PlanExerciseItem } from "@/types"

export function SessionPage() {
  const navigate = useNavigate()
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading } = useDashboard(activeDogId)
  const train = useTrainSession(activeDogId)

  // Ejercicios entrenados hoy y qué criterios cumplió cada uno.
  const [trained, setTrained] = useState<Record<string, boolean>>({})
  const [checked, setChecked] = useState<Record<string, Set<number>>>({})
  const [notesOpen, setNotesOpen] = useState(false)
  const [notes, setNotes] = useState("")

  if (!activeDogId) return <Navigate to="/" replace />

  // Ejercicios a practicar hoy: activos y NO superados (ni por encuesta ni por
  // sesiones). Los superados dejan de aparecer.
  const masteredIds = masteredExerciseIds(data?.exercise_progress)
  const todo = (data?.plan?.exercises ?? [])
    .filter((e) => e.active && !isSuperado(e, masteredIds))
    .sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  const trainedCount = todo.filter((e) => trained[e.id]).length

  function toggleTrained(id: string) {
    setTrained((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  function toggleCriterion(id: string, index: number) {
    setChecked((prev) => {
      const set = new Set(prev[id] ?? [])
      set.has(index) ? set.delete(index) : set.add(index)
      return { ...prev, [id]: set }
    })
  }

  function save() {
    const inputs: TrainInput[] = todo
      .filter((e) => trained[e.id])
      .map((e) => {
        const total = e.criterio_avanzar?.length ?? 0
        const set = checked[e.id] ?? new Set<number>()
        return {
          exerciseId: e.exercise.id,
          reinforcementTypeId: e.reinforcement_type.id,
          exerciseName: cap(e.exercise.name),
          result: criteriaResult(total, set),
          criteriaMet: set.size,
          criteriaTotal: total,
        }
      })
    if (inputs.length === 0) return
    train.mutate({ inputs, notes })
  }

  if (train.isSuccess) {
    return <SessionSuccess data={train.data} onDone={() => navigate("/", { replace: true })} />
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
        Marca lo que tu perro logró en cada ejercicio
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
            <ExerciseChecklist
              key={e.id}
              item={e}
              trained={!!trained[e.id]}
              checked={checked[e.id] ?? new Set()}
              onToggleTrained={() => toggleTrained(e.id)}
              onToggleCriterion={(i) => toggleCriterion(e.id, i)}
            />
          ))}

          {/* Nota opcional (plegable) */}
          {notesOpen ? (
            <label className="mt-2 flex flex-col gap-2">
              <span className="text-xs font-extrabold">Nota (opcional)</span>
              <textarea
                value={notes}
                onChange={(ev) => setNotes(ev.target.value)}
                rows={2}
                autoFocus
                placeholder="Se distrae con otros perros, responde mejor en casa…"
                className="resize-none rounded-xl border border-border bg-card p-3 text-sm font-medium outline-none focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-primary-soft"
              />
            </label>
          ) : (
            <button
              type="button"
              onClick={() => setNotesOpen(true)}
              className="mt-2 flex items-center gap-1.5 self-start text-xs font-extrabold text-primary-deep"
            >
              <Icon name="add_notes" className="text-base" />
              Agregar una nota (opcional)
            </button>
          )}

          {train.isError && (
            <p className="mt-3 text-center text-sm font-semibold text-destructive">
              No pudimos guardar la sesión. Inténtalo de nuevo.
            </p>
          )}

          <Button
            onClick={save}
            disabled={trainedCount === 0 || train.isPending}
            className="my-4 h-12 rounded-xl text-base font-extrabold"
          >
            {train.isPending ? (
              "Guardando…"
            ) : (
              <>
                <Icon name="check" className="text-xl" />
                Guardar sesión{trainedCount > 0 ? ` (${trainedCount})` : ""}
              </>
            )}
          </Button>
        </>
      )}
    </div>
  )
}

function ExerciseChecklist({
  item,
  trained,
  checked,
  onToggleTrained,
  onToggleCriterion,
}: {
  item: PlanExerciseItem
  trained: boolean
  checked: Set<number>
  onToggleTrained: () => void
  onToggleCriterion: (index: number) => void
}) {
  const criteria = item.criterio_avanzar ?? []
  const result = criteriaResult(criteria.length, checked)
  const meta = RESULT_META[result]

  return (
    <div className="mb-2.5 rounded-2xl border border-border bg-card p-3">
      <div className="flex items-center gap-2.5">
        <div className="grid size-9 flex-none place-items-center rounded-xl bg-primary-soft text-primary-deep">
          <Icon name={reinforcementIcon(item.reinforcement_type?.name)} className="text-lg" />
        </div>
        <div className="min-w-0 flex-1">
          <b className="block text-sm">{cap(item.exercise.name)}</b>
          <small className="text-[11px] font-bold text-muted-foreground">
            Refuerzo: {item.reinforcement_type?.name ?? "—"}
          </small>
        </div>
        <Link
          to={`/ejercicio/${item.exercise.id}`}
          className="flex flex-none items-center gap-0.5 text-[11px] font-extrabold text-primary-deep"
        >
          <Icon name="menu_book" className="text-sm" />
          Cómo
        </Link>
      </div>

      {/* Toggle: ¿lo entrenaste hoy? Revela el checklist. */}
      <button
        type="button"
        onClick={onToggleTrained}
        className={cn(
          "mt-2.5 flex w-full items-center gap-2 rounded-xl border-[1.5px] px-3 py-2.5 text-left transition-colors",
          trained
            ? "border-primary bg-primary-soft text-primary-deep"
            : "border-border bg-card text-muted-foreground"
        )}
      >
        <Icon
          name={trained ? "check_box" : "check_box_outline_blank"}
          fill={trained}
          className="text-xl"
        />
        <span className="text-sm font-extrabold">Entrené este ejercicio hoy</span>
      </button>

      {trained && (
        <div className="mt-2.5">
          {criteria.length > 0 ? (
            <>
              <p className="mb-1.5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                ¿Qué logró?
              </p>
              <ul className="flex flex-col gap-1.5">
                {criteria.map((c, i) => {
                  const on = checked.has(i)
                  return (
                    <li key={i}>
                      <button
                        type="button"
                        onClick={() => onToggleCriterion(i)}
                        className="flex w-full items-start gap-2 text-left"
                      >
                        <Icon
                          name={on ? "check_circle" : "radio_button_unchecked"}
                          fill={on}
                          className={cn(
                            "mt-0.5 flex-none text-lg",
                            on ? "text-primary-deep" : "text-muted-foreground"
                          )}
                        />
                        <span className="text-sm font-semibold">
                          {c}
                          {i === 0 && (
                            <span className="ml-1.5 rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-extrabold uppercase text-muted-foreground">
                              Clave
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
              <div
                className={cn(
                  "mt-2.5 flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-extrabold",
                  meta.tone
                )}
              >
                <Icon name={meta.icon} fill className="text-base" />
                {meta.label}
                <span className="ml-auto font-bold">
                  {checked.size}/{criteria.length} criterios
                </span>
              </div>
            </>
          ) : (
            <p className="text-xs font-semibold text-muted-foreground">
              Este ejercicio aún no tiene criterios cargados; se registra como
              practicado.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ---- Pantalla de éxito con feedback por ejercicio ----

const TONE = {
  done: "bg-primary-soft text-primary-deep",
  progress: "bg-amber-soft text-amber-deep",
  warn: "bg-coral-soft text-coral-deep",
} as const

function feedback(o: ExerciseOutcome) {
  if (o.mastered) {
    return {
      tone: "done" as const,
      icon: "check_circle",
      title: `¡${o.exerciseName} superado!`,
      sub: o.leveledUp
        ? `¡Subiste a ${o.newLevel ?? "nuevo nivel"}! Sigue practicando para mantenerlo.`
        : "Cumple todos los criterios de forma consistente. ¡Bien ahí!",
    }
  }
  if (o.result === "excelente") {
    return {
      tone: "done" as const,
      icon: "workspace_premium",
      title: `¡Excelente con ${o.exerciseName}!`,
      sub: `Cumplió todos los criterios. Mantenlo unas sesiones y queda superado · ${o.successRate}% de éxito en ${o.totalSessions} ${
        o.totalSessions === 1 ? "sesión" : "sesiones"
      }.`,
    }
  }
  if (o.result === "bien") {
    return {
      tone: "progress" as const,
      icon: "trending_up",
      title: `¡Vas bien con ${o.exerciseName}!`,
      sub: `Cumplió lo más importante; faltan criterios para dominarlo · ${o.successRate}% de éxito en ${o.totalSessions} ${
        o.totalSessions === 1 ? "sesión" : "sesiones"
      }.`,
    }
  }
  return {
    tone: "warn" as const,
    icon: "replay",
    title: `A reforzar ${o.exerciseName}`,
    sub: "Le faltó el criterio clave. Prueba otro refuerzo o cuéntanos qué pasó para darte tips.",
  }
}

function SessionSuccess({
  data,
  onDone,
}: {
  data: TrainSummary
  onDone: () => void
}) {
  return (
    <div className="flex min-h-safe flex-col overflow-y-auto px-5 pb-safe pt-safe">
      <div className="mx-auto mt-6 grid size-20 place-items-center rounded-full bg-primary-soft text-primary-deep">
        <Icon name="celebration" fill className="text-4xl" />
      </div>
      <h1 className="mt-4 text-center text-2xl font-bold">¡Sesión registrada!</h1>
      <div className="mx-auto mt-3 inline-flex items-center gap-2 rounded-full bg-amber-soft px-4 py-2 font-display text-lg font-extrabold text-amber-deep">
        <Icon name="bolt" fill className="text-xl" />+{data.xpEarned} XP
      </div>

      {/* Feedback por ejercicio */}
      <div className="mt-6 flex flex-col gap-2.5">
        {data.outcomes.map((o, i) => {
          const f = feedback(o)
          return (
            <div
              key={i}
              className="flex items-start gap-3 rounded-2xl border border-border bg-card p-3.5 text-left"
            >
              <div className={cn("grid size-10 flex-none place-items-center rounded-xl", TONE[f.tone])}>
                <Icon name={f.icon} fill className="text-xl" />
              </div>
              <div>
                <b className="block text-sm">{f.title}</b>
                <small className="text-xs font-semibold text-muted-foreground">{f.sub}</small>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recomendación de refuerzo de la IA */}
      {data.recommendation && (
        <div className="mt-3 rounded-2xl border border-coral-soft bg-coral-soft/50 p-4 text-left">
          <div className="mb-1 flex items-center gap-2 font-display text-sm font-extrabold text-coral-deep">
            <Icon name="lightbulb" fill className="text-lg" />
            Sugerencia de la IA
          </div>
          <p className="text-sm font-semibold">
            Prueba el refuerzo <b>{data.recommendation.recommendedName}</b>
            {data.recommendation.previousName && (
              <> en vez de {data.recommendation.previousName}</>
            )}
            .
          </p>
          {data.recommendation.reason && (
            <p className="mt-1 text-xs font-semibold text-muted-foreground">
              {data.recommendation.reason}
            </p>
          )}
          <p className="mt-1.5 text-xs font-extrabold text-coral-deep">
            Aplícalo desde la pantalla de inicio.
          </p>
        </div>
      )}

      {/* Logros */}
      {data.newAchievements.length > 0 && (
        <div className="mt-3 flex flex-col gap-2">
          {data.newAchievements.map((a, i) => (
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

      <Button onClick={onDone} className="mb-4 mt-6 h-12 rounded-xl text-base font-extrabold">
        Volver al inicio
        <Icon name="arrow_forward" className="text-xl" />
      </Button>
    </div>
  )
}
