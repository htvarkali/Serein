import { useEffect, useRef, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { ArrowUpRight, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

export const NAV = [
  { to: "/smokecast", label: "SmokeCast" },
  { to: "/world", label: "Forecast map" },
  { to: "/airplan", label: "AirPlan" },
  { to: "/about", label: "Data & methods" },
]

export function Wordmark({ className, onClick }: { className?: string; onClick?: () => void }) {
  return (
    <Link to="/" onClick={onClick}
      className={cn("inline-flex items-center gap-2 rounded-sm font-serif text-[2.6rem] leading-none tracking-tight", className)}
      aria-label="Serein home">
      Serein<span className="mb-1.5 size-1.5 self-end rounded-full bg-current" aria-hidden="true" />
    </Link>
  )
}

function NavLinks({ onClick, vertical }: { onClick?: () => void; vertical?: boolean }) {
  return NAV.map(({ to, label }) => (
    <NavLink key={to} to={to} onClick={onClick}
      className={({ isActive }) => cn(
        "rounded-lg transition-colors hover:bg-white/9 hover:text-primary",
        vertical ? "px-4 py-3 font-serif text-3xl leading-none" : "px-3 py-2 text-sm font-medium",
        isActive ? "bg-white/9 text-primary" : "text-foreground",
      )}>
      {label}
    </NavLink>
  ))
}

export function SiteLayout() {
  const [open, setOpen] = useState(false)
  const { pathname, hash } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const previousRoute = useRef(pathname)
  const menuNavigation = useRef(false)

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
      <header className="dark sticky top-0 z-40 border-b bg-background/95 text-foreground backdrop-blur">
        <div className="site-width flex h-[4.35rem] items-center justify-between gap-3">
          <Wordmark className="text-primary" />
          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary"><NavLinks /></nav>
          <a className="hidden items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium hover:bg-white/9 lg:inline-flex"
            href="https://github.com/htvarkali/Serein">GitHub <ArrowUpRight size={15} aria-hidden="true" /></a>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="size-11 rounded-full md:hidden" aria-label="Open navigation"><Menu aria-hidden="true" /></Button>
            </SheetTrigger>
            <SheetContent side="right"
              className="dark w-[min(90vw,22rem)] bg-background text-foreground"
              onCloseAutoFocus={event => {
                if (menuNavigation.current) {
                  event.preventDefault()
                  mainRef.current?.focus({ preventScroll: true })
                  menuNavigation.current = false
                }
              }}>
              <SheetTitle className="px-6 pt-6 font-serif text-3xl font-normal">Explore Serein</SheetTitle>
              <SheetDescription className="px-6">Daily wildfire smoke forecasting and exposure planning.</SheetDescription>
              <nav className="flex flex-col gap-1 px-3" aria-label="Mobile">
                <NavLink to="/" onClick={closeForNavigation} className="rounded-lg px-4 py-3 font-serif text-3xl leading-none hover:bg-white/9">Home</NavLink>
                <NavLinks vertical onClick={closeForNavigation} />
              </nav>
              <a className="mx-6 inline-flex w-fit items-center gap-2 rounded-md py-2 text-sm text-muted-foreground hover:text-primary"
                href="https://github.com/htvarkali/Serein">Code on GitHub <ArrowUpRight size={15} aria-hidden="true" /></a>
            </SheetContent>
          </Sheet>
        </div>
      </header>
      <main id="main" ref={mainRef} tabIndex={-1} className="scroll-mt-[4.35rem] focus:outline-none"><Outlet /></main>
      <footer className="dark border-t bg-background text-foreground">
        <div className="site-width grid gap-9 py-12 md:grid-cols-[1.5fr_1fr_1fr] md:py-16">
          <div>
            <Wordmark className="text-[clamp(3.4rem,6vw,5rem)] text-primary" />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              Falcon Devs · Foothill High School<br />Student research for the 2026–27 Conrad Challenge.
            </p>
          </div>
          <nav className="flex flex-col items-start gap-3 text-sm" aria-label="Footer">
            <Link to="/" className="text-muted-foreground hover:text-primary">Home</Link>
            {NAV.map(n => <Link key={n.to} to={n.to} className="text-muted-foreground hover:text-primary">{n.label}</Link>)}
          </nav>
          <div className="flex flex-col items-start gap-3 text-sm">
            <a className="inline-flex items-center gap-1 text-muted-foreground hover:text-primary"
              href="https://github.com/htvarkali/Serein">Code on GitHub <ArrowUpRight size={14} aria-hidden="true" /></a>
            <a className="text-muted-foreground hover:text-primary" href="https://github.com/htvarkali/Serein/graphs/contributors">Contributors</a>
            <Link className="text-muted-foreground hover:text-primary" to="/about">Data sources and credits</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
