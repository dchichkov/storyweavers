# kite — entity event lines (seed 3000)

Sam wanted to fly a kite, but the kite was torn. Sam said, “I would like to fix the kite.” Mum said, “The paper is thin.” Sam told Mum, “Let me cover the tear.” Using the tape, he covered the tear. He launched the kite in the wind, but the paper tore again. Sam said, “I want to make a sail.” Mum cut a small sail from the kite with the scissors. Sam tied the sail to the boat with the string. He placed the boat on the pond. Sam and Mum watched the boat. The boat sailed across the pond.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## boat (`boat`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 10: attach_sail | changed, frame.destination, state.remove:needs_sail | state: ['needs_sail'] → [] | hero, string, target |
| 11: launch_boat | changed, frame.patient, moved, state.add:sailing | location: meadow → pond; state: [] → ['sailing'] | hero |
| 12: ending | grammatical_subject | — | helper, hero, target |

Context-only events: none.

## Mum (`helper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | listener | — | hero, target |
| 2: inspect | speaker | — | hero, target |
| 3: choose_patch | listener | — | hero, target |
| 7: reconsider | listener | — | hero, target |
| 8: fetch_scissors | destination_holder, frame.actor | — | scissors |
| 9: cut_sail | frame.actor, grammatical_subject | — | scissors, target |
| 12: ending | grammatical_subject | — | boat, hero, target |

Context-only events: none.

## Sam (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.actor, grammatical_subject, speaker | — | helper, target |
| 2: inspect | frame.actor, listener | — | helper, target |
| 3: choose_patch | frame.actor, speaker | — | helper, target |
| 4: fetch_tape | destination_holder, frame.actor | — | target, tool |
| 5: mend | frame.actor, grammatical_subject | — | target, tool |
| 6: test_flight | changed, concept.changed:Curiosity, frame.actor, grammatical_subject | memes: {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.65, 'Trust': 0.35, 'Joy': 0.1} → {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.8, 'Trust': 0.35, 'Joy': 0.1} | target |
| 7: reconsider | frame.actor, speaker | — | helper, target |
| 10: attach_sail | frame.actor, grammatical_subject, source_holder | — | boat, string, target |
| 11: launch_boat | changed, concept.changed:Joy, frame.actor, grammatical_subject | memes: {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.8, 'Trust': 0.35, 'Joy': 0.1} → {'Care': 0.8, 'Fear': 0.35613833845891507, 'Curiosity': 0.8, 'Trust': 0.35, 'Joy': 0.5} | boat |
| 12: ending | frame.actor, grammatical_subject | — | boat, helper, target |

Context-only events: none.

## scissors (`scissors`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 8: fetch_scissors | changed, frame.patient, moved | location: basket → helper | helper |
| 9: cut_sail | frame.instrument | — | helper, target |

Context-only events: none.

## string (`string`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 10: attach_sail | changed, frame.instrument, moved | location: hero → boat | boat, hero, target |

Context-only events: none.

## kite (`target`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.patient, grammatical_subject | — | helper, hero |
| 2: inspect | frame.patient | — | helper, hero |
| 3: choose_patch | frame.patient | — | helper, hero |
| 4: fetch_tape | frame.patient | — | hero, tool |
| 5: mend | changed, frame.patient, state.add:repaired, state.remove:torn | state: ['fragile', 'grounded', 'torn'] → ['fragile', 'grounded', 'repaired'] | hero, tool |
| 6: test_flight | changed, frame.patient, state.add:torn, state.remove:repaired | state: ['fragile', 'grounded', 'repaired'] → ['fragile', 'grounded', 'torn'] | hero |
| 7: reconsider | frame.patient | — | helper, hero |
| 9: cut_sail | changed, frame.patient, renamed, state.add:sail, state.remove:grounded, state.remove:torn | noun: kite → sail; properties: ['flyable', 'portable'] → ['portable']; state: ['fragile', 'grounded', 'torn'] → ['fragile', 'sail'] | helper, scissors |
| 10: attach_sail | changed, frame.patient, moved, state.add:attached | location: meadow → boat; state: ['fragile', 'sail'] → ['attached', 'fragile', 'sail'] | boat, hero, string |
| 12: ending | frame.patient | — | boat, helper, hero |

Context-only events: none.

## tape (`tool`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 4: fetch_tape | changed, moved | location: basket → hero | hero, target |
| 5: mend | frame.instrument | — | hero, target |

Context-only events: none.
