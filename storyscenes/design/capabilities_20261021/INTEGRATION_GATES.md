# Proposed integration gates

Design acceptance cases, not implemented or executed tests. These supplement the
27 worker stories with cross-capability checks. Freeze cases before implementation
and retain failed outcomes; do not select only seeds whose story ends happily.

## G1: Consent, custody, and refused return

Compose requesting, lending, carrying, returning, refusing, and informing.

- An owner authorizes a named lender to lend one prop. Another character asks
  for it, accepts explicit terms, and later receives it physically.
- Request acceptance alone leaves physical state unchanged; handover activates
  the specific loan without changing legal ownership.
- The borrower offers to return the object to a third character. That character
  declines; the object stays with the borrower and the loan remains active.
- A new scoped authorization permits receipt at a specific site. A valid deposit
  then changes physical placement and discharges that loan atomically.
- Interventions: remove the authorization; substitute a different loan ID;
  record a delivery claim without physical receipt. None may falsely settle it.
- QA must distinguish who owns, who holds, where it is, and whether the identified
  loan has been returned. A claim of authorization is not sufficient evidence.

## G2: Moving contents and a delayed message

Compose carrying, observing, informing, and discovering_mistake.

- A character sees a prop in a container at location A. The container moves to B
  while that character is absent. Its contents move physically without revealing
  them to the mover or refreshing the absent observer's belief.
- A timestamped message about the original observation arrives after the move.
  Delivery is real; historical observation can remain accurate; a present-tense
  extrapolation can be stale. The message does not fetch current world truth.
- Later accessible evidence may support a revised current belief. Record the
  old belief, the evidence and the revision separately from corrective action.
- Interventions: keep the container closed; omit the second observation; change
  the claim's reference time. Distinguish unsupported, outdated, and disproved.
- QA must not describe a once-accurate observation as a lie or reveal unrendered
  container contents. If evidence is omitted from prose, abstain or omit the QA.

## G3: A promise is not a physical law

Compose requesting, promising, carrying, refusing, and informing.

- A character accepts a request; a distinct explicit promise commits them to a
  bounded action by an authored checkpoint. Neither step performs the action.
- A competing need changes their choice. Physical performance remains possible,
  but the promise is not fulfilled by the checkpoint.
- Record breach separately from ability and intention. An apology or promise to
  try again does not retroactively fulfill the original commitment.
- Interventions: perform the action without promising; promise without acting;
  ask a new request after the breach. Each history must remain distinguishable.
- A refusal of the new request must not cancel the old promise automatically.
- QA may explain the chosen priority only if the narrative supplies the motive.

## G4: Repetition, rejection, and narrative evidence

Compose observing, informing, requesting, and refusing.

- An action rejected during search produces no story event. A character's actual
  attempt that fails may produce an event with no physical state change.
- Repeating an already-heard warning or reaffirming a refusal can be meaningful
  without inventing a fake world flag. The event still has an actor, audience,
  focus, reason where established, and bounded execution.
- Prose selection/pruning preserves the speech evidence necessary for later
  explanations. Every relevant utterance has a stable event/response reference.
- Interventions: remove a reply; repeat a claim; hide a motive in the narration.
  Follow-up QA must not guess a reply target or expose the missing motive.

## Transfer and acceptance

1. Bind the same capability definitions in all three settings. Vary premises,
   accessibility, consent, evidence order and choices, not merely names/text.
2. Hold out at least one cross-capability combination from implementation demos.
   Do not let every test be written by the implementation author.
3. Require deterministic replay, well-defined effects, and invariant preservation.
   A predicate check is not proof that a free-English paragraph entails it.
4. Inspect rendered stories and QA together. Verify that each causal/temporal
   answer uses the appropriate reference time and reader-visible evidence.
5. Preserve legacy behavior via explicit versioning and pinned old replays.
6. Report semantic outcomes and intervention sensitivity separately from exact
   duplicate rate, compression, and literary scores. No arbitrary quality target
   is considered passed merely because the schema is valid.

Initial validation should be local and bounded. A paid literary/QA evaluation is
a separate approval and should keep its judge/protocol comparable to the baseline.
