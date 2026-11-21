# Beat annotations and generation: ten refinement rounds

Implemented six reusable beat readings on intact text, optional word-sampled scene expansions, functional dialogue, and physical setup/result reminders. The initial implementation is saved as round00; the ten refinements below changed code and were followed by recorded samples.

Presentation correction (Nov 15): the examples below now include sampled titles, openings, and closings. Their archived body prose and QA are unchanged. The [complete presented edition](../beats_20261115/preflight/report.md) contains all 18 final samples. Historical per-round reports remain raw evidence; new reports show framing for both expanded and baseline stories.

## Verification

- Original archive: 400 stories, 20 worlds, 46,964 tokens and 4,359 native events. Text, positions, original attribute tables and posteriors preserved; archived native effects replayed.
- Six annotated beat kinds: `{"choice": 963, "discovery": 200, "expectation": 443, "interruption": 420, "payoff": 877, "reaction": 80}`. Supporting events may remain unclassified.
- Final broad audit: 40 generations across 20 worlds, budgets 2 and 6; 5,444 normalized token/joint distributions, 279 grounded QA pairs, and 3 successful joined-plot runs with a shared budget.
- All 285 grammarworlds tests pass, including ten new beat regressions. These counts and code hashes describe the Nov 13 campaign snapshot, before subsequent refinements.
- New dialogue and reactions execute inside native scenes; native guards stay authoritative. No runtime LLM or learned weighting was added.

## What the final samples show

The final held-out set contains 18 runs on pottery, repair and museum, at seeds 103, 211 and 307, with two budgets. Mean optional beats used: 1.50; range 0–3. A cap of six does not force six additions.
Each expanded sample is paired with the closest-length baseline from a fixed 16-seed pool for its source. 15/18 pairs are within 10% of baseline length. The other pairs are longer; this is not a fully equal-length quality experiment. The seeds and word counts are shown, and selection uses length rather than a quality score.
Inspection now names the failed object; requests can lead naturally into an existing helper response; reminders connect the final grip, wheel or shadow to an earlier state. These are visible local improvements. They do not establish a calibrated literary-quality gain.

Remaining observed weaknesses: adjacent lines can repeat the same speaker (repair request followed by admission), two reminders can over-explain one repair, and some reactions remain generic. Native source plots still dominate composition. No Luna evaluation was run.

## Iteration record

| Round | Finding | Change and evidence |
|---|---|---|
| 1 | Wrong object after a setback | Inspection/help targeted the next instruction label or tray. Use the affected object from the setback. [Samples](round01/report.md) |
| 2 | Inspection is not discovery | Record attention/caution on the actor and requests as uttered. Looking does not invent a discovered cause or an answered request. [Samples](round02/report.md) |
| 3 | Repeated intentions and repeated results | Suppress a generic commitment when native dialogue already voices the choice; recall the original shadow wish instead of just saying small twice. [Samples](round03/report.md) |
| 4 | Mixed functions in a scene | Export pre-event expansions separately from native functions and preserve token beat posteriors. Later testing exposed the live metadata propagation defect fixed in round 7. [Samples](round04/report.md) |
| 5 | Pacing and visible setups | Keep the final short-story slot for a planted detail and downweight repeated forms. Silent logistical events cannot plant a reader-facing callback. [Samples](round05/report.md) |
| 6 | Tense and broader coverage | Correct present-tense dialogue/reminders. Broader testing covered all twenty worlds and exposed the joined-renderer argument bug fixed next. [Samples](round06/report.md) |
| 7 | Live attributes and joined stages | Fix the metadata propagation and renderer argument bugs. Regression verifies one continuing budget and receiving-world entity IDs. [Samples](round07/report.md) |
| 8 | Physical access and actual speech | Gate inspection/help by shared location. Distinguish Grandpa’s suggestion from a request; silent choices are not dialogue. [Samples](round08/report.md) |
| 9 | Answerability of the new beats | Add trace-based QA with earlier/later text evidence and utterance-time names. No assumption that a request was answered. [Samples](round09/report.md) |
| 10 | Concrete proposals and final audit | Name the tool of the selected action, bind callbacks to their actual detail, and expose native beat readings in live bundles. Held-out seeds 103, 211, 307. [Samples](round10_final/report.md) |

Round10 contains the preliminary final samples; round10_final adds the completion-audit correction for live native beat fields and preserves those samples’ prose. The initial archive-export attempt used fresh sampling, which could select a different branch. The successful exporter instead replays the archived frame tape; its output is **annotated_pool_v2**.

