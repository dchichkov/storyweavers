# The White Ribbons

Mara wants to save six community orchard rows before an overnight frost. She initially blames bees for old blossom damage. Physical inspection revises that belief without changing the damage's material cause. The notebook holds a composed two-part shelter method, transmitted only through accessible, colocated contact; divided attention halves both magnitudes. A small trial converts knowledge into a physical roof, checks its air gap, anchors, and warmth retention, and gates work on the orchard.

Eight bounded encounters lead to three material outcomes: six surviving rows with focused instruction and two workers; two surviving rows with focused instruction and one worker; no surviving marked rows when instruction is inaccessible or diluted. Ivo lends his fork in all cases, retaining ownership, and receives it back. Cooperation changes feasible coverage rather than merely changing a closing sentence. `shelter` is reused with the trial branch and the six rows, and selftest demonstrates both bindings.

The validator fixes frost as the material cause, preserves ownership, bounds surviving/protected rows, requires actual roof properties, and prevents six-row protection without a willing second worker. All actions transact; blocked notebook absorption is tested after a tentative write to verify rollback. Standalone unembedded content is also checked for no effects.

Ran:

- `python3 -B -m microdrama.authoring_trial_20261024.evaluate --candidate orchard`
- `python3 -B -m microdrama.authoring_trial_20261024.orchard.selftest`

The shared evaluator passes all 40 runs and finds three outcomes. Read the focused/cooperative, distracted/cooperative, focused/solo, and inaccessible/cooperative performances. After the first mechanically passing draft, tightened the world representation of the shelter trial: air gap, anchoring, and warmth retention are now committed physical facts rather than only literary descriptions. Also replaced numeral-heavy counting prose and aligned the inaccessible cabinet's placement with the orchard location. There were no failed command runs or failed evaluator attempts during authoring.

Limitations: This is a deliberately small, ordered night, with no scheduler variation across seeds. Shelter capacity (two rows alone or six together), frost severity, and warmth retention are categorical rather than a thermal or labor simulation. The trial does not teach an unsuccessful learner enough to recover before nightfall. Decorative cups, ribbons, dated marker, kitchen obligations, and cleaning are narrated elaborations, not separately simulated entities; QA cites the core modeled consequences. The old damage is known physical state, not a simulated prior frost episode. The belief revision has one route rather than competing interpretations. Outcomes concern surviving blossoms, not guaranteed eventual fruit yield.

## Parent-requested physical repair

The preserved first submission passed the shared mechanics but independent review correctly identified that trial warmth was equivalent to learned construction, and dawn copied protected rows without checking cold. The revision adds separate initial physical `valley.trial_cold` and `valley.night_cold` severities, each bounded 1–3, and constructed shelter resistance of 0 or 2. Construction and effective warmth are now distinct: a correctly built roof can fail its trial under severe cold, or pass a mild trial and still lose its flowers to a harsher night. Dawn reads frost, night severity, and actual row resistance. The overnight frost Boolean is explicitly validated as the story's fixed premise.

Selftest now constructs two additional worlds with identical access/cooperation/distraction, changing only one initial cold severity to 3. A severe trial leaves a properly constructed trial roof but no retained warmth, preventing orchard deployment. A severe night leaves all six roofs built but no surviving blossoms. Both keep learned magnitudes unchanged. Trial prose/QA distinguish bad construction from inadequate resistance; dawn prose/QA distinguish exposed losses from overwhelmed shelters. Ordinary eight-configuration outputs remain unchanged; evaluator again passes 40/40 and selftest passes both added physical counterfactuals. These repairs supersede the earlier categorical warmth limitation; the model remains categorical, not a heat-flow simulation.

### Second parent-requested prose repair

The severe-trial counterfactual now carries the same explanation into the neighboring deployment scene: the trial roof stood properly but its material had insufficient resistance, so repeating it would not protect the orchard. It no longer borrows the sagging-cloth explanation from the incorrectly constructed trial branch. The counterfactual selftest checks this distinction. Outcome QA now spells out “No,” “Two,” or “All six” instead of using numeric fragments. Shared evaluator and selftests were rerun successfully after this correction.
