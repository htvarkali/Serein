import { useEffect, useMemo, useRef, useState } from "react"
import { asset } from "@/data/site"
import { AQI, BOX, aqiOf, loadWorld, valueAt, type Which, type WorldData } from "@/lib/world"

// Live pieces for the home page. Everything shown here is read from the published
// forecast file (data/live.json); nothing is simulated.

type Live = { state: "loading" } | { state: "error" } | { state: "ready"; data: WorldData }

export function useLive(): Live {
  const [live, setLive] = useState<Live>({ state: "loading" })
  useEffect(() => {
    let alive = true
    loadWorld("live").then(data => alive && setLive({ state: "ready", data }), () => alive && setLive({ state: "error" }))
    return () => { alive = false }
  }, [])
  return live
}

const PT = "America/Los_Angeles"
const ptDate = (ms: number) => new Date(ms).toLocaleDateString("en-CA", { timeZone: PT })
const inWest = (lat: number, lon: number) => lat >= BOX.south && lat <= BOX.north && lon >= BOX.west && lon <= BOX.east

/** Hours (indexes) that fall on the Pacific-time calendar day after the issue day. */
function tomorrowHours(d: WorldData) {
  const start = Date.parse(d.start_utc)
  const issue = ptDate(start)
  const dates = Array.from({ length: d.hours }, (_, h) => ptDate(start + h * 3600e3))
  const next = dates.find(x => x > issue)
  return { date: next ?? null, hours: dates.flatMap((x, h) => (x === next ? [h] : [])) }
}

function dayMean(d: WorldData, which: Which, p: number, hours: number[]) {
  let sum = 0, n = 0
  for (const h of hours) { const v = valueAt(d, which, p, h); if (v !== null) { sum += v; n++ } }
  return n >= hours.length * 0.75 ? sum / n : null
}

const longDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })

type Geo = { features: { geometry: { type: string; coordinates: number[][][] | number[][][][] } }[] }
let statesCache: Promise<Geo> | null = null
const loadStates = () => (statesCache ??= fetch(asset("data/states.geojson")).then(r => r.json() as Promise<Geo>))

/** Dotted map of the West: one dot per 0.25-degree forecast grid point, colored by the
 *  EPA AQI category of its average PM2.5 over the chosen day. */
function DotCanvas({ d, values, label }: { d: WorldData; values: (number | null)[]; label: string }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const [states, setStates] = useState<Geo | null>(null)
  useEffect(() => { loadStates().then(setStates, () => setStates(null)) }, [])

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")!
    let frame = 0, w = 0, h = 0
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const k = Math.cos((40.5 * Math.PI) / 180)
    const spanX = (BOX.east - BOX.west) * k, spanY = BOX.north - BOX.south
    let scale = 1, ox = 0, oy = 0
    const project = (lat: number, lon: number): [number, number] => [ox + (lon - BOX.west) * k * scale, oy + (BOX.north - lat) * scale]
    const phase = values.map((_, i) => (i * 2.399) % (Math.PI * 2))
    // Only draw grid points over land (inside a state outline), so the dots form the map.
    const rings: number[][][] = []
    for (const f of states?.features ?? []) {
      const polys = (f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates) as number[][][][]
      for (const poly of polys) rings.push(poly[0])
    }
    const inside = (lat: number, lon: number) => {
      let hit = false
      for (const ring of rings) {
        for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
          const [xi, yi] = ring[i], [xj, yj] = ring[j]
          if ((yi > lat) !== (yj > lat) && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) hit = !hit
        }
        if (hit) return true
      }
      return false
    }
    const onLand = d.points.map(([lat, lon]) => !rings.length || inside(lat, lon))

    function resize() {
      const box = canvas!.getBoundingClientRect()
      w = box.width; h = box.height
      canvas!.width = Math.round(w * dpr); canvas!.height = Math.round(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      scale = Math.min(w / spanX, h / spanY) * 0.94
      ox = (w - spanX * scale) / 2; oy = (h - spanY * scale) / 2
    }
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)
    resize()

    function draw(now: number) {
      frame = requestAnimationFrame(draw)
      ctx.clearRect(0, 0, w, h)
      if (states) {
        ctx.save()
        ctx.beginPath(); ctx.rect(ox, oy, spanX * scale, spanY * scale); ctx.clip()
        ctx.strokeStyle = "#5b6cf659"; ctx.lineWidth = 0.8
        for (const f of states.features) {
          const polys = (f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates) as number[][][][]
          for (const poly of polys) for (const ring of poly) {
            ctx.beginPath()
            ring.forEach(([lon, lat], i) => { const [x, y] = project(lat, lon); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y) })
            ctx.stroke()
          }
        }
        ctx.restore()
      }
      const t = now / 1000
      const r = Math.max(1.1, scale * 0.25 * 0.36)
      d.points.forEach(([lat, lon, kind], i) => {
        if (!onLand[i]) return
        const v = values[i]
        const [x, y] = project(lat, lon)
        if (kind === 1) {
          ctx.globalAlpha = 0.9; ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 0.9
          ctx.beginPath(); ctx.arc(x, y, r * 0.85, 0, Math.PI * 2); ctx.stroke()
          return
        }
        if (v === null) { ctx.globalAlpha = 0.18; ctx.fillStyle = "#8a93a8" }
        else {
          const [cr, cg, cb] = aqiOf(v).rgb
          ctx.fillStyle = `rgb(${cr},${cg},${cb})`
          ctx.globalAlpha = 0.55 + 0.35 * (0.5 + 0.5 * Math.sin(t * 1.3 + phase[i]))
        }
        ctx.beginPath(); ctx.arc(x, y, v === null ? r * 0.6 : r, 0, Math.PI * 2); ctx.fill()
      })
      ctx.globalAlpha = 1
    }
    frame = requestAnimationFrame(draw)
    return () => { cancelAnimationFrame(frame); ro.disconnect() }
  }, [d, values, states])

  return <canvas ref={ref} role="img" aria-label={label} className="absolute inset-0 size-full" />
}

