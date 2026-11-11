# Reviewed lessons incorporated into prompt v2

These notes accumulate the first six-story batch's reviews. Music and seaside
corrections are verified; these lessons are incorporated into released prompt
v2. Stories 03–08 retain v1 provenance.

1. **Content and polarity.** A negation operator targets a positive proposition
   such as “Tomas finishes the race.” A statement reporting nonfinish may instead
   reference a separate negative proposition. Do not negate that negative
   proposition a second time. Event labels describe the underlying predicate;
   factuality/polarity carry the negation. The actual act of denying has its own
   utterance event. “Not my whale” reports a rejected candidate, not merely the
   broad problem of the book being missing.
2. **Information goals.** “I want to see if the sled can keep up” desires an
   answer, not that the sled succeeds. Keep the information-seeking goal separate
   from the open test proposition. A conditional “would have to admit” describes
   a consequence/requirement, not an intention to admit. Mark a conjunctive goal
   achieved only when every required part is supported: watching an anemone open
   does not establish having watched it open and close.
3. **Quotation inheritance.** A condition or question inside a quote remains
   attributed even if its scope ID is sN rather than qN. Inspect scope ancestry,
   not spelling. A later quoted mention of a narrator-established event retains
   the event's factuality but gets the quote's local assertion attribution.
   Check quotation audiences against utterance recipients. A joint obligation
   group is not automatically the speaker's audience.
4. **Beliefs as causes.** An actual attitude of certainty can cause an action;
   its false content must not be promoted to an actual-world causal fact. Bind
   the causal relation to the attitude event and keep the believed proposition
   as its content.
5. **Physical distinctions.** A carrier supporting an object differs from a
   weight restraining it from above. Support capacity differs from actual
   placement. Accept the proposed `affordance_supporting` field with a bound
   surface/object and explicit `can_support: true`; omit unknown placement.
   Prefer an existing typed field such as `object_temperature` over an ad hoc
   legacy description when the meanings coincide.
6. **Syntax and roles.** A prepositional complement is not a grammatical direct
   object. A body part can be the grammatical subject while its person is the
   semantic perceiver. An individual can be credited for a contribution to a
   joint event without becoming identical to its collective actor. Retain an
   explicit contribution/divided-labor bridge. Past morphology does not prove
   an anticipated or prevented event actually happened.
7. **Source gaps and evidence.** Keep endpoint states with missing transitions:
   bookmark on floor versus later inside book, sign in reeds versus folded
   blanket, jug on blanket versus in basket. Never invent a repair transition.
   Also keep unresolved event identity and chronology in earlier reports. A
   named label owner does not identify the label's author.
8. **Wire format and common values.** Legacy `attributes` is an array of
   `{"name": "...", "value": "..."}` pairs with string values, not strings or
   booleans. True/false semantic features belong in their typed catalog fields.
   Use `goal_polarity=achieve/avoid`, `belief_polarity=accepts/rejects`, and
   `proposition_polarity=positive/negative` for these distinct meanings. Keep
   assertion status limited to asserted/attributed_claim/candidate throughout
   nested bundles.

9. **Consent and participation.** A refusal of program participation does not
   prohibit later tapping from a seat or joining an informal duet. Bind consent
   to the specific proposed action, place and audience. Body cues can support a
   marked interpretation, not a diagnosis or permanent trait. Keep unnamed
   instrument players unknown and distinguish musical pattern identity from
   successive physical sound occurrences. Possessive ellipsis in a size
   comparison needs the omitted object, not its human possessor.

Music's independent review is incorporated in v2, including overt-pronoun and
pause-occurrence distinctions. The
full 1,024-field catalog continues to be available sparsely; these lessons do
not create a reduced feature list or a density quota.
