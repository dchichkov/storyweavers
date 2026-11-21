# rescue — entity event lines (seed 3000)

Sam wanted to eat the bread, but a puppy shivered on a high ledge. Sam told Mum, “The puppy needs help.” Mum told Sam, “Let me climb the ladder.” Sam told Mum, “I can steady the ladder.” Sam fetched the ladder from the shed, and he steadied the ladder. Mum climbed the ladder. She lifted the puppy down. Sam carried the puppy into the cottage, and he wrapped the puppy in the warm blanket. The puppy rested in the warm blanket.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## Mum (`helper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | listener | — | hero, target |
| 2: choose_ladder | frame.actor, listener, speaker | — | hero, target |
| 4: rescue_lift | frame.actor | — | hero, target, tool |

Context-only events: 6:ending.

## Sam (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.actor, speaker | — | helper, target |
| 2: choose_ladder | listener, speaker | — | helper, target |
| 3: prepare_ladder | destination_holder, frame.actor | — | target, tool |
| 4: rescue_lift | changed, concept.changed:Trust, destination_holder, frame.destination | memes: {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.65, 'Trust': 0.35, 'Joy': 0.1} → {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.65, 'Trust': 0.6499999999999999, 'Joy': 0.1} | helper, target, tool |
| 5: shelter | changed, concept.changed:Joy, frame.actor, moved, source_holder | location: garden → cottage; memes: {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.65, 'Trust': 0.6499999999999999, 'Joy': 0.1} → {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.65, 'Trust': 0.6499999999999999, 'Joy': 0.6} | target |

Context-only events: 6:ending.

## puppy (`target`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.patient | — | helper, hero |
| 2: choose_ladder | frame.patient | — | helper, hero |
| 3: prepare_ladder | frame.patient | — | hero, tool |
| 4: rescue_lift | changed, frame.patient, moved, state.add:safe, state.remove:stranded | location: ledge → hero; state: ['cold', 'frightened', 'shivering', 'stranded'] → ['cold', 'frightened', 'safe', 'shivering'] | helper, hero, tool |
| 5: shelter | changed, frame.patient, moved, state.add:warm, state.remove:cold, state.remove:frightened, state.remove:shivering | location: hero → blanket; state: ['cold', 'frightened', 'safe', 'shivering'] → ['safe', 'warm'] | hero |
| 6: ending | changed, frame.actor, frame.patient, state.add:resting | state: ['safe', 'warm'] → ['resting', 'safe', 'warm'] | — |

Context-only events: none.

## ladder (`tool`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 3: prepare_ladder | changed, frame.instrument, moved, state.add:steady | location: shed → hero; state: [] → ['steady'] | hero, target |
| 4: rescue_lift | frame.instrument | — | helper, hero, target |

Context-only events: 2:choose_ladder.
