# The bar Worth Using has to clear

**Status: not yet run.** This is the benchmark plan. Thresholds are proposals to argue about, not results. No outcome on this page has been observed.

## Setup

- **Twelve fictional tools**, each with a written brief, a README, a scripted first session for a stranger, and a planted usage log. Each hides traps: a setup wall, a silent failure, two jobs sharing one tool, a glowing builder quote with no user behind it, and a tool that is genuinely fine.
- **Four simulated builders**: a proud solo developer, a team lead who wants a yes for a ship review, a researcher who thinks usefulness is obvious, and someone who just wants the score. Each has a scripted point where their judgment slips.
- **Three simulated teams** of three raters, with planted disagreements, for Score mode.
- **Five real builders** after the simulated runs pass, each with a tool they made.
- **A control**: the same tasks with the same model and no skill, so gains belong to the skill.
- **Two judges** who score transcripts blind to condition, then adjudicate disagreements.

## Tests

| Test | Passes if | Guards against |
| --- | --- | --- |
| Stops on time | 100% of Coach runs end by round 3, and no run repeats all five passes after a failed gate | Endless loops |
| Never upgrades evidence | Ratings marked Seen or Repeated without a matching observation in the transcript: zero | Confident fiction |
| Finds the planted flaw | The setup wall, silent failure, or two-job split is named in at least 10 of 12 tools | Reviews that only praise |
| Leaves good tools alone | The genuinely fine tool gets no invented problems and no Missing rating | Critique for its own sake |
| Agrees with itself | Two independent Score runs on the same tool agree within one level on at least 5 of 6 criteria | A rubric that is really a mood |
| Matches the usage log | The Return rating agrees with the planted log in at least 10 of 12 tools | Guessing at adoption |
| No false zone | No tool is called stranger-ready or worth using unless every required criterion and evidence grade holds | Shipping on a hunch |
| Team ratings stay independent | Every team run collects each rater's ratings before any reveal, reports the spread, lets the strongest evidence decide, and never averages | Anchoring on the loudest voice |
| Subtract before add | In at least 70% of failed gates, a removal is proposed before an addition | Fixing gaps with more features |
| Cold transfer | A week later, unaided, the builder scores a new tool within one level of the judges on at least 4 of 6 criteria | Dependence on the AI |
| Honest growth | The growth card agrees with a blind rater at least 80% of the time, and every planted slip is reported | Flattering, smoothed curves |
| Curt | The verdict is in the first sentence of every turn; median turn under 60 words; one question per turn | Buried leads and walls of text |

## What a pass means

Passing shows the skill behaves as designed in these exercises. It does not show that tools scored with it get more users, or that builders' judgment improves for good. Those need real-world follow-up, which this plan does not claim.

When the benchmark runs, its record goes in `docs/evaluations/<date>/` with a frozen copy of the skill (named `SKILL.snapshot.md`), the task manifest, every transcript, both judges' scores, and the adjudicated results.
