## Manual review and limits of the scores

I read seed 1000 from all ten worlds and seeds 1001–1002 from `pond_concert`,
alongside selected traces. These twelve readings are qualitative examples, not
an estimate of the defect rate across the 1,000-story pool. All thirty saved
examples remain available in the per-world `samples.md` files.

The strongest sample was `hill_picnic` seed 1000: the opening gives Ada, Ben,
and Moss distinct preferences; learning about mud and Noor's need for shelter
changes the picnic; the windbreak and shared food demonstrate the outcome.
`roof_post` also has a clear practical turn. Both still overexplain their lessons.

| Example | Observed defect | Why the mechanical checks do not catch it |
|---|---|---|
| `pond_concert`, seed 1002 | The ending describes an anchored arrangement with pads and a log trembling together. The trace ends with `pads.linked = false`, `log.anchored = false`, and `sail.displayed = true`. | Citing the final event does not make an English sentence true. |
| `puppet_weather`, seed 1000 | “It held—or did not hold” and “she said, or” leave alternatives unresolved in the printed story. | Both are nonempty text with valid event citations. |
| `museum_of_small_things`, seed 1000 | “its condition sound”, “a tiny family_mark”, and “wanted the object to be return” expose state values and broken grammar. | Scalar values are valid simulation data, but need grammatical realization. |
| `night_garden`, seed 1000 | Many paragraphs repeat the action twice: dialogue or description followed by the event's summary. | Every event is covered, but coverage does not measure naturalness. |
| `clocktower_club`, seed 1000 | The prose puts the brass gear on the club table after servicing the mechanism, without any corresponding transfer/removal event. | The physical trace is too coarse to constrain every improvised prop detail. |
| `bakery_exchange`, seed 1000 | Characters repeatedly explain evidence, permission, and fairness. The plot proceeds, but much of the voice sounds instructional. | A consistent sequence can still lack wit and characterful dialogue. |
| `library_parade`, seed 1000 | Independent loans create extra preparation scenes even when those props do not help the chosen route. | An eligible optional scene can be causally irrelevant to the ending. |
| `kite_workshop`, seed 1000 | The inspection establishes that the frame condition is known without plainly saying what the condition is. | A knowledge flag is less informative than a well-realized observation. |

The automated judge gives `puppet_weather` 7/9 despite its visible unresolved
alternatives. Treat the scores as comparative signals, not certification that
the prose is usable. I would not accept the whole pool as finished training
material on the strength of its mechanical pass rate or mean quality score.

The important result is a working shared execution layer and a visible boundary
between simulated facts and narration. The experiment does **not** yet solve
literary composition: within-world diversity is low, scene ordering supplies
many apparent variants, and renderers remain mostly bespoke paragraph templates.
The independent `prose_seed` interface is implemented in the shared engine, but
none of the ten generated renderers changed its sampled text in the tested
prose-seed control. These renderers mostly derive variation from world state
and scene ordering, leaving the separate prose RNG unused.
There is no matched one-stage control run, so this trial cannot establish that
staged generation improves quality. The Terra recovery also changed reasoning
effort and feedback, so it does not isolate a model-only effect.

Next measurable targets: detect unresolved alternatives and raw state leakage;
require important prose claims to refer to explicit facts, not only event IDs;
remove optional scenes that contribute nothing to the selected outcome; then
compare a matched one-stage and staged batch using the same seeds and judge.
