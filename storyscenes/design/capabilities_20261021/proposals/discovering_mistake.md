# Discovering a Mistake: First-Pass Proposal

## Scope and existing behavior

Design only, not implemented or tested. Discovering a mistake compares an
embedded expectation with accessible evidence, explicitly revises it, and makes
the consequences available to later choices. It does not automatically repair
anything, persuade another person, or fulfill an obligation.

Reuse immutable role binding and candidate composition from
`storyscenes/algebra.py:Kernel.bind` and `Pattern`; atomic guarded effects from
`runtime.py:transition`; and before/after provenance from `runtime.py:solve`.
Currently `observe` overwrites `.knows.<fact>` with truth and `tell` copies the
speaker's stored belief. `test_algebra.py:test_explicit_stale_belief_survives_auto_declaration_and_tell`
demonstrates false-belief transmission. Neither operation represents an explicit
comparison, evidential disagreement, or acknowledged revision.

`conversation.py:truth_answer` compares belief with truth at the focused time;
`causal_answer` explains enabling guards, not motives. `dialogue.py:collect_dialogue`
indexes attributed speech, claims, and replies without executing speech acts.
`prose.py:render_book` checks card conditions, not every English assertion.
The 100-world `REPORT.md` and `storyscenes/TODO.md` document offstage QA and weak
causal focus despite zero deterministic evidence defects. These gaps motivate
reader-support checks, not prose-based reconstruction of missing world events.

Follow `COMPATIBILITY.md`: introduce an opt-in versioned contract, preserving
legacy Observe, Tell, ownership, frozen traces, and exports. Structured records
below require a new representation/compiler, not JSON hidden in scalar strings.
Beliefs and concerns reside in characters; records reference physical documents,
instruments, or witnessed acts. This advances `story.py`'s embedded-state north
star without claiming its universal memeplex algebra is already implemented.

## Reusable contract

**Participants and records, proposed.** Bind actor, subject, prior belief ID,
evidence IDs, and a small declared comparison rule. A proposition contains
subject, predicate, value, reference interval, and scope, including date or
instrument identity where relevant. A belief revision retains actor, proposition,
status (`accepted`, `uncertain`, `withdrawn`, `superseded`), and source IDs.
Evidence retains content, acquisition event/time, source/carrier, access recipient,
and the proposition's reference time separately. A discrepancy records the
specific incompatible propositions, rule, and assessment (`disproved`,
`unsupported`, `outdated`, `unresolved`). These are epistemic records associated
with existing physical characters, not invented abstract physical entities.

**Two candidate operations.** `RegisterMismatch(actor, belief, evidence, rule)`
requires an active, non-unknown prior belief and accessible relevant evidence.
It appends a discrepancy without changing belief or world truth. Mere difference
between Tuesday and Wednesday is not contradiction. `ReviseBelief(actor,
discrepancy, resolution)` requires that discrepancy and an admissible comparison;
atomically archives the active revision, installs the new revision, and links
both to the evidence. A decisive exclusion permits replacement; insufficient
support permits withdrawal to unknown, not acceptance of the opposite.
Unresolved conflicts may remain pending. Duplicate registration/revision is
idempotent and creates no second event.

**Reads, writes, and legality.** Read only the actor's belief, acquired evidence,
source-validity evidence, and authored comparison rules. The planner may inspect
truth to validate simulation, but the actor cannot revise from inaccessible
truth. Same-time contradiction establishes an earlier mistake only when the
evidence addresses that earlier interval; later change instead yields outdated.
Require typed values, compatible scope, and a finite auditable rule such as
identity/date lookup, direct exclusion, or source-dependency invalidation. No
general theorem prover or English inference. Received claims remain claims;
informing owns receipt and acceptance. Wrong evidence can yield a mistaken
revision; record its evidential basis without calling it verified truth.

Write only actor-bound discrepancy/belief history. Do not change instrument
condition, reservation, custody, ownership, request, promise, or another mind.
Separate events own correction. Choice reads explicit actor goals/concerns and
the revised belief; its motive link is distinct from enabling dependencies.
Concerns may gate or weight choices but are not automatically changed as a
reward for admitting error.

**Event/evidence fields.** Retain event ID, operation, actor/subject IDs,
belief-before/after IDs, discrepancy ID, evidence IDs, comparison-rule ID,
reference interval, assessment, and actual reads/writes. Later choices cite the
revision plus a goal/concern when that is their reason. Reader-support links
identify rendered spans establishing prior belief, contradiction, revision,
and consequence; annotations alone do not prove the English says these things.
QA requires both trace support and story support, preserves revision focus on
"Why?", and abstains on ambiguous or omitted evidence.

**Failure boundary.** Inaccessible evidence, unknown prior belief, wrong subject,
scope mismatch, or unsupported resolution rejects a candidate, not a narrated
attempt. `transition` currently rejects unchanged state; meaningful failed tests
must instead produce evidence/results or consume modeled resources. Repeated
speech needs informing's meaningful delivery record, not a dummy flag. Pivotal
revision events and their evidence must survive `planning.prune_path` through
semantic dependencies and explicit pivotal retention, followed by replay.
Non-goals: compulsory confession, correction, forgiveness, deception detection,
universal moral success, or automatic numerical confidence updates.

