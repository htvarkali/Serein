import { useCallback, useEffect, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ArrowLeft, Info, Pause, Play } from "lucide-react"
import { Area, ComposedChart, Line, ReferenceLine, XAxis, YAxis } from "recharts"
import ForecastMap from "@/components/site/ForecastMap"
import { PersonPanel } from "@/components/site/PersonPanel"
import { Wordmark } from "@/components/site/SiteLayout"
import { Button } from "@/components/ui/button"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { Switch } from "@/components/ui/switch"
import { AQI, chanceLabel, loadPeople, loadPlaces, loadWorld, localTime, nearestPoint, outlookExtras, peopleUnderSmoke, placesUnderSmoke, relativeDay, valueAt,
  type People, type Places, type Which, type WorldData } from "@/lib/world"

const PLACES = {
  seattle: { name: "Seattle area", coordinates: [-122.32, 47.60] },
  portland: { name: "Portland area", coordinates: [-122.69, 45.52] },
  sacramento: { name: "Sacramento area", coordinates: [-121.49, 38.57] },
  eastBay: { name: "East Bay", coordinates: [-122.17, 37.74] },
} satisfies Record<string, { name: string; coordinates: [number, number] }>
type Place = keyof typeof PLACES
type Coordinates = [number, number]
type Mode = "live" | "aug2023"
const LEADS = ["Issue day", "Day 1", "Day 2", "Day 3"]
const COLORS = ["≤ 9.0", "9.1–35.4", "35.5–55.4", "55.5–125.4", "125.5–225.4", "> 225.4"]
const selectClass = "min-h-11 w-full rounded-lg border bg-card px-3 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary [color-scheme:dark]"
const shortDate = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", month: "short", day: "numeric" })
const issueDate = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", month: "short", day: "numeric", year: "numeric" })
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 })
const chartConfig = {
  serein: { label: "Serein-scaled", color: "var(--chart-1)" },
  noaa: { label: "NOAA", color: "var(--chart-2)" },
} satisfies ChartConfig

type ForecastState = { mode: Mode; attempt: number; data?: WorldData; failed?: boolean }

function ForecastDetails({ data, picked, label, which, hour }: {
  data: WorldData; picked: number; label: string; which: Which; hour: number;
}) {
  const [showHourly, setShowHourly] = useState(false)
  const [lat, lng, kind] = data.points[picked]
  const days = data.daily ?? []
  const selected = valueAt(data, which, picked, hour)
  const series = useMemo(() => showHourly ? Array.from({ length: data.hours }, (_, h) => ({
    h, label: localTime(data, h), serein: valueAt(data, "serein", picked, h), noaa: valueAt(data, "noaa", picked, h),
  })) : [], [data, picked, showHourly])

  return <>
    <h2 className="text-3xl">{label}</h2>
    <p className="mt-1 text-sm text-muted-foreground">
      {kind === 1 ? "Forecast at an EPA monitor" : "Forecast grid point, about 25 km apart"} · {lat.toFixed(2)}°, {lng.toFixed(2)}°
    </p>
    <h3 className="mt-6 font-semibold">SmokeCast daily outlook</h3>
    <p className="mt-1 text-sm text-muted-foreground">Daily average PM₂.₅ and 90% forecast range, in µg/m³.</p>
    {days.length ? (
      <div className="mt-3 grid grid-cols-2 gap-2">
        {days.map(day => {
          const date = new Date(`${day.date}T00:00:00Z`)
          const median = day.q50[picked], low = day.q05[picked], high = day.q95[picked]
          const { chance, warned, lowConfidence } = outlookExtras(day, picked)
          return <div key={day.lead} className="rounded-xl border bg-background/55 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              {(day.date ? relativeDay(day.date) : null) ?? LEADS[day.lead] ?? `Day ${day.lead}`}
              {Number.isFinite(date.getTime()) ? ` · ${shortDate.format(date)}` : ""}
            </p>
            <p className="mt-2 font-serif text-3xl leading-none">{median ?? <span className="font-sans text-sm">No data</span>}</p>
            {typeof low === "number" && typeof high === "number" && <p className="mt-1 text-xs text-muted-foreground">Range {low}–{high}</p>}
            {chance !== null && <p className="mt-1 text-xs"><span className="font-medium">{chanceLabel(chance)}</span> <span className="text-muted-foreground">chance of USG</span></p>}
            {warned && <p className="mt-1.5 w-fit rounded-full bg-[#f0883e]/25 px-2 py-0.5 text-xs font-medium">Smoke warning</p>}
            {lowConfidence && <p className="mt-1.5 w-fit rounded-full border px-2 py-0.5 text-xs">Less certain</p>}
          </div>
        })}
      </div>
    ) : <p className="mt-3 text-sm text-muted-foreground">Daily outlook unavailable for this run.</p>}
    {days.some(day => day.p_usg || day.warn) && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
      USG: a daily average of 35.5 µg/m³ or more (AQI 101, “Unhealthy for Sensitive Groups”). Chances are
      calibrated on past forecasts; the warning is the rule we score against EPA’s forecast. Development results.
    </p>}

    <details className="mt-6 rounded-xl border bg-background/40" onToggle={event => setShowHourly(event.currentTarget.open)}>
      <summary className="cursor-pointer rounded-xl px-4 py-3 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-primary">Explore hourly estimates</summary>
      <div className="space-y-3 px-4 pb-4 text-sm">
        <p className="text-muted-foreground">{localTime(data, hour)} · {which === "serein" ? "Serein-scaled NOAA pattern" : "NOAA forecast"}</p>
        <p className="font-serif text-3xl leading-none">{selected === null ? "No hourly value" : `${selected} µg/m³`}</p>
        {showHourly && <ChartContainer config={chartConfig} className="h-40 w-full">
          <ComposedChart data={series} margin={{ left: -24, right: 4, top: 6 }}>
            <XAxis dataKey="h" tickFormatter={h => `+${h}h`} ticks={[0, 24, 48].filter(h => h < data.hours)} tickLine={false} axisLine={false} fontSize={11} />
            <YAxis tickLine={false} axisLine={false} fontSize={11} />
            <ReferenceLine x={hour} stroke="var(--foreground)" />
            <Area dataKey="serein" type="linear" fill="var(--color-serein)" fillOpacity={0.16} stroke="var(--color-serein)" strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="noaa" type="linear" stroke="var(--color-noaa)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
            <ChartTooltip content={<ChartTooltipContent labelFormatter={(_, payload) => (payload?.[0]?.payload as { label?: string } | undefined)?.label} />} />
          </ComposedChart>
        </ChartContainer>}
        <p className="text-xs text-muted-foreground">Hourly concentrations are illustrative. The daily outlook is the evaluated planning forecast.</p>
      </div>
    </details>
    <PersonPanel data={data} point={picked} which={which} />
  </>
}

