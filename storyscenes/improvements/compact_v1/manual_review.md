# Manual reading of the compact-authoring comparison

These are post-run, non-blind readings, separate from the unchanged Terra/Flex
set judge. I read two different recorded outcomes from each completed theater in
each pipeline, then inspected their event changes where the prose looked wrong.
The exact seed IDs below reproduce the samples. Neither pipeline's measured
stories were edited to improve these observations.

## Control: library_parade, seeds 1000 and 1001

The covered-books route has a recognizable turn: the mayor discovers that the
decorations are books, and his boast turns into a useful parade. It contains
pleasant images and dialogue. However, seed 1000's opening already says Juniper
identifies the books; the next observation repeats that discovery. The book-rain
scene puts the crowd in the square before the cart actually moves there.

The quiet-reader route is warm, but the ribbon-selection card already describes
Pip rolling silently, followed by a second actual rolling scene. Its ending then
repeats the walking-library image. The facts and action boundaries need tighter
coordination even though the final scalar outcome is correct.

## Control: pond_concert, seeds 1000 and 1001

The frog's dialogue is playful, especially the moonbeam croak and frog-sized
microphone. The quieter route has a substantial mistaken-belief correction.
It is also long and sequential, with repeated performance descriptions.

In seed 1000, the Golden Pebble supposedly lands in Jojo's hands during the
performance, but it belonged to Jojo initially and no transfer occurs. In seed
1001, Pip trades a prize that belongs to Jojo, without a preceding transfer to
Pip. This is a simulation-level ownership problem hidden inside a custom Act.
The shared Transfer precondition would have prevented it. The observed preference
is only likes_music=true, while the prose supplies a more specific gentle-music
preference. These are material grounding defects despite readable English.

## Compact: library_parade, seeds 1000 and 1001

The loose-cover, damaged-cart and quiet-reader constraints combine into a clear
delivery, followed by the mayor redirecting his ambition into a quiet procession.
The repaired wheel, tied cover and final book ownership make the consequences
more concrete than the control's loosely ordered display scenes. The pigeons
needing tickets and the cart that should not gallop like a goat provide warmth
and humor without replacing the causal work.

There is still procedural narration: several inspection/communication actions
are concatenated into a large bridge paragraph. Some lines name observations too
literally, such as the wind being “breezy.” Ownership language also slips in the
ending's “Ada's cart” even though it is borrowed from Bram. This is a reminder
that validated guards do not prove every free English phrase.

## Compact: pond_concert, seeds 1000 and 1002

The invitation, neighbor's wish and weather interact through the shared state.
The miniature drum, polite notes and anchored lily pad give the stories distinct
physical images. The ending-group change retains the actual outcome while
removing many versions driven only by incidental knowledge.

A repeated library limitation is visible: Move changes the prop's location but
not its carrier's. In seed 1000, prose says Ada carries the invitation from the
garden to the porch. The trace only moves invitation.location; a later action
then moves ada.location to the porch. Object motion and accompanying actor motion
need an explicit carrying operation, or prose that correctly describes moving
the object while remaining behind. The current test validates the declared
effects, not full physical realism.

The concert can also finish before the invitation is delivered. This is legal
under the authored guards, but it weakens the premise's apparent causal order.
The delivery-completion card is an event log rather than a scene. Finally,
pad_secured differs between these two samples while the primary plot remains a
quiet concert. Mechanical outcome counts must not be equated with distinct plots.

## Failed roof-post attempts

The control failed after six bounded mechanics patches, principally around
inconsistent dotted entity IDs and state keys. The compact draft hit its 5,500
output-token cap. A 575-token suffix completed the JSON, but the recovered draft
still needed schema/identity repairs and never reached a valid goal after six
small patches. All of these recovered-draft tokens are included in the final
compact comparison. Neither failure was hidden by a stronger-model rewrite.

## Interpretation

The measured reduction is 24.93% in output tokens including failed drafts and
all explicit recovery attempts: 27,671 control versus 20,773 compact. The common
two-world quality mean rises from 6.75 to 7.75/9. Completion remains 2/3 in both
pipelines. This supports the smaller authoring interface as a useful direction,
not a claim that the prototype is ready to generate 20,000 accepted worlds.

The next useful gates are carrying/location consistency, knowledge-specific
claims in English, causal ordering of promised events, and diversity measured
as materially different plots. Fix these in shared mechanics and authoring
contracts, then repeat a larger matched trial before changing scale estimates.
