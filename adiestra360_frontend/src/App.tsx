import { useEffect, useState } from "react"
import { AppRouter } from "@/routes/AppRouter"
import { Brandmark } from "@/components/Brandmark"
import { useAuth } from "@/stores/authStore"
import { useDogStore } from "@/stores/dogStore"

/** Splash mientras se rehidratan los tokens desde Capacitor Preferences. */
function Splash() {
  return (
    <div className="grid min-h-safe place-items-center pt-safe pb-safe">
      <Brandmark size={72} />
    </div>
  )
}

export default function App() {
  const [hydrated, setHydrated] = useState(
    useAuth.persist.hasHydrated() && useDogStore.persist.hasHydrated()
  )

  useEffect(() => {
    const check = () => {
      if (useAuth.persist.hasHydrated() && useDogStore.persist.hasHydrated()) {
        setHydrated(true)
      }
    }
    const unsubs = [
      useAuth.persist.onFinishHydration(check),
      useDogStore.persist.onFinishHydration(check),
    ]
    check()
    return () => unsubs.forEach((u) => u())
  }, [])

  if (!hydrated) return <Splash />
  return <AppRouter />
}
