# Executable plot stages and shared physical bindings

Pool: 400 source documents from 20 worlds; 58 distinct native source branches. Inputs contain a plot contract, Nia, Omar and a workshop. No source scenario, object, recipient or fine-event sequence is specified.

The planner previews native source suffixes, rejects incompatible bindings and unfinished plot trajectories, then samples a normalized distribution over prefixes ending at the next plot milestone. Completed stages and obligations are updated from actual execution. It preserves the same object (and gift recipient) through all stages. Each chosen prefix is generated through the existing annotated-token grammar.

| Plot | Seed | Complete, narrated, on time | Stage sources | Resumes | Simulated seconds |
|---|---:|---|---|---:|---:|
| adapt_gift | 7 | True | pottery → pottery → pottery → pottery | 3 | 101720 |
| adapt_gift | 19 | True | pottery → pottery → pottery → pottery | 3 | 267320 |
| adapt_gift | 42 | True | pottery → pottery → pottery → pottery | 3 | 101775 |
| adapt_gift | 103 | True | pottery → pottery → pottery → pottery | 3 | 184520 |
| changed_approach | 7 | True | pottery → pottery → pottery → pottery → pottery → pottery | 5 | 101720 |
| changed_approach | 19 | True | repair → repair → repair → repair → repair → repair | 5 | 325 |
| changed_approach | 42 | True | repair → repair → repair → repair → repair → repair | 5 | 435 |
| changed_approach | 103 | True | museum → museum → museum → museum → museum → museum | 5 | 370 |

## Capability-only comparison

This small matched-pool comparison checks identity, not literary quality. The old coarse planner only requires capability labels in order. Its object IDs below are diagnostic readings of the selected source targets, not constraints it enforced.

| Seed | Coarse labels complete | Same object | Selected sources |
|---|---|---|---|
| 7 | True | False | pottery → bakery |
| 19 | True | True | pottery |

## adapt_gift, seed 7

Nia told Omar, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Omar said, “The cup's wall is thick.” Grandpa Len said, “I could hold a bowl with two hands.” Nia told Omar, “I would like a thumb rest.” With the sponge, Nia formed the dent into a thumb rest. Omar fired the cup twice. The cup was cool. Nia handed Grandpa Len the cup. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

