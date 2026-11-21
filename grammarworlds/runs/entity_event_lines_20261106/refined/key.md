# key — entity event lines (seed 3000)

Sam wanted to read a storybook inside, but the door was locked. The key was missing. Mum said, “I could help you.” Sam told Mum, “I would like to locate the key.” He fetched the lantern from the porch. Using the lantern, he found the key under the bench. He unlocked the door with the key. He stepped inside the cottage. He hung the key on the hook. Sam opened the storybook beside Mum.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## door (`door`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | grammatical_subject | — | hero, target |
| 6: unlock_original | changed, frame.patient, state.add:open, state.remove:locked | state: ['locked'] → ['open'] | helper, hero, target |

Context-only events: none.

## Mum (`helper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: offer_help | frame.actor, speaker | — | hero, target |
| 3: choose_search | listener | — | hero, target |
| 6: unlock_original | changed, moved | location: courtyard → cottage | door, hero, target |

Context-only events: 8:ending.

## Sam (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.actor, grammatical_subject | — | door, target |
| 2: offer_help | listener | — | helper, target |
| 3: choose_search | frame.actor, speaker | — | helper, target |
| 4: fetch_light | destination_holder, frame.actor, grammatical_subject | — | target, tool |
| 5: find_key | destination_holder, frame.actor, frame.destination, grammatical_subject | — | target, tool |
| 6: unlock_original | changed, frame.actor, grammatical_subject, moved | location: courtyard → cottage | door, helper, target |
| 7: hang_key | frame.actor, grammatical_subject, source_holder | — | target |
| 8: ending | changed, frame.actor, grammatical_subject, state.add:reading | state: [] → ['reading'] | storybook |

Context-only events: none.

## storybook (`storybook`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 8: ending | changed, frame.patient, state.add:open | state: [] → ['open'] | hero |

Context-only events: 1:notice.

## key (`target`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: notice | frame.patient, grammatical_subject | — | door, hero |
| 2: offer_help | frame.patient | — | helper, hero |
| 3: choose_search | frame.patient | — | helper, hero |
| 4: fetch_light | frame.patient | — | hero, tool |
| 5: find_key | changed, frame.patient, moved, state.add:found, state.remove:hidden, state.remove:lost | location: under bench → hero; state: ['hidden', 'lost'] → ['found'] | hero, tool |
| 6: unlock_original | frame.instrument | — | door, helper, hero |
| 7: hang_key | changed, frame.patient, moved | location: hero → hook | hero |

Context-only events: 8:ending.

## lantern (`tool`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 4: fetch_light | changed, moved | location: porch → hero | hero, target |
| 5: find_key | frame.instrument | — | hero, target |

Context-only events: none.
