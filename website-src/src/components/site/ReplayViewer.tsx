import { useEffect, useMemo, useRef, useState } from "react"
import { Pause, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { aqiOf } from "@/lib/world"

type Replay = {
  monitors: [number, number, string][]
  days: Record<string, { observed: (number | null)[]; serein: (number | null)[]; noaa: (number | null)[];
    summary: { unhealthy_monitors: number; serein_warned: number; noaa_warned: number } }>
}
type Geo = { features: { geometry: { type: string; coordinates: number[][][] | number[][][][] } }[] }
const BOX = { lonMin: -125, lonMax: -110.5, latMin: 41.3, latMax: 49.2 }

function project(w: number, h: number, lat: number, lon: number) {
  const x = (lon - BOX.lonMin) / (BOX.lonMax - BOX.lonMin), y = (lat - BOX.latMin) / (BOX.latMax - BOX.latMin)
  const depth = 0.62 + 0.38 * (1 - y)
  return { x: w * (0.5 + (x - 0.5) * depth * 1.02), y: h * (0.97 - y * 0.52), s: depth }
}

function Panel({ title, values, monitors, states, caption }: {
  title: string; values: (number | null)[]; monitors: Replay["monitors"]; states: Geo | null; caption: string }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const c = ref.current
    if (!c || !states) return
    const ctx = c.getContext("2d")!, w = c.width, h = c.height
    ctx.clearRect(0, 0, w, h)
    ctx.strokeStyle = "rgba(220,235,215,.45)"; ctx.fillStyle = "rgba(220,235,215,.05)"
    for (const f of states.features) {
      const polys = (f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates) as number[][][][]
      for (const poly of polys) {
        ctx.beginPath()
        poly[0].forEach(([lon, lat], i) => {
          const p = project(w, h, Math.max(BOX.latMin - 1, Math.min(lat, BOX.latMax + 1)), lon)
          if (i) ctx.lineTo(p.x, p.y); else ctx.moveTo(p.x, p.y)
        })
        ctx.fill(); ctx.stroke()
      }
    }
    const order = monitors.map((_, i) => i).filter(i => values[i] !== null)
      .filter(i => monitors[i][0] >= BOX.latMin && monitors[i][0] <= BOX.latMax && monitors[i][1] >= BOX.lonMin && monitors[i][1] <= BOX.lonMax)
      .sort((a, b) => monitors[b][0] - monitors[a][0])
    for (const i of order) {
      const v = values[i] as number, p = project(w, h, monitors[i][0], monitors[i][1])
      const height = Math.min(v, 300) * 0.75 * p.s, half = 3.4 * p.s
      ctx.fillStyle = `rgb(${aqiOf(v).rgb.join(",")})`; ctx.fillRect(p.x - half, p.y - height, half * 2, height)
      ctx.fillStyle = "rgba(0,0,0,.25)"; ctx.fillRect(p.x, p.y - height, half, height)
    }
  }, [values, monitors, states])
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{caption}</CardDescription>
      </CardHeader>
      <CardContent><canvas ref={ref} width={560} height={420} className="h-auto w-full" role="img" aria-label={title} /></CardContent>
    </Card>
  )
}

export function ReplayViewer() {
  const [data, setData] = useState<Replay | null>(null)
  const [states, setStates] = useState<Geo | null>(null)
  const [k, setK] = useState(5)
  const [playing, setPlaying] = useState(false)
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/replay_aug2023.json`).then(r => r.json()).then(setData)
    fetch(`${import.meta.env.BASE_URL}data/states.geojson`).then(r => r.json()).then(setStates)
  }, [])
  const days = useMemo(() => (data ? Object.keys(data.days).sort() : []), [data])
  useEffect(() => {
    if (!playing || !days.length) return
    const t = setInterval(() => setK(x => (x + 1) % days.length), 1400)
    return () => clearInterval(t)
  }, [playing, days])
  const day = days[k], d = data && day ? data.days[day] : null
  return (
    <div>
      <div className="mt-8 flex items-center gap-4">
        <Button size="icon" className="size-11 rounded-full" onClick={() => setPlaying(p => !p)} aria-label={playing ? "Pause" : "Play"}>
          {playing ? <Pause /> : <Play />}
        </Button>
        <Slider className="flex-1" min={0} max={Math.max(days.length - 1, 0)} step={1} value={[k]}
          onValueChange={([v]) => { setPlaying(false); setK(v) }} aria-label="Day" />
        <div className="min-w-56 text-right font-serif text-4xl">
          {day ? new Date(day + "T12:00:00Z").toLocaleDateString("en-US", { month: "long", day: "numeric", timeZone: "UTC" }) : ""}
        </div>
      </div>
      {d && data && (
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <Panel title="NOAA's forecast, the day before" values={d.noaa} monitors={data.monitors} states={states}
            caption={`Flagged ${d.summary.noaa_warned} of ${d.summary.unhealthy_monitors} unhealthy monitors`} />
          <Panel title="Serein's forecast, the day before" values={d.serein} monitors={data.monitors} states={states}
            caption={`Flagged ${d.summary.serein_warned} of ${d.summary.unhealthy_monitors} unhealthy monitors`} />
          <Panel title="What the monitors measured" values={d.observed} monitors={data.monitors} states={states}
            caption={`${d.summary.unhealthy_monitors} monitors reached unhealthy for sensitive groups or worse`} />
        </div>
      )}
    </div>
  )
}
