import { useMemo, useState } from "react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { metrics, type MetricRow } from "@/data/results"
import { chip } from "./chip"

const MODELS = {
  smokecast: { label: "SmokeCast", color: "#c4e2b9" },
  noaa_best: { label: "NOAA fallback", color: "#f2ba84" },
  hrrr_smoke: { label: "HRRR-Smoke", color: "#8db7dc" },
  persistence: { label: "Yesterday's reading", color: "#c9a9e0" },
  gbm: { label: "Simpler ML model", color: "#7fb3a4" },
  smokecast_nograph: { label: "SmokeCast, no neighbors", color: "#e6dd9a" },
  climatology: { label: "Typical for the date", color: "#9aa59f" },
} as const
type Model = keyof typeof MODELS

const SUBSETS = {
  all: "All days",
  smoke_yesterday: "Smoky the day before",
  heavy_smoke_yesterday: "Heavy smoke the day before",
} as const
type Subset = keyof typeof SUBSETS

const MEASURES = {
  rmse: { label: "Forecast error", unit: "RMSE, µg/m³", better: "Lower is better.", scale: 1, digits: 2 },
  mae: { label: "Typical miss", unit: "MAE, µg/m³", better: "Lower is better.", scale: 1, digits: 2 },
  usg_pod: { label: "Unhealthy days caught", unit: "% of unhealthy-for-sensitive-groups days forecast", better: "Higher is better.", scale: 100, digits: 0 },
} as const
type Measure = keyof typeof MEASURES

const LEADS = ["Same day", "1 day ahead", "2 days ahead", "3 days ahead"]

const config = Object.fromEntries(
  Object.entries(MODELS).map(([key, m]) => [key, { label: m.label, color: m.color }]),
) satisfies ChartConfig

export function ForecastExplorer() {
  const [subset, setSubset] = useState<Subset>("all")
  const [measure, setMeasure] = useState<Measure>("rmse")
  const [shown, setShown] = useState<Model[]>(["smokecast", "noaa_best", "hrrr_smoke", "persistence"])
  const m = MEASURES[measure]

  const data = useMemo(() => {
    const rows = metrics.filter(r => r.subset === subset)
    return LEADS.map((label, lead) => {
      const point: Record<string, string | number | null> = { lead: label }
      for (const model of Object.keys(MODELS) as Model[]) {
        const row: MetricRow | undefined = rows.find(r => r.lead === lead && r.model === model)
        const v = row?.[measure]
        point[model] = v == null ? null : +(v * m.scale).toFixed(m.digits)
      }
      return point
    })
  }, [subset, measure, m])

  const days = metrics.find(r => r.subset === subset && r.model === "smokecast" && r.lead === 1)?.n ?? 0
  const sc = data[1].smokecast as number
  const nf = data[1].noaa_best as number
  const pct = measure === "usg_pod" ? "%" : ""

  return (
    <div className="grid gap-5 rounded-[.4rem] border border-[#88a79c60] bg-[#18332e] p-[clamp(1.1rem,3vw,2.2rem)]">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Explore the results</p>
          <h3 className="mt-2 font-[family-name:var(--serif)] text-[clamp(1.6rem,3vw,2.6rem)] leading-none text-[var(--sage)]">
            {m.label}, {SUBSETS[subset].toLowerCase()}
          </h3>
        </div>
        <p className="max-w-[26rem] text-[.86rem] text-[#b9cbbf]" aria-live="polite">
          One day ahead: SmokeCast {sc}{pct} vs. NOAA fallback {nf}{pct}. {m.better}
        </p>
      </div>

      <div className="grid gap-3">
        <ToggleGroup type="single" value={subset} onValueChange={v => v && setSubset(v as Subset)} spacing={2} aria-label="Which days" className="flex-wrap">
          {Object.entries(SUBSETS).map(([key, label]) => (
            <ToggleGroupItem key={key} value={key} className={chip("dark")}>{label}</ToggleGroupItem>
          ))}
        </ToggleGroup>
        <ToggleGroup type="single" value={measure} onValueChange={v => v && setMeasure(v as Measure)} spacing={2} aria-label="Measure" className="flex-wrap">
          {Object.entries(MEASURES).map(([key, x]) => (
            <ToggleGroupItem key={key} value={key} className={chip("dark")}>{x.label}</ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <ChartContainer config={config} className="aspect-auto h-[clamp(16rem,38vw,24rem)] w-full text-[#d7e6d8] [&_.recharts-cartesian-axis-tick_text]:fill-[#b9cbbf] [&_.recharts-cartesian-grid_line]:stroke-[#ffffff1a]">
        <LineChart data={data} margin={{ top: 12, right: 18, bottom: 4, left: 0 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="lead" tickLine={false} axisLine={false} tickMargin={10} />
          <YAxis tickLine={false} axisLine={false} width={44} domain={[0, "auto"]} />
          <ChartTooltip cursor={{ stroke: "#ffffff40" }} content={<ChartTooltipContent className="border-[var(--border)] bg-[var(--paper)] text-[var(--ink)]" />} />
          {shown.map(model => (
            <Line
              key={model + subset + measure}
              dataKey={model}
              stroke={MODELS[model].color}
              strokeWidth={model === "smokecast" ? 3.5 : 2}
              strokeDasharray={model === "climatology" ? "5 5" : undefined}
              dot={{ r: model === "smokecast" ? 5 : 3.5, fill: MODELS[model].color, strokeWidth: 0 }}
              activeDot={{ r: 7 }}
              connectNulls
              animationDuration={700}
            />
          ))}
        </LineChart>
      </ChartContainer>

      <ToggleGroup type="multiple" value={shown} onValueChange={v => v.length && setShown(v as Model[])} spacing={2} aria-label="Models shown" className="flex-wrap">
        {(Object.keys(MODELS) as Model[]).map(model => (
          <ToggleGroupItem key={model} value={model} className={chip("dark") + " gap-2 font-medium data-[state=on]:bg-[#ffffff14] data-[state=on]:text-[var(--paper)] data-[state=on]:border-[#ffffff40]! data-[state=off]:opacity-55"}>
            <span className="size-2.5 rounded-full" style={{ background: MODELS[model].color }} />
            {MODELS[model].label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      <p className="text-[.8rem] text-[#b9cbbf]">
        {m.unit}. Historical development results on held-out weeks of 2023, {days.toLocaleString()} monitor-days one day ahead. Tap a model to show or hide it.
        The NOAA fallback uses AQM first, then HRRR, then the previous day's measurement. HRRR-Smoke has no scored 2- or 3-day forecasts in these results.
      </p>
    </div>
  )
}
