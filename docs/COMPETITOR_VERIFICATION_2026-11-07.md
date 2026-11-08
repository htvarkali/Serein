# Competitor verification for Brief Q7 (task E-5)

Accessed November 7, 2026. This review completes the source check of the named
Q7 alternatives, including both original research references, and adds AirRater
and ExactAQ because they materially change the comparison. It supersedes the
[November 6 preliminary notes](COMPETITOR_SOURCE_CHECK.md). Both
[Brief Q7](drafts/innovation_brief.md#7-competition-300-words) and the
[Q6–Q10 working draft](drafts/innovation_brief_q6-q10_DRAFT.md) use the corrected
comparison. These are working materials for team review, not a submitted brief.

Evidence is limited to product-owner or agency documentation, developer listings,
and primary research. Advertised features are not independently tested performance.
We did not install the apps, measure comparative forecast skill, or conduct an
exhaustive patent or market search. A feature not mentioned by a source is **not**
evidence that the competitor lacks it. The review supports no “first,” “only,”
or “no other product combines these features” claim.

## Current services and historical alternatives

| Alternative | What the primary source supports | Implication for Serein's comparison |
|---|---|---|
| **EPA AirNow and Fire and Smoke Map** | Agency AQI forecasts are issued for reporting areas, from part of a city to a county; available horizons vary from one to six days. The Fire and Smoke Map combines monitors, corrected low-cost sensors, fire/smoke information, health guidance and smoke outlooks where available. [API FAQ](https://docs.airnowapi.org/faq); [map overview](https://www.airnow.gov/fasm-v4/about/). | AirNow already provides forecasts, sensor information and advice. Compare a specified reporting area, issue time, lead and pollutant; do not describe all AirNow products as a one-day forecast or a nowcast-only map. |
| **NOAA HRRR-Smoke and AQM/NAQFC** | NOAA documents 48-hour HRRR-Smoke forecasts for the 00, 06, 12 and 18 UTC cycles. NAQFC includes 72-hour guidance and bias-corrected products; NOAA's change log explicitly identifies AirNow observations in bias correction. [HRRR-Smoke](https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/); [NAQFC archive description](https://registry.opendata.aws/noaa-nws-naqfc-pds/); [NOAA change log](https://www.emc.ncep.noaa.gov/mmb/aq/AQChangelog.html). | “NOAA forecasts do not use monitors” is false as a blanket claim. Name the model, version, cycle and raw/bias-corrected product in a comparison. Do not conflate a model's native grid with a distributed output grid or claim an RRFS rollout from a scheduled date alone. |
| **PurpleAir and ExactAQ** | Sonoma Technology, the ExactAQ provider, documents its use of PurpleAir observations with AirNow, weather, land use and fire data to estimate air quality at and between sensors. ExactAQ currently advertises hourly updates and forecasts for the next 48 hours. [Provider's PurpleAir integration article](https://www.sonomatech.com/node/4916); [ExactAQ forecast feature](https://exactaq.com/features/air-quality-forecast/). | Distinguish the PurpleAir sensor map from a forecast service using its data. “PurpleAir offers readings, therefore there is no forecast alternative” misses an existing partnership and forecast covering locations between monitors. |
| **IQAir AirVisual** | IQAir advertises seven-day air-quality and weather forecasts developed with machine learning, alerts, historical/current data and exposure recommendations. [IQAir app page](https://www.iqair.com/air-quality-monitors/air-quality-app). | Forecasts and exposure advice are established features. The page alone does not justify claims that IQAir lacks smoke-model inputs, symptom personalization or useful forecasts. Its advertised horizon is not a measured accuracy guarantee. |
| **Google Air Quality API** | Google documents hourly forecasts up to 96 hours, 500 × 500 m resolution and recommendations for sensitive groups including children and people with asthma. Coverage varies by region. [API overview](https://developers.google.com/maps/documentation/air-quality/overview). | This is a developer API, not proof of what every consumer app displays. Fine spatial detail and sensitive-group advice cannot be claimed as unique to Serein; neither resolution nor horizon proves forecast skill. |
| **Apple Weather** | Apple's source page identifies BreezoMeter as the air-quality provider in the US and several other countries, with other providers in some regions. [Apple Weather data sources](https://support.apple.com/en-us/105038). | The page does not establish an air-quality forecast horizon. Do not transfer Google's API's 96-hour specification, or Apple's ten-day **weather** horizon, to Apple AQI. We make no horizon or missing-feature claim for Apple. |
| **Propeller Health — historical** | Resmed's 2018 announcement describes inhaler sensors paired with an app to record medication use and provide personal feedback. Resmed's current notice says the operating company has ceased operations and Resmed retains the brand, IP and assets. [Historical product description](https://newsroom.resmed.com/news-releases/news-details/2018/ResMed-to-Acquire-Propeller-Health-a-Leader-in-COPD-and-Asthma-Connected-Health-Solutions-for-225-Million/default.aspx); [current notice](https://www.resmed.com/en-us/health-professionals/solutions/propeller-health/). | Relevant precedent for respiratory self-management, not a currently operating competitor. The notice supplies no shutdown date and does not establish the status of other inhaler products or a “successor” app. |
| **EPA Smoke Sense — research; app unavailable per EPA notice** | EPA describes a citizen-science project studying smoke exposure, symptoms and risk communication. Its current page retains a notice that the app became unavailable December 8, 2024, would be down through summer 2025, and has no known next-version date. [EPA project page](https://www.epa.gov/air-research/smoke-sense-study-citizen-science-project-using-mobile-app). | Separate the continuing research record from app availability. Do not claim that the research project was permanently discontinued or that the app has relaunched because summer 2025 has passed. |
| **AirRater — Australia** | AirRater documents symptom logging, personal environmental-trigger identification and alerts. Its current developer listing advertises real-time and forecast air quality/pollen across Australia and explicitly addresses people responsible for children's health. [AirRater](https://airrater.org/); [AirHealth developer listing](https://play.google.com/store/apps/details?id=com.senset.airrater&hl=en-AU). | This is a close precedent for combining environmental information and personal symptom support, including caregiver use. Remove “adults only,” “no caregiver mode” and “no app learns from symptoms.” We do not infer a numerical forecast horizon or clinical effectiveness from the listing. |

## Research precedents, distinct from product availability

| Primary work | Supported scope and relevance |
|---|---|
| **Liao, Buch, Lamb and Gentine (2025), original NSF PAR 10611007 example** | *Simulating the air quality impact of prescribed fires using graph neural network-based PM2.5 forecasts*, Environmental Data Science. Uses a monitor graph, meteorology and fire information to forecast hourly PM2.5 in California out to 48 hours, with prescribed-fire applications. This establishes graph-based PM2.5 forecasting as prior work. Serein's proposed NOAA residual correction, daily targets and family interface are different design choices, not evidence of superiority. [Published paper](https://doi.org/10.1017/eds.2025.4). |
| **Wang, Bhudia, Dos Remedios, Teng and Ng (2020), original UBC example** | *Dense Forecasting of Wildfire Smoke Particulate Matter Using Sparsity Invariant Convolutional Neural Networks*, arXiv workshop preprint. Predicts 24-hour-ahead smoke PM2.5 on a 10 km British Columbia grid using sparse observations and FireWork/BlueSky forecasts, among other inputs. Forecast correction and prediction away from monitors already have research precedent; Serein proposes a graph-based correction to different inputs. [Paper](https://arxiv.org/abs/2009.11362); [full text](https://arxiv.org/html/2009.11362v1). |
| **Dimri et al. (2024), AGATNet** | Adaptive graph attention corrects CMAQ PM2.5 forecasts for South Korean monitoring stations through 72 hours. A graph network correcting a chemical-transport forecast is not a new methodological claim for Serein. [Journal paper](https://doi.org/10.1029/2024JH000244). |
| **Dong et al. (2026)** | *Machine Learning Bias Correction of HRRR-Smoke Surface PM2.5 Forecasts during the Alaska Wildfire Season*, ACS ES&T Air 3(5), 1263–1275. Studies random-forest and convolutional models for HRRR-Smoke correction using calibrated PurpleAir data. This is directly relevant prior work for Serein's proposed inputs and correction approach. [NOAA-hosted publication record and abstract](https://repository.library.noaa.gov/view/noaa/74016); [DOI](https://doi.org/10.1021/acsestair.5c00409). |
| **Liu, Ma, Dhillon and Mei (2024)** | *PM2.5 forecasting under distribution shift: A graph learning approach*, AI Open 5, 23–29. Compares graph and non-graph methods under different temporal splits and finds particular vulnerability to distribution shift for the tested GNNs. This motivates temporal evaluation; it does not establish Serein's generalization. [Journal paper](https://doi.org/10.1016/j.aiopen.2023.11.001). |
| **Berlinghieri et al., author manuscript v2 (2025)** | *Are Hourly PM2.5 Forecasts Sufficiently Accurate to Plan Your Day? Individual Decision Making in the Face of Increasing Wildfire Smoke*. Evaluates six forecasts and persistence for the 2023 CONUS fire season. Results depend on the decision and metric; persistence does **not** beat every model on every metric. Use it to motivate separate miss, false-alarm and exposure metrics, not a universal performance ranking. [Version actually reviewed](https://arxiv.org/html/2409.05866v2). |
| **Kim et al. (2025), JMIR preprint 84513** | *mHealth Intervention Integrating Personal PM2.5 Monitoring and Deep Learning to Reduce Pediatric Asthma Exacerbations: Pilot Study*. Describes 272 enrolled pediatric patients in Korea, with 109 entering an intervention phase using personalized alerts, forecast-based alerts or no intervention. It is a research precedent for personal PM sensitivity and pediatric alerts, not evidence for Serein's clinical benefit or a currently available consumer product. [Preprint and status page](https://preprints.jmir.org/preprint/84513). |

These publications describe different regions, targets, instruments and study
protocols. Their scores are not a matched comparison with Serein. The existence
of a paper also does not prove that its authors have no deployed service.

## Bounded positioning and remaining team decisions

Serein can describe its **proposed emphasis**: reproducible evaluation of daily
smoke forecasts, uncertainty ranges, and a caregiver check-in connected to a
family plan. The present family demonstration uses simulated children; clinical
and translation review remain open. Do not describe prospective interval
calibration, held-out results, symptom learning or family benefits as validated
because the code or evaluation protocol exists.

The team still needs to choose its pilot users, workflow and distribution, and
test usefulness with them. Those are strategy and validation tasks, not missing
facts about competitors. This review does not certify novelty or IP protection.
Public outreach programs are evidence that outreach exists, not evidence of
willingness to buy Serein, an agreement or a price.

Corrections to carry into any later brief/video revision:

- Remove “first/only,” including narrower replacement claims about the first US,
  free, caregiver or uncertainty-enabled combination. This search cannot prove
  them. Both Q7 drafts now use bounded positioning.
- Remove blanket statements that forecasts ignore monitors or that apps cannot
  personalize from symptoms. AQM, ExactAQ and AirRater provide counterexamples.
- Distinguish a documented product feature, advertised accuracy, a research
  finding and Serein's own measured result. One cannot substitute for another.
- Preserve dated availability notices for Propeller and Smoke Sense. Do not
  invent a shutdown date, relaunch or product succession.
- Other sections of the working briefs are outside this Q7 review and still
  require their own evidence and team approval.
