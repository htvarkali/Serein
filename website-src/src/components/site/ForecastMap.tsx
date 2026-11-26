import { useEffect, useRef, useState } from "react"
import type * as maplibregl from "maplibre-gl"
import type { FeatureCollection } from "geojson"
import "maplibre-gl/dist/maplibre-gl.css"
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url"
import { Button } from "@/components/ui/button"
import { BOX, drawSmoke, makeSmokeCanvas, windFeatures, type People, type Which, type WorldData } from "@/lib/world"

const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] }
type Phase = "loading" | "ready" | "unavailable"
type Coordinates = [number, number]

type Props = {
  data: WorldData | null
  which: Which
  hour: number
  playing: boolean
  people: People | null
  showPeople: boolean
  farOnly: boolean
  point: Coordinates | null
  focus: Coordinates | null
  onPick: (lng: number, lat: number) => void
}

function addMapLayers(map: maplibregl.Map, canvas: HTMLCanvasElement) {
  map.addSource("smoke", { type: "canvas", canvas, animate: false,
    coordinates: [[BOX.west, BOX.north], [BOX.east, BOX.north], [BOX.east, BOX.south], [BOX.west, BOX.south]] })
  map.addLayer({ id: "smoke", type: "raster", source: "smoke", paint: { "raster-opacity": 0.9, "raster-resampling": "linear" } }, "states")
  map.addSource("photo", { type: "raster", tileSize: 256, maxzoom: 16,
    tiles: ["https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"],
    attribution: "Imagery: USGS The National Map" })
  map.addLayer({ id: "photo", type: "raster", source: "photo", paint: { "raster-fade-duration": 200, "raster-saturation": -0.1 } }, "smoke")
  map.addSource("dem", { type: "raster-dem", encoding: "terrarium", tileSize: 256, maxzoom: 15,
    tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
    attribution: "Terrain: AWS Terrain Tiles (USGS 3DEP and others)" })
  map.setTerrain({ source: "dem", exaggeration: 1.4 })
  map.addSource("omt", { type: "vector", url: "https://tiles.openfreemap.org/planet", attribution: "© OpenStreetMap contributors, OpenFreeMap" })
  map.addLayer({ id: "roads", type: "line", source: "omt", "source-layer": "transportation", minzoom: 9,
    filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary"]]],
    paint: { "line-color": "#f4efe4", "line-opacity": 0.45, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.6, 14, 2.5] } })
  map.addLayer({ id: "buildings", type: "fill-extrusion", source: "omt", "source-layer": "building", minzoom: 13,
    paint: { "fill-extrusion-color": "#e3ddd0", "fill-extrusion-opacity": 0.9,
      "fill-extrusion-height": ["coalesce", ["get", "render_height"], 6], "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0] } })
  map.addSource("wind", { type: "geojson", data: EMPTY })
  map.addLayer({ id: "wind", type: "line", source: "wind", layout: { "line-cap": "round" },
    paint: { "line-color": "#ffffff", "line-opacity": 0.38, "line-width": ["interpolate", ["linear"], ["get", "speed"], 0, 0.5, 10, 2.2] } })
  map.addLayer({ id: "wind-flow", type: "line", source: "wind", layout: { "line-cap": "round", visibility: "none" },
    paint: { "line-color": "#ffffff", "line-opacity": 0.85, "line-width": ["interpolate", ["linear"], ["get", "speed"], 0, 0.8, 10, 2.6],
      "line-dasharray": [0, 4, 3] } })
  map.addSource("fires", { type: "geojson", data: EMPTY })
  map.addLayer({ id: "fires", type: "circle", source: "fires",
    paint: { "circle-color": "#ff6a1a", "circle-blur": 0.6, "circle-opacity": 0.9,
      "circle-radius": ["interpolate", ["linear"], ["sqrt", ["max", ["get", "frp"], 0]], 0, 2, 30, 10] } })
  map.addSource("monitors", { type: "geojson", data: EMPTY })
  map.addLayer({ id: "monitors", type: "circle", source: "monitors", minzoom: 6,
    paint: { "circle-radius": 3.5, "circle-color": "#ffffff", "circle-stroke-color": "#0b1222", "circle-stroke-width": 1 } })
  map.addSource("people", { type: "geojson", data: EMPTY })
  map.addLayer({ id: "people", type: "circle", source: "people", layout: { visibility: "none" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, ["*", 0.04, ["sqrt", ["get", "pop"]]], 10, ["*", 0.12, ["sqrt", ["get", "pop"]]]],
      "circle-color": ["match", ["get", "q"], 0, "#f2ba84", 1, "#e8c9a0", 2, "#d8d8c0", 3, "#b9d6c4", 4, "#8fc3b0", "#cccccc"],
      "circle-opacity": 0.75,
      "circle-stroke-color": ["case", [">=", ["get", "km"], 25], "#ff3b6b", "rgba(0,0,0,0)"],
      "circle-stroke-width": ["case", [">=", ["get", "km"], 25], 1.6, 0],
    } })
  map.addLayer({ id: "poi", type: "circle", source: "omt", "source-layer": "poi", minzoom: 11,
    filter: ["in", ["get", "class"], ["literal", ["school", "college", "hospital"]]],
    paint: { "circle-radius": 5, "circle-color": ["match", ["get", "class"], "hospital", "#ff5a5f", "#5b8def"],
      "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.2 } })
  map.addLayer({ id: "poi-labels", type: "symbol", source: "omt", "source-layer": "poi", minzoom: 13,
    filter: ["in", ["get", "class"], ["literal", ["school", "college", "hospital"]]],
    layout: { "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]], "text-font": ["Noto Sans Regular"], "text-size": 11, "text-offset": [0, 1.1], "text-anchor": "top" },
    paint: { "text-color": "#ffffff", "text-halo-color": "#0b1222", "text-halo-width": 1.2 } })
  map.addLayer({ id: "places", type: "symbol", source: "omt", "source-layer": "place",
    filter: ["in", ["get", "class"], ["literal", ["city", "town", "village"]]],
    layout: { "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]], "text-font": ["Noto Sans Regular"],
      "text-size": ["interpolate", ["linear"], ["zoom"], 5, 11, 10, 15] },
    paint: { "text-color": "#ffffff", "text-halo-color": "#0b1222", "text-halo-width": 1.4 } })
  map.addSource("picked", { type: "geojson", data: EMPTY })
  map.addLayer({ id: "picked", type: "circle", source: "picked",
    paint: { "circle-radius": 7, "circle-color": "#0b1222", "circle-stroke-color": "#fff5da", "circle-stroke-width": 3 } })
}

function setFeatures(map: maplibregl.Map, id: string, features: FeatureCollection) {
  map.getSource<maplibregl.GeoJSONSource>(id)?.setData(features)
}

export default function ForecastMap({ data, which, hour, playing, people, showPeople, farOnly, point, focus, onPick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [phase, setPhase] = useState<Phase>("loading")
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let active = true
    let map: maplibregl.Map | undefined
    setPhase("loading")
    const fail = () => {
      if (active) {
        window.clearTimeout(deadline)
        setPhase("unavailable")
      }
    }
    const deadline = window.setTimeout(fail, 10_000)
    import("maplibre-gl").then(maplibre => {
      if (!active) return
      maplibre.setWorkerUrl(workerUrl)
      const canvas = makeSmokeCanvas()
      canvasRef.current = canvas
      map = new maplibre.Map({
        container,
        center: [-120.1, 41.6], zoom: 4.7, pitch: 42, maxPitch: 70,
        scrollZoom: false, cooperativeGestures: true, maxTileCacheSize: 250, fadeDuration: 150,
        attributionControl: { compact: true },
        style: {
          version: 8,
          glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
          sources: { stateBoundaries: { type: "geojson", data: `${import.meta.env.BASE_URL}data/states.geojson`, attribution: "Boundaries: US Census Bureau" } },
          layers: [
            { id: "bg", type: "background", paint: { "background-color": "#0d1528" } },
            { id: "land", type: "fill", source: "stateBoundaries", paint: { "fill-color": "#1a2742" } },
            { id: "states", type: "line", source: "stateBoundaries", paint: { "line-color": "#c9a466", "line-opacity": 0.6, "line-width": 1.1 } },
          ],
        },
      })
      const current = map
      mapRef.current = current
      current.on("load", () => {
        if (!active) return
        window.clearTimeout(deadline)
        try {
          addMapLayers(current, canvas)
          current.addControl(new maplibre.NavigationControl({ visualizePitch: true }), "bottom-right")
          current.addControl(new maplibre.ScaleControl({ unit: "imperial" }), "bottom-left")
          current.getCanvas().style.cursor = "crosshair"
          // On a phone the open credits box covers about a fifth of the map. Start it
          // closed there; the (i) button still opens it.
          if (container.offsetWidth < 480) container.querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show")
          setPhase("ready")
        } catch {
          fail()
        }
      })
      current.on("webglcontextlost", fail)
    }).catch(fail)
    return () => {
      active = false
      window.clearTimeout(deadline)
      map?.remove()
      mapRef.current = null
      canvasRef.current = null
    }
  }, [attempt])

  useEffect(() => {
    const map = mapRef.current
    if (!map || phase !== "ready") return
    const click = (event: maplibregl.MapMouseEvent) => onPick(event.lngLat.lng, event.lngLat.lat)
    map.on("click", click)
    return () => { map.off("click", click) }
  }, [onPick, phase])

  useEffect(() => {
    const map = mapRef.current
    if (!map || phase !== "ready") return
    setFeatures(map, "fires", { type: "FeatureCollection", features: (data?.fires ?? []).map(([lat, lon, frp]) => (
      { type: "Feature", properties: { frp }, geometry: { type: "Point", coordinates: [lon, lat] } })) })
    setFeatures(map, "monitors", { type: "FeatureCollection", features: (data?.points ?? []).flatMap(([lat, lon, kind]) => (
      kind === 1 ? [{ type: "Feature" as const, properties: {}, geometry: { type: "Point" as const, coordinates: [lon, lat] } }] : [])) })
  }, [data, phase])

  useEffect(() => {
    const map = mapRef.current
    if (!map || phase !== "ready") return
    map.setLayoutProperty("people", "visibility", showPeople ? "visible" : "none")
    if (!showPeople || !people) return
    setFeatures(map, "people", { type: "FeatureCollection",
      features: people.tracts.filter(t => !farOnly || t[4] >= 25).map(([lat, lon, pop, q, km]) => (
        { type: "Feature", properties: { pop, q, km }, geometry: { type: "Point", coordinates: [lon, lat] } })) })
  }, [people, showPeople, farOnly, phase])

  useEffect(() => {
    const map = mapRef.current
    const canvas = canvasRef.current
    if (!map || !canvas || phase !== "ready") return
    if (data) drawSmoke(canvas, data, which, hour)
    else canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height)
    // Refresh the visible texture once. A continuously playing CanvasSource repaints even while paused.
    const smoke = map.getSource<maplibregl.CanvasSource>("smoke")
    smoke?.play()
    smoke?.pause()
    setFeatures(map, "wind", data ? windFeatures(data, hour) : EMPTY)
  }, [data, which, hour, phase])

  useEffect(() => {
    const map = mapRef.current
    if (!map || phase !== "ready") return
    setFeatures(map, "picked", point ? { type: "FeatureCollection", features: [
      { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: point } },
    ] } : EMPTY)
  }, [phase, point])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !focus || phase !== "ready") return
    map.easeTo({ center: focus, zoom: 5.9, duration: 450 })
  }, [focus, phase])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !playing || phase !== "ready") return
    let step = 0
    const dashes = [[0, 4, 3], [0.5, 4, 2.5], [1, 4, 2], [1.5, 4, 1.5], [2, 4, 1], [2.5, 4, 0.5], [3, 4, 0],
      [0, 0.5, 3, 3.5], [0, 1, 3, 3], [0, 1.5, 3, 2.5], [0, 2, 3, 2], [0, 2.5, 3, 1.5], [0, 3, 3, 1], [0, 3.5, 3, 0.5]]
    const update = () => {
      if (!map.getLayer("wind-flow")) return
      const animate = !document.hidden
      map.setLayoutProperty("wind-flow", "visibility", animate ? "visible" : "none")
      if (animate) map.setPaintProperty("wind-flow", "line-dasharray", dashes[step++ % dashes.length])
    }
    update()
    const interval = window.setInterval(update, 90)
    return () => {
      window.clearInterval(interval)
      if (map.getLayer("wind-flow")) map.setLayoutProperty("wind-flow", "visibility", "none")
    }
  }, [playing, phase])

  return (
    <div className="relative h-[clamp(19rem,52vh,37rem)] overflow-hidden bg-[#111a30]">
      {/* Inline position: maplibre-gl.css sets .maplibregl-map to position: relative, which
          beats Tailwind's layered "absolute" class and collapsed the map to 0 px tall. */}
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} inert={phase !== "ready"} />
      {phase !== "ready" && (
        <div className="absolute inset-0 grid place-items-center bg-[#0d1528] p-6 text-center">
          <div className="max-w-xs space-y-3" role="status">
            {phase === "loading" ? <p>Loading the terrain map…</p> : <>
              <p className="font-medium">The terrain map is unavailable.</p>
              <p className="text-sm text-muted-foreground">Choose a location to see its forecast.</p>
              <Button variant="outline" onClick={() => setAttempt(value => value + 1)}>Retry map</Button>
            </>}
          </div>
        </div>
      )}
    </div>
  )
}
