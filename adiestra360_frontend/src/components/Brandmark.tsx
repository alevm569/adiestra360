import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"

interface BrandmarkProps {
  /** Tamaño del logo en px (lado del círculo) */
  size?: number
  className?: string
}

/**
 * Logo de Adiestra360: una pata dentro de un anillo de progreso (el "360").
 * El mismo anillo que se repite en niveles y planes por toda la app.
 */
export function Brandmark({ size = 56, className }: BrandmarkProps) {
  return (
    <div
      className={cn("brandmark", className)}
      style={{ "--lsize": `${size}px` } as React.CSSProperties}
    >
      <Icon name="pets" fill />
    </div>
  )
}

/** Logo + wordmark "Adiestra360" en línea. */
export function Wordmark({
  size = 34,
  className,
}: {
  size?: number
  className?: string
}) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Brandmark size={size} />
      <span className="font-display text-base font-extrabold">
        Adiestra<span className="text-primary-deep">360</span>
      </span>
    </div>
  )
}
