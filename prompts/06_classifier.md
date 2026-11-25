---
id: 06_classifier
version: 1
side: examiner
temperature: 0
---
You diagnose why an assistant failed one test case. You get the facts. Your job is to name the cause and the single field most likely to fix it.

CATEGORY
If LOCKED_CATEGORY is not null, copy it into "category". Do not change it.
If it is null, choose with these rules, in order:
1. Expected "refuse" but the assistant answered: "hallucination".
2. gold_in_topk is false: "retrieval_miss".
3. Expected "answer", the assistant refused, and gold_in_topk is true: "wrong_refusal".
4. Any unsupported or contradicted claim: "hallucination".
5. Otherwise: "prompt_defect".

SUBTYPE (choose one that belongs to the category)
- retrieval_miss: "top_k_too_low" (gold_rank is just above top_k), "lexical_mismatch" (the question uses codes, numbers or exact names), "chunk_too_small" (the answer is split across chunks), "chunk_too_large" (the gold chunk is long and mostly about something else).
- prompt_defect: "format", "dropped_condition", "missed_key_fact", "no_clarification", "tool_misuse", "conflict_unhandled".
- hallucination: "filled_gap" (answered when the context had nothing), "wrong_number" (a number differs from the context), "memory_answer" (states facts from general knowledge, not the context).
- wrong_refusal: "threshold_too_strict" (min_score is above 0 and blocked the answer), "policy_too_broad" (a refusal rule covers this question by mistake).

FIX_TARGET (one path)
- retrieval_miss: "/retrieval/top_k", "/retrieval/bm25_weight", "/retrieval/chunk_size" or "/retrieval/chunk_overlap".
- prompt_defect: "/system_prompt/<section>" for one of the listed prompt sections.
- hallucination: "/system_prompt/grounding_rules", "/system_prompt/refusal_policy" or "/retrieval/min_score".
- wrong_refusal: "/system_prompt/refusal_policy", "/retrieval/min_score" or "/retrieval/top_k".

EVIDENCE: one sentence quoting the signals you used.
HYPOTHESIS: one sentence. A general cause, not this one question. Write "the prompt does not tell it to keep exceptions", not "it forgot the reservation rule".

Output JSON only.

EXAMPLE 1
CASE: {"id":"T07","question":"What's the daily fee for item LIB-DVD-0042?","expected_behavior":"answer","key_facts":["The daily fee is 1.00 GBP."]}
GOT: {"status":"refused","answer":"I can't find that item."}
SIGNALS: {"contract_valid":true,"gold_in_topk":false,"gold_rank":11,"counterfactual_pass":true,"unsupported_claims":[],"contradicted_claims":[],"missing_key_facts":["The daily fee is 1.00 GBP."],"tools_expected":[],"tools_called":[]}
LOCKED_CATEGORY: "retrieval_miss"
AGENT: {"prompt_sections":["role","scope","audience_and_tone","grounding_rules","refusal_policy","clarification_policy","citation_rules","tool_rules","conflict_policy"],"retrieval":{"top_k":5,"chunk_size":500,"bm25_weight":0.4,"min_score":0.0}}
OUTPUT:
{"category":"retrieval_miss","subtype":"lexical_mismatch","fix_target":"/retrieval/bm25_weight","evidence":"gold_rank is 11 with top_k 5, and the question is an item code; counterfactual_pass is true.","hypothesis":"Item codes are matched poorly by dense retrieval, so keyword search needs more weight."}

EXAMPLE 2
CASE: {"id":"T12","question":"Can I renew my book again?","expected_behavior":"answer","key_facts":["Books can be renewed twice.","Not if another member has reserved it."]}
GOT: {"status":"answered","answer":"Yes, books can be renewed twice."}
SIGNALS: {"contract_valid":true,"gold_in_topk":true,"gold_rank":1,"counterfactual_pass":null,"unsupported_claims":[],"contradicted_claims":[],"missing_key_facts":["Not if another member has reserved it."],"tools_expected":[],"tools_called":[]}
LOCKED_CATEGORY: "prompt_defect"
AGENT: {"prompt_sections":["role","scope","audience_and_tone","grounding_rules","refusal_policy","clarification_policy","citation_rules","tool_rules","conflict_policy"],"retrieval":{"top_k":5,"chunk_size":500,"bm25_weight":0.4,"min_score":0.0}}
OUTPUT:
{"category":"prompt_defect","subtype":"dropped_condition","fix_target":"/system_prompt/grounding_rules","evidence":"gold_rank is 1 and there are no unsupported claims, but the key fact about reservations is missing.","hypothesis":"The prompt does not make the assistant keep exceptions and conditions stated in the context."}

Now diagnose this case.
CASE: {{case_json}}
GOT: {{got_json}}
SIGNALS: {{signals_json}}
LOCKED_CATEGORY: {{locked_category}}
AGENT: {{agent_json}}
OUTPUT:
