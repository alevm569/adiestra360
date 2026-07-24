import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { OnboardingHeader } from "@/components/OnboardingHeader"
import { InputField } from "@/components/InputField"
import { Button } from "@/components/ui/button"
import { Icon } from "@/components/Icon"
import { useOnboarding } from "@/stores/onboardingStore"
import type { DogDraft } from "@/types"

const ENERGY: { value: DogDraft["energy_level"]; label: string }[] = [
  { value: "bajo", label: "Bajo" },
  { value: "medio", label: "Medio" },
  { value: "alto", label: "Alto" },
]

export function DogProfilePage() {
  const navigate = useNavigate()
  const setDog = useOnboarding((s) => s.setDog)

  const [name, setName] = useState("")
  const [age, setAge] = useState("")
  const [weight, setWeight] = useState("")
  const [breed, setBreed] = useState("")
  const [energy, setEnergy] = useState<DogDraft["energy_level"]>("medio")

  /**
   * El peso admite decimales. Se captura como texto porque en los teclados en
   * español el separador es la coma, y un <input type="number"> la descarta
   * (el campo se queda vacío al escribir "18,5"). Aquí se normaliza a punto y
   * se limita a 2 decimales, que es lo que guarda el backend.
   */
  function handleWeight(value: string) {
    const normalized = value.replace(",", ".")
    if (normalized === "" || /^\d{0,3}(\.\d{0,2})?$/.test(normalized)) {
      setWeight(normalized)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const parsedWeight = parseFloat(weight)
    setDog({
      name: name.trim(),
      breed: breed.trim(),
      age_months: age ? parseInt(age, 10) : null,
      weight: Number.isNaN(parsedWeight) ? null : parsedWeight,
      energy_level: energy,
    })
    navigate("/onboarding/quiz")
  }

  return (
    <div className="min-h-safe px-5 pb-safe">
      <OnboardingHeader
        title="Tu perro"
        step={2}
        totalSteps={3}
        heroIcon="pets"
        heroTitle="El perfil de tu perro"
        accent="coral"
      />

      {/* Foto (la cámara nativa se conecta después con @capacitor/camera) */}
      <div className="relative mx-auto mb-5 grid size-24 place-items-center rounded-full border-[3px] border-card bg-coral-soft text-coral-deep shadow-sm">
        <Icon name="pets" fill className="text-4xl" />
        <span className="absolute -bottom-0.5 -right-0.5 grid size-8 place-items-center rounded-full border-[2.5px] border-card bg-coral-deep text-white">
          <Icon name="photo_camera" className="text-base" />
        </span>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <InputField
          id="dog-name"
          label="Nombre"
          icon="sell"
          placeholder="Rocky"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <div className="flex gap-3">
          <div className="flex-1">
            <InputField
              id="dog-age"
              label="Edad (meses)"
              icon="cake"
              type="number"
              inputMode="numeric"
              min={0}
              placeholder="14"
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />
          </div>
          <div className="flex-1">
            <InputField
              id="dog-weight"
              label="Peso (kg)"
              icon="monitor_weight"
              type="text"
              inputMode="decimal"
              placeholder="18,5"
              hint="Puedes usar decimales"
              value={weight}
              onChange={(e) => handleWeight(e.target.value)}
            />
          </div>
        </div>

        <InputField
          id="dog-breed"
          label="Raza"
          icon="search"
          placeholder="Border Collie"
          value={breed}
          onChange={(e) => setBreed(e.target.value)}
        />

        <div className="flex flex-col gap-2">
          <span className="text-xs font-extrabold">Nivel de energía</span>
          <div className="flex gap-2">
            {ENERGY.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setEnergy(opt.value)}
                className={cn(
                  "flex-1 rounded-xl border-[1.5px] py-3 text-sm font-extrabold transition-colors",
                  energy === opt.value
                    ? "border-coral bg-coral-soft text-coral-deep"
                    : "border-border bg-card text-foreground"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <Button
          type="submit"
          className="mt-3 h-12 rounded-xl bg-linear-to-br from-coral to-coral-deep text-base font-extrabold"
        >
          Continuar a la encuesta
          <Icon name="arrow_forward" className="text-xl" />
        </Button>
      </form>
    </div>
  )
}
