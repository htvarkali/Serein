import { useEffect, useRef, useState, type ReactNode } from "react"
import { cn } from "@/lib/utils"

// Layout building blocks: off-white ("light") or black ("dark") bands,
// a small mono label, very large tight headings and a lead paragraph.
export function Section({ tone = "light", id, className, children }: {
  tone?: "light" | "dark"; id?: string; className?: string; children: ReactNode; stars?: boolean }) {
  return (
    <section id={id} tabIndex={id ? -1 : undefined}
      className={cn("scroll-mt-24 overflow-hidden focus:outline-none py-[clamp(5rem,10vw,10rem)]",
        tone === "dark" ? "dark band-dark text-foreground" : "band-light text-foreground", className)}>
      <div className="site-width">{children}</div>
    </section>
  )
}

export function Eyebrow({ children, dot, className }: { children: ReactNode; dot?: boolean; className?: string }) {
  return <p className={cn("eyebrow", dot && "no-star", className)} data-reveal="">{dot && <span className="status-dot" />}{children}</p>
}

export function Heading({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 data-reveal="" className={cn("mt-4 mb-6 max-w-[16ch] text-[clamp(3rem,6.4vw,6.6rem)]", className)}>{children}</h2>
}

/** A handwritten note in the accent color, with an optional curved arrow. */
export function Script({ children, className, arrow }: { children: ReactNode; className?: string; arrow?: boolean }) {
  return (
    <span aria-hidden="true" className={cn("script inline-flex items-start gap-1 text-[clamp(1.5rem,2.4vw,2.1rem)]", className)}>
      {children}
      {arrow && <svg viewBox="0 0 40 40" className="mt-4 size-8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M30 4c4 14-4 26-20 28" /><path d="M8 24l2 8 8-2" /></svg>}
    </span>
  )
}

export function Lead({ children, className }: { children: ReactNode; className?: string }) {
  return <p data-reveal="" className={cn("max-w-3xl text-[clamp(1rem,1.4vw,1.2rem)] leading-relaxed text-muted-foreground", className)}>{children}</p>
}

export function Split({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid items-center gap-[clamp(2rem,6vw,7rem)] md:grid-cols-2", className)}>{children}</div>
}

/** A line of text that scrolls sideways forever (the giant hero headline). */
export function Marquee({ text, className, reverse }: { text: string; className?: string; reverse?: boolean }) {
  return (
    <div className={cn("overflow-hidden whitespace-nowrap", className)} aria-hidden="true">
      <div className={cn("marquee", reverse && "reverse")}>
        {[0, 1].map(k => <span key={k} className="pr-[0.4em]">{text}&nbsp;–&nbsp;{text}&nbsp;–&nbsp;</span>)}
      </div>
    </div>
  )
}

/** Text whose words sharpen one by one as the paragraph scrolls through the screen. */
export function WordReveal({ text, className, as: Tag = "p" }: { text: string; className?: string; as?: "p" | "h2" | "h3" }) {
  const ref = useRef<HTMLElement>(null)
  const words = text.split(" ")
  const [lit, setLit] = useState(0)
  useEffect(() => {
    let frame = 0
    const update = () => {
      frame = 0
      const el = ref.current
      if (!el) return
      const r = el.getBoundingClientRect(), vh = window.innerHeight
      const progress = Math.min(1, Math.max(0, (vh * 0.9 - r.top) / (r.height + vh * 0.45)))
      setLit(Math.round(progress * words.length))
    }
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update) }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => { window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); cancelAnimationFrame(frame) }
  }, [words.length])
  return (
    <Tag ref={ref as never} className={className} aria-label={text}>
      {words.map((w, i) => <span key={i} aria-hidden="true" className={cn("word", i >= lit && "dim")}>{w} </span>)}
    </Tag>
  )
}

/** Opening for the inner pages: a dark video or photo, a status pill, a giant
 *  left-aligned title, the lead and a handwritten note. */
export function PageHero({ eyebrow, title, script, lead, media, children }: {
  eyebrow: string; title: ReactNode; script?: string; lead?: ReactNode
  media?: { image?: string; video?: string; position?: string; credit?: string }; children?: ReactNode }) {
  return (
    <section className="dark band-dark relative isolate overflow-hidden text-foreground">
      {media?.video
        ? <video className="absolute inset-0 -z-30 size-full object-cover opacity-55" src={media.video} poster={media.image}
            autoPlay muted loop playsInline aria-hidden="true" data-parallax="10" />
        : media?.image && <img src={media.image} alt="" className="absolute inset-0 -z-30 size-full object-cover opacity-45"
            style={{ objectPosition: media.position }} data-parallax="10" />}
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(180deg,#0a0a0acc,#0a0a0a55_40%,#0a0a0a_100%)]" />
      <div className="site-width flex min-h-[min(48rem,90svh)] flex-col justify-end pt-36 pb-[clamp(3rem,6vw,5rem)]">
        <p className="inline-flex w-fit items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-medium text-[#0a0a0a]" data-reveal="">
          {eyebrow}<span className="status-dot" /></p>
        <h1 data-reveal="" data-reveal-delay="0.1" className="mt-6 max-w-[14ch] text-[clamp(4rem,12vw,11rem)] leading-[0.92]">{title}</h1>
        <div className="mt-10 grid items-end gap-8 md:grid-cols-[1.3fr_1fr]">
          {lead && <p data-reveal="" data-reveal-delay="0.2" className="max-w-[40ch] text-[clamp(1.1rem,1.8vw,1.55rem)] leading-snug tracking-[-0.02em]">{lead}</p>}
          <div data-reveal="" data-reveal-delay="0.3">
            {script && <Script arrow className="mb-4">{script}</Script>}
            {children && <div className="flex flex-wrap gap-3">{children}</div>}
          </div>
        </div>
      </div>
      {media?.credit && <p className="absolute right-4 bottom-3 text-[0.65rem] text-muted-foreground/80 sm:right-6">{media.credit}</p>}
    </section>
  )
}
