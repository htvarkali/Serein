import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { sources } from "@/data/site"

export default function About() {
  return (
    <>
      <Section>
        <Eyebrow>Data & methods</Eyebrow>
        <h1 className="mt-3 mb-5 text-[clamp(4rem,10vw,9rem)]">How Serein works</h1>
        <Lead>Everything here comes from free public data or a named model, and every result says what it was tested on.</Lead>
      </Section>
      <Section className="pt-0">
        <Split className="items-start">
          <div>
            <Eyebrow>The forecast</Eyebrow>
            <Heading>What goes in.</Heading>
          </div>
          <div className="space-y-4 text-muted-foreground">
            <p>Every day at 11:30 AM Pacific, SmokeCast reads NOAA's smoke (HRRR-Smoke) and air-quality (AQM) forecasts, the
              weather, satellite smoke plumes and fire detections, and the latest readings from 425 EPA monitors in the western US.</p>
            <p>A graph neural network treats nearby monitors as neighbors and learns how NOAA's forecast tends to be wrong. Five
              copies are averaged, and each forecast comes with a 90% range calibrated to hold about 90% of the time.</p>
            <p>Smoke World and AirPlan show NOAA's hour-by-hour shape, scaled each day to SmokeCast's daily forecast. Forecast
              squares are about 25 km; terrain, photos and buildings are shown for context only.</p>
          </div>
        </Split>
      </Section>
      <Section className="pt-0">
        <Split className="items-start">
          <div>
            <Eyebrow>Honesty</Eyebrow>
            <Heading>How we keep it fair.</Heading>
          </div>
          <div className="space-y-4 text-muted-foreground">
            <p>The model never trains on the days it is scored on. Training uses 2021-22, development uses 2023, and the 2024-25
              seasons are locked for one final test, run once under rules published before the run.</p>
            <p>Each new idea must beat the current model on a fixed statistical test before it is used. Ideas that fail stay in
              the public experiment log.</p>
            <p>Health advice follows EPA, CDC and California guidance. It is general guidance for groups, not medical advice.</p>
          </div>
        </Split>
      </Section>
      <Section tone="dark">
        <Eyebrow>Data sources</Eyebrow>
        <Heading>Thank you to the people who share this data.</Heading>
        <div className="mt-8 divide-y divide-border border-y border-border">
          {sources.map(s => (
            <div key={s.name} className="grid gap-1 py-4 md:grid-cols-[1fr_2fr_1fr]">
              <div className="font-medium">{s.name}</div>
              <div className="text-muted-foreground">{s.what}</div>
              <div className="text-sm text-muted-foreground md:text-right">{s.license}</div>
            </div>
          ))}
        </div>
        <p className="mt-6 text-sm text-muted-foreground">Breathing rates: US EPA Exposure Factors Handbook (2011), Table 6-2.
          Cigarette comparison: Berkeley Earth, "Air Pollution and Cigarette Equivalence" (Muller and Muller), a rough rule of thumb.
          Code: <a className="underline" href="https://github.com/htvarkali/Serein">github.com/htvarkali/Serein</a>.</p>
      </Section>
    </>
  )
}
