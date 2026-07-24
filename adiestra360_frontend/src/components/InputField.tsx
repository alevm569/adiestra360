import * as React from "react"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface InputFieldProps extends React.ComponentProps<"input"> {
  label: string
  /** Nombre del icono Material a la izquierda */
  icon: string
  /** Texto de ayuda bajo el campo. */
  hint?: string
}

/**
 * Campo de formulario con etiqueta + icono adelante. Estilo de la marca.
 *
 * Los campos de contraseña traen un botón para mostrar/ocultar lo escrito:
 * teclear a ciegas en el móvil es la causa más común de "credenciales
 * inválidas".
 */
export function InputField({
  label,
  icon,
  id,
  className,
  type,
  hint,
  ...props
}: InputFieldProps) {
  const isPassword = type === "password"
  const [reveal, setReveal] = React.useState(false)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Icon
          name={icon}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-lg text-muted-foreground"
        />
        <Input
          id={id}
          type={isPassword && reveal ? "text" : type}
          className={cn("h-12 rounded-xl pl-10", isPassword && "pr-12", className)}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setReveal((v) => !v)}
            aria-label={reveal ? "Ocultar contraseña" : "Mostrar contraseña"}
            aria-pressed={reveal}
            tabIndex={-1}
            className="absolute right-1 top-1/2 grid size-10 -translate-y-1/2 place-items-center rounded-xl text-muted-foreground"
          >
            <Icon name={reveal ? "visibility_off" : "visibility"} className="text-xl" />
          </button>
        )}
      </div>
      {hint && (
        <small className="text-[11px] font-semibold text-muted-foreground">{hint}</small>
      )}
    </div>
  )
}
