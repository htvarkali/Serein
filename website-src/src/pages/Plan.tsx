import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { aqiOf, loadWorld, localTime, nearestPoint, valueAt, type WorldData } from "@/lib/world"

const PLACES: Record<string, [number, number]> = {
  Seattle: [47.61, -122.33], Spokane: [47.66, -117.43], Portland: [45.52, -122.68], Bend: [44.06, -121.31],
  Boise: [43.62, -116.2], Medford: [42.33, -122.87], Sacramento: [38.58, -121.49], Fresno: [36.74, -119.79],
  "San Francisco": [37.77, -122.42], "Los Angeles": [34.05, -118.24], "Las Vegas": [36.17, -115.14], Reno: [39.53, -119.81],
}

type Audience = "worker" | "family"

function advice(peak: number, who: Audience) {
  if (who === "worker") {
    if (peak >= 225.5) return "Plan indoor or filtered work. California's rule requires respirators if the current AQI tops 500."
    if (peak >= 55.5) return "Plan for smoke: heavy work in the cleanest hours, extra rest breaks, N95s for every worker."
    if (peak >= 35.5) return "Smoke possible: N95s on site and a plan to move work or change hours."
    return "No smoke action expected. Check the current AQI at the start of each shift, as the rule requires."
  }
  if (peak >= 125.5) return "Keep everyone inside with windows closed and an air purifier on if you have one."
  if (peak >= 55.5) return "Move play and exercise indoors or to the cleanest hours. Keep inhalers close."
  if (peak >= 35.5) return "People with asthma, children and older adults should shorten time outside in the smokiest hours."
  return "Air looks fine for normal activities."
}

export default function Plan() {
  const [data, setData] = useState<WorldData | null>(null)
  const [place, setPlace] = useState("Fresno")
  const [who, setWho] = useState<Audience>("worker")
  useEffect(() => { loadWorld("live").then(setData) }, [])

  const days = useMemo(() => {
    if (!data) return []
    const [lat, lon] = PLACES[place]
    const p = nearestPoint(data, lon, lat)
    if (p < 0) return []
    const groups = new Map<string, { h: number; v: number }[]>()
    for (let h = 0; h < data.hours; h++) {
      const v = valueAt(data, "serein", p, h)
      if (v === null) continue
      const key = new Date(Date.parse(data.start_utc) + h * 3600e3).toLocaleDateString("en-US", { timeZone: "America/Los_Angeles", weekday: "long", month: "short", day: "numeric" })
      groups.set(key, [...(groups.get(key) ?? []), { h, v }])
    }
    return [...groups.entries()].filter(([, xs]) => xs.length >= 6).slice(0, 4).map(([day, xs]) => {
      const mean = xs.reduce((s, x) => s + x.v, 0) / xs.length
      const peak = xs.reduce((m, x) => (x.v > m.v ? x : m))
      const clean = xs.reduce((m, x) => (x.v < m.v ? x : m))
      return { day, mean, peak, clean, hours: xs.length }
    })
  }, [data, place])

  return (
    <div className="mx-auto max-w-6xl px-5 pt-16">
      <Badge variant="secondary">Live forecast</Badge>
      <h1 className="mt-4 text-6xl md:text-7xl">Plan your day</h1>
      <p className="mt-4 max-w-3xl text-lg text-muted-foreground">
        The next three days of smoke for a place, with the smokiest and cleanest hours and what to do about them.
        {data && ` Forecast issued ${data.issue_date}.`}
      </p>
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Select value={place} onValueChange={setPlace}>
          <SelectTrigger className="w-56" aria-label="Place"><SelectValue /></SelectTrigger>
          <SelectContent>{Object.keys(PLACES).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
        </Select>
        <ToggleGroup type="single" variant="outline" value={who} onValueChange={v => v && setWho(v as Audience)} aria-label="For whom">
          <ToggleGroupItem value="worker" className="px-4">Outdoor crew</ToggleGroupItem>
          <ToggleGroupItem value="family" className="px-4">Family</ToggleGroupItem>
        </ToggleGroup>
        <Button asChild variant="secondary"><Link to="/world">Pick any place on the map</Link></Button>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {days.map(d => {
          const a = aqiOf(d.peak.v)
          return (
            <Card key={d.day}>
              <CardHeader>
                <CardDescription>{d.day}</CardDescription>
                <CardTitle className="font-serif text-5xl font-normal">{Math.round(d.mean)} <span className="text-base text-muted-foreground">µg/m³ avg</span></CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="size-3 rounded-sm" style={{ background: `rgb(${a.rgb.join(",")})` }} />
                  Peak {Math.round(d.peak.v)} ({a.name}) around {data && localTime(data, d.peak.h).split(", ").pop()}
                </div>
                <div className="text-muted-foreground">Cleanest around {data && localTime(data, d.clean.h).split(", ").pop()} ({Math.round(d.clean.v)} µg/m³)</div>
                <div className="rounded-lg bg-secondary p-3">{advice(d.peak.v, who)}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      <p className="mt-6 max-w-3xl text-xs text-muted-foreground">
        Hour-by-hour shape from NOAA's air-quality model, scaled each day to Serein's tested daily forecast; the hourly
        detail itself has not been tested yet. Forecast squares are about 25 km. California's wildfire smoke rule
        (Title 8, §5141.1) applies to the current AQI, so this never replaces the check at the start of each shift. Not
        medical advice.
      </p>
    </div>
  )
}
