# Theater: thirty fresh positions

Seeds 1000-1029; all positions retained, including exact duplicate texts.
Storytelling Terra/Luna: 7.833/8.000. Diversity: 4/4. Eighteen exact texts.
All fourteen API calls returned; estimated cost $0.10905745.

The new sample includes the previously unseen fastening-clip repair and audible
prompt branches. The clip actually changes crown size and is consumed; a second
fitting succeeds. In the cue story, Mina's memory changes only when the cue is
audible, or when the prompt book is physically brought onto the stage and read.
These render as complete little scenes. The recurring welcome and shadow plots
remain near-duplicates. The already-fitting-crown branch has the weakest turn.

## QA disagreement review

Terra accepts all 180 conversations, Luna 163. These are judge labels, not a
verified 9.4% error rate. Manual comparison of all seventeen Luna rejections
finds substantial over-literal judging and at least one internally contradictory
rejection. Representative cases:

| Sample | Luna objection | Manual assessment |
| --- | --- | --- |
| theater:1000 | Preparing to open the door is not stated | False rejection: Mina puts a hand on the door, ready to make the words true, then opens it. |
| theater:1000 | Hearing the cue is only implied | Ordinary causal inference: the words reach the stage and the missing sentence comes back to Mina. |
| theater:1006 | Entering from the wings does not establish entering the stage | Reasonable spatial inference from the entire scene; the world trace also enacts that exact travel. Hidden trace alone is not the reader's evidence. |
| theater:1015 | Jo entering onstage is unsupported | The rejection's own evidence says the story supports this. Treat as judge inconsistency. |
| theater:1016 | Chair is not explicitly called royal | The ruler's chair in the scene is a natural contextual description, not a new object. |
| theater:1009 | Behind the door differs from waiting in the wings | Avoidable spatial ambiguity in the answer. The modeled route joins wings and stage through the door, but the opening does not establish that geometry explicitly. |
| theater:1016 | Clip is not described as spare | "Available fastening clip" would be more exact than "spare clip"; not a major story contradiction. |

Keep the original grades and responses. Do not silently flip labels or rewrite
all natural implications into repetitive audit prose to maximize one judge.
These cases are useful candidates for a future mixed-quality judge calibration
set, not an independently adjudicated gold standard.
