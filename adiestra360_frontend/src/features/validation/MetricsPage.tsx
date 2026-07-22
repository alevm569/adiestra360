import { useState, type ReactNode } from "react"
import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useValidationMetrics } from "./api"
import type { MetricsSegment, ValidationMetrics } from "@/types"

type SegmentKey = "real" | "simulated" | "combined"

const SEGMENTS: { key: SegmentKey; label: string }[] = [
  { key: "real", label: "Reales" },
  { key: "simulated", label: "Simulados" },
  { key: "combined", label: "Todos" },
]

const ADJECTIVE_ORDER = ["Deficiente", "Pobre", "Aceptable", "Bueno", "Excelente"]

export function MetricsPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useValidationMetrics()
  const [segment, setSegment] = useState<SegmentKey>("real")

  if (isLoading) return <Loading />
  if (isError || !data) {
    const status = (error as { response?: { status?: number } })?.response?.status
    return <ErrorState forbidden={status === 403} onBack={() => navigate("/perfil")} />
  }

  return (
    <div className="flex h-dvh flex-col">
      <header className="flex items-center gap-2 border-b border-border px-4 pt-safe">
        <button
          type="button"
          onClick={() => navigate("/perfil")}
          className="grid size-9 place-items-center rounded-xl text-muted-foreground"
          aria-label="Volver"
        >
          <Icon name="arrow_back" className="text-xl" />
        </button>
        <h2 className="py-3 text-lg font-bold">Panel de validación</h2>
      </header>

      <div className="flex-1 overflow-y-auto px-5 pb-8">
        <Counts data={data} />
        <SegmentTabs value={segment} onChange={setSegment} />
        <Segment segment={data[segment]} />
      </div>
    </div>
  )
}

