import { createRoot } from "react-dom/client"
import { PanelTabs, type Panel } from "./islands/PanelTabs"
import type { Horizon } from "./islands/RmseBars"
import { FigureViewer } from "./islands/FigureViewer"
import { setupCountUp } from "./countUp"
import "./islands.css"

function readNumber(panel: Element, label: RegExp) {
  const dt = [...panel.querySelectorAll("dt")].find(d => label.test(d.textContent ?? ""))
  const value = Number.parseFloat(dt?.nextElementSibling?.textContent?.replace(/,/g, "") ?? "")
  return Number.isFinite(value) ? value : undefined
}

function readHorizon(panel: Element): Horizon | undefined {
  const smokecast = readNumber(panel, /SmokeCast RMSE/)
  const fallback = readNumber(panel, /Fallback RMSE/)
  return smokecast !== undefined && fallback !== undefined ? { smokecast, fallback } : undefined
}

// The static switchers stay the source of truth: content is read from the
// HTML, so the page still works if this script never loads.
for (const group of document.querySelectorAll<HTMLElement>("[data-switcher]")) {
  const buttons = [...group.querySelectorAll<HTMLButtonElement>("button[data-panel]")]
  const panels: Panel[] = []
  for (const button of buttons) {
    const el = group.querySelector<HTMLElement>(`#${CSS.escape(button.dataset.panel ?? "")}`)
    if (!el) break
    panels.push({
      id: el.id,
      label: button.textContent?.trim() ?? el.id,
      lang: button.lang || undefined,
      className: el.className,
      html: el.innerHTML,
      horizon: readHorizon(el),
    })
  }
  if (!panels.length || panels.length !== buttons.length) continue

  const initial = buttons.find(b => b.getAttribute("aria-pressed") === "true")?.dataset.panel ?? panels[0].id
  const ariaLabel = group.querySelector(".switch-controls")?.getAttribute("aria-label") ?? "Options"
  const tone = group.closest(".dark") ? "dark" : "light"

  // Render beside the static switcher and only remove it once React has
  // mounted, so a failed render leaves the working HTML version in place.
  const mount = document.createElement("div")
  mount.className = group.className
  mount.dataset.enhanced = "react"
  group.after(mount)
  createRoot(mount).render(
    <PanelTabs panels={panels} initial={initial} ariaLabel={ariaLabel} tone={tone} onMounted={() => group.remove()} />
  )
}

// Charts mount into [data-island] slots. The slot keeps its static figure
// until React replaces it, so the image stays if this script fails.
// Chart code loads only on pages that have a chart.
const islands = {
  "forecast-explorer": () => import("./islands/ForecastExplorer").then(m => m.ForecastExplorer),
  "checkin-explorer": () => import("./islands/CheckinExplorer").then(m => m.CheckinExplorer),
}
for (const slot of document.querySelectorAll<HTMLElement>("[data-island]")) {
  const load = islands[slot.dataset.island as keyof typeof islands]
  if (load) load().then(Island => createRoot(slot).render(<Island />))
}

const figureLinks = [...document.querySelectorAll<HTMLAnchorElement>('.figure-frame > a[href$=".png"]')]
if (figureLinks.length) {
  const host = document.body.appendChild(document.createElement("div"))
  createRoot(host).render(<FigureViewer links={figureLinks} />)
}

setupCountUp()
