// Smoke replay: three synced oblique 3D views of the same monitors (NOAA forecast,
// Serein forecast, measured). Column height = daily PM2.5, color = AQI level.
// Plain canvas, no external libraries; every value comes from aug2023.json.
(function () {
  const PANELS = ["noaa", "serein", "observed"];
  const BOX = { lonMin: -125, lonMax: -110.5, latMin: 41.3, latMax: 49.2 };
  const COLORS = [[9.0, "#4caf50"], [35.4, "#f6d32d"], [55.4, "#f0883e"], [125.4, "#e5484d"], [225.4, "#8e4ec6"], [Infinity, "#7d1f2c"]];
  const color = (v) => COLORS.find(([hi]) => v <= hi)[1];

  function project(canvas, lat, lon) {
    // Oblique view: the map plane is squashed vertically and tilted away from the viewer.
    const w = canvas.width, h = canvas.height;
    const x = (lon - BOX.lonMin) / (BOX.lonMax - BOX.lonMin);
    const y = (lat - BOX.latMin) / (BOX.latMax - BOX.latMin);
    const depth = 0.62 + 0.38 * (1 - y);           // nearer rows (south) look wider
    return { x: w * (0.5 + (x - 0.5) * depth * 1.02), y: h * (0.97 - y * 0.52), s: depth };
  }

  function drawStates(ctx, canvas, states) {
    ctx.strokeStyle = "rgba(196,226,185,.45)";
    ctx.fillStyle = "rgba(196,226,185,.06)";
    ctx.lineWidth = 1;
    for (const f of states.features) {
      const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
      for (const poly of polys) {
        ctx.beginPath();
        poly[0].forEach(([lon, lat], i) => {
          const p = project(canvas, Math.max(BOX.latMin - 1, Math.min(lat, BOX.latMax + 1)), lon);
          i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y);
        });
        ctx.fill(); ctx.stroke();
      }
    }
  }

  function drawColumns(ctx, canvas, monitors, values) {
    const order = monitors.map((m, i) => i).filter((i) => values[i] !== null)
      .filter((i) => monitors[i][0] >= BOX.latMin && monitors[i][0] <= BOX.latMax && monitors[i][1] >= BOX.lonMin && monitors[i][1] <= BOX.lonMax)
      .sort((a, b) => monitors[b][0] - monitors[a][0]);   // draw far (north) first
    for (const i of order) {
      const v = values[i];
      const p = project(canvas, monitors[i][0], monitors[i][1]);
      const height = Math.min(v, 300) * 0.75 * p.s;
      const half = 3.4 * p.s;
      ctx.fillStyle = color(v);
      ctx.fillRect(p.x - half, p.y - height, half * 2, height);
      ctx.fillStyle = "rgba(0,0,0,.25)";
      ctx.fillRect(p.x, p.y - height, half, height);      // shaded side for depth
      ctx.fillStyle = "rgba(255,255,255,.35)";
      ctx.fillRect(p.x - half, p.y - height - 1.5 * p.s, half * 2, 1.5 * p.s);
    }
  }

  async function main() {
    const [data, states] = await Promise.all([
      fetch("assets/replay/aug2023.json").then((r) => r.json()),
      fetch("assets/replay/states.geojson").then((r) => r.json()),
    ]);
    const days = Object.keys(data.days).sort();
    const slider = document.getElementById("replay-slider");
    const label = document.getElementById("replay-day");
    const play = document.getElementById("replay-play");
    slider.max = String(days.length - 1);

    function render(k) {
      const day = days[k], d = data.days[day], s = d.summary;
      label.textContent = new Date(day + "T12:00:00Z").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
      document.getElementById("replay-observed").textContent = `${s.unhealthy_monitors} monitors reached unhealthy-for-sensitive levels or worse.`;
      document.getElementById("replay-serein").textContent = `Flagged ${s.serein_warned} of ${s.unhealthy_monitors} a day ahead.`;
      document.getElementById("replay-noaa").textContent = `Flagged ${s.noaa_warned} of ${s.unhealthy_monitors} a day ahead.`;
      for (const name of PANELS) {
        const canvas = document.getElementById(`canvas-${name}`);
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawStates(ctx, canvas, states);
        drawColumns(ctx, canvas, data.monitors, d[name]);
      }
    }

    let timer = null;
    function stop() { clearInterval(timer); timer = null; play.textContent = "Play"; }
    play.addEventListener("click", () => {
      if (timer) return stop();
      play.textContent = "Pause";
      timer = setInterval(() => {
        const next = (Number(slider.value) + 1) % days.length;
        slider.value = String(next); render(next);
      }, 1400);
    });
    slider.addEventListener("input", () => { stop(); render(Number(slider.value)); });
    // ?day=2023-08-20 opens a given day (handy for links and recordings).
    const wanted = days.indexOf(new URLSearchParams(location.search).get("day"));
    const start = wanted >= 0 ? wanted : 0;
    slider.value = String(start);
    render(start);
  }
  document.addEventListener("DOMContentLoaded", main);
})();
