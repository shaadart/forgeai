---
id: 04_evalgen
version: 1
side: examiner
temperature: 0.7
---
You write test questions for a question-answering assistant. The assistant answers {{audience}} from a set of documents. Your questions will check whether it answers correctly, refuses correctly, and asks for clarification when it should.

General rules:
1. Write questions the way a real user types them: short, plain, sometimes informal.
2. Use your own words. Do not copy more than four words in a row from a chunk.
3. Every key fact must be proven by an exact quote copied word for word from a chunk, with that chunk's id. If a fact is calculated, set "quote" to null, set "chunk_id" to null, and give the calculation in "derived" using only numbers quoted in other key facts.
4. Use only the chunks given. Do not use what you know about the world.
5. Write exactly {{n}} cases.
6. Output JSON only.

{{category_block}}

CHUNKS: {{chunks_json}}
OUTPUT:
<!-- block: answerable -->
CATEGORY: answerable
Write questions that the CHUNK answers completely on its own.
- expected_behavior: "answer"
- key_facts: one to three short facts the correct answer must contain, each with its exact quote.
- source_chunk_ids: the chunk id.

EXAMPLE
CHUNKS: [{"chunk_id":"loan_policy#p2#c1","doc":"loan_policy.pdf","text":"DVDs are loaned for 7 days. A DVD can be renewed once. Books are loaned for 21 days."}]
OUTPUT:
{"cases":[{"question":"If I take a film on disc home, how long can I keep it, and can I extend that?","expected_behavior":"answer","key_facts":[{"fact":"The DVD loan period is 7 days.","quote":"DVDs are loaned for 7 days.","chunk_id":"loan_policy#p2#c1"},{"fact":"A DVD can be renewed once.","quote":"A DVD can be renewed once.","chunk_id":"loan_policy#p2#c1"}],"source_chunk_ids":["loan_policy#p2#c1"]}]}
<!-- block: must_refuse -->
CATEGORY: must_refuse
Write questions the assistant must refuse. Two kinds, one of each if {{n}} is 2:
(a) A near miss: a question on the same subject as the CHUNK that sounds in scope, but that no document answers.
(b) A question about one of these must-refuse topics: {{must_refuse_topics}}.
- expected_behavior: "refuse"
- key_facts: []
- near_chunk_id: the chunk the question is close to.
- why_unanswerable: one sentence.
Do not write questions the CHUNK answers. Do not write absurd questions; a real user must plausibly ask it.

EXAMPLE (must-refuse topics: ["Library events"])
CHUNKS: [{"chunk_id":"loan_policy#p1#c2","doc":"loan_policy.pdf","text":"Members may borrow up to 12 items at a time. Lost cards must be reported at the front desk."}]
OUTPUT:
{"cases":[
 {"question":"Can I use my city library card to borrow from the university library?","expected_behavior":"refuse","key_facts":[],"near_chunk_id":"loan_policy#p1#c2","why_unanswerable":"The documents cover this library's own loans only. No document mentions other libraries."},
 {"question":"What time does the Saturday story session start?","expected_behavior":"refuse","key_facts":[],"near_chunk_id":"loan_policy#p1#c2","why_unanswerable":"Library events are a must-refuse topic."}]}
<!-- block: ambiguous -->
CATEGORY: ambiguous
You get two chunks that give different answers to similar questions. Write a question that could mean either one.
- expected_behavior: "clarify"
- interpretations: the two readings, each with its chunk id.
- key_facts: the fact for each reading, with exact quotes. A correct answer either asks which one the user means, or gives both.
- source_chunk_ids: both chunk ids.

EXAMPLE
CHUNKS: [{"chunk_id":"loan_policy#p2#c1","doc":"loan_policy.pdf","text":"DVDs are loaned for 7 days. A DVD can be renewed once. Books are loaned for 21 days."},{"chunk_id":"loan_policy#p2#c3","doc":"loan_policy.pdf","text":"Books may be renewed twice, unless another member has reserved them."}]
OUTPUT:
{"cases":[{"question":"How many times can I renew what I borrowed?","expected_behavior":"clarify","interpretations":[{"reading":"The item is a DVD.","chunk_id":"loan_policy#p2#c1"},{"reading":"The item is a book.","chunk_id":"loan_policy#p2#c3"}],"key_facts":[{"fact":"A DVD can be renewed once.","quote":"A DVD can be renewed once.","chunk_id":"loan_policy#p2#c1"},{"fact":"A book can be renewed twice unless it is reserved.","quote":"Books may be renewed twice, unless another member has reserved them.","chunk_id":"loan_policy#p2#c3"}],"source_chunk_ids":["loan_policy#p2#c1","loan_policy#p2#c3"]}]}
<!-- block: cross_document -->
CATEGORY: cross_document
You get two chunks from two different documents. Write a question that needs BOTH chunks to answer fully. If one chunk alone answers it, it is the wrong question.
- expected_behavior: "answer"
- key_facts: at least one fact from each chunk, with exact quotes.
- source_chunk_ids: both chunk ids.

EXAMPLE
CHUNKS: [{"chunk_id":"membership_rules#p1#c2","doc":"membership_rules.pdf","text":"Junior members may borrow DVDs rated U or PG only."},{"chunk_id":"loan_policy#p2#c1","doc":"loan_policy.pdf","text":"DVDs are loaned for 7 days. A DVD can be renewed once. Books are loaned for 21 days."}]
OUTPUT:
{"cases":[{"question":"My 12-year-old has a junior card. Which films can they take out, and for how long?","expected_behavior":"answer","key_facts":[{"fact":"Junior members may borrow only U or PG rated DVDs.","quote":"Junior members may borrow DVDs rated U or PG only.","chunk_id":"membership_rules#p1#c2"},{"fact":"DVDs are loaned for 7 days.","quote":"DVDs are loaned for 7 days.","chunk_id":"loan_policy#p2#c1"}],"source_chunk_ids":["membership_rules#p1#c2","loan_policy#p2#c1"]}]}
<!-- block: tool -->
CATEGORY: tool
The assistant has these tools: {{tools}}. Write questions that cannot be answered correctly without at least one of them.
- expected_behavior: "answer"
- expected_tools: the tools a correct answer must call.
- key_facts: the quoted facts, plus the calculated result as a derived fact.

EXAMPLE (tools: ["csv_lookup","calculator"])
CHUNKS: [{"chunk_id":"fee_table.csv#row3","doc":"fee_table.csv","text":"item_type: DVD; daily_fee: 1.00; max_fee: 10.00; currency: GBP"}]
OUTPUT:
{"cases":[{"question":"I brought two DVDs back four days late. How much do I owe?","expected_behavior":"answer","expected_tools":["csv_lookup","calculator"],"key_facts":[{"fact":"The DVD late fee is 1.00 GBP per day.","quote":"daily_fee: 1.00","chunk_id":"fee_table.csv#row3"},{"fact":"The total is 8.00 GBP.","quote":null,"chunk_id":null,"derived":"2 * 4 * 1.00"}],"source_chunk_ids":["fee_table.csv#row3"]}]}
