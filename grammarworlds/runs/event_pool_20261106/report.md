# Event-pool retrieval experiment

A short structured brief now retrieves an authored event sequence along with
supporting entities and mechanics. The main test asks only for a reveal involving
a rabbit and a hat. It does not name the performer, spectator, wand, ribbon,
hutch, table, carrot, obstacle, recovery, or detailed event order.

The pool has five root recipes and six reusable subfragments. Three recipes are
variants of the newly authored hat story; two reuse the existing kite-repair and
moon-drawing ports. This is a bounded demonstration, not automatic extraction of
all seven existing grammarworlds.

## Transferred seed 0, actual generated text

Existing target entities are Ada, Teo, a brown rabbit, a velvet hat, a pen and a
desk. Ada is already declared capable of the portal action and this particular
hat has portal physics. The source's Merlin and June are not needed; missing
props are imported. The otherwise unrelated bell remains unchanged.

> Teo wanted to see a trick. The brown rabbit waited in the pen. Ada raised a velvet hat. Ada said, “I promise I'll show you a surprise.” She tapped the hat with the wand. The brown rabbit stayed in the pen. Teo spotted the tight ribbon around the hat. Ada untied the ribbon. With the wand, Ada tapped the hat again. The brown rabbit disappeared from the pen. Two ears appeared above the hat. Ada pulled the brown rabbit out of the hat. Teo laughed. Ada put the brown rabbit and the hat on the desk. She put the carrot beside the brown rabbit. The brown rabbit nibbled the carrot beside the open hat.

With an ordinary open hat and an actor without portal skill, the same concise
brief retrieves the stage mechanism. Teo closes his eyes, Ada places the rabbit
inside, and Teo opens his eyes before the shared reveal. There is no teleportation
or capability upgrade. The rabbit keeps its original entity ID in both cases.

## Iteration from reading samples

The first working version over-repeated “magician's hat,” used “June's eyes”
where “her eyes” was clearer, and allowed ears to appear before the spectator
reopened their eyes. The refined version adds a grounded short reference for
known hats, uses the existing typed possessive-pronoun construction, and includes
the spectator in the reveal's shared event/guards. Feeding now marks an offered
carrot first; the ending's nibbling event establishes the fed state.

Source flavor is intentionally allowed. The Merlinus variation retains the
source's June, hutch, wand, ribbon and carrot. Those defaults are logged instead
of being treated as facts deduced from the spelling of Merlinus.

## Results

Each setup uses seeds 0–19 with word attention off and on: **280 completed
samples**, all histories reconstructed and checked against final state.

| Setup | Completed | Distinct texts per 20, heads on | Event programs |
|---|---:|---:|---|
| Bare world, magical hat | 40/40 | 20 | Bound-hat obstacle/recovery |
| Existing Ada/Teo/rabbit/hat | 40/40 | 20 | Same program, rebound roles |
| Existing ordinary hat | 40/40 | 17 | Stage placement, shared reveal/ending |
| Merlinus with source flavor | 40/40 | 20 | Bound-hat program |
| Under-specified open hat | 40/40 | 19 | 11 stage / 9 magical selections per mode |
| Concise kite-flight goal | 40/40 | 14 | Four-event repair/flight chain |
| Concise drawing goal | 40/40 | 7 | Existing drawing scene |

Direct replay of the authored Merlin program and retrieval from the concise
brief produced identical text and final state in **40/40 paired comparisons**.
This is a control for loss introduced by retrieval, not independent evidence of
high prose quality: both execute the same authored program. No new Luna quality
judging was performed.

Word heads changed no distributions in the rabbit examples. They changed 30
word distributions in the kite condition. The new capability comes from
retrieved event structure, not improvements to word attention.

## Physical and structural checks

- 80 runs with removed portal physics, a misplaced wand, a non-calm rabbit, or
  missing accessible food blocked at the relevant event; reconstructed histories
  still matched their legal prefixes.
- Removing the ribbon entity violates the binding contract before replay.
- Disabling the pool produces an unresolved brief.
- Removing the recovery subfragment makes the bound-hat plan physically invalid;
  the planner does not silently pretend the hat was open.
- Existing rabbit/hat identities and initial states are preserved. No duplicate
  rabbit is created; unrelated entities remain unchanged.
- Nested fragment calls substitute roles explicitly and reject recursion,
  missing parameters, unknown primitives and overlong expansion.
- Trace-derived QA distinguishes teleportation from stage placement, explains
  the tied-ribbon obstacle, and checks the ending location and feeding state.

The full grammarworlds suite passes **154 tests**, including 14 event-pool tests.
The pool tests were rerun after the final forced-selection metadata refinement.

## Quality assessment and boundaries

The rabbit samples now have an explicit premise, dialogue, a physically motivated
setback/recovery where applicable, a reveal, and an ending that uses the actual
changed state. This is closer to an authored story than the earlier unordered
help/transfer loops. The known repeated-hat reference and spectator-order issues
were fixed after reading samples.

The prose is still simple and somewhat sequential; the stage version has less
of a turn than the blocked magical version. The drawing recipe is a scene, not
a complete story. Distinct wording does not imply broad plot diversity.

Retrieval uses authored signatures and weights, not learned similarity.
Mechanics and source fragments are reviewed authored exports. Existing local
role ambiguities can still require an explicit binding, and one brief selects
one root recipe. Broader multi-recipe composition and selecting fragments by
a softer overlap of events/state transitions are the next extensions.
