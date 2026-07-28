import { useRef, useState, type ChangeEvent } from "react"
import { Capacitor } from "@capacitor/core"
import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { fileToThumbnailDataUrl, thumbnailFromDataUrl } from "@/lib/image"

type Source = "camera" | "gallery"

interface StartOptions {
  /** Muestra la opción "Quitar foto" (cuando el perro ya tiene una). */
  canRemove?: boolean
}

interface PickerOptions {
  onRemove?: () => void
}

/**
 * Selector de foto con AVISO DE PERMISO PREVIO.
 *
 * Al abrirlo se muestra una hoja explicando que se usará la cámara o la galería
 * y para qué. Solo cuando el usuario elige una opción (su aceptación) se accede:
 *  - En nativo (Capacitor): se pide el permiso del sistema (cámara o fotos) y,
 *    únicamente si lo concede, se abre. Si lo niega, se le explica cómo activarlo.
 *  - En web: el propio diálogo del navegador es la puerta de permiso; se dispara
 *    un <input type="file"> (con `capture` para la cámara).
 *
 * Devuelve una miniatura como data URL vía `onPicked`.
 */
export function usePhotoPicker(
  onPicked: (dataUrl: string) => void,
  options: PickerOptions = {}
) {
  const [open, setOpen] = useState(false)
  const [canRemove, setCanRemove] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cameraRef = useRef<HTMLInputElement>(null)
  const galleryRef = useRef<HTMLInputElement>(null)

  const isNative = Capacitor.isNativePlatform()

  function start(opts: StartOptions = {}) {
    setError(null)
    setCanRemove(!!opts.canRemove)
    setOpen(true)
  }

  function close() {
    if (!busy) setOpen(false)
  }

  async function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = "" // permite volver a elegir la misma foto
    if (!file) return
    setBusy(true)
    try {
      onPicked(await fileToThumbnailDataUrl(file))
      setOpen(false)
    } catch {
      setError("No se pudo procesar la imagen. Inténtalo con otra.")
    } finally {
      setBusy(false)
    }
  }

  async function choose(source: Source) {
    setError(null)
    if (isNative) {
      await chooseNative(source)
    } else {
      // El selector del navegador ya pide al usuario qué compartir.
      ;(source === "camera" ? cameraRef : galleryRef).current?.click()
    }
  }

  async function chooseNative(source: Source) {
    setBusy(true)
    try {
      const { Camera, CameraSource, CameraResultType } = await import("@capacitor/camera")
      const group = source === "camera" ? "camera" : "photos"

      // 1) Verificar el permiso; si está "prompt", pedirlo (diálogo del sistema).
      let status = await Camera.checkPermissions()
      let state = source === "camera" ? status.camera : status.photos
      if (state === "prompt" || state === "prompt-with-rationale") {
        status = await Camera.requestPermissions({ permissions: [group] })
        state = source === "camera" ? status.camera : status.photos
      }

      // 2) Sin permiso concedido, no accedemos: se explica cómo habilitarlo.
      if (state !== "granted" && state !== "limited") {
        setError(
          source === "camera"
            ? "No diste permiso para la cámara. Puedes activarlo en los ajustes del teléfono."
            : "No diste permiso para tus fotos. Puedes activarlo en los ajustes del teléfono."
        )
        return
      }

      // 3) Con permiso, abrir cámara o galería.
      const photo = await Camera.getPhoto({
        source: source === "camera" ? CameraSource.Camera : CameraSource.Photos,
        resultType: CameraResultType.DataUrl,
        quality: 80,
        width: 640,
        correctOrientation: true,
      })
      if (photo.dataUrl) {
        onPicked(await thumbnailFromDataUrl(photo.dataUrl))
        setOpen(false)
      }
    } catch (err) {
      // getPhoto lanza también si el usuario cancela: eso no es un error.
      const msg = String((err as Error)?.message ?? "").toLowerCase()
      if (!msg.includes("cancel")) {
        setError("No se pudo abrir. Inténtalo de nuevo.")
      }
    } finally {
      setBusy(false)
    }
  }

  function remove() {
    options.onRemove?.()
    setOpen(false)
  }

  const element = (
    <>
      {/* Inputs de respaldo para web (montados siempre para poder dispararlos). */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFile}
      />
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFile}
      />
      {open && (
        <PhotoPickerSheet
          busy={busy}
          error={error}
          canRemove={canRemove && !!options.onRemove}
          onCamera={() => choose("camera")}
          onGallery={() => choose("gallery")}
          onRemove={remove}
          onClose={close}
        />
      )}
    </>
  )

  return { start, element, busy }
}

function PhotoPickerSheet({
  busy,
  error,
  canRemove,
  onCamera,
  onGallery,
  onRemove,
  onClose,
}: {
  busy: boolean
  error: string | null
  canRemove: boolean
  onCamera: () => void
  onGallery: () => void
  onRemove: () => void
  onClose: () => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="Foto del perro"
      onClick={onClose}
    >
      <div
        className="w-full rounded-t-3xl bg-background px-5 pb-safe pt-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-center gap-2">
          <h2 className="flex-1 text-lg font-bold">Foto de tu perro</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            disabled={busy}
            className="grid size-9 flex-none place-items-center rounded-xl border border-border bg-card disabled:opacity-50"
          >
            <Icon name="close" className="text-xl" />
          </button>
        </div>

        {/* Aviso de permiso: se pide acceso ANTES de abrir cámara/galería. */}
        <p className="mb-4 text-sm font-semibold text-muted-foreground">
          Adiestra360 usará tu cámara o galería solo para la foto de tu perro.
          Elige una opción para dar acceso.
        </p>

        {error && (
          <p className="mb-3 flex items-start gap-1.5 rounded-xl bg-coral-soft p-3 text-xs font-bold text-coral-deep">
            <Icon name="error" fill className="flex-none text-sm" />
            {error}
          </p>
        )}

        {busy ? (
          <div className="grid place-items-center py-8 text-muted-foreground">
            <Icon name="progress_activity" className="animate-spin text-3xl" />
          </div>
        ) : (
          <div className="flex flex-col gap-2.5 pb-2">
            <SheetAction icon="photo_camera" label="Tomar foto" onClick={onCamera} />
            <SheetAction icon="photo_library" label="Elegir de la galería" onClick={onGallery} />
            {canRemove && (
              <SheetAction
                icon="delete"
                label="Quitar foto"
                tone="danger"
                onClick={onRemove}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SheetAction({
  icon,
  label,
  tone = "default",
  onClick,
}: {
  icon: string
  label: string
  tone?: "default" | "danger"
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-3 rounded-2xl border border-border bg-card p-3.5 text-left text-sm font-bold"
    >
      <span
        className={cn(
          "grid size-9 flex-none place-items-center rounded-xl",
          tone === "danger" ? "bg-coral-soft text-coral" : "bg-primary-soft text-primary-deep"
        )}
      >
        <Icon name={icon} className="text-lg" />
      </span>
      {label}
      <Icon name="chevron_right" className="ml-auto text-xl text-muted-foreground" />
    </button>
  )
}
