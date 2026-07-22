import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { cn } from "@/lib/utils"
import { OnboardingHeader } from "@/components/OnboardingHeader"
import { InputField } from "@/components/InputField"
import { Button } from "@/components/ui/button"
import { Icon } from "@/components/Icon"
import { useRegister } from "./api"

export function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [consent, setConsent] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLocalError(null)
    if (password.length < 8) {
      setLocalError("La contraseña debe tener al menos 8 caracteres.")
      return
    }
    if (password !== confirm) {
      setLocalError("Las contraseñas no coinciden.")
      return
    }
    if (!consent) {
      setLocalError("Debes aceptar el uso de datos para continuar.")
      return
    }
    register.mutate(
      { name, email, password, research_consent: consent },
      { onSuccess: () => navigate("/onboarding/dog", { replace: true }) }
    )
  }

  const error =
    localError ??
    (register.isError
      ? "No pudimos crear la cuenta. ¿El correo ya está registrado?"
      : null)

  return (
    <div className="min-h-safe px-5 pb-safe">
      <OnboardingHeader
        title="Crea tu cuenta"
        step={1}
        totalSteps={3}
        heroIcon="badge"
        heroTitle="Tus datos"
        accent="primary"
        onBack={() => navigate("/login")}
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <InputField
          id="name"
          label="Nombre"
          icon="person"
          placeholder="Tu nombre"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <InputField
          id="email"
          label="Correo"
          icon="mail"
          type="email"
          inputMode="email"
          placeholder="tucorreo@ejemplo.com"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <InputField
          id="password"
          label="Contraseña"
          icon="lock"
          type="password"
          placeholder="Mínimo 8 caracteres"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <InputField
          id="confirm"
          label="Confirmar contraseña"
          icon="lock"
          type="password"
          placeholder="Repite tu contraseña"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />

        {/* Consentimiento informado (uso de datos para la tesis) */}
        <div className="mt-1 rounded-2xl border border-border bg-card p-3.5">
          <button
            type="button"
            onClick={() => setConsent((v) => !v)}
            aria-pressed={consent}
            className="flex w-full items-start gap-2.5 text-left"
          >
            <Icon
              name={consent ? "check_box" : "check_box_outline_blank"}
              fill={consent}
              className={cn(
                "mt-0.5 flex-none text-xl",
                consent ? "text-primary-deep" : "text-muted-foreground"
              )}
            />
            <span className="text-xs font-semibold text-muted-foreground">
              Acepto que mis datos de uso (entrenamientos, progreso y estadísticas)
              se utilicen de forma anónima con fines académicos para una tesis de
              maestría.
            </span>
          </button>
          <button
            type="button"
            onClick={() => setShowDetail((v) => !v)}
            className="mt-2 ml-[30px] flex items-center gap-1 text-[11px] font-extrabold text-primary-deep"
          >
            {showDetail ? "Ocultar detalle" : "Más información"}
            <Icon
              name={showDetail ? "expand_less" : "expand_more"}
              className="text-sm"
            />
          </button>
          {showDetail && (
            <p className="mt-2 ml-[30px] text-[11px] font-semibold leading-relaxed text-muted-foreground">
              Registramos tu actividad dentro de la app (sesiones de entrenamiento,
              progreso de tu perro y uso de las funciones) para analizar la
              efectividad del sistema como parte de una tesis de maestría. Los datos
              se tratan de forma agregada y anónima, no se comparten con terceros y
              puedes solicitar su eliminación en cualquier momento.
            </p>
          )}
        </div>

        {error && (
          <p className="text-sm font-semibold text-destructive">{error}</p>
        )}

        <Button
          type="submit"
          disabled={register.isPending || !consent}
          className="mt-2 h-12 rounded-xl text-base font-extrabold"
        >
          {register.isPending ? "Creando…" : "Continuar"}
          <Icon name="arrow_forward" className="text-xl" />
        </Button>
      </form>

      <p className="mt-5 text-center text-sm font-semibold text-muted-foreground">
        ¿Ya tienes cuenta?{" "}
        <Link to="/login" className="font-extrabold text-primary-deep">
          Inicia sesión
        </Link>
      </p>
    </div>
  )
}