function Counts({ data }: { data: ValidationMetrics }) {
  const items = [
    { value: data.counts.real_users, label: "Reales" },
    { value: data.counts.simulated_users, label: "Simulados" },
    { value: data.counts.total_users, label: "Total" },
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

function SegmentTabs({
  value,
  onChange,
}: {
  value: SegmentKey
  onChange: (s: SegmentKey) => void
}) {
  return (
    <div className="mt-4 flex gap-1.5 rounded-xl bg-muted p-1">
      {SEGMENTS.map((s) => (
        <button
          key={s.key}
          type="button"
          onClick={() => onChange(s.key)}
          className={cn(
            "flex-1 rounded-lg py-1.5 text-xs font-extrabold transition-colors",
            value === s.key
              ? "bg-card text-primary-deep shadow-sm"
              : "text-muted-foreground"
          )}
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}

function Segment({ segment }: { segment: MetricsSegment }) {
  const u = segment.usage
  if (u.users === 0) {
    return (
      <p className="mt-8 text-center text-sm font-bold text-muted-foreground">
        No hay datos en este segmento todavía.
      </p>
    )
  }
  return (
    <>
      <SectionTitle>Uso y progreso</SectionTitle>
      <div className="grid grid-cols-2 gap-2.5">
        <Kpi icon="check_circle" value={pct(u.success_rate)} label="Tasa de éxito" />
        <Kpi icon="fitness_center" value={u.total_sessions} label="Sesiones" />
        <Kpi
          icon="repeat"
          value={num(u.avg_sessions_per_user)}
          label="Sesiones/usuario"
        />
        <Kpi
          icon="calendar_month"
          value={num(u.avg_active_days)}
          label="Días activos (prom.)"
        />
        <Kpi
          icon="local_fire_department"
          value={num(u.avg_current_streak)}
          label="Racha actual (prom.)"
        />
        <Kpi icon="military_tech" value={num(u.avg_total_xp)} label="XP (prom.)" />
        <Kpi
          icon="verified"
          value={u.mastered_exercises}
          label="Ejercicios dominados"
        />
        <Kpi
          icon="rule"
          value={u.criteria_completion_rate == null ? "—" : pct(u.criteria_completion_rate)}
          label="Criterios cumplidos"
        />
      </div>

      <SectionTitle>Cuestionario SUS</SectionTitle>
      <SusCard segment={segment} />

      <SectionTitle>Tasa de éxito por ejercicio</SectionTitle>
      {segment.by_exercise.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sin sesiones registradas.</p>
      ) : (
        <div className="space-y-2">
          {segment.by_exercise.map((ex) => (
            <div
              key={ex.exercise_id}
              className="rounded-2xl border border-border bg-card p-3 shadow-sm"
            >
              <div className="mb-1.5 flex items-center justify-between text-sm font-bold">
                <span>{ex.exercise_name}</span>
                <span className="text-primary-deep">{pct(ex.success_rate)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-primary-soft">
                <div
                  className="h-full rounded-full bg-linear-to-r from-primary to-primary-deep"
                  style={{ width: `${ex.success_rate}%` }}
                />
              </div>
              <p className="mt-1 text-[10px] font-bold text-muted-foreground">
                {ex.total_sessions} sesión(es)
              </p>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function SusCard({ segment }: { segment: MetricsSegment }) {
  const s = segment.sus
  if (s.n === 0) {
    return (
      <div className="rounded-2xl border border-border bg-card p-4 text-sm text-muted-foreground shadow-sm">
        Aún no hay respuestas del cuestionario en este segmento.
      </div>
    )
  }
  const maxBucket = Math.max(1, ...Object.values(s.distribution))
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-end justify-between">
        <div>
          <span className="font-display text-4xl font-bold">{num(s.mean)}</span>
          <span className="ml-1 text-sm font-bold text-muted-foreground">/ 100</span>
        </div>
        <span className="rounded-full bg-primary-soft px-2.5 py-1 text-xs font-extrabold text-primary-deep">
          {s.adjective}
        </span>
      </div>
      <p className="mt-1 text-xs font-bold text-muted-foreground">
        {s.n} respuesta(s) · mediana {num(s.median)} · rango {num(s.min)}–{num(s.max)}
      </p>
      {s.above_industry_avg_pct != null && (
        <p className="mt-0.5 text-xs font-bold text-muted-foreground">
          {pct(s.above_industry_avg_pct)} por encima de la media de la industria (68)
        </p>
      )}

      {/* Distribución por adjetivo */}
      <div className="mt-3 space-y-1.5">
        {ADJECTIVE_ORDER.map((adj) => {
          const count = s.distribution[adj] ?? 0
          return (
            <div key={adj} className="flex items-center gap-2 text-[11px] font-bold">
              <span className="w-20 text-muted-foreground">{adj}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${(count / maxBucket) * 100}%` }}
                />
              </div>
              <span className="w-4 text-right text-muted-foreground">{count}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function Kpi({
  icon,
  value,
  label,
}: {
  icon: string
  value: string | number
  label: string
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-3 shadow-sm">
      <Icon name={icon} className="text-xl text-primary-deep" />
      <b className="mt-1 block font-display text-xl">{value}</b>
      <small className="text-[10px] font-extrabold leading-tight text-muted-foreground">
        {label}
      </small>
    </div>
  )
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h3 className="mb-2.5 mt-6 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

const pct = (v: number | null) => (v == null ? "—" : `${v}%`)
const num = (v: number | null) => (v == null ? "—" : `${v}`)

function Loading() {
  return (
    <div className="grid h-dvh place-items-center text-muted-foreground">
      <Icon name="progress_activity" className="animate-spin text-3xl" />
    </div>
  )
}

function ErrorState({
  forbidden,
  onBack,
}: {
  forbidden: boolean
  onBack: () => void
}) {
  return (
    <div className="grid h-dvh place-items-center px-8 text-center">
      <div>
        <Icon name={forbidden ? "lock" : "error"} className="text-4xl text-muted-foreground" />
        <p className="mt-2 text-sm font-bold text-muted-foreground">
          {forbidden
            ? "No tienes acceso al panel de validación."
            : "No se pudieron cargar las métricas."}
        </p>
        <Button className="mt-4" variant="outline" onClick={onBack}>
          Volver
        </Button>
      </div>
    </div>
  )
}
