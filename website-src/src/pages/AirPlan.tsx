import { Link } from "react-router-dom"
import { ArrowDown, ArrowRight, CalendarDays, CloudSun, Wind } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader } from "@/components/ui/card"
import { PlanCards } from "@/components/site/PlanCards"
import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { asset } from "@/data/site"

const useCases = [
  { icon: CalendarDays, title: "Organize an activity", description: "If the outlook suggests higher pollution, consider lining up an indoor backup and choosing when to revisit the plan." },
  { icon: CloudSun, title: "Plan with your family", description: "Use the daily outlook to plan trips or outdoor time. Follow any care plan you already have and check official conditions before heading out." },
  { icon: Wind, title: "Prepare for an outdoor shift", description: "Use the outlook to prepare for potential smoke. Check current conditions and follow the applicable workplace guidance before a shift." },
]

export default function AirPlan() {
  return (
    <>
      <section className="dark relative isolate overflow-hidden bg-background text-foreground">
        <img src={asset("img/photo-family.webp")} width={1440} height={1080} alt=""
          className="absolute inset-0 -z-10 h-full w-full object-cover opacity-55" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-background via-background/85 to-background/35" />
        <div className="mx-auto w-[min(100%-2*clamp(1.25rem,5.5vw,6rem),82rem)] py-[clamp(5rem,11vw,9rem)]">
          <Eyebrow>Smoke planning</Eyebrow>
          <h1 className="mt-3 mb-5 text-[clamp(3.6rem,10vw,9rem)]">AirPlan</h1>
          <Lead className="max-w-[36ch]">See what the next three days could bring and give yourself time to prepare.</Lead>
          <Button asChild size="lg" className="mt-7"><Link to="/airplan#example">View the outlook <ArrowDown aria-hidden="true" /></Link></Button>
        </div>
      </section>

      <Section id="example">
        <Heading>Plan around the daily outlook.</Heading>
        <Lead>Choose a location for the daily PM₂.₅ estimate, forecast range, and suggestions for preparing.</Lead>
        <div className="mt-8"><PlanCards /></div>
      </Section>

      <Section className="pt-0">
        <Heading>How to use the forecast.</Heading>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {useCases.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="h-full">
              <CardHeader>
                <Icon aria-hidden="true" className="mb-2 size-6 text-primary" />
                <h3 className="text-xl font-semibold">{title}</h3>
                <CardDescription className="text-base">{description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium">
          <a href="https://www.airnow.gov/" className="underline underline-offset-4">Check current AQI on AirNow</a>
          <a href="https://www.airnow.gov/aqi/aqi-basics/using-air-quality-index/" className="underline underline-offset-4">Learn how AQI works</a>
          <a href="https://www.dir.ca.gov/title8/5141_1.html" className="underline underline-offset-4">California workplace smoke guidance</a>
        </div>
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
