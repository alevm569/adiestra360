import { useState, type ReactNode } from "react"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"

/**
 * Reglas del progreso, explicadas donde se generan las dudas.
 *
 * Fuente de verdad en el backend:
 *  - `training/views.check_exercise_mastered` (3 sesiones exitosas + la última
 *    Excelente; 1 Excelente si la encuesta ya lo marcó como dominado),
 *  - `lib/exercise.criteriaResult` (cómo se puntúa cada sesión),
 *  - `recommendations/views.SUCCESS_THRESHOLD` (sugerencia de refuerzo < 50%).
 * Si cambia alguna, actualizar también este texto.
 */
const RULES: { icon: string; tone: string; title: string; body: ReactNode }[] = [
  {
    icon: "checklist",
    tone: "bg-sky-soft text-sky-deep",
    title: "Cómo se puntúa cada sesión",
    body: (
      <>
        Al registrar la sesión marcas los criterios que logró tu perro.{" "}
        <b>Excelente</b> = cumplió todos; <b>Va bien</b> = cumplió el criterio clave (el
        primero de la lista) pero no todos; <b>Reforzar</b> = le faltó el criterio clave.
        Excelente y Va bien cuentan como sesión exitosa.
      </>
    ),
  },
  {
    icon: "verified",
    tone: "bg-primary-soft text-primary-deep",
    title: "Cuándo un ejercicio queda Superado",
    body: (
      <>
        Cuando sus <b>últimas 3 sesiones fueron exitosas</b> y la <b>más reciente fue
        Excelente</b>. Si la encuesta inicial ya lo marcó como dominado, basta con 1
        sesión Excelente para confirmarlo.
      </>
    ),
  },
  {
    icon: "donut_large",
    tone: "bg-amber-soft text-amber-deep",
    title: "Por qué el porcentaje no sube en cada sesión",
    body: (
      <>
        El anillo del inicio mide <b>ejercicios superados ÷ ejercicios activos del
        plan</b>, no sesiones. Por eso no se mueve al registrar una sesión suelta: salta
        el día que un ejercicio llega a Superado (normalmente, a la tercera sesión buena).
      </>
    ),
  },
  {
    icon: "trending_up",
    tone: "bg-primary-soft text-primary-deep",
    title: "Lo que sí cambia en cada sesión",
    body: (
      <>
        Tu <b>XP</b> y tu <b>racha</b>, y en la tarjeta de Desempeño la <b>tasa de
        éxito</b>, el <b>tiempo de respuesta</b> y el <b>número de sesiones</b>. También
        cambia la etiqueta del ejercicio: Empezar → Continuar → Repasar.
      </>
    ),
  },
  {
    icon: "lock_open",
    tone: "bg-sky-soft text-sky-deep",
    title: "Desbloqueos y niveles",
    body: (
      <>
        Trabajas con <b>2 ejercicios activos</b> a la vez. Al superar uno se desbloquea el
        siguiente del nivel, y cuando superas todos los activos, tu perro{" "}
        <b>sube de nivel</b> y el plan se llena con los ejercicios del nuevo.
      </>
    ),
  },
  {
    icon: "lightbulb",
    tone: "bg-coral-soft text-coral-deep",
    title: "Cuándo la IA sugiere cambiar el refuerzo",
    body: (
      <>
        Con al menos 3 sesiones y una tasa de éxito <b>por debajo del 50%</b>, la app te
        propone el siguiente refuerzo del ranking que salió de la encuesta (comida,
        pelota, caricias…).
      </>
    ),
  },
]

/** Hoja inferior con las reglas del progreso. */
export function ProgressRulesSheet({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="Cómo funciona el progreso"
      onClick={onClose}
    >
      <div
        className="max-h-[86dvh] w-full overflow-y-auto rounded-t-3xl bg-background px-5 pb-safe shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center gap-2 bg-background pb-2 pt-4">
          <h2 className="flex-1 text-lg font-bold">Cómo funciona el progreso</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="grid size-9 flex-none place-items-center rounded-xl border border-border bg-card"
          >
            <Icon name="close" className="text-xl" />
          </button>
        </div>

        <p className="mb-4 text-sm font-semibold text-muted-foreground">
          Estas son las reglas que usa la app para decidir cuándo avanzas.
        </p>

        <div className="flex flex-col gap-2.5 pb-4">
          {RULES.map((r) => (
            <div key={r.title} className="rounded-2xl border border-border bg-card p-3.5">
              <div className="flex items-center gap-2.5">
                <span
                  className={cn(
                    "grid size-9 flex-none place-items-center rounded-xl",
                    r.tone
                  )}
                >
                  <Icon name={r.icon} fill className="text-lg" />
                </span>
                <b className="text-sm">{r.title}</b>
              </div>
              <p className="mt-2 text-sm font-semibold text-muted-foreground">{r.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Disparador de la hoja de reglas. Se coloca junto a los números que confunden
 * (el anillo del inicio, el resumen del plan), que es donde nace la pregunta.
 */
export function ProgressRulesButton({
  label = "¿Cómo funciona?",
  className,
}: {
  label?: string
  className?: string
}) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "inline-flex items-center gap-1 text-[11px] font-extrabold text-primary-deep",
          className
        )}
      >
        <Icon name="help" fill className="text-sm" />
        {label}
      </button>
      {open && <ProgressRulesSheet onClose={() => setOpen(false)} />}
    </>
  )
}
