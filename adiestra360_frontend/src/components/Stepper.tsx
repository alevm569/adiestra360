import { cn } from "@/lib/utils"

interface StepperProps {
  total: number
  /** Paso actual (1-indexado) */
  current: number
  /** Clase de color de la barra activa, p. ej. "bg-primary", "bg-coral", "bg-amber" */
  accentClass?: string
}

/** Barras de progreso del onboarding. */
export function Stepper({ total, current, accentClass = "bg-primary" }: StepperProps) {
  return (
    <div className="flex gap-1.5">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={cn(
            "h-1.5 flex-1 rounded-full transition-colors",
            i < current ? accentClass : "bg-muted"
          )}
        />
      ))}
    </div>
  )
}