export default function World() {
  const [search, setSearch] = useSearchParams()
  const mode: Mode = search.get("mode") === "aug2023" ? "aug2023" : "live"
  const [which, setWhich] = useState<Which>("serein")
  const [hour, setHour] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState("900")
  const [result, setResult] = useState<ForecastState | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [place, setPlace] = useState<Place | Coordinates>("seattle")
  const [focus, setFocus] = useState<Coordinates | null>(null)
  const [people, setPeople] = useState<People | null>(null)
  const [places, setPlaces] = useState<Places | null>(null)
  const [peopleFailed, setPeopleFailed] = useState(false)
  const [showPeople, setShowPeople] = useState(false)
  const [farOnly, setFarOnly] = useState(false)

  const active = result?.mode === mode && result.attempt === attempt ? result : null
  const data = active?.data ?? null
  const selectedHour = Math.min(hour, (data?.hours ?? 1) - 1)
  const coords = typeof place === "string" ? PLACES[place].coordinates : place
  const placeName = typeof place === "string" ? PLACES[place].name : "Selected location"
  const picked = useMemo(() => data ? nearestPoint(data, coords[0], coords[1]) : -1, [data, coords])
  const mapPoint = useMemo<Coordinates | null>(() => {
    if (!data || picked < 0) return null
    const [lat, lng] = data.points[picked]
    return [lng, lat]
  }, [data, picked])
  const counts = useMemo(() => data && people && showPeople ? peopleUnderSmoke(data, which, selectedHour, people) : null,
    [data, people, showPeople, which, selectedHour])
  const placeCounts = useMemo(() => data && places && showPeople && places.schools.length + places.hospitals.length > 0
    ? placesUnderSmoke(data, which, selectedHour, places) : null, [data, places, showPeople, which, selectedHour])
  const start = data ? Date.parse(data.start_utc) : 0
  const expired = mode === "live" && data && Date.now() >= start + data.hours * 3_600_000
  const stale = mode === "live" && data && Date.now() - start >= 36 * 3_600_000
  const issued = data ? issueDate.format(new Date(start)) : ""
  const time = data ? localTime(data, selectedHour) : ""

  useEffect(() => { window.scrollTo({ top: 0, behavior: "instant" }) }, [])

  useEffect(() => {
    let cancelled = false
    loadWorld(mode).then(loaded => {
      if (!cancelled) setResult({ mode, attempt, data: loaded })
    }).catch(() => {
      if (!cancelled) setResult({ mode, attempt, failed: true })
    })
    return () => { cancelled = true }
  }, [mode, attempt])

  useEffect(() => {
    if (!playing || !data) return
    const timer = window.setInterval(() => {
      if (!document.hidden) setHour(value => (value + 1) % data.hours)
    }, Number(speed))
    return () => window.clearInterval(timer)
  }, [playing, speed, data])

  const pickMapLocation = useCallback((lng: number, lat: number) => { setPlace([lng, lat]); setFocus(null) }, [])

  function changeMode(next: Mode) {
    setPlaying(false)
    setHour(0)
    setSearch(next === "aug2023" ? { mode: "aug2023" } : {})
  }

  function togglePeople(enabled: boolean) {
    setShowPeople(enabled)
    if (!enabled || people) return
    setPeopleFailed(false)
    loadPeople().then(setPeople).catch(() => setPeopleFailed(true))
    // Schools and hospitals are optional: without the file the counts simply do not show.
    loadPlaces().then(setPlaces).catch(() => undefined)
  }

  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <a href="#map-main" onClick={event => {
        event.preventDefault()
        const main = document.getElementById("map-main")
        main?.focus()
        main?.scrollIntoView({ block: "start" })
      }} className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-card focus:px-4 focus:py-3">Skip to content</a>
      <header className="border-b border-white/10 bg-deep/60">
        <div className="mx-auto flex max-w-[91rem] items-center justify-between gap-4 px-4 py-4 sm:px-7">
          <Wordmark className="text-3xl text-primary" />
          <Button asChild variant="ghost"><Link to="/"><ArrowLeft aria-hidden="true" /> Back to site</Link></Button>
        </div>
      </header>

      <main id="map-main" tabIndex={-1} className="mx-auto max-w-[91rem] px-4 py-7 focus:outline-none sm:px-7 lg:py-10">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className="text-5xl sm:text-6xl">Forecast explorer</h1>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">Choose a place to compare four daily SmokeCast outlooks and explore the hourly map.</p>
          </div>
          <label className="grid w-full max-w-xs gap-1.5 text-sm font-medium">
            Forecast run
            <select className={selectClass} value={mode} onChange={event => changeMode(event.target.value as Mode)}>
              <option value="live">Latest published forecast</option>
              <option value="aug2023">August 2023: Pacific Northwest</option>
            </select>
          </label>
        </div>

        {data && <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-primary/25 bg-primary/7 px-4 py-3 text-sm" role="status">
          <span className="font-semibold text-primary">{mode === "aug2023" ? "Archived example" : expired ? "Forecast period ended" : stale ? "Older forecast" : "Latest published run"}</span>
          <span className="text-muted-foreground">Issued {issued}{expired || stale ? " · Check current conditions on AirNow." : ""}</span>
          {(expired || stale) && <a className="text-primary underline underline-offset-4" href="https://www.airnow.gov/">Open AirNow</a>}
        </div>}
        {active?.failed && <div className="mb-4 rounded-lg border border-[#f2ba84]/35 bg-[#f2ba84]/8 p-4 text-sm">
          <p role="alert">The forecast file couldn’t load. Try again or choose an archived example.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setAttempt(value => value + 1)}>Retry forecast</Button>
            {mode === "live" && <Button variant="secondary" onClick={() => changeMode("aug2023")}>Open archived example</Button>}
          </div>
        </div>}

        <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(19rem,23rem)]">
          <aside className="min-w-0 rounded-2xl border bg-card p-4 sm:p-5 lg:col-start-2 lg:row-start-1" aria-label="Location forecast">
            <label className="mb-5 grid gap-1.5 text-sm font-medium">
              Location
              <select className={selectClass} value={typeof place === "string" ? place : "map"} onChange={event => {
                const next = event.target.value as Place
                setPlace(next)
                setFocus(PLACES[next].coordinates)
              }}>
                {typeof place !== "string" && <option value="map" disabled>Selected on the map</option>}
                {Object.entries(PLACES).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
              </select>
            </label>
            {data && picked >= 0 ? <ForecastDetails data={data} picked={picked} label={placeName} which={which} hour={selectedHour} /> :
              <p className="text-sm text-muted-foreground" role="status">{data ? "No forecast covers that spot. Choose a location or select another point on the map." : active?.failed ? "Location forecasts will appear when the run loads." : "Loading location forecasts…"}</p>}
          </aside>

          <section className="min-w-0 overflow-hidden rounded-2xl border bg-card lg:col-start-1 lg:row-start-1" aria-labelledby="hourly-map-heading">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 sm:px-5">
              <div>
                <h2 id="hourly-map-heading" className="font-sans text-base font-semibold tracking-normal">Illustrative hourly map</h2>
                <p className="mt-1 text-xs text-muted-foreground">Select a point for its daily outlook.</p>
              </div>
              <div className="flex rounded-lg border p-1" role="group" aria-label="Hourly map source">
                {(["serein", "noaa"] as const).map(source => (
                  <Button key={source} type="button" size="sm" variant={which === source ? "secondary" : "ghost"} aria-pressed={which === source}
                    onClick={() => setWhich(source)}>{source === "serein" ? "Serein-scaled" : "NOAA"}</Button>
                ))}
              </div>
            </div>
            <ForecastMap data={data} which={which} hour={selectedHour} playing={playing} people={people} showPeople={showPeople} farOnly={farOnly}
              point={mapPoint} focus={focus} onPick={pickMapLocation} />
            <div className="space-y-4 border-t px-4 py-4 sm:px-5">
              <div className="flex flex-wrap items-end gap-3">
                <Button type="button" className="min-h-11" disabled={!data || data.hours < 2} onClick={() => setPlaying(value => !value)}>
                  {playing ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}{playing ? "Pause" : "Play"}
                </Button>
                <label className="grid min-w-[min(100%,11rem)] flex-1 gap-1 text-sm font-medium">
                  {data ? time : "Forecast hour"}
                  <input type="range" className="h-7 w-full accent-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" min={0}
                    max={(data?.hours ?? 1) - 1} disabled={!data || data.hours < 2} value={selectedHour} aria-label="Forecast hour" aria-valuetext={time || undefined}
                    onChange={event => { setPlaying(false); setHour(Number(event.target.value)) }} />
                </label>
                <label className="grid w-24 gap-1 text-xs text-muted-foreground">
                  Speed
                  <select className={selectClass} value={speed} onChange={event => setSpeed(event.target.value)}>
                    <option value="900">1×</option><option value="450">2×</option><option value="225">4×</option>
                  </select>
                </label>
              </div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground" aria-label="Map color scale">
                <span className="font-semibold text-foreground">PM₂.₅, µg/m³</span>
                {AQI.map((category, index) => <span key={category.name} className="inline-flex items-center gap-1">
                  <span aria-hidden="true" className="size-2.5 rounded-sm" style={{ background: `rgb(${category.rgb.join(",")})` }} /> {COLORS[index]}
                </span>)}
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">The hourly map shows NOAA’s modeled pattern, optionally adjusted to SmokeCast’s daily forecast. A clear map can reflect low concentrations or missing coverage.</p>
              <div className="border-t pt-3 text-sm">
                <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                  <label className="flex items-center gap-2"><Switch checked={showPeople} onCheckedChange={togglePeople} /> Population overlay</label>
                  {showPeople && <label className="flex items-center gap-2"><Switch checked={farOnly} onCheckedChange={setFarOnly} /> Only 25+ km from a monitor</label>}
                </div>
                {showPeople && (peopleFailed ? <p className="mt-3 text-xs text-muted-foreground">Population data could not load. <button className="text-primary underline" onClick={() => togglePeople(true)}>Retry</button></p> : people ? <>
                  <p className="mt-3 text-xs leading-relaxed text-muted-foreground">Dot size shows population. Color shows tract income quintile, from orange to green. A red ring marks tracts 25 km or farther from a monitor.</p>
                  {counts && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    About <strong className="text-foreground">{compact.format(farOnly ? counts.farUsg : counts.usg)}</strong> residents live in the {farOnly ? "selected distant tracts" : "tracts"} where this hourly illustration exceeds 35.5 µg/m³. This estimate uses census tract centers and outdoor concentrations.
                  </p>}
                  {placeCounts && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    At this hour, <strong className="text-foreground">{placeCounts.schools.toLocaleString("en-US")}</strong> public schools and <strong className="text-foreground">{placeCounts.hospitals.toLocaleString("en-US")}</strong> hospitals are where the map exceeds 35.5 µg/m³ (outdoor air).
                  </p>}
                </> : <p className="mt-3 text-xs text-muted-foreground" role="status">Loading population data…</p>)}
              </div>
            </div>
          </section>
        </div>

        <details className="mt-4 rounded-xl border bg-card/45 text-sm">
          <summary className="flex cursor-pointer list-none items-center gap-2 rounded-xl px-4 py-3 font-semibold focus-visible:outline-2 focus-visible:outline-primary">
            <Info className="size-4" aria-hidden="true" /> Map sources and limitations
          </summary>
          <div className="space-y-2 px-4 pb-4 leading-relaxed text-muted-foreground">
            <p>{data?.source}</p>
            <p>Smoke values are estimates at monitor or grid locations. Buildings, terrain, and roads are geographic context. Use the daily outlook for advance planning and <a href="https://www.airnow.gov/" className="text-primary underline">AirNow</a> for current air quality.</p>
            <Link className="inline-block text-primary underline" to="/about">See data sources and methods</Link>
          </div>
        </details>
      </main>
    </div>
  )
}
