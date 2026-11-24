import type { Feature, FeatureCollection } from "geojson"
// Data and drawing helpers for Smoke World. The hour-by-hour file comes from
// `python -m serein.world` (NOAA AQM hourly shape, scaled per local day to Serein).

export type WorldData = {
  issue_date: string
  start_utc: string
  hours: number
  source: string
  points: [number, number, number][] // lat, lon, kind (1 = EPA monitor, 0 = map grid)
  noaa: (number | null)[]
  serein: (number | null)[]
  wind_hours: number[]
  u: (number | null)[]
  v: (number | null)[]
  fires: [number, number, number][] // lat, lon, fire radiative power
  // SmokeCast's tested daily forecast per local day: median and 90% range per point.
  daily?: { lead: number; date: string | null; q05: (number | null)[]; q50: (number | null)[]; q95: (number | null)[] }[]
  grid: Int32Array
}
export type Which = "serein" | "noaa"

export const GRID = { lat0: 32, lon0: -125, step: 0.25, rows: 69, cols: 45 }
export const BOX = { west: -125, east: -114, south: 32, north: 49 }

export const AQI = [
  { hi: 9.0, rgb: [76, 175, 80], name: "Good" },
  { hi: 35.4, rgb: [246, 211, 45], name: "Moderate" },
  { hi: 55.4, rgb: [240, 136, 62], name: "Unhealthy for sensitive groups" },
  { hi: 125.4, rgb: [229, 72, 77], name: "Unhealthy" },
  { hi: 225.4, rgb: [142, 78, 198], name: "Very unhealthy" },
  { hi: Infinity, rgb: [125, 31, 44], name: "Hazardous" },
] as const
export const aqiOf = (v: number) => AQI[Math.max(0, AQI.findIndex(a => v <= a.hi))]

