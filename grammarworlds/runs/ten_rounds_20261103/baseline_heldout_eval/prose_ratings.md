# Grammarworlds: Luna quality and diversity

Judge: gpt-6-luna; Flex; reasoning none; existing calibrated 0–9 rubric.
420 generated stories; 140 judged. Complete: True.
Random positions, no deduplication or quality filtering. Generation is classical and unchanged.

| Scenario | Quality / 9 | Diversity / 9 | Plot groups | Exact unique texts | Event-kind paths |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 1 | 1 | 30/60 | 9 |
| kite | 6.00 | 1 | 1 | 15/60 | 14 |
| key | 5.00 | 1 | 1 | 15/60 | 16 |
| music | 4.90 | 1 | 3 | 6/60 | 23 |
| greenhouse | 5.00 | 1 | 1 | 12/60 | 16 |
| library | 6.00 | 1 | 1 | 8/60 | 8 |
| pottery | 6.00 | 1 | 2 | 4/60 | 4 |

## Quality dimensions

| Dimension | Mean / 9 |
| --- | ---: |
| coherence | 7.50 |
| style | 4.57 |
| grammar | 8.57 |
| storytelling | 4.94 |
| overall | 5.56 |

## Diversity dimensions (mean within scenario)

| Dimension | Mean / 9 |
| --- | ---: |
| premise | 1.00 |
| causal_path | 1.14 |
| ending | 1.29 |
| language | 1.29 |
| overall | 1.00 |

## rescue

All 20 stories share the same problem and resolution: a cold animal is stranded on a high ledge, a child uses a ladder to bring it down, and it rests in a blanket. The child, animal, and wording change, but the causal structure and warm-rest ending do not (for example, s000014, s000017, and s000057).

Causal plot groups:

- 20 stories: A child rescues a cold animal from a high ledge with a ladder, wraps it in a warm blanket, and the animal rests. In some versions the child first cannot reach it.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The rescue proceeds clearly to the kitten resting warm, though the brief, repetitive action sequence offers little development.
- s000028 (6/9): The rabbit is brought down and warmed in a clear sequence, but the prose is repetitive and minimally developed.
- s000058 (6/9): The kitten’s rescue and warm rest complete the action, though the story is a bare, repetitive sequence.

## kite

All sampled stories use the same torn-kite problem, tape repair, relaunch, and kite-dancing ending. Differences such as names, parent labels, whether the kite falls on the grass, and wording of the repair do not create distinct plots (for example, s000014, s000028, s000053, and s000041). This assessment describes only this sample, not the generator as a whole.

Causal plot groups:

- 20 stories: A child finds a kite torn, gets or uses tape to repair it, then launches it and sees it fly successfully.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The repair sequence is clear and ends with a vivid flying-kite image, though the very brief, repetitive sentences leave little development.
- s000028 (6/9): A clear problem-to-repair-to-flight arc, but the prose is repetitive and the resolution arrives abruptly.
- s000058 (6/9): The kite’s successful flight gives a concrete ending; the short, formulaic telling offers little detail beyond the repair steps.

## key

All 20 stories share the same locked-door, missing-key problem, lantern-assisted search under a bench, unlocking, and stepping through. Names and small wording differences do not change the plot; s000057, s000039, s000035, s000024, and s000038 add only an initial failure to see the key. The sample shows little meaningful variation, without establishing diversity across the whole generator.

Causal plot groups:

- 20 stories: A child faces a locked door and missing key, uses a lantern to find the key under a bench, unlocks the door, and steps through; some versions add a brief initial failure to see the key.

Lowest-rated samples (ties retain judge order):

- s000014 (5/9): The lantern helps Lily locate the missing key and enter, but the brief, repetitive sequence offers little beyond the basic resolution.
- s000028 (5/9): Ben finds the key with the lantern and opens the door; the clear sequence is very bare and ends without much narrative development.
- s000058 (5/9): Nora finds the key, unlocks the door, and steps through; the events are clear but told in a repetitive, minimal style.

## music

All stories share the same premise and nearly identical wording: Nia wants to play a duet, Mateo initially refuses, and she chooses a solo. Most (s000028, s000058, s000023, s000036, s000017, s000053, s000048, s000002, s000035, s000018) add Mateo’s later invitation to play privately; others have Nia accept his choice (s000014, s000034, s000057, s000039, s000024, s000038, s000007, s000041), while s000021 and s000042 repeat his refusal. These are minor outcome branches of one narrow setup, with little meaningful variation in language or ending.

Causal plot groups:

