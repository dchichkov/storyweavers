# Assignment: author one executable microdrama

Fill in `CANDIDATE`, `PREMISE`, and `DESTINATION` before dispatch. Give this same
contract to each author. This is an authoring task, not permission to change the
shared engine or the evaluator. Read this file and `microdrama/engine.py` first.
The parent repository instructions apply; this task explicitly targets the
isolated microdrama prototype, not gen6/gen7.

## Objective

Write a complete small story-world for PREMISE, not a renamed version of the Pig
Palace. Deliver executable local encounters and their literary performances.
The author may use an LLM; the resulting program must use only classical Python.

Readers should encounter a premise, an understandable desire, an obstacle,
physical action, a consequential turn, and an ending image proving what changed.
Aim for 450–900 words per story. Write readable paragraphs with dialogue where
useful; do not turn state changes into a list of event reports.

## Scope and ownership

- Write only within DESTINATION. Do not inspect another candidate's work.
- Reuse `microdrama.engine`: `World`, `Memeplex`, `Microdrama`, `Episode`, and
  transactions. Do not copy or change the engine, evaluator, or existing fable.
- Python 3.9+, standard library only. No runtime network, model calls, external
  datasets, or dependencies on other experiment folders.
- Choose a small cast, 6–12 bounded encounters, and at least two materially
  different outcomes. Optional encounters and local branching are welcome.
- Outcomes must follow world state. Never accept a desired ending as input.
- A physically present instruction carrier conveys knowledge through actual
  contact and access; distraction dilutes transmission. Unembedded content does
  nothing. Use `Memeplex` composition and `Transaction.absorb` at least once.
- Separate material truth from a belief or rumor. Changing a belief must not
  rewrite the physical cause. Preserve ownership separately from temporary use
  if the story involves borrowing or occupation.
- Knowing instructions is not successful action: apply them to a physical task
  and check its outcome. Cooperation must affect a real available action or
  result. At least one encounter implementation must support two role/object
  bindings, demonstrated by your own test.
- Encode all input conditions in initial physical-carrier state. Actions read
  that state; narration reads only committed episode snapshots. No later state
  or hidden configuration may silently rewrite an earlier event.

## Exact interface: `pack.py`

```python
TITLE = "Your story title"

def build_world(config):
    # config has exactly these Boolean keys:
    # access: instruction carrier can be read
    # cooperate: another character is willing/able to assist
    # distraction: the learner's attention is divided
    # Return microdrama.engine.World.
    # Include a physical group entity named 'valley', with
    # valley.ended = False and valley.outcome = '' initially.
    # The existing scheduler uses valley.ended as its terminal flag.
    ...

def dramas():
    # Return tuple[Microdrama]. Each perform(world, params) ignores params;
    # all meaningful conditions are read through transaction state.
    ...

def render(episode):
    # Return a nonempty list of dictionaries:
    # {"text": str, "evidence": list[event_id], "reveals": list[state_key]}.
    # evidence must name events in this episode. reveals names facts actually
    # communicated in the paragraph; use [] for decorative-only paragraphs.
    # The evaluator supplies id/drama fields.
    ...

def questions(world, episodes):
    # Return >= 6 dictionaries, all answerable from this generated story:
    # {"question": str, "answer": str,
    #  "facts": [{"event": event_id, "key": state_key, "value": value}, ...]}.
    # Facts refer to the state AFTER that event, not the final world unless it
    # is the final event. Answer in two grounded sentences, without audit filler.
    # Cover who/what, cause, an object or place, and a changed belief or outcome.
    # Every cited fact must also be revealed by the prose for that event.
    ...
```

World constraints: every key starts with an existing entity ID; declare every
key before execution; scalar values only. Every entity used in movement or
transmission needs `.location`. Books additionally need `.accessible`. Every
transferred meme needs a predeclared `.meme.NAME` field on both carriers. `set`
preserves types. Record all changes through `world.act` and its transaction.
The world validator must enforce your story's important physical invariants.
An action cannot be a no-op; an encounter is atomic. Use only actual declared
characters as action participants. `valley` is a community carrier, not a
free-floating concept or desired-outcome label.

## Deliverables and checking

Deliver `pack.py`, `selftest.py`, and `AUTHOR_NOTES.md` in DESTINATION. Add an
empty `__init__.py` if needed. In the notes explain the premise, invariants,
reusable practice, outcomes, and limitations. Record failed attempts honestly.

Run from `/Users/dmitry/storyweavers`:

```bash
python3 -B -m microdrama.authoring_trial_20261024.evaluate --candidate CANDIDATE
python3 -B -m microdrama.authoring_trial_20261024.CANDIDATE.selftest
```

The shared evaluator checks all 8 Boolean configurations at seeds 0–4, exact
replay, deterministic generation, historical fact evidence, reader exposure,
sentence/length basics, and meaningful final-state differences. Its checks do
not prove literary quality. Read your default story plus two contrasting cases
and improve them. Test a blocked action with no leaked effects and your reusable
practice with a second binding. Do not edit the evaluator to make yourself pass.

Stop after your package works and report the commands, limitations, and changed
files. The parent will independently evaluate and read it, preserving the first
submission before requesting any repairs. No commits, pushes, or extra agents.
