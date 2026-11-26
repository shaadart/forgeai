# Where ForgeAI lied to me

Each entry: what lied, how it was caught, and which check now stops it. Real runs only.

## 1. The agent invented citation ids (25 Nov, smoke run)
- **Lie:** the agent cited `leave_policy#s6#c1`, which does not exist. It built the id from the heading "## 6.".
- **Caught by:** deterministic checks 3 and 4 failed answers whose text was correct.
- **Now stopped by:** the prompt shows short labels (C1, C2) and code maps them back to chunk ids. An unknown label still fails check 3.

## 2. A healthy judge looked broken (25 Nov, smoke run)
- **Lie:** the canary report said the judge missed a planted claim. It had flagged it, as `contradicted` instead of `unsupported`.
- **Caught by:** reading the judge's raw reply in `llm_calls.jsonl`.
- **Now stopped by:** the planted-claim canary accepts any label other than `supported`, because either one fails the answer.

## 3. The test writer asked "unanswerable" questions the documents answer (25 Nov, smoke run)
- **Lie:** "How many vacation days do part-time employees get?" was filed as must-refuse. The policy answers it in part.
- **Caught by:** a must-refuse case failing although the agent's answer was grounded.
- **Now stopped by:** the answerability gate rejects `partial` as well as `supported`.

## 4. The judge graded a question as a false fact (25 Nov, smoke run)
- **Lie:** a correct clarifying question was labelled an `unsupported` claim, so the case failed as a hallucination and the loop spent both refits on it.
- **Caught by:** the evidence column quoted the agent's question as the unsupported claim.
- **Now stopped by:** code drops any claim that ends in a question mark.

## 5. Correct refusals came back "unknown" (25 Nov, smoke run)
- **Lie:** the two judge passes "disagreed" on refusals. Only `asks_clarification` differed, set off by "try rephrasing", and a refusal's verdict never reads it.
- **Caught by:** comparing the two raw judge replies.
- **Now stopped by:** the disagreement check compares only the labels the pass rule uses for that case.

## 6. The report blamed overfitting when nothing had been fitted (25 Nov, smoke run)
- **Lie:** "the refits likely overfitted", with no refit kept.
- **Caught by:** reading the certificate next to the refit log.
- **Now stopped by:** the warning names chance or an uneven split when no refit was accepted.

## 7. The judge accepted arithmetic the agent made up (25 Nov, smoke run, not a defect in the checks)
- **Lie:** asked about leave after a parent dies, the agent added 5 days and 2 days and answered "7 days". The judge accepted it.
- **Caught by:** deterministic check 5: 7 appears in no context. The case is counted `unknown`, not passed.
- **Now stopped by:** the same check. It stays out of the pass count.

## 8. An unconfirmed default refused the topic the brief asked for (25 Nov, MLC run)
- **Lie:** the interviewer asked whether to refuse the Maritime Labour Convention because the crew handbook did not mention it. The Convention itself was in the folder. Nobody answered, so the default "Yes, refuse" became a requirement and the agent was told to refuse it.
- **Caught by:** the answerability gate rejected 17 must-refuse cases because the documents answered them, and half of the agent's replies were refusals.
- **Now stopped by:** a refusal nobody confirmed, about something the brief asks about, moves back to must-answer, where the documents decide. Exclusions written in the brief or chosen by a person stay. The overrule is printed as an assumption.
- **The first fix lied too:** it only matched refusals worded exactly like the brief. A later model wrote "General MLC complaints" and "Wage calculations (unless company policy referenced)", which slipped through.

## 9. The generator's work was silently replaced by a template (25 Nov, MLC run)
- **Lie:** the agent on disk looked generated. The model's second reply was valid but sent each prompt section as a list, so code rejected it and used the template.
- **Caught by:** `generator_log.json` and the raw reply in `llm_calls.jsonl`.
- **Now stopped by:** lists of rules are accepted and joined. A template fallback is still logged as a generator defect.

