import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

const NAV = [
  { to: "/world", label: "Smoke World" },
  { to: "/replay", label: "Replay" },
  { to: "/results", label: "Results" },
  { to: "/plan", label: "Plan your day" },
  { to: "/about", label: "Data & methods" },
]

export function Wordmark({ className }: { className?: string }) {
  return (
    <Link to="/" className={cn("font-serif text-3xl leading-none tracking-tight", className)} aria-label="Serein home">
      Serein
    </Link>
  )
}

function NavLinks({ onClick }: { onClick?: () => void }) {
  return (
    <>
      {NAV.map(n => (
        <NavLink key={n.to} to={n.to} onClick={onClick}
          className={({ isActive }) => cn("rounded-full px-3 py-1.5 text-sm transition-colors hover:bg-accent",
            isActive ? "bg-accent text-foreground" : "text-muted-foreground")}>
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
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-5">
          <Wordmark />
          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary"><NavLinks /></nav>
          <div className="ml-auto flex items-center gap-2">
            <Button asChild size="sm" className="hidden sm:inline-flex"><Link to="/world">Open Smoke World</Link></Button>
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden" aria-label="Menu"><Menu /></Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <SheetTitle className="px-4 pt-4"><Wordmark /></SheetTitle>
                <nav className="flex flex-col gap-1 p-4" aria-label="Mobile"><NavLinks onClick={() => setOpen(false)} /></nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>
      <main><Outlet /></main>
      <footer className="mt-24 border-t border-border/60">
        <div className="mx-auto grid max-w-6xl gap-8 px-5 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Wordmark className="text-5xl text-primary" />
            <p className="mt-3 max-w-sm text-sm text-muted-foreground">
              Student research for the Conrad Challenge 2026-27. Foothill High School.
              Not medical advice.
            </p>
          </div>
          <nav className="flex flex-col gap-2 text-sm" aria-label="Footer">
            {NAV.map(n => <Link key={n.to} to={n.to} className="text-muted-foreground hover:text-foreground">{n.label}</Link>)}
          </nav>
          <div className="flex flex-col gap-2 text-sm">
            <a className="text-muted-foreground hover:text-foreground" href="https://github.com/htvarkali/Serein">Code on GitHub</a>
            <Link className="text-muted-foreground hover:text-foreground" to="/about">Data sources and credits</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
