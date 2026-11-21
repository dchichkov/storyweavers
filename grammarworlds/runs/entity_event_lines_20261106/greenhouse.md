# greenhouse — entity event lines (seed 3000)

Nia wanted to water the sunflower, but the tomato seedlings were thirsty. Mr Bell said, “The tap is broken.” The rain barrel held one can of water. Nia told Mr Bell, “I want to water the sunflower first.” Using the watering can, she watered the sunflower. The shade cloth fell. The tomato seedlings had a brown leaf. Nia secured the umbrella above the tomato seedlings with the garden tie. Mr Bell fixed the tap. Nia watered the tomato seedlings with water from the tap. Mrs Okafor fixed the shade cloth with the clip. Nia said, “I promise I'll water the tomato seedlings first tomorrow.” The brown leaf remained under the repaired shade cloth.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## rain barrel (`barrel`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 3: fill | changed, concept.changed:Water, frame.patient, state.add:empty, state.remove:one_can_of_water | memes: {'Water': 2} → {'Water': 0}; state: ['one_can_of_water'] → ['empty'] | can, hero |

Context-only events: none.

## watering can (`can`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: borrow | changed, frame.patient, moved | location: caretaker → hero | caretaker, hero |
| 3: fill | changed, concept.changed:Water, frame.instrument, state.add:full, state.remove:empty | memes: {'Water': 0} → {'Water': 2}; state: ['empty'] → ['full'] | barrel, hero |
| 5: water_first | changed, concept.changed:Water, frame.instrument, state.add:empty, state.remove:full | memes: {'Water': 2} → {'Water': 0}; state: ['full'] → ['empty'] | hero, sunflower |
| 9: refill | changed, concept.changed:Water, frame.instrument, state.add:full, state.remove:empty | memes: {'Water': 0} → {'Water': 2}; state: ['empty'] → ['full'] | hero, tap |
| 10: water_second | changed, concept.changed:Water, frame.instrument, state.add:empty, state.remove:full | memes: {'Water': 2} → {'Water': 0}; state: ['full'] → ['empty'] | hero, tomatoes |
| 12: return | changed, frame.patient, moved | location: hero → caretaker | caretaker, hero |

Context-only events: none.

## Mr Bell (`caretaker`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | speaker | — | hero |
| 2: borrow | source_holder | — | can, hero |
| 4: choose_flower | listener | — | hero |
| 8: repair_tap | frame.actor | — | tap |
| 12: return | destination_holder, frame.destination | — | can, hero |
| 13: ending | listener | — | hero, sunflower, tomatoes |

Context-only events: 10:water_second.

## clip (`clip`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 11: repair_shade | changed, frame.instrument, moved | location: owner → cloth | cloth, hero, owner, tie, umbrella |

Context-only events: none.

## shade cloth (`cloth`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 6: shade_break | changed, frame.actor, frame.patient, state.add:broken, state.remove:intact | state: ['intact'] → ['broken'] | leaf, tomatoes |
| 11: repair_shade | changed, frame.patient, state.add:repaired, state.remove:broken | state: ['broken'] → ['repaired'] | clip, hero, owner, tie, umbrella |

Context-only events: 7:secure, 13:ending.

## Nia (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.actor, listener | — | caretaker |
| 2: borrow | destination_holder, frame.actor, frame.destination | — | can, caretaker |
| 3: fill | frame.actor | — | barrel, can |
| 4: choose_flower | frame.actor, speaker | — | caretaker |
| 5: water_first | frame.actor | — | can, sunflower |
| 7: secure | frame.actor, source_holder | — | pot, tie, tomatoes, umbrella |
| 9: refill | frame.actor | — | can, tap |
| 10: water_second | frame.actor | — | can, tomatoes |
| 11: repair_shade | destination_holder | — | clip, cloth, owner, tie, umbrella |
| 12: return | frame.actor, source_holder | — | can, caretaker |
| 13: ending | changed, concept.changed:Care, frame.actor, speaker, state.add:promised_seedlings_first | memes: {'Care': 0.9, 'Desire': 0.7} → {'Care': 1, 'Desire': 0.7}; state: [] → ['promised_seedlings_first'] | caretaker, sunflower, tomatoes |

Context-only events: none.

## leaf (`leaf`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 6: shade_break | changed, state.add:brown, state.remove:green | state: ['green'] → ['brown'] | cloth, tomatoes |

Context-only events: 13:ending.

## Mrs Okafor (`owner`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 11: repair_shade | changed, frame.actor, moved, source_holder | location: outside → greenhouse | clip, cloth, hero, tie, umbrella |

Context-only events: none.

## pot (`pot`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 7: secure | frame.destination | — | hero, tie, tomatoes, umbrella |

Context-only events: none.

## sunflower (`sunflower`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 5: water_first | changed, concept.changed:Water, frame.patient, state.add:watered, state.remove:dry | memes: {'Water': 0} → {'Water': 2}; state: ['dry'] → ['watered'] | can, hero |
| 13: ending | changed, state.add:upright | state: ['watered'] → ['upright', 'watered'] | caretaker, hero, tomatoes |

Context-only events: 1:notice, 4:choose_flower, 6:shade_break.

## tap (`tap`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 8: repair_tap | changed, frame.patient, state.add:repaired, state.remove:broken | state: ['broken'] → ['repaired'] | caretaker |
| 9: refill | frame.patient | — | can, hero |

Context-only events: 1:notice, 10:water_second.

## garden tie (`tie`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 7: secure | changed, frame.instrument, moved | location: drawer → umbrella | hero, pot, tomatoes, umbrella |
| 11: repair_shade | changed, moved | location: umbrella → drawer | clip, cloth, hero, owner, umbrella |

Context-only events: none.

## tomato seedling (`tomatoes`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 6: shade_break | changed, state.add:brown_leaf, state.add:exposed | state: ['drooping', 'dry'] → ['brown_leaf', 'drooping', 'dry', 'exposed'] | cloth, leaf |
| 7: secure | changed, state.add:shaded, state.remove:exposed | state: ['brown_leaf', 'drooping', 'dry', 'exposed'] → ['brown_leaf', 'drooping', 'dry', 'shaded'] | hero, pot, tie, umbrella |
| 10: water_second | changed, concept.changed:Water, frame.patient, state.add:watered, state.remove:dry | memes: {'Water': 0} → {'Water': 2}; state: ['brown_leaf', 'drooping', 'dry', 'shaded'] → ['brown_leaf', 'drooping', 'shaded', 'watered'] | can, hero |
| 13: ending | changed, state.add:upright, state.remove:drooping | state: ['brown_leaf', 'drooping', 'shaded', 'watered'] → ['brown_leaf', 'shaded', 'upright', 'watered'] | caretaker, hero, sunflower |

Context-only events: 1:notice, 4:choose_flower.

## umbrella (`umbrella`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 7: secure | changed, frame.patient, moved, state.add:open, state.remove:closed | location: hero → pot; state: ['closed'] → ['open'] | hero, pot, tie, tomatoes |
| 11: repair_shade | changed, moved, state.add:closed, state.remove:open | location: pot → hero; state: ['open'] → ['closed'] | clip, cloth, hero, owner, tie |

Context-only events: none.
