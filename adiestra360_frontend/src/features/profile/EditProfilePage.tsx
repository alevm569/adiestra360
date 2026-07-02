import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { Icon } from "@/components/Icon"
import { InputField } from "@/components/InputField"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/stores/authStore"
import { useUpdateProfile } from "./api"

export function EditProfilePage() {
  const navigate = useNavigate()
  const user = useAuth((s) => s.user)
  const update = useUpdateProfile()
  const [name, setName] = useState(user?.name ?? "")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    update.mutate(
      { name: name.trim() },
      { onSuccess: () => navigate("/perfil") }
    )
  }

  return (
    <div className="min-h-safe px-5 pb-safe">
      <div className="flex items-center gap-2.5 pt-safe">
        <button
          type="button"
          onClick={() => navigate("/perfil")}
          aria-label="Atrás"
          className="grid size-9 place-items-center rounded-xl border border-border bg-card"
        >
          <Icon name="arrow_back" className="text-xl" />
        </button>
        <h2 className="py-2 text-lg font-bold">Editar perfil</h2>
      </div>

      <div className="mx-auto my-6 grid size-24 place-items-center rounded-full border-[3px] border-card bg-linear-to-br from-primary to-primary-deep text-white shadow-sm">
        <Icon name="person" fill className="text-5xl" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <InputField
          id="name"
          label="Nombre"
          icon="person"
          placeholder="Tu nombre"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <div className="flex flex-col gap-2">
          <span className="text-xs font-extrabold">Correo</span>
          <div className="flex items-center gap-2.5 rounded-xl border border-border bg-muted px-3 py-3 text-sm font-semibold text-muted-foreground">
            <Icon name="mail" className="text-lg" />
            {user?.email}
          </div>
          <small className="text-[11px] font-semibold text-muted-foreground">
            El correo no se puede cambiar por ahora.
          </small>
        </div>

        {update.isError && (
          <p className="text-sm font-semibold text-destructive">
            No pudimos guardar los cambios. Inténtalo de nuevo.
          </p>
        )}

        <Button
          type="submit"
          disabled={update.isPending || !name.trim()}
          className="mt-3 h-12 rounded-xl text-base font-extrabold"
        >
          {update.isPending ? "Guardando…" : "Guardar cambios"}
          <Icon name="check" className="text-xl" />
        </Button>
      </form>
    </div>
  )
}
