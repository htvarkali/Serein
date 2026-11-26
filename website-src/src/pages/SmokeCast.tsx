import { Link } from "react-router-dom"
import { ArrowDown, ArrowRight, BookOpen, Network, Radar, SlidersHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { EquityChart, HiddenChart, RmseChart, WarningsChart } from "@/components/site/ResultCharts"
import { ReplayViewer } from "@/components/site/ReplayViewer"
import { Eyebrow, Heading, Lead, PageHero, Section, Split } from "@/components/site/Section"
import { SOURCE_DEV, asset, headline, rmseByLead } from "@/data/site"

const docs = "https://github.com/htvarkali/Serein/blob/main/docs"

const steps = [
  { icon: Radar, title: "Start with official forecasts", description: "Use NOAA’s forecasts, weather, and satellite smoke information to set the starting point." },
  { icon: Network, title: "Learn from nearby monitors", description: "A graph neural network learns how recent readings at neighboring monitors can correct that starting forecast." },
  { icon: SlidersHorizontal, title: "Estimate a range", description: "Average five trained models and calibrate their forecast range with development data. Use the range to see how much uncertainty remains." },
]

const review = [
  { title: "The reserved test", description: "The protocol reserves the 2024–25 fire seasons for evaluation after the methods are frozen. The results above come from development runs.", link: "BACKTEST_PROTOCOL.md", label: "Read the evaluation protocol" },
  { title: "Daily averages and hourly timing", description: "In development, scaling NOAA’s hourly values improved some comparisons with NOAA. Repeating SmokeCast’s daily estimate across every hour was as accurate or better than using the scaled hourly pattern. SmokeCast’s primary forecast is the daily average.", link: "HOURLY_ACCURACY.md", label: "Read the hourly study" },
  { title: "What the experiments taught us", description: "Several changes to the training data and model failed the team’s checks. Recalibration improved estimated warning probabilities in development without changing the point forecast.", link: "EXPERIMENTS.md", label: "Read the experiment log" },
]

export default function SmokeCast() {
  const dayThree = rmseByLead.find(row => row.lead === "Day 3")

  return (
    <>
      <PageHero eyebrow="Forecast research" title="SmokeCast" script="tested on held-out 2023 weeks"
        media={{ video: asset("motion/hayes-fire.mp4"), image: asset("img/photo-research.webp"), credit: "Hayes Fire, Olympic National Park. Courtesy of the National Park Service." }}
        lead={<>A daily outlook for wildfire smoke, up to three days ahead. SmokeCast learns from air-monitor readings and NOAA forecasts to
          estimate daily fine particle pollution (PM₂.₅), and each estimate comes with a range so people can plan around uncertainty.</>}>
        <Button asChild size="lg" className="h-12 px-7"><Link to="/smokecast#results">Compare forecasts <ArrowDown aria-hidden="true" /></Link></Button>
        <Button asChild variant="outline" size="lg" className="h-12 px-7"><Link to="/smokecast#replay">Replay a smoke week</Link></Button>
      </PageHero>

      <Section tone="dark" id="results">
        <Eyebrow>2023 development results</Eyebrow>
        <Heading>What changes across three days?</Heading>
        <Lead>See how daily pollution estimates and warning performance compare on matched locations and dates.</Lead>

        <Tabs defaultValue="error" className="mt-8">
          <TabsList aria-label="Choose a development result" className="grid h-auto! w-full grid-cols-2 gap-1 p-1 sm:max-w-3xl sm:grid-cols-4">
            <TabsTrigger value="error" className="min-h-11 whitespace-normal px-2">Forecast error</TabsTrigger>
            <TabsTrigger value="warnings" className="min-h-11 whitespace-normal px-2">Warnings</TabsTrigger>
            <TabsTrigger value="hidden" className="min-h-11 whitespace-normal px-2">Hidden monitors</TabsTrigger>
            <TabsTrigger value="equity" className="min-h-11 whitespace-normal px-2">Monitor access</TabsTrigger>
          </TabsList>
          <Card className="gilded mt-2 min-w-0">
            <TabsContent value="error" className="min-w-0">
              <CardHeader className="px-4 sm:px-6">
                <h3 className="text-lg font-semibold">Daily PM₂.₅ forecast error</h3>
                <CardDescription>
                  Lower root mean square error (RMSE) is better. Three days ahead, SmokeCast scored {dayThree?.serein.toFixed(1)}
                  {" "}vs. {dayThree?.noaa.toFixed(1)} µg/m³ for the benchmark. The benchmark uses AQM, then HRRR,
                  then the previous day’s level when both forecasts are unavailable.
                </CardDescription>
              </CardHeader>
              <CardContent className="px-3 sm:px-6"><RmseChart /></CardContent>
            </TabsContent>
            <TabsContent value="warnings" className="min-w-0">
              <CardHeader className="px-4 sm:px-6">
                <h3 className="text-lg font-semibold">High-pollution days caught</h3>
                <CardDescription>
                  One day ahead, SmokeCast caught {headline.warnedSerein}% of days with unhealthy conditions for sensitive groups
                  or worse, versus {headline.warnedEpa}% for the official AirNow forecast, with {headline.falseSerein} versus
                  {" "}{headline.falseEpa} false alarms. At two days, SmokeCast caught more events and raised more false alarms
                  (48 versus 36).
                </CardDescription>
              </CardHeader>
              <CardContent className="px-3 sm:px-6"><WarningsChart /></CardContent>
            </TabsContent>
            <TabsContent value="hidden" className="min-w-0">
              <CardHeader className="px-4 sm:px-6">
                <h3 className="text-lg font-semibold">Next-day error at hidden monitors</h3>
                <CardDescription>
                  Monitors are grouped by distance to the nearest visible monitor. In the 30–60 km group, SmokeCast scored
                  7.8 vs. 12.3 µg/m³ for the benchmark across 21 sites. The group beyond 60 km had three sites and is omitted here.
                </CardDescription>
              </CardHeader>
              <CardContent className="px-3 sm:px-6"><HiddenChart /></CardContent>
            </TabsContent>
            <TabsContent value="equity" className="min-w-0">
              <CardHeader className="px-4 sm:px-6">
                <h3 className="text-lg font-semibold">Who lives far from an EPA monitor?</h3>
                <CardDescription>
                  This coverage study groups census tracts by household income across the six-state study area.
                  The figures count regulatory PM₂.₅ monitors and exclude community sensors such as PurpleAir.
                </CardDescription>
              </CardHeader>
              <CardContent className="px-3 sm:px-6"><EquityChart /></CardContent>
            </TabsContent>
          </Card>
        </Tabs>
        <p className="mt-4 text-sm text-muted-foreground">{SOURCE_DEV}</p>
      </Section>

      <Section id="replay">
        <Eyebrow>August 15–21, 2023</Eyebrow>
        <Heading>Replay a smoke week.</Heading>
        <Lead>Compare the forecasts made the day before with the next day’s monitor readings in the Pacific Northwest.</Lead>
        <ReplayViewer />
        <p className="mt-4 max-w-3xl text-sm text-muted-foreground">
          Each column is an EPA monitor. Height shows daily PM₂.₅ and color shows the daily AQI category.
          A forecast flags a monitor when its daily estimate reaches 35.5 µg/m³.
        </p>
        <Button asChild variant="outline" className="mt-5"><Link to="/world?mode=aug2023">Open the archived map <ArrowRight aria-hidden="true" /></Link></Button>
      </Section>

      <Section className="pt-0">
        <Heading>How SmokeCast works.</Heading>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {steps.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="gilded h-full" data-reveal="">
              <CardHeader>
                <Icon aria-hidden="true" className="mb-2 size-7 text-primary" strokeWidth={1.3} />
                <h3 className="text-xl font-semibold">{title}</h3>
                <CardDescription className="text-base">{description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </Section>

      <Section id="evaluation" className="pt-0">
        <Split className="items-start">
          <div>
            <Heading>What the model still needs to prove.</Heading>
            <Lead>Reliable warnings at longer leads are the next challenge. Heavy pollution peaks still tend to be underestimated.</Lead>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {review.map(({ title, description, link, label }) => (
              <div key={title} className="py-5">
                <h3 className="text-xl font-medium">{title}</h3>
                <p className="mt-2 text-muted-foreground">{description}</p>
                <a href={`${docs}/${link}`} className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-primary underline underline-offset-4">
                  <BookOpen aria-hidden="true" className="size-4" />{label}
                </a>
              </div>
            ))}
          </div>
        </Split>
      </Section>

      <Section tone="dark">
        <Split>
          <Heading>Use the forecast to plan ahead.</Heading>
          <div className="space-y-5">
            <Lead>See the expected daily pollution and uncertainty for a selected location in AirPlan.</Lead>
            <Button asChild size="lg"><Link to="/airplan">Open AirPlan <ArrowRight aria-hidden="true" /></Link></Button>
          </div>
        </Split>
      </Section>
    </>
  )
}
