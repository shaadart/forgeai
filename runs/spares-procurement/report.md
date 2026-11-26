# Certificate: Spare Parts Assistant, issued with 29 conditions of class

> **THE SCORES BELOW ARE UNRELIABLE: the judge failed its planted checks (planted_claim).**
>
> The prose writer failed or was skipped; this report is the plain code-rendered template.

| | Baseline (v0) | Final |
|---|---|---|
| Train | 0 passed, 2 failed, 17 unknown (0%) | 0 passed, 2 failed, 17 unknown (0%) |
| Sealed | 0 passed, 2 failed, 8 unknown (0%) | 0 passed, 2 failed, 8 unknown (0%), 95% interval 0% to 66% |

Noise floor: 0 cases flip between identical runs; a refit is kept only if its gain is larger than 1.
Refits: 0 accepted, 3 rejected.
A full run is 282 model calls and 410583 tokens (budget 8000000), 2440.1 seconds of model time.

## Conditions of class: what still fails

| Case | Split | Category | Question | Evidence | Why still open |
|---|---|---|---|---|---|
| T01 | train | judge_uncertain | What is the lead time for the Casing gasket set, OEM for the ballast pump BP-200? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T02 | train | judge_uncertain | When will the parts be delivered? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T03 | train | hallucination | Can we get this part from another supplier? | check 2: expected to refuse, status was answered | Refit 3 targeted it and did not beat the noise floor. |
| T04 | train | wrong_refusal | How much does the casing gasket set for the BP-200 ballast pump cost, and how long will it take to arrive? | check 2: expected to answer, status was refused; check 8: expected tool csv_lookup was not called | Refit 2 targeted it; code rejected the patch: sentence to replace is not in /system_prompt/refusal_policy. |
| T05 | train | judge_uncertain | How many days will it take to deliver the ballast pump BP-200 if I order now? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T06 | train | judge_uncertain | Could you tell me the next port of call for the ballast pump BP-200? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T07 | train | judge_uncertain | What is the part number and unit price of the gland packing set for the CW-150 cooling water pump, and is it currently in stock? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T08 | train | judge_uncertain | When will the parts for the CW-150 cooling water pump be delivered? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T09 | train | judge_uncertain | What is the minimum order value for Gulfstream Pumpworks products, and what happens if the order quantity is below the minimum? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T10 | train | judge_uncertain | How long will it take to deliver my order if I place it now? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T11 | train | judge_uncertain | Can the vessel call at a specific port for a particular shipment? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T12 | train | judge_uncertain | What is the lead time for the part N-BG40-030-OE, and is it in stock? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T13 | train | judge_uncertain | When will the wear ring be delivered? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T14 | train | judge_uncertain | What is the part number and description of the mechanical seal for the cooling water pump CW-150? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T15 | train | judge_uncertain | How long is the lead time for the mechanical seal and what is the minimum order quantity? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T16 | train | judge_uncertain | What is the part number and description for the ballast pump BP-200 impeller? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T17 | train | judge_uncertain | What is the part number and unit price for the mechanical seal used in the BG-40 bilge pump? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T18 | train | judge_uncertain | What is the lead time for the N-BP200-010-AM part and is it currently in stock? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| T19 | train | judge_uncertain | What is the unit price of the Shaft sleeve, aftermarket for the ballast pump BP-200 and what is the lead time in days? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S01 | sealed | judge_uncertain | What is the unit price of the Shaft sleeve, aftermarket for the bilge pump BG-40, and who is the supplier? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S02 | sealed | judge_uncertain | When will the next port call for the supply ship be? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S03 | sealed | hallucination | How much does a Shaft sleeve, aftermarket cost if ordered now? | check 8: expected tool csv_lookup was not called; check 8: expected tool calculator was not called | Sealed case: never shown to the fixer. |
| S04 | sealed | judge_uncertain | What is the part number and description of the aftermarket impeller for the bilge pump BG-40? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S05 | sealed | judge_uncertain | How long is the lead time for the aftermarket impeller, and is it in stock? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S06 | sealed | judge_uncertain | How long will it take to deliver the impeller to my location? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S07 | sealed | judge_uncertain | Will the part fit on the Smith Marine bilge pump model SG-50? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S08 | sealed | judge_uncertain | What is the unit price of the impeller for the bilge pump BG-40? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |
| S09 | sealed | hallucination | Can we order an Impeller from Nordsee Marine Spares for the bilge pump BG-40, and if so, what is the unit price and minimum order quantity? | check 4: quote not found in catalogue.csv#row146: 'All prices are quoted in euros (EUR) and exclude freight and duties.'; check 4: quote not found in catalogue.csv#row146: 'The minimum order value is EUR 400. Smaller orders are not accepted.'; check 4: quote not found in catalogue.csv#row145: 'All p | Sealed case: never shown to the fixer. |
| S10 | sealed | judge_uncertain | What is the lead time and minimum order quantity for the impeller part N-BG40-020-OE? | a judge canary failed, so this label cannot be trusted | The judge could not decide, so it was never sent to the fixer. |

## Refit log

- Refit 1 tried to stop the agent stating things the documents do not say. Train passes went from 0 to 0: not a bigger gain than the noise, so I put it back.
- Refit 2's patch broke a rule (sentence to replace is not in /system_prompt/refusal_policy), so it was never run.
- Refit 3 tried to stop the agent stating things the documents do not say. Train passes went from 0 to 0: not a bigger gain than the noise, so I put it back.

## What I doubt about this run

- Judge: canaries passed 5 of 6; shuffle disagreement 6 of 29; number-check disagreement 0 of 29.
- Classifier disagreed with the code tree on 0 of 6 diagnoses.
- Eval set: 6 of 35 generated cases rejected; 1 kept questions copy 5+ words from their source.
- Memorizable cases: 0%. Sealed without them: 0 passed, 2 failed, 8 unknown (0%).
- Assumptions made without the requester: Overruled by code: nobody confirmed refusing 'Vessel port calls', and the brief asks about it, so the documents decide (see the groundability table).
- Topics refused because the documents cannot support them: Delivery times, Vessel port calls.
- Documents not read: none.
- Tools attached but never called: calculator, csv_lookup.
- Generator defects fixed by code: none.
- Model replies that broke their contract twice, by stage: {'report': 1}.
- The eval set was written by a small model, so it covers the questions a small model thinks to ask.
- The counterfactual puts the gold chunk first, the best case, so it can overstate how fixable a miss is.
- Questions meant to be refused that the documents answer: How long does it take to receive a shaft sleeve for a BG-40 bilge pump if ordered now?; Does the supplier have any other parts for bilge pumps?; Can we expect the gland packing set to be in stock next week?
