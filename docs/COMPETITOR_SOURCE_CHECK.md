# Competitor source checks for the Innovation Brief

**Historical preliminary check (November 6).** The
[November 7 verification](COMPETITOR_VERIFICATION_2026-11-07.md) supersedes this
record and updates both Q7 drafts. The open items and draft status below describe
the earlier check, not the current E-5 status.

Checked November 6, 2026 against product-owner pages. These notes support review
of section 7 of the [Innovation Brief draft](drafts/innovation_brief.md).
They cover the named product examples and both research references, but do not
complete E-5 or a novelty search. The brief and its verification placeholders
are unchanged. These are documentation checks, not installed-app tests or a
comparative accuracy evaluation.

## Availability corrections

| Draft example | What the official page supports | Suggested treatment in the brief |
|---|---|---|
| Propeller Health | Resmed says the subsidiary operating as Propeller Health has ceased operations. Resmed retains its brand, intellectual property and assets. [Resmed notice](https://www.resmed.com/en-us/health-professionals/solutions/propeller-health/) | Do not list the company as an active provider. Verify former inhaler features and any ongoing partner offerings separately. This notice does not establish a shutdown date or the status of other inhaler products. |
| EPA Smoke Sense | EPA says the app would be unavailable beginning December 8, 2024 and directs visitors to AirNow for wildfire smoke and air-quality information. The page still describes the citizen-science research project. [EPA project page](https://www.epa.gov/air-research/smoke-sense-study-citizen-science-project-using-mobile-app) | Cite the research project as related work and distinguish it from the app's availability. Do not present the app as currently available or infer that the entire research project ended. |

The Resmed page does not give the operational shutdown date. Its page metadata
shows an August 12, 2025 modification, which is not evidence that operations
ended on that date. EPA's page displays a September 29, 2026 update date; the
December 2024 date belongs to its app-availability notice. Neither app was
installed or tested during this check.

## IQAir already advertises forecasts and exposure advice

IQAir's [AirVisual app product page](https://www.iqair.com/air-quality-monitors/air-quality-app)
advertises seven-day air-pollution and weather forecasts, historical and current
air-quality information, and advice for reducing exposure. A forecast several
days ahead, or general air-quality advice, is therefore not sufficient by itself
to distinguish Serein from this product.

The [developer's U.S. App Store description](https://apps.apple.com/us/app/iqair-airvisual-air-quality/id1048912974)
also advertises seven-day air-pollution and weather forecasts and advice for
sensitive groups. Its separate three-day forecast item concerns pollen. Keep
pollutant forecasts, pollen forecasts and weather horizons distinct when
summarizing the listing. These statements come from the developer description,
not user reviews or an installed-app check.

For the IQAir part of the combined IQAir/Google/Apple row, a supported replacement
for the unresolved lead-time placeholder is: "IQAir advertises seven-day
air-pollution and weather forecasts, with general exposure advice."

This is a documented product claim, not an independent accuracy measurement.
The reviewed page does not establish the forecast's model-input details,
location-by-location availability, smoke-day accuracy relative to NOAA, or
clinician-reviewed personalization for an individual child. It also does not
establish that those capabilities are absent. Google and Apple have separate
checks below; IQAir's description cannot support claims about their services.

## Separate Google and Apple products

Google's [Air Quality API overview](https://developers.google.com/maps/documentation/air-quality/overview)
documents hourly forecasts up to 96 hours, location-specific pollutant data and
recommendations, and a 500 by 500 meter resolution. Recommendations include
children and people with asthma. The overview says coverage varies by country
and region. These are API capabilities; do not assume every Google consumer
interface exposes the same horizon or fields.

Google's [consumer air-quality help](https://support.google.com/maps/answer/11270845?hl=en)
distinguishes station-based and model-based displays. The model combines
regulatory monitors, commercial sensors, dispersion models, satellite data,
weather and other inputs on a 500 meter grid. The help describes reporting delays
and local events that models can miss. It supports describing modeled local
information, rather than treating all Google displays as city-wide station
readings. Neither page establishes independently measured smoke-day accuracy or
a child-specific sensitivity estimate learned from symptom history.

Apple's [Weather data-source page](https://support.apple.com/en-us/105038), dated
June 5, 2026, identifies BreezoMeter for U.S. air-quality information and QWeather
for mainland China. It also names those providers for air-quality maps. The
page's ten-day forecast section concerns weather; it does not establish a
ten-day PM2.5 forecast. Keep Apple's AQI horizon unresolved rather than copying
Google's API horizon or IQAir's advertised horizon into the Apple row. Device
version and regional availability still need checking in the actual interface.
The [iPhone Weather guide](https://support.apple.com/guide/iphone/check-the-weather-iph1ac0b35f/ios),
displayed for iOS 27 during this check, describes the AQI scale and air-quality
details but does not establish a specific AQI forecast horizon.

## AirNow varies by reporting area

The [AirNow API FAQ](https://docs.airnowapi.org/faq#reportingAreaForecasts)
says agencies issue forecasts through reporting areas, which can span part of a
city or an entire county. Forecast availability, pollutants, seasonality and
format vary. Documented horizons range from one to six days; not every area has
a daily forecast. The [Air Quality 101 page](https://docs.airnowapi.org/aq101#aqForecast)
describes predictions of daily AQI using air-quality and weather information.

Use "agency-issued daily AQI forecasts by reporting area, with local variation
in coverage and horizon" rather than a universal metro-only or next-day-only
description. The FAQ also distinguishes reporting-area observations from
individual monitor observations. A location lookup is not necessarily a unique
neighborhood forecast. These pages do not establish that agencies ignore current
observations, nor that a clinician-reviewed personal model is present or absent.

## NOAA already provides observation-based correction

The [NOAA operational AQM change log](https://www.emc.ncep.noaa.gov/mmb/aq/AQChangelog.html)
documents Kalman Filter Analog bias correction using AirNow observations. It
records a July 20, 2021 extension from 48 to 72 hours and a May 14, 2024 change
from approximately 12 km model domains to a unified 13 km domain. Therefore,
"not corrected with live monitors" is too broad for the combined NOAA row.
Observation-based statistical correction and direct assimilation of PM2.5 into
the model state are different claims; this documentation establishes the former.

The [NOAA-managed archive description](https://registry.opendata.aws/noaa-nws-naqfc-pds/)
distinguishes raw and bias-corrected AQM fields and the model version used at
each date. Its approximately 5 km CONUS output spacing is a product-grid
description, separate from v7's native 13 km model grid. Keep native resolution,
archived output spacing and the version in Serein's historical comparison separate.

The [RAP/HRRR-Smoke user guide](https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/HRRR-Smoke_VIIRS_Activefire_user_guide.pdf)
describes a 3 km HRRR-Smoke grid, 48-hour forecasts at 00, 06, 12 and 18 UTC,
and 18-hour forecasts at other CONUS cycles. It uses satellite fire radiative
power and assimilated meteorological observations. Those weather observations
do not by themselves establish surface-PM2.5 assimilation. The
[operational smoke page](https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/)
also identifies the four extended cycles. A uniform "three-day HRRR forecast"
would be unsupported. Serein's third local-day forecast is a separate output
whose source-hour availability must be audited.

## PurpleAir: document monitoring, leave forecast absence open

PurpleAir's [current homepage](https://www.purpleair.com/)
describes real-time sensor monitoring and links to its map. This supports the
draft's monitoring description. The first explanatory post in the
[AQI help topic](https://community.purpleair.com/t/air-quality-index-aqi/111/1),
retrieved through its [public JSON view](https://community.purpleair.com/t/air-quality-index-aqi/111.json),
describes selectable averaging periods for displaying current conditions. An
averaging window is not a forward forecast horizon. This checks the explanatory
post, not opinions in later replies. Neither source proves that no PurpleAir
product, partner or map feature offers a forecast. Keep that broader question
open rather than treating a monitoring description as a missing-feature claim.

## Both research references contain relevant prior methods

| Reference reviewed | What it establishes | Bounded comparison for the brief |
|---|---|---|
| Liao, Buch, Lamb and Gentine (2025), [NSF record](https://par.nsf.gov/biblio/10611007), [full paper](https://par.nsf.gov/servlets/purl/10611007), DOI 10.1017/eds.2025.4 | California hourly PM2.5 forecasts over a 48-hour window using a directed monitor graph, recurrent temporal modeling and wind-related edges. The paper also simulates prescribed-fire contributions. | Graphs with monitor nodes and wind-aware transport are relevant prior work. Serein combines NOAA forecast correction, daily quantile outputs and a separate synthetic personal-risk prototype; those design differences do not establish novelty or better accuracy. |
| Wang, Bhudia, Dos Remedios, Teng and Ng (2020), [arXiv record](https://arxiv.org/abs/2009.11362), [full text](https://arxiv.org/html/2009.11362) | A sparsity-invariant convolutional model predicts PM2.5 24 hours ahead on a 10 km British Columbia grid. Inputs include FireWork and BlueSky forecasts, meteorology and fire/smoke information. Section 2.2 describes randomly shuffled input-output pairs. | Learning improvements to existing smoke forecasts and producing dense maps from sparse labels are prior methods. Serein's graph architecture and evaluation schedule differ. The paper's reported errors are not directly comparable with Serein's daily western-U.S. results. |

These papers describe forecasting methods and experiments. Their text does not
establish the current availability or absence of a family-facing service.
Do not keep the blanket "research code, not a family-facing service" statement
without checking deployment and later work. Neither comparison establishes that
Serein is the first system to combine the listed capabilities.

## What remains open

- Check the actual Google and Apple consumer interfaces for the target geography
  and device version. API documentation is not evidence of every app's features.
- Resolve PurpleAir's forecast question with a direct product source.
- Match NOAA model versions and fields to each archived evaluation season. The
  change log and dataset description do not verify Serein's decoded inputs.
- Review later work and deployments of the two research methods before making
  service-availability claims. These two papers do not constitute a novelty search.
- Replace claims about missing features or missing published evaluations with
  bounded statements about the sources actually reviewed, unless a broader
  search supports the stronger claim.

These checks do not establish a clinical benefit, an accuracy advantage, market
size, or uniqueness. Recheck product availability before submitting the brief.