async function fetchData<T>(file: string, cache: RequestCache = "default"): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 15_000)
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/${file}.json`, { signal: controller.signal, cache })
    if (!response.ok) throw new Error(`Forecast data request failed (${response.status})`)
    return await response.json() as T
  } finally {
    window.clearTimeout(timer)
  }
}

const cache = new Map<string, { request: Promise<WorldData>; started: number }>()
export function loadWorld(mode: string): Promise<WorldData> {
  const existing = cache.get(mode)
  if (existing && (mode !== "live" || Date.now() - existing.started < 120_000)) return existing.request

  const request: Promise<WorldData> = fetchData<WorldData>(mode, mode === "live" ? "no-cache" : "default")
    .then(d => {
      if (!Array.isArray(d.points) || !d.points.length || !Number.isInteger(d.hours) || d.hours < 1 ||
          !Number.isFinite(Date.parse(d.start_utc)) || !Array.isArray(d.fires) ||
          !Array.isArray(d.wind_hours) || !Array.isArray(d.u) || !Array.isArray(d.v) ||
          ![d.noaa, d.serein].every(values => Array.isArray(values) && values.length === d.points.length * d.hours)) {
        throw new Error("Forecast data is incomplete")
      }
      d.grid = new Int32Array(GRID.rows * GRID.cols).fill(-1)
      d.points.forEach(([lat, lon, kind], i) => {
        if (kind !== 0) return
        const r = Math.round((lat - GRID.lat0) / GRID.step)
        const c = Math.round((lon - GRID.lon0) / GRID.step)
        if (r >= 0 && r < GRID.rows && c >= 0 && c < GRID.cols) d.grid[r * GRID.cols + c] = i
      })
      return d
    }).catch(error => {
      if (cache.get(mode)?.request === request) cache.delete(mode)
      throw error
    })
  cache.set(mode, { request, started: Date.now() })
  return request
}

export function valueAt(d: WorldData, which: Which, p: number, h: number): number | null {
  if (p < 0 || p >= d.points.length || h < 0 || h >= d.hours) return null
  const value = d[which][p * d.hours + h]
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

// ---- smoke image: rows spaced in Web Mercator so the image lines up with the map ----
const SCALE = 8
const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))
export function makeSmokeCanvas() {
  const canvas = document.createElement("canvas")
  canvas.width = (GRID.cols - 1) * SCALE
  canvas.height = (GRID.rows - 1) * SCALE
  return canvas
}
let rowLat: Float64Array | null = null
export function drawSmoke(canvas: HTMLCanvasElement, d: WorldData, which: Which, hour: number) {
  const ctx = canvas.getContext("2d")
  if (!ctx) return
  if (!rowLat || rowLat.length !== canvas.height) {
    rowLat = new Float64Array(canvas.height)
    for (let y = 0; y < canvas.height; y++) {
      const m = mercY(BOX.north) + (mercY(BOX.south) - mercY(BOX.north)) * (y / (canvas.height - 1))
      rowLat[y] = ((Math.atan(Math.exp(m)) - Math.PI / 4) * 360) / Math.PI
    }
  }
  const img = ctx.createImageData(canvas.width, canvas.height)
  const px = img.data, W = canvas.width
  const field = Float32Array.from(d.grid, p => valueAt(d, which, p, hour) ?? NaN)
  for (let y = 0; y < canvas.height; y++) {
    const fr = Math.min(Math.max((rowLat[y] - GRID.lat0) / GRID.step, 0), GRID.rows - 1)
    const r0 = Math.min(Math.floor(fr), GRID.rows - 2), ty = fr - r0
    for (let x = 0; x < W; x++) {
      const fc = x / SCALE, c0 = Math.min(Math.floor(fc), GRID.cols - 2), tx = fc - c0
      const i = r0 * GRID.cols + c0
      const a = field[i], b = field[i + 1], c = field[i + GRID.cols], e = field[i + GRID.cols + 1]
      const v = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + e * tx) * ty
      if (!(v >= 6)) continue // Missing values and low concentrations stay transparent.
      const { rgb } = aqiOf(v)
      const k = (y * W + x) * 4
      px[k] = rgb[0]; px[k + 1] = rgb[1]; px[k + 2] = rgb[2]
      px[k + 3] = Math.min(0.8, 0.1 + v / 95) * 255
    }
  }
  ctx.putImageData(img, 0, 0)
}

export function nearestPoint(d: WorldData, lng: number, lat: number) {
  let best = -1, bd = Infinity
  const k = Math.cos((lat * Math.PI) / 180)
  d.points.forEach(([la, lo], i) => {
    const dd = (la - lat) ** 2 + ((lo - lng) * k) ** 2
    if (dd < bd) { bd = dd; best = i }
  })
  return Math.sqrt(bd) < 0.4 ? best : -1
}

export function windFeatures(d: WorldData, hour: number): FeatureCollection {
  const features: Feature[] = []
  const nh = d.wind_hours.length
  // Nearest HRRR wind hour (every 3 hours), at most 2 hours away.
  let j = -1
  d.wind_hours.forEach((h, k) => { if (Math.abs(h - hour) <= 2 && (j < 0 || Math.abs(h - hour) < Math.abs(d.wind_hours[j] - hour))) j = k })
  if (j < 0) return { type: "FeatureCollection", features }
  for (let r = 0; r < GRID.rows; r += 2) {
    for (let c = 0; c < GRID.cols; c += 2) {
      const p = d.grid[r * GRID.cols + c]
      if (p < 0) continue
      const u = d.u[p * nh + j], v = d.v[p * nh + j]
      if (typeof u !== "number" || typeof v !== "number" || !Number.isFinite(u) || !Number.isFinite(v)) continue
      const [lat, lon] = d.points[p]
      const s = 0.035
      features.push({ type: "Feature", properties: { speed: Math.hypot(u, v), bearing: (Math.atan2(u, v) * 180) / Math.PI },
        geometry: { type: "LineString", coordinates: [[lon, lat], [lon + (u * s) / Math.cos((lat * Math.PI) / 180), lat + v * s]] } })
    }
  }
  return { type: "FeatureCollection", features }
}

export function localTime(d: WorldData, hour: number) {
  const t = new Date(Date.parse(d.start_utc) + hour * 3600e3)
  return t.toLocaleString("en-US", { timeZone: "America/Los_Angeles", weekday: "short", month: "short", day: "numeric", hour: "numeric" }) + " PT"
}

// Smoke at any location, by bilinear interpolation on the 0.25 degree grid (null outside it).
export function sampleAt(d: WorldData, which: Which, hour: number, lat: number, lon: number): number | null {
  const fr = (lat - GRID.lat0) / GRID.step, fc = (lon - GRID.lon0) / GRID.step
  if (fr < 0 || fc < 0 || fr > GRID.rows - 1 || fc > GRID.cols - 1) return null
  const r0 = Math.min(Math.floor(fr), GRID.rows - 2), c0 = Math.min(Math.floor(fc), GRID.cols - 2)
  const ty = fr - r0, tx = fc - c0
  const g = (r: number, c: number) => {
    const p = d.grid[r * GRID.cols + c]
    return p < 0 ? null : valueAt(d, which, p, hour)
  }
  const a = g(r0, c0), b = g(r0, c0 + 1), c = g(r0 + 1, c0), e = g(r0 + 1, c0 + 1)
  if (a === null || b === null || c === null || e === null) return null
  return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + e * tx) * ty
}

export type People = { source: string; tracts: [number, number, number, number, number][] } // lat, lon, population, income quintile (0 lowest), km to monitor
let peopleCache: Promise<People> | null = null
export const loadPeople = () => (peopleCache ??= fetchData<People>("people").catch(error => {
  peopleCache = null
  throw error
}))

// People living where this hour's smoke is at or above each level.
export function peopleUnderSmoke(d: WorldData, which: Which, hour: number, people: People) {
  let usg = 0, unhealthy = 0, farUsg = 0
  for (const [lat, lon, pop, , km] of people.tracts) {
    const v = sampleAt(d, which, hour, lat, lon)
    if (v === null) continue
    if (v >= 35.5) { usg += pop; if (km >= 25) farUsg += pop }
    if (v >= 55.5) unhealthy += pop
  }
  return { usg, unhealthy, farUsg }
}
