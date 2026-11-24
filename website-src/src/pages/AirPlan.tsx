import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PlanCards } from "@/components/site/PlanCards"
import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { asset } from "@/data/site"
import { BREATHING } from "@/data/exposure"

// Same order as the original AirPlan page: introduction, an example, how it works, and
// the proposed pilot. The example now uses the live forecast instead of a fictional child.
export default function AirPlan() {
  return (
    <>
      <section className="dark relative isolate overflow-hidden bg-background text-foreground">
        <video className="absolute inset-0 -z-10 h-full w-full object-cover opacity-50" src={asset("motion/lake.mp4")}
          poster={asset("img/photo-family.webp")} autoPlay muted loop playsInline aria-hidden="true" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-background via-background/75 to-transparent" />
        <div className="mx-auto w-[min(100%-2*clamp(1.25rem,5.5vw,6rem),82rem)] py-[clamp(6rem,12vw,10rem)]">
          <Eyebrow>For people</Eyebrow>
          <h1 className="mt-3 mb-4 text-[clamp(4rem,10vw,9rem)]">AirPlan</h1>
          <Lead className="max-w-[34ch]">What should a smoke forecast mean for a crew's shift or a family's afternoon?</Lead>
        </div>
      </section>

      <Section id="example">
        <Eyebrow>Live forecast</Eyebrow>
        <Heading>Plan the next three days.</Heading>
        <Lead>Pick a place and who it is for. Each day shows the average smoke, the smokiest and cleanest hours, and what to do.</Lead>
        <div className="mt-8"><PlanCards /></div>
      </Section>

      <Section className="pt-0">
        <Split className="items-start">
          <div>
            <Eyebrow>How it works</Eyebrow>
            <Heading>What does a person breathe in?</Heading>
          </div>
          <div className="space-y-5">
            <Lead>A child running at recess breathes several times more air than a child sitting in class, so the same smoke
              gives a bigger dose. AirPlan uses published breathing rates for each age and activity.</Lead>
            <div className="divide-y divide-border border-y border-border">
              {Object.values(BREATHING).map(b => (
                <div key={b.label} className="flex items-baseline justify-between gap-4 py-3">
                  <span>{b.label}</span>
                  <span className="whitespace-nowrap font-medium">{b.m3PerHour.toFixed(1)} m³ of air an hour</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">Source: US EPA Exposure Factors Handbook (2011), Table 6-2, mean values.
              Smoke World multiplies these by the hourly forecast at any place you click, and compares the result with Berkeley
              Earth's rough rule that breathing 22 µg/m³ for a day is about as harmful as one cigarette.</p>
            <Button asChild><Link to="/world">Try it in Smoke World <ArrowRight /></Link></Button>
          </div>
        </Split>
      </Section>

      <Section className="pt-0">
        <Eyebrow>Built on existing rules</Eyebrow>
        <Heading>Advice people already follow.</Heading>
        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <Card><CardHeader>
            <CardTitle className="text-xl">Outdoor crews</CardTitle>
            <CardDescription className="text-base">California's wildfire smoke rule (Title 8, §5141.1) applies when the current
              AQI for PM2.5 reaches 151, and tells employers to check AQI forecasts at the start of each shift: move work, change
              schedules, add rest, and offer N95s. Above 500, respirators are required. AirPlan gives three days to plan, and
              never replaces the current-AQI check.</CardDescription>
          </CardHeader></Card>
          <Card><CardHeader>
            <CardTitle className="text-xl">Families</CardTitle>
            <CardDescription className="text-base">EPA's AQI guidance tells sensitive groups (people with asthma, children,
              older adults) to cut back outdoor activity as levels rise. AirPlan points to the hours when that matters and the
              cleaner hours when it doesn't. It is general guidance, not medical advice.</CardDescription>
          </CardHeader></Card>
        </div>
      </Section>

      <Section tone="dark" id="pilot">
        <Split>
          <div>
            <Eyebrow>Proposed research</Eyebrow>
            <Heading>What would a pilot test?</Heading>
          </div>
          <div className="space-y-4">
            <Lead>Whether outdoor crews and families change plans when they get a three-day smoke outlook, and whether the
              advice is clear.</Lead>
            <p className="text-muted-foreground">We are starting with interviews of outdoor workers, farm managers and school
              nurses. Any study with real people would need consent, an adult advisor and review of the advice by a health
              professional. No personal health data is collected on this site.</p>
          </div>
        </Split>
      </Section>
    </>
  )
}
