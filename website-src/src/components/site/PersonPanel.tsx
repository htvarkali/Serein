import { useMemo, useState } from "react"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { localTime, valueAt, type Which, type WorldData } from "@/lib/world"
import { BREATHING, CIGARETTE_UG_M3_DAY } from "@/data/exposure"

// How much smoke one kind of person breathes in at this place, for a chosen window.
// Dose (micrograms) = sum over hours of PM2.5 (µg/m³) × breathing rate (m³/hour).
// Breathing rates: US EPA Exposure Factors Handbook (2011), Table 6-2.
export function PersonPanel({ data, point, which }: { data: WorldData; point: number; which: Which }) {
  const [who, setWho] = useState(Object.keys(BREATHING)[0])
  const [start, setStart] = useState(0)
  const [length, setLength] = useState(2)
  const person = BREATHING[who]

  const result = useMemo(() => {
    const dose = (from: number) => {
      let ug = 0, concHours = 0, n = 0
      for (let h = from; h < Math.min(from + length, data.hours); h++) {
        const c = valueAt(data, which, point, h)
        if (c === null) continue
        ug += c * person.m3PerHour; concHours += c; n++
      }
      return { ug, concHours, n }
    }
    return { chosen: dose(start) }
  }, [data, which, point, person, start, length])

  const cigarettes = (concHours: number) => concHours / (CIGARETTE_UG_M3_DAY * 24)
  const fmt = (x: number) => (x < 0.1 ? x.toFixed(2) : x.toFixed(1))

  return (
    <div className="space-y-3 rounded-xl border bg-card/60 p-4">
      <div className="font-medium">What a person breathes in here</div>
      <div className="grid gap-2">
        <Label htmlFor="who" className="text-xs text-muted-foreground">Person and activity</Label>
        <Select value={who} onValueChange={setWho}>
          <SelectTrigger id="who"><SelectValue /></SelectTrigger>
          <SelectContent>{Object.entries(BREATHING).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent>
        </Select>
      </div>
      <div className="grid gap-2">
        <Label className="text-xs text-muted-foreground">Starting {localTime(data, start)}, for {length} hours</Label>
        <Slider min={0} max={data.hours - length} step={1} value={[start]} onValueChange={([v]) => setStart(v)} aria-label="Start hour" />
        <Slider min={1} max={8} step={1} value={[length]} onValueChange={([v]) => { setLength(v); setStart(s => Math.min(s, data.hours - v)) }} aria-label="Hours" />
      </div>
      {result.chosen.n === 0 ? <p className="text-sm text-muted-foreground">No forecast for these hours.</p> : (
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-serif text-3xl">{Math.round(result.chosen.ug)} µg</span> of fine particles, breathing about
            {" "}{person.m3PerHour.toFixed(1)} m³ of air an hour.
          </p>
          <p className="text-muted-foreground">
            By Berkeley Earth's rough rule of thumb (breathing {CIGARETTE_UG_M3_DAY} µg/m³ for a day is about as harmful as
            1 cigarette), being outside here for these hours is like about <strong className="text-foreground">{fmt(cigarettes(result.chosen.concHours))} cigarettes</strong>.
            It compares health effects, not particles inhaled.
          </p>
          <p className="text-xs text-muted-foreground">
            Uses the hour-by-hour values at this place. Their daily level is tested; which hours are worst is not reliable,
            so treat the time of day as rough. Outdoor air; indoors with windows closed is usually lower. Typical values for
            the group, not a medical estimate for any one person.
          </p>
        </div>
      )}
    </div>
  )
}
