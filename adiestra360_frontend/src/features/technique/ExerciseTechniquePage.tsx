import type { ReactNode } from "react"
import { Link, Navigate, useNavigate, useParams } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useDogStore } from "@/stores/dogStore"
import { useExerciseTechnique } from "./api"
import type { StepAlternative, TechniqueStep } from "@/types"

export function ExerciseTechniquePage() {
  const navigate = useNavigate()
  const { exerciseId } = useParams()
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError } = useExerciseTechnique(exerciseId, activeDogId)

  if (!activeDogId) return <Navigate to="/" replace />

  const tech = data?.technique

  return (
    <div className="px-5">
      <div className="flex items-center gap-2.5 pt-safe">
        <button
          type="button"
          onClick={() => navigate(-1)}
          aria-label="Atrás"
          className="grid size-9 place-items-center rounded-xl border border-border bg-card"
        >
          <Icon name="arrow_back" className="text-xl" />
        </button>
        <h2 className="py-2 text-lg font-bold">Cómo enseñar</h2>
      </div>

      {isLoading && (
        <div className="grid place-items-center py-20 text-muted-foreground">
          <Icon name="progress_activity" className="animate-spin text-3xl" />
        </div>
      )}

      {isError && (
        <p className="mt-4 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-destructive">
          No pudimos cargar la técnica.
        </p>
      )}

      {data && (
        <>
          <h1 className="mt-1 text-2xl font-bold">{cap(data.exercise.name)}</h1>
          {tech?.objetivo && (
            <p className="mt-1.5 text-sm font-semibold text-muted-foreground">
              {tech.objetivo}
            </p>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            {tech?.duracion && <Chip icon="timer">{tech.duracion}</Chip>}
            {tech?.frecuencia && <Chip icon="event_repeat">{tech.frecuencia}</Chip>}
            {data.recommended_reinforcement && (
              <Chip icon={reinforcementIcon(data.recommended_reinforcement)}>
                Refuerzo: {data.recommended_reinforcement}
              </Chip>
            )}
          </div>

          {tech?.prerrequisito && (
            <Callout icon="flag" tone="sky" title="Antes de este ejercicio">
              {tech.prerrequisito}
            </Callout>
          )}

          {!tech ? (
            <p className="mt-6 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-muted-foreground">
              Aún no hay tutorial cargado para este ejercicio.
            </p>
          ) : (
            <>
              {tech.materiales.length > 0 && (
                <BulletCard icon="backpack" title="Necesitas" items={tech.materiales} />
              )}
              {tech.reglas.length > 0 && (
                <BulletCard icon="rule" title="Antes de empezar" items={tech.reglas} />
              )}

              {/* Pasos */}
              <SectionTitle>Pasos</SectionTitle>
              <ol>
                {tech.steps.map((step, i) => (
                  <StepCard
                    key={step.order ?? i}
                    step={step}
                    index={i}
                    suggestAlternative={data.suggest_alternative}
                    alternativeReason={data.alternative_reason}
                  />
                ))}
              </ol>

              {tech.errores_comunes.length > 0 && (
                <>
                  <SectionTitle>Errores comunes</SectionTitle>
                  {tech.errores_comunes.map((e, i) => (
                    <div
                      key={i}
                      className="mb-2.5 rounded-2xl border border-border bg-card p-3.5"
                    >
                      <div className="flex items-start gap-2.5">
                        <Icon name="error" fill className="text-lg text-coral" />
                        <b className="text-sm">{e.error}</b>
                      </div>
                      <div className="mt-1.5 flex items-start gap-2.5">
                        <Icon name="check_circle" fill className="text-lg text-primary-deep" />
                        <p className="text-sm font-semibold text-muted-foreground">
                          {e.correccion}
                        </p>
                      </div>
                    </div>
                  ))}
                </>
              )}

              {tech.criterio_avanzar.length > 0 && (
                <BulletCard
                  icon="verified"
                  title="Sabrás que lo domina cuando…"
                  items={tech.criterio_avanzar}
                  className="mb-4"
                />
              )}
            </>
          )}
        </>
      )}

      {/* CTA fijo: enlaza el tutorial con el registro de la sesión del día. */}
      {data && (
        <div className="sticky bottom-0 -mx-5 mt-2 border-t border-border bg-background/95 px-5 py-3 pb-safe backdrop-blur">
          <Button asChild className="h-12 w-full rounded-xl text-base font-extrabold">
            <Link to="/sesion">
              <Icon name="checklist" className="text-xl" />
              Registrar sesión de hoy
            </Link>
          </Button>
        </div>
      )}
    </div>
  )
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <p className="mb-2.5 mt-5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
      {children}
    </p>
  )
}

