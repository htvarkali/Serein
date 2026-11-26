import { ArrowRight, Code } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Heading, PageHero, Section, Split } from "@/components/site/Section"
import { asset, sources } from "@/data/site"

const repository = "https://github.com/htvarkali/Serein"
const docs = `${repository}/blob/main/docs`

const references = [
  { title: "Model methods", file: "METHODS.md", description: "Inputs, the monitor network, and how forecast ranges are calibrated." },
  { title: "Backtest protocol", file: "BACKTEST_PROTOCOL.md", description: "Forecast issue times, baselines, metrics, and the reserved test seasons." },
  { title: "Experiment log", file: "EXPERIMENTS.md", description: "What changed the results, and which model ideas the team rejected." },
  { title: "Hourly analysis", file: "HOURLY_ACCURACY.md", description: "Evidence on daily levels and the timing of pollution within a day." },
]

export default function About() {
  return (
    <>
      <PageHero eyebrow="Data and methods" title="How Serein works" script="methods"
        media={{ image: asset("img/world-preview.webp") }}
        lead="Serein is a student research project studying whether recent local readings can improve wildfire smoke forecasts.">
        <Button asChild variant="outline" size="lg" className="h-12 px-7"><a href={repository}><Code aria-hidden="true" /> View the project on GitHub</a></Button>
      </PageHero>
      <Section className="pt-0">
        <Split className="items-start">
          <Heading>From data to a daily outlook.</Heading>
          <div className="space-y-4 text-muted-foreground">
            <p>SmokeCast combines archived NOAA smoke and air-quality forecasts with weather, satellite observations, and recent readings from EPA air monitors across the study region.</p>
            <p>A graph neural network learns how nearby measurements can correct the forecast at a location. An ensemble of five models estimates daily PM₂.₅ for the issue day and the following three days, with a calibrated range.</p>
            <p>Forecasts on the map represent an area. The map’s hourly layer uses NOAA’s hourly pattern, and the research results report daily and hourly comparisons separately.</p>
          </div>
        </Split>
      </Section>
      <Section className="pt-0">
        <Split className="items-start">
          <Heading>How we evaluate the forecasts.</Heading>
          <div className="space-y-5 text-muted-foreground">
            <p>The team fitted SmokeCast on 2021–22 fire seasons and developed it using 2023. The draft protocol reserves 2024–25 for the final evaluation after the methods are frozen.</p>
            <p>Results are matched by date and location. The team compares daily errors, warning tradeoffs, and performance at sites whose readings are hidden from the model.</p>
            <ul className="divide-y divide-border border-y border-border">
              {references.map(({ title, file, description }) => (
                <li key={file} className="py-4">
                  <a href={`${docs}/${file}`} className="inline-flex items-center gap-2 font-medium text-primary underline underline-offset-4">
                    {title} <ArrowRight aria-hidden="true" className="size-4" />
                  </a>
                  <p className="mt-1 text-sm">{description}</p>
                </li>
              ))}
            </ul>
          </div>
        </Split>
      </Section>
      <Section tone="dark">
        <Heading>Sources and acknowledgments.</Heading>
        <dl className="mt-8 divide-y divide-border border-y border-border">
          {sources.map(({ name, what, license }) => (
            <div key={name} className="grid gap-1 py-4 md:grid-cols-[1fr_2fr_1fr] md:gap-5">
              <dt className="font-medium">{name}</dt>
              <dd className="text-muted-foreground">{what}</dd>
              <dd className="text-sm text-muted-foreground md:text-right">{license}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-6 max-w-3xl text-sm text-muted-foreground">
          Breathing rates used in the map’s educational example come from the US EPA Exposure Factors Handbook (2011), Table 6-2.
          The example illustrates how activity can change estimated exposure.
        </p>
      </Section>
    </>
  )
}
