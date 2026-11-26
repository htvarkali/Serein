import { useEffect, useRef, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { ArrowUpRight, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { StarField, scrollToTop, useSiteMotion } from "@/components/site/Motion"
import { cn } from "@/lib/utils"

export const NAV = [
  { to: "/smokecast", label: "SmokeCast" },
  { to: "/world", label: "Forecast map" },
  { to: "/airplan", label: "AirPlan" },
  { to: "/about", label: "Data & methods" },
]

const REPO = "https://github.com/htvarkali/Serein"

export function Wordmark({ className, onClick, tagline = true }: { className?: string; onClick?: () => void; tagline?: boolean }) {
  return (
    <Link to="/" onClick={onClick} className={cn("group inline-flex flex-col rounded-sm leading-none", className)} aria-label="Serein home">
      <span className="font-serif text-[2.1rem] font-light tracking-[0.02em]">Serein</span>
      {tagline && <span className="mt-1 text-[0.56rem] font-semibold tracking-[0.34em] text-gold uppercase">Forecasting the air</span>}
    </Link>
  )
}

/** Gold monogram: an S inside two rings, used in the footer. */
export function Monogram({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 120" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="mono-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f1dcb2" /><stop offset=".5" stopColor="#c9a466" /><stop offset="1" stopColor="#8f6a32" />
        </linearGradient>
      </defs>
      <circle cx="60" cy="60" r="56" fill="none" stroke="url(#mono-gold)" strokeWidth="1" />
      <g className="spin-slow"><circle cx="60" cy="60" r="49" fill="none" stroke="url(#mono-gold)" strokeWidth=".6" strokeDasharray="1 5" /></g>
      <text x="60" y="80" textAnchor="middle" fontFamily="Cormorant, Georgia, serif" fontWeight="300" fontSize="62" fill="url(#mono-gold)">S</text>
    </svg>
  )
}

function NavLinks({ onClick, vertical }: { onClick?: () => void; vertical?: boolean }) {
  return NAV.map(({ to, label }) => (
    <NavLink key={to} to={to} onClick={onClick}
      className={({ isActive }) => cn(vertical
        ? "rounded-lg px-4 py-3 font-serif text-4xl font-light leading-none hover:text-gold"
        : "nav-link text-[0.7rem] font-semibold tracking-[0.24em] uppercase", isActive && (vertical ? "text-gold" : "active"))}>
      {label}
    </NavLink>
  ))
}

export function SiteLayout() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { pathname, hash } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const previousRoute = useRef(pathname)
  const menuNavigation = useRef(false)
  useSiteMotion()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

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

      <header className={cn("dark fixed inset-x-0 top-0 z-40 text-foreground transition-[background-color,box-shadow,backdrop-filter] duration-500",
        scrolled ? "bg-night/96 shadow-[0_1px_0_#c9a46640] backdrop-blur-xl" : "bg-transparent")}>
        <div className={cn("site-width hidden items-center justify-between border-b border-white/10 text-[0.72rem] text-muted-foreground transition-all duration-500 md:flex",
          scrolled ? "h-0 overflow-hidden border-transparent opacity-0" : "h-10 opacity-100")}>
          <p className="flex items-center gap-2"><span className="status-dot" />Student research · Conrad Challenge 2026–27</p>
          <div className="flex items-center gap-6">
            <span>Falcon Devs · Foothill High School</span>
            <a href={REPO} className="inline-flex items-center gap-1 hover:text-gold">Code on GitHub <ArrowUpRight size={13} aria-hidden="true" /></a>
          </div>
        </div>
        <div className="site-width flex h-[4.6rem] items-center justify-between gap-4">
          <Wordmark />
          <nav className="hidden items-center gap-9 lg:flex" aria-label="Primary"><NavLinks /></nav>
          <div className="flex items-center gap-3">
            <Button asChild variant="outline" className="hidden h-10 px-5 sm:inline-flex">
              <Link to="/world">Open the map</Link>
            </Button>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <button className="grid size-11 place-items-center rounded-full border border-gold/50 transition-colors hover:bg-gold/10 lg:hidden" aria-label="Open navigation">
                  <Menu aria-hidden="true" className="size-[1.1rem]" />
                </button>
              </SheetTrigger>
              <SheetContent side="right" className="dark night w-[min(90vw,24rem)] border-gold/30 text-foreground"
                onCloseAutoFocus={event => {
                  if (menuNavigation.current) {
                    event.preventDefault()
                    mainRef.current?.focus({ preventScroll: true })
                    menuNavigation.current = false
                  }
                }}>
                <StarField density={0.7} embers={false} />
                <SheetTitle className="px-6 pt-8"><span className="script gold-text text-6xl">Serein</span></SheetTitle>
                <SheetDescription className="px-6 caps text-[0.62rem]">Wildfire smoke forecasting</SheetDescription>
                <nav className="flex flex-col gap-1 px-3 pt-4" aria-label="Mobile">
                  <NavLink to="/" onClick={closeForNavigation} className="rounded-lg px-4 py-3 font-serif text-4xl font-light leading-none hover:text-gold">Home</NavLink>
                  <NavLinks vertical onClick={closeForNavigation} />
                </nav>
                <a className="mx-6 mt-auto mb-8 inline-flex w-fit items-center gap-2 caps text-[0.62rem] text-muted-foreground hover:text-gold" href={REPO}>
                  Code on GitHub <ArrowUpRight size={14} aria-hidden="true" /></a>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      <main id="main" ref={mainRef} tabIndex={-1} className="focus:outline-none"><Outlet /></main>

      <footer className="dark night relative overflow-hidden text-foreground">
        <StarField density={0.6} embers={false} />
        <div className="absolute left-1/2 top-0 h-28 w-px bg-gradient-to-b from-transparent to-gold/70" aria-hidden="true" />
        <div className="site-width flex flex-col items-center pt-32 pb-14 text-center">
          <Monogram className="float size-28" />
          <p className="script gold-text mt-6 text-[clamp(4rem,9vw,7rem)]">Serein</p>
          <p className="caps mt-3 text-[0.62rem] text-muted-foreground">Wildfire smoke forecasts, three days ahead</p>
          <nav className="mt-12 flex flex-wrap justify-center gap-x-9 gap-y-4" aria-label="Footer">
            <Link to="/" className="nav-link caps text-[0.64rem]">Home</Link>
            {NAV.map(n => <Link key={n.to} to={n.to} className="nav-link caps text-[0.64rem]">{n.label}</Link>)}
          </nav>
          <div className="mt-14 grid w-full gap-6 border-t border-gold/20 pt-8 text-sm text-muted-foreground md:grid-cols-3 md:text-left">
            <p>Falcon Devs · Foothill High School<br />Student research for the 2026–27 Conrad Challenge.</p>
            <p className="md:text-center">Forecasts support planning. Check current conditions on{" "}
              <a className="text-gold underline-offset-4 hover:underline" href="https://www.airnow.gov/">AirNow</a>.</p>
            <div className="flex flex-col gap-2 md:items-end">
              <a className="inline-flex items-center gap-1 hover:text-gold" href={REPO}>Code on GitHub <ArrowUpRight size={14} aria-hidden="true" /></a>
              <a className="hover:text-gold" href={`${REPO}/graphs/contributors`}>Contributors</a>
              <Link className="hover:text-gold" to="/about">Data sources and credits</Link>
            </div>
          </div>
        </div>
      </footer>

      <button onClick={scrollToTop} aria-label="Back to top"
        className={cn("btn-gold fixed right-5 bottom-5 z-40 grid size-14 place-items-center rounded-full text-xl transition-all duration-500 sm:right-8 sm:bottom-8",
          scrolled ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-4 opacity-0")}>
        <span aria-hidden="true">✦</span>
      </button>
    </div>
  )
}
