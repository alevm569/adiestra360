import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { Brandmark } from "@/components/Brandmark"
import { Icon } from "@/components/Icon"
import { InputField } from "@/components/InputField"
import { Button } from "@/components/ui/button"
import { useLogin } from "./api"

export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    login.mutate(
      { email, password },
      { onSuccess: () => navigate("/", { replace: true }) }
    )
  }

  return (
    <div className="relative min-h-safe overflow-hidden px-6 pt-safe pb-safe">
      {/* Huellas de marca (decorativas) */}
      <Icon
        name="pets"
        fill
        className="pointer-events-none absolute -right-4 top-20 rotate-[18deg] text-[120px] text-primary-deep/[0.06]"
      />
      <Icon
        name="pets"
        fill
        className="pointer-events-none absolute -left-5 top-44 -rotate-[22deg] text-[88px] text-primary-deep/[0.06]"
      />
      <Icon
        name="pets"
        fill
        className="pointer-events-none absolute bottom-16 right-8 rotate-[8deg] text-[64px] text-primary-deep/[0.06]"
      />

      <div className="relative z-10 mx-auto flex min-h-safe w-full max-w-sm flex-col justify-center py-10">
        <div className="mb-5 flex justify-center">
          <Brandmark size={78} />
        </div>
        <div className="mb-6 flex items-center justify-center gap-1 font-display text-2xl font-extrabold">
          Adiestra<span className="text-primary-deep">360</span>
        </div>

        <h1 className="text-center text-2xl font-bold">Hola de nuevo</h1>
        <p className="mb-7 mt-1.5 text-center text-sm font-semibold text-muted-foreground">
          Inicia sesión para seguir entrenando
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <InputField
            id="email"
            label="Correo"
            icon="mail"
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="tucorreo@ejemplo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          {/* El botón del ojo (dentro de InputField) permite revisar lo escrito. */}
          <InputField
            id="password"
            label="Contraseña"
            icon="lock"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {login.isError && (
            <p className="text-sm font-semibold text-destructive">
              Credenciales inválidas. Revisa tu correo y contraseña.
            </p>
          )}

          <Button
            type="submit"
            disabled={login.isPending}
            className="mt-2 h-12 rounded-xl text-base font-extrabold"
          >
            {login.isPending ? "Entrando…" : "Iniciar sesión"}
            <Icon name="arrow_forward" className="text-xl" />
          </Button>
        </form>

        <p className="mt-5 text-center text-sm font-semibold text-muted-foreground">
          ¿Primera vez aquí?{" "}
          <Link to="/register" className="font-extrabold text-primary-deep">
            Crea tu cuenta
          </Link>
        </p>
      </div>
    </div>
  )
}
