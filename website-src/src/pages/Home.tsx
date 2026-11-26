import { Link } from "react-router-dom"
import { ArrowRight, ArrowUpRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Eyebrow, Heading, Lead, Script, Section, Split } from "@/components/site/Section"
import { StarField } from "@/components/site/Motion"
import { ForecastCompare, LiveBar } from "@/components/site/LiveForecast"
import { ForecastDial } from "@/components/site/ForecastDial"
import { SOURCE_DEV, asset, headline, rmseByLead, team } from "@/data/site"

const threeDay = rmseByLead[3]

const projects = [
  {
    title: "SmokeCast",
    to: "/smokecast",
    image: "img/photo-research.webp",
    kicker: "The forecast",
    description: "Compare Serein’s daily forecasts with public benchmarks, including at withheld monitor locations.",
    action: "See the research",
  },
  {
    title: "Forecast map",
    to: "/world",
    image: "img/world-preview.webp",
    kicker: "Smoke World",
    description: "Choose a place to see its daily estimate and range, or explore a recorded smoke event.",
    action: "Explore the map",
  },
  {
    title: "AirPlan",
    to: "/airplan",
    image: "img/photo-family.webp",
    kicker: "Planning",
    description: "See how families and outdoor crews could use a forecast to plan ahead. Family examples use simulated histories.",
    action: "See planning examples",
  },
]

function ProjectCard({ project, index }: { project: (typeof projects)[number]; index: number }) {
  return (
    <Link to={project.to} data-reveal="" data-reveal-delay={String(index * 0.12)}
      className="project-tile group relative flex min-h-[30rem] min-w-0 flex-col justify-end overflow-hidden rounded-[1.6rem] border border-transparent text-[#f3ead8]">
      <img src={asset(project.image)} alt="" loading="lazy" decoding="async"
        className="absolute inset-0 -z-10 size-full object-cover transition-transform duration-[1.4s] ease-out group-hover:scale-[1.06]" />
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,#0b122200_25%,#0b1222e6_88%)]" />
      <div className="p-7 sm:p-8">
        <p className="text-[0.6rem] font-semibold tracking-[0.3em] text-[#ecd3a0] uppercase">{project.kicker}</p>
        <div className="mt-2 flex items-end justify-between gap-4">
          <h3 className="font-serif text-5xl font-light leading-none">{project.title}</h3>
          <span className="arrow-dot" aria-hidden="true"><ArrowUpRight className="size-5" /></span>
        </div>
        <p className="mt-4 max-w-[34ch] text-sm leading-relaxed text-[#f3ead8]/80">{project.description}</p>
        <span className="sr-only">{project.action}</span>
      </div>
    </Link>
  )
}

