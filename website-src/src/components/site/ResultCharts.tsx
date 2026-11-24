import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { equity, hiddenByDistance, rmseByLead, warnings } from "@/data/site"

const vsNoaa = { serein: { label: "SmokeCast", color: "var(--chart-1)" }, noaa: { label: "Reference forecast", color: "var(--chart-2)" } } satisfies ChartConfig
const vsEpa = { serein: { label: "SmokeCast", color: "var(--chart-1)" }, epa: { label: "AirNow", color: "var(--chart-2)" } } satisfies ChartConfig
const eq = { far25: { label: "25 km or more", color: "var(--chart-1)" }, far50: { label: "50 km or more", color: "var(--chart-2)" } } satisfies ChartConfig

type Row = Record<string, string | number>
type Column = { key: string; label: string; unit?: string }

function Bars({ data, axisColumn, series, config, unit, extraColumns = [], tickFormatter }: {
  data: Row[]
  axisColumn: Column
  series: string[]
  config: ChartConfig
  unit?: string
  extraColumns?: Column[]
  tickFormatter?: (value: string) => string
}) {
  const tableColumns = [
    ...series.map(key => ({ key, label: String(config[key].label), unit })),
    ...extraColumns,
  ]

  return (
    <>
      <ChartContainer config={config} className="h-64 w-full min-w-0 sm:h-72" aria-hidden="true">
        <BarChart data={data} accessibilityLayer={false} margin={{ top: 8, right: 4, bottom: 4, left: 0 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey={axisColumn.key} tickLine={false} axisLine={false} tickMargin={8} fontSize={11} tickFormatter={tickFormatter} />
          <YAxis tickLine={false} axisLine={false} unit={unit} width={36} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent className="flex-wrap gap-x-4 gap-y-2" />} />
          {series.map(key => <Bar key={key} dataKey={key} fill={`var(--color-${key})`} radius={[4, 4, 0, 0]} maxBarSize={56} isAnimationActive={false} />)}
        </BarChart>
      </ChartContainer>
      <details className="mt-3 border-t border-border">
        <summary className="min-h-11 cursor-pointer rounded-md py-3 text-sm font-medium text-primary focus-visible:ring-2 focus-visible:ring-ring">
          View exact values
        </summary>
        <div className="overflow-x-auto rounded-md border" tabIndex={0} role="region" aria-label="Chart values">
          <table className="w-full text-left text-sm tabular-nums">
            <thead className="bg-secondary text-secondary-foreground">
              <tr>
                <th scope="col" className="p-2 font-medium sm:px-3">{axisColumn.label}</th>
                {tableColumns.map(({ key, label }) => <th key={key} scope="col" className="p-2 text-right font-medium sm:px-3">{label}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.map(row => (
                <tr key={row[axisColumn.key]}>
                  <th scope="row" className="p-2 font-medium sm:px-3">{row[axisColumn.key]}</th>
                  {tableColumns.map(({ key, unit: suffix }) => <td key={key} className="p-2 text-right sm:px-3">{row[key]}{suffix}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  )
}

export const RmseChart = () => <Bars data={rmseByLead} axisColumn={{ key: "lead", label: "Forecast day" }} series={["serein", "noaa"]} config={vsNoaa} />
export const WarningsChart = () => <Bars data={warnings} axisColumn={{ key: "lead", label: "Lead time" }} series={["serein", "epa"]} config={vsEpa} unit="%"
  extraColumns={[{ key: "fSerein", label: "SmokeCast false alarms" }, { key: "fEpa", label: "AirNow false alarms" }]} />
export const HiddenChart = () => <Bars data={hiddenByDistance} axisColumn={{ key: "band", label: "Distance" }} series={["serein", "noaa"]} config={vsNoaa}
  extraColumns={[{ key: "sites", label: "Sites" }]} />
export const EquityChart = () => <Bars data={equity} axisColumn={{ key: "quintile", label: "Income quintile" }} series={["far25", "far50"]} config={eq} unit="%"
  tickFormatter={value => value.replace(" income", "")} />
