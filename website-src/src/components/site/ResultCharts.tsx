import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { equity, hiddenByDistance, rmseByLead, warnings } from "@/data/site"

const vsNoaa = { serein: { label: "Serein", color: "var(--chart-1)" }, noaa: { label: "NOAA best", color: "var(--chart-2)" } } satisfies ChartConfig
const vsEpa = { serein: { label: "Serein", color: "var(--chart-1)" }, epa: { label: "EPA official", color: "var(--chart-2)" } } satisfies ChartConfig
const eq = { far25: { label: "25+ km from a monitor", color: "var(--chart-1)" }, far50: { label: "50+ km", color: "var(--chart-3)" } } satisfies ChartConfig

type Row = Record<string, string | number>
function Bars({ data, x, keys, config, unit, small }: { data: Row[]; x: string; keys: string[]; config: ChartConfig; unit?: string; small?: boolean }) {
  return (
    <ChartContainer config={config} className="h-72 w-full">
      <BarChart data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey={x} tickLine={false} axisLine={false} fontSize={small ? 11 : 12} />
        <YAxis tickLine={false} axisLine={false} unit={unit} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        {keys.map(k => <Bar key={k} dataKey={k} fill={`var(--color-${k})`} radius={4} />)}
      </BarChart>
    </ChartContainer>
  )
}

export const RmseChart = () => <Bars data={rmseByLead} x="lead" keys={["serein", "noaa"]} config={vsNoaa} />
export const WarningsChart = () => <Bars data={warnings} x="lead" keys={["serein", "epa"]} config={vsEpa} unit="%" />
export const HiddenChart = () => <Bars data={hiddenByDistance} x="band" keys={["serein", "noaa"]} config={vsNoaa} />
export const EquityChart = () => <Bars data={equity} x="quintile" keys={["far25", "far50"]} config={eq} unit="%" small />
