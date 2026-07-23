import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Stepper } from "@/components/Stepper"
import { Button } from "@/components/ui/button"
import { useOnboarding } from "@/stores/onboardingStore"
import { useDogStore } from "@/stores/dogStore"
import { useQuiz, useCreateDog } from "./api"
import type { QuizAnswer, QuizQuestion } from "@/types"

const CATEGORY: Record<string, { label: string; icon: string; chip: string }> = {
  dog_knowledge: {
    label: "Conducta",
    icon: "pets",
    chip: "bg-primary-soft text-primary-deep",
  },
  reinforcement: {
    label: "Refuerzo",
    icon: "redeem",
    chip: "bg-coral-soft text-coral-deep",
  },
  owner_experience: {
    label: "Tu experiencia",
    icon: "person",
    chip: "bg-sky-soft text-sky-deep",
  },
}

function buildAnswer(q: QuizQuestion, answer: string): QuizAnswer {
  return {
    id: q.id,
    answer,
    exercise_related: q.exercise_related ?? null,
    reinforcement_related: q.reinforcement_related ?? null,
    experience_related: q.experience_related ?? null,
  }
}

export function QuizPage() {
  const navigate = useNavigate()
  const dog = useOnboarding((s) => s.dog)
  const setActiveDog = useDogStore((s) => s.setActiveDog)

  const { data: questions, isLoading, isError } = useQuiz()
  const createDog = useCreateDog()

  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})

  // Si llegaron aquí sin haber llenado el perfil del perro, volver atrás.
  if (!dog) return <Navigate to="/onboarding/dog" replace />

  if (isLoading) {
    return (
      <div className="grid min-h-safe place-items-center text-muted-foreground">
        <Icon name="progress_activity" className="animate-spin text-3xl" />
      </div>
    )
  }

  if (isError || !questions || questions.length === 0) {
    return (
      <div className="grid min-h-safe place-items-center px-8 text-center">
        <p className="text-sm font-semibold text-destructive">
          No pudimos cargar la encuesta. Revisa tu conexión e inténtalo de nuevo.
        </p>
      </div>
    )
  }

  const question = questions[index]
  const total = questions.length
  const selected = answers[question.id]
  const isLast = index === total - 1
  const cat = CATEGORY[question.category] ?? CATEGORY.dog_knowledge

  function select(option: string) {
    setAnswers((prev) => ({ ...prev, [question.id]: option }))
  }

  function goBack() {
    if (index > 0) setIndex((i) => i - 1)
    else navigate("/onboarding/dog")
  }

  function next() {
    if (!isLast) {
      setIndex((i) => i + 1)
      return
    }
    // Última pregunta: armar respuestas y crear perro + plan.
    const quiz_answers = questions!.map((q) => buildAnswer(q, answers[q.id]))
    createDog.mutate(
      { dog: dog!, quiz_answers },
      {
        onSuccess: (data) => {
          // No limpiamos el borrador aquí: nullear el perro dispararía el guard
          // "sin perro" y rebotaría a /onboarding/dog antes de navegar al inicio.
          setActiveDog(data.dog.id)
          navigate("/", { replace: true })
        },
      }
    )
  }

  return (
    <div className="flex min-h-safe flex-col px-5 pb-safe">
      <div className="pt-safe">
        <div className="flex items-center gap-2.5 py-2">
          <button
            type="button"
            onClick={goBack}
            aria-label="Atrás"
            className="grid size-9 place-items-center rounded-xl border border-border bg-card"
          >
            <Icon name="arrow_back" className="text-xl" />
          </button>
          <h2 className="text-lg font-bold">Conozcamos a {dog.name || "tu perro"}</h2>
        </div>
        <Stepper total={3} current={3} accentClass="bg-amber" />
      </div>

      <div className="mt-4 mb-4 flex items-center justify-between">
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-extrabold",
            cat.chip
          )}
        >
          <Icon name={cat.icon} className="text-sm" />
          {cat.label}
        </span>
        <small className="text-xs font-extrabold text-muted-foreground">
          Pregunta {index + 1} de {total}
        </small>
      </div>

      <div className="flex-1">
        <h1 className="mb-5 text-xl leading-snug text-pretty">{question.question}</h1>

        <div className="flex flex-col gap-2.5">
          {question.options.map((option) => {
            const isSel = selected === option
            return (
              <button
                key={option}
                type="button"
                onClick={() => select(option)}
                className={cn(
                  "flex items-center gap-3 rounded-2xl border-[1.5px] p-3.5 text-left text-sm font-bold transition-colors",
                  isSel
                    ? "border-amber bg-amber-soft"
                    : "border-border bg-card"
                )}
              >
                <Icon
                  name={isSel ? "check_circle" : "radio_button_unchecked"}
                  fill={isSel}
                  className={cn(
                    "flex-none text-[22px]",
                    isSel ? "text-amber-deep" : "text-muted-foreground/50"
                  )}
                />
                {option}
              </button>
            )
          })}
        </div>
      </div>

      {createDog.isError && (
        <p className="mb-2 text-center text-sm font-semibold text-destructive">
          No pudimos crear el plan. Inténtalo de nuevo.
        </p>
      )}

      {isLast && (
        <p className="mb-2 text-center text-xs font-semibold text-muted-foreground">
          La encuesta mezcla preguntas sobre ti y sobre {dog.name || "tu perro"}
        </p>
      )}

      <Button
        type="button"
        onClick={next}
        disabled={!selected || createDog.isPending}
        className={cn(
          "mb-4 h-12 rounded-xl text-base font-extrabold",
          isLast && "bg-linear-to-br from-amber to-amber-deep"
        )}
      >
        {isLast ? (
          <>
            {createDog.isPending ? "Generando…" : "Generar plan con IA"}
            <Icon name="auto_awesome" className="text-xl" />
          </>
        ) : (
          <>
            Siguiente
            <Icon name="arrow_forward" className="text-xl" />
          </>
        )}
      </Button>
    </div>
  )
}
