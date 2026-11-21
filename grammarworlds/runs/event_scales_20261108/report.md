# Multiple event scales and world time

20 worlds; 60 authored episodes; 249 fine-event kinds. Two annotated samples per world. These yield 86 observed episode-ending prefixes. Source text is preserved in annotated documents.

## Matched receiver experiment

Nia has a rattling garden trolley and an uncontrolled shadow. The explicit goal requires a repaired trolley, a small controlled shadow, and a performance started after those preparations. Deadline: one simulated hour. No source scenarios or event sequence are supplied. Both policies use the same candidate pool, native guards, attachment variants and four-episode limit. Plain samples feasible alternatives uniformly; contextual uses physical goal progress, closure, duration fit and import/event cost. This is a small designed fixture, not a held-out literary-quality evaluation.

| Policy | Goal met on time | Mean needs met / 3 | Mean episodes | Deadline overruns | Episodes with no immediate goal progress |
|---|---:|---:|---:|---:|---:|
| plain | 0/4 | 0.50 | 3.25 | 1 | 11 |
| contextual | 4/4 | 3.00 | 3.25 | 0 | 1 |

## Generated examples

### plain, seed 7

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Omar. Nia told Omar, “I need an answering beat.” Omar told Nia, “I am not ready for the audience.” Omar said, “I could write a rhythm.” He wrote a rhythm on the paper with the pencil. Nia practiced Omar's rhythm on the little drum. Nia played Omar's rhythm on the little drum before Dalia. Omar clapped. Nia bowed. Nia said, “I want to play your rhythm again.” Nia put the paper between the little drum and the second drum.

The sketchbook was windblown. Nia told Omar, “I want to draw the sea.” She fetched the map from the garden wall. She followed the bathhouse path. Omar said, “I am worried.”

The garden trolley was rattling. Nia told Omar, “I would like to repair the garden trolley.” Omar said, “I need to move the tomato tray.” Nia borrowed the spanner. Using the spanner, Nia tightened the nut. The wheel was locked. Nia said, “I am wrong.” Omar put the tomato tray under the bench. She loosened the nut. She found the kite string inside the wheel. Mr Rafi held the wheel. She unwound the kite string. Nia fitted the wheel. The wheel spun smoothly.

The silver star was missing. Nia said, “I need a star.” Omar said, “I could help you.” Nia fetched the needle from the costume shelf. The brass button was heavy. Using the needle, she stitched the brass button on the felt star. She tied the felt star's loop twice. Nia told Omar, “I have a light.” She put the felt star beside the Moon puppet. Nia returned the needle to the costume shelf. The brass button shone beside the red curtain.

Result: episode_limit; 1195 seconds; 1/3 needs achieved.

| Selected source | Coarse episode | New fine events | Simulated interval (seconds) | Needs advanced |
|---|---|---:|---:|---|
| music | Perform and acknowledge the collaboration | 11 | 0–440 | none |
| seaside | Locate a place to draw | 3 | 440–565 | none |
| repair | Diagnose the obstruction and restore the wheel | 7 | 565–710 | working trolley |
| puppets | Speak up and contribute the star | 9 | 710–1195 | none |

### contextual, seed 7

The garden trolley was rattling. Nia told Omar, “I would like to repair the garden trolley.” Omar said, “I need to move the tomato tray.” Nia borrowed the spanner. Using the spanner, she tightened the nut. The wheel was locked. Nia told Omar, “I am wrong.” Omar put the tomato tray under the bench. She loosened the nut. She located the kite string inside the wheel. Omar held the wheel. Nia unwound the kite string. She fitted the wheel. The wheel spun smoothly. Nia and Omar placed the tomato tray in the garden trolley. Nia pushed the garden trolley to the sheltered corner. She returned the spanner to the bench. The tomato tray was sheltered. The wheel was quiet.

Nia said, “I would like to show Dot a small shadow.” Omar told Nia, “I would like a dragon.” Nia borrowed the torch. Nia moved the torch. The shadow grew. Omar read the instruction label. Nia told Omar, “I need to steady the torch.” Nia steadied the torch with the clay wedge. Nia moved the paper moth toward the screen. The shadow shrank.

Nia told Omar, “I would like the golden cape.” Omar held the Moon robe. Nia borrowed the golden cape. Omar said, “I need a Sun costume.” Nia gave Omar the golden cape. The golden cape's hem was long. Nia told Omar, “I could help you.” Omar gathered the golden cape's front. Nia fetched the Sun disk from the prop box. Nia gave the Sun disk to Omar. Omar raised the Sun disk. Nia swirled with the blue ribbons. Omar hung the golden cape in the costume cupboard. The golden cape shone.

Result: goal_achieved; 1120 seconds; 3/3 needs achieved.

| Selected source | Coarse episode | New fine events | Simulated interval (seconds) | Needs advanced |
|---|---|---:|---:|---|
| repair | Move the load and return the tool | 10 | 0–490 | working trolley |
| museum | Control one variable and test again | 6 | 490–740 | controlled shadow |
| costume | Perform together and return the costume | 10 | 740–1120 | shared performance |

## Boundaries and remaining defects

- Coarse goals are authored predicate graphs. There is no natural-language goal parser or learned planning policy.
- Episode memberships are authored; entity-specific chains are derived participant threads, not independent causal subplans.
- Time is sampled from estimated bands (5 seconds, 1 minute, 1 hour, 1 day). Events execute serially; there is no overlap scheduler. Parent duration estimates are descriptive and are not added again.
- Token candidates contain current commitments and duration distributions before sampling. Retrospective source observations are labeled separately.
- Native source prefixes may bring prerequisite events, props and motives. Compatible prefixes can resume on existing carriers without replaying earlier events.
- The prose still resembles linked mini-stories; the shared demonstration goal is in the structured fixture and is not consistently expressed as one opening/ending in the text. This is a long-range selection improvement, not evidence of improved literary quality.
- Some partial source commitments remain open when the receiving goal finishes. There is no Luna evaluation in this experiment.

Full candidate probabilities, selected token distributions, timings, native events and replay specifications: `continuations.jsonl.gz`. Intact source annotations: `stories.memory.jsonl.gz`.
