import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { Brandmark } from "@/components/Brandmark"
import { Icon } from "@/components/Icon"
import { InputField } from "@/components/InputField"
import { Button } from "@/components/ui/button"
import { apiErrorMessage, useConfirmPasswordReset, useRequestPasswordReset } from "./api"

/**
 * Recuperación de contraseña en dos pasos dentro de la misma pantalla:
 * 1) se pide el correo y el backend manda un código de 6 dígitos;
 * 2) se escribe ese código junto con la nueva contraseña.
 *
 * Se usa un código y no un enlace porque la app corre como PWA y como APK de
 * Capacitor: un enlace del correo abriría el navegador y dejaría al usuario
 * fuera de la app instalada.
 */
export function ForgotPasswordPage() {
  const navigate = useNavigate()
  const request = useRequestPasswordReset()
  const confirm = useConfirmPasswordReset()

  const [step, setStep] = useState<"email" | "code">("email")
  const [email, setEmail] = useState("")
  const [code, setCode] = useState("")
  const [password, setPassword] = useState("")
  const [repeat, setRepeat] = useState("")
  const [localError, setLocalError] = useState<string | null>(null)

  function handleRequest(e: FormEvent) {
    e.preventDefault()
    setLocalError(null)
    request.mutate(
      { email: email.trim() },
      { onSuccess: () => setStep("code") }
    )
  }

  function handleConfirm(e: FormEvent) {
    e.preventDefault()
    setLocalError(null)
    if (password.length < 8) {
      setLocalError("La contraseña debe tener al menos 8 caracteres.")
      return
    }
    if (password !== repeat) {
      setLocalError("Las contraseñas no coinciden.")
      return
    }
    confirm.mutate(
      { email: email.trim(), code: code.trim(), new_password: password },
      // El backend ya devolvió tokens: se entra directo al dashboard.
      { onSuccess: () => navigate("/", { replace: true }) }
    )
  }

  // En el paso 2 puede fallar el cambio o el reenvío; el del cambio manda.
  let error = localError
  if (!error && step === "code" && confirm.isError) {
    error = apiErrorMessage(confirm.error, "El código no es válido o ya caducó.")
  }
  if (!error && request.isError) {
    error = apiErrorMessage(
      request.error,
      "No pudimos enviar el correo. Inténtalo de nuevo en unos minutos."
    )
  }

  return (
    <div className="relative min-h-safe overflow-hidden px-6 pt-safe pb-safe">
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

      <div className="relative z-10 mx-auto flex min-h-safe w-full max-w-sm flex-col justify-center py-10">
        <div className="mb-5 flex justify-center">
          <Brandmark size={64} />
        </div>

        <h1 className="text-center text-2xl font-bold">
          {step === "email" ? "¿Olvidaste tu contraseña?" : "Revisa tu correo"}
        </h1>
        <p className="mb-7 mt-1.5 text-center text-sm font-semibold text-muted-foreground">
          {step === "email" ? (
            "Escribe tu correo y te enviamos un código para crear una nueva."
          ) : (
            <>
              Enviamos un código de 6 dígitos a{" "}
              <b className="text-foreground">{email.trim()}</b>. Caduca en{" "}
              {request.data?.expires_in_minutes ?? 15} minutos; si no lo ves,
              revisa la carpeta de spam.
            </>
          )}
        </p>

        {step === "email" ? (
          <form onSubmit={handleRequest} className="flex flex-col gap-4">
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

            {error && (
              <p className="text-sm font-semibold text-destructive">{error}</p>
            )}

            <Button
              type="submit"
              disabled={request.isPending}
              className="mt-2 h-12 rounded-xl text-base font-extrabold"
            >
              {request.isPending ? "Enviando…" : "Enviar código"}
              <Icon name="send" className="text-xl" />
            </Button>
          </form>
        ) : (
          <form onSubmit={handleConfirm} className="flex flex-col gap-4">
            <InputField
              id="code"
              label="Código"
              icon="pin"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="000000"
              maxLength={6}
              // Solo dígitos: en el móvil el teclado numérico deja colar espacios.
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              className="tracking-[0.4em]"
              required
            />
            <InputField
              id="new-password"
              label="Nueva contraseña"
              icon="lock"
              type="password"
              autoComplete="new-password"
              placeholder="Mínimo 8 caracteres"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <InputField
              id="repeat-password"
              label="Repite la contraseña"
              icon="lock"
              type="password"
              autoComplete="new-password"
              placeholder="Repite tu contraseña"
              value={repeat}
              onChange={(e) => setRepeat(e.target.value)}
              required
            />

            {error && (
              <p className="text-sm font-semibold text-destructive">{error}</p>
            )}

            <Button
              type="submit"
              disabled={confirm.isPending || code.length < 6}
              className="mt-2 h-12 rounded-xl text-base font-extrabold"
            >
              {confirm.isPending ? "Guardando…" : "Cambiar contraseña"}
              <Icon name="check" className="text-xl" />
            </Button>

            <ResendButton
              onResend={() => {
                setLocalError(null)
                request.mutate({ email: email.trim() })
              }}
              pending={request.isPending}
            />
          </form>
        )}

        <p className="mt-5 text-center text-sm font-semibold text-muted-foreground">
          <Link to="/login" className="font-extrabold text-primary-deep">
            Volver a iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  )
}

/**
 * Reenvío con cuenta atrás: el backend ignora las peticiones repetidas antes de
 * 60 s, así que el botón espera lo mismo en vez de fingir que envió otro correo.
 */
function ResendButton({
  onResend,
  pending,
}: {
  onResend: () => void
  pending: boolean
}) {
  const [seconds, setSeconds] = useState(60)

  useEffect(() => {
    if (seconds <= 0) return
    const timer = setTimeout(() => setSeconds((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [seconds])

  if (seconds > 0) {
    return (
      <p className="text-center text-xs font-bold text-muted-foreground">
        ¿No te llegó? Puedes pedir otro código en {seconds}s
      </p>
    )
  }

  return (
    <button
      type="button"
      disabled={pending}
      onClick={() => {
        onResend()
        setSeconds(60)
      }}
      className="text-center text-xs font-extrabold text-primary-deep disabled:opacity-50"
    >
      Enviar otro código
    </button>
  )
}
