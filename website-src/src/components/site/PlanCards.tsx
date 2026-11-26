import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { ArrowRight, CalendarDays } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { aqiOf, loadWorld, nearestPoint, relativeDay, type WorldData } from "@/lib/world"

const PLACES: Record<string, [number, number]> = {
  "San Francisco": [37.77, -122.42], Seattle: [47.61, -122.33], Spokane: [47.66, -117.43],
  Portland: [45.52, -122.68], Bend: [44.06, -121.31], Boise: [43.62, -116.2],
  Medford: [42.33, -122.87], Sacramento: [38.58, -121.49], Fresno: [36.74, -119.79],
  "Los Angeles": [34.05, -118.24], "Las Vegas": [36.17, -115.14], Reno: [39.53, -119.81],
}

type Audience = "activity" | "family" | "worker"
type Dataset = "live" | "aug2023"
type Snapshot = { state: "loading" | "error" } | { state: "ready"; data: WorldData }
type DayPlan = { lead: number; date: string | null; median: number; low: number; high: number }

const planningNotes = {
  activity: {
    plan: "Line up an indoor or rescheduled option and decide when to update participants.",
    watch: "Keep an alternative available and check conditions again before committing.",
    check: "Keep your usual plan flexible and check current AQI before the activity.",
  },
  family: {
    plan: "Consider an indoor alternative and review your usual care plan.",
    watch: "Plan for a possible change to outdoor activities and check current conditions.",
    check: "Check current AQI before going out, especially if anyone is sensitive to smoke.",
  },
  worker: {
    plan: "Prepare a backup for outdoor work and review your workplace smoke procedures.",
    watch: "Consider what work could be adjusted and set a time for the next AQI check.",
    check: "Check current AQI and follow your workplace smoke procedures before the shift.",
  },
}

const dateLabel = (day: string) =>
  new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" })
    .format(new Date(day + "T12:00:00Z"))

const isNumber = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value)

function DailyCard({ day, audience }: { day: DayPlan; audience: Audience }) {
  const { lead, date, median, low, high } = day
  const aqi = aqiOf(median)
  const note = planningNotes[audience][median >= 35.5 ? "plan" : high >= 35.5 ? "watch" : "check"]
  // A reader thinks in "today" and "tomorrow"; the run thinks in days ahead. Show both.
  const leadLabel = lead === 0 ? "Issue day" : `Day ${lead} ahead`
  const when = date ? relativeDay(date) : null

  return (
    <Card className="h-full gap-4">
      <CardHeader className="px-4 sm:px-6">
        <h3 className="text-sm font-medium text-muted-foreground">
          {when ? <span className="text-foreground">{when}</span> : leadLabel}{date ? <> · <time dateTime={date}>{dateLabel(date)}</time></> : null}
          {when && <span className="block text-xs font-normal">{leadLabel}</span>}
        </h3>
        <p className="font-serif text-5xl font-normal tabular-nums">{median} <span className="font-sans text-base text-muted-foreground">µg/m³</span></p>
      </CardHeader>
      <CardContent className="space-y-3 px-4 text-sm sm:px-6">
        <p className="flex items-start gap-2 font-medium">
          <span aria-hidden="true" className="mt-1 size-3 shrink-0 rounded-full border border-foreground/20" style={{ background: `rgb(${aqi.rgb.join(",")})` }} />
          {aqi.name}
        </p>
        <p className="text-muted-foreground">Forecast range {low}–{high} µg/m³</p>
        <p className="rounded-lg bg-secondary p-3 leading-relaxed text-secondary-foreground">{note}</p>
      </CardContent>
    </Card>
  )
}

