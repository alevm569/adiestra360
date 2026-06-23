import * as React from "react"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface InputFieldProps extends React.ComponentProps<"input"> {
  label: string
  /** Nombre del icono Material a la izquierda */
  icon: string
}

/** Campo de formulario con etiqueta + icono adelante. Estilo de la marca. */
export function InputField({
  label,
  icon,
  id,
  className,
  ...props
}: InputFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Icon
          name={icon}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-lg text-muted-foreground"
        />
        <Input id={id} className={cn("h-12 rounded-xl pl-10", className)} {...props} />
      </div>
    </div>
  )
}
