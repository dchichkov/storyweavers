# Physical-family cross-review

Reviewed carrying, lending, returning, `COMPATIBILITY.md`, and `INTEGRATION_GATES.md`. Design findings only; no implementation or executed tests.

## Findings

### 1. Delayed settlement contradicts the completion operation

`returning.md`, **Reusable contract / Atomic performance**, requires `CompleteReturn` to apply carrying's parent change and discharge together. Its **Library / receive-only intervention**, however, permits Sol to receive the atlas while `A2` remains active, with Inez settling later. Once Sol holds it, Nia cannot perform another hand-back. Repeating the receipt would fabricate movement and violate carrying's duplicate-handoff rule.

Separate physical receipt from settlement evidence. Immediate authorized receipt/deposit can atomically discharge. Delayed settlement must reference the original receipt plus explicit settlement authority and policy; it writes the loan status, not another parent edge. Do not imply that a later grant retroactively authorized an earlier discharge. Decide whether this case belongs in the first slice; otherwise label that intervention deferred rather than supported.

### 2. A physical custodian is not always an actor

`carrying.md`, **Reusable contract**, derives custody from the actor ancestor: placing Ada's tote on the library bench leaves no physical custodian while Ada remains borrower. `lending.md`, **Reusable contract / ActivateLoan**, instead expects receipt "from C to B" and release through C. That wording excludes collection from an authorized cabinet or table where C is absent. Its **Observatory** ending also describes continued custody although the detector is inside a cabinet, not physically held by Kit.

Use source parent/path for physical control, and separate borrower, keeper, release authority, and legal owner. Kit may manage access without being the derived custodian. Likewise Rui's wrench in the **Lending / Harbor** tray leaves Rui's obligation intact despite empty hands. Do not add a second writable custody slot to reconcile these stories.

### 3. Acceptance, readiness, and receipt need distinct identities

The proposals agree that agreement acceptance and return-offer acceptance do not move anything. But carrying's **Handoff** accepts unspecified "readiness/acceptance evidence"; lending's consent is tied to terms/revision, while returning's acceptance targets a return offer. These are not interchangeable tokens. **Carrying / Harbor**, where Jo says "I'm ready," must support receipt without opening a loan. **Lending / Observatory** accepts terms without receiving the detector or acquiring debt.

Bind readiness to giver, recipient, object, and offered operation. Bind loan consent to agreement revision; bind return acceptance to offer/loan. Recheck current capacity and source path at performance; an earlier acceptance is not a reservation of hands or custody.

### 4. Joint validation is agreed, but its read boundary is missing

All three contracts claim atomicity without specifying the common pre-state. If custody or a grant changes between offer/acceptance and execution, carrying must not commit while activation/discharge fails, nor vice versa. G1 requires this distinction; `COMPATIBILITY.md`, **Mechanics**, warns that labels are not verified operations.

Validate physical graph/access/load, current source, scoped grants, agreement revision, and loan status against one state, then commit the bundle or nothing. Authorized cabinet return in **Returning / Observatory** additionally needs explicit latch effects and postconditions; generic Put alone does not latch a cabinet. Keep that bounded domain effect outside carrying. Derived path reads must survive pruning and replay, including unchanged containment edges.

### 5. Information acceptance cannot supply authority

In **Returning / Library**, reading Sol's note supplies character evidence, while the actual scoped grant validates discharge. In **Lending / Harbor**, Tessa's accepted old permission claim cannot enlarge her current grant. G2 also requires timestamped location claims to remain historical after a container moves. Distinguish claim/belief acceptance from domain consent and actual grant validity; neither receipt nor settlement automatically refreshes beliefs. Reader QA needs rendered support for the relevant time and scope, not a hidden grant or path alone.

## Smallest shared interface

Use one explicitly versioned physical/social extension with:

- Carrying-owned parent graph and derived timed place/custodian queries; pickup, handoff, and deposit produce one receipt identity with object, participants/source, destination, and event reference.
- Lending-owned immutable agreement revision, explicit consents, scoped grant, and loan activation/debtor. Returning owns discharge validation/status and references that loan and receipt.
- A joint transaction validating declared physical and social reads against one pre-state, with typed evidence links for rendering, QA, and replay. Keep observation, claims, motives, and interaction acceptance separately referenced.

Defer recursive delegation, amendments, generalized legal adjudication, and arbitrary event-only repetition. Failed return offers can meaningfully become declined without physical changes; unchanged speech still needs G4's bounded event facility, not dummy flags. Preserve legacy Move/owner/Tell and frozen fixtures exactly; new adapters must reject implicit legacy reinterpretation.

## Five Falsifying Tests

1. Sol receives `A2` under receive-only authority; later authorized settlement closes it using that receipt. Assert exactly one handover, unchanged later placement, and no effect on `A1`. Without settlement authority/policy, debt remains.
2. Ada puts the book-containing tote on the bench. Assert book location follows the tote, physical custodian becomes absent, borrower remains Ada, and no loan discharges. Authorized cabinet collection must work without inventing an actor holder.
3. Jo accepts receipt, then fills his remaining hand; revoke a lender's grant in a parallel variant before activation. Each joint operation must reject without partial physical/social writes or fictional failed-attempt prose.
4. Accept a delivery claim without receipt; accept an outdated authority claim; move a closed container after observation. None may activate/discharge a loan, create authority, reveal contents, or refresh the observer's belief.
5. Replay an authorized cabinet deposit with required latch, then remove latch capability. Only the first settles. Pruning retains its access/authority dependencies; legacy replays retain their original semantics.

## Coordinator Resolutions Required

Freeze: receipt identity shared across pickup/handoff/deposit; readiness versus domain-consent references; source-path versus keeper/borrower roles; joint pre-state validation and evidence reads; whether delayed settlement is supported, including its authority and timing policy; latch-effect composition; and version/adapter boundaries. These are blocking interface decisions. No wholesale ontology expansion or literary rewrite is needed.
