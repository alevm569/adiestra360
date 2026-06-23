import { cn } from "@/lib/utils"

interface IconProps {
  /** Nombre del símbolo de Material Symbols Rounded, p. ej. "pets", "local_fire_department" */
  name: string
  /** Versión rellena del icono */
  fill?: boolean
  className?: string
}

/**
 * Icono de Material Symbols Rounded (el set de iconos de la marca).
 * Uso: <Icon name="pets" fill className="text-2xl" />
 * El tamaño se controla con font-size (clases text-*).
 */
export function Icon({ name, fill, className }: IconProps) {
  return (
    <span
      aria-hidden="true"
      className={cn("material-symbols-rounded", fill && "fill", className)}
    >
      {name}
    </span>
  )
}
