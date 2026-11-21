# Local event-line variants for Mateo

The first occurrence of each music branch in seeds 3000–3019. These are extracted projections with different surrounding conditions, not interchangeable scripts.

## choose_solo — source seed 3000

invite → decline → choose_solo → response

Shared events needing coordination: 3, 4, 5, 8.

| Event | Mateo’s tags | Other participants |
|---|---|---|
| 3: invite | frame.patient, listener | hero |
| 4: decline | changed, frame.actor, mentioned, qa_context, speaker, state.add:declined_public | hero |
| 5: choose_solo | listener, qa_context | hero |
| 8: response | changed, concept.changed:Trust, frame.actor, grammatical_subject, mentioned, qa_context, state.add:applauded | hero |

The JSON slice includes entry/exit state, shared dialogue/movements, incoming/outgoing declared dependencies, and global flag effects. Actual guards still need revalidation.

## offer_private — source seed 3001

invite → decline → offer_private → pickup → join → response → return

Shared events needing coordination: 3, 4, 5, 6, 7, 8, 9.

| Event | Mateo’s tags | Other participants |
|---|---|---|
| 3: invite | frame.patient, listener | hero |
| 4: decline | changed, frame.actor, mentioned, qa_context, speaker, state.add:declined_public | hero |
| 5: offer_private | changed, frame.actor, mentioned, qa_context, speaker, state.add:consented | hero |
| 6: pickup | destination_holder, frame.actor, frame.destination | spare |
| 7: join | changed, frame.actor, grammatical_subject, mentioned, qa_context, state.add:joined | hero, spare |
| 8: response | changed, concept.changed:Trust, grammatical_subject, listener, mentioned, qa_context, state.add:smiled | hero |
| 9: return | frame.actor, source_holder | spare |

The JSON slice includes entry/exit state, shared dialogue/movements, incoming/outgoing declared dependencies, and global flag effects. Actual guards still need revalidation.

## offer_pattern — source seed 3003

invite → decline → offer_pattern → write_pattern → response → ending

Shared events needing coordination: 3, 4, 5, 6, 9, 11.

| Event | Mateo’s tags | Other participants |
|---|---|---|
| 3: invite | frame.patient, listener, mentioned | hero |
| 4: decline | changed, frame.actor, mentioned, qa_context, speaker, state.add:declined_public | hero |
| 5: offer_pattern | changed, frame.actor, mentioned, qa_context, speaker, state.add:pattern_consent | hero |
| 6: write_pattern | frame.actor, grammatical_subject, mentioned, qa_context | paper, pencil |
| 9: response | changed, concept.changed:Trust, frame.actor, grammatical_subject, mentioned, qa_context, state.add:applauded | hero |
| 11: ending | listener, qa_context | hero, paper |

The JSON slice includes entry/exit state, shared dialogue/movements, incoming/outgoing declared dependencies, and global flag effects. Actual guards still need revalidation.
