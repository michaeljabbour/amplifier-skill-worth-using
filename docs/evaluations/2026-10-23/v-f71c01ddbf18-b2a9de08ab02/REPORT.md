# Worth Using: live pilot and full-run budget

**The pilot is blocked before any live call. No skill effect, provider setting support, token usage, latency or dollar cost has been measured.** The requested model configuration is incomplete; there is no pilot-based full-run cost projection. This is an unrun test, not a null result.

Source commit: `8a3a3ac5c26b007d592c0f423f74b52c157e00e9`. Record status: `blocked_before_live_pilot`.

## Provider-returned models and accepted requests

Successful requests establish that the provider accepted the submitted payload. Temperature and token limits below are recorded request settings; these APIs do not echo their effective server settings. A seed parameter is best effort where accepted. Anthropic receives no seed parameter.

| Role | Requested model | Exact returned model ID(s) | Successful / failed calls | Sent temperature | Sent max output tokens |
| --- | --- | --- | --- | --- | --- |
| eval | UNSET | None returned | 0 / 0 | Unvalidated | Unvalidated |
| judge | UNSET | None returned | 0 / 0 | Unvalidated | Unvalidated |
| simulator | UNSET | None returned | 0 / 0 | Unvalidated | Unvalidated |

Requested settings and exact requested/sent seeds are in `scores/pilot_accepted_settings.json`; each successful call retains its exact returned ID in `pilot/live/calls.jsonl`. The simulator keeps its default model selection from EVAL_MODEL.

## Token cost per conversation

Tokens and seconds are sums of actual returned usage across assistant turns. Judge reviews are shown separately; shared simulator generation and script audits appear in the next table. Empty values mean unavailable. Dollar estimates require configured rates or sourced `pilot/pricing.json` prices for the exact returned models.

| Conversation | Agent input / output tokens | Agent seconds | Agent USD | Judge input / output tokens | Judge USD |
| --- | --- | --- | --- | --- | --- |
| No live conversations | Not measured | Not measured | Unavailable | Not measured | Unavailable |

## All pilot resource use

| Condition | Role / purpose | Calls attempted / complete / error | Input tokens | Output tokens | Seconds | Estimated USD |
| --- | --- | --- | --- | --- | --- | --- |
| No live calls | None | 0 / 0 / 0 | Not measured | Not measured | Not measured | Unavailable |

## Full-run projection and approval stop

The planned full evaluation is **324 development conversations plus 108 private held-out conversations = 432**, with 864 blind judgments, 48 simulator scripts and 48 judge script audits. The 18-conversation pilot is separate. Each Coach conversation can require 1–12 evaluated-agent calls, so 432 conversations are not 432 API calls.

The current main runner still accepts only the 12 development fixtures. Private input loading and separate held-out analysis must be integrated before the approved full run. Private fixture text, keys, blinded packets and transcripts can reveal the holdout and must stay out of the public PR.

**Projected tokens, seconds and dollars: unavailable until a complete live pilot.** No placeholder price or synthetic usage estimate is substituted.

The full run remains stopped until the user has reviewed the pilot and cost projection. A passing pilot does not authorize the full run.

## Errors and limitations

- preflight: EVAL_MODEL is unset
- preflight: OPENAI_API_KEY is unset
- preflight: JUDGE_MODEL is unset
- preflight: SIMULATOR_MODEL is unset (defaults to EVAL_MODEL)
- preflight: EVAL_MODEL_FAMILY is unset; declare the actual model family explicitly
- preflight: JUDGE_MODEL_FAMILY is unset; declare the actual model family explicitly

Coach turn caps, if reached, remain censoring rather than successful stopping. The simulator is an LLM-generated fixed script replayed across conditions, not an adaptive conversation. Repeated reviews by one OpenAI judge measure that judge's consistency, not independent-judge agreement. All pilot dossiers are fictional development cases.

## Full-run interpretation safeguards

The headline unsupported-evidence-upgrade metric must appear beside final rating coverage, evidence-classification coverage and evidence reference-grade agreement. Omitting ratings cannot count as an honesty win. Public development results and private held-out results will be separate; a headline gain must also hold on the four held-out fixtures. Null or negative comparisons are reported plainly. No real-world tool usefulness claim follows from these exercises.

No efficacy effect sizes, confidence intervals or five illustrative efficacy excerpts are supplied for this pilot. The five final excerpts must be selected from real full-run transcripts. Private excerpts require a disclosure decision because they can reveal held-out scenarios. Real tools and real usage logs are a later, separate cohort.

## Reproduce this pilot

```bash
python3 evals/run.py --conditions skill,baseline --seeds 1 --pilot
```

Model IDs and credentials come only from environment variables; do not put API keys in files or transcripts. The placebo is automatically added to the requested two conditions. See the frozen source and protocol files beside this report.