## Story 1: Library - The Wrong Wednesday

**Premise and initial evidence.** Nia wants the shared projector for tonight's
map club. She believes her reservation covers Wednesday the 14th; the unchanged
dated ledger assigns her the 21st and Omar the 14th. The reader sees her penciled
"tonight" note and the ledger's two dated rows when she opens it. Omar wants his
book group's screening undisturbed. The error is date application, not a
reservation secretly changing while Nia looks away.

**Six beats, illustrative rather than prescribed.**
1. Nia gathers maps under her accepted 14th reservation belief; her preparation
   serves the club goal, without moving the projector by implication.
2. With the desk open and ledger accessible, she reads both rows. Observing
   creates date-scoped evidence, not automatic revision.
3. She compares her booking identity and date, registering a disproved belief.
4. She explicitly revises: her booking is next week. Omar's booking and the
   projector remain unchanged; disappointment does not grant permission.
5. Wanting tonight's meeting to happen, she requests the available paper atlas
   and announces a table session. Library authority accepts; separate allocation
   and delivery events provide the atlas.
6. The club meets around an unfolded atlas while light from Omar's screening
   crosses the glass door. The image proves adaptation, not a corrected booking.

**Effective exchange.**
- Nia tells Omar: "I read next week's row as tonight's. This booking is yours."
- Nia asks librarian Sol: "May our club use the large atlas tonight instead?"
- Sol replies: "Yes, the atlas is available for your table."

The first speech communicates her revision; the request and acceptance enable
allocation but do not themselves deliver the atlas.

**Interventions.** Change the ledger so Nia really holds the 14th: no mistake
discovery is legal, and the projector route remains available. Make the atlas
unavailable: revision still succeeds, but the table-session route fails; an
explicit postponement can end the story without altering either reservation.

**QA, with required rendered evidence.**
1. What changed in Nia's understanding? "Nia first thought her booking was for
   tonight. She then recognized that it was for the following Wednesday."
   Require her initial expectation and explicit revision, linked to belief IDs.
2. Linked follow-up, Why? "Her dated row said the 21st, not the 14th. The row for
   the 14th belonged to Omar." Require both visible ledger rows and comparison.
3. Linked follow-up, What happened next? "Nia asked Sol for the large atlas.
   Sol agreed, so a table session became possible." Require the subsequent
   request and acceptance events; preserve revision focus through the Why turn.

## Story 2: Harbor - The Motor That Was Turning

**Premise and initial evidence.** Ivo wants a repaired pump aboard a fishing
boat before departure. He believes its motor has failed because the outlet is
still. The workshop's isolated test rule states that a motor turning its shaft
during this test is not a failed motor; it says nothing about downstream faults.
The motor and shaft have not been repaired between suspicion and test. Reader
evidence includes Ivo's diagnosis, the idle outlet, and the test's limited scope.
Mechanic Ren wants unsafe substitutions avoided.

**Six beats.**
1. Ivo prepares a replacement-motor request because he believes that diagnosis.
2. Ren offers an isolated test; Ivo accepts testing to avoid wasting the scarce
   spare. Safe isolation and access are prerequisites, not his motive.
3. Testing consumes a modeled battery charge and reveals the shaft turning
   while the pump outlet remains still; observing supplies those results.
4. Ivo registers the exclusion and revises "motor failed" to false. The cause
   of the pump fault remains unknown; no coupling fault is invented.
5. He withdraws the replacement request and asks to delay dispatch for further
   inspection. The captain accepts the delay; departure readiness changes only
   through those separately owned actions.
6. The boat stays moored, with an inspection tag beside the still-open pump.
   Discovery prevents a misdirected replacement but does not complete a repair.

**Effective exchange.**
- Ren tells Ivo: "The shaft is turning in isolation; this test clears the motor."
- Ivo tells the captain: "My motor diagnosis was wrong. Please hold dispatch for inspection."
- The captain replies: "I'll hold dispatch; we still need a working pump."

Index the diagnosis revision, request, and acceptance/commitment separately;
the captain's words are not proof of subsequent performance.

**Interventions.** Occlude the shaft indicator: the test consumes charge but
provides no decisive exclusion, so diagnosis stays uncertain rather than
cleared. Remove authority to delay departure: Ivo can still discover the error
and withdraw his request, but the captain may refuse; record that refusal and
its consequences without undoing the revision or certifying a safe departure.

**QA, with required rendered evidence.**
1. What did Ivo discover? "The motor was turning during the isolated test.
   Ivo withdrew his belief that the motor had failed." Require result and revision.
2. Linked follow-up, Why did that change his diagnosis? "A turning shaft ruled
   out a failed motor under this test's stated rule. It did not explain the
   remaining pump problem." Require the scoped rule and explicit remaining unknown.
