# Follow-on experiments

The first proof of concept is bounded to one fable. These are research extensions,
not hidden claims about capabilities already delivered.

1. **Cross-fable reuse.** Reuse reading, teaching, testing, and collective defense
   in a different setting. Keep the world operations unchanged. Measure how many
   new state fields, rules, and prose performances are required. Gate: two complete
   stories with distinct conflicts, each with at least one shared practice that
   changes its outcome. Merely changing names does not count.
2. **An integration experiment.** Give independently authored encounter modules
   a fixed schema and invariants, then integrate them. Record total authoring and
   repair effort, conflicting effects, dead ends, and rejected patches. Gate:
   audit every candidate, including failures; compare against a single-author
   baseline. Do not claim a 10,000-agent benefit before measuring it.
3. **Richer local choice.** Offer retrying a failed trial, asking a peer, hiding a
   second book, or contesting the newspaper. Let consequences make later choices
   available. Gate: at least one new causal route, not another paragraph ordering.
4. **Memeplex algebra.** Give composite stories and actions first-class executable
   semantics while preserving physical embedding. Gate: a small whole narrative
   can be embedded, transmitted, and enacted through the same interface as a
   concept; an unembedded copy must remain inert.
5. **Reader annotation audit.** Independently check the semantic exposure labels
   against the actual English, including adversarial prefixes. Gate: no answer
   from facts hidden at that prefix, and no annotation claiming that an unstated
   numerical magnitude was literally communicated. Current annotations expose
   semantic facts at encounter boundaries, not numeric prose entailment.
6. **Question breadth.** Add contextual `Who helped?` and `Where was it?`, then
   paraphrases of the current questions. Gate: preserve event/entity focus across
   at least three turns and refuse missing information. The present grammar
   deliberately accepts only the catalog plus `Why?` and `What happened next?`.

## Known qualitative limitations from this pass

- `fixed_spine`: The first ten encounters follow an authored order.
- `limited_outcome_diversity`: The 240-run grid has three institutional outcomes;
  75% end with a closed palace. The five unfiltered samples all do so.
- `coarse_learning`: A scalar threshold models understanding, including failures
  after a short demonstration. There is no forgetting, partial procedural
  knowledge, or retry; the interrupted-teaching branch makes this simplification
  most visible.
- `didactic_voice`: Several narrator sentences state the moral directly. The
  physical tests and final images carry it more effectively than those comments.
- `narrow_character_policy`: Mira and Tansy are bound to different crafts. The
  separate-work mentoring rule favors Mira; this is a local arrangement, not a
  general theory of how tutoring reaches a group.
- `author_exposure_annotations`: Reader evidence is manually declared; checking
  event IDs and values cannot prove every English sentence semantically correct.
- `limited_followup_grammar`: Unsupported queries fail closed. After `next`, a
  new `why` works only if the new encounter has a catalog topic.

Mechanical failures found and fixed during the pass included a Python 3.9 type
annotation issue, a too-short failure answer, and state effects that were not
fully recorded. Reading also prompted distinct interruption prose, a protest
paragraph that works for one objector, and a physically plausible final viewpoint.