function Chip({ icon, children }: { icon: string; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-[11px] font-extrabold text-muted-foreground">
      <Icon name={icon} className="text-sm" />
      {children}
    </span>
  )
}

function Callout({
  icon,
  tone,
  title,
  children,
}: {
  icon: string
  tone: "sky" | "amber"
  title: string
  children: ReactNode
}) {
  const tones = {
    sky: "bg-sky-soft text-sky-deep",
    amber: "bg-amber-soft text-amber-deep",
  }
  return (
    <div className={cn("mt-4 flex items-start gap-2.5 rounded-2xl p-3.5", tones[tone])}>
      <Icon name={icon} fill className="text-lg" />
      <div>
        <b className="block text-xs font-extrabold uppercase tracking-wider">{title}</b>
        <p className="text-sm font-semibold text-foreground">{children}</p>
      </div>
    </div>
  )
}

function BulletCard({
  icon,
  title,
  items,
  className,
}: {
  icon: string
  title: string
  items: string[]
  className?: string
}) {
  return (
    <div className={cn("mt-4 rounded-2xl border border-border bg-card p-3.5", className)}>
      <div className="mb-2 flex items-center gap-2 text-primary-deep">
        <Icon name={icon} fill className="text-lg" />
        <b className="text-xs font-extrabold uppercase tracking-wider">{title}</b>
      </div>
      <ul className="flex flex-col gap-1">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2 text-sm font-semibold">
            <span className="text-muted-foreground">·</span>
            {it}
          </li>
        ))}
      </ul>
    </div>
  )
}

function StepCard({
  step,
  index,
  suggestAlternative,
  alternativeReason,
}: {
  step: TechniqueStep
  index: number
  suggestAlternative: boolean
  alternativeReason: string | null
}) {
  return (
    <li className="mb-2.5 rounded-2xl border border-border bg-card p-3.5">
      <div className="flex gap-3">
        <span className="grid size-6 flex-none place-items-center rounded-full bg-primary-soft font-display text-xs font-extrabold text-primary-deep">
          {step.order ?? index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <b className="block text-sm">{step.title}</b>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">{step.text}</p>
        </div>
      </div>

      {step.image && (
        <img
          src={step.image}
          alt={step.title}
          loading="lazy"
          className="mt-2.5 w-full rounded-xl border border-border object-cover"
        />
      )}

      {step.alternative && (
        <AlternativeBlock
          alt={step.alternative}
          highlighted={suggestAlternative}
          reason={alternativeReason}
        />
      )}
    </li>
  )
}

function AlternativeBlock({
  alt,
  highlighted,
  reason,
}: {
  alt: StepAlternative
  highlighted: boolean
  reason: string | null
}) {
  return (
    <div
      className={cn(
        "mt-3 rounded-xl p-3",
        highlighted ? "bg-amber-soft" : "bg-muted"
      )}
    >
      <div
        className={cn(
          "mb-1 flex items-center gap-1.5 text-xs font-extrabold",
          highlighted ? "text-amber-deep" : "text-muted-foreground"
        )}
      >
        <Icon name={highlighted ? "auto_awesome" : "alt_route"} fill className="text-sm" />
        Alternativa: {alt.title}
        {highlighted && (
          <span className="rounded-full bg-amber px-1.5 py-0.5 text-[9px] text-amber-deep">
            Recomendada
          </span>
        )}
      </div>

      {highlighted && reason && (
        <p className="mb-1.5 text-[11px] font-bold text-amber-deep">{reason}</p>
      )}

      <p className="text-sm font-semibold">{alt.text}</p>
      <p className="mt-1 text-[11px] font-bold text-muted-foreground">
        Cuándo: {alt.when}
      </p>

      {alt.image && (
        <img
          src={alt.image}
          alt={alt.title}
          loading="lazy"
          className="mt-2.5 w-full rounded-xl border border-border object-cover"
        />
      )}
    </div>
  )
}
