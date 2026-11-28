# Reference list for the Innovation Brief attachment (task S-10), draft 3

Draft 3 (2026-11-23): every entry checked against Crossref, PubMed or the source page; titles, DOIs, pages and dead links corrected, duplicates marked. Items still marked [TEAM] need a person.

Update of 2026-11-25: entries 7, 44, 46 and 57 settled; entries 58 to 66 added for the business plan and the revised Brief sections 8 and 10. Two [TEAM] items are left: A6 (partly settled 2026-11-26), and the list of AI tools at the end, which the Rules require.

Format: author/organization, year, title, venue, URL. Sections A and B are the
model's own citations (from `docs/METHODS.md` and `docs/DATA.md`); sections C to F
support brief sections 3, 6, 7, 9 and 10. Remove any reference whose number is cut
from the final text. Verify every link the day before submission. Where a DOI is
known it is given; where only a journal citation exists, add the DOI before submitting.

## A. Model priors and clinical evidence (Q4, Q5; from METHODS.md)

A1. Sugrue, R., et al. 2026. Wildfire-Specific PM2.5 Asthma Risk Across a Disproportionately Burdened Pediatric Population in Northern California. GeoHealth 10(2): e2025GH001530. https://doi.org/10.1029/2025GH001530
A2. Khetsuriani, N., et al. 2007. Prevalence of viral respiratory tract infections in children with asthma. Journal of Allergy and Clinical Immunology 119(2): 314-321. https://doi.org/10.1016/j.jaci.2006.08.041
A3. Williams, L. K., et al. 2011. Quantifying the proportion of severe asthma exacerbations attributable to inhaled corticosteroid nonadherence. Journal of Allergy and Clinical Immunology 128(6): 1185-1191.e2. https://doi.org/10.1016/j.jaci.2011.09.011
A4. Strickland, M. J., et al. 2010. Short-term associations between ambient air pollutants and pediatric asthma emergency department visits. American Journal of Respiratory and Critical Care Medicine 182(3): 307-316. https://doi.org/10.1164/rccm.200908-1201OC
A5. Gent, J. F., et al. 2009. Symptoms and medication use in children with asthma and traffic-related sources of fine particle pollution. Environmental Health Perspectives 117(7): 1168-1174. https://doi.org/10.1289/ehp.0800335 (Evidence considered and not used; cite only if Q4 mentions it.)
A6. CDC. Asthma Call-back Survey (ACBS). https://www.cdc.gov/asthma/acbs/ ; and CDC, National Asthma Control Program. AsthmaStats: Uncontrolled Asthma Among Children With Current Asthma, 2018-2020 (last reviewed July 1, 2022; archived page). https://archive.cdc.gov/www_cdc_gov/asthma/asthma_stats/uncontrolled-asthma-children-2018-2020.htm (Read 2026-11-26: from the BRFSS Child Asthma Call-back Survey in 21 states; asthma control "was classified as well controlled or uncontrolled based on the national asthma guidelines" (NAEPP Expert Panel Report 3, 2007); 44.0% of children with current asthma had uncontrolled asthma.) [TEAM: neither CDC page states the rule "symptoms on 9 or more of 30 days" that `docs/METHODS.md` and `src/serein/personal/model.py` quote for "not well controlled". Find it in Expert Panel Report 3 or the ACBS analysis guidance, or reword those two places to cite the guideline through this page. Also: CDC's 21-state figure means 56% of children were well controlled, lower than the 78% from Illinois 2017 in METHODS.md; say which one the prior leans on. A paper that may state the rule could not be opened on 2026-11-25 or 2026-11-26 because PubMed Central blocked the request: "Assessing asthma control and associated risk factors among persons with current asthma", https://pmc.ncbi.nlm.nih.gov/articles/PMC4552346/ . Open it in a browser.]
A7. US EPA. 2024. Final Reconsideration of the National Ambient Air Quality Standards for Particulate Matter (PM) (final rule of Feb 7, 2024, which also revises the PM2.5 AQI). https://www.epa.gov/pm-pollution/final-reconsideration-national-ambient-air-quality-standards-particulate-matter-pm
A8. Barkjohn, K. K., Gantt, B., Clements, A. L. 2021. Development and application of a United States-wide correction for PM2.5 data collected with the PurpleAir sensor. Atmospheric Measurement Techniques 14: 4617-4637. https://doi.org/10.5194/amt-14-4617-2021

