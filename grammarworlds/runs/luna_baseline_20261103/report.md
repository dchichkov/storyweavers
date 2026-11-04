# Grammarworlds: Luna quality and diversity

Judge: gpt-6-luna; Flex; reasoning none; existing calibrated 0–9 rubric.
300 generated stories; 60 judged. Complete: True.
Random positions, no deduplication or quality filtering. Generation is classical and unchanged.

| Scenario | Quality / 9 | Diversity / 9 | Plot groups | Exact unique texts | Event-kind paths |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 1 | 2 | 100/100 | 11 |
| kite | 6.15 | 2 | 3 | 100/100 | 16 |
| key | 7.00 | 2 | 2 | 100/100 | 15 |

## Quality dimensions

| Dimension | Mean / 9 |
| --- | ---: |
| coherence | 7.67 |
| style | 6.05 |
| grammar | 8.33 |
| storytelling | 6.05 |
| overall | 6.38 |

## Diversity dimensions (mean within scenario)

| Dimension | Mean / 9 |
| --- | ---: |
| premise | 1.00 |
| causal_path | 2.00 |
| ending | 1.00 |
| language | 2.00 |
| overall | 1.67 |

## rescue

All 20 stories use the same core premise and outcome: a child rescues a small animal stranded on a high ledge with a ladder, then warms it in a cottage. The only meaningful causal variation is whether the child acts independently (group 0; e.g. s000029, s000076) or asks an adult for advice or the ladder (group 1; e.g. s000073, s000070). Failed reaching and whether the child fetches or climbs the ladder are minor branches, not substantially different plots. Endings and language remain highly similar across the set.

Causal plot groups:

- 10 stories: The child independently recognizes or obtains a ladder, sometimes after an unsuccessful reach, and uses it to bring the stranded animal down before warming it indoors.
- 10 stories: The child asks an adult for help or advice; the adult recommends and sometimes brings the ladder, which the child uses to rescue the stranded animal and warm it indoors.

Lowest-rated samples (ties retain judge order):

- s000029 (6/9): The ladder rescue proceeds clearly to a safe, concrete ending, though the brief, repetitive action sequence has little development.
- s000057 (6/9): Nora retrieves a ladder and safely rescues the kitten; the ending is clear but the story is very compressed.
- s000047 (6/9): Sam’s failed reach motivates the ladder rescue, which ends with the kitten warm and safe; the prose is repetitive.

## kite

All twenty stories concern repairing a torn kite so it can fly again. Most follow the same repair-and-launch sequence, with minor variation in whether the child figures out the tape alone (s000057, s000043, s000009, s000042) or gets adult advice and supplies (s000047, s000073, s000034). Three add a failed launch before repair (s000029, s000068, s000088). All end with the repaired kite flying, so outcomes and language remain highly repetitive. These sampled stories do not establish the diversity of the whole generator.

Causal plot groups:

- 3 stories: The child tries to fly the damaged kite before repairing it; the failed launch reveals the problem, prompting a tape repair and successful flight.
- 4 stories: The child independently recognizes or uses tape to mend the torn kite, then launches the repaired kite successfully.
- 13 stories: The child seeks adult advice or help obtaining tape, repairs the torn kite, and gets it flying again.

Lowest-rated samples (ties retain judge order):

- s000057 (6/9): Nora notices the torn kite, repairs it, and gets it flying; the outcome is clear, though the repeated phrasing is plain.
- s000047 (6/9): Sam seeks Mum’s advice, repairs the kite, and launches it successfully; the simple sequence resolves the problem clearly.
- s000073 (6/9): Mum provides tape, Ben repairs the tear and thanks her; the flying kite gives a concrete, complete ending.

## key

All twenty stories share the same central problem and outcome: a locked cottage, a missing key under a dark bench, lantern-assisted discovery, and entry. The main causal variation is whether the child independently realizes light will help (s000029, s000096) or asks an adult who suggests or supplies the lantern (s000057, s000068); some include an unsuccessful search first (s000043, s000049). Thanks and minor wording changes do not create new plot structures. This sample is highly repetitive and does not establish the generator’s broader diversity.

Causal plot groups:

- 8 stories: The child independently recognizes or uses the lantern to illuminate the dark hiding place, finds the key, and opens the cottage.
- 12 stories: The child seeks an adult’s help or advice, obtains or is given the lantern, finds the key under the bench, and opens the cottage.

Lowest-rated samples (ties retain judge order):

- s000029 (7/9): The lantern reveals the missing key and resolves the locked-door problem, though the brief, plain sequence offers little character or emotional development.
- s000057 (7/9): Nora’s unsuccessful search motivates asking Dad for help, and the lantern solves the problem; the ending is clear but quite matter-of-fact.
- s000047 (7/9): Mum’s lantern suggestion directly helps Sam find the key and enter, though the repeated actions feel more like a sequence of events than a developed tale.

## Scope

Each diversity score describes 20 sampled positions per scenario, not the full generator. These three authored recovery situations share much of their machinery. No cross-scenario semantic diversity score is claimed. Exact unique strings and different event-kind sequences do not establish different plots; optional goal/thanks beats can inflate path counts. Trigram overlap and repeated sentences are available in mechanical.json; they measure surface reuse, not quality. One Luna judgment per set is a diagnostic baseline, not an independently calibrated human evaluation or confidence interval. Requests, untouched samples, responses, token usage, and source snapshots are saved for audit. No price estimate is claimed.
