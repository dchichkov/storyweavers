# Held-out comparison review

All 20 source worlds were generated with seeds 701 and 907, beat budget 6, and expanded continuations. I read all 40 bodies. This compares the final integrated corrections with the earlier read-only audit snapshot; it is not an isolated ablation. The earlier code was not separately frozen. Both row sets and the final source hashes are preserved alongside this report.

All 40 runs completed and passed physical replay, story annotation, normalized joint token probabilities, and raw-body/framed-body alignment. The 160 selected QA pairs and all 44 dedicated beat QA pairs passed their evidence-offset checks. These checks establish consistency, not literary quality. The focused grammar, presentation, and subject-coherence suite passed all 32 tests.

Four bodies and two titles changed. Two library event sequences also changed because narrowing an earlier candidate distribution changes later seeded draws; those stories cannot be compared as wording-only edits.

| Case | Earlier output | Current output / interpretation |
|---|---|---|
| pond 701 | “The long net was free again. She used the long net…” | “…Mina used the long net…” The optional callback now exposes its grammatical subject before the next clause is sampled. |
| picnic 907 | “The picnic basket was safe now. She saved the sandwich…” | “…Bea saved the sandwich…” The same subject-scope correction. |
| greenhouse 701 / 907 | Titles used “Tomato Seedling.” | Titles use “Tomato Seedlings,” matching the plural entity and source noun grammar. |
| library 907 | “Mina looked closely at the mitten,” before any narrated mitten introduction. | No unseen-mitten inspection. The resulting continuation also takes another native branch. |

Focused construction tests additionally verify that the object in “Let us try the torch” belongs to the hypothetical embedded try action; “safe to wear” has an unspecified wearer, rather than making the cape the actor; and quoted requests/proposals preserve speaker/listener roles. No suggesting beat was sampled in these 40 runs, so the first check relies on its explicit construction test.

Remaining storytelling limitations are visible:

- Callbacks can repeat a state already made clear. Greenhouse 701: repair, “The shade cloth was repaired now,” then seedlings under repaired cloth. Pond 701 repeats free/free-again across a walk. Orchard 907 repeats no-longer-bending/unbent across the gift delivery. No deduplication heuristic was added.
- Subject continuity only operates inside a scene. Costume 701 and 907 still have “Rafi held the Moon robe. She borrowed the golden cape.” Repair 701 and 907 still switch from Niko placing a tray to “She loosened the nut.” The intended actors remain recoverable, but the surface reference is abrupt.
- Title selection still follows the source target. Both music samples have a signup-sheet title although their bodies focus on a drum and duet and never mention the sheet.
- Some inserted speech lacks a response or concrete follow-through: bakery 701 asks for help with smudged icing, then moves directly to placing the cake. This is grounded optional speech, but it adds little dramatic development.
- At this snapshot, market 701's beat QA includes the spoken brass scale in its answer/evidence but omits it from `entity_ids`; the candidate token/action annotations do identify the scale. This was reported separately to the parent working on QA.

Most bodies are unchanged from the earlier snapshot. The corrections improve specific reference and annotation failures; this sample does not establish a broad quality gain.

Artifacts: [all stories and selected QA](review_40.samples.md), [summary and source hashes](review_40.summary.json), [rerun script](review_40.rerun.py), and the `review_40.before.jsonl.gz` / `review_40.after.jsonl.gz` traces. Run the script from the repository environment to repeat the same 40 cases.


## Follow-up after review

The market701 missing-scale QA binding was fixed after this snapshot. Beat QA
now collects entity references from selected token attributes matching the exact
beat and native frame, so a spoken instrument need not equal the native patient.
`test_spoken_tool_is_in_evidence_bindings_even_when_patient_differs` covers it.
The final campaign audit and round10_final use the corrected QA implementation.
The saved before/after review traces remain the original review evidence.