/** Before/after slider (NOAA's forecast vs. the SmokeCast-adjusted field) for tomorrow. */
export function ForecastCompare() {
  const live = useLive()
  const [split, setSplit] = useState(50)
  const box = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)

  const model = useMemo(() => {
    if (live.state !== "ready") return null
    const d = live.data
    const { date, hours } = tomorrowHours(d)
    if (!date || hours.length < 18) return null
    const noaa = d.points.map((_, p) => dayMean(d, "noaa", p, hours))
    const serein = d.points.map((_, p) => dayMean(d, "serein", p, hours))
    const grid = d.points.flatMap((pt, i) => (pt[2] === 0 ? [i] : []))
    const share = (vals: (number | null)[]) => {
      const vs = grid.map(i => vals[i]).filter((v): v is number => v !== null)
      return vs.length ? Math.round((100 * vs.filter(v => v > 9.0).length) / vs.length) : 0
    }
    return { d, date, noaa, serein, aboveGood: { noaa: share(noaa), serein: share(serein) } }
  }, [live])

  function setFromPointer(clientX: number) {
    const r = box.current?.getBoundingClientRect()
    if (!r) return
    setSplit(Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100)))
  }

  return (
    <figure className="min-w-0">
      <div ref={box} className="outlined relative aspect-[5/6] w-full cursor-ew-resize touch-none overflow-hidden rounded-[1.6rem] bg-[#111111] select-none sm:aspect-[4/4.2]"
        onPointerDown={e => { dragging.current = true; e.currentTarget.setPointerCapture(e.pointerId); setFromPointer(e.clientX) }}
        onPointerMove={e => dragging.current && setFromPointer(e.clientX)}
        onPointerUp={() => { dragging.current = false }}>
        {model ? <>
          <DotCanvas d={model.d} values={model.serein} label={`SmokeCast-adjusted average PM2.5 for ${longDate(model.date)}`} />
          <div className="absolute inset-0" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }}>
            <div className="absolute inset-0 bg-[#111111]" />
            <DotCanvas d={model.d} values={model.noaa} label={`NOAA forecast average PM2.5 for ${longDate(model.date)}`} />
          </div>
          <span className="absolute top-4 left-4 rounded-full bg-black/45 px-3 py-1.5 text-[0.6rem] font-semibold tracking-[0.22em] text-[#f5f5f5] uppercase backdrop-blur">NOAA forecast</span>
          <span className="absolute top-4 right-4 rounded-full bg-[#5b6cf6]/90 px-3 py-1.5 text-[0.6rem] font-semibold tracking-[0.22em] text-[#ffffff] uppercase">SmokeCast</span>
          <div className="pointer-events-none absolute inset-y-0 w-px bg-[#f5f5f5]/80" style={{ left: `${split}%` }}>
            <span className="compare-handle absolute top-1/2 left-1/2 grid size-12 -translate-1/2 place-items-center rounded-full bg-[#ffffff] text-[#0a0a0a]">⟷</span>
          </div>
        </> : <p className="absolute inset-0 grid place-items-center p-8 text-center text-sm text-muted-foreground">
          {live.state === "error" ? "The latest forecast could not load. Try the forecast map." : live.state === "loading" ? "Loading the latest forecast…" : "This run does not cover a full next day."}
        </p>}
      </div>
      <label className="sr-only" htmlFor="compare-split">Move the divider between the NOAA forecast and SmokeCast</label>
      <input id="compare-split" type="range" min={0} max={100} value={Math.round(split)} onChange={e => setSplit(Number(e.target.value))}
        className="mt-4 w-full accent-[#5b6cf6]" />
      {model && <figcaption className="mt-3 space-y-3 text-sm text-muted-foreground">
        <p>Average PM₂.₅ over {longDate(model.date)} (Pacific time), from the run issued {longDate(model.d.issue_date)}.
          Each dot is a 0.25° forecast grid point; white rings are EPA monitors. Grid points above “Good”:
          {" "}NOAA {model.aboveGood.noaa}%, SmokeCast {model.aboveGood.serein}%.</p>
        <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs" aria-label="AQI categories">
          {AQI.slice(0, 5).map(a => <li key={a.name} className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-full" style={{ background: `rgb(${a.rgb.join(",")})` }} />{a.name}</li>)}
        </ul>
      </figcaption>}
    </figure>
  )
}
