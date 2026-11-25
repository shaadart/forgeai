---
id: 01b_requirements
version: 1
side: builder
temperature: 0
---
You turn a brief and a short interview into a requirements document for a question-answering assistant.

INPUT
- BRIEF: the requester's paragraph.
- INVENTORY: the files the assistant will answer from.
- INTERVIEW: questions and answers. "source":"requester" means a person answered. "source":"default" means nobody answered and the default was used.
- CAPABILITIES: the only capability names you may use.

WRITE
1. scope: one or two sentences. What the assistant answers, and from which files.
2. audience: who asks the questions.
3. tone: three to six words.
4. must_answer: the topics the assistant must answer, one topic per item.
   - Take topics only from the BRIEF and the INTERVIEW. Do not add a topic just because a file mentions it.
   - Give one example_question a real user would ask.
   - Give the capabilities the example_question needs:
     "retrieval": the answer is written in the files. Every topic has this.
     "lookup_rows": the answer needs exact rows from a table file (codes, prices, quantities).
     "arithmetic": the answer needs a calculation (a total, a difference, a percentage).
     "today": the answer depends on today's date (a deadline, "how long until").
     "live_weather": the answer needs current or forecast weather or sea state.
   - Add a capability only if the example_question cannot be answered without it. A topic that mentions money, dates or weather does not automatically need a capability.
5. must_refuse: topics the assistant must decline. Include topics the BRIEF or INTERVIEW excludes, and topics an interview answer says to refuse. Give a reason and a referral (where the user should go instead). If you do not know a referral, write "your manager or the responsible department".
6. assumptions: one item for every INTERVIEW answer with "source":"default". Say in plain words what was assumed.

RULES
1. If the BRIEF and an INTERVIEW answer disagree, follow the INTERVIEW answer and add an assumption that says so.
2. Plain words. No marketing language.
3. Output JSON only.

EXAMPLE
BRIEF: "I want a bot that helps library members with borrowing rules and late fees, and also tells them about events."
INTERVIEW: [{"id":"Q1","question":"No file covers library events. Should the assistant refuse event questions and point members to the events page?","answer":"Yes. Refuse event questions and point to the events page.","source":"default"},{"id":"Q2","question":"Late fees appear in both loan_policy.pdf and fee_table.csv. If they disagree, which one is current?","answer":"Show both values and say they disagree.","source":"default"}]
OUTPUT:
{"scope":"Answers library members' questions about borrowing, renewals and late fees, using loan_policy.pdf and fee_table.csv.",
 "audience":"Library members",
 "tone":"Friendly, short, plain",
 "must_answer":[
  {"id":"T1","topic":"Borrowing limits","example_question":"How many books can I take out at once?","capabilities":["retrieval"]},
  {"id":"T2","topic":"Renewals","example_question":"Can I renew a DVD?","capabilities":["retrieval"]},
  {"id":"T3","topic":"Late fee totals","example_question":"I returned two DVDs three days late. What do I owe?","capabilities":["retrieval","lookup_rows","arithmetic"]}],
 "must_refuse":[
  {"id":"X1","topic":"Library events","reason":"No file covers events.","referral":"the library events page"}],
 "assumptions":[
  {"text":"Event questions are refused and sent to the events page. Nobody confirmed this.","from_question":"Q1"},
  {"text":"If the two fee sources disagree, both values are shown. Nobody confirmed this.","from_question":"Q2"}]}

Note: T3 does not need "today". The member states how many days late.

Now do the same for this input.
BRIEF: {{brief}}
INVENTORY: {{inventory_json}}
INTERVIEW: {{interview_json}}
CAPABILITIES: {{capabilities_json}}
OUTPUT:
