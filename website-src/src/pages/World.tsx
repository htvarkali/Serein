import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Link } from "react-router-dom"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import { Info, Pause, Play, X } from "lucide-react"
import { Area, ComposedChart, Line, ReferenceLine, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { PersonPanel } from "@/components/site/PersonPanel"
import { Wordmark } from "@/components/site/SiteLayout"
import { AQI, BOX, aqiOf, drawSmoke, loadWorld, localTime, makeSmokeCanvas, nearestPoint, valueAt, windFeatures,
  type Which, type WorldData } from "@/lib/world"

const MODES = { live: "Live: today + 3 days", aug2023: "Example: August 2023 smoke event" } as const
type Mode = keyof typeof MODES

const chartConfig = {
  serein: { label: "Serein", color: "var(--chart-1)" },
  noaa: { label: "NOAA", color: "var(--chart-2)" },
} satisfies ChartConfig

function initialMode(): Mode {
  const m = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("mode")
  return m === "aug2023" ? "aug2023" : "live"
}

export default function World() {
  const mapEl = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const canvas = useMemo(() => makeSmokeCanvas(), [])
  const [mode, setMode] = useState<Mode>(initialMode)
  const [which, setWhich] = useState<Which>("serein")
  const [hour, setHour] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState("450")
  const [data, setData] = useState<WorldData | null>(null)
  const [ready, setReady] = useState(false)
  const [picked, setPicked] = useState<number | null>(null)

  // ---- map, once ----
  useEffect(() => {
    if (!mapEl.current) return
    const map = new maplibregl.Map({
      container: mapEl.current,
      center: [-120.6, 41.2], zoom: 5.1, pitch: 52, bearing: -8, maxPitch: 80,
      // Smoother loading: keep many tiles in memory, fade instead of popping in,
      // and fetch lower-zoom tiles ahead so there is always something to show.
      maxTileCacheSize: 4000, fadeDuration: 180, refreshExpiredTiles: false,
      attributionControl: { compact: true },
      style: {
        version: 8,
        glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
        sources: {
          photo: { type: "raster", tileSize: 256, maxzoom: 16,
            tiles: ["https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"],
            attribution: "Imagery: USGS The National Map" },
          dem: { type: "raster-dem", encoding: "terrarium", tileSize: 256, maxzoom: 15,
            tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
            attribution: "Terrain: AWS Terrain Tiles (USGS 3DEP and others)" },
          omt: { type: "vector", url: "https://tiles.openfreemap.org/planet", attribution: "© OpenStreetMap contributors, OpenFreeMap" },
        },
        layers: [
          { id: "bg", type: "background", paint: { "background-color": "#1d2a26" } },
          { id: "photo", type: "raster", source: "photo", paint: { "raster-fade-duration": 250, "raster-saturation": -0.1 } },
        ],
        sky: { "sky-color": "#9ec6e6", "horizon-color": "#e9e3cf", "fog-color": "#d7d2c4", "sky-horizon-blend": 0.6, "horizon-fog-blend": 0.6, "fog-ground-blend": 0.35 },
      },
    })
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right")
    map.addControl(new maplibregl.ScaleControl({ unit: "imperial" }), "bottom-left")
    map.on("load", () => {
      map.setTerrain({ source: "dem", exaggeration: 1.4 })
      map.addSource("smoke", { type: "canvas", canvas, animate: true,
        coordinates: [[BOX.west, BOX.north], [BOX.east, BOX.north], [BOX.east, BOX.south], [BOX.west, BOX.south]] })
      map.addLayer({ id: "smoke", type: "raster", source: "smoke", paint: { "raster-opacity": 0.85, "raster-resampling": "linear" } })
      map.addLayer({ id: "states", type: "line", source: "omt", "source-layer": "boundary",
        filter: ["all", ["==", ["get", "admin_level"], 4], ["!=", ["get", "maritime"], 1]],
        paint: { "line-color": "#ffffff", "line-opacity": 0.5, "line-width": 1.2 } })
      map.addLayer({ id: "roads", type: "line", source: "omt", "source-layer": "transportation", minzoom: 9,
        filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary"]]],
        paint: { "line-color": "#f4efe4", "line-opacity": 0.45, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.6, 14, 2.5] } })
      map.addLayer({ id: "buildings", type: "fill-extrusion", source: "omt", "source-layer": "building", minzoom: 13,
        paint: { "fill-extrusion-color": "#e3ddd0", "fill-extrusion-opacity": 0.9,
          "fill-extrusion-height": ["coalesce", ["get", "render_height"], 6], "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0] } })
      map.addSource("wind", { type: "geojson", data: { type: "FeatureCollection", features: [] } })
      map.addLayer({ id: "wind", type: "line", source: "wind", layout: { "line-cap": "round" },
        paint: { "line-color": "#ffffff", "line-opacity": 0.65, "line-width": ["interpolate", ["linear"], ["get", "speed"], 0, 0.5, 10, 2.2] } })
      map.addSource("fires", { type: "geojson", data: { type: "FeatureCollection", features: [] } })
      map.addLayer({ id: "fires", type: "circle", source: "fires",
        paint: { "circle-color": "#ff6a1a", "circle-blur": 0.6, "circle-opacity": 0.9,
          "circle-radius": ["interpolate", ["linear"], ["sqrt", ["max", ["get", "frp"], 0]], 0, 2, 30, 10] } })
      map.addSource("monitors", { type: "geojson", data: { type: "FeatureCollection", features: [] } })
      map.addLayer({ id: "monitors", type: "circle", source: "monitors", minzoom: 6,
        paint: { "circle-radius": 3.5, "circle-color": "#ffffff", "circle-stroke-color": "#102321", "circle-stroke-width": 1 } })
      map.addLayer({ id: "places", type: "symbol", source: "omt", "source-layer": "place",
        filter: ["in", ["get", "class"], ["literal", ["city", "town", "village"]]],
        layout: { "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]], "text-font": ["Noto Sans Regular"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 5, 11, 10, 15] },
        paint: { "text-color": "#ffffff", "text-halo-color": "#091615", "text-halo-width": 1.4 } })
      setReady(true)
    })
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [canvas])

  // ---- data for the mode ----
  useEffect(() => {
    let cancelled = false
    loadWorld(mode).then(d => { if (!cancelled) { setData(d); setHour(h => Math.min(h, d.hours - 1)) } })
    return () => { cancelled = true }
  }, [mode])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready || !data) return
    ;(map.getSource("fires") as maplibregl.GeoJSONSource).setData({ type: "FeatureCollection", features: data.fires.map(([lat, lon, frp]) => (
      { type: "Feature", properties: { frp }, geometry: { type: "Point", coordinates: [lon, lat] } })) })
    ;(map.getSource("monitors") as maplibregl.GeoJSONSource).setData({ type: "FeatureCollection", features: data.points.flatMap(([lat, lon, kind], i) => (
      kind === 1 ? [{ type: "Feature" as const, properties: { i }, geometry: { type: "Point" as const, coordinates: [lon, lat] } }] : [])) })
  }, [ready, data])

  // ---- redraw smoke and wind for the hour ----
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready || !data) return
    drawSmoke(canvas, data, which, hour)
    ;(map.getSource("wind") as maplibregl.GeoJSONSource).setData(windFeatures(data, hour))
  }, [ready, data, which, hour, canvas])

  // ---- play ----
  useEffect(() => {
    if (!playing || !data) return
    const t = setInterval(() => setHour(h => (h + 1) % data.hours), Number(speed))
    return () => clearInterval(t)
  }, [playing, speed, data])

  // ---- click a place ----
  const onClick = useCallback((e: maplibregl.MapMouseEvent) => {
    if (!data) return
    const p = nearestPoint(data, e.lngLat.lng, e.lngLat.lat)
    setPicked(p >= 0 ? p : null)
  }, [data])
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.on("click", onClick)
    return () => { map.off("click", onClick) }
  }, [onClick])

  const changeMode = (m: Mode) => {
    setMode(m); setHour(0); setPicked(null)
    if (m === "aug2023") mapRef.current?.flyTo({ center: [-121.5, 45.6], zoom: 5.8, pitch: 55, bearing: -10, duration: 2500 })
  }

  const series = useMemo(() => {
    if (!data || picked === null) return []
    return Array.from({ length: data.hours }, (_, h) => ({
      h, label: localTime(data, h), serein: valueAt(data, "serein", picked, h), noaa: valueAt(data, "noaa", picked, h) }))
  }, [data, picked])
  const now = data && picked !== null ? valueAt(data, which, picked, hour) : null

  return (
    <div className="dark fixed inset-0 bg-background text-foreground">
      <div ref={mapEl} style={{ position: "absolute", inset: 0 }} role="application" aria-label="3D map of the western US with the smoke forecast" />

      <header className="absolute inset-x-3 top-3 z-10 flex flex-wrap items-center gap-3 rounded-2xl border bg-background/80 px-4 py-2.5 backdrop-blur">
        <Wordmark className="text-2xl text-primary" />
        <span className="font-medium">Smoke World</span>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Select value={mode} onValueChange={v => changeMode(v as Mode)}>
            <SelectTrigger className="w-[260px]" aria-label="Forecast"><SelectValue /></SelectTrigger>
            <SelectContent>{Object.entries(MODES).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
          </Select>
          <ToggleGroup type="single" value={which} onValueChange={v => v && setWhich(v as Which)} variant="outline" aria-label="Which forecast">
            <ToggleGroupItem value="serein" className="px-4">Serein</ToggleGroupItem>
            <ToggleGroupItem value="noaa" className="px-4">NOAA</ToggleGroupItem>
          </ToggleGroup>
          <Popover>
            <PopoverTrigger asChild><Button variant="ghost" size="icon" aria-label="About this map"><Info /></Button></PopoverTrigger>
            <PopoverContent className="w-96 text-sm">
              <p className="font-medium">Where this comes from</p>
              <p className="mt-2 text-muted-foreground">{data?.source}</p>
              <p className="mt-2 text-muted-foreground">Smoke detail is about 25 km: two places in the same square get the same number. The daily level is SmokeCast's tested forecast; the hour-to-hour movement is NOAA's pattern, which did not prove reliable at saying which hours are worst. Terrain, photos, roads and buildings are context only.</p>
              <p className="mt-2 text-muted-foreground">Map: imagery USGS The National Map; terrain AWS Terrain Tiles (USGS 3DEP and others); places, roads and buildings © OpenStreetMap contributors via OpenFreeMap; engine MapLibre GL JS.</p>
              <Button asChild variant="link" className="mt-1 px-0"><Link to="/about">All sources and methods</Link></Button>
            </PopoverContent>
          </Popover>
          <Button asChild variant="secondary" size="sm"><Link to="/">Back to site</Link></Button>
        </div>
      </header>

      <Card className="absolute right-3 top-20 z-10 hidden w-64 bg-background/80 backdrop-blur md:block">
        <CardContent className="space-y-1.5 p-4 text-sm">
          {AQI.map(a => (
            <div key={a.name} className="flex items-center gap-2">
              <span className="size-3 rounded-sm" style={{ background: `rgb(${a.rgb.join(",")})` }} />{a.name}
            </div>
          ))}
          <p className="pt-2 text-xs text-muted-foreground">
            {mode === "live" ? `Live forecast issued ${data?.issue_date ?? ""}. Click anywhere for that place.` : "Forecast issued Aug 18, 2023, during a major Pacific Northwest smoke event."}
          </p>
        </CardContent>
      </Card>

      {picked !== null && data && (
        <Card className="absolute bottom-28 left-3 top-20 z-10 w-[min(400px,calc(100%-24px))] overflow-y-auto bg-background/90 backdrop-blur">
          <CardContent className="space-y-4 p-5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <Badge variant="secondary">{data.points[picked][2] === 1 ? "EPA air monitor" : "Forecast square, about 25 km"}</Badge>
                <div className="mt-1 text-xs text-muted-foreground">{data.points[picked][0].toFixed(2)}, {data.points[picked][1].toFixed(2)}</div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setPicked(null)} aria-label="Close"><X /></Button>
            </div>
            <div>
              <div className="font-serif text-5xl">{now === null ? "No data" : `${now} µg/m³`}</div>
              <div className="text-sm text-muted-foreground">{now === null ? "" : aqiOf(now).name} · {localTime(data, hour)} · {which === "serein" ? "Serein" : "NOAA"}</div>
            </div>
            {data.daily && (
              <div className="grid grid-cols-4 gap-2 rounded-xl border p-3 text-center">
                {data.daily.map(d => {
                  const q50 = d.q50[picked], q05 = d.q05[picked], q95 = d.q95[picked]
                  return (
                    <div key={d.lead}>
                      <div className="text-[0.7rem] uppercase tracking-wide text-muted-foreground">{["Today", "Tomorrow", "Day 2", "Day 3"][d.lead] ?? `Day ${d.lead}`}</div>
                      <div className="font-serif text-2xl">{q50 ?? "–"}</div>
                      <div className="text-[0.7rem] text-muted-foreground">{q05 !== null && q95 !== null ? `${q05}-${q95}` : ""}</div>
                    </div>
                  )
                })}
                <div className="col-span-4 text-left text-xs text-muted-foreground">SmokeCast's tested daily forecast, µg/m³, with its 90% range. The chart below is the untested hour-by-hour pattern.</div>
              </div>
            )}
            <ChartContainer config={chartConfig} className="h-40 w-full">
              <ComposedChart data={series} margin={{ left: -18, right: 6, top: 6 }}>
                <XAxis dataKey="h" tickFormatter={h => (h % 24 === 0 ? `+${h}h` : "")} tickLine={false} axisLine={false} interval={0} fontSize={11} />
                <YAxis tickLine={false} axisLine={false} fontSize={11} />
                <ReferenceLine y={35.5} stroke="var(--aqi-usg)" strokeDasharray="4 3" />
                <ReferenceLine x={hour} stroke="#fff" />
                <Area dataKey="serein" type="monotone" fill="var(--color-serein)" fillOpacity={0.18} stroke="var(--color-serein)" strokeWidth={2.5} connectNulls />
                <Line dataKey="noaa" type="monotone" stroke="var(--color-noaa)" strokeWidth={1.5} dot={false} connectNulls />
                <ChartTooltip content={<ChartTooltipContent labelFormatter={(_, p) => (p?.[0]?.payload as { label: string })?.label} />} />
              </ComposedChart>
            </ChartContainer>
            <p className="text-xs text-muted-foreground">Dashed line: unhealthy for sensitive groups (35.5 µg/m³).</p>
            <PersonPanel data={data} point={picked} which={which} />
          </CardContent>
        </Card>
      )}

      <div className="absolute bottom-4 left-1/2 z-10 flex w-[min(940px,calc(100%-24px))] -translate-x-1/2 items-center gap-4 rounded-2xl border bg-background/85 px-4 py-3 backdrop-blur">
        <Button size="icon" className="size-11 rounded-full" onClick={() => setPlaying(p => !p)} aria-label={playing ? "Pause" : "Play"}>
          {playing ? <Pause /> : <Play />}
        </Button>
        <Slider className="flex-1" min={0} max={(data?.hours ?? 72) - 1} step={1} value={[hour]}
          onValueChange={([v]) => { setPlaying(false); setHour(v) }} aria-label="Forecast hour" />
        <div className="min-w-44 text-right">
          <div className="font-medium">{data ? localTime(data, hour) : ""}</div>
          <div className="text-xs text-muted-foreground">Hour {hour + 1} of {data?.hours ?? 72}{hour > 48 ? " · no wind after hour 48" : ""}</div>
        </div>
        <Select value={speed} onValueChange={setSpeed}>
          <SelectTrigger className="w-20" aria-label="Speed"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="900">1x</SelectItem><SelectItem value="450">2x</SelectItem><SelectItem value="200">4x</SelectItem></SelectContent>
        </Select>
      </div>
    </div>
  )
}
