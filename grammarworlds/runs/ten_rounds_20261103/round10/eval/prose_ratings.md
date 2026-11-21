# Grammarworlds: Luna quality and diversity

Judge: gpt-6-luna; Flex; reasoning none; existing calibrated 0–9 rubric.
420 generated stories; 140 judged. Complete: True.
Random positions, no deduplication or quality filtering. Generation is classical and unchanged.

| Scenario | Quality / 9 | Diversity / 9 | Plot groups | Exact unique texts | Event-kind paths |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 7.00 | 2 | 2 | 28/60 | 2 |
| kite | 7.20 | 3 | 3 | 30/60 | 3 |
| key | 6.00 | 2 | 2 | 42/60 | 2 |
| music | 7.00 | 2 | 3 | 5/60 | 3 |
| greenhouse | 5.80 | 2 | 3 | 15/60 | 3 |
| library | 6.00 | 2 | 2 | 8/60 | 24 |
| pottery | 7.00 | 2 | 3 | 6/60 | 6 |

## Quality dimensions

| Dimension | Mean / 9 |
| --- | ---: |
| coherence | 7.72 |
| style | 5.57 |
| grammar | 8.57 |
| storytelling | 6.04 |
| overall | 6.57 |

## Diversity dimensions (mean within scenario)

| Dimension | Mean / 9 |
| --- | ---: |
| premise | 1.86 |
| causal_path | 2.43 |
| ending | 2.43 |
| language | 1.71 |
| overall | 2.14 |

## rescue

All stories share the central problem of a shivering animal stranded on a high ledge and end with it wrapped in a warm blanket. Most use the same bread-in-basket-and-rope rescue (for example, s000014 and s000041); only s000034, s000002, s000039, and s000035 use a ladder instead. Character and animal substitutions do not change the plot, and the ladder branch is a small causal variation. These sampled stories are highly similar, without establishing the diversity of the full generator.

Causal plot groups:

- 16 stories: A child shares bread to coax a frightened animal from a high ledge into a rope-lowered basket, then brings it inside and wraps it warmly.
- 4 stories: A child steadies a ladder while an adult climbs up and lifts the stranded animal down, then the child brings it inside and wraps it warmly.

Lowest-rated samples (ties retain judge order):

- s000014 (7/9): The rescue is easy to follow and ends with the rabbit warm, though the repeated actions make the telling plain.
- s000028 (7/9): The rescue is easy to follow and ends with the rabbit warm, though the repeated actions make the telling plain.
- s000058 (7/9): Sam shares his bread to lure the rabbit into the basket, then brings it inside to rest; the prose is clear but repetitive.

## kite

All stories share the damaged-kite setup and use nearly the same short, repetitive language. Four stories (s000014, s000017, s000035, s000007, s000041) resolve it by taping and flying the kite; most others repurpose it as a boat sail (including s000058, s000023, s000034, s000002, s000024). Only s000036, s000021, s000039, and s000018 make the failed tape repair a consequential turn before the sail solution. Names and minor dialogue differences do not create new plots; these sample stories show limited variation, not the full generator’s range.

Causal plot groups:

- 6 stories: Tape the torn kite successfully, then fly it; the boat-sail suggestion is unused.
- 10 stories: Skip repairing the torn kite and cut material from it to make a boat sail, which carries the boat across the pond.
- 4 stories: Try taping and flying the kite, but it tears again; then repurpose it into a sail and send the boat across the pond.

Lowest-rated samples (ties retain judge order):

- s000014 (7/9): The tape repair succeeds and the kite’s dance gives a clear ending, though the boat-sail line is left unexplained.
- s000028 (7/9): The repaired kite flies successfully, ending with a vivid image; the boat-sail remark does not affect the plot.
- s000058 (7/9): The torn kite is repurposed into a sail, and the boat crossing the pond completes the practical problem-solving arc.

## key

All stories share the same cottage-and-storybook problem. Most (for example, s000014 and s000041) use a lantern to find the hidden key; a smaller branch (s000036 and s000053) uses a spare key and postpones the search. Character names and family terms vary, but the outcomes and language remain very similar. This small sample does not establish the generator’s overall diversity.

Causal plot groups:

- 14 stories: A child wants to read inside, discovers the door is locked and the key missing, finds the key under a bench using a lantern, unlocks the door, and reads with a parent.
- 6 stories: A child admits the key is missing, borrows a spare key from a parent to enter and read, then returns it and leaves a reminder to search for the missing key later.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The lantern reveals the misplaced key and resolves the locked-door problem, though the simple sequence has little dramatic development.
- s000028 (6/9): The search, discovery, and unlocking form a clear sequence, but the telling is repetitive and minimally developed.
- s000058 (6/9): Sam finds the key with the lantern and reaches the book; the ending resolves the problem but is told plainly.

## music

Nearly all stories share the same premise of Nia hoping to make music with hesitant Mateo. Most (including s000014 and s000053) resolve this with Nia performing a solo; s000058 and s000021 instead have Mateo write a rhythm for her to play, while s000017 and s000041 resolve the hesitation with a private duet. These are meaningful but limited branches, and the language and endings remain very similar across the sample.

Causal plot groups:

