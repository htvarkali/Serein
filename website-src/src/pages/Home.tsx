import { useMemo, useState, type CSSProperties } from "react"
import { Link } from "react-router-dom"
import { ArrowDown, ArrowRight, ArrowUp, ArrowUpRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Eyebrow, Heading, Lead, Marquee, Script, Section, Split, WordReveal } from "@/components/site/Section"
import { ForecastCompare, useLive } from "@/components/site/LiveForecast"
import { ForecastDial } from "@/components/site/ForecastDial"
import { BOX } from "@/lib/world"
import { SOURCE_DEV, asset, headline, rmseByLead, sources, team, updates } from "@/data/site"

const threeDay = rmseByLead[3]
const docs = "https://github.com/htvarkali/Serein/blob/main/docs"

const pillars = [
  { title: "SmokeCast", tag: "The forecast", to: "/smokecast", tone: "bg-[#5b6cf6] text-white", tagTone: "bg-white/20 text-white", rotate: "-3deg",
    text: "Compare Serein’s daily forecasts with public benchmarks, including at withheld monitor locations.", image: "img/photo-research.webp" },
  { title: "Forecast map", tag: "Smoke World", to: "/world", tone: "bg-[#e7dfcc] text-[#0a0a0a]", tagTone: "bg-[#0a0a0a] text-white", rotate: "2deg",
    text: "Choose a place to see its daily estimate and range, or explore a recorded smoke event.", image: "img/world-preview.webp" },
  { title: "AirPlan", tag: "Planning", to: "/airplan", tone: "bg-[#1a1a1a] text-white border border-white/10", tagTone: "bg-white/10 text-white", rotate: "-1deg",
    text: "See how families and outdoor crews could use a forecast to plan ahead. Family examples use simulated histories.", image: "img/photo-family.webp" },
]

const stats = [
  { big: `${threeDay.serein}`, unit: "µg/m³", title: "Forecast error three days ahead", note: `Versus ${threeDay.noaa} for the AQM → HRRR → persistence baseline. Lower is better.` },
  { big: `${headline.warnedSerein}%`, unit: "", title: "High-pollution area-days warned a day ahead", note: `The official forecast warned on ${headline.warnedEpa}%. False alarms were ${headline.falseSerein} vs. ${headline.falseEpa}.` },
  { big: `${headline.hiddenSerein}`, unit: "µg/m³", title: "Next-day error at withheld monitors", note: `Versus ${headline.hiddenNoaa} for the same fallback baseline at monitor locations hidden from the model.` },
]

const longDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })

function LiveFacts() {
  const live = useLive()
  const facts = useMemo(() => {
    if (live.state !== "ready") return null
    const d = live.data
    return [
      [longDate(d.issue_date), "latest run"],
      [`${d.hours} h`, "looks ahead"],
      [d.points.filter(p => p[2] === 1).length.toLocaleString(), "EPA monitors"],
      [d.fires.filter(([lat, lon]) => lat >= BOX.south && lat <= BOX.north && lon >= BOX.west && lon <= BOX.east).length.toLocaleString(), "fire detections, West"],
    ]
  }, [live])
  return (
    <dl className="grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4" aria-live="polite">
      {(facts ?? [["…", "latest run"], ["…", "looks ahead"], ["…", "EPA monitors"], ["…", "fire detections, West"]]).map(([v, k]) => (
        <div key={k}><dd className="text-2xl font-medium tracking-[-0.03em]">{live.state === "error" ? "n/a" : v}</dd><dt className="text-sm text-white/60">{k}</dt></div>
      ))}
    </dl>
  )
}

function StatCarousel() {
  const [i, setI] = useState(0)
  const s = stats[i]
  return (
    <div className="relative flex min-h-[22rem] flex-col justify-between overflow-hidden rounded-[1.6rem] bg-[linear-gradient(135deg,#5b6cf6,#7b88ff)] p-[clamp(1.75rem,4vw,3rem)] text-white" aria-live="polite">
      <div className="flex items-start justify-between gap-6">
        <p className="max-w-[18ch] text-[clamp(1.6rem,2.6vw,2.4rem)] leading-tight tracking-[-0.03em]">{s.title}</p>
        <div className="flex flex-col gap-2">
          <button aria-label="Previous result" onClick={() => setI((i + stats.length - 1) % stats.length)} className="grid size-11 place-items-center rounded-lg border border-white/40 hover:bg-white/15"><ArrowUp className="size-4" /></button>
          <button aria-label="Next result" onClick={() => setI((i + 1) % stats.length)} className="grid size-11 place-items-center rounded-lg border border-white/40 hover:bg-white/15"><ArrowDown className="size-4" /></button>
        </div>
      </div>
      <div key={i} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        <p className="text-[clamp(4.5rem,9vw,8rem)] leading-none font-normal tracking-[-0.06em]">{s.big}<span className="ml-2 text-2xl tracking-normal opacity-80">{s.unit}</span></p>
        <p className="mt-3 max-w-md text-white/85">{s.note}</p>
        <p className="mt-5 font-mono text-[0.62rem] tracking-[0.16em] text-white/70 uppercase">{i + 1} / {stats.length} · Development backtest, 2023</p>
      </div>
    </div>
  )
}

