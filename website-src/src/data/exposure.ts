// Mean short-term inhalation rates from the US EPA Exposure Factors Handbook (2011),
// Chapter 6, Table 6-2 (males and females combined), in m³/minute, converted to m³/hour.
// https://www.epa.gov/sites/default/files/2015-09/documents/efh-chapter06.pdf (pages 6-4, 6-5)
const perHour = (m3PerMinute: number) => m3PerMinute * 60

export const BREATHING: Record<string, { label: string; m3PerHour: number }> = {
  childPlay: { label: "Child 6-10, playing outside (moderate activity)", m3PerHour: perHour(2.2e-2) },
  childSit: { label: "Child 6-10, sitting (sedentary)", m3PerHour: perHour(4.8e-3) },
  teenSport: { label: "Teen 11-15, sports practice (high activity)", m3PerHour: perHour(4.9e-2) },
  worker: { label: "Adult 21-30, outdoor work (moderate activity)", m3PerHour: perHour(2.6e-2) },
  runner: { label: "Adult 21-30, running (high activity)", m3PerHour: perHour(5.0e-2) },
  olderWalk: { label: "Adult 61-70, walking (light activity)", m3PerHour: perHour(1.2e-2) },
}

// Berkeley Earth, "Air Pollution and Cigarette Equivalence" (R. A. Muller and E. A. Muller,
// 2015, updated 2023): "1 cigarette is equivalent to an air pollution of 22 μg/m3 for one day."
// A rough comparison of health effects, not of particles inhaled.
export const CIGARETTE_UG_M3_DAY = 22