- 13 stories: Mateo is not ready to perform with an audience, so Nia practices and performs a solo for Dalia; Mateo applauds.
- 5 stories: Mateo avoids performing by writing a rhythm, which Nia practices and plays for Dalia, then preserves beside a second drum as an invitation to continue.
- 2 stories: Because Mateo is uncomfortable performing for an audience, he and Nia play a duet privately, answering each other’s beats.

Lowest-rated samples (ties retain judge order):

- s000014 (7/9): Nia turns Mateo’s reluctance into a solo performance, which has a clear outcome, though the ending is brief.
- s000028 (7/9): Nia turns Mateo’s reluctance into a solo performance, which has a clear outcome, though the ending is brief.
- s000058 (7/9): Mateo contributes a written rhythm when he is not ready to perform; Nia plays it, then leaves it with a second drum as a concrete invitation to continue.

## greenhouse

The set centers on one garden problem: a broken tap, scarce water, and fallen shade. Most stories share the sunflower-first path, leaving a brown leaf and making a promise (s000002, s000023, s000058); a smaller branch waters tomatoes first, then uses the repaired tap for the sunflower (s000017, s000028). A few divide the water and shelter both plants under an umbrella (s000007, s000014). These are limited variations within a shared structure, and the prose is highly repetitive. This small sample does not establish the diversity of the entire generator.

Causal plot groups:

- 4 stories: Nia divides the limited water between both plants, then shelters them together under an umbrella while the tap remains broken.
- 4 stories: Nia uses the scarce water on the thirsty tomatoes first, protects them from the fallen shade cloth, then waters the sunflower after the tap is repaired.
- 12 stories: Nia waters the sunflower first, leaving the tomatoes with a brown leaf; after the tap and shade are repaired she waters the tomatoes and promises to prioritize them tomorrow.

Lowest-rated samples (ties retain judge order):

- s000014 (5/9): The equal split and umbrella shelter address both plants, but the brief, repetitive narration offers little development.
- s000057 (5/9): Sharing the scarce water and moving both plants under the umbrella gives a simple resolution, but it is unclear how one can adequately waters both.
- s000007 (5/9): Nia divides the limited water and shelters both plants, but the one-can allocation and final claim that both stand upright feel underexplained.

## library

The set has just two causal patterns: in s000014, s000023, s000017, s000021, s000034, s000042, s000035, s000018, and s000007 Mina keeps her moon-atlas plan while Ms Alvarez retrieves Jun’s book; in s000028, s000058, s000036, s000053, s000048, s000002, s000057, s000039, s000024, s000038, and s000041 Mina sets that plan aside to help Jun and draws a whale instead. Variations such as “saw” versus “spotted,” or “used” versus “lifted” the ladder, do not make materially different plots. This small sample does not establish diversity for the whole generator.

Causal plot groups:

- 9 stories: Mina promises to help Jun find his missing whale book, but continues with her moon-atlas sketch while Ms Alvarez retrieves the book; Mina finishes a moon drawing.
- 11 stories: Mina sets aside her moon-atlas sketch to help Jun with his missing whale book; Ms Alvarez retrieves it, and Mina draws a whale from it.

Lowest-rated samples (ties retain judge order):

- s000014 (6/9): The book is retrieved and Mina completes her moon sketch, though Jun’s missing-book search and the reciprocal help feel abruptly stitched together.
- s000028 (6/9): Mina sets aside her moon plan to help Jun, then draws a whale from the recovered book; the resolution is clear but told in repetitive, event-by-event prose.
- s000058 (6/9): Mina chooses to help Jun and finishes a whale drawing after Ms Alvarez retrieves the book; the sequence is clear but lacks much scene or emotional development.

## pottery

All stories share the same pottery-gift setup and mishap, followed by firing and Grandpa using the result. Most are near duplicates: thumb-rest variants (s000014, s000017, s000034, s000042, s000039, s000024, s000038, s000007), bowl conversions (s000058, s000036, s000053, s000021, s000048, s000057, s000018, s000041), and smoothed-dent cup endings (s000023, s000002, s000035). These few examples show little variation in plot or language.

Causal plot groups:

- 9 stories: After a cup is dented, Bea shapes the dent into a thumb rest; Grandpa drinks from the cup and rests his thumb there.
- 8 stories: After a cup is dented, Bea reshapes it into a bowl suited to Grandpa's two-handed grip; he uses the bowl.
- 3 stories: After a cup is dented, Bea smooths the dent and Grandpa uses the cup's wide handle.

Lowest-rated samples (ties retain judge order):

- s000014 (7/9): The dent becomes a useful thumb rest, and Grandpa tests it with tea; the simple, repetitive narration is clear.
- s000028 (7/9): The dent is repurposed as a thumb rest that Grandpa uses, though the telling is very step-by-step.
- s000058 (7/9): Bea changes the damaged cup into the two-handed bowl Grandpa says he can hold; the outcome is concrete but plainly narrated.

## Scope

Each diversity score describes 20 sampled positions per scenario, not the full generator. These authored situations share much of their machinery. No cross-scenario semantic diversity score is claimed. Exact unique strings and different event-kind sequences do not establish different plots; optional goal/thanks beats can inflate path counts. Trigram overlap and repeated sentences are available in mechanical.json; they measure surface reuse, not quality. One Luna judgment per set is a diagnostic baseline, not an independently calibrated human evaluation or confidence interval. Requests, untouched samples, responses, token usage, and source snapshots are saved for audit. No price estimate is claimed.
