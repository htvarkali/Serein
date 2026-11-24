import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { SOURCE_DEV, equity, headline, hiddenByDistance, rmseByLead, warnings } from "@/data/site"

const vsNoaa = { serein: { label: "Serein", color: "var(--chart-1)" }, noaa: { label: "NOAA best", color: "var(--chart-2)" } } satisfies ChartConfig
const vsEpa = { serein: { label: "Serein", color: "var(--chart-1)" }, epa: { label: "EPA official", color: "var(--chart-2)" } } satisfies ChartConfig
const eq = { far25: { label: "25+ km from a monitor", color: "var(--chart-1)" }, far50: { label: "50+ km", color: "var(--chart-3)" } } satisfies ChartConfig

function ChartCard({ title, desc, children, note }: { title: string; desc: string; children: React.ReactNode; note?: string }) {
  return (
    <Card>
      <CardHeader><CardTitle className="text-xl">{title}</CardTitle><CardDescription>{desc}</CardDescription></CardHeader>
      <CardContent>{children}{note && <p className="mt-3 text-xs text-muted-foreground">{note}</p>}</CardContent>
    </Card>
  )
}

export default function Results() {
  return (
    <div className="mx-auto max-w-6xl px-5 pt-16">
      <Badge variant="secondary">Evidence</Badge>
      <h1 className="mt-4 text-6xl md:text-7xl">Does it work?</h1>
      <p className="mt-4 max-w-3xl text-lg text-muted-foreground">
        Serein was trained on the 2021-22 fire seasons and scored on 2023 weeks it never trained on, against NOAA's best
        forecast and EPA's official AQI forecast on the same places and days. The 2024-25 seasons are locked for a
        one-time final test under rules written down in advance.
      </p>
      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        <ChartCard title="Typical forecast error" desc="RMSE in µg/m³, lower is better">
          <ChartContainer config={vsNoaa} className="h-72 w-full">
            <BarChart data={rmseByLead}><CartesianGrid vertical={false} /><XAxis dataKey="lead" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} /><ChartTooltip content={<ChartTooltipContent />} /><ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="serein" fill="var(--color-serein)" radius={6} /><Bar dataKey="noaa" fill="var(--color-noaa)" radius={6} /></BarChart>
          </ChartContainer>
        </ChartCard>
        <ChartCard title="Unhealthy days warned ahead" desc="% of reporting-area days that reached unhealthy for sensitive groups"
          note={`False alarms, 1 day ahead: Serein ${headline.falseSerein}, EPA ${headline.falseEpa}. 2 days ahead: Serein 48, EPA 36 (a real tradeoff).`}>
          <ChartContainer config={vsEpa} className="h-72 w-full">
            <BarChart data={warnings}><CartesianGrid vertical={false} /><XAxis dataKey="lead" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} unit="%" /><ChartTooltip content={<ChartTooltipContent />} /><ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="serein" fill="var(--color-serein)" radius={6} /><Bar dataKey="epa" fill="var(--color-epa)" radius={6} /></BarChart>
          </ChartContainer>
        </ChartCard>
        <ChartCard title="Where there is no monitor" desc="Error at monitors hidden from Serein, by distance to the nearest monitor it could see (next day)"
          note="Same 20% of monitors hidden in every run (fixed seed). The 60+ km band has only 3 sites and is not shown.">
          <ChartContainer config={vsNoaa} className="h-72 w-full">
            <BarChart data={hiddenByDistance}><CartesianGrid vertical={false} /><XAxis dataKey="band" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} /><ChartTooltip content={<ChartTooltipContent />} /><ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="serein" fill="var(--color-serein)" radius={6} /><Bar dataKey="noaa" fill="var(--color-noaa)" radius={6} /></BarChart>
          </ChartContainer>
        </ChartCard>
        <ChartCard title="Who lives far from a monitor" desc="Share of people living far from any EPA monitor, by neighborhood income (6 western states, 56 million people)"
          note="ACS 2019-2023 tract income and population; 425 EPA monitors. Most of the far residents are rural.">
          <ChartContainer config={eq} className="h-72 w-full">
            <BarChart data={equity}><CartesianGrid vertical={false} /><XAxis dataKey="quintile" tickLine={false} axisLine={false} fontSize={11} />
              <YAxis tickLine={false} axisLine={false} unit="%" /><ChartTooltip content={<ChartTooltipContent />} /><ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="far25" fill="var(--color-far25)" radius={6} /><Bar dataKey="far50" fill="var(--color-far50)" radius={6} /></BarChart>
          </ChartContainer>
        </ChartCard>
      </div>
      <Card className="mt-4">
        <CardHeader><CardTitle className="text-xl">What we tried that did not work</CardTitle></CardHeader>
        <CardContent className="text-muted-foreground">
          Nine attempts to make the forecast more accurate failed our pre-registered test, and we report them: bigger models,
          more seasons, extra fire and satellite inputs, and five ways of blending forecasters. What did pass: warning
          probabilities recalibrated so that "60%" really means about 60%, and a low-confidence flag that marks the days
          with the largest misses. Every try is in the project's experiment log on GitHub.
        </CardContent>
      </Card>
      <p className="mt-4 text-xs text-muted-foreground">{SOURCE_DEV}</p>
    </div>
  )
}
