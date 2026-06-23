import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
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
    register.mutate(
      { name, email, password },
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

        {error && (
          <p className="text-sm font-semibold text-destructive">{error}</p>
        )}

        <Button
          type="submit"
          disabled={register.isPending}
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
