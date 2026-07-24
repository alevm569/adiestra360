import { Link, Navigate, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon, storedSessionResult, RESULT_META } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useDogStore } from "@/stores/dogStore"
import { useSessionHistory } from "./api"
import type { TrainingSessionRecord } from "@/types"

/** Sesiones de un mismo día, ya ordenadas de la más reciente a la más antigua. */
interface DayGroup {
  key: string
  label: string
  sessions: TrainingSessionRecord[]
}

const dayKey = (iso: string) => {
  const d = new Date(iso)
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
}

function dayLabel(iso: string) {
  const d = new Date(iso)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)

  if (dayKey(iso) === dayKey(today.toISOString())) return "Hoy"
  if (dayKey(iso) === dayKey(yesterday.toISOString())) return "Ayer"
  return d.toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  })
}

const hour = (iso: string) =>
  new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })

/** Agrupa el historial por día conservando el orden del backend (desc). */
function groupByDay(sessions: TrainingSessionRecord[]): DayGroup[] {
  const groups: DayGroup[] = []
  for (const s of sessions) {
    const key = dayKey(s.session_date)
    const last = groups[groups.length - 1]
    if (last && last.key === key) last.sessions.push(s)
    else groups.push({ key, label: dayLabel(s.session_date), sessions: [s] })
  }
  return groups
}

export function HistoryPage() {
  const navigate = useNavigate()
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError } = useSessionHistory(activeDogId)

  if (!activeDogId) return <Navigate to="/" replace />

  const sessions = data ?? []
  const days = groupByDay(sessions)
  const successes = sessions.filter((s) => s.success).length
  const successRate = sessions.length
    ? Math.round((successes / sessions.length) * 100)
    : 0

  return (
    <div className="min-h-safe px-5 pb-10">
      <div className="sticky top-0 z-10 -mx-5 flex items-center gap-2.5 border-b border-border bg-background/95 px-5 pt-safe backdrop-blur">
        <button
          type="button"
          onClick={() => navigate(-1)}
          aria-label="Atrás"
          className="grid size-9 place-items-center rounded-xl border border-border bg-card"
        >
          <Icon name="arrow_back" className="text-xl" />
        </button>
        <h2 className="py-2 text-lg font-bold">Historial de sesiones</h2>
      </div>

      {isLoading && (
        <div className="grid place-items-center py-20 text-muted-foreground">
          <Icon name="progress_activity" className="animate-spin text-3xl" />
        </div>
      )}

      {isError && (
        <p className="mt-4 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-destructive">
          No pudimos cargar el historial.
        </p>
      )}

      {data && sessions.length === 0 && (
        <div className="mt-6 rounded-2xl border border-border bg-card p-6 text-center shadow-sm">
          <div className="mx-auto mb-3 grid size-14 place-items-center rounded-2xl bg-primary-soft text-primary-deep">
            <Icon name="history" className="text-3xl" />
          </div>
          <p className="mb-4 text-sm font-semibold text-muted-foreground">
            Aún no hay sesiones registradas. Cuando entrenes, aquí verás el resumen de
            cada día.
          </p>
          <Button asChild variant="cta" className="h-12 w-full rounded-xl font-extrabold">
            <Link to="/sesion">
              <Icon name="check_circle" className="text-xl" />
              Registrar sesión de hoy
            </Link>
          </Button>
        </div>
      )}

      {sessions.length > 0 && (
        <>
          <Summary
            total={sessions.length}
            days={days.length}
            successRate={successRate}
          />

          {days.map((day) => (
            <DayCard key={day.key} day={day} />
          ))}
        </>
      )}
    </div>
  )
}

function Summary({
  total,
  days,
  successRate,
}: {
  total: number
  days: number
  successRate: number
}) {
  const items = [
    { value: total, label: "Sesiones" },
    { value: days, label: "Días" },
    { value: `${successRate}%`, label: "Éxito" },
  ]
  return (
    <div className="mt-4 flex items-center rounded-2xl border border-border bg-card p-3.5 shadow-sm">
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

function DayCard({ day }: { day: DayGroup }) {
  const excellent = day.sessions.filter(
    (s) => storedSessionResult(s) === "excelente"
  ).length

  return (
    <div className="mt-4">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
          {day.label}
        </span>
        <small className="text-[11px] font-extrabold text-muted-foreground">
          {day.sessions.length} ejercicio(s)
          {excellent > 0 && ` · ${excellent} excelente(s)`}
        </small>
      </div>

      <div className="rounded-2xl border border-border bg-card shadow-sm">
        {day.sessions.map((s, i) => (
          <SessionRow key={s.id} session={s} first={i === 0} />
        ))}
      </div>
    </div>
  )
}

function SessionRow({
  session,
  first,
}: {
  session: TrainingSessionRecord
  first: boolean
}) {
  const meta = RESULT_META[storedSessionResult(session)]
  return (
    <div className={cn("p-3.5", !first && "border-t border-border")}>
      <div className="flex items-center gap-3">
        <div className={cn("grid size-9 flex-none place-items-center rounded-xl", meta.tone)}>
          <Icon name={meta.icon} fill className="text-lg" />
        </div>
        <div className="min-w-0 flex-1">
          <Link
            to={`/ejercicio/${session.exercise}`}
            className="block truncate text-sm font-bold"
          >
            {cap(session.exercise_name)}
          </Link>
          <small className="flex items-center gap-1 text-[11px] font-bold text-muted-foreground">
            <Icon
              name={reinforcementIcon(session.reinforcement_name)}
              className="text-xs"
            />
            {session.reinforcement_name ?? "—"} · {hour(session.session_date)}
          </small>
        </div>
        <div className="flex-none text-right">
          <span
            className={cn(
              "rounded-full px-2.5 py-1 text-[10px] font-extrabold",
              meta.tone
            )}
          >
            {meta.label}
          </span>
          {session.criteria_total ? (
            <small className="mt-1 block text-[10px] font-extrabold text-muted-foreground">
              {session.criteria_met ?? 0}/{session.criteria_total} criterios
            </small>
          ) : null}
        </div>
      </div>

      {session.notes && (
        <p className="mt-2 flex gap-1.5 rounded-xl bg-muted p-2.5 text-xs font-semibold text-muted-foreground">
          <Icon name="sticky_note_2" className="flex-none text-sm" />
          {session.notes}
        </p>
      )}
    </div>
  )
}
