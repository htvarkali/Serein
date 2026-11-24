import { Link } from "react-router-dom"
import { ArrowRight, CloudFog, HardHat, Map, ShieldCheck, Users, Wind } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SOURCE_DEV, asset, headline, team } from "@/data/site"

function Stat({ value, label, sub }: { value: string; label: string; sub: string }) {
  return (
    <Card className="bg-card/70">
      <CardContent className="p-6">
        <div className="font-serif text-6xl leading-none text-primary">{value}</div>
        <div className="mt-3 font-medium">{label}</div>
        <div className="mt-1 text-sm text-muted-foreground">{sub}</div>
      </CardContent>
    </Card>
  )
}

export function Home() {
  return (
    <>
      <section className="relative isolate overflow-hidden">
        <video className="absolute inset-0 -z-10 h-full w-full object-cover opacity-45" src={asset("motion/hero-smoke.mp4")}
          autoPlay muted loop playsInline aria-hidden="true" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-background/30 via-background/60 to-background" />
        <div className="mx-auto max-w-6xl px-5 pb-24 pt-28 md:pt-40">
          <Badge variant="secondary" className="mb-6">Conrad Challenge 2026-27 · Health & Nutrition</Badge>
          <h1 className="max-w-4xl text-balance text-6xl leading-[0.95] md:text-8xl">
            Wildfire smoke, <em className="text-primary">three days</em> before it reaches you.
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
            Serein forecasts smoke for every neighborhood in the western US, hour by hour, and turns it into a plan
            for the people who breathe it most. On held-out 2023 smoke days it warned a day ahead on
            {" "}{headline.warnedSerein}% of unhealthy days. The official forecast caught {headline.warnedEpa}%.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg"><Link to="/world">Open Smoke World <ArrowRight /></Link></Button>
            <Button asChild size="lg" variant="secondary"><Link to="/results">See the evidence</Link></Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5">
        <div className="grid gap-4 md:grid-cols-3">
          <Stat value={`${headline.warnedSerein}%`} label="Unhealthy days warned a day ahead"
            sub={`EPA's official forecast: ${headline.warnedEpa}%, with more false alarms (${headline.falseEpa} vs ${headline.falseSerein}).`} />
          <Stat value={`${Math.round((1 - headline.rmseSerein / headline.rmseNoaa) * 100)}%`} label="Smaller error than NOAA, next day"
            sub={`Typical miss ${headline.rmseSerein} vs ${headline.rmseNoaa} µg/m³ (RMSE).`} />
          <Stat value="18x" label="The monitor gap"
            sub="People in the lowest-income neighborhoods are 18 times as likely to live 25+ km from any air monitor." />
        </div>
        <p className="mt-3 text-xs text-muted-foreground">{SOURCE_DEV}</p>
      </section>

      <section className="mx-auto mt-28 max-w-6xl px-5">
        <h2 className="text-5xl md:text-6xl">How it works</h2>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            { icon: Wind, title: "Read everything at 11:30 AM", text: "NOAA's smoke and air-quality models, the weather, satellite fire detections and what 425 EPA monitors measure right now." },
            { icon: CloudFog, title: "Correct NOAA with live sensors", text: "A graph neural network treats monitors as neighbors: if the monitor upwind just jumped, yours is next. It forecasts days 0-3 with an honest range." },
            { icon: HardHat, title: "Turn it into a plan", text: "Hour-by-hour smoke, the chance of unhealthy air, a low-confidence flag, and what to do: move a shift, keep recess indoors, have N95s ready." },
          ].map(({ icon: Icon, title, text }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="size-6 text-primary" />
                <CardTitle className="mt-3 text-xl">{title}</CardTitle>
                <CardDescription className="text-base">{text}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto mt-28 max-w-6xl px-5">
        <Card className="overflow-hidden">
          <div className="grid md:grid-cols-[1.1fr_1fr]">
            <div className="relative min-h-72">
              <img src={asset("img/world-preview.png")} alt="Smoke World: 3D map of the Pacific Northwest with the August 2023 smoke forecast, wind and fires"
                className="absolute inset-0 h-full w-full object-cover" />
            </div>
            <CardContent className="flex flex-col justify-center gap-4 p-8">
              <Badge className="w-fit"><Map /> Smoke World</Badge>
              <h3 className="font-serif text-4xl">Fly over the West. Watch the next 72 hours.</h3>
              <p className="text-muted-foreground">
                Real terrain and aerial imagery, the smoke forecast hour by hour, wind and live fires. Click any place for
                its smoke curve and advice. Switch between NOAA and Serein.
              </p>
              <Button asChild className="w-fit"><Link to="/world">Open Smoke World <ArrowRight /></Link></Button>
            </CardContent>
          </div>
        </Card>
      </section>

      <section className="mx-auto mt-28 max-w-6xl px-5">
        <h2 className="text-5xl md:text-6xl">Who it's for</h2>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            { icon: HardHat, title: "Outdoor crews", text: "California's wildfire smoke rule (Title 8, §5141.1) already tells employers to check AQI forecasts at each shift. Serein gives them three days to plan." },
            { icon: Users, title: "Families", text: "People with asthma, children and older adults get the hours to stay inside and the hours that are safe, free." },
            { icon: ShieldCheck, title: "Places without a monitor", text: "Rural and lower-income areas are the most likely to have no air monitor nearby. Serein still beat NOAA there, even 30-60 km from one." },
          ].map(({ icon: Icon, title, text }) => (
            <Card key={title} className="bg-card/60">
              <CardHeader>
                <Icon className="size-6 text-primary" />
                <CardTitle className="mt-3 text-xl">{title}</CardTitle>
                <CardDescription className="text-base">{text}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto mt-28 max-w-6xl px-5" id="team">
        <h2 className="text-5xl md:text-6xl">The team</h2>
        <p className="mt-3 text-muted-foreground">Five students at Foothill High School.</p>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {team.map(m => (
            <Card key={m.name}>
              <CardHeader>
                <CardTitle className="text-lg">{m.name}</CardTitle>
                <CardDescription>{m.grade}{m.role ? `. ${m.role}` : ""}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>
    </>
  )
}
