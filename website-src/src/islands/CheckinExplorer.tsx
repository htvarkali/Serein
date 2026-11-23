import { useState } from "react"
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { Slider } from "@/components/ui/slider"
import { checkins } from "@/data/results"

const KINDS = {
  very_sensitive: { label: "Very sensitive child", color: "#be773e" },
  typical: { label: "Typical child", color: "#18322d" },
  not_sensitive: { label: "Less sensitive child", color: "#7c9e90" },
} as const
type Kind = keyof typeof KINDS

const config = Object.fromEntries(
  Object.entries(KINDS).map(([k, v]) => [k, { label: v.label, color: v.color }]),
) satisfies ChartConfig

const STEPS = [...new Set(checkins.map(r => r.k))].sort((a, b) => a - b)
const data = STEPS.map(k => {
  const point: Record<string, number> = { k }
  for (const r of checkins.filter(r => r.k === k)) point[r.kind] = +(100 * r.gain).toFixed(1)
  return point
})

export function CheckinExplorer() {
  const [step, setStep] = useState(STEPS.indexOf(30))
  const k = STEPS[step]
  const point = data[step]

  return (
    <div className="grid gap-5 rounded-[.45rem] border border-[var(--border)] bg-[var(--paper)] p-[clamp(1.1rem,3vw,2rem)] shadow-[0_18px_40px_#162d2812]">
      <div>
        <p className="eyebrow">Drag to add check-in days</p>
        <p className="mt-2 font-[family-name:var(--serif)] text-[clamp(2rem,3.8vw,3.3rem)] leading-[.95]" aria-live="polite">
          After {k} check-in {k === 1 ? "day" : "days"}
        </p>
      </div>

      <Slider
        value={[step]}
        min={0}
        max={STEPS.length - 1}
        step={1}
        onValueChange={([v]) => setStep(v)}
        aria-label="Check-in days"
        className="py-2 [&_[data-slot=slider-range]]:bg-[var(--grove)] [&_[data-slot=slider-thumb]]:size-5 [&_[data-slot=slider-thumb]]:cursor-grab [&_[data-slot=slider-thumb]]:border-[var(--grove)] [&_[data-slot=slider-thumb]]:bg-[var(--paper)] [&_[data-slot=slider-track]]:bg-[#d6dece]"
      />

      <dl className="grid grid-cols-3 gap-3">
        {(Object.keys(KINDS) as Kind[]).map(kind => (
          <div key={kind} className="flex flex-col justify-between gap-1 border-t border-[#bec9b7] pt-3">
            <dt className="flex items-center gap-2 text-[.8rem]">
              <span className="size-2.5 shrink-0 rounded-full" style={{ background: KINDS[kind].color }} />
              {KINDS[kind].label}
            </dt>
            <dd className="mt-1 font-[family-name:var(--serif)] text-[clamp(1.8rem,3.3vw,3rem)] leading-none tabular-nums">
              {point[kind] > 0 ? "+" : ""}{point[kind].toFixed(1)}%
            </dd>
          </div>
        ))}
      </dl>

      <ChartContainer config={config} className="aspect-auto h-[15rem] w-full [&_.recharts-cartesian-axis-tick_text]:fill-[var(--muted)] [&_.recharts-cartesian-grid_line]:stroke-[#162d2814]">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="k" type="number" domain={[0, 100]} ticks={STEPS} tickLine={false} axisLine={false} tickMargin={8} />
          <YAxis tickLine={false} axisLine={false} width={40} unit="%" />
          <ReferenceLine x={k} stroke="#be773e" strokeDasharray="4 4" />
          <ChartTooltip content={<ChartTooltipContent labelFormatter={(_, p) => `${p?.[0]?.payload?.k} check-in days`} />} />
          {(Object.keys(KINDS) as Kind[]).map(kind => (
            <Line key={kind} dataKey={kind} stroke={KINDS[kind].color} strokeWidth={2.5} dot={{ r: 3, fill: KINDS[kind].color, strokeWidth: 0 }} isAnimationActive={false} />
          ))}
        </LineChart>
      </ChartContainer>

      <p className="text-[.8rem] text-[var(--muted)]">
        Improvement in Brier score over the group-only estimate, averaged across 300 simulated children. Higher is better.
        Simulated data only; real families have not been tested.
      </p>
    </div>
  )
}
