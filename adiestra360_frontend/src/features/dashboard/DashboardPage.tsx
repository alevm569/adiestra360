import { Wordmark } from "@/components/Brandmark"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/stores/authStore"

/**
 * Placeholder del dashboard — solo para validar el flujo de login.
 * La pantalla real (anillo de nivel, racha, ejercicios de hoy) se arma después
 * siguiendo el mockup aprobado.
 */
export function DashboardPage() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)

  return (
    <div className="min-h-safe px-5 pt-safe pb-safe">
      <div className="flex items-center justify-between py-3">
        <Wordmark size={34} />
        <Button
          variant="ghost"
          size="icon"
          onClick={logout}
          aria-label="Cerrar sesión"
        >
          <Icon name="logout" className="text-xl" />
        </Button>
      </div>

      <div className="mt-2">
        <p className="text-sm font-extrabold text-muted-foreground">
          Hola, {user?.name ?? "entrenador"}
        </p>
        <h1 className="mt-0.5 text-2xl font-bold">Hoy toca entrenar</h1>
      </div>

      <div className="mt-8 rounded-2xl border border-dashed border-border bg-card p-6 text-center">
        <div className="mx-auto mb-3 flex size-12 items-center justify-center rounded-2xl bg-primary-soft text-primary-deep">
          <Icon name="construction" className="text-2xl" />
        </div>
        <p className="text-sm font-semibold text-muted-foreground">
          Aquí va el dashboard real (anillo de nivel, racha y ejercicios de hoy),
          siguiendo el mockup aprobado.
        </p>
      </div>
    </div>
  )
}