export function Home() {
  return (
    <>
      {/* Hero: smoke video, a status pill, a giant title scrolling sideways, then the statement. */}
      <section className="dark night relative isolate flex min-h-[100svh] flex-col justify-end overflow-hidden text-white" id="overview">
        <video className="absolute inset-0 -z-30 size-full object-cover" src={asset("motion/hero-smoke.mp4")} poster={asset("img/photo-hero.webp")}
          autoPlay muted loop playsInline aria-hidden="true" data-parallax="14" />
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,#0a0a0a88,transparent_50%,#0a0a0aaa),linear-gradient(180deg,#0a0a0a99,transparent_30%,#0a0a0acc_75%,#0a0a0a)]" />
        <div className="site-width flex md:justify-end md:pr-[12%]" data-reveal="">
          <Link to="/world" className="inline-flex w-fit items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-medium text-[#0a0a0a] hover:bg-[#5b6cf6] hover:text-white">
            Latest forecast run is live <span className="status-dot" />
          </Link>
        </div>
        <h1 className="sr-only">Plan ahead for wildfire smoke</h1>
        <Marquee text="Plan ahead for wildfire smoke" className="mt-6 text-[clamp(4.5rem,13vw,13rem)] leading-[1.05] font-normal tracking-[-0.05em]" />
        <div className="site-width grid gap-10 pt-8 pb-[clamp(2.5rem,5vw,4.5rem)] md:grid-cols-[1.35fr_1fr]" data-reveal="" data-reveal-delay="0.2">
          <p className="max-w-[30ch] text-[clamp(1.45rem,2.6vw,2.4rem)] leading-[1.12] font-normal tracking-[-0.04em]">
            Serein estimates daily air pollution up to three days ahead, with a range that shows how uncertain each forecast is.
          </p>
          <div className="space-y-6">
            <LiveFacts />
            <Script arrow className="text-white/90!">a student forecast, tested in the open</Script>
          </div>
        </div>
      </section>

      {/* Data sources strip */}
      <div className="dark night border-t border-white/10 py-8 text-white/55">
        <p className="sr-only">Built on public data from: {sources.map(s => s.name).join(", ")}</p>
        <Marquee reverse text={sources.map(s => s.name).join("   ·   ")} className="text-[1.05rem] font-medium tracking-[-0.01em]" />
      </div>

      {/* Statement with a pill photo inside the heading, then a word-by-word paragraph */}
      <Section id="problem">
        <h2 className="flex flex-wrap items-center gap-x-[0.25em] text-[clamp(3.2rem,8vw,8rem)] leading-[1.02]" data-reveal="">
          A little more time
          <span className="inline-block h-[0.8em] w-[1.9em] overflow-hidden rounded-full align-middle" aria-hidden="true">
            <img src={asset("img/photo-research.webp")} alt="" className="size-full object-cover" loading="lazy" />
          </span>
          <span className="text-[#5b6cf6]">to prepare.</span>
        </h2>
        <div className="mt-[clamp(3rem,7vw,6rem)] md:pl-[20%]">
          <WordReveal className="max-w-[34ch] text-[clamp(1.6rem,3.1vw,2.75rem)] leading-[1.18] tracking-[-0.035em]"
            text="When smoke could affect a practice, a shift, or a family’s plans, advance notice gives people time to prepare an alternative. SmokeCast learns from recent monitor readings and existing forecasts, and we test how well it estimates pollution when nearby readings are limited." />
          <Button asChild className="mt-10 h-14 pl-2 pr-6">
            <Link to="/#team"><span className="flex -space-x-2">{team.slice(0, 3).map(m => (
              <span key={m.name} className="grid size-10 place-items-center rounded-full border-2 border-[#0a0a0a] bg-[#e7dfcc] text-[0.6rem] font-semibold text-[#0a0a0a]">{m.name.split(" ").map(p => p[0]).join("")}</span>
            ))}</span>Meet the team</Link>
          </Button>
        </div>
      </Section>

      {/* Live comparison inside a big black rounded panel */}
      <section id="compare" className="parchment pb-[clamp(5rem,10vw,9rem)]">
        <div className="site-width">
          <div className="dark night overflow-hidden rounded-[2.2rem] p-[clamp(1.5rem,5vw,5rem)] text-foreground">
            <Split className="md:grid-cols-[0.9fr_1.1fr]">
              <div>
                <Eyebrow dot>Latest published run</Eyebrow>
                <Heading className="max-w-[11ch] text-[clamp(2.8rem,5.4vw,5.4rem)]">NOAA’s forecast, <span className="text-[#8f9bff]">then ours.</span></Heading>
                <Lead>Drag the line to compare tomorrow’s average from NOAA’s forecast with the SmokeCast-adjusted version from the same run.</Lead>
                <p className="mt-5 max-w-lg text-sm leading-relaxed text-muted-foreground" data-reveal="">
                  SmokeCast starts from NOAA’s forecasts and learns from recent monitor readings how to correct them. This is the real latest run,
                  so on a clear day most of the West is simply “Good.” The daily average is the evaluated forecast.
                </p>
                <Button asChild className="mt-8 h-12 px-6"><Link to="/world">Open the full map <ArrowRight aria-hidden="true" /></Link></Button>
              </div>
              <div data-reveal="" data-reveal-delay="0.15"><ForecastCompare /></div>
            </Split>
          </div>
        </div>
      </section>

      {/* Approach: three tilted cards that stack while scrolling */}
      <Section tone="dark" id="project">
        <div className="text-center">
          <Eyebrow className="justify-center">Our approach</Eyebrow>
          <h2 className="mx-auto mt-4 max-w-[12ch] text-[clamp(3.4rem,8vw,8rem)]" data-reveal="">How Serein makes a forecast</h2>
          <Lead className="mx-auto max-w-2xl text-center">One project in three parts: a tested forecast, a map you can explore, and planning examples built on both.</Lead>
        </div>
        <div className="mx-auto mt-20 max-w-3xl space-y-[18vh] pb-[6vh]">
          {pillars.map((p, i) => (
            <Link key={p.to} to={p.to} style={{ "--i": i, "--r": p.rotate } as CSSProperties}
              className={`stack-card group block overflow-hidden rounded-[1.8rem] p-[clamp(1.75rem,4vw,3.25rem)] text-center shadow-[0_40px_80px_-30px_#000] ${p.tone}`}>
              <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${p.tagTone}`}>{p.tag}</span>
              <h3 className="mt-5 text-[clamp(3.4rem,8vw,6.5rem)] leading-none tracking-[-0.05em]">{p.title}</h3>
              <p className="mx-auto mt-5 max-w-[40ch] text-[clamp(1rem,1.5vw,1.2rem)] opacity-85">{p.text}</p>
              <div className="relative mx-auto mt-8 aspect-[16/8] max-w-xl overflow-hidden rounded-2xl">
                <img src={asset(p.image)} alt="" loading="lazy" className="size-full object-cover transition-transform duration-700 group-hover:scale-105" />
                <span className="absolute bottom-4 left-1/2 inline-flex -translate-x-1/2 items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-medium text-[#0a0a0a]">
                  More about {p.title} <ArrowUpRight className="size-4" aria-hidden="true" /></span>
              </div>
            </Link>
          ))}
        </div>
      </Section>

      {/* Results */}
      <Section tone="dark" id="results" className="!pt-0">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <h2 className="max-w-[12ch] text-[clamp(3rem,6.4vw,6.4rem)]" data-reveal="">What the forecasts got right</h2>
          <p className="max-w-sm text-sm text-muted-foreground" data-reveal="">{SOURCE_DEV}</p>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-[1fr_1.6fr]">
          <div className="flex flex-col justify-between rounded-[1.6rem] border border-white/10 bg-[linear-gradient(180deg,#151515,#0a0a0a)] p-8" data-reveal="">
            <div>
              <span className="grid size-14 place-items-center rounded-full bg-[#5b6cf6] text-xl text-white" aria-hidden="true">↗</span>
              <h3 className="mt-6 text-3xl tracking-[-0.04em]">See every result</h3>
              <p className="mt-3 text-muted-foreground">Forecast error by day, warnings, hidden monitors, and who lives far from an EPA monitor.</p>
            </div>
            <Button asChild className="mt-8 h-12 w-fit px-6"><Link to="/smokecast">Open SmokeCast results <ArrowRight aria-hidden="true" /></Link></Button>
          </div>
          <div data-reveal="" data-reveal-delay="0.1"><StatCarousel /></div>
        </div>
        <div className="mt-16 grid items-center gap-10 md:grid-cols-[1fr_1.1fr]">
          <div data-reveal="">
            <Eyebrow>Forecast error by day</Eyebrow>
            <p className="mt-4 max-w-md text-[clamp(1.3rem,2vw,1.8rem)] leading-snug tracking-[-0.03em]">Each ring is one forecast day. Shorter arcs mean smaller errors; SmokeCast is the bright arc.</p>
          </div>
          <div data-reveal="" data-reveal-delay="0.1"><ForecastDial /></div>
        </div>
      </Section>

      {/* Update log from the experiment record */}
      <Section tone="dark" id="updates" className="!pt-0">
        <div className="text-center">
          <h2 className="text-[clamp(4rem,11vw,10rem)]" data-reveal="">Update log</h2>
          <p className="mt-3 text-[clamp(1.2rem,2vw,1.6rem)] tracking-[-0.02em]" data-reveal="">Last change <span className="text-[#8f9bff]">{longDate(updates[0].date)}</span>, failures included</p>
        </div>
        <ol className="mx-auto mt-14 max-w-4xl divide-y divide-white/10 border-y border-white/10">
          {updates.map((u, i) => (
            <li key={u.title} data-reveal="" data-reveal-delay={String(Math.min(i, 4) * 0.06)} className="grid gap-2 py-6 sm:grid-cols-[8rem_7rem_1fr] sm:items-baseline">
              <span className="font-mono text-xs tracking-[0.12em] text-muted-foreground uppercase">{longDate(u.date)}</span>
              <span className={`w-fit rounded-full px-3 py-1 text-xs font-medium ${u.kind === "Failed" ? "bg-white/8 text-white/70" : u.kind === "Accepted" ? "bg-[#3fbf6f]/20 text-[#7fe0a3]" : "bg-[#5b6cf6]/25 text-[#c3c9ff]"}`}>{u.kind}</span>
              <div>
                <p className="text-lg font-medium tracking-[-0.02em]">{"doc" in u
                  ? <a className="hover:text-[#8f9bff]" href={`${docs}/${u.doc}`}>{u.title} <ArrowUpRight className="inline size-4" aria-hidden="true" /></a> : u.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{u.note}</p>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      {/* Next and team */}
      <Section id="next">
        <Split className="items-start">
          <div>
            <Eyebrow>Project status</Eyebrow>
            <Heading className="max-w-[10ch]">What we’re testing next</Heading>
            <Script arrow>still open questions</Script>
          </div>
          <ol className="space-y-4">
            {[
              ["Reserved seasons", "The team is preparing a final evaluation on the 2024–25 fire seasons. We’ll publish the results after the evaluation rules are frozen."],
              ["Timing of smoke spikes", "In development tests, the daily estimates were more useful than the hourly pattern for anticipating pollution levels. Precise arrival times need more research."],
              ["Use in practice", "We’re exploring how families and people who schedule outdoor activities could use a daily outlook alongside current air-quality information."],
            ].map(([term, description], i) => (
              <li key={term} data-reveal="" data-reveal-delay={String(i * 0.1)} className="rounded-[1.4rem] bg-white p-7 shadow-[0_20px_50px_-35px_#0005]">
                <p className="font-mono text-xs text-[#5b6cf6]">0{i + 1}</p>
                <h3 className="mt-2 text-2xl tracking-[-0.03em]">{term}</h3>
                <p className="mt-2 text-muted-foreground">{description}</p>
              </li>
            ))}
          </ol>
        </Split>
      </Section>

      <Section id="team" className="!pt-0">
        <h2 className="text-[clamp(3rem,7vw,7rem)]" data-reveal="">The team <span className="text-[#5b6cf6]">behind Serein</span></h2>
        <p className="mt-4 text-lg text-muted-foreground" data-reveal="">Falcon Devs · five students at Foothill High School</p>
        <ul className="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {team.map((member, i) => (
            <li key={member.name} data-reveal="" data-reveal-delay={String(i * 0.08)}
              className={`flex min-h-56 flex-col rounded-[1.4rem] p-6 ${i % 3 === 0 ? "bg-[#0a0a0a] text-white" : i % 3 === 1 ? "bg-[#e7dfcc]" : "bg-white"}`}>
              <span className={`grid size-14 place-items-center rounded-full text-sm font-semibold ${i % 3 === 0 ? "bg-[#5b6cf6] text-white" : "bg-[#0a0a0a] text-white"}`}>
                {member.name.split(" ").map(part => part[0]).join("")}</span>
              <h3 className="mt-auto pt-6 text-xl tracking-[-0.03em]">{member.name}</h3>
              <p className="text-sm opacity-60">{member.grade}</p>
              {member.role && <p className="mt-3 text-sm opacity-80">{member.role}</p>}
            </li>
          ))}
        </ul>
      </Section>
    </>
  )
}
