# Clinician review request (task C-8)

Target: one pediatric pulmonologist, allergist, pediatrician, respiratory therapist,
or certified asthma educator (AE-C). A school nurse counts if no one else responds.
Ask by Nov 21 so feedback lands before the Dec 7 final test and the Dec 21 brief draft.

Who to ask, in order: a team member's own pediatrician; any parent on the team who
works in healthcare; the asthma or pulmonology clinic at the nearest children's
hospital (general inbox, say "student project, 20-minute written review"); the
regional asthma coalition (California: RAMP, rampasthma.org; Oregon: Oregon Asthma
Network; Washington: Washington Asthma Initiative); a university respiratory-therapy
program; your school nurse for an introduction.

Make it a 20-minute ask with everything attached. **Ready to attach (2026-11-27):**
[`docs/review/clinician_packet.pdf`](../review/clinician_packet.pdf), which holds attachments 1 to 3
below, generated from the code by `scripts/build_review_packets.py`. Rebuild it after any
change to the messages or the priors. Clinicians say yes to small,
specific, bounded requests and no to "can we chat sometime."

---

## Email

Subject: 20-minute review request: smoke-day asthma messages for families (student project)

Dear Dr. [Name],

I'm a high school student on a five-person team building Serein, a free tool for
families of children with asthma. It forecasts wildfire smoke for a family's
neighborhood one to three days ahead and sends a short green, yellow or red plan for
their child the evening before, in English or Spanish. We are entering it in the
Conrad Challenge, a national student innovation competition, with a submission due
January 7.

We will not send any message to a real family without a clinician's review, and we
have not yet found one. Would you be willing to spend about 20 minutes reviewing
two things, in writing, at any time before [date]?

1. The six messages a family could receive (green, yellow, red, in English and
   Spanish). About one page.
2. A one-page table of the published studies we used as starting assumptions for
   how smoke, viral infections and inhaled-steroid adherence affect a child's
   symptom risk.

Both are attached, with a short review sheet of five questions. Our rules, which
you can also check: plans can only be stricter than EPA's public guidance, never
looser; every message tells families to follow their child's own asthma action plan
and lists emergency signs; the tool never diagnoses or changes medication.

If you are willing, we would like to name you as a reviewer in our submission (role
and affiliation only, or anonymously if you prefer). We are also happy to make any
change you ask for, or to remove anything you think should not be said to a parent.

Thank you for considering it.

[Name], [grade], [school], on behalf of Team Serein
[email] · [project site]

---

## Attachment 1: the messages

Paste the six messages from `docs/mockups/messages.md` (WhatsApp long form and SMS
short form for green, yellow and red, English and Spanish). Include the fictional
child's name note: "Maya is a made-up child; the numbers are from a sample forecast."

## Attachment 2: the priors table

Paste the priors table from `docs/METHODS.md` (Sugrue 2026, Khetsuriani 2007,
Williams 2011, Strickland 2010, CDC ACBS) with one line each on what we took from
the paper and how it enters the model.

## Attachment 3: review sheet (one page)

Please answer in a sentence or two each; "fine" is a complete answer.

1. **Safety floor.** Our plans can only be stricter than EPA AQI guidance for
   sensitive groups, and always say "follow your child's asthma action plan" and
   list emergency signs (hard to breathe, lips or nails blue, rescue inhaler not
   helping, call 911). Is anything missing from that floor?
2. **Wording.** Is there any sentence in the six messages you would not want a
   parent to read? Please mark it and say why.
3. **Thresholds.** The plan is at least yellow when the forecast median is
   "Unhealthy for Sensitive Groups" or worse (or the upper end of the range is
   "Unhealthy"), and red when it is "Very Unhealthy". The child's log can raise the
   zone: yellow when the estimated chance of symptoms is 1.3 times, or 5 points
   above, the same child on a clean-air day; red at 2 times or 15 points. Does that
   make clinical sense?
4. **Priors.** Do the starting assumptions in the table match your clinical
   experience? Is any effect size implausible for children?
5. **Learning from check-ins.** We estimate a child's smoke sensitivity from a
   daily six-tap check-in (symptoms, rescue inhaler use, activity, sick today?).
   What would make that estimate misleading? What should we never infer from it?

Optional: May we name you as a reviewer (name, role, affiliation)? [yes / role and
affiliation only / anonymously / no]

---

## After the review

- Record their answers in `docs/interviews/C1_YYYY-MM-DD.md` (no patient info).
- Make every change they ask for, or write down why not and ask again.
- Update `review_status` in `src/serein/personal/messages/en.yaml` and `es.yaml`.
- Brief Q5: "Reviewed by [role, affiliation], who asked us to change X and Y."
- Website safety section: same line.
- Send them the final submission and a thank-you.
