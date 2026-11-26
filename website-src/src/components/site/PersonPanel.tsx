import { useState } from "react"
import { localTime, valueAt, type Which, type WorldData } from "@/lib/world"
import { BREATHING } from "@/data/exposure"

export function PersonPanel({ data, point, which }: { data: WorldData; point: number; which: Which }) {
  const [who, setWho] = useState(Object.keys(BREATHING)[0])
  const [start, setStart] = useState(0)
  const [length, setLength] = useState(2)
  const person = BREATHING[who]
  const duration = Math.min(length, data.hours)
  const firstHour = Math.min(start, data.hours - duration)

  let mass = 0
  let available = 0
  for (let hour = firstHour; hour < firstHour + duration; hour++) {
    const concentration = valueAt(data, which, point, hour)
    if (concentration === null) continue
    mass += concentration * person.m3PerHour
    available += 1
  }

  return (
    <details className="mt-3 rounded-xl border bg-background/40">
      <summary className="cursor-pointer rounded-xl px-4 py-3 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-primary">Illustrative particle intake</summary>
      <div className="space-y-3 px-4 pb-4 text-sm">
        <p className="text-xs leading-relaxed text-muted-foreground">A calculation using a typical breathing rate and the selected model’s hourly outdoor concentrations. Hourly timing is uncertain.</p>
        <label className="grid gap-1.5">
          Example person and activity
          <select className="min-h-11 w-full rounded-md border bg-card px-2 text-sm [color-scheme:dark]" value={who} onChange={event => setWho(event.target.value)}>
            {Object.entries(BREATHING).map(([key, option]) => <option key={key} value={key}>{option.label}</option>)}
          </select>
        </label>
        <label className="grid gap-1">
          Start · {localTime(data, firstHour)}
          <input type="range" className="h-7 w-full accent-primary" min={0} max={data.hours - duration} value={firstHour}
            aria-label="Exposure start hour" aria-valuetext={localTime(data, firstHour)} onChange={event => setStart(Number(event.target.value))} />
        </label>
        <label className="grid gap-1">
          Time outdoors · {duration} {duration === 1 ? "hour" : "hours"}
          <input type="range" className="h-7 w-full accent-primary" min={1} max={Math.min(8, data.hours)} value={duration}
            aria-label="Exposure duration in hours" onChange={event => setLength(Number(event.target.value))} />
        </label>
        {available < duration ? <p className="text-xs text-muted-foreground">Data is available for {available} of {duration} hours. Choose a window with complete data for an estimate.</p> : (
          <p className="leading-relaxed"><span className="font-serif text-3xl">{Math.round(mass)} µg</span> estimated inhaled particle mass for this example.</p>
        )}
      </div>
    </details>
  )
}
