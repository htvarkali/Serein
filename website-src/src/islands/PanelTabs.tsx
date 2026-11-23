import { useEffect, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RmseBars, type Horizon } from "./RmseBars"

export type Panel = {
  id: string
  label: string
  lang?: string
  className: string
  html: string
  horizon?: Horizon
}

type Props = {
  panels: Panel[]
  initial: string
  ariaLabel: string
  tone: "light" | "dark"
  onMounted: () => void
}

// Replaces the site's aria-pressed switcher with Radix tabs: arrow keys move
// between options and screen readers announce a real tab list.
export function PanelTabs({ panels, initial, ariaLabel, tone, onMounted }: Props) {
  const [active, setActive] = useState(initial)
  useEffect(onMounted, [onMounted])
  const horizons = panels.flatMap(p => (p.horizon ? [p.horizon] : []))
  const current = panels.find(p => p.id === active)?.horizon

  return (
    <Tabs value={active} onValueChange={setActive} className="gap-0">
      <TabsList
        aria-label={ariaLabel}
        className="mb-[1.15rem] h-auto! w-full flex-wrap justify-start gap-[.45rem] rounded-none bg-transparent p-0"
      >
        {panels.map(p => (
          <TabsTrigger
            key={p.id}
            value={p.id}
            lang={p.lang}
            className={
              "h-auto flex-none cursor-pointer bg-transparent rounded-[.25rem] border px-[.9rem] py-[.62rem] text-[.86rem] font-bold shadow-none! transition-colors duration-200 " +
              (tone === "dark"
                ? "border-[#7c9e90] text-[var(--paper)] hover:bg-[var(--sage)] hover:text-[var(--deep)] data-[state=active]:border-[var(--sage)] data-[state=active]:bg-[var(--sage)] data-[state=active]:text-[var(--deep)]"
                : "border-[var(--border)] text-[var(--ink)] hover:border-[var(--grove)] data-[state=active]:border-[var(--grove)] data-[state=active]:bg-[var(--grove)] data-[state=active]:text-[var(--paper)]")
            }
          >
            {p.label}
          </TabsTrigger>
        ))}
      </TabsList>

      {current && horizons.length > 1 && <RmseBars current={current} all={horizons} />}

      {panels.map(p => (
        <TabsContent
          key={p.id}
          value={p.id}
          lang={p.lang}
          className={p.className + " animate-[island-in_.32s_ease-out]"}
        >
          {/* Same-page markup that was already in the static HTML. The original
              id stays on this wrapper so existing #links keep working. */}
          <div id={p.id} className="contents" dangerouslySetInnerHTML={{ __html: p.html }} />
        </TabsContent>
      ))}
    </Tabs>
  )
}
