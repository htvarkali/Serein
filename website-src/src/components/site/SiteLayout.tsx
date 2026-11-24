import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

// Same site map as the original website (Home, SmokeCast, AirPlan), plus Smoke World
// and a data page.
export const NAV = [
  { to: "/smokecast", label: "SmokeCast" },
  { to: "/world", label: "Smoke World" },
  { to: "/airplan", label: "AirPlan" },
  { to: "/about", label: "Data & methods" },
]

export function Wordmark({ className }: { className?: string }) {
  return (
    <Link to="/" className={cn("inline-flex items-center gap-2 font-serif text-[2.4rem] leading-none tracking-tight", className)} aria-label="Serein home">
      Serein
    </Link>
  )
}

function NavLinks({ onClick, vertical }: { onClick?: () => void; vertical?: boolean }) {
  return (
    <>
      {NAV.map(n => (
        <NavLink key={n.to} to={n.to} onClick={onClick}
          className={({ isActive }) => cn("text-sm font-medium transition-colors hover:text-primary",
            vertical ? "py-2 font-serif text-4xl" : "", isActive ? "text-primary" : "text-foreground/80")}>
          {n.label}
        </NavLink>
      ))}
    </>
  )
}

export function SiteLayout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:bg-card focus:p-3">Skip to content</a>
      <header className="dark sticky top-0 z-40 border-b bg-background/95 text-foreground backdrop-blur">
        <div className="mx-auto flex h-[4.5rem] w-[min(100%-2*clamp(1.25rem,5.5vw,6rem),82rem)] items-center gap-8">
          <Wordmark className="text-[2.2rem]" />
          <nav className="hidden items-center gap-7 md:flex" aria-label="Primary"><NavLinks /></nav>
          <div className="ml-auto flex items-center gap-3">
            <a className="hidden text-sm text-foreground/70 hover:text-primary lg:inline" href="https://github.com/htvarkali/Serein">GitHub ↗</a>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden" aria-label="Menu"><Menu /></Button>
              </SheetTrigger>
              <SheetContent side="right" className="dark w-80 bg-background text-foreground">
                <SheetTitle className="px-6 pt-6"><Wordmark /></SheetTitle>
                <p className="px-6 text-sm text-muted-foreground">Wildfire smoke research for families and outdoor workers.</p>
                <nav className="flex flex-col px-6 pt-4" aria-label="Mobile"><NavLinks vertical onClick={() => setOpen(false)} /></nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>
      <main id="main"><Outlet /></main>
      <footer className="dark border-t bg-background text-foreground">
        <div className="mx-auto grid w-[min(100%-2*clamp(1.25rem,5.5vw,6rem),82rem)] gap-10 py-16 md:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <Wordmark className="text-[clamp(3.8rem,7vw,5.7rem)] text-primary" />
            <p className="mt-4 max-w-sm text-sm text-muted-foreground">
              Student research for the Conrad Challenge 2026-27, Foothill High School. Not medical advice.
            </p>
          </div>
          <nav className="flex flex-col gap-2 text-sm" aria-label="Explore Serein">
            <Link to="/" className="text-muted-foreground hover:text-primary">Home</Link>
            {NAV.map(n => <Link key={n.to} to={n.to} className="text-muted-foreground hover:text-primary">{n.label}</Link>)}
          </nav>
          <div className="flex flex-col gap-2 text-sm">
            <a className="text-muted-foreground hover:text-primary" href="https://github.com/htvarkali/Serein">Code on GitHub ↗</a>
            <a className="text-muted-foreground hover:text-primary" href="https://github.com/htvarkali/Serein/graphs/contributors">Contributors ↗</a>
            <Link className="text-muted-foreground hover:text-primary" to="/about">Data sources and credits</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
