# music — entity event lines (seed 3000)

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Mateo. Nia said, “I need an answering beat.” Mateo told Nia, “I am not ready for the audience.” Nia said, “I'll perform a solo.” Nia rehearsed a soft beat and a loud beat. Nia played the solo on the little drum before Dalia. Mateo clapped. Nia bowed.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## little drum (`drum`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: borrow | changed, frame.patient, moved | location: shelf → hero | hero |
| 7: perform | frame.instrument | — | hero |
| 9: return | changed, frame.instrument, frame.patient, moved | location: hero → shelf | hero |

Context-only events: 6:prepare_solo.

## Nia (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: opening | frame.actor | — | — |
| 2: borrow | destination_holder, frame.actor, frame.destination | — | drum |
| 3: invite | frame.actor, speaker | — | partner |
| 4: decline | listener | — | partner |
| 5: choose_solo | changed, frame.actor, speaker, state.add:accepted_boundary | state: ['wants_duet'] → ['accepted_boundary', 'wants_duet'] | partner |
| 6: prepare_solo | changed, frame.actor, state.add:loud_beat, state.add:practiced, state.add:soft_beat | state: ['accepted_boundary', 'wants_duet'] → ['accepted_boundary', 'loud_beat', 'practiced', 'soft_beat', 'wants_duet'] | program |
| 7: perform | changed, frame.actor, state.add:performed_solo | state: ['accepted_boundary', 'loud_beat', 'practiced', 'soft_beat', 'wants_duet'] → ['accepted_boundary', 'loud_beat', 'performed_solo', 'practiced', 'soft_beat', 'wants_duet'] | drum |
| 8: response | changed, concept.changed:Joy, state.add:bowed | memes: {'Care': 0.8, 'Desire': 0.85, 'Fear': 0.29368300307534906} → {'Care': 0.8, 'Desire': 0.85, 'Fear': 0.29368300307534906, 'Joy': 0.8}; state: ['accepted_boundary', 'loud_beat', 'performed_solo', 'practiced', 'soft_beat', 'wants_duet'] → ['accepted_boundary', 'bowed', 'loud_beat', 'performed_solo', 'practiced', 'soft_beat', 'wants_duet'] | partner |
| 9: return | frame.actor, source_holder | — | drum |
| 10: ending | frame.actor | — | — |

Context-only events: none.

## Mateo (`partner`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 3: invite | frame.patient, listener | — | hero |
| 4: decline | changed, frame.actor, speaker, state.add:declined_public | state: ['public_unready'] → ['declined_public', 'public_unready'] | hero |
| 5: choose_solo | listener | — | hero |
| 8: response | changed, concept.changed:Trust, frame.actor, state.add:applauded | memes: {'Trust': 0.4122342160869985, 'Fear': 0.6589448461157755, 'Readiness': 0.1} → {'Trust': 0.6122342160869985, 'Fear': 0.6589448461157755, 'Readiness': 0.1}; state: ['declined_public', 'public_unready'] → ['applauded', 'declined_public', 'public_unready'] | hero |

Context-only events: 2:borrow, 7:perform.

## signup sheet (`program`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 6: prepare_solo | changed, frame.patient, state.add:solo | state: [] → ['solo'] | hero |

Context-only events: none.
