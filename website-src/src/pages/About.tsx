import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { sources, team } from "@/data/site"

export default function About() {
  return (
    <div className="mx-auto max-w-6xl px-5 pt-16">
      <Badge variant="secondary">Data & methods</Badge>
      <h1 className="mt-4 text-6xl md:text-7xl">How Serein works</h1>
      <div className="mt-10 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-xl">The forecast</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-muted-foreground">
            <p>Every day at 11:30 AM Pacific, Serein reads NOAA's smoke (HRRR-Smoke) and air-quality (AQM) forecasts, the
              weather, satellite smoke plumes and fire detections, and the latest readings from 425 EPA monitors in the western US.</p>
            <p>A graph neural network treats nearby monitors as neighbors and learns how NOAA's forecast tends to be wrong.
              Five copies are averaged, and each forecast comes with a 90% range that is calibrated to hold about 90% of the time.</p>
            <p>Smoke World and Plan your day show NOAA's hour-by-hour shape, scaled each day to Serein's daily forecast.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-xl">How we keep it honest</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-muted-foreground">
            <p>The model never trains on the days it is scored on. Training uses 2021-22, development uses 2023, and the
              2024-25 seasons are locked for one final test, run once, under rules published before the run.</p>
            <p>Each new idea must beat the current model on a fixed statistical test before it is used. Failed ideas are kept
              in the public experiment log.</p>
            <p>Health advice follows EPA, CDC and California guidance. It is general guidance for groups, not medical advice.</p>
          </CardContent>
        </Card>
      </div>
      <h2 className="mt-20 text-5xl">Data sources</h2>
      <p className="mt-3 text-muted-foreground">Every source is free and public. Thank you to the agencies and communities who share them.</p>
      <Card className="mt-6">
        <CardContent className="divide-y p-0">
          {sources.map(s => (
            <div key={s.name} className="grid gap-1 px-6 py-4 md:grid-cols-[1fr_2fr_1fr]">
              <div className="font-medium">{s.name}</div>
              <div className="text-muted-foreground">{s.what}</div>
              <div className="text-sm text-muted-foreground md:text-right">{s.license}</div>
            </div>
          ))}
        </CardContent>
      </Card>
      <h2 className="mt-20 text-5xl">Team</h2>
      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {team.map(m => (
          <Card key={m.name}><CardHeader><CardTitle className="text-lg">{m.name}</CardTitle>
            <CardDescription>{m.grade}{m.role ? `. ${m.role}` : ""}</CardDescription></CardHeader></Card>
        ))}
      </div>
      <Separator className="my-12" />
      <p className="text-sm text-muted-foreground">
        Code: <a className="underline" href="https://github.com/htvarkali/Serein">github.com/htvarkali/Serein</a>.
        Results on this site are development numbers until the final 2024-25 test is run.
      </p>
    </div>
  )
}
