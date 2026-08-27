import { useRef } from "react"
import { Link, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { cap } from "@/lib/exercise"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { usePhotoPicker } from "@/features/photo/usePhotoPicker"
import { useActiveDogId, useDogStore } from "@/stores/dogStore"
import { useDogs, useUpdateDogPhoto } from "./api"

export function DogsPage() {
  const navigate = useNavigate()
  const activeDogId = useActiveDogId()
  const setActiveDog = useDogStore((s) => s.setActiveDog)
  const { data: dogs, isLoading, isError } = useDogs()
  const updatePhoto = useUpdateDogPhoto()

  // Perro cuya foto se está editando (el picker es único y compartido).
  const editingId = useRef<string | null>(null)
  const picker = usePhotoPicker(
    (photo) => {
      if (editingId.current) updatePhoto.mutate({ id: editingId.current, photo })
    },
    {
      onRemove: () => {
        if (editingId.current) updatePhoto.mutate({ id: editingId.current, photo: null })
      },
    }
  )

  function editPhoto(id: string, hasPhoto: boolean) {
    editingId.current = id
    picker.start({ canRemove: hasPhoto })
  }

  function select(id: string) {
    setActiveDog(id)
    navigate("/")
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
        <h2 className="py-2 text-lg font-bold">Mis perros</h2>
      </div>

      {isLoading && (
        <div className="grid place-items-center py-20 text-muted-foreground">
          <Icon name="progress_activity" className="animate-spin text-3xl" />
        </div>
      )}

      {isError && (
        <p className="mt-4 rounded-2xl border border-border bg-card p-6 text-center text-sm font-semibold text-destructive">
          No pudimos cargar tus perros.
        </p>
      )}

      {dogs && (
        <div className="mt-4 flex flex-col gap-2.5">
          {dogs.map((dog) => {
            const isActive = dog.id === activeDogId
            const updating = updatePhoto.isPending && editingId.current === dog.id
            return (
              <div
                key={dog.id}
                className={cn(
                  "flex items-center gap-3 rounded-2xl border bg-card p-3.5 transition-colors",
                  isActive ? "border-primary ring-[3px] ring-primary-soft" : "border-border"
                )}
              >
                {/* La foto es su propio botón: toca para cambiarla. */}
                <button
                  type="button"
                  onClick={() => editPhoto(dog.id, !!dog.photo)}
                  aria-label={dog.photo ? `Cambiar la foto de ${dog.name}` : `Añadir foto a ${dog.name}`}
                  className="relative flex-none"
                >
                  {dog.photo ? (
                    <img
                      src={dog.photo}
                      alt={dog.name}
                      className="size-12 rounded-2xl object-cover"
                    />
                  ) : (
                    <div className="grid size-12 place-items-center rounded-2xl bg-primary-soft text-primary-deep">
                      <Icon name="pets" fill className="text-2xl" />
                    </div>
                  )}
                  <span className="absolute -bottom-1.5 -right-1.5 grid size-7 place-items-center rounded-full border-2 border-card bg-primary-deep text-white shadow-sm">
                    <Icon name="photo_camera" fill className="text-base" />
                  </span>
                  {updating && (
                    <span className="absolute inset-0 grid place-items-center rounded-2xl bg-card/70 text-primary-deep">
                      <Icon name="progress_activity" className="animate-spin text-xl" />
                    </span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => select(dog.id)}
                  className="flex min-w-0 flex-1 items-center gap-3 text-left"
                >
                  <div className="min-w-0 flex-1">
                    <b className="block font-display text-base">{dog.name}</b>
                    <small className="text-xs font-bold text-muted-foreground">
                      {[cap(dog.breed), `Nivel ${dog.training_level ?? 1}`]
                        .filter(Boolean)
                        .join(" · ")}
                    </small>
                  </div>
                  {isActive ? (
                    <span className="rounded-full bg-primary-soft px-2.5 py-1 text-[10px] font-extrabold text-primary-deep">
                      Activo
                    </span>
                  ) : (
                    <Icon name="chevron_right" className="text-xl text-muted-foreground" />
                  )}
                </button>
              </div>
            )
          })}

          <Button
            asChild
            variant="outline"
            className="mt-2 h-12 rounded-xl border-dashed text-base font-extrabold"
          >
            <Link to="/onboarding/dog">
              <Icon name="add" className="text-xl" />
              Agregar otro perro
            </Link>
          </Button>
        </div>
      )}

      {picker.element}
    </div>
  )
}
