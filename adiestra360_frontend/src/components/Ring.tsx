import { cn } from "@/lib/utils"

interface RingProps {
  /** Porcentaje 0-100 que se rellena del anillo */
  percent: number
  /** Lado del círculo en px */
  size?: number
  /** Grosor del anillo en px */
  thickness?: number
  className?: string
  children?: React.ReactNode
}

/**
 * Anillo de progreso — el elemento de marca "360".
 * El color de relleno es el primario; el resto, el verde suave.
 */
export function Ring({
  percent,
  size = 72,
  thickness = 8,
  className,
  children,
}: RingProps) {
  const clamped = Math.max(0, Math.min(100, percent))
  return (
    <div
      className={cn("grid flex-none place-items-center rounded-full", className)}
      style={{
        width: size,
        height: size,
        background: `conic-gradient(var(--primary) ${clamped}%, var(--primary-soft) 0)`,
      }}
    >
      <div
        className="grid place-items-center rounded-full bg-card text-center leading-none"
        style={{ width: size - thickness * 2, height: size - thickness * 2 }}
      >
        {children}
      </div>
    </div>
  )
}
