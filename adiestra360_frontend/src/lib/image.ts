/**
 * Utilidades para subir la foto del perro.
 *
 * La imagen se guarda como data URL (base64) en la BD, así que conviene
 * reducirla en el cliente antes de enviarla: se redimensiona a una miniatura
 * y se recomprime a JPEG. Una foto de cámara (varios MB) queda en decenas de KB,
 * suficiente para el avatar del listado y del perfil.
 */

const readAsDataUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })

/**
 * Reduce una imagen (data URL) a una miniatura cuadrada (recorte centrado)
 * como data URL JPEG. Si el navegador no puede decodificar el formato (p. ej.
 * algún HEIC de iOS), devuelve la imagen original tal cual.
 */
export async function thumbnailFromDataUrl(
  dataUrl: string,
  size = 320,
  quality = 0.72
): Promise<string> {
  try {
    const img = await loadImage(dataUrl)
    // Recorte cuadrado centrado (el avatar es un círculo).
    const side = Math.min(img.width, img.height)
    const sx = (img.width - side) / 2
    const sy = (img.height - side) / 2

    const canvas = document.createElement("canvas")
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext("2d")
    if (!ctx) return dataUrl
    ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size)
    return canvas.toDataURL("image/jpeg", quality)
  } catch {
    return dataUrl
  }
}

/** Igual que `thumbnailFromDataUrl`, pero a partir de un archivo (input file). */
export async function fileToThumbnailDataUrl(
  file: File,
  size = 320,
  quality = 0.72
): Promise<string> {
  return thumbnailFromDataUrl(await readAsDataUrl(file), size, quality)
}