Bindings: `{"object": "u0__cup", "recipient": "u0__grandpa"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | goal | — | satisfied |
| adapt_for_recipient | thumb | uses_discovery #6 | satisfied |
| give_same_object | give | payoff_of #2 | satisfied |
| show_useful_result | ending | ending_evidence #23 | satisfied |

Open obligations: 0. Missing narration: 0.

## adapt_gift, seed 19

Nia told Omar, “I want to give a cup to Grandpa Len.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Omar said, “The cup's wall is thick.” Grandpa Len said, “I can hold a bowl with two hands.” Nia said, “I would like a bowl.” Nia reshaped the cup into a bowl with the shaping rib. Omar fired the bowl twice. The bowl was cool. Nia gave Grandpa Len the bowl. Grandpa Len poured tea into the bowl. Grandpa Len held the bowl with two hands.

Bindings: `{"object": "u0__cup", "recipient": "u0__grandpa"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | goal | — | satisfied |
| adapt_for_recipient | remake | uses_discovery #6 | satisfied |
| give_same_object | give | payoff_of #2 | satisfied |
| show_useful_result | ending | ending_evidence #23 | satisfied |

Open obligations: 0. Missing narration: 0.

## adapt_gift, seed 42

Nia said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Omar told Nia, “The cup's wall is thick.” Grandpa Len said, “I can hold a bowl with two hands.” Nia said, “I would like a thumb rest.” Nia used the sponge to shape the dent into a thumb rest. Omar fired the cup twice. The cup was cool. Nia handed Grandpa Len the cup. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

Bindings: `{"object": "u0__cup", "recipient": "u0__grandpa"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | goal | — | satisfied |
| adapt_for_recipient | thumb | uses_discovery #6 | satisfied |
| give_same_object | give | payoff_of #2 | satisfied |
| show_useful_result | ending | ending_evidence #23 | satisfied |

Open obligations: 0. Missing narration: 0.

## adapt_gift, seed 103

Nia said, “I would like to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Omar said, “The cup's wall is thick.” Grandpa Len said, “I can hold a bowl with two hands.” Nia said, “I would like to smooth the dent.” Using the sponge, Nia smoothed out the dent. Omar fired the cup twice. The cup was cool. Nia gave Grandpa Len the cup. Grandpa Len poured tea into the cup. Grandpa Len held the cup's wide handle.

Bindings: `{"object": "u0__cup", "recipient": "u0__grandpa"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | goal | — | satisfied |
| adapt_for_recipient | smooth | uses_discovery #6 | satisfied |
| give_same_object | give | payoff_of #2 | satisfied |
| show_useful_result | ending | ending_evidence #23 | satisfied |

Open obligations: 0. Missing narration: 0.

## changed_approach, seed 7

Nia told Omar, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Omar told Nia, “The cup's wall is thick.” Grandpa Len told Nia, “I can hold a bowl with two hands.” Nia told Omar, “I would like a thumb rest.” With the sponge, Nia shaped the dent into a thumb rest. Omar fired the cup twice. The cup was cool. Nia gave the cup to Grandpa Len. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

Bindings: `{"object": "u0__cup"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | goal | — | satisfied |
| attempt_fails | slip | — | satisfied |
| discover_why | inspect | responds_to #4 | satisfied |
| change_approach | thumb | uses_discovery #6 | satisfied |
| achieve_goal | give | payoff_of #2 | satisfied |
| show_changed_world | ending | ending_evidence #23 | satisfied |

Open obligations: 0. Missing narration: 0.

## changed_approach, seed 19

The blue cart was rattling. Nia told Omar, “I want to repair the blue cart.” Omar said, “I need to move the tomato tray.” Nia borrowed the spanner. Using the spanner, she tightened the nut. The wheel was locked. Nia said, “I am wrong.” Omar placed the tomato tray under the bench. She loosened the nut. She located the kite string inside the wheel. Omar held the wheel. She unwound the kite string. She fitted the wheel. The wheel spun smoothly. Nia and Omar placed the tomato tray in the blue cart. She pushed the blue cart to the sheltered corner. She returned the spanner to the bench. The tomato tray was sheltered. The wheel was quiet.

Bindings: `{"object": "u0__cart"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | cart_goal | — | satisfied |
| attempt_fails | tighten_wrongly | — | satisfied |
| discover_why | diagnose_string | explains_problem #3 | satisfied |
| change_approach | refit_and_test | uses_discovery #5 | satisfied |
| achieve_goal | move_plants | payoff_of #1 | satisfied |
| show_changed_world | quiet_wheel | ending_evidence #7 | satisfied |

Open obligations: 0. Missing narration: 0.

## changed_approach, seed 42

The blue cart was rattling. Nia said, “I want to repair the blue cart.” Omar said, “I need to move the tomato tray.” Nia borrowed the spanner. With the spanner, she tightened the nut. The wheel was locked. Nia said, “I am wrong.” Omar placed the tomato tray under the bench. Nia loosened the nut. She discovered the kite string inside the wheel. Mr Rafi held the wheel. She unwound the kite string. Nia fitted the wheel. The wheel spun smoothly. Nia and Omar placed the tomato tray in the blue cart. She pushed the blue cart to the sheltered corner. She returned the spanner to the bench. The tomato tray was sheltered. The wheel was quiet.

Bindings: `{"object": "u0__cart"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | cart_goal | — | satisfied |
| attempt_fails | tighten_wrongly | — | satisfied |
| discover_why | diagnose_string | explains_problem #3 | satisfied |
| change_approach | refit_and_test | uses_discovery #5 | satisfied |
| achieve_goal | move_plants | payoff_of #1 | satisfied |
| show_changed_world | quiet_wheel | ending_evidence #7 | satisfied |

Open obligations: 0. Missing narration: 0.

## changed_approach, seed 103

Nia said, “I would like to show Dot a small shadow.” Omar told Nia, “I want a dragon.” Nia borrowed the torch. Nia moved the torch. The shadow grew. Omar read the instruction label. Nia said, “I need to steady the torch.” Nia steadied the torch with the clay wedge. Nia moved the paper moth toward the screen. The shadow shrank. Dot said, “I could try.” Dot held the paper moth beside the screen. The shadow was small.

Bindings: `{"object": "u0__shadow"}`.

| Stage | Native event | Narrative evidence | Narrated |
|---|---|---|---|
| establish_desire | exhibit_goal | — | satisfied |
| attempt_fails | moving_light | — | satisfied |
| discover_why | read_small_print | responds_to #3 | satisfied |
| change_approach | clay_support | uses_discovery #4 | satisfied |
| achieve_goal | controlled_trial | enables #5 | satisfied |
| show_changed_world | little_wings | payoff_of #1 | satisfied |

Open obligations: 0. Missing narration: 0.

## Limits

- The implementation executes two local plot structures, not all nine archetypes. Existing source annotations supply the available readings.
- Full native suffix lookahead strongly favors coherent reuse of one authored story. This is staged retrieval and execution, not evidence of inventing novel cross-source plots.
- Setup/payoff obligations and same-entity checks are enforced. Discovery links are authored narrative relations over actual events; they are not an automatically inferred causal theory.
- Character knowledge records only new native `knows_*`/`understands_*` states. Reader exposure records narrated events and typed referents. There is no general false-belief, hidden-motive or reader-comprehension model.
- Narration gates require visible text with relevant typed entities for each plot milestone. This catches silent or unrelated endings, but does not measure elegance or guarantee explicit causal connective wording.
- No added connective prose, runtime LLM or learned weights. The stronger coherence here comes primarily from preserving authored relationships and rejecting incompatible continuations.
- All durations remain authored estimates. No deadline was imposed in these samples; pottery can take days.

## Validation

All 270 grammarworlds tests pass, including nine new plot regressions. All 40 sampled stage distributions normalize. Generated stage rows replay and re-annotate successfully; the recorded source hashes match the final code. See `tests.log` and `validation.json`. No Luna quality evaluation was run.
