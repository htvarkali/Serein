import type { ReactNode } from "react"
import { StarField } from "@/components/site/Motion"
import { cn } from "@/lib/utils"

// Building blocks for the layout: parchment ("light") or night-sky ("dark") bands, a
// gold letter-spaced label, a thin serif heading and a lead paragraph.
export function Section({ tone = "light", id, className, children, stars = true }: {
  tone?: "light" | "dark"; id?: string; className?: string; children: ReactNode; stars?: boolean }) {
  return (
    <section id={id} tabIndex={id ? -1 : undefined}
      className={cn("scroll-mt-24 overflow-hidden focus:outline-none py-[clamp(4.5rem,9vw,9rem)]",
        tone === "dark" ? "dark night text-foreground" : "parchment text-foreground", className)}>
      {tone === "dark" && stars && <StarField density={0.8} embers={false} />}
      <div className="site-width">{children}</div>
    </section>
  )
}

export function Eyebrow({ children, dot, className }: { children: ReactNode; dot?: boolean; className?: string }) {
  return <p className={cn("eyebrow", dot && "no-star", className)} data-reveal="">{dot && <span className="status-dot" />}{children}</p>
}

export function Heading({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 data-reveal="" className={cn("mt-4 mb-6 max-w-[16ch] text-[clamp(3rem,6vw,6rem)]", className)}>{children}</h2>
}

/** A gold handwritten word, used sparingly as a section signature. */
export function Script({ children, className }: { children: ReactNode; className?: string }) {
  return <span aria-hidden="true" className={cn("script gold-text block text-[clamp(3.4rem,7vw,6.5rem)]", className)}>{children}</span>
}

export function Lead({ children, className }: { children: ReactNode; className?: string }) {
  return <p data-reveal="" className={cn("max-w-3xl text-[clamp(1rem,1.45vw,1.22rem)] leading-relaxed font-light text-muted-foreground", className)}>{children}</p>
}

export function Split({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid items-center gap-[clamp(2rem,6vw,7rem)] md:grid-cols-2", className)}>{children}</div>
}

/** Centered night-sky page opening shared by the inner pages: image or video wash,
 *  stars and embers, gold label, thin display title and a handwritten accent. */
export function PageHero({ eyebrow, title, script, lead, media, children }: {
  eyebrow: string; title: ReactNode; script?: string; lead?: ReactNode
  media?: { image?: string; video?: string; position?: string; credit?: string }; children?: ReactNode }) {
  return (
    <section className="dark night relative isolate overflow-hidden text-foreground">
      {media?.video
        ? <video className="absolute inset-0 -z-30 size-full object-cover opacity-45" src={media.video} poster={media.image}
            autoPlay muted loop playsInline aria-hidden="true" data-parallax="10" />
        : media?.image && <img src={media.image} alt="" className="absolute inset-0 -z-30 size-full object-cover opacity-40"
            style={{ objectPosition: media.position }} data-parallax="10" />}
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(180deg,#0b1222cc,#0b122299_45%,#0b1222_100%)]" />
      <StarField density={1.1} />
      <div className="site-width flex min-h-[min(46rem,86svh)] flex-col items-center justify-center py-[clamp(6rem,12vw,10rem)] text-center">
        <p className="eyebrow justify-center" data-reveal="">{eyebrow}</p>
        <div className="relative mt-6">
          {script && <span aria-hidden="true" className="script gold-text pointer-events-none absolute left-1/2 top-1/2 -z-10 -translate-x-1/2 -translate-y-[38%] whitespace-nowrap text-[clamp(5rem,15vw,13rem)] opacity-35">{script}</span>}
          <h1 data-reveal="" data-reveal-delay="0.1" className="text-[clamp(3.8rem,10vw,9.5rem)] tracking-[0.01em]">{title}</h1>
        </div>
        <div className="divider-star mt-7" data-reveal="" data-reveal-delay="0.2">✦</div>
        {lead && <p data-reveal="" data-reveal-delay="0.25" className="mt-7 max-w-[44ch] text-[clamp(1.02rem,1.5vw,1.25rem)] font-light leading-relaxed text-muted-foreground">{lead}</p>}
        {children && <div data-reveal="" data-reveal-delay="0.35" className="mt-9 flex flex-wrap justify-center gap-3">{children}</div>}
      </div>
      {media?.credit && <p className="absolute right-4 bottom-3 text-[0.65rem] text-muted-foreground/80 sm:right-6">{media.credit}</p>}
    </section>
  )
}
