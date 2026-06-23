import { cn } from "@/lib/utils"
import { Icon } from "@/components/Icon"
import { Stepper } from "@/components/Stepper"

type Accent = "primary" | "coral" | "amber"

const ACCENTS: Record<Accent, { bar: string; heroBg: string; heroText: string }> = {
  primary: { bar: "bg-primary", heroBg: "bg-primary-soft", heroText: "text-primary-deep" },
  coral: { bar: "bg-coral", heroBg: "bg-coral-soft", heroText: "text-coral-deep" },
  amber: { bar: "bg-amber", heroBg: "bg-amber-soft", heroText: "text-amber-deep" },
}

interface OnboardingHeaderProps {
  title: string
  step: number
  totalSteps: number
  heroIcon: string
  heroTitle: string
  accent?: Accent
  onBack?: () => void
}

export function OnboardingHeader({
  title,
  step,
  totalSteps,
  heroIcon,
  heroTitle,
  accent = "primary",
  onBack,
}: OnboardingHeaderProps) {
  const a = ACCENTS[accent]
  return (
    <div className="pt-safe">
      <div className="flex items-center gap-2.5 py-2">
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            aria-label="Atrás"
            className="grid size-9 place-items-center rounded-xl border border-border bg-card"
          >
            <Icon name="arrow_back" className="text-xl" />
          </button>
        ) : (
          <span className="size-9" />
        )}
        <h2 className="text-lg font-bold">{title}</h2>
      </div>

      <Stepper total={totalSteps} current={step} accentClass={a.bar} />

      <div
        className={cn(
          "relative mt-4 mb-4 flex items-center gap-3 overflow-hidden rounded-2xl p-4",
          a.heroBg
        )}
      >
        <Icon
          name="pets"
          fill
          className={cn(
            "pointer-events-none absolute -right-1 -top-3 rotate-[16deg] text-[78px] opacity-[0.08]",
            a.heroText
          )}
        />
        <div className="relative z-10 grid size-12 flex-none place-items-center rounded-xl bg-card shadow-sm">
          <Icon name={heroIcon} fill className={cn("text-2xl", a.heroText)} />
        </div>
        <div className="relative z-10">
          <b className="block font-display text-base">{heroTitle}</b>
          <small className={cn("text-xs font-extrabold", a.heroText)}>
            PASO {step} DE {totalSteps}
          </small>
        </div>
      </div>
    </div>
  )
}
