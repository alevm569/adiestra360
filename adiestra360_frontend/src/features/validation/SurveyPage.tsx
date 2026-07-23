import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useSurvey, useSubmitSurvey } from "./api"
import type { SurveyData, SurveySubmission } from "@/types"

const ITEMS = Array.from({ length: 10 }, (_, i) => i + 1)

export function SurveyPage() {
  const navigate = useNavigate()
  const survey = useSurvey()
  const submit = useSubmitSurvey()

  if (survey.isLoading) return <Loading />
  if (survey.isError || !survey.data) return <ErrorState onBack={() => navigate("/perfil")} />

  return (
    <SurveyForm
      data={survey.data}
      submitting={submit.isPending}
      onSubmit={(payload) =>
        submit.mutate(payload, { onSuccess: () => navigate("/perfil") })
      }
      onBack={() => navigate("/perfil")}
    />
  )
}

function SurveyForm({
  data,
  submitting,
  onSubmit,
  onBack,
}: {
  data: SurveyData
  submitting: boolean
  onSubmit: (payload: SurveySubmission) => void
  onBack: () => void
}) {
  const existing = data.response
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [comment, setComment] = useState("")

  // Prefill si el usuario ya respondió antes.
  useEffect(() => {
    if (existing) {
      const rec = existing as unknown as Record<string, number>
      const initial: Record<number, number> = {}
      ITEMS.forEach((n) => {
        initial[n] = rec[`q${n}`]
      })
      setAnswers(initial)
      setComment(existing.comment ?? "")
    }
  }, [existing])

  const answeredCount = ITEMS.filter((n) => answers[n]).length
  const complete = answeredCount === 10

  function handleSubmit() {
    if (!complete) return
    const payload = {
      comment: comment.trim() || undefined,
    } as SurveySubmission
    ITEMS.forEach((n) => {
      payload[`q${n}`] = answers[n]
    })
    onSubmit(payload)
  }

  const minLabel = data.scale[0]?.label ?? "En desacuerdo"
  const maxLabel = data.scale[data.scale.length - 1]?.label ?? "De acuerdo"

  return (
    <div className="flex h-dvh flex-col">
      {/* Header */}
      <header className="flex items-center gap-2 border-b border-border px-4 pt-safe">
        <button
          type="button"
          onClick={onBack}
          className="grid size-9 place-items-center rounded-xl text-muted-foreground"
          aria-label="Volver"
        >
          <Icon name="arrow_back" className="text-xl" />
        </button>
        <h2 className="py-3 text-lg font-bold">Cuestionario de usabilidad</h2>
      </header>

      {/* Body */}
      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-4">
        <p className="mt-4 text-sm text-muted-foreground">
          Ayúdanos a mejorar Adiestra360. Indica cuánto estás de acuerdo con cada
          frase pensando en tu experiencia usando la app.
        </p>

        {existing && (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-primary-soft px-3 py-2 text-xs font-bold text-primary-deep">
            <Icon name="check_circle" fill className="text-base" />
            Ya respondiste. Puedes actualizar tus respuestas.
          </div>
        )}

        <div className="mt-4 space-y-4">
          {data.questions.map((q, idx) => (
            <div
              key={q.id}
              className="rounded-2xl border border-border bg-card p-4 shadow-sm"
            >
              <p className="mb-3 text-sm font-bold">
                <span className="text-muted-foreground">{idx + 1}. </span>
                {q.text}
              </p>
              <div className="flex items-center justify-between gap-1.5">
                {data.scale.map((s) => {
                  const active = answers[q.id] === s.value
                  return (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() =>
                        setAnswers((prev) => ({ ...prev, [q.id]: s.value }))
                      }
                      aria-label={s.label}
                      className={cn(
                        "grid size-10 flex-1 place-items-center rounded-xl border text-sm font-extrabold transition-colors",
                        active
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-background text-muted-foreground"
                      )}
                    >
                      {s.value}
                    </button>
                  )
                })}
              </div>
              <div className="mt-1.5 flex justify-between text-[10px] font-bold text-muted-foreground">
                <span>{minLabel}</span>
                <span>{maxLabel}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Comentario abierto */}
        <div className="mt-4">
          <label className="mb-1.5 block text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
            Comentario (opcional)
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            placeholder="¿Qué te gustó o qué mejorarías?"
            className="w-full resize-none rounded-2xl border border-border bg-card p-3 text-sm outline-none focus:border-primary"
          />
        </div>
      </div>

      {/* Footer */}
      <div
        className="border-t border-border bg-card px-5 pt-3"
        style={{ paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom))" }}
      >
        <div className="mb-2 text-center text-xs font-bold text-muted-foreground">
          {answeredCount} / 10 respondidas
        </div>
        <Button
          className="h-11 w-full text-base"
          disabled={!complete || submitting}
          onClick={handleSubmit}
        >
          {submitting ? (
            <Icon name="progress_activity" className="animate-spin text-xl" />
          ) : existing ? (
            "Actualizar respuestas"
          ) : (
            "Enviar cuestionario"
          )}
        </Button>
      </div>
    </div>
  )
}

function Loading() {
  return (
    <div className="grid h-dvh place-items-center text-muted-foreground">
      <Icon name="progress_activity" className="animate-spin text-3xl" />
    </div>
  )
}

function ErrorState({ onBack }: { onBack: () => void }) {
  return (
    <div className="grid h-dvh place-items-center px-8 text-center">
      <div>
        <Icon name="error" className="text-4xl text-muted-foreground" />
        <p className="mt-2 text-sm font-bold text-muted-foreground">
          No se pudo cargar el cuestionario.
        </p>
        <Button className="mt-4" variant="outline" onClick={onBack}>
          Volver
        </Button>
      </div>
    </div>
  )
}