export function Home() {
  return (
    <>
      {/* Hero: the smoke loop under a night sky, the title, and live facts in a glass bar. */}
      <section className="dark night relative isolate flex min-h-[100svh] flex-col overflow-hidden text-foreground" id="overview">
        <video className="absolute inset-0 -z-30 size-full object-cover" src={asset("motion/hero-smoke.mp4")} poster={asset("img/photo-hero.webp")}
          autoPlay muted loop playsInline aria-hidden="true" data-parallax="14" />
        <div className="absolute inset-0 -z-20 bg-[radial-gradient(ellipse_at_50%_40%,#0b122255,#0b1222d9_70%),linear-gradient(180deg,#0b1222ee,#0b122255_30%,#0b122288_70%,#0b1222)]" />
        <StarField density={1.2} />
        <div className="site-width flex flex-1 flex-col items-center justify-center pt-40 pb-10 text-center">
          <p className="eyebrow justify-center" data-reveal="">Student research · Wildfire smoke</p>
          <h1 className="mt-7 text-[clamp(3.6rem,9.6vw,9.4rem)] leading-[0.9]" data-reveal="" data-reveal-delay="0.12">
            <span className="block font-light">Plan ahead for</span>
            <em className="gold-text block font-normal italic">wildfire smoke.</em>
          </h1>
          <div className="divider-star mt-8" data-reveal="" data-reveal-delay="0.22">✦</div>
          <p className="caps mt-7 text-[0.68rem] leading-loose text-[#f3ead8]/85" data-reveal="" data-reveal-delay="0.3">
            Daily air pollution estimates · up to three days ahead<br />with a range that shows how uncertain each forecast is
          </p>
        </div>
        <div className="site-width pb-[clamp(2rem,5vw,4rem)]" data-reveal="" data-reveal-delay="0.45"><LiveBar /></div>
      </section>

      {/* Welcome */}
      <Section className="!pb-0 text-center">
        <Script className="text-[clamp(5rem,12vw,9rem)]">Welcome</Script>
        <p className="caps mt-2 text-[0.66rem] text-muted-foreground" data-reveal="">to a student forecast for wildfire smoke</p>
        <div className="divider-star mt-8" aria-hidden="true">✦</div>
      </Section>

      <Section id="problem">
        <Split>
          <div className="relative" data-reveal="">
            <div className="gilded overflow-hidden rounded-[1.6rem]">
              <img src={asset("img/photo-research.webp")} alt="Smoke rising from the Hayes Fire over a forested mountain valley"
                className="aspect-[4/5] w-full scale-110 object-cover grayscale-[35%] sepia-[18%]" data-parallax="8" loading="lazy" />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">Hayes Fire, Olympic National Park. Courtesy of the National Park Service.</p>
          </div>
          <div>
            <Eyebrow>Why we built Serein</Eyebrow>
            <div className="brush">
              <Heading className="max-w-[13ch] text-[clamp(3rem,5.4vw,5.6rem)]">A little more time <em className="italic text-primary">to prepare.</em></Heading>
            </div>
            <Lead>When smoke could affect a practice, a shift, or a family’s plans, advance notice gives people time to prepare an alternative.</Lead>
            <p className="mt-4 max-w-xl text-muted-foreground" data-reveal="">SmokeCast learns from recent monitor readings and existing forecasts. We test how well it estimates pollution when nearby readings are limited.</p>
          </div>
        </Split>
      </Section>

      {/* Live side-by-side */}
      <Section tone="dark" id="compare">
        <Split className="md:grid-cols-[0.9fr_1.1fr]">
          <div>
            <Eyebrow dot>Latest published run</Eyebrow>
            <Heading className="max-w-[12ch] text-[clamp(3rem,5.6vw,5.8rem)]">NOAA’s forecast, <em className="gold-text italic">then ours.</em></Heading>
            <Lead>Drag the line to compare tomorrow’s average from NOAA’s forecast with the SmokeCast-adjusted version from the same run.</Lead>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-muted-foreground" data-reveal="">
              SmokeCast starts from NOAA’s forecasts and learns from recent monitor readings how to correct them. This is the real
              latest run, so on a clear day most of the West is simply “Good.” The daily average is the evaluated forecast.
            </p>
            <Button asChild className="mt-8 h-12 px-7"><Link to="/world">Open the full map <ArrowRight aria-hidden="true" /></Link></Button>
          </div>
          <div data-reveal="" data-reveal-delay="0.15"><ForecastCompare /></div>
        </Split>
      </Section>

      {/* The three parts of the project */}
      <Section id="project" className="text-center">
        <Script>The work</Script>
        <p className="caps mt-1 text-[0.66rem] text-muted-foreground" data-reveal="">Three parts of one project</p>
        <div className="mt-12 grid gap-5 text-left md:grid-cols-3">
          {projects.map((project, i) => <ProjectCard key={project.to} project={project} index={i} />)}
        </div>
      </Section>

      {/* Results with the dial */}
      <Section tone="dark" id="results">
        <Split className="md:grid-cols-[1fr_1fr]">
          <div>
            <Eyebrow>Development backtest · 2023</Eyebrow>
            <Heading className="max-w-[13ch] text-[clamp(3rem,5.6vw,5.8rem)]">What the forecasts <em className="gold-text italic">got right.</em></Heading>
            <Lead>SmokeCast estimated daily fine particulate matter (PM₂.₅) at matched places and dates. The warning comparison uses official reporting-area forecasts.</Lead>
          </div>
          <div data-reveal="" data-reveal-delay="0.1"><ForecastDial /></div>
        </Split>
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {[
            { kicker: "Three days ahead", value: <>{threeDay.serein}<span className="ml-1 font-sans text-lg text-muted-foreground">µg/m³</span></>, title: "Forecast error (RMSE)",
              note: `Versus ${threeDay.noaa} for the AQM → HRRR → persistence baseline. Lower is better.` },
            { kicker: "One day ahead", value: <>{headline.warnedSerein}%</>, title: "High-pollution area-days warned",
              note: `The official forecast warned on ${headline.warnedEpa}%. False alarms were ${headline.falseSerein} vs. ${headline.falseEpa}.` },
            { kicker: "One day ahead · withheld monitors", value: <>{headline.hiddenSerein}<span className="ml-1 font-sans text-lg text-muted-foreground">µg/m³</span></>, title: "Forecast error (RMSE)",
              note: `Versus ${headline.hiddenNoaa} for the same fallback baseline at withheld monitor locations.` },
          ].map((tile, i) => (
            <article key={tile.kicker} data-reveal="" data-reveal-delay={String(i * 0.12)} className="gilded rounded-2xl bg-[#111a30]/70 p-[clamp(1.6rem,3vw,2.5rem)] text-center backdrop-blur">
              <span className="text-gold" aria-hidden="true">✦</span>
              <p className="caps mt-3 text-[0.6rem] text-gold">{tile.kicker}</p>
              <p className="result-number mt-4">{tile.value}</p>
              <h3 className="mt-4 font-semibold">{tile.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{tile.note}</p>
            </article>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-xl text-sm text-muted-foreground">{SOURCE_DEV}</p>
          <Button asChild variant="outline" className="h-12 px-7"><Link to="/smokecast">See all results <ArrowRight aria-hidden="true" /></Link></Button>
        </div>
      </Section>

      <Section id="next">
        <Split className="items-start">
          <div>
            <Eyebrow>Project status</Eyebrow>
            <Heading className="max-w-[12ch] text-[clamp(3rem,5vw,5.4rem)]">What we’re testing <em className="italic text-primary">next.</em></Heading>
          </div>
          <ol className="space-y-4">
            {[
              ["Reserved seasons", "The team is preparing a final evaluation on the 2024–25 fire seasons. We’ll publish the results after the evaluation rules are frozen."],
              ["Timing of smoke spikes", "In development tests, the daily estimates were more useful than the hourly pattern for anticipating pollution levels. Precise arrival times need more research."],
              ["Use in practice", "We’re exploring how families and people who schedule outdoor activities could use a daily outlook alongside current air-quality information."],
            ].map(([term, description], i) => (
              <li key={term} data-reveal="" data-reveal-delay={String(i * 0.1)} className="gilded flex gap-5 rounded-2xl bg-card/70 p-6">
                <span className="font-serif text-4xl leading-none font-light text-primary">0{i + 1}</span>
                <div>
                  <h3 className="text-lg font-semibold">{term}</h3>
                  <p className="mt-2 text-muted-foreground">{description}</p>
                </div>
              </li>
            ))}
          </ol>
        </Split>
      </Section>

      <Section id="team" className="!pt-0 text-center">
        <Script>Falcon Devs</Script>
        <Heading className="mx-auto max-w-none text-[clamp(2.6rem,4.6vw,4.6rem)]">The team behind Serein</Heading>
        <p className="caps text-[0.64rem] text-muted-foreground" data-reveal="">Five students at Foothill High School</p>
        <ul className="mt-12 grid gap-4 text-left sm:grid-cols-2 xl:grid-cols-5">
          {team.map((member, i) => (
            <li key={member.name} data-reveal="" data-reveal-delay={String(i * 0.08)} className="gilded flex flex-col items-center rounded-2xl bg-card/80 p-6 text-center">
              <span className="grid size-16 place-items-center rounded-full border border-gold/60 font-serif text-2xl font-light text-primary">
                {member.name.split(" ").map(part => part[0]).join("")}
              </span>
              <h3 className="mt-4 text-base font-semibold">{member.name}</h3>
              <p className="caps mt-1 text-[0.58rem] text-primary">{member.grade}</p>
              {member.role && <p className="mt-3 text-sm text-muted-foreground">{member.role}</p>}
            </li>
          ))}
        </ul>
      </Section>
    </>
  )
}
