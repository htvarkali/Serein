import { Link } from "react-router-dom"
import { ArrowDown, ArrowRight, ArrowUpRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { SOURCE_DEV, asset, headline, rmseByLead, team } from "@/data/site"

const threeDay = rmseByLead[3]

const projects = [
  {
    title: "SmokeCast",
    to: "/smokecast",
    image: "img/photo-research.webp",
    description: "Compare Serein’s daily forecasts with public benchmarks, including at withheld monitor locations.",
    action: "See the research",
  },
  {
    title: "Forecast map",
    to: "/world",
    image: "img/world-preview.webp",
    description: "Choose a place to see its daily estimate and range, or explore a recorded smoke event.",
    action: "Explore the map",
  },
  {
    title: "AirPlan",
    to: "/airplan",
    image: "img/photo-family.webp",
    description: "See how families and outdoor crews could use a forecast to plan ahead. Family examples use simulated histories.",
    action: "See planning examples",
  },
]

function ProjectCard({ project }: { project: (typeof projects)[number] }) {
  return (
    <Link to={project.to} className="project-tile group flex min-w-0 flex-col rounded-xl border bg-card text-foreground">
      <div className="overflow-hidden rounded-t-[inherit]">
        <img src={asset(project.image)} alt="" loading="lazy" decoding="async"
          className="aspect-[16/10] w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" />
      </div>
      <div className="flex flex-1 flex-col p-6 sm:p-7">
        <h3 className="font-serif text-4xl leading-none">{project.title}</h3>
        <p className="mt-3 mb-5 text-muted-foreground">{project.description}</p>
        <span className="mt-auto inline-flex items-center gap-2 text-sm font-semibold">
          {project.action} <ArrowUpRight aria-hidden="true" size={16} />
        </span>
      </div>
    </Link>
  )
}

export function Home() {
  return (
    <>
      <section className="serein-hero dark relative isolate flex items-center overflow-hidden bg-background text-foreground" id="overview">
        <img className="serein-hero-photo absolute inset-0 -z-20 size-full object-cover"
          src={asset("img/photo-hero.webp")} alt="" fetchPriority="high" decoding="async" width={1920} height={958} />
        <div className="serein-hero-shade absolute inset-0 -z-10" />
        <div className="site-width relative py-[clamp(4.75rem,9vw,9rem)]">
          <p className="serein-hero-label">Student research <span aria-hidden="true">/</span> Wildfire smoke</p>
          <h1 className="mt-6 text-[clamp(3.45rem,8.15vw,8rem)]">
            Plan ahead for <em className="block text-primary">wildfire smoke.</em>
          </h1>
          <p className="mt-6 max-w-lg text-[clamp(1.04rem,1.7vw,1.3rem)] leading-relaxed text-muted-foreground">
            Serein estimates daily air pollution up to three days ahead, with a range that shows how uncertain each forecast is.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="min-h-12 rounded-full px-6">
              <Link to="/world">Explore the forecast <ArrowRight aria-hidden="true" /></Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full bg-background/80 px-6">
              <Link to="/#results">See the evidence <ArrowDown aria-hidden="true" /></Link>
            </Button>
          </div>
        </div>
      </section>

      <Section id="problem" className="!py-[clamp(3.25rem,7vw,6rem)]">
        <Split className="items-start">
          <div>
            <Eyebrow>Why we built Serein</Eyebrow>
            <Heading className="max-w-[14ch] text-[clamp(2.9rem,5vw,5.35rem)]">A little more time to prepare</Heading>
          </div>
          <div className="max-w-xl space-y-4 md:pt-8">
            <Lead>When smoke could affect a practice, a shift, or a family’s plans, advance notice gives people time to prepare an alternative.</Lead>
            <p className="text-muted-foreground">SmokeCast learns from recent monitor readings and existing forecasts. We test how well it estimates pollution when nearby readings are limited.</p>
          </div>
        </Split>
      </Section>

      <Section id="project" className="!pt-0 !pb-[clamp(3.5rem,7vw,7rem)]">
        <div className="grid gap-5 md:grid-cols-3">
          {projects.map(project => <ProjectCard key={project.to} project={project} />)}
        </div>
      </Section>

      <Section tone="dark" id="results" className="!py-[clamp(3.5rem,7vw,7rem)]">
        <Eyebrow>Development backtest · 2023</Eyebrow>
        <Heading className="max-w-none text-[clamp(3rem,6vw,6rem)]">What the forecasts got right</Heading>
        <Lead>SmokeCast estimated daily fine particulate matter (PM₂.₅) at matched places and dates. The warning comparison uses official reporting-area forecasts.</Lead>
        <div className="mt-9 grid gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-3">
          <article className="result-tile bg-background p-[clamp(1.5rem,3vw,2.75rem)]">
            <p className="text-sm font-semibold text-muted-foreground">Three days ahead</p>
            <p className="result-number mt-3">{threeDay.serein}<span className="ml-1 text-lg text-muted-foreground">µg/m³</span></p>
            <h3 className="mt-3 font-semibold">Forecast error (RMSE)</h3>
            <p className="mt-2 text-sm text-muted-foreground">Versus {threeDay.noaa} for the AQM → HRRR → persistence baseline. Lower is better.</p>
          </article>
          <article className="result-tile bg-background p-[clamp(1.5rem,3vw,2.75rem)]">
            <p className="text-sm font-semibold text-muted-foreground">One day ahead</p>
            <p className="result-number mt-3">{headline.warnedSerein}%</p>
            <h3 className="mt-3 font-semibold">High-pollution area-days warned</h3>
            <p className="mt-2 text-sm text-muted-foreground">The official forecast warned on {headline.warnedEpa}%. False alarms were {headline.falseSerein} vs. {headline.falseEpa}.</p>
          </article>
          <article className="result-tile bg-background p-[clamp(1.5rem,3vw,2.75rem)]">
            <p className="text-sm font-semibold text-muted-foreground">One day ahead · withheld monitors</p>
            <p className="result-number mt-3">{headline.hiddenSerein}<span className="ml-1 text-lg text-muted-foreground">µg/m³</span></p>
            <h3 className="mt-3 font-semibold">Forecast error (RMSE)</h3>
            <p className="mt-2 text-sm text-muted-foreground">Versus {headline.hiddenNoaa} for the same fallback baseline at withheld monitor locations.</p>
          </article>
        </div>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-xl text-sm text-muted-foreground">{SOURCE_DEV}</p>
          <Button asChild variant="outline" className="min-h-11 rounded-full"><Link to="/smokecast">See all results <ArrowRight aria-hidden="true" /></Link></Button>
        </div>
      </Section>

      <Section id="next" className="!py-[clamp(3.5rem,7vw,7rem)]">
        <Split className="items-start">
          <div>
            <Eyebrow>Project status</Eyebrow>
            <Heading className="text-[clamp(2.9rem,5vw,5.35rem)]">What we’re testing next</Heading>
          </div>
          <dl className="divide-y divide-border border-y border-border">
            {[
              ["Reserved seasons", "The team is preparing a final evaluation on the 2024–25 fire seasons. We’ll publish the results after the evaluation rules are frozen."],
              ["Timing of smoke spikes", "In development tests, the daily estimates were more useful than the hourly pattern for anticipating pollution levels. Precise arrival times need more research."],
              ["Use in practice", "We’re exploring how families and people who schedule outdoor activities could use a daily outlook alongside current air-quality information."],
            ].map(([term, description]) => (
              <div key={term} className="py-5">
                <dt className="text-lg font-semibold">{term}</dt>
                <dd className="mt-2 text-muted-foreground">{description}</dd>
              </div>
            ))}
          </dl>
        </Split>
      </Section>

      <Section id="team" className="!pt-0 !pb-[clamp(3.5rem,7vw,6rem)]">
        <div className="border-t pt-9">
          <Eyebrow>Falcon Devs</Eyebrow>
          <Heading className="max-w-none text-[clamp(2.9rem,5vw,5.35rem)]">The team behind Serein</Heading>
          <p className="text-muted-foreground">Five students at Foothill High School.</p>
          <ul className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            {team.map(member => (
              <li key={member.name} className="rounded-xl border bg-card p-5">
                <h3 className="text-base font-semibold">{member.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{member.grade}</p>
                {member.role && <p className="mt-3 text-sm text-muted-foreground">{member.role}</p>}
              </li>
            ))}
          </ul>
        </div>
      </Section>
    </>
  )
}
