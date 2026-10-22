# Conversational QA

Conversational QA is an offline layer over a saved story's world trace and
attributed dialogue. It keeps
the generated story, authoring prompts and old mechanical `qa` field unchanged.
There are no Luna/Terra calls to create or answer these conversations.

## Generate questions and follow-ups

```bash
python storyscenes/run.py storyscenes/runs/compact_algebra_v2/library_parade \
  --seed 1000 --qa

python storyscenes/run.py storyscenes/runs/compact_algebra_v2/library_parade \
  --seed 1000 --qa --qa-limit 6 --json > /tmp/story-qa.jsonl

python storyscenes/qa_checks.py /tmp/story-qa.jsonl
```

The original frozen runtime still generates the story. The current QA library
then adds `conversations` and `conversation_metadata`. `--qa-seed` varies the
question selection without changing the story or its simulation. New runtime
snapshots also include the standalone QA tools.

Each conversation has up to three question/answer pairs by default. Selection
balances question kinds and explores follow-up branches with a bounded search.
A short trace may support only two pairs or fewer conversations than requested;
the engine does not invent extra events to fill a quota. Boundary answers are
explicit abstentions, counted separately from supported answers.

## Talk about one story

```bash
python storyscenes/qa.py storyscenes/runs/compact_algebra_v2/library_parade \
  --seed 1000 --interactive

python storyscenes/qa.py storyscenes/runs/compact_algebra_v2/library_parade \
  --seed 1000 \
  --ask 'Who did Bram lend the shared cart to?' \
  --ask 'Why?' \
  --ask 'Who had it?' \
  --ask 'What happened next?'
```

Interactive mode lists supported starter questions. Choose a number or type a
listed question, then use short follow-ups:

- `Why?` / `How was that possible?` explains recorded prerequisites. It does
  not turn an enabling condition into an invented motive.
- `What happened next?` and `What happened before that?` move through the actual
  event order. A causal explanation keeps the original focus for the next turn.
- `Who had it?`, `Who had it before that?`, and `Where was it?` inspect the
  focused object's state at that point. An ambiguous person pronoun asks for
  clarification rather than silently selecting an actor or prop.
- `How did they know?` follows an observation or a speaker's stored belief.
- `Was that true?` compares the belief with the physical fact at that time.
  An outdated belief can be transmitted without becoming true.
- `Who helped?` describes a recorded causal contribution from a speaker/giver;
  it does not infer an intention to help from every event in the causal graph.

This is a bounded interpreter, not unrestricted natural-language chat. Unknown
questions and missing motives abstain and preserve the conversation's focus.
There is no invented continuation beyond the ending. Start a new listed question
to switch subjects, or construct a fresh `Conversation(trace)` to reset context.

## Questions about dialogue

```bash
python storyscenes/qa.py storyscenes/runs/compact_algebra_v2/pond_concert \
  --seed 1000 \
  --ask 'What did Ada tell Frog?' \
  --ask 'Why did she say that?' \
  --ask 'Who were they talking to?' \
  --ask 'What happened next?'
```

- `What did Ada say?`, `What did Ada tell Frog?`, and `What did Ada say to Frog?`
  retrieve attributed words. Several matching speeches require selection from
  numbered starter questions. These numbers count indexed speeches, not every
  utterance in the story.
- `Who said “Mira wants quiet today”?` identifies a unique quoted speaker.
- `Who were they talking to?`, `Who said that?`, and `What were the exact words?`
  refer to the current speech.
- `Why?` / `Why did she say that?` / `Why did Ada say that?` use an explicitly
  linked speaker belief or goal. Without that annotation, a matching Tell scene
  can provide speaker/listener knowledge context, explicitly distinguished from
  a motive. Otherwise the answer says the reason is not recorded.
- `What was said next?`, `What was said before that?`, and `What did Ada say next?`
  navigate indexed speech. `What did they reply?` requires an explicit reply link;
  the next quotation is not automatically treated as a reply.
- `Was that true?` checks an authored factual claim against the corresponding
  world state. Merely saying something does not make it true. An unannotated
  quotation cannot be classified as true, false or a deliberate lie.

Pass `Conversation(trace, paragraphs)` to enable dialogue in the Python API.
CLI and `enrich()` do this automatically. `enrich(..., include_dialogue=False)`
retains the original trace-only conversation selection and regression pins.

