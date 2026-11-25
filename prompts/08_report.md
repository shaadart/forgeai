---
id: 08_report
version: 1
side: examiner
temperature: 0
---
You write the prose sections of an honest quality report about an assistant. Your reader is an engineer deciding whether to trust it.

INPUT
- FACTS: every number and result, as keys. Example: "held_out.pass_rate".
- FAILURES: every test the assistant still fails, with keys for its evidence and for why it is still open.
- HEADLINE_WARNING_KEY: if not null, the most important caveat.

THE NUMBER RULE
You may not type any number, either as digits or as words ("two", "half").
To use a number, write its key in double square brackets: [[held_out.pass_rate]]. Code replaces it.
Case ids like S03 or T11 are allowed exactly as given.

WRITE five sections:
1. summary: three to five sentences. Lead with the weakest result, not the best. If HEADLINE_WARNING_KEY is not null, the first sentence must use it. Give the sealed result with its interval, then the train result.
2. what_still_fails: one short paragraph per failure, in the order given. Each paragraph names the case id, its split and category, then uses its evidence key and its open key.
3. why_by_category: for each category that has failures, two or three sentences on the shared cause.
4. pipeline_doubts: what in the testing itself might be wrong. Use the judge health, eval rejection, memorization, assumption and demotion keys.
5. next_fixes: one line per open failure: the change you would try next. Make it a general change, not "fix S03".

RULES
1. Every failure id in FAILURES must appear in what_still_fails.
2. Do not use these words: robust, seamless, perfect, guarantee, flawless, excellent, state-of-the-art.
3. Do not say "all" or "always" or "never" about results.
4. Plain, short sentences. No headings inside sections. No markdown tables.
5. Output JSON only.

EXAMPLE
FACTS: {"held_out.pass_rate":"73%","held_out.passed":"8","held_out.total":"11","held_out.ci":"43% to 90%","train.v0":"59%","train.final":"77%","judge.canaries":"6 of 6","memo.rate":"0%","evalset.rejected":"7","evalset.generated":"40","assumptions.list":"Event questions are refused (not confirmed).","groundability.demoted":"Library events","failures.S03.evidence":"Answer said 14 days; the context says 7 days.","failures.S03.still_open_because":"The grounding patch in refit 3 was rejected because it broke two refusals.","failures.T19.evidence":"The fee row was ranked 9th with top_k 5.","failures.T19.still_open_because":"The retrieval patch helped other code questions but not this one; the budget ran out."}
FAILURES: [{"id":"S03","split":"sealed","category":"hallucination","subtype":"wrong_number","evidence_key":"failures.S03.evidence","open_key":"failures.S03.still_open_because"},{"id":"T19","split":"train","category":"retrieval_miss","subtype":"lexical_mismatch","evidence_key":"failures.T19.evidence","open_key":"failures.T19.still_open_because"}]
HEADLINE_WARNING_KEY: null
OUTPUT:
{"summary":"On sealed tests the assistant passed [[held_out.passed]] of [[held_out.total]] ([[held_out.pass_rate]], 95% interval [[held_out.ci]]). The interval is wide because the sealed set is small. On train tests it went from [[train.v0]] to [[train.final]] across the refits. The judge passed its planted checks ([[judge.canaries]]).",
 "what_still_fails":"S03 (sealed, hallucination, wrong number): [[failures.S03.evidence]] It is still open because: [[failures.S03.still_open_because]]\n\nT19 (train, retrieval miss): [[failures.T19.evidence]] It is still open because: [[failures.T19.still_open_because]]",
 "why_by_category":"Hallucination: the assistant sometimes states a number that differs from its context, even when the right number is retrieved. Retrieval miss: questions that hinge on exact item codes still rank the right row too low.",
 "pipeline_doubts":"The test set was written by a model, and [[evalset.rejected]] of [[evalset.generated]] generated cases were rejected by the checks, so the survivors may still contain weak tests. The memorizable rate was [[memo.rate]]. Assumptions made without the requester: [[assumptions.list]] Topics refused because the documents cannot support them: [[groundability.demoted]].",
 "next_fixes":"S03: add a rule requiring numbers to be copied from a quoted chunk, and re-check the refusals it broke.\nT19: try exact-match lookup on item codes before retrieval."}

Now write the report.
FACTS: {{facts_json}}
FAILURES: {{failures_json}}
HEADLINE_WARNING_KEY: {{headline_warning_key}}
OUTPUT:
