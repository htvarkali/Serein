import { rmseByLead } from "@/data/site"

// A radial bar chart in the style of an astrolabe. Each ring is one forecast day; arc
// length is proportional to RMSE (full sweep = MAX µg/m³), SmokeCast in gold and the
// reference forecast in blue-grey. Only the outer rings and orbiting dots are decoration.
const MAX = 16
const SWEEP = 270
const START = -135

function arc(r: number, value: number) {
  const a0 = (START * Math.PI) / 180
  const a1 = ((START + (SWEEP * Math.min(value, MAX)) / MAX) * Math.PI) / 180
  const p = (a: number) => `${200 + r * Math.sin(a)} ${200 - r * Math.cos(a)}`
  const large = (SWEEP * value) / MAX > 180 ? 1 : 0
  return `M ${p(a0)} A ${r} ${r} 0 ${large} 1 ${p(a1)}`
}

export function ForecastDial() {
  const rings = rmseByLead.map((row, i) => ({ ...row, r: 156 - i * 24 }))
  const ticks = Array.from({ length: 72 }, (_, i) => i)
  return (
    <figure className="relative mx-auto w-full max-w-[38rem]">
      <svg viewBox="0 0 400 400" className="w-full overflow-visible" role="img"
        aria-label={`Forecast error by day, root mean square error in micrograms per cubic meter. ${rmseByLead.map(r => `${r.lead}: SmokeCast ${r.serein}, reference ${r.noaa}`).join("; ")}.`}>
        <defs>
          <linearGradient id="dial-gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#f1dcb2" /><stop offset=".55" stopColor="#c9a466" /><stop offset="1" stopColor="#9c7638" />
          </linearGradient>
          <radialGradient id="dial-glow"><stop offset="0" stopColor="#c9a46633" /><stop offset="1" stopColor="#c9a46600" /></radialGradient>
        </defs>
        <circle cx="200" cy="200" r="198" fill="url(#dial-glow)" />
        <g className="spin-slow">
          <circle cx="200" cy="200" r="192" fill="none" stroke="#c9a46655" strokeWidth=".6" />
          {ticks.map(i => {
            const a = (i * 5 * Math.PI) / 180, long = i % 6 === 0
            return <line key={i} x1={200 + 186 * Math.sin(a)} y1={200 - 186 * Math.cos(a)} x2={200 + (long ? 176 : 181) * Math.sin(a)} y2={200 - (long ? 176 : 181) * Math.cos(a)}
              stroke="#c9a466" strokeOpacity={long ? 0.7 : 0.35} strokeWidth={long ? 0.9 : 0.5} />
          })}
          <circle cx="200" cy="8" r="3.2" fill="#ecd3a0"><animate attributeName="opacity" values="1;.4;1" dur="3s" repeatCount="indefinite" /></circle>
        </g>
        <g className="spin-rev">
          <circle cx="200" cy="200" r="181" fill="none" stroke="#c9a46640" strokeWidth=".5" strokeDasharray="2 6" />
          <circle cx="381" cy="200" r="2.4" fill="#e08a4f" />
        </g>
        {rings.map(({ lead, serein, noaa, r }) => (
          <g key={lead}>
            <path d={arc(r, MAX)} fill="none" stroke="#ffffff" strokeOpacity=".07" strokeWidth="12" strokeLinecap="round" />
            <path d={arc(r + 4, noaa)} fill="none" stroke="#8fa3c7" strokeOpacity=".85" strokeWidth="3" strokeLinecap="round" />
            <path d={arc(r - 3, serein)} fill="none" stroke="url(#dial-gold)" strokeWidth="6" strokeLinecap="round" className="dial-arc" pathLength={1} />
            <text x={200 + (r + 1) * Math.sin((-139 * Math.PI) / 180)} y={200 - (r + 1) * Math.cos((-139 * Math.PI) / 180) + 3} textAnchor="end" fontSize="7.5" letterSpacing="1.6" fill="#f3ead8" fillOpacity=".8"
              fontFamily="Montserrat Variable, sans-serif" fontWeight="600">{lead.toUpperCase()}</text>
          </g>
        ))}
        <text x="200" y="200" textAnchor="middle" fontFamily="Cormorant, serif" fontWeight="300" fontSize="30" fill="#f3ead8">RMSE</text>
        <text x="200" y="214" textAnchor="middle" fontFamily="Montserrat Variable, sans-serif" fontSize="6.5" letterSpacing="1.8" fill="#c9a466">µg/m³ · LOWER IS BETTER</text>
        {[4, 8, 12, 16].map(v => {
          const a = ((START + (SWEEP * v) / MAX) * Math.PI) / 180
          return <text key={v} x={200 + 172 * Math.sin(a)} y={200 - 172 * Math.cos(a) + 3} textAnchor="middle" fontSize="8" fill="#b8b1a3"
            fontFamily="Montserrat Variable, sans-serif">{v}</text>
        })}
      </svg>
      <figcaption className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2"><span className="h-1.5 w-6 rounded-full bg-gradient-to-r from-[#f1dcb2] to-[#9c7638]" />SmokeCast</span>
        <span className="inline-flex items-center gap-2"><span className="h-0.5 w-6 rounded-full bg-[#8fa3c7]" />Reference forecast (AQM → HRRR → persistence)</span>
      </figcaption>
    </figure>
  )
}
