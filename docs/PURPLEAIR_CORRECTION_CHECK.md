# PurpleAir correction check (A-12 follow-up), 2026-11-27

`src/serein/data/purpleair.py` asks for its EPA correction coefficients to be checked
against the papers before the final test (`TODO(A-12)` in `epa_correction`). This note
records that check. **Nothing here changes current results:** PurpleAir data has not been
downloaded (A-14 waits on the cost estimate), so no model or score uses this code yet.
The code was not changed; the decision below is for the owners of A-12 and A-14.

## What was checked

| Item | Code | Sources | Result |
|---|---|---|---|
| Low range, 0 to 30 µg/m³ | `0.524 x - 0.0862 RH + 5.75` | Barkjohn et al. 2021, Eq. 10 (summary of the page, not verbatim); EPA slides, May 2021 (0.52, 0.086, 5.75, rounded) | Matches |
| Middle range, 50 to 210 | `0.786 x - 0.0862 RH + 5.75` | EPA slides, May 2021, "Final Correction (cf_atm)" | Matches, **for cf_atm input** |
| High range, 260 and up | `2.966 + 0.69 x + 8.84e-4 x^2` | EPA slides, May 2021 (0.69, 8.84 x 10^-4, 2.97 rounded) | Matches, **for cf_atm input** |
| Blends at 30 to 50 and 210 to 260 | weighted, five pieces | Jaffe et al. 2023 describe EPA's newer algorithm as a five-part piecewise regression with weighting to smooth the transitions | Same shape. Coefficients of the blends not seen in text (see "Not verified") |
| Joins between pieces | | | Checked here: no jump at 30, 50, 210 or 260 µg/m³ (differences under 1e-8 at RH 20 and 60) |
| A/B agreement | keep if within 5 µg/m³ **or** 70% | Barkjohn et al. 2021: 5 µg/m³ **and** 61% on 24-hour averages decides removal | Same either/or logic; the percent threshold differs, see below |

## The finding: input channel

The code passes the mean of the **cf_1** channels (`pm2.5_cf_1_a`, `pm2.5_cf_1_b`) into
the extended correction. The sources point to **cf_atm** for that correction:

- Jaffe et al. (2023, AMT 16:1311, read on NOAA's repository) say EPA's newer
  algorithm, the one used for the AirNow Fire and Smoke Map, starts from the
  "CF = Atm" data.
- EPA's May 2021 slides give the piecewise version with the 0.786 middle slope and the
  0.69 and 8.84 x 10^-4 high-range terms under the heading "Final Correction
  (cf_atm)". The cf_1 version on the same slides is different: linear up to
  343 µg/m³, then 0.46 x + 3.93 x 10^-4 x^2 + 2.97.

The two channels agree in clean air and drift apart as concentrations rise, so the
mismatch matters most on smoke days, which is where PurpleAir would be used.

## Options for A-14

Point costs from `estimate_history_points(300 sensors, 365 days)`:

| Option | Fields to buy | Points | Note |
|---|---|---|---|
| A. Buy cf_atm instead of cf_1 and feed it to the current correction | `pm2.5_atm_a`, `pm2.5_atm_b`, `humidity` | 7,900,200 (same as now) | Matches EPA's current map method. Decide whether A/B QC also runs on cf_atm |
| B. Buy both channels | cf_1 and cf_atm, plus humidity | 13,156,200 (1.67 times) | QC on cf_1 as in the 2021 paper, correction on cf_atm |
| C. Keep cf_1 and use the 2021 cf_1 correction instead | as now | 7,900,200 | Older method; EPA's map moved to the cf_atm version |

Whichever is chosen, it should be written into the protocol change log before data is
bought, since PurpleAir would be a new input.

## Not verified, and how to finish

- **Barkjohn et al. 2022 (Sensors 22:9669)**, the paper that defines the extended
  correction, could not be read: the publisher showed an automated bot check, and it
  was not worked around. Someone should open it in a browser and confirm (1) the input
  channel, (2) the coefficients of the two blended ranges, and (3) the A/B rule for
  hourly data.
- **70% vs. 61%.** The 2021 paper used 61% (two standard deviations) on 24-hour
  averages. The code's docstring says 70% mirrors the AirNow Fire and Smoke Map, which
  works on hourly data; that may be right, but no source read here states it.
- EPA's code repository linked from its technical page (`USEPA/FASM-sensor-AQI-analysis`)
  could not be read beyond the README.

## Sources (read 2026-11-27)

- Barkjohn, K. K., Gantt, B., and Clements, A. L. 2021. Development and application of
  a United States-wide correction for PM2.5 data collected with the PurpleAir sensor.
  Atmos. Meas. Tech. 14, 4617-4637. https://amt.copernicus.org/articles/14/4617/2021/
- U.S. EPA. 2021 (May 19). Tools and Resources webinar slides on PurpleAir data in
  smoke (slides 37 and 56). https://www.epa.gov/sites/default/files/2021-05/documents/toolsresourceswebinar_purpleairsmoke_210519b.pdf
- Jaffe, D. A., et al. 2023. Atmos. Meas. Tech. 16, 1311-1322, doi 10.5194/amt-16-1311-2023
  (an evaluation of EPA's PurpleAir correction in smoke, dust and urban events). https://repository.library.noaa.gov/view/noaa/58181
- U.S. EPA. Technical approaches for the sensor data on the AirNow Fire and Smoke Map.
  https://www.epa.gov/air-sensor-toolbox/technical-approaches-sensor-data-airnow-fire-and-smoke-map
- Not read (bot check): Barkjohn, K. K., et al. 2022. Sensors 22, 9669 (the extended
  correction for heavy smoke).
