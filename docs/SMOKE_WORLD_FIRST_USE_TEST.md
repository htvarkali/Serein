# Watching five people use Smoke World for the first time (task W-19)

Written 2026-11-26. Nobody has been tested yet. This is the script and the sheet to
fill in. It takes about 15 minutes a person and needs no code.

The point is to find where a new person gets stuck or reads the page wrongly. It
does not measure whether the forecast is right, and five people are too few for
percentages. Report counts ("3 of 5 could not find...") and what they said.

## Who to ask

Five people who have never seen the site and are not on the team. Try for a mix:

1. a parent,
2. a teacher, coach or school nurse,
3. a student who is not in a computer science class,
4. someone over 60,
5. anyone, on a phone instead of a laptop (this one also informs W-12).

## Rules

- No names in the notes. Use T1 to T5 and a role ("parent", "coach").
- Ask before you start: "I'm testing the website, not you. Can I write down what you
  do and say? I won't write your name." Stop if they say no.
- Do not record audio or the screen without asking. Typed notes are enough.
- Do not ask about anyone's health. If they bring up their own child, do not write
  down anything that could identify the child.
- Two of us per session if possible: one talks, one writes.

## Setup

- Open htvarkali.github.io/Serein on the home page, in a private window, on their
  own device if they are willing. Note the device and whether it is a phone.
- If the West is clear of smoke that day, the live map will look empty. That is
  worth seeing once, but for at least three of the five, start task 3 from the
  August 2023 example so there is smoke to read.
- Say this, and nothing more: "This is a website a group of students made about
  wildfire smoke. I'll ask you to try a few things. Please think out loud. I can't
  help or answer questions until the end, because I need to see where it's confusing."

## The hardest rule

When they get stuck, stay quiet and count to thirty. Write down what they try. Only
then say "what would you try next?" If they are still stuck after a minute, mark the
task as not done and move on. Every time we help, we lose the finding.

## Tasks

Read each task aloud exactly. The words avoid the names of buttons on purpose.

| # | Say this | Done means | What it tells us |
|---|---|---|---|
| 1 | "Without clicking anything yet: what is this website for, and who is it for?" | They say smoke, a forecast, and children or asthma, in their own words | Whether the home page explains itself |
| 2 | "Find the map of smoke." | They reach the Smoke World page | Whether the way in is findable |
| 3 | "Find out how smoky it is expected to be tomorrow in a town you know." | They pick a place and read the daily level | The main job of the page |
| 4 | "The forecast gives a low and a high number. What do you think they mean?" | They say something like "it could be anywhere between these" | Whether the range is understood or ignored |
| 5 | "Watch how the smoke changes over the next three days." | They press play or drag the hour control | Whether the time controls are found |
| 6 | "Is the hour-by-hour picture something you would rely on to plan a soccer practice at 4 pm? Why?" | Any answer. Note whether they noticed that the hourly map is labeled as illustrative | Whether our limit is visible. We tested the daily level, not the hours |
| 7 | "This map can show two versions of the forecast. Switch to the other one." | They switch between NOAA and Serein | Whether the comparison is findable and what they think it is |
| 8 | "Find out where this information comes from." | They open the data sources | Whether the sources are findable |
| 9 | "If your child had asthma and you saw this for tomorrow, what would you do?" | Any answer. Write it word for word | Whether the page leads to an action |
| 10 | "Where would you look to see what the air is like right now?" | Any answer. Note whether they know this page is a forecast and AirNow is for now | Whether a forecast is mistaken for a current reading |

## What to write down for each task

| Tester | Task | Done without help? | Seconds | First thing they tried | Where they got stuck | Their words |
|---|---|---|---|---|---|---|
| T1 | 1 | | | | | |
| T1 | 2 | | | | | |

One row per task per person: fifty rows in all. Save as
`docs/interviews/W19_T1_YYYY-MM-DD.md` and so on, with the role and device at the top.

## Three questions at the end

1. "What was the most confusing part?"
2. "What would you want it to tell you that it doesn't?"
3. "Would you open this again on a smoky day? What would you use now?"

Now you may answer their questions.

## Turning it into fixes

After all five, list every place where someone got stuck and count how many people
it happened to.

| Stuck on | People (of 5) | Rating | Fix | Board task |
|---|---|---|---|---|
| | | | | |

Rating: **3** if someone could not finish a task or drew a wrong and risky conclusion
(for example, reading the forecast as the air right now, or trusting an hour-by-hour
value); **2** if they finished after a struggle; **1** if it was only a comment.
Fix every 3 before the video is filmed. Fix a 2 if two or more people hit it.

Put two things in the Brief (section 5, feedback): how many people we watched, and the
one change we made because of it. Do not report anything we did not see.

## Labels on the page as of 2026-11-26

For whoever reads the notes later, since the page is still changing: the map page is
headed "Forecast explorer"; choosing a place shows "SmokeCast daily outlook" with the
"Daily average PM₂.₅ and 90% forecast range"; the hourly view is "Explore hourly
estimates" over an "Illustrative hourly map" with a "Forecast hour" control and Play;
the two versions are "NOAA" and "Serein-scaled"; the past event is "August 2023:
Pacific Northwest"; sources are under "See data sources and methods".
