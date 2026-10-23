# A worked run, start to finish

This is an **invented example**. The lab, the people, the tool, and every number are fictional. Nobody was observed and no usage was logged. It shows the shape of a Coach run, including the parts that go badly.

## The tool

A genomics lab has written a command-line tool that checks sample sheets before a sequencing run: barcodes that collide, missing columns, sample names the sequencer will reject. It reads a 40-line configuration file that describes every rule. The lab uses it weekly and calls it SheetCheck. Three other labs installed it after a conference talk. As far as anyone knows, none of them ran it twice.

The builder is the lab's research software engineer. Target, agreed at the start: *stranger-ready*. Budget: three rounds.

## Opening read

> **Reviewer:** Who used it last week who isn't on your team?
>
> **Builder:** Nobody I can name. Three labs installed it.
>
> **Reviewer:** Installed is a claim. Walk me through a stranger's first ten minutes. Where do they stall?
>
> **Builder:** They don't, really. You point it at the config and go.

Before hearing any ratings, the builder rates the tool: Job Partial, First value **Solid**, Fit Partial, Outcome Partial, Trust Partial, Return Partial. All Claimed.

Private placement of the builder, with evidence: Perspective **Early** (describes what the tool does). Specificity **Early** ("labs"). Evidence **Early** (counts installs as use). Calibration **Developing** (rated Return only Partial, honestly). Subtraction **Early** (the config file is a point of pride).

## Round one

**Name the user.** The reviewer shows a vague sentence beside a specific one, then asks for the builder's.

> **Builder:** "I made this for labs that sequence, so their runs don't fail."
>
> **Reviewer:** That's every lab with a sequencer, which is the problem. Who actually touches the sheet, and when?
>
> **Builder:** "I made this for the core-facility staff who check sample sheets before booking the Monday run, which today costs them a re-run, or a day of emails, whenever a sheet is wrong."

Gate: role, recurring job, cost. **Pass.** The builder chose facility staff over principal investigators because "PIs never touch the sheet; the facility gets the angry email."

**Watch the first ten minutes.** The builder predicts the first stall: "maybe the install." A postdoc from a neighboring lab, who has never seen the tool, tries it with her own sheet while the builder watches without helping. She installs it in two minutes, then spends 23 more on the config file and gives up. First value is **Missing, Seen**. Calibration drops to **Early**: the builder had rated First value Solid. Dip labeled: *watched a real user for the first time*.

The reviewer asks what could be removed before anything is added. The builder proposes a setup guide, then hears the question again and cuts the config to one optional flag, with sensible defaults for the two common sequencers. They chose that over the guide because "a guide is a confession." Gate: **pass**, by the second route: the stall is named and a fix chosen. First value stays Missing until a stranger tries the fix.

**Break it on purpose.** The builder picks the input most likely to fool it: a sheet with an extra column the tool doesn't know. It passes the sheet as clean, silently ignoring the column. Gate: **fail**. Trust is **Missing, Claimed**: the builder found it, not a user. The builder chooses to list every skipped column in the output over failing hard, because "they still need to book the run."

**Say what changed.** First try: "runs are more reliable." The reviewer asks for the user's words, without adjectives. The builder shows the facility manager the new output; she says, "that's the email I send twice a week." Outcome: **Solid, Seen**. Gate: **pass**.

**Check for return.** Confidence before scoring: high. Ratings now: Job Solid Seen, First value Missing Seen (the cut hasn't met a stranger yet), Fit Solid Seen, Outcome Solid Seen, Trust Partial Claimed (fixed, untested), Return Missing Claimed. Target **not met**. Diagnosis rows: *the demo works; a stranger's first try doesn't → return to Watch*, and *users trust it until the first silent mistake → return to Break.*

## Round two (Watch, Break, Check)

The builder leads; the reviewer prompts only at the gates. A second stranger, a technician from another floor, gets a clear result in three minutes with no help. First value: **Solid, Seen**. On the second Break, faced with confusing error text, the builder proposes a small web dashboard to explain errors. The reviewer asks what could be cut instead. The builder shortens every message to one line naming the row and the fix, and drops the dashboard. Subtraction dips, then recovers: *the old reflex to add came back under pressure.* Trust: **Solid, Seen**, after the technician recognizes a skipped column in the output and fixes her sheet herself.

**Check for return.** Confidence before scoring: medium. Stranger-ready: **met**. Worth using: **not shown**, because Return can't be seen in an afternoon. Return check set.

## The two cards

```
USEFULNESS CARD · SheetCheck · round 2 of 3
User + job    Core-facility staff · checking sample sheets before the Monday booking · a failed sheet costs a re-run or a day of emails
Job           Solid · Seen · The facility manager confirmed the job and the weekly rhythm
First value   Solid · Seen · A technician got a clear result in three minutes, alone, after the config was cut
Fit           Solid · Seen · Runs on the spreadsheet they already export
Outcome       Solid · Seen · "That's the email I send twice a week."
Trust         Solid · Seen · Skipped columns are listed; the technician fixed her own sheet
Return        Missing · Claimed · Not observable yet
Zone          Stranger-ready met · Worth using not yet
Return check  Facility staff · in two weeks · they run it before a Monday booking without a reminder
Cut           The 40-line config file, now one optional flag
```

```
GROWTH CARD · research software engineer · fictional
Started at   "Nobody I can name. Three labs installed it."
             Perspective E · Specificity E · Evidence E · Calibration D · Subtraction E
Got to       "The facility manager, every Monday. I've watched two people use it now."
             Perspective S · Specificity S · Evidence S · Calibration S · Subtraction S
Trace        Calibration fell at the first Watch (rated First value Solid, watched a postdoc give up), then rose.
             Subtraction rose when the config was cut at the first Watch, slipped at the second Break (proposed a dashboard), recovered.
Decisions    Name the user · facility staff over PIs · "PIs never touch the sheet; the facility gets the angry email"
             Watch · cut the config over writing a guide · "a guide is a confession"
             Break · list skipped columns over failing hard · "they still need to book the run"
Calibration  Opening: rated First value Solid, observed Missing · Close: rated medium confidence, stranger-ready met
Next time    Start on Evidence, scaffold level "together". Run the return check before changing anything else.
```

Worth using is not claimed, because nobody has come back yet. The card says so. That is the useful part.