## Selected final stories

### pottery, seed 307, budget 6

The Cup

Once upon a time, there was someone named Bea.

The Cup

Once upon a time, there was someone named Bea.

Bea said, “I would like to give a cup to Grandpa Len.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Bea said, “Could you help me with the cup?” Mr Ivo told Bea, “The cup's wall is thick.” Grandpa Len said, “I could hold a bowl with two hands.” Bea said, “I want to smooth the dent.” Using the sponge, Bea smoothed the dent. Mr Ivo fired the cup twice. The cup was cool. Bea handed Grandpa Len the cup. Grandpa Len poured tea into the cup. The dent was smooth now. Grandpa Len held the cup's wide handle.

Q: What did Bea ask for after the setback?

A: The shaping rib slipped. The cup was dented. Bea asked Mr Ivo for help with the cup.

Q: Which earlier detail does this later moment bring back?

A: The shaping rib slipped. The cup was dented. The dent was smooth now.

### repair, seed 103, budget 6

Ada and the Blue Cart

One day, Ada was at the courtyard.

The blue cart was rattling. Ada said, “I want to repair the blue cart.” Niko said, “I need to move the tomato tray.” Ada borrowed the spanner. With the spanner, she tightened the nut. The wheel was locked. Ada looked closely at the wheel. Ada said, “I am wrong.” Niko placed the tomato tray under the bench. She loosened the nut. Ada discovered the kite string inside the wheel. Niko held the wheel. She unwound the kite string. She fitted the wheel. The wheel spun smoothly. The blue cart no longer rattled. Ada and Niko placed the tomato tray in the blue cart. Ada pushed the blue cart to the sheltered corner. She returned the spanner to the bench. The wheel that had locked now turned freely. The tomato tray was sheltered. The wheel was quiet.

Q: What did Ada inspect after the setback?

A: With the spanner, she tightened the nut. The wheel was locked. Ada looked closely at the wheel.

Q: Which earlier detail does this later moment bring back?

A: The blue cart was rattling. Ada said, “I want to repair the blue cart.” Niko said, “I need to move the tomato tray.” The blue cart no longer rattled.

### museum, seed 103, budget 6

Miri and the Shadow

One day, Miri was at the museum.

Miri and the Shadow

One day, Miri was at the museum.

Miri said, “I want to show Dot a small shadow.” Kit said, “I would like a dragon.” Miri borrowed the torch. Miri moved the torch. The shadow grew. Miri hesitated. Kit read the instruction label. Miri told Kit, “I need to steady the torch.” Miri steadied the torch with the clay wedge. Miri moved the paper moth toward the screen. The shadow shrank. Dot told Miri, “I can try.” This was the small shadow Miri had wanted. Dot held the paper moth beside the screen. The shadow was small.

Q: How did Miri react before continuing?

A: Miri moved the torch. The shadow grew. Miri hesitated before continuing.

Q: Which earlier detail does this later moment bring back?

A: Miri said, “I want to show Dot a small shadow.” Kit said, “I would like a dragon.” This was the small shadow Miri had wanted.

### Concrete proposal (development seed 42)

Miri and the Shadow

One day, Miri was at the museum.

Miri said, “I would like to show Dot a small shadow.” Kit said, “I would like a dragon.” Miri borrowed the torch. Miri moved the torch. The shadow grew. Miri hesitated. Kit read the instruction label. Miri said, “I need to steady the torch.” Miri said, “I will try the book stack.” Miri rested the torch on the book stack. This time, the torch stayed still. Miri moved the paper moth toward the screen. The shadow shrank. Dot said, “I could try.” Dot held the paper moth beside the screen. The shadow was small.

The End.

## Reproduce

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario museum --seed 42 --beat-budget 6 --continuations expanded --qa
.venv/bin/python -m unittest grammarworlds.test_beats -v
.venv/bin/python -m grammarworlds.beat_annotation_export --out /tmp/annotated-beats
.venv/bin/python -m grammarworlds.beat_experiment --out /tmp/beat-samples --seeds 103 211 307 --change "Reproduce final held-out sample set"
```

See [BEATS.md](../../BEATS.md) for APIs, scope and limits. `final_audit.jsonl.gz` retains broad source and joined traces; each round includes paired raw text, QA and a code snapshot.
