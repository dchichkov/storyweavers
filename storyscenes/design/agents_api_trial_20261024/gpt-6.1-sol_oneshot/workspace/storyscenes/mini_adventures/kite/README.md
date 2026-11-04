# The Space Beside the Reel

Offline story-first pack for ingredient seed 2026102401. The reference is preserved separately from the shorter executable scenes. No execution tools were available in this single-response authoring run: tests, integration check, word-count measurement, and first-draw runtime inspection are UNEXECUTED. No bundle artifact was written to disk; this response is the bundle.

## Run

From the repository root:

    python -m storyscenes.mini_adventures.kite.world --seed 2026102401 --scenes 8
    python -m unittest storyscenes.mini_adventures.kite.test_world
    python check_pack.py .

The supplied integration check is untouched. The pack can be imported directly; shared inventory discovery is not modified.

## Explicit ending recipes

    from storyscenes.mini_adventures.kite.world import Parameters, generate
    print(generate(0, count=7, params=Parameters(wind=1, gentle=True, frayed=True, mend=True))['story'])
    print(generate(0, count=8, params=Parameters(wind=0, gentle=True, frayed=True, mend=True))['story'])

The first recipe reaches `ending_air` / `shared_flight`. The second reaches `ending_table` / `shared_table`. Wind 2, a forceful invitation (`gentle=False`), or an unrepaired fray (`frayed=True, mend=False`) also prevents shared flight. A sound initial line does not require mending. Wind values mean calm, steady breeze, and unsafe gusts respectively.

Six required encounters plus one or two optional vignettes produce exactly seven or eight scenes. Seeded bounded DFS chooses the optional selection and order. Replay returns JSON-native episode dictionaries identical to generation. All local effects use the supplied LocalPlay. Failed candidates are detached; rejected search branches are never narrated.

Persistent effects include early line repair enabling flight, invitation style changing Ivo's participation, and paid-out string requiring winding before return. Deferred repair is explicitly enacted with Nan on return, not silently granted. Both endings finish a shared activity; the table ending acknowledges the failed flight rather than promising success tomorrow.

## Limits

This is a symbolic physical model, not aerodynamic simulation. The group travels together; the kite remains carried by Mara except during the abstracted flight. Incidental gestures, tools and paper scraps are prose details, not inventory objects. Flight distance, line length and tail snags from the longer reference are not simulated. Four consequential parameters and two optional observations offer a small family of stories, not unlimited diversity. Eight-scene stories contain both vignettes; seven-scene stories contain one. Tests include 200 requested routes, replay and event validation through the shared verifier, invalid input, atomic rejection, continuity, optional omission and paired counterfactuals, but their results are not claimed here.
