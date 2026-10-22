# Manual review — cache optimization

Reviews are not blinded. Readings compare prose with recorded state; automatic
quality scores alone do not prove grounding.

## Low-reasoning development pilot

Night garden, seeds 1000, 1001, 1002: complete openings and warm imagery, with
an intelligible desire to welcome a shy visitor. Still too many small narrated
bookkeeping steps. Seed 1000 begins with breezy weather, but a later shared
lighting card claims “the air was quiet.” The card should not assert a wind
condition absent from its evidence. Several Move cards describe carrying the
object even though Move itself changes only the object's location. These are
remaining semantic defects, not failures of the JSON guards. This pilot was
stopped for poor mechanics acceptance before its planned evaluation.

## First ten-world trial (compact_cached_v2)

Pond concert, seed 1000: a clear wish and an actual invitation/performance,
with concrete objects and playful dialogue (the floating stage resembles a
runaway pancake). Still a sequence of many setup actions. Move cards narrate
carrying although neither child has a tracked location. Pip performs in the
English while the final state records pip.joined=false and pip.heard_music=true;
the scene may describe Pip as a performer without a matching participation
flag. This needs an explicit distinction between performing and audience
participation, or better prose entailment. The recipient response and wind
branch are otherwise consistent with the inspected trace.

Night garden, seed 1000: a complete warm welcome with a particular guest and an
ending image. The opening connects Ada's unknown knowledge of the moth's wish
to a plan for an extra performer; that causal wording is premature. Several
phrases expose setup mechanics (“careful protection,” “ready lamp”), but the
state-driven change in light and guest participation is readable. The ending
correctly keeps the invitation with the moth; the lamp remains on loan and the
story does not falsely claim it was returned. Borrowing versus legal ownership
is still somewhat muddled by the model's prose and the runtime owner slot.


Hill picnic, seed 1000: a specific shared-lunch goal, a stubborn donkey, and a
visible shift from pride to patience. Stronger character-driven turn than the
other inspected cases. The closing repeats the calming beat instead of showing
a fresh final image. The carrot is a prose detail whose physical availability
is not established in the inspected state; carrying locations remain thin.

Puppet weather, seed 1000: a compact complete performance with a quiet audience,
wind protection and a timid performer becoming steady. Readable and warm but
formulaic, with repeated curtain/breeze wording. The final invited=false flag
is not automatically a contradiction because Mina is already nearby; the story
should not claim an invitation occurred. The inspected text does not do so.

## Frozen-mechanics prose comparisons

Both original worlds (library_parade and pond_concert) were reused without paid
mechanics generation. Three original traces per world replayed exactly before
evaluation. Every comparison used the same ten uniform sample positions per
world. English is newly generated; grades are stochastic, not blinded human
ratings.

Factored v1: library sample 57 has Nell wanting to join, followed by observation
and communication cards saying she wants quiet. The original sample 57 preserves
join correctly. Pond prose sometimes calls windy water still. These are real
condition-selection/English-entailment failures despite the same world trace.
The 6.65/9 result is not accepted for its 63.7% lower prose-authoring price.

Factored v2: restoring conditions and using medium reasoning fixes the inspected
library join branch. It has warm details: the cart squeaks as if it has a library
card; the mayor's eyebrows become two surprised bookmarks. It promises return of
the cart although the goal ends before a return, and retains a lot of narrated
bookkeeping. The 7.50/9 result remains below the user's 7.75 target.

Full v1: library sample 57 again preserves join and has a coherent invitation
and ending. The crab-like damaged cart is a pleasing recurring image. It still
states the cart temporarily “belonged” to Ada and describes owned library books
as gifts; some awkwardness is inherited from the world's ownership model. An
observation paragraph (“understood exactly what had been delivered”) reads as a
ledger update. The aggregate 7.30/9 does not reproduce the historical benchmark.
This rerun includes the pre-existing stronger ending guards added after the
historical baseline; it is not an exact-byte historical prompt replay.

Decision: preserve the original benchmark and use request-preserving cache-only
transport by default. Do not claim that fuller context guarantees any particular
score, or select new stories by repeatedly sampling until their grades improve.

## Final ten-world trial (compact_cached_v3), initial readings

Roof-post, seed 1000: a complete, playful delivery story (“No paper butterflies”)
with a specific windy transport choice. It now succeeds mechanically without a
repair. The ending invents Pip's return flight, and the Move primitive still
leaves the dragon's recorded location unchanged while prose describes carrying.
This is `unrecorded_action` / `carrier_location_drift`, not resolved by caching.

Library parade, seed 1000: clear preparation, greeting and a warm ending; the
wind changes real cart decoration, and the recipient's wishes matter. Several
observations/tellings read as a checklist, and an entire paragraph only confirms
receipt. The books remain at location=library while prose transports them in the
cart to Mina. The engine needs containment/co-location semantics before claiming
physical grounding; loading a container is not yet an automatic contents move.

Pond concert, seed 1000: a real borrowed ribbon is returned, and a quiet listener
changes the musical choice. However a drum-movement card contains the Korean
word “공연” followed by an English self-correction, an unrequested language
switch. Several lending phrases (“without pretending it belonged to her”) sound
like an ownership audit. This is evidence that full context alone does not solve
Luna's literary/grounding errors.

Night garden, seed 1000: the welcome has a clear signal and response, but its
breezy opening becomes a “still garden” later. More seriously, the shade is
returned before the lamp is switched on, while prose says the covered lamp
continues shining. The frame allows removing ownership without clearing the
covered state; the text adds premature light. Record both physical and narrative
causality failures; passing state assertions is insufficient.

Bakery, seed 1000: the wish, changed flavor, corrected label and gift make a
complete causal arc. Merely adding spice cannot generally turn a sweet cake
savory; the physical transition is simplistic. The ending's “Ada's cake” after
transfer is ambiguous, and the exchange/return promise is not completed.

Museum, seed 1000: warm specific objects and a considerate visitor arrangement,
with loans that really return to their owners. The ending repeats the return
beats and places Pip on the roof although the ribbon's final location is still
museum. Visitor comfort is mostly described as a result, with little difficulty
to make the resolution feel earned.

Hill picnic, seed 1000: an appealing pride-to-help turn, with “heavier than my
best boast” and the elephants/basket callback. But Dapple's capacity=3 and the
basket weight=4 become “three carrying spaces,” an odd literal rendering of an
abstract capacity value. Actor locations remain hill_base while prose has them
at the meadow. Keep the warmth while improving physical meaning and reducing
inventory/ownership narration.

Clocktower, seed 1000 and judged samples 29/57: the premise explicitly contrasts
one and three bell rings, but the modular ringing card always describes a single
tap/note. The investigated/corrected signal is then not realized in the English.
“Nia noticed that she wanted to join” and “her awake face” are awkward renderings
of introspection and booleans. The judge's 4.90 mean is a meaningful failure of the
central story, not a reason to exclude it from the batch mean.

## Fresh-seed verification

Seven of the eight completed generators pass 100 new seeds and pinned replay.
Bakery fails closed on a newly reached ending state: the guarded common evidence
for its ending has a different incidental knowledge value. The 100 authoring
samples did not cover this ordering. Keep its generated/judged samples in the
trial totals, but quarantine it for unrestricted generation. Do not weaken the
ending guards or silently give it an ungrounded fallback paragraph.
