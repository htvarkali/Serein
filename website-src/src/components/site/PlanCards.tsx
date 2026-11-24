import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { aqiOf, loadWorld, nearestPoint, type WorldData } from "@/lib/world"

const PLACES: Record<string, [number, number]> = {
  Seattle: [47.61, -122.33], Spokane: [47.66, -117.43], Portland: [45.52, -122.68], Bend: [44.06, -121.31],
  Boise: [43.62, -116.2], Medford: [42.33, -122.87], Sacramento: [38.58, -121.49], Fresno: [36.74, -119.79],
  "San Francisco": [37.77, -122.42], "Los Angeles": [34.05, -118.24], "Las Vegas": [36.17, -115.14], Reno: [39.53, -119.81],
}

type Audience = "worker" | "family"

// Advice from the tested daily forecast: the median and the top of the 90% range.
// No hour-specific advice: the hour-to-hour pattern did not prove reliable (docs/HOURLY_ACCURACY.md).
function advice(median: number, high: number, who: Audience) {
  if (who === "worker") {
    if (median >= 225.5) return "Plan indoor or filtered work. California's rule requires respirators if the current AQI tops 500."
    if (median >= 55.5) return "Plan for smoke: lighter outdoor work, extra rest breaks and N95s for every worker."
    if (high >= 55.5 || median >= 35.5) return "Smoke possible: N95s on site and a plan to move work or change hours if the current AQI rises."
    return "No smoke action expected. Check the current AQI at the start of each shift, as the rule requires."
  }
  if (median >= 125.5) return "Keep everyone inside with windows closed and an air purifier on if you have one."
  if (median >= 55.5) return "Move play and exercise indoors. People with asthma should keep inhalers close."
  if (high >= 35.5 || median >= 35.5) return "People with asthma, children and older adults should watch the current AQI and cut back time outside if it rises."
  return "Air looks fine for normal activities."
}

export function PlanCards() {
  const [data, setData] = useState<WorldData | null>(null)
  const [place, setPlace] = useState("Fresno")
  const [who, setWho] = useState<Audience>("worker")
  useEffect(() => { loadWorld("live").then(setData) }, [])

  const days = useMemo(() => {
    if (!data?.daily) return []
    const [lat, lon] = PLACES[place]
    const p = nearestPoint(data, lon, lat)
    if (p < 0) return []
    return data.daily.flatMap(d => {
      const q50 = d.q50[p], q05 = d.q05[p], q95 = d.q95[p]
      if (q50 === null || q05 === null || q95 === null) return []
      const label = d.date
        ? new Date(d.date + "T12:00:00Z").toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric", timeZone: "UTC" })
        : `Day ${d.lead}`
      return [{ label, q05, q50, q95 }]
    })
  }, [data, place])

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <Select value={place} onValueChange={setPlace}>
          <SelectTrigger className="w-56 bg-card" aria-label="Place"><SelectValue /></SelectTrigger>
          <SelectContent>{Object.keys(PLACES).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
        </Select>
        <ToggleGroup type="single" variant="outline" value={who} onValueChange={v => v && setWho(v as Audience)} aria-label="For whom">
          <ToggleGroupItem value="worker" className="px-4">Outdoor crew</ToggleGroupItem>
          <ToggleGroupItem value="family" className="px-4">Family</ToggleGroupItem>
        </ToggleGroup>
        <Button asChild variant="outline"><Link to="/world">Pick any place on the map</Link></Button>
        {data && <span className="text-sm text-muted-foreground">Live forecast issued {data.issue_date}</span>}
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {days.map(d => {
          const a = aqiOf(d.q50)
          return (
            <Card key={d.label}>
              <CardHeader>
                <CardDescription>{d.label}</CardDescription>
                <CardTitle className="font-serif text-5xl font-normal">{d.q50} <span className="text-base text-muted-foreground">µg/m³</span></CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="size-3 rounded-sm" style={{ background: `rgb(${a.rgb.join(",")})` }} />
                  {a.name} (daily average)
                </div>
                <div className="text-muted-foreground">Likely between {d.q05} and {d.q95} µg/m³ (90% range)</div>
                <div className="rounded-lg bg-secondary p-3">{advice(d.q50, d.q95, who)}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      <p className="mt-6 max-w-3xl text-xs text-muted-foreground">
        SmokeCast's tested daily forecast for the nearest forecast point (about 25 km squares). We tested whether the
        hour-to-hour pattern can tell which hours will be worst, and it could not, so this gives no hour-specific advice.
        California's wildfire smoke rule (Title 8, §5141.1) applies to the current AQI, so this never replaces the check at
        the start of each shift. Not medical advice.
      </p>
    </div>
  )
}
