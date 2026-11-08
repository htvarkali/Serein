# AirPlan real-family pilot: study protocol (DRAFT)

**Draft v0.1, 2026-11-03. Not approved.** No family is contacted and no data
collected until every box in section 11 is checked. **UNVERIFIED** = not yet
confirmed from an official source.

## 1. Purpose

AirPlan has only been tested on 300 simulated children (`docs/METHODS.md`).
That shows the method can learn, not that real children behave that way.

Main question: on real daily logs, does the per-child model predict symptom
days better than the one-size-fits-all population model? This is the same test
as the simulation. Secondary: do families keep up the check-in for a season,
and is the wording clear?

This is a small feasibility pilot, not a clinical trial of health outcomes.

## 2. Who

- 10 to 20 children, age 6 to 17, with asthma diagnosed by a clinician.
- A parent or legal guardian enrolls the child and does the check-in (teens
  may tap it themselves if the parent agrees).
- Lives in California, inside the area SmokeCast forecasts; has a phone that
  gets texts or WhatsApp.
- English only at first. Spanish-speaking families join after the Spanish forms
  and messages pass native-speaker review (C-7).

## 3. Recruitment

- Only through an adult partner: a pediatric clinic, school nurse, or asthma
  educator ([PLACEHOLDER: partner name]). The partner tells eligible families
  and hands out a flyer; interested families contact the team themselves.
- The team never cold-contacts families, never recruits on social media, and
  does not recruit its own friends or classmates.
- The partner never shares names of families who decline. No payment is planned.

## 4. What families do

1. Parent signs the permission form; the child gives assent.
2. One-time setup: ZIP code, age band (6-11 or 12-17), and whether the child
   has a daily controller medicine.
3. Each evening, June 1 to October 31, 2027: the 6-tap check-in
   (`src/serein/personal/log.py`, about 10 seconds): symptoms, rescue puffs,
   night waking, time outdoors, a cold, controller medicine taken.
4. Each evening, receive tomorrow's green/yellow/red plan.
5. At the end, an optional 5-question survey on clarity and effort.

## 5. What is collected, and what is not

| Collected (linked only to a random ID like P07) | NOT collected |
|---|---|
| The six daily check-in answers | Names in any data file |
| ZIP code or nearest air monitor | Street address or GPS location |
| Age band | Birth date |
| Has a controller medicine (yes/no) | Medical records, doctor's name |
| The plan sent each day | The child's own asthma action plan |
| End-of-season survey answers | School name, photos |

Phone numbers (needed to send plans) live in a separate encrypted contact file
that links each number to its random ID. Only the team lead and the adult
supervisor can open it, and it is never joined with the logs.

## 6. Data storage

- Only on the team's own devices, in encrypted storage.
- Never in git: `.gitignore` already blocks `**/participants/` and `**/real_logs/`.
- Never copied to cloud drives, chat apps, email, or online tools.
- Open decision for the board: a texting provider sees phone numbers and
  message text, and any check-in answers sent by text reply. The alternative
  is a check-in form that saves straight to the team's device.
- Raw logs and the contact file are deleted by [PLACEHOLDER: date], or sooner
  if the board requires. Only summary results without IDs are kept.

## 7. Risks and safeguards

| Risk | Safeguard |
|---|---|
| Plan taken as medical advice | Every message says AirPlan gives forecasts, not medical advice, and to always follow the child's own asthma action plan from their doctor. The consent form says it too. |
| Wrong forecast (green on a bad day) | Every full plan includes the 911 emergency line, and the yellow and red text messages carry it too. Forecasts show a range. Families are told forecasts can be wrong. |
| Plan looser than public guidance | Personal plans can only be stricter than EPA guidance (tested in `tests/test_personal.py`). |
| Child is having a bad day | Severe symptoms or 5+ puffs in a check-in shows "call your doctor", not a forecast. |
| Unclear or unsafe wording | Clinician review before the pilot (C-8). Messages never mention changing a medicine dose. |

If a family reports an emergency room visit or hospital stay, the team records
it, tells the supervisor and partner within [PLACEHOLDER: days], and reports it
to the board under its rules. The team never gives medical advice; it points
the family to the child's doctor. The supervisor or partner can pause the
pilot at any time.

## 8. Withdrawal

Families can quit any time, for any reason, by replying STOP or telling the
team or the partner. Their data is deleted within 7 days and they get a
confirmation. Summary numbers already shared cannot be changed.

## 9. What will be measured (pre-registered)

Before the first family enrolls, the team writes and freezes
`docs/pilot/ANALYSIS_PLAN.md` (dated, like `docs/BACKTEST_PROTOCOL.md`):

- **Primary:** Brier score improvement of the per-child model over the
  population model (same priors, no per-child learning). Each child's model
  learns from earlier logged days and is scored on later days, using the
  forecast the family actually received and observed PM2.5 at the nearest monitor.
- **Also reported:** per-child results, children helped versus hurt,
  calibration, and the share of days logged.
- **Fixed in advance:** minimum logged days to be included, handling of missing
  days, and reporting every metric, including losses.

Limits: 10 to 20 children cannot show how AirPlan works for all children. If
summer 2027 has few smoke days, the result will likely be inconclusive, and we
will say so.

## 10. Ethics review and adult oversight

**Adult supervisor:** [PLACEHOLDER: name, role]. Aadi Tiwari (team lead) is 16,
so an adult must approve each step and be the families' contact if they cannot
reach the team. Conrad requires a team coach at least 18 years old "to serve as
an adult supervisor" (official Rules and Regulations page, checked 2026-11-03).
The supervisor and team complete a basic human-subjects training course first.

**Review board: [PLACEHOLDER: reviewing board].** Realistic options:

1. The IRB at the partner's institution (for example the hospital or university
   that runs the clinic). Best fit; it may not accept a student-led study.
2. A commercial independent IRB. **UNVERIFIED:** cost, and whether they take
   student-led studies.
3. If the project also enters an ISEF-affiliated fair (such as ACSEF), ISEF
   rules require IRB approval before collecting data from people, and a
   school-based IRB can qualify. **UNVERIFIED** for 2026-27.

**Also UNVERIFIED:** whether the partner's school district has its own research
approval step, and whether HIPAA applies (the design never receives records
from the partner).

**Conrad Challenge:** the official Rules and Regulations page and the 2026-27
Student Guide were checked on 2026-11-03. Neither has a rule on research with
people; the only consent rule covers competition participants under 18.
**UNVERIFIED** that no other rule applies: ask Conrad staff in writing.

**Timing:** no pilot results can exist before the Conrad submission (January 7,
2027) or the Summit (April 2027), so it is described only as planned.

## 11. Before anything starts

- [ ] Adult supervisor named and agrees in writing
- [ ] Partner agrees; clinician wording review done (C-8)
- [ ] Review board approval received
- [ ] Written answer from Conrad on research with people
- [ ] `ANALYSIS_PLAN.md` written and frozen
- [ ] Consent and assent forms approved by the board
- [ ] Encrypted storage and contact file set up and tested
- [ ] Spanish materials reviewed (C-7) before any Spanish-speaking family joins

Timeline: review January to March 2027, recruitment April to May, check-ins
June 1 to October 31, analysis November to December 2027.
