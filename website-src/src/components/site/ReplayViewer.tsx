import { useEffect, useRef, useState } from "react"
import { Pause, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { asset } from "@/data/site"
import { aqiOf } from "@/lib/world"

type ReplayDay = {
  observed: (number | null)[]
  serein: (number | null)[]
  noaa: (number | null)[]
  summary: { unhealthy_monitors: number; serein_warned: number; noaa_warned: number }
}
type Replay = {
  monitors: [number, number, string][]
  days: Record<string, ReplayDay>
}
type Geo = { features: { geometry: { type: string; coordinates: number[][][] | number[][][][] } }[] }
type ReplayResult = { state: "loading" | "error" } | { state: "ready"; replay: Replay; states: Geo; days: string[] }

const BOX = { lonMin: -125, lonMax: -110.5, latMin: 41.3, latMax: 49.2 }
const formatter = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", timeZone: "UTC" })

function project(w: number, h: number, lat: number, lon: number) {
  const x = (lon - BOX.lonMin) / (BOX.lonMax - BOX.lonMin)
  const y = (lat - BOX.latMin) / (BOX.latMax - BOX.latMin)
  const depth = 0.62 + 0.38 * (1 - y)
  return { x: w * (0.5 + (x - 0.5) * depth * 1.02), y: h * (0.97 - y * 0.52), s: depth }
}

function Panel({ title, values, monitors, states, caption }: {
  title: string; values: (number | null)[]; monitors: Replay["monitors"]; states: Geo; caption: string
}) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext("2d")
    if (!canvas || !ctx) return

    const { width, height } = canvas
    ctx.clearRect(0, 0, width, height)
    ctx.strokeStyle = "rgba(220,235,215,.45)"
    ctx.fillStyle = "rgba(220,235,215,.05)"
    for (const feature of states.features) {
      const { type, coordinates } = feature.geometry
      const polygons = (type === "Polygon" ? [coordinates] : coordinates) as number[][][][]
      for (const poly of polygons) {
        ctx.beginPath()
        poly[0].forEach(([lon, lat], index) => {
          const point = project(width, height, Math.max(BOX.latMin - 1, Math.min(lat, BOX.latMax + 1)), lon)
          if (index) ctx.lineTo(point.x, point.y)
          else ctx.moveTo(point.x, point.y)
        })
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      }
    }

    const order = monitors.map((_, i) => i).filter(i => Number.isFinite(values[i]))
      .filter(i => monitors[i][0] >= BOX.latMin && monitors[i][0] <= BOX.latMax && monitors[i][1] >= BOX.lonMin && monitors[i][1] <= BOX.lonMax)
      .sort((a, b) => monitors[b][0] - monitors[a][0])
    for (const i of order) {
      const value = values[i] as number
      const point = project(width, height, monitors[i][0], monitors[i][1])
      const barHeight = Math.min(value, 300) * 0.75 * point.s
      const half = 3.4 * point.s
      ctx.fillStyle = `rgb(${aqiOf(value).rgb.join(",")})`
      ctx.fillRect(point.x - half, point.y - barHeight, half * 2, barHeight)
      ctx.fillStyle = "rgba(0,0,0,.25)"
      ctx.fillRect(point.x, point.y - barHeight, half, barHeight)
    }
  }, [values, monitors, states])

  return (
    <Card className="gap-4 overflow-hidden">
      <CardHeader className="px-4 sm:px-6">
        <h3 className="text-base font-semibold leading-snug">{title}</h3>
        <CardDescription>{caption}</CardDescription>
      </CardHeader>
      <CardContent className="px-4 sm:px-6">
        <canvas ref={ref} width={560} height={360} className="h-auto w-full rounded-md bg-[#18322d]"
          role="img" aria-label={`Monitor map. ${title}. ${caption}`} />
      </CardContent>
    </Card>
  )
}

async function readJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(asset(path), { signal })
  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export function ReplayViewer() {
  const [result, setResult] = useState<ReplayResult>({ state: "loading" })
  const [attempt, setAttempt] = useState(0)
  const [dayIndex, setDayIndex] = useState(0)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller
    Promise.all([
      readJson<Replay>("data/replay_aug2023.json", signal),
      readJson<Geo>("data/states.geojson", signal),
    ]).then(([replay, states]) => {
      const days = Object.keys(replay.days).sort()
      if (!days.length || !Array.isArray(replay.monitors) || !Array.isArray(states.features)) {
        throw new Error("Replay data is incomplete")
      }
      if (!signal.aborted) {
        setDayIndex(Math.max(0, days.indexOf("2023-08-20")))
        setResult({ state: "ready", replay, states, days })
      }
    }).catch(() => {
      if (!signal.aborted) setResult({ state: "error" })
    })
    return () => controller.abort()
  }, [attempt])

  const dayCount = result.state === "ready" ? result.days.length : 0
  useEffect(() => {
    if (!playing || dayCount < 2) return
    const timer = window.setInterval(() => setDayIndex(index => (index + 1) % dayCount), 1600)
    return () => window.clearInterval(timer)
  }, [playing, dayCount])

  if (result.state !== "ready") return (
    <div className="mt-8 grid min-h-36 place-content-center gap-3 rounded-xl border bg-card p-5 text-center">
      <p role="status" className="text-muted-foreground">{result.state === "error" ? "The smoke replay couldn’t load." : "Loading the smoke replay…"}</p>
      {result.state === "error" && <Button type="button" variant="outline" onClick={() => {
        setPlaying(false)
        setDayIndex(0)
        setResult({ state: "loading" })
        setAttempt(value => value + 1)
      }}>Try again</Button>}
    </div>
  )

  const { days, replay, states } = result
  const date = days[dayIndex]
  const day = replay.days[date]
  const dayLabel = formatter.format(new Date(date + "T12:00:00Z"))
  const { unhealthy_monitors, serein_warned, noaa_warned } = day.summary

  return (
    <div>
      <div className="mt-8 grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-3 rounded-xl border bg-card p-4 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:px-5">
        <Button type="button" size="icon" className="size-11 rounded-full" disabled={dayCount < 2}
          onClick={() => setPlaying(value => !value)} aria-label={playing ? "Pause replay" : "Play replay"}>
          {playing ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}
        </Button>
        <input type="range" className="col-span-2 row-start-2 h-11 min-w-0 w-full accent-primary outline-none focus-visible:ring-2 focus-visible:ring-ring sm:col-span-1 sm:row-start-auto"
          min={0} max={dayCount - 1} step={1} value={dayIndex} aria-label="Replay date" aria-valuetext={dayLabel}
          onChange={event => { setPlaying(false); setDayIndex(event.currentTarget.valueAsNumber) }} />
        <time dateTime={date} className="col-start-2 row-start-1 min-w-0 text-right font-serif text-3xl sm:col-start-auto sm:row-start-auto">{dayLabel}</time>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <Panel title="Reference forecast" values={day.noaa} monitors={replay.monitors} states={states}
          caption={`Flagged ${noaa_warned} of ${unhealthy_monitors} monitors that reached the threshold`} />
        <Panel title="Serein forecast" values={day.serein} monitors={replay.monitors} states={states}
          caption={`Flagged ${serein_warned} of ${unhealthy_monitors} monitors that reached the threshold`} />
        <Panel title="Recorded conditions" values={day.observed} monitors={replay.monitors} states={states}
          caption={`${unhealthy_monitors} monitors reached unhealthy for sensitive groups or worse`} />
      </div>
    </div>
  )
}
