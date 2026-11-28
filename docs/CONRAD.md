# Conrad Challenge 2026-27: what we must submit

Source: official [2026-2027 Student Guide](https://conrad.spacecenter.org/wp-content/uploads/2026/08/2026-2027-Conrad-Challenge-Student-Guide-Official.pdf), read in full on 2026-11-01.

## Dates
| What | When |
|---|---|
| Team registration + **Lean Canvas** | **Oct 29, 2026, 11:59 pm CT** (already passed: confirm it was submitted in the Award Force portal) |
| Financial aid for the $499 fee: applications open | Nov 2 to **Dec 3, 2026, 11:59 pm** (the event page says ET, the calendar entry CST; treat the earlier one as the deadline) |
| **Innovation Stage: Brief + Video + Website + $499 fee** | **Jan 7, 2027, 11:59 pm CT** (team's internal target: Jan 1) |
| Innovators/Finalists announced | February 2027 |
| Innovation Summit (finalists), Space Center Houston | April 21-24, 2027 |

Financial aid for the fee is available (apply via the portal link in the guide; one form per team, linked from the Innovation Stage page). Dates added 2026-11-27 from the Conrad pages cited in `docs/drafts/references_DRAFT.md` (entries 64 and 65).

## Category
Options: Aerospace & Aviation, Cyber-Technology & Security, **Energy & Environment**,
**Health & Nutrition**, The Water Challenge. Serein fits **Health & Nutrition**
(children's asthma) or Energy & Environment (wildfire smoke). Confirm which one
was picked on the Lean Canvas.

## Innovation Brief: 10 questions, 3,000 words total
| # | Question (word limit) | Where our material is |
|---|---|---|
| 1 | Elevator Pitch (150) | README intro |
| 2 | Team (150) | README task S-3 (names, roles) |
| 3 | Opportunity (300) | README "three gaps"; interviews (E-1) |
| 4 | Key Metrics (750): how it works, what's new, impact, IP protection | docs/METHODS.md; backtest results (D-5); AirPlan simulation |
| 5 | Validation/Progress (450) | Backtest vs NOAA + EPA (`outputs/backtest/`), simulation study, expert feedback (C-8), interviews |
| 6 | Market (300) | E-4 |
| 7 | Competition (300) | E-5 |
| 8 | Go-To-Market (150) | E-4, E-7 partner letters |
| 9 | Business Model (300) | E-4 |
| 10 | Fundraising (150) | E-4 |
| - | Reference list (attachment) | docs/METHODS.md citations, docs/DATA.md |
| - | Up to 2 optional attachments | Backtest figure + forecast map / app screenshot |

## Video: 3-5 minutes
Must show a model of the innovation (sketch, wireframe, prototype). We have a
working prototype: the Streamlit app (`app/streamlit_app.py`) and forecast maps
(`serein map`). Upload to YouTube/Vimeo (unlisted is OK) AND as MP4 < 800 MB.

## Website
Team story, mission; model of the innovation with images; brand (name, logo,
colors); accessible by direct link (may be hidden from search engines).

## How judges score (Scoring Guide)
| Weight | Area | What they ask | Our strongest evidence |
|---|---|---|---|
| 30% | Innovation | Unique? Impactful? Defensible? | Graph network on sensors + personal Bayesian plans; nothing like it in AirNow/PurpleAir/IQAir |
| 20% | Storytelling & Professionalism | Would an investor want more? | One child's story (Maya) + the backtest chart |
| 20% | Practicality | Will it work? Proof of concept? Evidence? | **Pre-registered backtest beating NOAA/EPA**, working app, tests |
| 20% | Marketing Strategy | Markets, buyers, competition | School districts, Medicaid asthma programs, air districts |
| 10% | Finances | Costs, revenue, funding | Cloud cost per city per month; free for families |

Practicality explicitly rewards "data, expert testimony, ... research establishing
feasibility": the backtest and an expert review (C-8) map directly onto it.
