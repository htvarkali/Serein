import { Link } from "react-router-dom"
import { ArrowDown, ArrowRight, CalendarDays, CloudSun, Wind } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader } from "@/components/ui/card"
import { PlanCards } from "@/components/site/PlanCards"
import { Eyebrow, Heading, Lead, PageHero, Section, Split } from "@/components/site/Section"
import { asset } from "@/data/site"

const useCases = [
  { icon: CalendarDays, title: "Organize an activity", description: "If the outlook suggests higher pollution, consider lining up an indoor backup and choosing when to revisit the plan." },
  { icon: CloudSun, title: "Plan with your family", description: "Use the daily outlook to plan trips or outdoor time. Follow any care plan you already have and check official conditions before heading out." },
  { icon: Wind, title: "Prepare for an outdoor shift", description: "Use the outlook to prepare for potential smoke. Check current conditions and follow the applicable workplace guidance before a shift." },
]

export default function AirPlan() {
  return (
    <>
      <PageHero eyebrow="Smoke planning" title="AirPlan" script="plan with the range, not just the number"
        media={{ video: asset("motion/lake.mp4"), image: asset("img/photo-family.webp") }}
        lead="See what the next three days could bring and give yourself time to prepare.">
        <Button asChild size="lg" className="h-12 px-7"><Link to="/airplan#example">View the outlook <ArrowDown aria-hidden="true" /></Link></Button>
      </PageHero>

      <Section id="example">
        <Heading>Plan around the daily outlook.</Heading>
        <Lead>Choose a location for the daily PM₂.₅ estimate, forecast range, and suggestions for preparing.</Lead>
        <div className="mt-8"><PlanCards /></div>
      </Section>

      <Section className="pt-0">
        <Heading>How to use the forecast.</Heading>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {useCases.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="outlined h-full" data-reveal="">
              <CardHeader>
                <Icon aria-hidden="true" className="mb-2 size-7 text-primary" strokeWidth={1.3} />
                <h3 className="text-xl font-semibold">{title}</h3>
                <CardDescription className="text-base">{description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-1 text-sm font-medium">
          <a href="https://www.airnow.gov/" className="py-1.5 underline underline-offset-4">Check current AQI on AirNow</a>
          <a href="https://www.airnow.gov/aqi/aqi-basics/using-air-quality-index/" className="py-1.5 underline underline-offset-4">Learn how AQI works</a>
          <a href="https://www.dir.ca.gov/title8/5141_1.html" className="py-1.5 underline underline-offset-4">California workplace smoke guidance</a>
        </div>
      </Section>

      <Section id="child-plan" className="pt-0">
        <Split>
          <div>
            <Eyebrow>In testing, not yet public</Eyebrow>
            <Heading>A plan for one child with asthma.</Heading>
            <Lead>The outlook above is the same for everyone. Serein’s second part learns how strongly one child reacts to smoke and turns tomorrow’s forecast into a green, yellow or red plan for that child.</Lead>
          </div>
          <div className="space-y-4" data-reveal="">
            <ol className="list-decimal space-y-2 pl-5 text-base leading-relaxed">
              <li>Each evening a parent answers six questions with taps: symptoms, quick-relief inhaler puffs, night waking, time outdoors, a cold, and the daily controller medicine.</li>
              <li>A small statistical model learns from those answers how much that child’s symptoms rise on smoky days.</li>
              <li>The plan combines that with the forecast range. A forecast of air unhealthy for sensitive groups is always at least yellow, whatever the child’s log says, and every plan points back to the child’s own asthma action plan from their doctor.</li>
            </ol>
            <figure>
              <img src={asset("img/demo-family-plan.webp")} width={552} height={388} loading="lazy"
                alt="Demo app screenshot: a red plan for a fictional child, Maya, two days ahead, with the smoke forecast, her chance of symptoms and steps such as staying indoors with an air purifier and keeping the rescue inhaler close."
                className="w-full rounded-xl border bg-white" />
              <figcaption className="mt-2 text-sm text-muted-foreground">The family plan in our demo app, for a fictional child.</figcaption>
            </figure>
            <p className="text-sm text-muted-foreground">So far this has been tested only on simulated children. It stays in the demo app until a clinician has reviewed the wording and we have talked with families. The code is in the{" "}
              <a href="https://github.com/htvarkali/Serein/tree/main/src/serein/personal" className="underline underline-offset-4">project repository</a>.</p>
          </div>
        </Split>
      </Section>

      <Section tone="dark" id="pilot">
        <Split>
          <div>
            <Eyebrow>Project status</Eyebrow>
            <Heading>What would earlier notice change?</Heading>
          </div>
          <div className="space-y-5">
            <Lead>AirPlan is a research prototype. A proposed pilot would ask activity organizers and families whether the outlook gives them enough time to prepare and whether the range is easy to understand.</Lead>
            <p className="text-sm text-muted-foreground">This site collects no personal health information. The daily outlook supports planning. Use current official air-quality information and your organization’s policy to make activity decisions.</p>
            <Button asChild variant="outline" size="lg"><Link to="/smokecast">See the forecast evidence <ArrowRight aria-hidden="true" /></Link></Button>
          </div>
        </Split>
      </Section>
    </>
  )
}
