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

const cache = new Map<string, Promise<WorldData>>()
export function loadWorld(mode: string): Promise<WorldData> {
  if (!cache.has(mode)) {
    cache.set(mode, fetch(`${import.meta.env.BASE_URL}data/${mode}.json`).then(r => r.json()).then((d: WorldData) => {
      d.grid = new Int32Array(GRID.rows * GRID.cols).fill(-1)
      d.points.forEach(([lat, lon, kind], i) => {
        if (kind !== 0) return
        const r = Math.round((lat - GRID.lat0) / GRID.step), c = Math.round((lon - GRID.lon0) / GRID.step)
        if (r >= 0 && r < GRID.rows && c >= 0 && c < GRID.cols) d.grid[r * GRID.cols + c] = i
      })
      return d
    }))
  }
  return cache.get(mode)!
}

export const valueAt = (d: WorldData, which: Which, p: number, h: number) => d[which][p * d.hours + h] ?? null

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
  const ctx = canvas.getContext("2d")!
  if (!rowLat || rowLat.length !== canvas.height) {
    rowLat = new Float64Array(canvas.height)
    for (let y = 0; y < canvas.height; y++) {
      const m = mercY(BOX.north) + (mercY(BOX.south) - mercY(BOX.north)) * (y / (canvas.height - 1))
      rowLat[y] = ((Math.atan(Math.exp(m)) - Math.PI / 4) * 360) / Math.PI
    }
  }
  const img = ctx.createImageData(canvas.width, canvas.height)
  const px = img.data, W = canvas.width
  const g = (r: number, c: number) => {
    const p = d.grid[r * GRID.cols + c]
    return p === undefined || p < 0 ? null : valueAt(d, which, p, hour)
  }
  for (let y = 0; y < canvas.height; y++) {
    const fr = Math.min(Math.max((rowLat[y] - GRID.lat0) / GRID.step, 0), GRID.rows - 1)
    const r0 = Math.min(Math.floor(fr), GRID.rows - 2), ty = fr - r0
    for (let x = 0; x < W; x++) {
      const fc = x / SCALE, c0 = Math.min(Math.floor(fc), GRID.cols - 2), tx = fc - c0
      const a = g(r0, c0), b = g(r0, c0 + 1), c = g(r0 + 1, c0), e = g(r0 + 1, c0 + 1)
      if (a === null || b === null || c === null || e === null) continue
      const v = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + e * tx) * ty
      if (v < 6) continue // clean air stays see-through
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
  const j = d.wind_hours.findIndex(h => Math.abs(h - hour) <= 1.5)
  if (j < 0) return { type: "FeatureCollection", features }
  for (let r = 0; r < GRID.rows; r += 2) {
    for (let c = 0; c < GRID.cols; c += 2) {
      const p = d.grid[r * GRID.cols + c]
      if (p < 0) continue
      const u = d.u[p * nh + j], v = d.v[p * nh + j]
      if (u === null || v === null) continue
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
