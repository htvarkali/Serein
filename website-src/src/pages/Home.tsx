import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { SOURCE_DEV, asset, headline, team } from "@/data/site"

// Same flow as the original home page: overview, problem, project, results, next steps, team.
function Stat({ value, label, sub }: { value: string; label: string; sub: string }) {
  return (
    <div className="border-t border-border pt-5">
      <div className="font-serif text-[clamp(3.5rem,7vw,6rem)] leading-none text-primary">{value}</div>
      <div className="mt-3 font-medium">{label}</div>
      <div className="mt-1 text-sm text-muted-foreground">{sub}</div>
    </div>
  )
}

function ProjectCard({ eyebrow, title, text, to, cta, image }: { eyebrow: string; title: string; text: string; to: string; cta: string; image: string }) {
  return (
    <Card className="overflow-hidden p-0">
      <img src={asset(image)} alt="" className="aspect-[16/10] w-full object-cover" />
      <CardContent className="space-y-3 p-6">
        <Eyebrow>{eyebrow}</Eyebrow>
        <h3 className="font-serif text-4xl">{title}</h3>
        <p className="text-muted-foreground">{text}</p>
        <Button asChild variant="link" className="px-0 text-base font-bold"><Link to={to}>{cta} <ArrowRight /></Link></Button>
      </CardContent>
    </Card>
  )
}

export function Home() {
  return (
    <>
      <section className="dark relative isolate overflow-hidden bg-background text-foreground" id="overview">
        <video className="absolute inset-0 -z-10 h-full w-full object-cover opacity-60" src={asset("motion/hero-smoke.mp4")}
          poster={asset("img/photo-hero.webp")} autoPlay muted loop playsInline aria-hidden="true" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-background via-background/70 to-transparent" />
        <div className="mx-auto w-[min(100%-2*clamp(1.25rem,5.5vw,6rem),82rem)] py-[clamp(6rem,14vw,12rem)]">
          <Eyebrow dot>Wildfire smoke research</Eyebrow>
          <h1 className="mt-4 text-[clamp(4rem,10vw,9rem)]">A clearer view of<br /><em className="text-primary">wildfire smoke.</em></h1>
          <p className="mt-6 max-w-xl text-[clamp(1.06rem,1.6vw,1.35rem)] text-muted-foreground">
            Serein forecasts smoke for every neighborhood in the western US, three days ahead and hour by hour, and turns
            it into a plan for the people who breathe it most.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg"><Link to="/world">Open Smoke World <ArrowRight /></Link></Button>
            <Button asChild size="lg" variant="outline"><Link to="/smokecast">See the results</Link></Button>
          </div>
        </div>
      </section>

      <Section id="problem">
        <Split>
          <div>
            <Eyebrow>The problem</Eyebrow>
            <Heading>Smoke crosses a region. Exposure varies locally.</Heading>
          </div>
          <div className="space-y-5">
            <Lead>When smoke arrives, people need to decide what tomorrow looks like: recess, practice, a shift outdoors.
              The official forecast covers whole metro areas and missed more than half of the unhealthy days in 2023.</Lead>
            <p className="text-muted-foreground">The gap is widest where there is no air monitor at all. In the lowest-income
              neighborhoods of the western US, 10.8% of people live 25 km or more from any EPA monitor, compared with 0.6% in
              the highest-income neighborhoods.</p>
          </div>
        </Split>
      </Section>

      <Section id="project" className="pt-0">
        <Eyebrow>The project</Eyebrow>
        <Heading>From a forecast to a decision.</Heading>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          <ProjectCard eyebrow="Forecast research" title="SmokeCast" to="/smokecast" cta="Explore the forecast" image="img/photo-research.webp"
            text="A graph neural network that corrects NOAA's smoke forecast with live readings from 425 air monitors, 0-3 days ahead, with an honest range." />
          <ProjectCard eyebrow="See it hour by hour" title="Smoke World" to="/world" cta="Open Smoke World" image="img/world-preview.png"
            text="Fly over the West on real terrain and watch the next 72 hours of smoke, wind and fires. Click any place for its forecast." />
          <ProjectCard eyebrow="Plans for people" title="AirPlan" to="/airplan" cta="Plan a day" image="img/photo-family.webp"
            text="The forecast as a plan for outdoor crews and families: what each of the next days looks like, what to do, and how much smoke a person breathes in." />
        </div>
      </Section>

      <Section tone="dark" id="results">
        <Eyebrow dot>Development results · 2023</Eyebrow>
        <Heading>How well did it do?</Heading>
        <Lead>On 2023 smoke-season weeks it never trained on, SmokeCast was compared with NOAA's best forecast and EPA's
          official AQI forecast on the same places and days. The reserved 2024-25 test runs once, after the rules are frozen.</Lead>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          <Stat value={`${headline.warnedSerein}%`} label="Unhealthy days warned a day ahead" sub={`EPA's official forecast: ${headline.warnedEpa}%, with more false alarms (${headline.falseEpa} vs ${headline.falseSerein}).`} />
          <Stat value={`${headline.rmseSerein}`} label="Next-day error, µg/m³" sub={`NOAA's best forecast: ${headline.rmseNoaa}. Lower is better.`} />
          <Stat value={`${headline.hiddenSerein}`} label="Error where there is no monitor" sub={`At monitors hidden from the model. NOAA: ${headline.hiddenNoaa}.`} />
        </div>
        <p className="mt-6 text-xs text-muted-foreground">{SOURCE_DEV}</p>
        <Button asChild className="mt-8"><Link to="/smokecast">All results and the August 2023 replay <ArrowRight /></Link></Button>
      </Section>

      <Section id="next">
        <Split className="items-start">
          <div>
            <Eyebrow>Project status</Eyebrow>
            <Heading>What comes next.</Heading>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {[
              ["The final test", "The rules are written down. On December 17 they are frozen, and the 2024-25 seasons are scored once."],
              ["Hour by hour", "Tested against real hourly readings: the correction beats NOAA hour by hour, but no forecast we tried can tell which hours of a day will be worst, so we only give advice for the day."],
              ["People", "Interviews with outdoor crews, farm managers and school nurses, and a review of the advice by a health professional."],
            ].map(([t, d]) => (
              <div key={t} className="py-6">
                <h3 className="text-xl font-medium">{t}</h3>
                <p className="mt-2 text-muted-foreground">{d}</p>
              </div>
            ))}
          </div>
        </Split>
      </Section>

      <Section id="team" className="pt-0">
        <Split className="items-start">
          <div>
            <Eyebrow>The team</Eyebrow>
            <Heading>Five students at Foothill High School.</Heading>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {team.map(m => (
              <div key={m.name} className="py-5">
                <h3 className="text-xl font-medium">{m.name}</h3>
                <p className="mt-1 text-muted-foreground">{m.grade}{m.role ? `. ${m.role}.` : "."}</p>
              </div>
            ))}
          </div>
        </Split>
      </Section>
    </>
  )
}
