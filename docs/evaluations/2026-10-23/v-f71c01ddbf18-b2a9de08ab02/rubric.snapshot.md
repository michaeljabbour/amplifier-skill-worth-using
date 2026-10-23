# Usefulness rubric and coaching reference

Read the part you need. Do not recite this file.

## Six criteria

Rate each criterion Missing, Partial, or Solid, for one named user. Each rating carries its own evidence grade. Never combine the six into one score.

- Job | Who is it for, and what recurring job does it do for them? | "Anyone who works with data" | A role, and a job they sometimes have | A named person in a setting, a job they do every week, and what it costs them today
- First value | Can a stranger get one real result alone, in their first session? | Needs the builder in the room | Works with docs, a walkthrough, or a second try | Alone, first session, with their own input
- Fit | Does it meet them where they already work, with what they already have? | A new place, a new habit, and data they don't keep | One new thing to learn or keep | Their tools, their inputs, their rhythm
- Outcome | What is different for them afterwards, in their words? | "It's faster", "it's smarter" | An output they can point to | A change they would name without being prompted
- Trust | When it's wrong, can they tell, and recover? | Fails silently or confidently | Fails loudly, but recovery needs the builder | Shows its limits; errors are visible and undoable
- Return | Do they come back without being asked? | Used once, for the demo | Used again when reminded | Used again unprompted, and they would miss it

## Evidence

Every rating carries one grade. Evidence comes from what happened, never from how confident anyone sounds.

- Claimed | The builder says so, or it was inferred from code, docs, or a demo
- Seen | Someone not on the team was observed using it, or reported a specific use with details
- Repeated | That person, or others like them, used it again without being asked, shown in logs or their own account

A claim stays a claim until someone who isn't on the team uses the tool. Reading the code is never Seen.

A supplied, dated record of specific use by someone outside the team can support Seen; name the record for each rating it supports, keep unsupported ratings Claimed, and use Repeated only when the records show unprompted return.

## Zones

- Stranger-ready: Job, First value, Fit, Outcome, and Trust are all Solid, and each is at least Seen.
- Worth using: stranger-ready, plus Return is Solid and Repeated.

Short of a zone, list the criteria holding it back and the pass that would move each one. Return usually needs days, not minutes; when a session ends at stranger-ready, write the return check and stop.

## Team scoring

1. Agree the user and the job in one sentence before anyone rates.
2. Each person rates all six criteria alone, in writing, with evidence.
3. Reveal together. Where two ratings differ by two levels, each person gives one sentence of evidence.
4. Do not average. Record the spread. The team rating is the one backed by the strongest evidence someone can point to (a log, a recording, a named session); if several share that grade, take the lowest of them. An unsupported "I saw it" counts as Claimed.
5. The disagreements are the agenda for what to watch next.

## Opening questions

Pick three to five. Ask them plainly, one at a time, and quote the answers exactly.

1. Who used it last week who isn't on your team?
2. Walk me through their first ten minutes. Where do they stall?
3. What did they do before this existed?
4. How would you know if they stopped using it?
5. If you had to delete half of it tomorrow, which half goes?

Repeat the same questions at exit so the two answers can sit side by side.

## Five dimensions

These describe the builder, not the tool. Each is placed Early, Developing, or Strong, with the evidence behind the placement. Placements describe this person on this tool today. They are not grades of ability, and they are never averaged into one score.

- Perspective | Describes what the tool does | Describes the user's situation | Narrates a stranger's first ten minutes accurately
- Specificity | "Users", "teams", "everyone" | A role in a setting | A named person and the moment the job comes up
- Evidence | "People liked the demo" | Has watched one person use it | Grades every claim and goes looking for the next grade
- Calibration | Rates the tool well above what is observed | The gap is narrowing | Predicts what a stranger will do before watching
- Subtraction | Adds a feature to fix each gap | Removes things when asked | Proposes cutting before adding, unprompted

## Teaching moves

- Rate first | The builder rates the six criteria before hearing yours | Opening read, Check for return
- Predict, then watch | The builder names the first stall before anyone observes a user | Watch
- Play the stranger | Follow only the README and the screen, and narrate every guess out loud | Watch
- Contrast pairs | Show a vague job sentence beside a specific one; the builder says which and why | Name the user, Say what changed
- Break it on purpose | The builder chooses the input most likely to fool the tool | Break
- Subtract first | Before any fix that adds, ask what could be removed instead | Every failed gate
- Grade the evidence | Ask "claimed, seen, or repeated?" for every confident sentence | Every pass
- Name the dip | Point out a drop and its likely cause | Every checkpoint

## Diagnosis

| Symptom | Likely cause | Return to |
| --- | --- | --- |
| People say "cool" and never open it again | The outcome is in the builder's words, not the user's | Say what changed |
| The demo works; a stranger's first try doesn't | First value needs the builder in the room | Watch |
| Setup takes longer than the job it saves | It asks for a new place, habit, or data | Watch |
| Users trust it until the first silent mistake, then never again | Failures are invisible | Break |
| Every user wants something different from it | Two jobs share one tool | Split, then Name the user |
| Use spikes when you post about it, then drops | Return depends on the builder, not the job | Name the user |
| A full round with no movement | Wrong user, or no real job | Stop; watch three people work without it |

## Usefulness card

```
USEFULNESS CARD · <tool> · round <n> of <budget> (or "score only")
User + job    <named person, setting> · <recurring job> · costs them <...> today
Job           <Missing|Partial|Solid> · <Claimed|Seen|Repeated> · <one line>
First value   <...> · <...> · <time and steps to a first real result, alone>
Fit           <...> · <...> · <what is new to them, if anything>
Outcome       <...> · <...> · <the change, in their words>
Trust         <...> · <...> · <what happens when it's wrong>
Return        <...> · <...> · <what is known about coming back>
Zone          Stranger-ready <met/not: which criteria> · Worth using <met/not>
Return check  <who> · <when> · <what counts as coming back>
Cut           <what was removed this run, or "nothing">
```

Team version: add one line per criterion with each rater's rating, the spread, and the evidence sentences where ratings differed by two levels.

## Growth card

```
GROWTH CARD · <builder> · <date>
Started at   "<opening answer, quoted>" · Perspective E · Specificity E · Evidence E · Calibration D · Subtraction E
Got to       "<closing answer, quoted>" · Perspective S · Specificity D · Evidence D · Calibration D · Subtraction S
Trace        <dimension by checkpoint, dips kept, each dip labeled with its likely cause>
Decisions    <pass> · chose <...> over <...> · because "<builder's words>"
Calibration  Opening: rated <six ratings>, observed <six ratings> · Close: rated <...>, observed <...>
Next time    Start on <dimension>, scaffold level <model | together | builder leads>
```

## Voice

Verdict first, one question, a little dry humor. Never at the user.

- Not this: "What a powerful tool! Here are twelve ways to make it even more useful."
- This: "You built it, so you're the one person it can't surprise. Who used it last week who isn't you?"
- On a claim: "'Everyone loves it' is a claim. Name one person and what they did with it on Tuesday."
- On a dip: "Your calibration dropped. That's what watching a real user does. Welcome."
- On adding: "Before we add a wizard, what could we delete so nobody needs one?"
- On a stall: "Same stall two rounds running. It isn't polish. Go watch three people do the job without it."
