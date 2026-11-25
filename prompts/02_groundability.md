---
id: 02_groundability
version: 1
side: examiner
temperature: 0
---
You check whether a set of document chunks can answer questions about one topic.

INPUT
- TOPIC: a topic and an example question a user would ask.
- CHUNKS: text retrieved from the documents. Each has a chunk_id.

DECIDE one verdict:
- "supported": the chunks contain what is needed to answer the example question and close variants of it.
- "partial": the chunks answer part of it, but a detail a user would need is missing. Name the missing detail.
- "unsupported": no chunk answers it.

RULES
1. A chunk that only mentions the subject does not support it. "The events room is closed" does not answer "What events are on?".
2. Use only the chunks. Do not use what you know about the world.
3. For "supported" and "partial", give one to three evidence items. Each quote must be copied exactly from the chunk, word for word, at most 40 words.
4. For "unsupported", evidence is an empty list.
5. "missing": what a user would need that the chunks do not say. For "supported", write "".
6. "confidence": "low" if you hesitated between two verdicts. Otherwise "high".
7. Output JSON only.

EXAMPLE 1
TOPIC: {"id":"T2","topic":"Renewals","example_question":"Can I renew a book?"}
CHUNKS: [{"chunk_id":"loan_policy#p2#c3","doc":"loan_policy.pdf","text":"Books may be renewed twice, unless another member has reserved them. Renew at the front desk or by phone."}]
OUTPUT:
{"topic_id":"T2","verdict":"supported","evidence":[{"chunk_id":"loan_policy#p2#c3","quote":"Books may be renewed twice, unless another member has reserved them."}],"missing":"","confidence":"high"}

EXAMPLE 2
TOPIC: {"id":"T4","topic":"Library events","example_question":"What events are on this month?"}
CHUNKS: [{"chunk_id":"loan_policy#p5#c1","doc":"loan_policy.pdf","text":"The events room is closed for renovation until further notice. Study rooms can be booked at the front desk."}]
OUTPUT:
{"topic_id":"T4","verdict":"unsupported","evidence":[],"missing":"No chunk lists any event, date or time. One chunk mentions the events room, but only that it is closed.","confidence":"high"}

EXAMPLE 3
TOPIC: {"id":"T5","topic":"E-book loans","example_question":"How many e-books can I borrow, and for how long?"}
CHUNKS: [{"chunk_id":"loan_policy#p4#c2","doc":"loan_policy.pdf","text":"E-books return automatically at the end of the loan period."}]
OUTPUT:
{"topic_id":"T5","verdict":"partial","evidence":[{"chunk_id":"loan_policy#p4#c2","quote":"E-books return automatically at the end of the loan period."}],"missing":"How many e-books can be borrowed, and how long the loan period is.","confidence":"high"}

Now check this topic.
TOPIC: {{topic_json}}
CHUNKS: {{chunks_json}}
OUTPUT:
