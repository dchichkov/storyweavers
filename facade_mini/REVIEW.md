# Expanded prototype review — October 24, 2026

This is the implementing agent's review, not an independent literary evaluation.
The second pass expanded both authored material and the ways the guest can
change the evening. The original delivery is preserved in `versions/v1/`.

## What changed

| Loaded inventory | First delivery | Expanded delivery |
| --- | ---: | ---: |
| Sequenced short beats | 8 | 27 |
| Within-beat goals | 23 | 80 |
| Ending categories | 5 | 8 |
| Performance slots | 66 | 183 |
| Unique authored lines | 130 | 422 |

The expanded library contains 6,004 words across unique loaded lines, 11 public
topics with 30 tiers, eight private content units, and 15 social-exchange
bindings. Dynamic interaction prose is excluded. These are inventory measures,
not estimates of authoring effort or equivalents to Façade's production beats.

The most material improvement is causal range. Constructive outcomes now have
four demonstrated approaches: direct mediation, giving the hosts room to initiate
their own conversation, supporting private confidences and voluntary disclosure,
and negotiating practical commitments. The initiative route uses neither
`reflect` nor `mediate`. The practical route uses neither empathy nor reflection.
The hosts' responsibility and knowledge still constrain what is possible.

Private conversations update only the people present. A promise can be kept or
broken; betrayal changes the remaining arc and survives an apology. Apologies
address particular offenses, allowing a new repair after a new offense without
letting repeated apologies accumulate trust. Aftermath scenes enact changes in
the room before the ending: papers move, dates are marked, terms are written,
and an overnight bag can be prepared.

## Final verification

- **35 tests passed**, including audience boundaries, private conversation tiers,
  voluntary disclosure, betrayal, offense-specific apologies, distinct successful
  routes, late interruptions, exact replay, and local HTTP integration.
- **1,000 development sessions** passed on the final source: seeds 0–499 under
  each of two policies. All 27 beats were selected across the curious-policy run.
- **400 reserved sessions** passed: seeds 1000–1199 under each policy. This range
  was declared in `DEVELOPMENT.md` before the final repairs.
- Every audited session terminated within 48 accepted moves, satisfied world
  invariants and private audience checks, and reproduced its complete exported
  record under exact replay.
- Eleven scripted examples witness all eight ending categories. The direct
  mediation and distrust scripts differ in just two early choices: empathy
  becomes blame. Their identical later intervention yields repair versus an
  unresolved evening, with different selected scenes.
- A fresh standalone copy ran from an unrelated working directory. Four saved
  traces replayed in fresh processes; a partial private conversation resumed
  through return and departure.
- The browser was inspected visually and exercised through private conversation
  controls. HTTP tests cover save/load and separate browser sessions. The native
  browser file chooser itself was not automated. A screenshot is saved as
  `player-preview.png`.

| Final run | Sessions | Repair | Practical | Separate | Other endings | Failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Development, broad | 500 | 5 | 0 | 0 | 495 | 0 |
| Development, curious | 500 | 26 | 0 | 2 | 472 | 0 |
| Reserved, broad | 200 | 3 | 0 | 0 | 197 | 0 |
| Reserved, curious | 200 | 14 | 0 | 0 | 186 | 0 |

The broad policy randomly chooses supported actions, with extra weight for
listening. The curious policy excludes departure and provocation and also weights
listening. These are synthetic policies, not estimates of human experience.
Random traversal did **not** find the practical ending; its scripted witness
proves reachability, not discoverability. Separation remains rare. The original
prototype had no random repairs, but its action space differs, so that comparison
is not a controlled improvement rate. Exact transcripts and beat paths are not
counts of independently good stories.

Detailed reports and the final source snapshot are in `reviews/release/`.
The earlier failed audit is retained separately rather than replaced.

## Two reading and repair rounds

Round 1 preserved all eleven demonstrations and curious-policy seeds 0, 17, and
41. Full readings of the private, practical, betrayal, and separation routes and
the three random samples exposed several failures of dramatic continuity:

- Betrayal could be followed by a sweet memory or a companionable dinner. It now
  urgently interrupts the topic and leads to a distinct crisis and aftermath.
- Closing dialogue could reopen a decision already made. Closing variants now
  acknowledge the existing agreement or boundary.
- Direct responsibility prompts could repeat a host's spontaneous admission as
  though it were new. Accountability now selects an acknowledgment.
- Re-entry could mention an unintroduced brush roll. The replacement refers to
  the interrupted conversation; physical state and key movement were also checked.
- Silence in the kitchen repeated one gesture. It now advances toward returning
  to the table, and apologies distinguish judgment from betraying confidence.

Round 2 read the revised betrayal, initiative, silent, practical, and random
seed-17 transcripts in full. The practical route now ends with budget and
calendar commitments rather than generic affection. The initiative route gives
the hosts a sustained exchange with one another. Betrayal persists through the
ending instead of being erased by a social repair command.

The second curious traversal also exposed **five crashes in 500 sessions**
(seeds 146, 181, 235, 386, 435). A late betrayal interrupted a closing beat that
the director then tried to select again. The repair completes the evening from
the new crisis and aftermath without replaying consumed closing goals. A focused
test and all five failing seeds are now regressions. The original failures remain
in `reviews/round2/curious.json`; the final recheck is in `reviews/release/`.

The second reading motivated knowledge-aware reminder variants for family
history, reduced work hours, artistic ambitions, refund terms, and travel dates.
The same information can arrive through a question or a scene; it should not
always sound like a first revelation. A browser JavaScript syntax error also
escaped the HTTP tests and was caught by the actual visual check, then fixed.
Frozen source and transcripts accompany both rounds.

## What this experiment does and does not establish

This is a substantially larger working text drama, with state-based variation,
reusable social exchanges, private knowledge, and persistent consequences. The
second pass occupied approximately one hour of elapsed implementation and review
time. That is not a measurement of human-equivalent labor or a speedup factor.

The paper reports approximately three person-years of content authoring beyond
the architecture, including performance specification. These small text beats
lack that production scope: no animation, voice acting, continuous language
understanding, or concurrent character behaviors. Matching the number 27 does
not reproduce the authors' achievement or refute their cost estimate.
[Mateas & Stern, 2005](https://ojs.aaai.org/index.php/AIIDE/article/view/18722)

The social model remains compact and authored. Some general responses repeat;
sympathetic memories can soften high anger too quickly. Commitments cannot yet
be renegotiated, and betrayal cannot be repaired within this evening. Knowledge
tracks facts, not partial hints or uncertain interpretations. One premise and
explicit menus constrain player expression. There has been no independent reader
study, accessibility audit, or human-only authoring baseline.

The next useful authoring-cost test is the fixed extension brief in
`AUTHORING.md`: preserve attempts, time the work, and compare independently judged
quality against a human-only baseline. `TODO.md` records the remaining defects.
