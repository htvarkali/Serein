import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

// Building blocks for the editorial layout: full-width light or dark bands, a small
// uppercase label, a large serif heading and a lead paragraph.
export function Section({ tone = "light", id, className, children }: {
  tone?: "light" | "dark"; id?: string; className?: string; children: ReactNode }) {
  return (
    <section id={id} tabIndex={id ? -1 : undefined} className={cn("scroll-mt-20 focus:outline-none py-[clamp(4rem,9vw,9rem)]", tone === "dark" ? "dark bg-background text-foreground" : "bg-background", className)}>
      <div className="site-width">{children}</div>
    </section>
  )
}

export function Eyebrow({ children, dot }: { children: ReactNode; dot?: boolean }) {
  return <p className="eyebrow">{dot && <span className="status-dot" />}{children}</p>
}

export function Heading({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn("mt-2 mb-5 max-w-[16ch] text-[clamp(3.1rem,6vw,6.25rem)]", className)}>{children}</h2>
}

export function Lead({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("max-w-3xl text-[clamp(1.06rem,1.6vw,1.35rem)] leading-normal text-muted-foreground", className)}>{children}</p>
}

export function Split({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid items-center gap-[clamp(2rem,6vw,7rem)] md:grid-cols-2", className)}>{children}</div>
}
