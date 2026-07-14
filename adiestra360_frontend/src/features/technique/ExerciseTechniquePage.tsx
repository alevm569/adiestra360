import { useState, type ReactNode } from "react"
import { Navigate, useNavigate, useParams } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap, reinforcementIcon } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { useDogStore } from "@/stores/dogStore"
import { useExerciseTechnique } from "./api"
import type { TechniqueMethod } from "@/types"

export function ExerciseTechniquePage() {
  const navigate = useNavigate()
  const { exerciseId } = useParams()
  const activeDogId = useDogStore((s) => s.activeDogId)
  const { data, isLoading, isError } = useExerciseTechnique(exerciseId, activeDogId)
  const [selected, setSelected] = useState(0)

  if (!activeDogId) return <Navigate to="/" replace />

  const methods: TechniqueMethod[] = data
    ? [data.suggested_method, ...data.other_methods].filter(
        (m): m is TechniqueMethod => Boolean(m)
      )
    : []
  const suggestedKey = data?.suggested_method?.method_key
  const method = methods[selected]

  return (
    <div className="min-h-safe px-5 pb-safe">
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
          {/* Ejercicio */}
          <h1 className="mt-1 text-2xl font-bold">{cap(data.exercise.name)}</h1>
          {data.exercise.description && (
            <p className="mt-1 text-sm font-semibold text-muted-foreground">
              {data.exercise.description}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {data.exercise.difficulty != null && (
              <Chip icon="signal_cellular_alt">Dificultad {data.exercise.difficulty}</Chip>
            )}
            {data.exercise.estimated_duration != null && (
              <Chip icon="timer">{data.exercise.estimated_duration} min</Chip>
            )}
            {data.recommended_reinforcement && (
              <Chip icon={reinforcementIcon(data.recommended_reinforcement)}>
                Refuerzo: {data.recommended_reinforcement}
              </Chip>
            )}
          </div>

          {methods.length === 0 ? (
            <p className="mt-6 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-muted-foreground">
              Aún no hay pasos cargados para este ejercicio.
            </p>
          ) : (
            <>
              {/* Selector de método */}
              <p className="mt-5 mb-2 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                Método · elegido según la energía de tu perro ({data.motivation})
              </p>
              <div className="flex gap-2">
                {methods.map((m, i) => {
                  const isSuggested = m.method_key === suggestedKey
                  const isSel = i === selected
                  return (
                    <button
                      key={m.method_key}
                      type="button"
                      onClick={() => setSelected(i)}
                      className={cn(
                        "flex flex-1 items-center justify-center gap-1.5 rounded-xl border-[1.5px] py-2.5 text-sm font-extrabold transition-colors",
                        isSel
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-card text-foreground"
                      )}
                    >
                      {isSuggested && (
                        <Icon name="auto_awesome" fill className="text-sm" />
                      )}
                      {m.method_name}
                    </button>
                  )
                })}
              </div>

              {method && <MethodDetail method={method} />}
            </>
          )}
        </>
      )}
    </div>
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

function MethodDetail({ method }: { method: TechniqueMethod }) {
  return (
    <div className="mt-4">
      {method.method_description && (
        <p className="mb-3 text-sm font-semibold text-muted-foreground">
          {method.method_description}
        </p>
      )}

      {method.materials && (
        <div className="mb-4 flex items-start gap-2.5 rounded-2xl border border-border bg-card p-3.5">
          <Icon name="backpack" fill className="text-lg text-primary-deep" />
          <div>
            <b className="block text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
              Necesitas
            </b>
            <p className="text-sm font-semibold">{method.materials}</p>
          </div>
        </div>
      )}

      <p className="mb-2.5 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
        Pasos
      </p>
      <ol className="mb-4">
        {method.steps.map((step, i) => (
          <li key={i} className="mb-2.5 rounded-2xl border border-border bg-card p-3">
            <div className="flex gap-3">
              <span className="grid size-6 flex-none place-items-center rounded-full bg-primary-soft font-display text-xs font-extrabold text-primary-deep">
                {i + 1}
              </span>
              <span className="text-sm font-semibold">{step.text}</span>
            </div>
            {step.image && (
              <img
                src={step.image}
                alt={`Paso ${i + 1}`}
                loading="lazy"
                className="mt-2.5 w-full rounded-xl border border-border object-cover"
              />
            )}
          </li>
        ))}
      </ol>

      {method.tips && (
        <div className="mb-6 flex items-start gap-2.5 rounded-2xl bg-amber-soft p-3.5">
          <Icon name="lightbulb" fill className="text-lg text-amber-deep" />
          <div>
            <b className="block text-xs font-extrabold uppercase tracking-wider text-amber-deep">
              Tip
            </b>
            <p className="text-sm font-semibold">{method.tips}</p>
          </div>
        </div>
      )}
    </div>
  )
}
