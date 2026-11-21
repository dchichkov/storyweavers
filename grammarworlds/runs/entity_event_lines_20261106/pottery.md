# pottery — entity event lines (seed 3000)

Bea said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len said, “I could hold a bowl with two hands.” Bea said, “I would like a thumb rest.” Using the sponge, Bea shaped the dent into a thumb rest. Mr Ivo fired the cup twice. The cup was cool. Bea handed the cup to Grandpa Len. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.

## bench (`bench`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 10: return_sponge | frame.destination | — | hero, sponge |
| 16: unload_bisque | frame.destination | — | cup, helper |

Context-only events: none.

## glaze (`blue_glaze`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 17: glaze | frame.instrument | — | cup, hero |

Context-only events: none.

## cup (`cup`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: goal | frame.patient | — | grandpa, helper, hero |
| 3: shape | changed, frame.patient, state.add:shaped | state: ['stable', 'thick', 'wet', 'wide_handle'] → ['shaped', 'stable', 'thick', 'wet', 'wide_handle'] | hero, tool |
| 4: slip | changed, frame.patient, state.add:dented | state: ['shaped', 'stable', 'thick', 'wet', 'wide_handle'] → ['dented', 'shaped', 'stable', 'thick', 'wet', 'wide_handle'] | hero, tool |
| 5: inspect | frame.patient | — | helper, hero |
| 6: consult | frame.patient | — | grandpa, hero |
| 8: thumb | changed, frame.patient, state.add:safe_edges, state.add:thumb_rest, state.add:wall_checked | state: ['dented', 'shaped', 'stable', 'thick', 'wet', 'wide_handle'] → ['dented', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wet', 'wide_handle'] | helper, hero, sponge |
| 11: shelve | changed, frame.patient, moved | location: bench → shelf | hero, shelf |
| 12: dry | changed, frame.actor, frame.patient, state.add:dry, state.remove:wet | state: ['dented', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wet', 'wide_handle'] → ['dented', 'dry', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | shelf |
| 13: load_bisque | changed, frame.patient, moved | location: shelf → kiln | helper, kiln |
| 14: bisque | changed, frame.patient, state.add:bisque, state.add:hot | state: ['dented', 'dry', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'dented', 'dry', 'hot', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | helper, kiln |
| 15: cool_bisque | changed, frame.actor, frame.patient, state.add:cool, state.remove:hot | state: ['bisque', 'dented', 'dry', 'hot', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'cool', 'dented', 'dry', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | kiln |
| 16: unload_bisque | changed, frame.patient, moved | location: kiln → bench | bench, helper |
| 17: glaze | changed, frame.patient, state.add:blue, state.add:glazed | state: ['bisque', 'cool', 'dented', 'dry', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'blue', 'cool', 'dented', 'dry', 'glazed', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | blue_glaze, hero |
| 18: load_final | changed, frame.patient, moved | location: bench → kiln | helper, kiln |
| 19: fire | changed, frame.patient, state.add:fired, state.add:hot, state.remove:cool | state: ['bisque', 'blue', 'cool', 'dented', 'dry', 'glazed', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'blue', 'dented', 'dry', 'fired', 'glazed', 'hot', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | helper, kiln |
| 20: cool_final | changed, frame.actor, frame.patient, state.add:cool, state.remove:hot | state: ['bisque', 'blue', 'dented', 'dry', 'fired', 'glazed', 'hot', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'blue', 'cool', 'dented', 'dry', 'fired', 'glazed', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | kiln |
| 21: deliver | changed, frame.patient, moved | location: kiln → hero | helper, hero |
| 22: give | changed, frame.patient, moved | location: hero → grandpa | grandpa, hero |
| 23: use | changed, frame.patient, state.add:tea | state: ['bisque', 'blue', 'cool', 'dented', 'dry', 'fired', 'glazed', 'safe_edges', 'shaped', 'stable', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] → ['bisque', 'blue', 'cool', 'dented', 'dry', 'fired', 'glazed', 'safe_edges', 'shaped', 'stable', 'tea', 'thick', 'thumb_rest', 'wall_checked', 'wide_handle'] | grandpa, teapot |
| 24: ending | frame.patient | — | grandpa |

Context-only events: 7:fetch_sponge.

## Grandpa Len (`grandpa`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: need | frame.actor | — | old_mug |
| 2: goal | frame.destination | — | cup, helper, hero |
| 6: consult | frame.actor, speaker | — | cup, hero |
| 22: give | destination_holder, frame.destination | — | cup, hero |
| 23: use | frame.actor | — | cup, teapot |
| 24: ending | changed, frame.actor, state.add:thumb_in_rest | state: ['stiff_hand'] → ['stiff_hand', 'thumb_in_rest'] | cup |

Context-only events: none.

## Mr Ivo (`helper`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: goal | listener | — | cup, grandpa, hero |
| 5: inspect | frame.actor, speaker | — | cup, hero |
| 8: thumb | listener | — | cup, hero, sponge |
| 9: return_rib | destination_holder, frame.destination | — | hero, tool |
| 13: load_bisque | frame.actor | — | cup, kiln |
| 14: bisque | frame.actor | — | cup, kiln |
| 16: unload_bisque | frame.actor | — | bench, cup |
| 18: load_final | frame.actor | — | cup, kiln |
| 19: fire | frame.actor | — | cup, kiln |
| 21: deliver | frame.actor | — | cup, hero |

Context-only events: none.

## Bea (`hero`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 2: goal | frame.actor, speaker | — | cup, grandpa, helper |
| 3: shape | frame.actor | — | cup, tool |
| 4: slip | frame.actor | — | cup, tool |
| 5: inspect | listener | — | cup, helper |
| 6: consult | listener | — | cup, grandpa |
| 7: fetch_sponge | changed, destination_holder, frame.actor, frame.destination, state.add:hoped_to_smooth | state: [] → ['hoped_to_smooth'] | sponge |
| 8: thumb | frame.actor, speaker | — | cup, helper, sponge |
| 9: return_rib | frame.actor, source_holder | — | helper, tool |
| 10: return_sponge | frame.actor, source_holder | — | bench, sponge |
| 11: shelve | frame.actor | — | cup, shelf |
| 17: glaze | frame.actor | — | blue_glaze, cup |
| 21: deliver | destination_holder, frame.destination | — | cup, helper |
| 22: give | frame.actor, source_holder | — | cup, grandpa |

Context-only events: none.

## kiln (`kiln`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 13: load_bisque | frame.destination | — | cup, helper |
| 14: bisque | frame.instrument | — | cup, helper |
| 15: cool_bisque | frame.instrument | — | cup |
| 18: load_final | frame.destination | — | cup, helper |
| 19: fire | frame.instrument | — | cup, helper |
| 20: cool_final | frame.instrument | — | cup |

Context-only events: none.

## mug (`old_mug`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 1: need | frame.patient | — | grandpa |

Context-only events: none.

## shelf (`shelf`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 11: shelve | frame.destination | — | cup, hero |
| 12: dry | frame.destination | — | cup |

Context-only events: none.

## sponge (`sponge`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 7: fetch_sponge | changed, frame.patient, moved | location: bench → hero | hero |
| 8: thumb | frame.instrument | — | cup, helper, hero |
| 10: return_sponge | changed, frame.patient, moved | location: hero → bench | bench, hero |

Context-only events: 24:ending.

## teapot (`teapot`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 23: use | changed, frame.instrument, state.remove:tea | state: ['tea'] → [] | cup, grandpa |

Context-only events: none.

## shaping rib (`tool`)

| Event | Tags | Own changes | Shared with |
|---|---|---|---|
| 3: shape | frame.instrument | — | cup, hero |
| 4: slip | frame.instrument | — | cup, hero |
| 9: return_rib | changed, frame.patient, moved | location: hero → helper | helper, hero |

Context-only events: 24:ending.