For existing frozen stories, a conservative importer recognizes explicit,
adjacent named attributions such as `Ada told Frog, “…”` and `“…,” Ada said`.
It preserves exact character spans, including separate spans for supported
interrupted speech. It does not guess who “he” refers to, who heard a remark,
or which reply follows from a nearby action. Unsupported interruptions are
skipped rather than returning only a vocative such as “Tomas,”. This limits
coverage: an unindexed line can still exist in the story.

New `render_book` runs index explicit quotations before joining bridge cards,
preserving their precise originating event with no extra model output tokens.
Authors can also add structured annotations to a selected prose variant:

```python
{
    'text': 'Ada told Ben, “The box is closed.” Ben replied, “I will remember that.”',
    'when': [],
    'dialogue': [
        {'speaker': 'ada', 'listener': 'ben', 'quote_indices': [0],
         'reason_keys': ['ada.knows.box.open'],
         'claim': {'key': 'box.open', 'value': False, 'at': 'before'}},
        {'speaker': 'ben', 'listener': 'ada', 'quote_indices': [1], 'reply_to': 0},
    ],
}
```

The scene must carry those participants and read any `reason_keys` as
prerequisites. Reasons may reference the speaker's `.want` or `.knows.*`, not
another character's private goal or an arbitrary convenient world fact. `claim`
is optional; its `at` is `before` (default) or `after` the associated event.
It describes the *assertion*, which can differ from world truth. `reply_to` is
the index of an earlier annotated utterance in that same variant. A variant's
dialogue list describes all its indexed speeches; unknown pronouns can be bound
explicitly by the author. The renderer converts quote indices to exact offsets
and adjusts offsets/reply links when combining cards.

These fields are optional. Existing compact authoring prompts and text-only
response schemas do not request them, so there is no extra API cost. Annotations
are validated for exact spans, participants, times and referenced facts; an
explicit named attribution cannot be contradicted by metadata. Semantic checks
of quote meaning and the authored motive relationship remain necessary.

## Evidence and export

Every supported answer carries `event_ids`, `entity_ids`, exact timed `facts`,
and its `focus`. Initial facts use time zero; event IDs identify after-event
state. The answer text has no internal field names. Shared knowledge, ownership
and movement kernels have typed realizations; common physical properties have
explicit language mappings. Unknown fields or enum values are not emitted as
raw English or guessed from free-form scene summaries.

Dialogue turns additionally carry `utterances`: exact quote spans, paragraph,
speaker, any known listener, event linkage and authored reasons/claims/replies.
Their source is `story_dialogue`. This is separate from `world_trace` facts;
extracting a quote never updates beliefs or physical state. Grouped legacy prose
may identify a passage but not a precise event; action follow-ups then ask for
an event question rather than jumping to an arbitrary later action.

```python
from conversation import Conversation

dialog = Conversation(sample['trace'], sample.get('paragraphs'))
question = dialog.starters()[0]['question']
answer = dialog.ask(question)
follow_up = dialog.ask('Why?')
```

Draft chat JSONL keeps only user/assistant text in messages, with provenance in
metadata:

```bash
python storyscenes/qa.py storyscenes/runs/compact_algebra_v2/library_parade \
  --seed 1000 --chat-jsonl > /tmp/story-chat-review.jsonl
```

These exports require story-alignment review. Trace correctness does not prove
that an answer is stated in, or agrees with, the English story. For example,
some older worlds move a prop in prose without updating its location in state.
QA can expose that discrepancy; it must not invent a new state to conceal it.
Export metadata therefore says `requires_story_alignment_review` rather than
claiming the rows are automatically ready for training.

## Reproduce the QA trial

```bash
python storyscenes/qa_trial.py \
  --run storyscenes/runs/compact_algebra_v2 \
  --run storyscenes/runs/improvement_luna_v6 \
  --out /tmp/storyscenes-qa-trial
python -m unittest discover -s storyscenes -p 'test_*.py'
```

The trial reads the existing pinned stories without regeneration. It records
typed-event coverage, supported answers, abstentions, question kinds, substantive
sentence counts, provenance checks and source hashes. Six representative cases
are pinned in `conversation_pins.json`. Behavioral tests also cover stale beliefs,
loan returns, unrecorded motives, misleading summaries, ambiguous pronouns,
independent conversations, future evidence and unchanged frozen story output.

These checks measure deterministic grounding and conversational continuity.
They are not a new literary-quality score or a replacement for semantic review.
Results and limitations: [initial QA report](improvements/conversational_qa_v1/REPORT.md).
Dialogue extension: [results and examples](improvements/dialogue_qa_v1/REPORT.md).