- 8 stories: After Mateo refuses a duet, Nia performs a solo and accepts his choice; the story closes with the drums on the shelf.
- 10 stories: After Mateo initially refuses, Nia performs a solo; Mateo later invites her to play privately, and they play a duet.
- 2 stories: After Mateo refuses, Nia performs a solo, but Mateo repeats his refusal and the story ends with the drums on the shelf.

Lowest-rated samples (ties retain judge order):

- s000021 (4/9): Nia performs alone after Mateo declines, but the repeated refusal and shelf detail provide little sense of a complete ending.
- s000042 (4/9): Nia performs a solo, but Mateo’s repeated refusal and the abrupt shelf image leave the story without a satisfying close.
- s000014 (5/9): Nia’s solo follows Mateo’s refusal, but the story ends abruptly with the drums on a shelf rather than a satisfying closing moment.

## greenhouse

All sampled stories share the same garden problem and resolution: thirsty tomato seedlings during a broken tap, fallen shade, Nia's watering and umbrella, adult repairs, and the seedlings sheltered at the end (for example, s000014 and s000058). Differences are limited to minor wording and the order of repairs; these few samples do not establish diversity for the entire generator.

Causal plot groups:

- 20 stories: Nia notices thirsty tomato seedlings despite a broken tap, waters them with a can, improvises an umbrella after the shade cloth falls, and adults repair the tap and cloth; the seedlings end sheltered.

Lowest-rated samples (ties retain judge order):

- s000014 (5/9): The watering and improvised umbrella address immediate needs, but repetitive event-like sentences leave little character or emotional development.
- s000028 (5/9): Nia waters the seedlings and shields them after the cloth falls; the ending shows them protected, though the prose is list-like.
- s000058 (5/9): The broken tap and fallen shade prompt practical fixes, but the short, repetitive narration feels more like a report than a developed story.

## library

All 20 stories share the same problem and causal sequence: Jun’s whale book is missing, the children search and notice a high-shelf clue, Ms Alvarez retrieves it, and they read together. Variants in whether Mina’s atlas is saved or returned and in wording such as “spotted” versus “saw” do not change the plot (for example, s000014 and s000028). This small sample indicates near-duplication, not the diversity of the entire generator.

Causal plot groups:

- 20 stories: Jun cannot find his whale book; Mina helps search, a high-shelf clue reveals where it is, and Ms Alvarez retrieves it so the friends can read together.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The missing book is found on a high shelf and shared, though the ending is brief and Mina’s choice is repeated.
- s000028 (6/9): Jun spots the high-shelf clue and the librarian retrieves the book; the moon atlas is saved, but the resolution feels procedural.
- s000058 (6/9): The book is retrieved and they read together, but the repeated action-focused sentences give the story little emotional development.

## pottery

All stories share Bea making a cup for Grandpa, a shaping mishap, a sponge-based response, firing, and the gift being used. The only meaningful branch is smoothing the dent with Grandpa holding the wide handle (s000028, s000017, s000034, s000057, s000042, s000039, s000035) versus adding a thumb rest that Grandpa uses (s000014, s000058, s000023, s000036, s000053, s000021, s000048, s000002, s000024, s000038, s000018, s000007, s000041). This sample is highly repetitive and does not establish the diversity of the entire generator.

Causal plot groups:

- 13 stories: Bea makes a cup for Grandpa, adds a thumb rest after a shaping mishap, fires and gives it to him; he uses the rest.
- 7 stories: Bea makes a cup for Grandpa, smooths the dent from a shaping mishap, fires and gives it to him; he holds its wide handle.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The cup’s design responds to Grandpa’s stiff hand, and its successful use completes the gift, though the terse sequence has little emotional texture.
- s000028 (6/9): Bea repairs the dent and the wide handle suits Grandpa, but the events are presented plainly with little development beyond the practical payoff.
- s000058 (6/9): The thumb rest is a sensible adaptation and Grandpa uses it, though the short, repetitive sentences make the story feel more like a sequence of steps.

## Scope

Each diversity score describes 20 sampled positions per scenario, not the full generator. These authored situations share much of their machinery. No cross-scenario semantic diversity score is claimed. Exact unique strings and different event-kind sequences do not establish different plots; optional goal/thanks beats can inflate path counts. Trigram overlap and repeated sentences are available in mechanical.json; they measure surface reuse, not quality. One Luna judgment per set is a diagnostic baseline, not an independently calibrated human evaluation or confidence interval. Requests, untouched samples, responses, token usage, and source snapshots are saved for audit. No price estimate is claimed.
