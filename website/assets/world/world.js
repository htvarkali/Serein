// Serein Smoke World: the hour-by-hour smoke forecast on a 3D map of the western US.
// Open data only, no accounts: USGS aerial imagery, AWS terrain tiles, OpenFreeMap
// (OpenStreetMap) for places and buildings, MapLibre GL JS as the engine. The smoke
// values come from assets/world/<mode>.json, made by `python -m serein.world`.
(function () {
  "use strict";
  const GRID = { lat0: 32, lon0: -125, step: 0.25, rows: 69, cols: 45 };
  const BOX = { west: -125, east: -114, south: 32, north: 49 };
  const CANVAS_SCALE = 8;
  const AQI = [[9.0, [76, 175, 80]], [35.4, [246, 211, 45]], [55.4, [240, 136, 62]],
               [125.4, [229, 72, 77]], [225.4, [142, 78, 198]], [Infinity, [125, 31, 44]]];
  const AQI_NAMES = ["Good", "Moderate", "Unhealthy for sensitive groups", "Unhealthy", "Very unhealthy", "Hazardous"];
  const aqiIndex = (v) => Math.max(0, AQI.findIndex(([hi]) => v <= hi));

  const state = { mode: "live", which: "serein", hour: 0, data: {}, timer: null };
  const $ = (id) => document.getElementById(id);

  // ---------- data ----------
  async function load(mode) {
    if (!state.data[mode]) {
      const d = await fetch(`assets/world/${mode}.json`).then((r) => r.json());
      d.grid = new Int32Array(GRID.rows * GRID.cols).fill(-1);
      d.points.forEach(([lat, lon, kind], i) => {
        if (kind !== 0) return;
        const r = Math.round((lat - GRID.lat0) / GRID.step), c = Math.round((lon - GRID.lon0) / GRID.step);
        if (r >= 0 && r < GRID.rows && c >= 0 && c < GRID.cols) d.grid[r * GRID.cols + c] = i;
      });
      state.data[mode] = d;
    }
    return state.data[mode];
  }
  const value = (d, which, p, h) => d[which][p * d.hours + h];

  // ---------- smoke canvas (rows spaced in Web Mercator so the image sits correctly) ----------
  const canvas = document.createElement("canvas");
  canvas.width = (GRID.cols - 1) * CANVAS_SCALE;
  canvas.height = (GRID.rows - 1) * CANVAS_SCALE;
  const ctx = canvas.getContext("2d");
  const mercY = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  const rowLat = new Float64Array(canvas.height);
  for (let y = 0; y < canvas.height; y++) {
    const t = y / (canvas.height - 1);
    const m = mercY(BOX.north) + (mercY(BOX.south) - mercY(BOX.north)) * t;
    rowLat[y] = (Math.atan(Math.exp(m)) - Math.PI / 4) * 360 / Math.PI;
  }

  function drawSmoke(d) {
    const img = ctx.createImageData(canvas.width, canvas.height);
    const px = img.data, W = canvas.width;
    const g = (r, c) => {
      const p = d.grid[r * GRID.cols + c];
      if (p === undefined || p < 0) return null;
      const v = value(d, state.which, p, state.hour);
      return v === undefined ? null : v;
    };
    for (let y = 0; y < canvas.height; y++) {
      const fr = Math.min(Math.max((rowLat[y] - GRID.lat0) / GRID.step, 0), GRID.rows - 1);
      const r0 = Math.min(Math.floor(fr), GRID.rows - 2), ty = fr - r0;
      for (let x = 0; x < W; x++) {
        const fc = x / CANVAS_SCALE, c0 = Math.min(Math.floor(fc), GRID.cols - 2), tx = fc - c0;
        const a = g(r0, c0), b = g(r0, c0 + 1), c = g(r0 + 1, c0), e = g(r0 + 1, c0 + 1);
        if (a === null || b === null || c === null || e === null) continue;
        const v = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + e * tx) * ty;
        if (v < 6) continue;                                       // clean air stays clear
        const col = AQI[aqiIndex(v)][1];
        const alpha = Math.min(0.82, 0.12 + v / 90);
        const k = (y * W + x) * 4;
        px[k] = col[0]; px[k + 1] = col[1]; px[k + 2] = col[2]; px[k + 3] = alpha * 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  // ---------- wind and fires ----------
  function windGeoJSON(d) {
    const feats = [];
    if (!d.wind_hours.length) return { type: "FeatureCollection", features: feats };
    let j = -1;
    d.wind_hours.forEach((h, k) => { if (h <= state.hour + 1.5 && Math.abs(h - state.hour) <= 1.5) j = k; });
    if (j < 0) return { type: "FeatureCollection", features: feats };
    const nh = d.wind_hours.length;
    for (let r = 0; r < GRID.rows; r += 3) {
      for (let c = 0; c < GRID.cols; c += 3) {
        const p = d.grid[r * GRID.cols + c];
        if (p < 0) continue;
        const u = d.u[p * nh + j], v = d.v[p * nh + j];
        if (u === null || v === null) continue;
        const [lat, lon] = d.points[p];
        const s = 0.045;                                           // degrees per m/s, for drawing only
        feats.push({ type: "Feature", properties: { speed: Math.hypot(u, v) },
          geometry: { type: "LineString", coordinates: [[lon, lat], [lon + u * s / Math.cos(lat * Math.PI / 180), lat + v * s]] } });
      }
    }
    return { type: "FeatureCollection", features: feats };
  }

  const fireGeoJSON = (d) => ({ type: "FeatureCollection", features: d.fires.map(([lat, lon, frp]) => (
    { type: "Feature", properties: { frp }, geometry: { type: "Point", coordinates: [lon, lat] } })) });
  const monitorGeoJSON = (d) => ({ type: "FeatureCollection", features: d.points.flatMap(([lat, lon, kind], i) => (
    kind === 1 ? [{ type: "Feature", properties: { i }, geometry: { type: "Point", coordinates: [lon, lat] } }] : [])) });

  // ---------- clock ----------
  function updateClock(d) {
    const t = new Date(Date.parse(d.start_utc) + state.hour * 3600e3);
    $("w-when").textContent = t.toLocaleString("en-US", { timeZone: "America/Los_Angeles", weekday: "short", month: "short", day: "numeric", hour: "numeric" }) + " PT";
    $("w-offset").textContent = `Hour ${state.hour + 1} of ${d.hours}, forecast issued ${d.issue_date}` + (state.hour > 48 ? " (no wind forecast after hour 48)" : "");
  }

  // ---------- popup for a clicked place ----------
  function nearestPoint(d, lng, lat) {
    let best = -1, bd = Infinity;
    const k = Math.cos(lat * Math.PI / 180);
    d.points.forEach(([la, lo], i) => {
      const dd = (la - lat) ** 2 + ((lo - lng) * k) ** 2;
      if (dd < bd) { bd = dd; best = i; }
    });
    return Math.sqrt(bd) < 0.4 ? best : -1;
  }

  function advice(maxV) {
    if (maxV >= 125.5) return "Very unhealthy smoke likely. Everyone should limit time outside; outdoor workers need respirators and indoor or filtered work.";
    if (maxV >= 55.5) return "Unhealthy smoke likely. Move strenuous outdoor work and play to cleaner hours or indoors; have N95s ready.";
    if (maxV >= 35.5) return "Unhealthy for sensitive groups at times. People with asthma, children and older adults should shorten time outdoors.";
    return "No smoke action expected. Keep checking the current AQI.";
  }

  function sparkline(d, p) {
    const W = 300, H = 90, n = d.hours;
    const s = [], o = [];
    for (let h = 0; h < n; h++) { s.push(value(d, "serein", p, h)); o.push(value(d, "noaa", p, h)); }
    const top = Math.max(40, ...s.filter((v) => v !== null), ...o.filter((v) => v !== null));
    const path = (arr) => arr.map((v, h) => v === null ? "" : `${h && arr[h - 1] !== null ? "L" : "M"}${(h / (n - 1) * W).toFixed(1)},${(H - v / top * (H - 6)).toFixed(1)}`).join("");
    const y35 = (H - 35.5 / top * (H - 6)).toFixed(1);
    const xNow = (state.hour / (n - 1) * W).toFixed(1);
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="72-hour smoke forecast">
      <line x1="0" x2="${W}" y1="${y35}" y2="${y35}" stroke="#f0883e" stroke-dasharray="4 3" stroke-width="1"/>
      <path d="${path(o)}" fill="none" stroke="#9fb3ad" stroke-width="1.5"/>
      <path d="${path(s)}" fill="none" stroke="#c4e2b9" stroke-width="2.5"/>
      <line x1="${xNow}" x2="${xNow}" y1="0" y2="${H}" stroke="#fff" stroke-width="1"/></svg>
      <div style="font-size:.75rem;color:#c4e2b9">Green: Serein. Grey: NOAA. Dashed: unhealthy for sensitive groups (35.5).</div>`;
  }

  function showPopup(map, d, p, lngLat) {
    const [lat, lon, kind] = d.points[p];
    const now = value(d, state.which, p, state.hour);
    const series = [];
    for (let h = 0; h < d.hours; h++) series.push(value(d, state.which, p, h));
    const maxV = Math.max(...series.filter((v) => v !== null));
    const html = `<div class="w-pop"><h4>${kind === 1 ? "EPA air monitor" : "Forecast square (about 25 km)"}</h4>
      <div style="color:#c4e2b9;font-size:.8rem">${lat.toFixed(2)}, ${lon.toFixed(2)}</div>
      <div class="w-now">${now === null ? "No data" : `${now} µg/m³`}</div>
      <div>${now === null ? "" : AQI_NAMES[aqiIndex(now)]} at this hour (${state.which === "serein" ? "Serein" : "NOAA"})</div>
      ${sparkline(d, p)}
      <div class="w-advice">Next 3 days: ${advice(maxV)}</div></div>`;
    new maplibregl.Popup({ maxWidth: "340px" }).setLngLat(lngLat).setHTML(html).addTo(map);
  }

  // ---------- map ----------
  async function main() {
    const map = new maplibregl.Map({
      container: "map",
      center: [-120.6, 41.2], zoom: 5.1, pitch: 52, bearing: -8, maxPitch: 80,
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
          omt: { type: "vector", url: "https://tiles.openfreemap.org/planet",
            attribution: "&copy; OpenStreetMap contributors, OpenFreeMap" },
        },
        layers: [
          { id: "photo", type: "raster", source: "photo", paint: { "raster-saturation": -0.15 } },
        ],
        sky: { "sky-color": "#9ec6e6", "horizon-color": "#e9e3cf", "fog-color": "#d7d2c4", "sky-horizon-blend": 0.6, "horizon-fog-blend": 0.6, "fog-ground-blend": 0.4 },
      },
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "imperial" }), "bottom-left");

    await new Promise((ok) => map.on("load", ok));
    map.setTerrain({ source: "dem", exaggeration: 1.4 });

    map.addSource("smoke", { type: "canvas", canvas, animate: true,
      coordinates: [[BOX.west, BOX.north], [BOX.east, BOX.north], [BOX.east, BOX.south], [BOX.west, BOX.south]] });
    map.addLayer({ id: "smoke", type: "raster", source: "smoke", paint: { "raster-opacity": 0.85, "raster-resampling": "linear" } });
    map.addLayer({ id: "states", type: "line", source: "omt", "source-layer": "boundary",
      filter: ["all", ["==", ["get", "admin_level"], 4], ["!=", ["get", "maritime"], 1]],
      paint: { "line-color": "#ffffff", "line-opacity": 0.55, "line-width": 1.2 } });
    map.addLayer({ id: "buildings", type: "fill-extrusion", source: "omt", "source-layer": "building", minzoom: 13,
      paint: { "fill-extrusion-color": "#d8d2c4", "fill-extrusion-opacity": 0.85,
        "fill-extrusion-height": ["coalesce", ["get", "render_height"], 6],
        "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0] } });
    map.addSource("wind", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: "wind", type: "line", source: "wind",
      paint: { "line-color": "#ffffff", "line-opacity": 0.7, "line-width": ["interpolate", ["linear"], ["get", "speed"], 0, 0.6, 10, 2.2] } });
    map.addSource("fires", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: "fires", type: "circle", source: "fires",
      paint: { "circle-color": "#ff6a1a", "circle-blur": 0.5, "circle-opacity": 0.9,
        "circle-radius": ["interpolate", ["linear"], ["sqrt", ["max", ["get", "frp"], 0]], 0, 2, 30, 9] } });
    map.addSource("monitors", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: "monitors", type: "circle", source: "monitors", minzoom: 6,
      paint: { "circle-radius": 3.5, "circle-color": "#ffffff", "circle-stroke-color": "#102321", "circle-stroke-width": 1 } });
    map.addLayer({ id: "places", type: "symbol", source: "omt", "source-layer": "place",
      filter: ["in", ["get", "class"], ["literal", ["city", "town"]]],
      layout: { "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]], "text-font": ["Noto Sans Regular"],
        "text-size": ["interpolate", ["linear"], ["zoom"], 5, 11, 10, 15] },
      paint: { "text-color": "#ffffff", "text-halo-color": "#091615", "text-halo-width": 1.4 } });

    async function refresh(full) {
      const d = await load(state.mode);
      if (full) {
        $("w-hour").max = String(d.hours - 1);
        state.hour = Math.min(state.hour, d.hours - 1);
        map.getSource("fires").setData(fireGeoJSON(d));
        map.getSource("monitors").setData(monitorGeoJSON(d));
        $("w-source").textContent = d.source;
        $("w-note").textContent = state.mode === "live"
          ? `Live forecast issued ${d.issue_date}. Press play to watch the next 72 hours.`
          : "Example: the forecast issued on August 18, 2023, during a major Pacific Northwest smoke event.";
      }
      drawSmoke(d);
      map.getSource("wind").setData(windGeoJSON(d));
      updateClock(d);
      $("w-hour").value = String(state.hour);
    }

    map.on("click", async (e) => {
      const d = await load(state.mode);
      const p = nearestPoint(d, e.lngLat.lng, e.lngLat.lat);
      if (p >= 0) showPopup(map, d, p, e.lngLat);
    });
    $("w-hour").addEventListener("input", () => { state.hour = Number($("w-hour").value); refresh(false); });
    $("w-mode").addEventListener("change", () => {
      state.mode = $("w-mode").value; state.hour = 0;
      if (state.mode === "aug2023") map.flyTo({ center: [-121.5, 45.6], zoom: 5.8, pitch: 55, bearing: -10, duration: 2500 });
      refresh(true);
    });
    for (const which of ["serein", "noaa"]) {
      $(`w-${which}`).addEventListener("click", () => {
        state.which = which;
        $("w-serein").setAttribute("aria-pressed", String(which === "serein"));
        $("w-noaa").setAttribute("aria-pressed", String(which === "noaa"));
        refresh(false);
      });
    }
    const play = $("w-play");
    function stop() { clearInterval(state.timer); state.timer = null; play.innerHTML = "&#9654;"; play.setAttribute("aria-label", "Play"); }
    play.addEventListener("click", () => {
      if (state.timer) return stop();
      play.innerHTML = "&#10074;&#10074;"; play.setAttribute("aria-label", "Pause");
      state.timer = setInterval(async () => {
        const d = await load(state.mode);
        state.hour = (state.hour + 1) % d.hours; refresh(false);
      }, Number($("w-speed").value));
    });
    $("w-speed").addEventListener("change", () => { if (state.timer) { stop(); play.click(); } });

    const mode = new URLSearchParams(location.search).get("mode");
    if (mode === "aug2023") { $("w-mode").value = "aug2023"; state.mode = "aug2023"; map.jumpTo({ center: [-121.5, 45.6], zoom: 5.8, pitch: 55, bearing: -10 }); }
    const hour = Number(new URLSearchParams(location.search).get("hour"));
    if (Number.isFinite(hour) && hour > 0) state.hour = hour;
    refresh(true);
  }
  document.addEventListener("DOMContentLoaded", main);
})();
