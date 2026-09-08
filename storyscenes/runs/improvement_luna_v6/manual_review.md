# Final manual reading and limits of the scores

I read seed 1000 from all ten final worlds with the saved trace, and the exact
lowest-rated judged texts for roof_post (`s000029`, source_index 29),
kite_workshop (`s000005`, source_index 5), and hill_picnic (`s000029`). These
13 readings are qualitative evidence, not a defect-rate estimate. The same
sample IDs are zero-based positions in `quality/inputs.json`.

Overall quality improved modestly, 6.68 → 6.94. Grammar (7.63 → 8.29) and style
(5.93 → 6.77) improved, diversity rose 2.20 → 3.20, and scores below six fell
17 → 6. Coherence was effectively unchanged (6.75 → 6.76); storytelling slipped
6.80 → 6.61. Two formerly strong worlds regressed: roof_post 7.80 → 6.10 and
hill_picnic 8.00 → 6.50. This is not a clean literary-quality win.

The warmer voice is visible in the actual prose. Puppet Weather gives its shy
performer a specific want and an amusing voice (“My nose is not ready for fame”).
The pond concert lets music “tiptoe and twirl.” The bakery's shared crumbs make
a concrete ending instead of an explanation of fairness. These are better
sentences, but strong sentences can still cover weak or inconsistent mechanics.

| Final sample | What works | Remaining defect |
|---|---|---|
| bakery_exchange, 1000 | A small shared treat and distinctive squirrel dialogue. | Some other seeds still muddle label versus actual filling; not all choices fulfill the opening promise. |
| clocktower_club, 1000 | A specific gentle-bell choice and a completed meeting. | A practice-rope discovery sounds the bell before it is unlocked; much of the middle is still procedural. A sleeping-neighbor branch can end with an unexplained startled grin. |
| hill_picnic, 1000 | Moss's procession creates a warm ending image. | The bell sounds before a corresponding ringing state change; the transfer's wording also conflates giving and tying it. The hilltop branch moves characters in prose while their location state stays at the foot. |
| kite_workshop, 1000 | The inspection names what was found; the note reaches its destination. | A private mailbox is followed by dialogue referring to a lively crowd. In judged s000005, a weather note is overwritten by a sky cheer without a motivated turn. |
| library_parade, 1000 | The revised ending correctly leaves books in the arrived cart; unsupported bell and banner claims were removed from the route's conclusion. | The folding-shelf revelation still unfolds a room in English while only knowledge changes in the trace. The loaded cart travels to the square and back without a strong reason. |
| museum_of_small_things, 1000 | Clearer grammar, playful dialogue, a completed whisper tour. | Ada displays the brass key after trading it to Pip, with no display-loan or return event. The judge's 7.7 average is not evidence of grounded ownership. |
| night_garden, 1000 | A gentle tableau and a moth landing; the unresolved location alternative was removed. | The opening opens the gate, then the first action opens it again. Physical event granularity is still coarse. |
| pond_concert, 1000 | Actual performance followed by Nora's traced response. Strong voice. | The final two paragraphs repeat the dancing-comma image. |
| puppet_weather, 1000 | A shy performer's request changes how the show works; a complete shadow performance. | The audience's arrival is described again in some branches; certain invitation sequences remain awkward. |
| roof_post, 1000 and s000029 | A completed delivery and playful physical details. | A catalog patch edited a neighboring card: the ribbon-tying event now narrates another hook selection. The judged sample repeats discovery and selection. The ending also rings an unrecorded bell. |

## What the review pipeline did and did not establish

The ten bounded Terra reviews returned short findings over three stories and
state changes, with no script input and a 1,600-token output cap. Luna wrote all
changes. Reviews were reused in the final pass. Some findings were questionable:
for example, ordinary narrator knowledge was sometimes treated as illicit
character knowledge. Other important defects were missed. Fix suggestions must
be checked against the trace, not accepted as authoritative.

The final pass stopped discarding findings just because their layer was labeled
“simulation”; unsupported prose can often be narrowed without changing the
world. This fixed some route endings. However, prose patches can target a wrong
array entry even while producing valid JSON and keeping all mechanical tests
green. The rooftop example is a concrete regression caused by this weakness.
A stronger next edit protocol should address scenes by stable IDs, require the
expected old text, and compare the changed passage to its event before accepting
it. The current indexed inventory is insufficient.

Mechanical completion and fact bindings do not establish English entailment.
The current batch is useful prototype evidence; I would not launch 20,000 worlds
as accepted training data based on its mean score. The next acceptance pass
should target unrecorded actions, character/prop locations, contradictory
commitments, and incorrect patch targets, and preserve the per-world regressions
rather than hiding them in an overall average.

The cost result is stronger than the quality result: all 125,608 authoring output
tokens (including unsuccessful and superseded Luna drafts) used Luna. Authoring
cost was about $0.1955 for ten mechanically successful worlds. The 104 authoring
requests show that the workflow is still repair-heavy. Human review time is not
included in the dollar projection, and the literary acceptance rate is not yet
measured.
