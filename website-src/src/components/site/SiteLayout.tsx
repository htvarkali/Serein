import { useEffect, useRef, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { ArrowUpRight, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { useSiteMotion } from "@/components/site/Motion"
import { team } from "@/data/site"
import { cn } from "@/lib/utils"

export const NAV = [
  { to: "/smokecast", label: "SmokeCast" },
  { to: "/world", label: "Forecast map", sup: "live" },
  { to: "/airplan", label: "AirPlan" },
  { to: "/about", label: "Data & methods" },
]

const REPO = "https://github.com/htvarkali/Serein"
const DOCS = `${REPO}/blob/main/docs`

/** Logo: a small tilted pill (the team name) over the project name. */
export function Wordmark({ className, onClick }: { className?: string; onClick?: () => void; tagline?: boolean }) {
  return (
    <Link to="/" onClick={onClick} className={cn("inline-flex flex-col items-start leading-none", className)} aria-label="Serein home">
      <span className="-rotate-6 rounded-full bg-current px-2 py-0.5 text-[0.55rem] font-semibold tracking-[0.06em] uppercase">
        <span className="pill-text text-[#0a0a0a]">Falcon Devs</span></span>
      <span className="-mt-0.5 text-[1.55rem] font-semibold tracking-[-0.03em] uppercase">Serein</span>
    </Link>
  )
}

function Initials({ name }: { name: string }) {
  return <span className="grid size-9 place-items-center rounded-full border-2 border-[#0a0a0a] bg-[#e7dfcc] text-[0.62rem] font-semibold text-[#0a0a0a]">
    {name.split(" ").map(part => part[0]).join("")}</span>
}

export function SiteLayout() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [onLight, setOnLight] = useState(false)
  const { pathname, hash } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const previousRoute = useRef(pathname)
  const menuNavigation = useRef(false)
  useSiteMotion()

  useEffect(() => {
    // The logo is white over dark sections and black over light ones: check what sits under it.
    const onScroll = () => {
      setScrolled(window.scrollY > 120)
      const under = document.elementsFromPoint(60, 40).find(el => !el.closest("header"))
      setOnLight(!!under && !under.closest(".dark"))
    }
    onScroll()
    // Lazy pages render a moment after navigation, so check again once they are in.
    const timers = [150, 500, 1200].map(ms => window.setTimeout(onScroll, ms))
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => { timers.forEach(window.clearTimeout); window.removeEventListener("scroll", onScroll) }
  }, [pathname])

  useEffect(() => {
    const routeChanged = previousRoute.current !== pathname
    previousRoute.current = pathname
    const frame = requestAnimationFrame(() => {
      const section = hash ? document.getElementById(hash.slice(1)) : null
      if (section) {
        section.scrollIntoView({ block: "start" })
        section.focus({ preventScroll: true })
      } else if (routeChanged) {
        window.scrollTo(0, 0)
        mainRef.current?.focus({ preventScroll: true })
      }
    })
    return () => cancelAnimationFrame(frame)
  }, [pathname, hash])

  function closeForNavigation() {
    menuNavigation.current = true
    setOpen(false)
  }

  return (
    <div className="min-h-screen">
      <a href="#main" onClick={event => {
        event.preventDefault()
        mainRef.current?.focus()
        mainRef.current?.scrollIntoView({ block: "start" })
      }} className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-card focus:px-4 focus:py-3">Skip to content</a>

      {/* Logo and links over the hero; after scrolling only a pill and a round menu button stay. */}
      <header className="pointer-events-none fixed inset-x-0 top-0 z-40">
        <div className="flex items-start justify-between px-[clamp(1.125rem,3vw,2.5rem)] pt-5">
          <div className="pointer-events-auto flex items-center gap-4">
            <Wordmark className={cn("transition-colors duration-300", onLight ? "text-[#0a0a0a] [&_.pill-text]:text-white" : "text-white")} />
            <Link to="/world" className={cn("inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-medium text-[#0a0a0a] shadow-lg transition-all duration-500 hover:bg-[#5b6cf6] hover:text-white",
              scrolled ? "translate-y-0 opacity-100" : "pointer-events-none -translate-y-3 opacity-0")}>
              See tomorrow’s forecast <span className="status-dot" />
            </Link>
          </div>
          <nav className={cn("pointer-events-auto hidden items-center gap-8 pt-2 text-[0.95rem] text-white transition-opacity duration-300 lg:flex", scrolled && "pointer-events-none opacity-0")} aria-label="Primary">
            {NAV.map(({ to, label, sup }) => (
              <NavLink key={to} to={to} className={({ isActive }) => cn("nav-link", isActive && "active")}>{label}{sup && <sup>{sup}</sup>}</NavLink>
            ))}
          </nav>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <button aria-label="Open navigation" className={cn("pointer-events-auto absolute right-[clamp(1.125rem,3vw,2.5rem)] top-4 grid size-[4.4rem] place-items-center rounded-full border border-black/10 bg-[#f3f3f3] text-[#0a0a0a] shadow-xl transition-all duration-500 hover:scale-105",
                scrolled ? "scale-100 opacity-100" : "scale-75 opacity-0 lg:pointer-events-none max-lg:scale-100 max-lg:opacity-100")}>
                <Menu aria-hidden="true" className="size-5" strokeWidth={1.5} />
              </button>
            </SheetTrigger>
            <SheetContent side="right" showCloseButton={false} className="dark band-dark w-[min(100vw,34rem)] border-0 bg-[#0a0a0a] p-0 text-foreground"
              onCloseAutoFocus={event => {
                if (menuNavigation.current) {
                  event.preventDefault()
                  mainRef.current?.focus({ preventScroll: true })
                  menuNavigation.current = false
                }
              }}>
              <div className="flex items-center justify-between px-8 pt-8">
                <SheetTitle className="text-white"><Wordmark onClick={closeForNavigation} /></SheetTitle>
                <SheetClose className="grid size-14 place-items-center rounded-full bg-white text-[#0a0a0a]" aria-label="Close navigation"><X className="size-5" /></SheetClose>
              </div>
              <SheetDescription className="px-8 pt-6 text-sm">Wildfire smoke forecasts, up to three days ahead.</SheetDescription>
              <nav className="flex flex-col px-8 pt-8" aria-label="Mobile">
                {[{ to: "/", label: "Home" }, ...NAV].map(({ to, label }) => (
                  <NavLink key={to} to={to} onClick={closeForNavigation}
                    className={({ isActive }) => cn("border-b border-white/10 py-4 text-[2.6rem] leading-none tracking-[-0.045em] transition-colors hover:text-[#8f9bff]", isActive && "text-[#8f9bff]")}>{label}</NavLink>
                ))}
              </nav>
              <a className="mx-8 mt-auto mb-8 inline-flex w-fit items-center gap-2 text-sm text-muted-foreground hover:text-white" href={REPO}>
                Code on GitHub <ArrowUpRight size={14} aria-hidden="true" /></a>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      <main id="main" ref={mainRef} tabIndex={-1} className="focus:outline-none"><Outlet /></main>

      <footer className="dark band-dark relative overflow-hidden text-foreground">
        <div className="site-width grid gap-14 pt-[clamp(6rem,12vw,11rem)] pb-10 lg:grid-cols-[1fr_2fr]">
          <div>
            <Wordmark className="text-white" />
            <p className="mt-6 max-w-xs text-[0.95rem]">Student research for the 2026–27 Conrad Challenge. The forecast map updates each morning from the latest run.</p>
            <div className="mt-6 flex flex-col items-start gap-3">
              <Button asChild className="h-12 bg-[#5b6cf6]! px-6 text-white!"><Link to="/world">Open the forecast map</Link></Button>
              <Button asChild variant="outline" className="h-12 px-6"><a href={REPO}>Code on GitHub</a></Button>
            </div>
          </div>
          <div>
            <h2 className="flex flex-wrap items-center gap-x-5 text-[clamp(3rem,6.5vw,6.4rem)] leading-[0.95]">
              <span className="flex -space-x-3" aria-hidden="true">{team.slice(0, 3).map(m => <Initials key={m.name} name={m.name} />)}</span>
              Plan ahead for wildfire smoke
            </h2>
            <div className="mt-16 grid grid-cols-2 gap-10 text-[0.95rem] sm:grid-cols-4">
              {[
                ["Project", [["SmokeCast", "/smokecast"], ["Forecast map", "/world"], ["AirPlan", "/airplan"], ["Data & methods", "/about"]]],
                ["Research", [["Methods", `${DOCS}/METHODS.md`], ["Backtest protocol", `${DOCS}/BACKTEST_PROTOCOL.md`], ["Experiment log", `${DOCS}/EXPERIMENTS.md`], ["Hourly study", `${DOCS}/HOURLY_ACCURACY.md`]]],
                ["Data", [["EPA AirNow", "https://www.airnow.gov/"], ["NOAA forecasts", "/about"], ["Sources & credits", "/about"]]],
                ["Team", [["Falcon Devs", "/#team"], ["Contributors", `${REPO}/graphs/contributors`], ["GitHub", REPO]]],
              ].map(([title, links]) => (
                <div key={title as string}>
                  <p className="text-muted-foreground">{title as string}</p>
                  <ul className="mt-4 space-y-2.5 font-medium">
                    {(links as string[][]).map(([label, href]) => <li key={label}>
                      {href.startsWith("http") ? <a className="hover:text-[#8f9bff]" href={href}>{label}</a> : <Link className="hover:text-[#8f9bff]" to={href}>{label}</Link>}
                    </li>)}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="site-width flex flex-wrap items-center justify-between gap-4 border-t border-white/10 py-7 text-sm font-medium">
          <p>2026 Falcon Devs · Foothill High School</p>
          <p className="rounded-full bg-white/8 px-4 py-1.5 font-mono text-[0.62rem] tracking-[0.18em] text-muted-foreground uppercase">Conrad Challenge 2026–27</p>
          <p className="text-muted-foreground">Forecasts support planning. Check current conditions on <a className="text-white underline-offset-4 hover:underline" href="https://www.airnow.gov/">AirNow</a>.</p>
        </div>
      </footer>
    </div>
  )
}