## B. Data sources (Q4, Q5; from DATA.md and README)

B1. US EPA AirNow. Hourly AQ observations and reporting-area forecasts (files.airnowtech.org). https://docs.airnowapi.org/
B2. NOAA NESDIS. Hazard Mapping System (HMS) fire and smoke product. https://www.ospo.noaa.gov/products/land/hms.html
B3. NASA FIRMS. Fire Information for Resource Management System. https://firms.modaps.eosdis.nasa.gov/
B4. NOAA GSL. HRRR-Smoke (High-Resolution Rapid Refresh with smoke). https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/ ; AWS Open Data: https://registry.opendata.aws/noaa-hrrr-pds/
B5. NOAA NWS. National Air Quality Forecast Capability (AQM/NAQFC). AWS Open Data: https://registry.opendata.aws/noaa-nws-naqfc-pds/
B6. PurpleAir. API documentation and pricing. https://develop.purpleair.com/ ; https://community.purpleair.com/t/api-pricing/4523
B7. Berlinghieri, R., Burt, D. R., Giani, P., Fiore, A. M., Broderick, T. 2026. Are Hourly PM2.5 Forecasts Sufficiently Accurate to Plan Your Day? Individual Decision-Making in the Face of Increasing Wildfire Smoke. Bulletin of the American Meteorological Society 107(3): E598-E614. https://doi.org/10.1175/BAMS-D-24-0291.1 (motivates the persistence baseline)

## C. Health burden and smoke effects (Q3, Q6)

1. CDC. 2026. Most Recent National Asthma Data (most figures are 2024 data; emergency and hospital figures are 2023; page reviewed Oct 6, 2026). https://www.cdc.gov/asthma-data/about/most-recent-asthma-data.html
2. Same paper as A1; cite it once. Sugrue, R., et al. 2026. Wildfire-Specific PM2.5 Asthma Risk Across a Disproportionately Burdened Pediatric Population in Northern California. GeoHealth 10(2): e2025GH001530. https://doi.org/10.1029/2025GH001530
3. Aguilera, R., Corringham, T., Gershunov, A., Leibel, S., Benmarhnia, T. 2021. Fine Particles in Wildfire Smoke and Pediatric Respiratory Health in California. Pediatrics 147(4): e2020027128. https://doi.org/10.1542/peds.2020-027128
4. Heft-Neal, S., Gould, C. F., Childs, M. L., Kiang, M. V., Nadeau, K. C., Duggan, M., Bendavid, E., Burke, M. 2023. Emergency department visits respond nonlinearly to wildfire smoke. PNAS 120(39): e2302409120. https://doi.org/10.1073/pnas.2302409120
5. Washington State Office of Financial Management. 2022 (August). Increased medical and emergency department claims for asthma after wildfire smoke exposure in Washington, 2014-2018. https://ofm.wa.gov/sites/default/files/public/dataresearch/healthcare/pdf/smoke_exposure_extract.pdf (now redirects to a /wp-content/uploads/ address; recheck before submitting)
6. Oregon Health Authority. 2025. OHA data show poor air quality linked to more emergency visits. https://www.oregon.gov/oha/erd/pages/oha-data-show-poor-air-quality-linked-to-more-emergency-visits.aspx
7. Gabbay, J. M., Bajaj, B. V. M., Levano, S. R., Perez, J. M., Islamovic, F., Graham, R. J., Kahn, J. G., Hametz, P. A., Fiori, K. P., Rastogi, D. 2025. National Economic Burden of Pediatric Asthma Hospitalizations. Annals of the American Thoracic Society 22(10): 1611-1614. https://doi.org/10.1513/AnnalsATS.202501-128RL (Read 2026-11-25: a cross-sectional analysis of the 2022 Kids' Inpatient Database; 64,393 hospitalizations; mean cost $7,464 and total $480.6 million, both hospital costs in 2022 dollars derived from charges with the cost-to-charge ratio, not charges.)
8. Pearson, W. S., Goates, S. A., Harrykissoon, S. D., Miller, S. A. 2014. State-based Medicaid costs for pediatric asthma emergency department visits. Preventing Chronic Disease 11: 140139. https://doi.org/10.5888/pcd11.140139
9. Roemer, M. 2024 (September). Costs of Treat-and-Release Emergency Department Visits in the United States, 2021. HCUP Statistical Brief #311. AHRQ. https://hcup-us.ahrq.gov/reports/statbriefs/sb311-ED-visit-costs-2021.pdf
10. Nurmagambetov, T., Kuwahara, R., Garbe, P. 2018. The Economic Burden of Asthma in the United States, 2008-2013. Annals of the American Thoracic Society 15(3): 348-356. https://doi.org/10.1513/annalsats.201703-259oc (also cited in AAFA Asthma Facts and Figures, updated April 2026: https://aafa.org/wp-content/uploads/2025/04/aafa-asthma-facts-and-figures.pdf)

