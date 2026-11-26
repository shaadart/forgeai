# Certificate: Maritime Labour Assistant, issued with 13 conditions of class

> The prose writer failed or was skipped; this report is the plain code-rendered template.

| | Baseline (v0) | Final |
|---|---|---|
| Train | 9 passed, 4 failed, 4 unknown (69%) | 9 passed, 4 failed, 4 unknown (69%) |
| Sealed | 7 passed, 3 failed, 2 unknown (70%) | 7 passed, 3 failed, 2 unknown (70%), 95% interval 40% to 89% |

Noise floor: 3 cases flip between identical runs; a refit is kept only if its gain is larger than 3.
Refits: 0 accepted, 3 rejected.
A full run is 336 model calls and 827485 tokens (budget 8000000), 15925.5 seconds of model time.

## Conditions of class: what still fails

| Case | Split | Category | Question | Evidence | Why still open |
|---|---|---|---|---|---|
| T03 | train | judge_uncertain | Does the Maritime Labour Convention, 2006 apply to all types of ships? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |
| T04 | train | judge_uncertain | What are the key points regarding on-board complaint procedures for seafarers under this regulation? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |
| T06 | train | hallucination | Can a ship's crew member be punished for complaining about poor working conditions? | check 2: expected to refuse, status was answered | Refit 1 targeted it and did not beat the noise floor. |
| T08 | train | prompt_defect | What procedures should recruitment agencies follow for dealing with incompetence or indiscipline? | check 4: quote not found in mlc_2006_consolidated_2022#p26.2#c1: '(h) procedures which are in accordance with the principles of natural justice fo' | Refit 2 targeted it and did not beat the noise floor. |
| T10 | train | judge_uncertain | What are the conditions under which seafarers can be repatriated according to the MLC 2006? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |
| T11 | train | retrieval_miss | What costs must the shipowner cover during seafarers' repatriation according to the MLC 2006? | check 4: quote not found in mlc_2006_consolidated_2022#p40.1#c1: 'all expenses reasonably incurred by the seafarer, including the cost of repatria' | Refit 3 targeted it and did not beat the noise floor. |
| T15 | train | hallucination | What are the rules for splitting the rest periods and what happens if rest is lost due to an emergency? | unsupported claim: The interval between consecutive periods of rest shall not exceed 14 hours. | Refit 1 targeted it and did not beat the noise floor. |
| T16 | train | judge_uncertain | What does 'able seafarer' mean in this context? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |
| S02 | sealed | hallucination | What are the minimum wages for seafarers under the Maritime Labour Convention, 2006? | check 2: expected to refuse, status was answered | Sealed case: never shown to the fixer. |
| S03 | sealed | hallucination | Can seafarers refuse to work in conditions that do not comply with the Maritime Labour Convention, 2006, and what are the implications? | check 2: expected to refuse, status was answered | Sealed case: never shown to the fixer. |
| S04 | sealed | retrieval_miss | What are the main obligations of the competent authority regarding seafarer recruitment and placement services? | missing key fact: The competent authority should consider promoting effective cooperation among seafarer recruitment and placement services.; missing key fact: Consideration should be given to encouraging international cooperation between Members and relevant organizations. | Sealed case: never shown to the fixer. |
| S05 | sealed | judge_uncertain | What are the main responsibilities of the Designated Person Ashore (DPA) according to the crew handbook, and how do they relate to the safety and health regulations mentioned in the MLC 2006? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |
| S06 | sealed | judge_uncertain | What are the responsibilities of the Master and the crewing officer ashore, and how does the Designated Person Ashore handle complaints that cannot be resolved on board? | the two judge passes disagree | The judge could not decide, so it was never sent to the fixer. |

## Refit log

- Refit 1 tried to stop the agent stating things the documents do not say. Train passes went from 9 to 7: not a bigger gain than the noise, so I put it back.
- Refit 2 tried to stop the agent mishandling text it had found. Train passes went from 9 to 9: not a bigger gain than the noise, so I put it back.
- Refit 3 tried to stop the agent not finding the right passage. Train passes went from 9 to 11: not a bigger gain than the noise, so I put it back.

## What I doubt about this run

- Judge: canaries passed 6 of 6; shuffle disagreement 6 of 29; number-check disagreement 0 of 29.
- Classifier disagreed with the code tree on 0 of 12 diagnoses.
- Eval set: 10 of 39 generated cases rejected; 6 kept questions copy 5+ words from their source.
- Memorizable cases: 0%. Sealed without them: 7 passed, 3 failed, 2 unknown (70%).
- Assumptions made without the requester: If the two fee sources disagree, both values are shown. Nobody confirmed this. The company's crew policies are in company_crew_handbook.docx. Nobody confirmed this. Overruled by code: nobody confirmed refusing 'Implementation of the Maritime Labour Convention, 2006', and the brief asks about it, so the documents decide (see the groundability table). Overruled by code: nobody confirmed refusing 'Company crew policies', and the brief asks about it, so the documents decide (see the groundability table).
- Topics refused because the documents cannot support them: Wages, Implementation of the Maritime Labour Convention, 2006.
- Documents not read: none.
- Tools attached but never called: none.
- Generator defects fixed by code: dropped tool csv_lookup: no supported topic needs it, or nothing for it to read; dropped tool calculator: no supported topic needs it, or nothing for it to read; dropped tool date: no supported topic needs it, or nothing for it to read.
- Model replies that broke their contract twice, by stage: {'agent': 1, 'report': 1}.
- The eval set was written by a small model, so it covers the questions a small model thinks to ask.
- The counterfactual puts the gold chunk first, the best case, so it can overstate how fixable a miss is.
- Questions meant to be refused that the documents answer: What is the minimum number of days off a seafarer should get per month according to the Maritime Labour Convention, 2006?; Can a seafarer waive their right to minimum annual leave with pay?; Can seafarers be placed in positions that require different qualifications than those they possess?; How should the shipowner handle the repatriation of a seafarer who is ill and requires medical treatment?
