# Conversational QA prototype

The new QA layer runs offline over immutable Storyscenes traces. It adds
conversation state, natural answers, follow-ups and draft chat export without
rewriting stories, changing authoring prompts or making API calls. The original
7.75 story benchmark remains unchanged; this pass does not claim a new literary
score for either the stories or QA.

## Available now

- Starter questions about discoveries, shared information, loans/transfers,
  movement, initial wishes and supported state changes.
- Follow-up why/next/previous/holder/location questions retain entity, event and
  time focus. Explaining a cause does not move the chronological cursor back to
  that cause when the user next asks what happened afterward.
- Belief checks compare the character's stored information with the world at the
  same time. Information can be stale; a speaker does not transmit omniscient truth.
- Loan/return answers distinguish the current holder and recorded lender.
  Arbitrary ownership changes are not described as voluntary gifts.
- Unsupported questions, missing motives, ambiguous people and events beyond the
  ending abstain. Failed resolution does not change the conversation's focus.
- Every supported answer carries exact facts with time indices, event/entity
  references and a trace fingerprint. Free-form scene summaries are not used as
  proof or copied into answers.

Try the [interactive CLI and examples](../../CONVERSATIONAL_QA.md), or read the
[four-pair loan conversation](example.txt). `run.py ... --qa --json` adds QA to
an unchanged frozen sample; `qa.py ... --chat-jsonl` writes draft chat records
with provenance outside the spoken messages.

## Trial and verification

The trial reads three previously saved samples from each of the two compact
benchmark worlds and ten earlier workshop worlds. It makes no generation or
judge calls and records the current QA source hashes.

| Measurement | Result |
| --- | ---: |
| Stories sampled | 36 across 12 world instances |
| Conversations | 200 |
| Three-pair conversations | 159 |
| Two-pair conversations | 41 |
| Supported answers | 493 |
| Explicit boundary abstentions | 66 |
| Timed-fact, focus-replay and raw-fragment errors | 0 |
| Supported answers with 2+ substantive sentences | 67.5% overall; 75% on compact benchmark |
| Mean supported-answer length | 13.5 words |
| Typed events with a supported description | 149 / 305 |
| Conversations per sampled story | 2–6 |
| API requests / added API cost | 0 / $0 |

Question kinds include knowledge, information source, belief checks, causal
prerequisites, contributors, chronology, ownership, location, desires and state
changes. The broad sample underfills the requested six conversations on some
older worlds. Missing vocabulary or a thin trace is not padded with invented
facts. Bare “Yes.” is not counted as a substantive sentence.

**93 tests pass**, including the original Storyscenes suite and 21 new QA tests.
Six representative stories pin exact wording, follow-up focus and evidence.
Behavioral cases include false-belief transmission, return history, stolen
ownership versus gifts, unrecorded motives, misleading summaries, ambiguous
pronouns, independent conversations, future evidence, irrelevant sibling effects
in causal frames, and unchanged output from the frozen world CLI.

Interactive input/quit and chat JSONL export were exercised. Python compilation,
source-hash checks and whitespace checks passed. No original run, sample, story
or authoring contract was modified.

## Manual reading and remaining limitations

The library loan conversation gives a coherent chain: Bram lends the cart,
its repaired condition and tied cover explain why the loan is possible, Ada has
it on loan, and the next recorded event moves the cart to the library. The
lender is not confused with the current holder, and a shared-kernel Move does
not invent matching movement by the person.

The synthetic changed-box case transmits Ada's outdated belief to Ben. The
follow-up correctly says the box was open then and identifies Ada as Ben's
information source. A fake rocket trip in a scene summary does not appear.

Night-garden review exposed a useful causal distinction: one event both invites
Pip and opens the gate, but the later performance reads the gate state. Its
explanation now follows the relevant gate change, not the unrelated invitation
flag merely because both were written by one event.

The language is still templated. Repeated ownership confirmations and “At that
point” phrasing can be shallow. Some legitimate answers have only one supported
sentence. The field/enum vocabulary deliberately covers a subset of custom
world definitions: legacy locations such as `leaves` or `selected_hook` without
physical entity bindings are not invented as new places.

Trace grounding also does not prove that the prose states the answer. For
example, the baseline library book can remain at location=library in state while
its English story describes delivery elsewhere. QA must expose that discrepancy
rather than overwrite the simulation. Chat exports are marked
`requires_story_alignment_review`; they are not automatically accepted training
data. A semantic story/QA judge and richer author-time grammatical mappings are
next steps, separate from these deterministic checks.

Evidence: [checks and coverage](checks.json), [all story/conversation samples](samples.md),
[JSONL worksheet](samples.jsonl), [example chat export](example_chat.jsonl),
[test output](tests.txt). Reproduce with `qa_trial.py` as documented in the
[QA guide](../../CONVERSATIONAL_QA.md).