## D. Market and payers (Q6, Q8, Q9)

11. California Department of Education. 2026. School district organization list (935 districts). https://www.cde.ca.gov/re/lr/do/schooldistrictlist.asp
12. Oregon Department of Education. Schools and districts (197 districts). https://www.oregon.gov/ode/schools-and-districts/pages/default.aspx
13. Washington OSPI. About school districts (295 districts). https://ospi.k12.wa.us/about-ospi/about-school-districts
14. NCES. 2025. Common Core of Data, 2023-24 summary table 1 (13,303 regular districts). https://nces.ed.gov/ccd/tables/202324_summary_1.asp
15. KFF. 2026. Total Medicaid and CHIP child enrollment, July 2026. https://www.kff.org/medicaid/state-indicator/total-medicaid-and-chip-child-enrollment/
16. Regional Asthma Management and Prevention (RAMP). 2025 (updated June 2025). California's Asthma Preventive Services Fact Sheet. https://rampasthma.org/wp-content/uploads/2025/07/APS-Fact-Sheet-revised.pdf
17. Washington State Hospital Association. 2026. UW Medicine data and outreach connects patients to wildfire smoke guidance. https://members.wsha.org/weekly-newsletter/weekly-report-friday-july-10-thursday-july-16-2026/uw-medicine-data-and-outreach-connects-patient-to-critical-wildfire-smoke-guidance/
18. Bay Area Air Quality Management District. 2023 (Nov 13). RFP #2023-042, Advertising, Communications, and Survey Research Services for Spare the Air Program. https://www.baaqmd.gov/~/media/files/administration/rfp-rfq/2023/rfp-2023-042-sta-advertising/rfp-2023-042-sta-advertising-and-outreach-pdf.pdf
19. Ventura County Air Pollution Control District. Farmworker wildfire smoke alert program. https://www.vcapcd.org/farmworker-wildfire-smoke-alert/
20. Putnam County Board of Education. 2024. Agenda, June 27, 2024 (ParentSquare contract). https://meeting.boeconnect.net/Public/Agenda/546?meeting=641780
21. Times News. 2025. LASD buys subscription for emergency system (Raptor pricing). https://www.tnonline.com/20250702/lasd-buys-subscription-for-emergency-system/
22. US EPA. Air Quality Flag Program. https://www.epa.gov/air-quality/air-quality-flag-program

## E. Competition (Q7)