export function PlanCards() {
  const [snapshot, setSnapshot] = useState<Snapshot>({ state: "loading" })
  const [dataset, setDataset] = useState<Dataset>("live")
  const [attempt, setAttempt] = useState(0)
  const [place, setPlace] = useState("San Francisco")
  const [audience, setAudience] = useState<Audience>("activity")

  useEffect(() => {
    let active = true
    loadWorld(dataset).then(
      data => { if (active) setSnapshot({ state: "ready", data }) },
      () => { if (active) setSnapshot({ state: "error" }) },
    )
    return () => { active = false }
  }, [dataset, attempt])

  const data = snapshot.state === "ready" ? snapshot.data : null
  const days = useMemo(() => {
    if (!data?.daily) return []
    const [lat, lon] = PLACES[place]
    const point = nearestPoint(data, lon, lat)
    if (point < 0) return []
    return data.daily.flatMap(({ lead, date, q05, q50, q95 }): DayPlan[] => {
      const [low, median, high] = [q05[point], q50[point], q95[point]]
      return isNumber(low) && isNumber(median) && isNumber(high) ? [{ lead, date, median, low, high }] : []
    })
  }, [data, place])

  const issueDate = data?.issue_date
  const isStale = dataset === "live" && data !== null && Date.now() - Date.parse(data.start_utc) > 36 * 60 * 60 * 1000

  return (
    <div>
      <div className="rounded-xl border bg-card p-4 sm:p-6">
        <div className="grid items-end gap-4 lg:grid-cols-[minmax(0,1fr)_auto_auto]">
          <div className="min-w-0 space-y-1.5">
            <label htmlFor="outlook-place" className="text-sm font-medium">Location</label>
            <Select value={place} onValueChange={setPlace}>
              <SelectTrigger id="outlook-place" className="min-h-11 w-full bg-background"><SelectValue /></SelectTrigger>
              <SelectContent>{Object.keys(PLACES).map(name => <SelectItem key={name} value={name}>{name}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="min-w-0 space-y-1.5">
            <p id="outlook-audience" className="text-sm font-medium">Planning for</p>
            <ToggleGroup type="single" variant="outline" value={audience} onValueChange={value => value && setAudience(value as Audience)}
              aria-labelledby="outlook-audience" className="flex w-full flex-wrap gap-1">
              <ToggleGroupItem value="activity" className="min-h-11 px-3">An activity</ToggleGroupItem>
              <ToggleGroupItem value="family" className="min-h-11 px-3">A family</ToggleGroupItem>
              <ToggleGroupItem value="worker" className="min-h-11 px-3">An outdoor crew</ToggleGroupItem>
            </ToggleGroup>
          </div>
          <Button asChild variant="outline" size="lg" className="min-h-11 max-w-full justify-self-start">
            <Link to={dataset === "aug2023" ? "/world?mode=aug2023" : "/world"}>Explore the map <ArrowRight aria-hidden="true" /></Link>
          </Button>
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t pt-3">
          <p className="flex min-h-8 items-center gap-2 text-sm text-muted-foreground">
            <CalendarDays aria-hidden="true" className="size-4 shrink-0" />
            {issueDate
              ? <>{dataset === "aug2023" ? "Archived example issued " : "Latest available forecast issued "}<time dateTime={issueDate}>{issueDate}</time></>
              : dataset === "aug2023" ? "Archived example" : "Latest available forecast"}
          </p>
          <Button type="button" variant="link" className="min-h-11 px-0 underline" onClick={() => {
            setSnapshot({ state: "loading" })
            setDataset(dataset === "live" ? "aug2023" : "live")
          }}>
            {dataset === "live" ? "See a past smoke event" : "Show the latest outlook"}
          </Button>
        </div>
      </div>

      {isStale && <p className="mt-4 rounded-lg border bg-secondary p-4 text-sm text-secondary-foreground">
        This snapshot may be out of date. Check current conditions and advisories on{" "}
        <a href="https://www.airnow.gov/" className="font-medium underline underline-offset-4">AirNow</a>.
      </p>}

      {snapshot.state === "loading" && (
        <div className="mt-6 grid min-h-32 place-items-center rounded-xl border bg-card p-4 text-center text-muted-foreground" role="status">
          Loading the daily outlook…
        </div>
      )}
      {snapshot.state === "error" && (
        <div className="mt-6 space-y-3 rounded-xl border bg-card p-5">
          <p role="status">The daily outlook couldn’t load.</p>
          <Button type="button" variant="outline" onClick={() => {
            setSnapshot({ state: "loading" })
            setAttempt(value => value + 1)
          }}>Try again</Button>
        </div>
      )}
      {snapshot.state === "ready" && (
        days.length ? <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {days.map(day => <DailyCard day={day} audience={audience} key={day.lead} />)}
        </div> : <p className="mt-6 rounded-xl border bg-card p-5 text-muted-foreground" role="status">
          Daily estimates are unavailable for {place} in this snapshot. Choose another location or switch outlooks.
        </p>
      )}
      <p className="mt-5 max-w-3xl text-sm text-muted-foreground">
        These estimates are daily outdoor PM₂.₅ averages for the nearest forecast point. Check{" "}
        <a href="https://www.airnow.gov/" className="underline underline-offset-4">current AQI</a> and follow local or workplace guidance before making activity decisions.
      </p>
    </div>
  )
}