## 10. The generator wrote a made-up rule into the agent's instructions (25 Nov, MLC run)
- **Lie:** the citation rules gave an example, \"Seafarers shall have at least 102 hours of rest in every 7-day period\", which is in no document. An agent could repeat it.
- **Caught by:** reading `agent.v0.yaml` before the evals ran.
- **Now stopped by:** code removes any generated rule that states a number the requirements never mention, and logs it as a generator defect.

## 11. The sealed set never tested refusals (25 Nov, MLC run)
- **Lie:** the held-out score would have covered 6 plain answerable questions only. Every refusal, ambiguous and cross-document case had fallen into train.
- **Caught by:** counting categories per side in `evalset.jsonl`.
- **Now stopped by:** a group is sealed whenever that moves each category toward one third, with mixed groups placed first. The same eval set now splits 18 train and 12 sealed, with all categories on both sides.

## 12. A made-up part number refused four good topics (25 Nov, spares run)
- **Lie:** the requirements writer gave part `P12345` in its example questions. No such part exists. The groundability check searched for it, found nothing and reported that the catalogue did not cover finding parts, suppliers, minimum quantities or totals. The run stopped as "not groundable".
- **Caught by:** reading `requirements.json` next to `groundability.json`.
- **Now stopped by:** code replaces an identifier found in no document with a real one from the catalogue.

## 13. "The catalogue lists only one supplier" (25 Nov, spares run)
- **Lie:** the checker saw the 8 nearest rows, all from one supplier, and reported that no comparison was possible. The catalogue has two suppliers.
- **Caught by:** counting suppliers in `catalogue.csv`.
- **Now stopped by:** the groundability check adds a row for each other value of a short column.

## 14. The row that was asked for did not come back (25 Nov, spares run)
- **Lie:** asked about part `N-BP200-010-OE`, the checker reported it "is not listed". It is row 1. Near-identical rows pushed it to rank 15.
- **Caught by:** ranking the exact row for the failing question.
- **Now stopped by:** a rare part code in the question puts its chunk first.

## 15. The made-up part number came back as a plain number (25 Nov, Colab spares run)
- **Lie:** a second model asked about "the 1234 engine" and "the 5678 pump". Neither exists. Four of six topics were reported as not covered, and the run stopped again.
- **Caught by:** reading `requirements.json` from the stopped run. The fix for entry 12 only matched codes with letters.
- **Now stopped by:** an example question with a number of four or more digits found in no document is replaced by the topic name.

## 16. One self-test failed and the whole score read as 0% (25 Nov, Colab MLC run)
- **Lie:** the report showed 0 passed. The number-swap test had changed "paragraph 6" to "paragraph 7" in a sentence that repeated a correct fact. The judge folded the two into one claim and never saw the number, so every model verdict became unknown.
- **Caught by:** reading the judge's raw reply in `llm_calls.jsonl`.
- **Now stopped by:** the swap changes a number that a key fact states.
- **Still open:** the judge can miss a wrong number inside a sentence that repeats a correct one.

## 17. Correct refusals were graded as made-up claims (26 Nov, Colab MLC run)
- **Lie:** three replies correctly declined. The judge listed "The assistant cannot help with wages" as a claim, found no document stating it, and all three cases failed as hallucinations.
- **Caught by:** reading the failed cases next to the agent's replies.
- **Now stopped by:** code drops claims that describe the reply itself, as the judge prompt already asks.

## 18. Citing two sources counted as citing none (26 Nov, Colab runs)
- **Lie:** the judge supported a claim with evidence "E1, E5". Code knew no item of that name and changed the claim to unsupported. On the spares run this failed the padding self-test, so no model verdict counted.
- **Caught by:** reading the raw judge replies in `llm_calls.jsonl`.
- **Now stopped by:** a citation naming several real items counts. A citation naming an unknown item still fails.

