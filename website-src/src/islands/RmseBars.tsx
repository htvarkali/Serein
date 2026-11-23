export type Horizon = { smokecast: number; fallback: number }

// One chart that morphs between horizons. Bars share a scale across every
// horizon so error visibly grows as the forecast reaches further ahead.
export function RmseBars({ current, all }: { current: Horizon; all: Horizon[] }) {
  const max = Math.max(...all.flatMap(h => [h.smokecast, h.fallback]))
  const rows = [
    { name: "SmokeCast", value: current.smokecast, fill: "bg-[var(--sage)]" },
    { name: "Fallback", value: current.fallback, fill: "bg-[#7c9e90]" },
  ]
  const gain = 1 - current.smokecast / current.fallback

  return (
    <figure className="mb-4 rounded-[.4rem] border border-[#88a79c60] p-[clamp(1.1rem,2.6vw,1.8rem)]">
      <div className="grid gap-3" aria-hidden="true">
        {rows.map(r => (
          <div key={r.name} className="grid grid-cols-[6.5rem_1fr_3.2rem] items-center gap-3 text-[.86rem]">
            <span className="text-[#d7e6d8]">{r.name}</span>
            <span className="h-[.7rem] overflow-hidden rounded-full bg-[#ffffff12]">
              <span
                className={"block h-full origin-left rounded-full motion-safe:transition-transform motion-safe:duration-500 motion-safe:ease-[cubic-bezier(.22,1,.36,1)] " + r.fill}
                style={{ transform: `scaleX(${r.value / max})` }}
              />
            </span>
            <span className="text-right tabular-nums text-[var(--paper)]">{r.value.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <figcaption className="mt-4 text-[.82rem] text-[#b9cbbf]" aria-live="polite">
        SmokeCast error is {Math.round(gain * 100)}% lower than the fallback at this horizon.
      </figcaption>
    </figure>
  )
}