These competition sources were accessed November 7, 2026. The
[verification record](../COMPETITOR_VERIFICATION_2026-11-07.md) identifies the
claim each source supports and distinguishes current products, availability
notices and research. Existing reference numbers are retained; additional Q7
sources are numbered 48–53 below.

23. US EPA AirNow. API FAQ: reporting areas and forecast availability. [Official documentation](https://docs.airnowapi.org/faq).
24. US EPA AirNow. About the Fire and Smoke Map. [Official map overview](https://www.airnow.gov/fasm-v4/about/).
25. NOAA GSL. HRRR-Smoke. [Model documentation](https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/).
26. NOAA NCEP EMC. Operational Air Quality Forecast Change Log. [Implementation history and AirNow-based bias correction](https://www.emc.ncep.noaa.gov/mmb/aq/AQChangelog.html).
27. NOAA. National Air Quality Forecast Capability archive, Registry of Open Data on AWS. [Dataset description](https://registry.opendata.aws/noaa-nws-naqfc-pds/).
28. Google. Air Quality API overview. [Official API documentation](https://developers.google.com/maps/documentation/air-quality/overview).
29. Apple. 2026. Feature availability and data sources in the Weather app. [Official support page](https://support.apple.com/en-us/105038).
30. IQAir. AirVisual air-quality app. [Product page](https://www.iqair.com/air-quality-monitors/air-quality-app).
31. California Air Resources Board. 2022. California Air Resources Board releases California Smoke Spotter 2.0. [Historical launch announcement](https://ww2.arb.ca.gov/news/california-air-resources-board-releases-california-smoke-spotter-2). A dated precedent, not confirmation of current app availability; not needed for the shortened Q7.
32. Resmed. Propeller Health operating-status notice. [Current notice](https://www.resmed.com/en-us/health-professionals/solutions/propeller-health/).
33. US EPA. Smoke Sense Study: A Citizen Science Project Using a Mobile App. [Project and app-availability notice](https://www.epa.gov/air-research/smoke-sense-study-citizen-science-project-using-mobile-app).
34. AirRater. Environmental information, symptoms and personal alerts. [App Store listing](https://apps.apple.com/au/app/airrater/id1050535426); see also the developer listing, reference 50. (airrater.org currently redirects to a browser safety warning, so it is not linked.)
35. Liao, K., Buch, J., Lamb, K., Gentine, P. 2025. Simulating the air quality impact of prescribed fires using graph neural network-based PM2.5 forecasts. Environmental Data Science 4: e11. [Published paper, DOI 10.1017/eds.2025.4](https://doi.org/10.1017/eds.2025.4). This is the paper in the original NSF PAR 10611007 reference.
36. Dong, Z., Mao, J., Sayeed, A., Gupta, P., Zhao, T., Ahmadov, R., James, E. 2026. Machine Learning Bias Correction of HRRR-Smoke Surface PM2.5 Forecasts during the Alaska Wildfire Season. ACS ES&T Air 3(5): 1263–1275. [NOAA publication record and abstract](https://repository.library.noaa.gov/view/noaa/74016); [DOI 10.1021/acsestair.5c00409](https://doi.org/10.1021/acsestair.5c00409).
37. Same work as B7 (published version, cite once). The earlier check read the arXiv manuscript 2409.05866v2; the journal page (published March 24, 2026) now loads. Berlinghieri, R., Burt, D. R., Giani, P., Fiore, A. M., Broderick, T. 2026. Are Hourly PM2.5 Forecasts Sufficiently Accurate to Plan Your Day? Individual Decision-Making in the Face of Increasing Wildfire Smoke. Bulletin of the American Meteorological Society 107(3): E598-E614. https://doi.org/10.1175/BAMS-D-24-0291.1
38. Liu, Y., Ma, J., Dhillon, P., Mei, Q. 2024. PM2.5 forecasting under distribution shift: A graph learning approach. AI Open 5: 23–29. [Published paper, DOI 10.1016/j.aiopen.2023.11.001](https://doi.org/10.1016/j.aiopen.2023.11.001).
39. Kim, P., et al. 2025. mHealth Intervention Integrating Personal PM2.5 Monitoring and Deep Learning to Reduce Pediatric Asthma Exacerbations: Pilot Study. JMIR Preprints 84513, September 22. [Preprint and status page](https://preprints.jmir.org/preprint/84513), DOI 10.2196/preprints.84513. Do not describe this source as a validated Serein intervention.

## F. Costs and fundraising (Q9, Q10)

40. Twilio. 2026. US SMS pricing. https://www.twilio.com/en-us/sms/pricing/us
41. Meta. WhatsApp Business Platform pricing. https://developers.facebook.com/docs/whatsapp/pricing
42. Render. 2026. Pricing. https://render.com/pricing
43. PurpleAir. 2023. API pricing. https://community.purpleair.com/t/api-pricing/4523
44. USPTO. 2026. Fee schedule. https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule ; trademark fees: https://www.uspto.gov/trademarks/trademark-fee-information (read 2026-11-25, page updated November 4, 2026: $350 per class for a base electronic application, plus $100 per class for insufficient information and $200 per class for free-form descriptions of goods and services)
45. Space Center Houston. 2026. Conrad Challenge 2026-27 Student Guide. https://conrad.spacecenter.org/wp-content/uploads/2026/08/2026-2027-Conrad-Challenge-Student-Guide-Official.pdf
46. Conrad Challenge. 2026. 2026 Conrad Challenge Innovation Summit Awards. https://conrad.spacecenter.org/2026-awards/ (Read 2026-11-25. The page lists the 2025-26 awards and names no 1517 Fund or AWS prize, and the 2024-25 list at conradchallenge.org is a parked domain, so the sentence about those prizes was removed from Brief section 10. Do not cite this entry unless a section mentions Conrad awards.)
47. Davidson Institute. Davidson Fellows Scholarship, 2027 cycle. https://www.davidsongifted.org/gifted-programs/fellows-scholarship/eligibility/how-to-apply/

## Additional competition references (Q7)

Accessed November 7, 2026.

48. Sonoma Technology. 2023. Adding PurpleAir Data to the ExactAQ Hyper-Local Air Quality Map. [Provider's article](https://www.sonomatech.com/node/4916).
49. ExactAQ / Sonoma Technology. Air Quality Forecast. [Current forecast feature](https://exactaq.com/features/air-quality-forecast/).
50. AirHealth. AirRater. Google Play developer listing. [Current description of forecasts, symptom triggers and caregiver use](https://play.google.com/store/apps/details?id=com.senset.airrater&hl=en-AU).
51. Wang, R., Bhudia, A., Dos Remedios, B., Teng, M., Ng, R. 2020. Dense Forecasting of Wildfire Smoke Particulate Matter Using Sparsity Invariant Convolutional Neural Networks. Workshop preprint, arXiv 2009.11362. [Abstract and version record](https://arxiv.org/abs/2009.11362); [full text](https://arxiv.org/html/2009.11362v1).
52. Dimri, R., Choi, Y., Salman, A. K., Park, J., Singh, D. 2024. AGATNet: An Adaptive Graph Attention Network for Bias Correction of CMAQ-Forecasted PM2.5 Concentrations Over South Korea. Journal of Geophysical Research: Machine Learning and Computation 1(3): e2024JH000244. [Published paper, DOI 10.1029/2024JH000244](https://doi.org/10.1029/2024JH000244).
53. Resmed. 2018. ResMed to Acquire Propeller Health, a Leader in COPD and Asthma Connected Health Solutions, for $225 Million. [Historical product description, December 3](https://newsroom.resmed.com/news-releases/news-details/2018/ResMed-to-Acquire-Propeller-Health-a-Leader-in-COPD-and-Asthma-Connected-Health-Solutions-for-225-Million/default.aspx). Current operating status is documented separately in reference 32.

## Novelty check (Q4), added 2026-11-23

54. Huang, J., McQueen, J., Wilczak, J., et al. 2017. Improving NOAA NAQFC PM2.5 Predictions with a Bias Correction Approach. Weather and Forecasting 32(2): 407-421. https://doi.org/10.1175/WAF-D-16-0118.1
55. Hamer, S., Sleeman, J., Stajner, I. 2023. Forecast-Aware Model Driven LSTM. arXiv 2303.12963. https://arxiv.org/abs/2303.12963
56. Su, J. G., Barrett, M. A., Henderson, K., et al. 2017. Feasibility of Deploying Inhaler Sensors to Identify the Impacts of Environmental Triggers and Built Environment Factors on Asthma Short-Acting Bronchodilator Use. Environmental Health Perspectives 125(2): 254-261. https://doi.org/10.1289/EHP266
57. Google. Air Quality API overview (hourly forecasts up to 96 h on a 500 m grid). https://developers.google.com/maps/documentation/air-quality/overview (Rechecked 2026-11-25, page updated 2026-11-09: hourly forecasts "up to 96 hours", "500 x 500 meters resolution", over 100 countries, health recommendations for groups including children and people with asthma; no accuracy figures on the page. Recheck the day before submitting, as for every link.)

## Business plan and Brief sections 8 and 10, added 2026-11-25

Read 2026-11-25. Entries 58 to 62 are cited only in `docs/drafts/business_plan.md`
unless the outdoor-employer buyer is added to Brief section 6.

58. California Code of Regulations, Title 8, section 5141.1. Protection from Wildfire Smoke. https://www.dir.ca.gov/title8/5141_1.html
59. Oregon Administrative Rules 437-002-1081. Protection from Wildfire Smoke (effective July 1, 2022). https://www.law.cornell.edu/regulations/oregon/Or-Admin-Code-SS-437-002-1081
60. Washington State Department of Labor and Industries. Wildfire smoke (chapter 296-820 WAC). https://www.lni.wa.gov/safety-health/safety-topics/topics/wildfire-smoke
61. California Employment Development Department. 2025. California Agricultural Employment, 2023 annual average (state total 407,700). https://labormarketinfo.edd.ca.gov/file/agric/ca-ag-employ-map-2023.pdf
62. California Education Code section 42127 (school district budgets adopted on or before July 1). https://california.public.law/codes/education_code_section_42127
63. Lozano Smith. 2025 (December 10). Bid Thresholds Raised For 2026 (Public Contract Code section 20111(a): $119,100 for K-12 purchases of equipment, materials, supplies and services other than construction, from January 1, 2026). https://lozanosmith.com/news-clientnewsbriefdetail.php?news_id=3451 (A law firm's summary; the 2027 amount is usually announced in December, so recheck before submitting. Cited in Brief section 8.)
64. Conrad Challenge. Phase 2: Innovation Stage (deadline January 7, 2027; $499 per team; financial aid applications November 2 to December 3, 2026). https://conrad.spacecenter.org/the-challenge/innovation-stage/ (Cited in Brief section 10.)
65. Conrad Challenge. Financial Aid Opens for Phase 2: Innovation Stage. https://conrad.spacecenter.org/calendar/financial-aid-opens-for-phase-2-innovation-stage-2/
66. USPTO. Trademark Status and Document Retrieval, serial numbers 90636402 and 98444557 (status pages generated 2026-11-26 01:00 EST). https://tsdr.uspto.gov/ (Supports `docs/drafts/ip_decision_memo.md`; not cited in the Brief.)

## Market size, Brief section 6, added 2026-11-27

Read 2026-11-27. The total (7,366,904 students) and the $3.7 to $11.1 million range are
computed in `src/serein/business.py` (`district_market`) and tested.

67. California Department of Education. Fingertip Facts on Education in California, 2025-26 (5,731,260 students, K-12 including charter schools; 1,011 districts including county offices). https://www.cde.ca.gov/DS/ad/ceffingertipfacts.asp
68. Oregon Department of Education. Oregon Statewide Report Card 2025-26 (539,644 students on the first school day of October 2025; 197 districts). https://www.oregon.gov/ode/schools-and-districts/reportcards/Documents/rptcd2026.pdf
69. Superville, D. R. 2026 (January 9). Public school enrollment falls across Washington state. The Seattle Times, reprinted in The Spokesman-Review (1.096 million students in prekindergarten through 12th grade in October 2025, citing OSPI data). https://www.spokesman.com/stories/2026/jan/09/public-school-enrollment-falls-across-wa/ [TEAM: OSPI's own report card page would not load for us; if someone can open https://reportcard.ospi.k12.wa.us, replace this with OSPI's exact figure.]

## AI tools (required by the Rules and Regulations)

Conrad's Rules and Regulations, "Use of and Standards for Competition Submissions",
item 4 (read 2026-11-25): a submission "may not copy or use other materials- including
artificial intelligence (AI) tools- without properly citing the source." Item 2 says
the submission "must be entirely the work of the student team members."
https://conrad.spacecenter.org/the-challenge/rules-and-regulations/

No part of the Brief, the website or this list names an AI tool yet.

[TEAM: before submitting, list here every AI tool any of us used, with the maker, the
version or model if known, the months of use, the address, and one line on what it was
used for (for example code, documentation, literature search, drafting). Each member
answers for their own part. Then say in one sentence, in the Brief or on the website,
which parts are our own decisions. Judge Q&A answer 22 depends on this.]

## Optional attachments (up to 2): recommendation

The Student Guide allows two attachments beyond the reference list. Judges skim; pick the
two that carry the most of the argument on their own.

1. **`docs/results/figures/fig_warnings_vs_epa.png`** (warnings a day ahead, Serein vs
   EPA's official forecast, hits and false alarms). It is the single chart that says
   "we warn earlier and cry wolf less," which is the claim a parent, a nurse and an
   investor all care about. Regenerate after the final test; caption it with the season
   and the word "held-out."
2. **`docs/results/figures/map_20230818.png`** (the neighborhood forecast map on a real
   smoke day) **or** `fig_improvement_map_L1.png` (monitors where Serein beat NOAA).
   The forecast map shows the product; the improvement map shows the evidence. If the
   video already shows the map, attach the improvement map here. Either way, add a
   caption that names the date, the lead, and the baseline.

Not recommended as attachments: `fig_rmse_by_lead_all.png` (RMSE is already in the text
and a line chart of error adds little for non-specialists); `airplan_learning_curve.png`
(simulated children; a judge may read it as real data unless captioned carefully).
### Fill-in template (2026-11-27)

One row per tool per member. Leave nothing out: a tool used once for one paragraph
still gets a row. Ask each member separately, and include tools used only for code.

| Member | Tool and maker | Version or model | Months used | Address | Used for |
|---|---|---|---|---|---|
| [name] | [tool] ([company]) | [version] | [Mon YYYY to Mon YYYY] | [https://...] | [code / documentation / literature search / drafting / editing / images] |

Reference-list form, one per tool (APA 7th style, the form APA gives for AI tools):

> [Company]. ([year of the version used]). *[Tool name]* ([version or model]) [Large
> language model]. [https://...]

Statement for the Brief or the website, to finish once the table is filled in:

> We used [tools] for [what, in plain words]. The research question, the study design,
> the choice of data and of the test years, the protocol and its acceptance rule, every
> number we report, and every decision about the product were made by the team, and we
> checked every line of code and text we kept.

Only claim in that statement what is true for every member. Before writing it, check:

- [ ] Every member has filled in their own rows, including "none" if that is true.
- [ ] The tools are also named in the reference list, in the form above.
- [ ] The statement matches the table (no tool used for something the statement leaves out).
- [ ] Judge Q&A answer 22 (`docs/drafts/judge_qa_prep.md`) says the same thing.
