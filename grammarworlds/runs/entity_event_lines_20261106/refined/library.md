# library — entity event lines (seed 3000)

Mina held a moon atlas. She wanted to sketch the moon. Jun said, “My whale book is missing.” Mina told Jun, “I promise to help you.” Mina and Jun searched the window nook, but Mina did not locate the whale book. Jun noticed the star bookmark on the high shelf. Ms Alvarez reserved the moon atlas for Mina. Using the ladder, Ms Alvarez lifted the whale book down. Ms Alvarez handed Jun the whale book. Jun said, “I can help you.” Jun opened the moon atlas for Mina. Mina sketched the moon from the moon atlas on the paper. Mina showed Jun the moon drawing.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## moon atlas (`atlas`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: wish | frame.patient | — | hero |
| 4: place_atlas | changed, frame.patient, moved | location: hero → desk | hero |
| 8: reserve_atlas | changed, frame.patient, state.add:reserved | state: ['moon_picture'] → ['moon_picture', 'reserved'] | helper, hero |
| 13: checkout_atlas | changed, frame.patient, moved, state.add:checked_out, state.remove:reserved | location: desk → hero; state: ['moon_picture', 'reserved'] → ['checked_out', 'moon_picture'] | helper, hero |
| 14: share_atlas | changed, frame.patient, state.add:open | state: ['checked_out', 'moon_picture'] → ['checked_out', 'moon_picture', 'open'] | friend, hero |

Context-only events: 17:sketch_moon, 18:ending.

## whale book (`book`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: missing | frame.patient | — | friend, hero |
| 10: retrieve | changed, frame.patient, moved, state.add:found, state.remove:missing | location: high_shelf → helper; state: ['missing', 'whale_picture'] → ['found', 'whale_picture'] | helper, ladder |
| 11: recognize | frame.patient | — | friend |
| 12: checkout | changed, frame.patient, moved, state.add:checked_out | location: helper → friend; state: ['found', 'whale_picture'] → ['checked_out', 'found', 'whale_picture'] | friend, helper |
| 18: ending | changed, frame.patient, state.add:open | state: ['checked_out', 'found', 'whale_picture'] → ['checked_out', 'found', 'open', 'whale_picture'] | hero |

Context-only events: 5:failed_search, 6:clue.

## star bookmark (`bookmark`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 6: clue | frame.patient | — | friend, tool |

Context-only events: 11:recognize.

## Jun (`friend`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: missing | frame.actor, listener, speaker | — | book, hero |
| 5: failed_search | grammatical_subject | — | hero, mitten, tool |
| 6: clue | frame.actor, grammatical_subject | — | bookmark, tool |
| 11: recognize | frame.actor | — | book |
| 12: checkout | destination_holder, frame.destination | — | book, helper |
| 14: share_atlas | changed, concept.changed:Care, frame.actor, grammatical_subject, speaker | memes: {'Care': 0.46560750590167027, 'Fear': 0.33233051531214985, 'Trust': 0.5274398506242907} → {'Care': 0.6656075059016703, 'Fear': 0.33233051531214985, 'Trust': 0.5274398506242907} | atlas, hero |

Context-only events: 7:request_help, 10:retrieve, 18:ending.

## Ms Alvarez (`helper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 7: request_help | frame.patient | — | hero |
| 8: reserve_atlas | grammatical_subject | — | atlas, hero |
| 9: fetch_ladder | frame.actor | — | ladder |
| 10: retrieve | destination_holder, frame.actor, frame.destination, grammatical_subject | — | book, ladder |
| 12: checkout | frame.actor, grammatical_subject, source_holder | — | book, friend |
| 13: checkout_atlas | frame.actor | — | atlas, hero |
| 16: return_ladder | frame.actor | — | ladder |

Context-only events: 3:borrow.

## Mina (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: wish | frame.actor, grammatical_subject | — | atlas |
| 2: missing | listener, speaker | — | book, friend |
| 3: borrow | destination_holder, frame.actor | — | tool |
| 4: place_atlas | frame.actor, source_holder | — | atlas |
| 5: failed_search | frame.actor, grammatical_subject | — | friend, mitten, tool |
| 7: request_help | frame.actor | — | helper |
| 8: reserve_atlas | frame.actor | — | atlas, helper |
| 13: checkout_atlas | destination_holder, frame.destination | — | atlas, helper |
| 14: share_atlas | listener | — | atlas, friend |
| 15: return_trolley | frame.actor, source_holder | — | tool |
| 17: sketch_moon | changed, concept.changed:Joy, frame.actor, grammatical_subject | memes: {'Care': 0.5833258768626751, 'Fear': 0.38736600615069816, 'Trust': 0.36835132413049776} → {'Care': 0.5833258768626751, 'Fear': 0.38736600615069816, 'Trust': 0.36835132413049776, 'Joy': 0.7} | paper, pencil |
| 18: ending | frame.actor, grammatical_subject | — | book |

Context-only events: 6:clue, 10:retrieve.

## ladder (`ladder`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 9: fetch_ladder | changed, frame.patient, moved | location: store → library | helper |
| 10: retrieve | frame.instrument | — | book, helper |
| 16: return_ladder | changed, frame.patient, moved | location: library → store | helper |

Context-only events: 18:ending.

## mitten (`mitten`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 5: failed_search | changed, frame.patient, moved | location: window_nook → tool | friend, hero, tool |

Context-only events: none.

## paper (`paper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 17: sketch_moon | changed, frame.patient, renamed, state.add:moon_drawing, state.remove:blank | noun: paper → drawing; state: ['blank'] → ['moon_drawing'] | hero, pencil |

Context-only events: 18:ending.

## pencil (`pencil`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 17: sketch_moon | frame.instrument | — | hero, paper |

Context-only events: none.

## book trolley (`tool`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 3: borrow | changed, frame.patient, moved | location: station → hero | hero |
| 5: failed_search | frame.instrument | — | friend, hero, mitten |
| 6: clue | frame.instrument | — | bookmark, friend |
| 15: return_trolley | changed, frame.patient, moved | location: hero → station | hero |

Context-only events: 4:place_atlas, 18:ending.
