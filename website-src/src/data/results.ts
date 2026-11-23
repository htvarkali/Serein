// Read straight from the committed results snapshot, so the charts always
// match docs/results. Rebuild the islands after those files change.
import metricsCsv from "../../../docs/results/metrics.csv?raw"
import airplanCsv from "../../../docs/results/airplan_simulation_summary.csv?raw"

type Row = Record<string, string>

function parse(csv: string): Row[] {
  const [header, ...lines] = csv.trim().split(/\r?\n/)
  const keys = header.split(",")
  return lines.map(line => Object.fromEntries(line.split(",").map((v, i) => [keys[i], v])))
}

const num = (v: string | undefined) => (v === undefined || v === "" ? null : Number(v))

export type MetricRow = {
  lead: number
  subset: string
  model: string
  n: number
  rmse: number | null
  mae: number | null
  usg_pod: number | null
  usg_far: number | null
}

export const metrics: MetricRow[] = parse(metricsCsv).map(r => ({
  lead: Number(r.lead),
  subset: r.subset,
  model: r.model,
  n: Number(r.n),
  rmse: num(r.rmse),
  mae: num(r.mae),
  usg_pod: num(r.usg_pod),
  usg_far: num(r.usg_far),
}))

export type CheckinRow = { k: number; kind: string; gain: number }

export const checkins: CheckinRow[] = parse(airplanCsv).map(r => ({
  k: Number(r.k),
  kind: r.kind,
  gain: Number(r.gain),
}))
