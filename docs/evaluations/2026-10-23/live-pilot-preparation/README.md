# Live pilot preparation for Worth Using 0.1.2

The live pilot is blocked until the requested model IDs and API-key environment variables are available to the execution process. No evaluated-agent, simulator, or judge calls had been made when this preparation note was written. This is not a null or negative result.

The treatment is the exact skill and rubric from `8a3a3ac5c26b007d592c0f423f74b52c157e00e9`. The pilot command is:

```bash
python3 evals/run.py --conditions skill,baseline --seeds 1 --pilot
```

The effective conditions include the required placebo. The pilot has two public development fixtures, one seed, three conditions, and three tasks: 18 conversations. The user has authorized this pilot, with an explicit stop for a measured full-run cost projection before any full execution. The requested roles are Claude for evaluation, OpenAI for judging, and the unchanged simulator default.

The selected [pilot record](../v-f71c01ddbf18-b2a9de08ab02/REPORT.md) records exit code 2 at environment preflight, with zero live API requests. The [private freeze commitment](PRIVATE_HOLDOUT_COMMITMENT.json) was verified before any evaluation-model output existed.

## Measurement and remaining work

The pilot report must use its actual `pilot/live/` records. It must distinguish requested settings from request-level acceptance and server-echoed values, include per-conversation usage and auxiliary calls, and preserve missing usage as unknown. A rejected request cannot demonstrate setting support. Two calls to one judge measure repeated-judge consistency, not independent-judge agreement.

The twelve public fixtures are development cases. The four new private fictional cases, their keys, team submissions, and eventual private transcripts stay outside the public repository. Only a content commitment and aggregate results belong in this PR. [The held-out addendum](HELDOUT_PROTOCOL.md) defines the proposed claim safeguards and lists the implementation required before a full run. Its floors are premeasurement design choices and are not observed results.

The expanded full comparison is 324 development conversations plus 108 held-out conversations, with 864 transcript reviews, 48 simulator generations, and 48 script audits before retries. Pilot calls are additional. Multi-turn Coach conversations make HTTP-call counts larger than conversation counts. A dollar projection requires actual pilot usage and verified prices for the configured model IDs; no estimate is supplied from invented models or usage.

## Source observation outside the treatment

The opening stage in `recipes/worth-using-round.yaml` now permits named, dated outside-use records. The later scoring stage still says, “Use Seen only for what the builder reports a real person outside the team doing; everything else is Claimed.” That remaining restriction is outside the two-file treatment used in this experiment. The recipe, skill, rubric, and site are unchanged by this preparation.

## Follow-up boundary

After a full fictional run, add two or three actual tools only with authentic, authorized session records and usage logs. Report that cohort separately. No real tools or real usage observations have been supplied for this record.
