/** Capitaliza la primera letra (los nombres del backend vienen en minúscula). */
export const cap = (s?: string | null) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : ""

const REINFORCEMENT_ICON: Record<string, string> = {
  pelota: "sports_baseball",
  comida: "restaurant",
  caricias: "front_hand",
}

/** Icono Material según el tipo de refuerzo. */
export const reinforcementIcon = (name?: string) =>
  name ? REINFORCEMENT_ICON[name.toLowerCase()] ?? "redeem" : "redeem"
