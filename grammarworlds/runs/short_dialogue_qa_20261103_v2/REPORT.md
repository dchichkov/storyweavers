# Short narration and QA audit

All seven worlds, seeds 0–59, past and present. No sample filtering. Original generated versions are stored alongside each new story and QA set.

| World | Stories | Old mean words | New mean words | Reduction | QA pairs | Guard checks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rescue | 120 | 58.9 | 48.8 | 17% | 720 | 120 |
| kite | 120 | 45.0 | 41.6 | 8% | 600 | 120 |
| key | 120 | 62.7 | 49.4 | 21% | 720 | 120 |
| music | 120 | 136.3 | 58.3 | 57% | 684 | 450 |
| greenhouse | 120 | 148.0 | 88.0 | 41% | 720 | 600 |
| library | 120 | 204.2 | 88.9 | 56% | 720 | 3422 |
| pottery | 120 | 229.1 | 84.1 | 63% | 720 | 5640 |

Every sample completed and replayed, contains at least two physical speakers, and supplies at least five distinct QA pairs covering at least three question kinds. Every answer has at least two full sentences and an exact text span tied to a narrated event. Word probabilities normalize and telescope to surface probability during generation.

The underlying event guards and effects are preserved. Routine physical steps may have empty surfaces; they still execute and appear in the trace. Later narration summarizes only completed events (e.g. pottery firings). Speech uses typed present-tense clauses inside past/present reporting. The frozen GF/Codeco-derived grammar modules are unchanged; new speech constructions sit above them.

QA is for these generated texts, using authored semantic-to-text alignments. It is not a parser for arbitrary uploaded stories. Modified text fails closed. Full answers may paraphrase or make simple local inferences; there is no automatic proof of every English entailment. The templates and representative samples have been read manually; no new model-judge rating is claimed.

Known limits: repeated character names, narrow plot families, a small set of QA templates, and dialogue that remains direct and simple. Shorter prose is not evidence of increased plot diversity. These are symbolic rule programs; source bytes/tokens are not neural parameter counts.

[Read all seven sample stories with QA and evidence](samples.md).