3. Linked follow-up, Was the pump fixed then? "No, the outlet was still not
   flowing. The boat remained moored for inspection." Require unchanged pump
   result and recorded hold, not inference from abandoned planner candidates.

## Story 3: Observatory - Yesterday's Bright Point

**Premise and initial evidence.** Sera wants to send a promising new bright-point
report before the radio window closes. She believes the point was independently
captured tonight. Technician Tavi suspects a copied image. Tonight's working
file actually references yesterday's exposure; no fresh exposure exists. The
reader initially receives Sera's expectation, then sees both file identifiers
and the matching exposure timestamp with Sera. Whether the bright point exists
in the sky tonight remains unknown.

**Six beats.**
1. Sera drafts a report based on the supposed independent exposure; it is not
   yet transmitted. Her curiosity motivates reporting, not omniscient certainty.
2. Tavi communicates a duplication concern with its file source; receipt alone
   does not force Sera's acceptance.
3. Sera accesses the image log and verifies the identical exposure identifier.
   The identity rule contradicts independence, not the point's existence.
4. She explicitly revises the exposure attribution and withdraws the unsupported
   tonight-detection claim. Both belief dependencies remain inspectable.
5. Clouds prevent a fresh exposure within the radio window. Sera chooses to
   send a correction about the copied file rather than a discovery claim;
   informing records delivery without guaranteeing remote acceptance.
6. The radio lamp goes dark beside the old exposure and an empty tonight slot.
   Accurate uncertainty is the ending, not a replacement discovery.

**Effective exchange.**
- Tavi tells Sera: "These files name the same exposure. Please check the log."
- Sera replies: "You're right about the copy. Tonight's point is still unconfirmed."
- Sera radios base: "Withdraw my draft claim; the image was yesterday's exposure."

The draft withdrawal changes local report status; the transmitted correction
does not rewrite base's beliefs without a receipt/acceptance event.

**Interventions.** Substitute a distinct verified tonight exposure ID: the copy
contradiction disappears; retain the report route without inventing confirmation
from identity alone. Allow clear sky and sufficient time: Sera may request and
obtain a fresh exposure, but its independent result, not discovery itself,
determines whether a new report becomes justified.

**QA, with required rendered evidence.**
1. Which belief was disproved? "Sera's belief that tonight's image was an
   independent exposure was disproved. Both files referred to yesterday's image."
   Require old belief, both identifiers, timestamp, and explicit revision.
2. Linked follow-up, Did that prove the point was absent tonight? "No, a copied
   image could not settle tonight's sky. Sera left that claim unconfirmed."
   Require the stated evidential limitation and withdrawal to unknown.
3. Linked follow-up, Why didn't she check again? "Clouds blocked a fresh exposure
   before the radio window closed. Sera sent the correction instead." Require
   visible weather/time constraints and recorded choice, not a hidden schedule.

## Cross-capability composition

Observing owns access and timed evidence; informing owns claim, receipt, and
acceptance. For conflicting prior beliefs, acceptance refers to this contract's
resolution rather than independently overwriting the slot. Observing may
initialize unknown beliefs or refresh matching support without a mistake event.
This agrees with `messages/observing.md:observing-01` and
`messages/informing.md:informing-01`, subject to coordinator approval.
Outside that peer group, requesting owns atlas allocation requests and dispatch
delay negotiation; promising owns any captain commitment and its performance;
refusing owns a refusal, reason, and aftermath. Discovery cannot discharge them.
Carrying owns physical receipt/location of the atlas; lending/returning own any
loan identity and discharge. No epistemic event moves equipment or changes title.

## Acceptance tests

- Positive: each trace preserves prior belief, accessible evidence, explicit
  comparison, revision, and independently executed consequence; replay is legal.
- Negative: hidden evidence, mismatched dates, unknown priors, and unsupported
  replacement create no discovery; later world changes classify outdated, not
  false-at-the-time. Planner rejection never becomes a narrated failed attempt.
- Separation: disable every corrective action; revision remains reachable and
  material problems remain unresolved. Repeated revision adds no dummy state.
- Interventions: execute all six changes above; compare belief, legal choices,
  and actual outcomes, not merely different prose. Preserve decisive evidence
  through pruning even when physical endpoints could otherwise match.
- Transfer: bind the same comparison/revision contract across date lookup,
  diagnostic exclusion, and dependency invalidation. Renaming props alone is
  not semantic variety; uncertainty and correction availability must vary too.
- QA/rendering: all nine pairs require span-backed, timed support and full
  answers. Remove a required passage: abstain. Test Why-focus retention, no
  offstage questions, no future evidence, indexed speech, and no invented motives.

## Open decisions

Smallest slice: finite propositions, immutable belief/evidence IDs, explicit
mismatch and revision, three comparison rules, and story-supported QA adapters.
Coordinator must settle evidence accessibility, revision ownership, temporal
scope, dependency-preserving pruning, and versioned record representation.
Defer confidence arithmetic, adversarial testimony, general diagnosis, and
unbounded belief chains. None is needed to keep discovery separate from repair.