## 19. The report writer said five of six self-tests failed (25 Nov, Colab MLC run)
- **Lie:** the written summary said "5 out of 6 canaries failed". Five had passed.
- **Caught by:** the rule that the writer may not type numbers. Its text was rejected twice.
- **Now stopped by:** the same rule. The report falls back to the template filled by code.

## 20. The fix for made-up part numbers produced nonsense questions (26 Nov, Colab spares run)
- **Lie:** code swapped each invented number for the first real part, a ballast pump seal. The checker was then asked about "the N-BP200-010-OE engine spares from Gulfstream" and about its total cost, answered "unsupported", and the run stopped.
- **Caught by:** reading the checker's questions in `llm_calls.jsonl`.
- **Now stopped by:** the intake model is shown real sample rows. If it still invents an identifier, code asks about the columns of one real row.
- **Still open:** that replacement question is easy to support, so for such a topic the load line is weaker.

## 21. "No chunk states the total" (26 Nov, Colab spares run)
- **Lie:** the checker reported order totals as not covered because no document states the cost of 10 units. The unit price was in the chunks it was given, and the agent has a calculator.
- **Caught by:** reading the checker's reply next to its chunks.
- **Now stopped by:** for a topic that needs arithmetic, the checker is told a calculator exists and only the input numbers are needed. The quote check still applies.

## 22. "The chunks do not provide the unit prices" (26 Nov, Colab spares run)
- **Lie:** asked for the price and lead time of a mechanical seal, and for the cost of seals and impellers, the checker reported both as not covered. The rows it was given listed those items with `unit_price` and `lead_time_days`. The run stopped again.
- **Caught by:** reading the checker's reply next to its chunks.
- **Now stopped by:** for a topic that needs table lookup or arithmetic, a retrieved row listing an item the question names overrules "unsupported". The overrule is written to `groundability.json` and flagged.
- **Still open:** the rule proves the item is listed, not that every column the user needs is there.

## 23. "No chunk states the monthly wage" (26 Nov, MLC run)
- **Lie:** the checker marked "Wages" as unsupported, so the agent was told to refuse it. The Convention has Regulation 2.2, Wages. The checker's example question asked for one person's monthly figure.
- **Caught by:** reading `groundability.json` while writing the README.
- **Still open:** nothing stops this yet. The topic is listed as demoted in the report.

## 24. A teaching example ended up in the agent's instructions (26 Nov, spares run)
- **Lie:** the spares agent is told to keep conditions "such as 'unless another member has reserved them'", a sentence from the library example inside the factory's own prompt.
- **Caught by:** reading `agent.final.yaml`.
- **Still open:** no check rejects text copied from a prompt example.

## 25. A calculator for a question-and-answer brief (26 Nov, tool selection test)
- **Lie:** for a crew-rights brief with nothing to compute, the intake model tagged a topic as arithmetic and the agent got a calculator.
- **Caught by:** `tests/test_tool_selection.py` with the Mistral builder.
- **Now stopped by:** the arithmetic tag is dropped unless the brief asks for totals, calculations or similar.
- **Still open:** a brief that needs sums but words it differently would get no calculator.

## 26. What an untuned third brief exposed (26 Nov, HR trial)
I wrote a new brief and three small synthetic documents and ran the factory once, with no code change (sealed 14 of 18; the run is not committed).
- **Lie:** "The documents do not cover travel expense limits." The checker's example question was about train tickets. The policy does state flight classes and a meal limit, so the agent refused a question about premium economy that its documents answer. Same pattern as 23.
- **Lie:** the eval set looks like 18 sealed questions. Four of them are one "how many leave days" question reworded, and two more repeat two others, so the score rests on fewer distinct questions.
- **Lie:** a correct answer about who approves a large claim was failed for not also naming who approves small ones.
- **Lie:** code removed the whole "cite every fact" rule from the prompt because its example held a number. The output contract still asks for citations.
- **Caught by:** reading the failed cases, `requirements.final.json` and `generator_log.json`.
- **Still open:** all four.
