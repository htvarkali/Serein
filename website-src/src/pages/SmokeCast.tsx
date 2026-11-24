import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { EquityChart, HiddenChart, RmseChart, WarningsChart } from "@/components/site/ResultCharts"
import { ReplayViewer } from "@/components/site/ReplayViewer"
import { Eyebrow, Heading, Lead, Section, Split } from "@/components/site/Section"
import { SOURCE_DEV, asset, headline } from "@/data/site"

// Same order as the original SmokeCast page: introduction, results, how it works,
// what remains to test, then a link onward. The August 2023 replay is new.
export default function SmokeCast() {
  return (
    <>
      <Section>
        <Split>
          <div>
            <Eyebrow>The forecast model</Eyebrow>
            <h1 className="mt-3 mb-4 text-[clamp(4rem,10vw,9rem)]">SmokeCast</h1>
            <Lead className="max-w-[30ch]">A local view of how smoke may move over the next three days.</Lead>
            <p className="mt-4 text-muted-foreground">
              SmokeCast uses readings from air monitors to correct NOAA's forecasts. It estimates fine particle pollution,
              called PM2.5, for each day and gives a range of likely values.
            </p>
            <Button asChild className="mt-6"><a href="#results">Explore the results ↓</a></Button>
          </div>
          <figure>
            <img src={asset("img/world-preview.png")} alt="Smoke World view of the August 2023 Pacific Northwest smoke forecast"
              className="w-full rounded-lg border shadow-xl" />
            <figcaption className="mt-3 text-sm text-muted-foreground">August 2023 Pacific Northwest smoke event in Smoke World.</figcaption>
          </figure>
        </Split>
      </Section>

      <Section tone="dark" id="results">
        <Eyebrow>Development results · 2023</Eyebrow>
        <Heading>How far ahead can we see?</Heading>
        <Lead>Compare SmokeCast with NOAA's best forecast and EPA's official forecast at the same places and dates.</Lead>
        <Tabs defaultValue="error" className="mt-10">
          <TabsList className="flex h-auto flex-wrap">
            <TabsTrigger value="error">Forecast error</TabsTrigger>
            <TabsTrigger value="warnings">Warnings vs. EPA</TabsTrigger>
            <TabsTrigger value="hidden">No monitor nearby</TabsTrigger>
            <TabsTrigger value="equity">Who lacks a monitor</TabsTrigger>
          </TabsList>
          <Card className="mt-4">
            <TabsContent value="error"><CardHeader><CardTitle>Typical miss (RMSE, µg/m³), lower is better</CardTitle>
              <CardDescription>Next day: {headline.rmseSerein} vs. {headline.rmseNoaa} for NOAA's best forecast.</CardDescription></CardHeader>
              <CardContent><RmseChart /></CardContent></TabsContent>
            <TabsContent value="warnings"><CardHeader><CardTitle>Unhealthy days warned ahead (%)</CardTitle>
              <CardDescription>False alarms a day ahead: SmokeCast {headline.falseSerein}, EPA {headline.falseEpa}. Two days ahead SmokeCast warns more and has more false alarms (48 vs. 36), a real tradeoff.</CardDescription></CardHeader>
              <CardContent><WarningsChart /></CardContent></TabsContent>
            <TabsContent value="hidden"><CardHeader><CardTitle>Error at monitors hidden from the model</CardTitle>
              <CardDescription>By distance to the nearest monitor it could see, next day. The 60+ km group has only 3 sites and is left out.</CardDescription></CardHeader>
              <CardContent><HiddenChart /></CardContent></TabsContent>
            <TabsContent value="equity"><CardHeader><CardTitle>People living far from any monitor (%)</CardTitle>
              <CardDescription>By neighborhood income, 6 western states, about 56 million people (Census ACS 2019-2023).</CardDescription></CardHeader>
              <CardContent><EquityChart /></CardContent></TabsContent>
          </Card>
        </Tabs>
        <p className="mt-4 text-xs text-muted-foreground">{SOURCE_DEV}</p>
      </Section>

      <Section id="replay">
        <Eyebrow>Real data · August 15-21, 2023</Eyebrow>
        <Heading>Replay a smoke week.</Heading>
        <Lead>Each column is an EPA air monitor in Washington, Oregon or Idaho: height is the daily PM2.5, color the AQI
          level. Left and middle are forecasts made the day before; right is what happened.</Lead>
        <div className="mt-8"><ReplayViewer /></div>
        <p className="mt-4 max-w-3xl text-sm text-muted-foreground">
          "Flagged" counts monitors whose day-ahead forecast was at or above 35.5 µg/m³ among those that really reached it.{" "}
          <Link className="underline" to="/world?mode=aug2023">See this week hour by hour in Smoke World</Link>.
        </p>
      </Section>

      <Section className="pt-0">
        <Eyebrow>How it works</Eyebrow>
        <Heading>From nearby readings to a local forecast.</Heading>
        <Lead>SmokeCast brings air-quality observations, weather forecasts and satellite smoke information into one model.</Lead>
        <ol className="mt-10 grid gap-5 md:grid-cols-3">
          {[
            ["Begin with NOAA forecasts", "The model starts from NOAA's smoke and air-quality forecasts and learns how to adjust them using recent observations."],
            ["Connect nearby monitors", "A graph neural network lets each location use what nearby monitors see. It trains with some readings hidden, so it can forecast where there is no monitor."],
            ["Show the uncertainty", "Five copies of the model are averaged and every forecast has a range calibrated to hold the true value about 90% of the time."],
          ].map(([t, d], i) => (
            <li key={t}><Card className="h-full"><CardHeader>
              <span className="font-serif text-5xl text-muted-foreground">{i + 1}</span>
              <CardTitle className="mt-2 text-xl">{t}</CardTitle>
              <CardDescription className="text-base">{d}</CardDescription>
            </CardHeader></Card></li>
          ))}
        </ol>
      </Section>

      <Section id="evaluation" className="pt-0">
        <Split className="items-start">
          <div>
            <Eyebrow>Evaluation</Eyebrow>
            <Heading>What remains to test.</Heading>
          </div>
          <div className="divide-y divide-border border-y border-border">
            {[
              ["The final test", "The 2024-25 seasons have never been scored. The rules are written down in advance and run once after the December 17 freeze, including where SmokeCast loses."],
              ["What did not work", "Nine attempts to improve accuracy failed our fixed test: bigger models, more seasons, fire and satellite inputs, and five ways of blending forecasters. Each is in the public experiment log."],
              ["What did", "Warning probabilities recalibrated so that 60% really means about 60%, and a low-confidence flag that marks the days with the largest misses."],
              ["Hour by hour", "Against real hourly readings, the corrected hourly values beat NOAA's, but neither tells which hours of a day will be worst. A flat daily value is as accurate, so advice is given per day."],
            ].map(([t, d]) => (
              <div key={t} className="py-6"><h3 className="text-xl font-medium">{t}</h3><p className="mt-2 text-muted-foreground">{d}</p></div>
            ))}
          </div>
        </Split>
      </Section>

      <Section tone="dark">
        <Split>
          <div>
            <Eyebrow>For people</Eyebrow>
            <Heading>What could a forecast mean for your day?</Heading>
          </div>
          <div className="space-y-5">
            <Lead>AirPlan turns the forecast into a plan for each of the next days, for outdoor crews and families.</Lead>
            <Button asChild><Link to="/airplan">Explore AirPlan <ArrowRight /></Link></Button>
          </div>
        </Split>
      </Section>
    </>
  )
}
