# Bounded Site-Scoped Grant Follow-Up

2026-10-22. Independent review of the sole remaining P2 finding in
`final_review.md`, limited to grant location/authority, old JSON defaults,
and production rendering/QA support.

## Findings

**No findings in the reviewed scope.** The original dry-bench/launch probe now
has the required restricted/unrestricted contrast. This closes that specific
missing site-binding finding; it does not certify every Harbor proposal beat,
other capability slices, or overall acceptance.

`physical.py:218` retains exact active grant matching by grantee, object, right,
scope, destination and issuer, and additionally checks both grantee and object
at the optional place. `offer_loan` and `activate_loan` call the shared lending
authority check; `complete_return` independently checks the settlement grant
at performance. Acceptance/readiness therefore do not carry authority to a new
place. Place references are validated as places, not actors or objects.

## Exact Verification

- Ran the requested command from `/Users/dmitry/storyweavers`:
  `.venv/bin/python -m unittest discover -s storyscenes -p 'test_capability_sites.py'`.
  **5 tests passed**. These include restricted/unrestricted offers, return and
  activation rechecks, atomic rejection, invalid place references, old JSON
  loading, authority-answer support masks/replay, and designated deposit-site
  behavior.
- Ran an additional unpersisted Python stdin probe with
  `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -`. Independently extended
  `two_offer_story(harbor=True)` with a launch and open outward route, rather
  than relying on the new return fixture. After second-offer acceptance and
  readiness at the bench, legally moved borrower (carrying the prop) and
  receiver aboard. The unchanged `finish2` rejected with `settle1.place=room`;
  the state fingerprint stayed identical, A1 remained active, and no receipt
  appeared. Changing **only settle1** to `place=None` let that same operation
  discharge A1 aboard and move the prop to the receiver. The failed branch
  supplied no supported `finish2:1` authority answer.
- Independently prepared O2 consent/readiness at the bench, moved both actors
  aboard, then attempted unchanged `collect2`. Tested a restricted lend grant
  alone, a restricted release grant alone, and neither restricted. Each
  restricted case rejected atomically, leaving readiness unconsumed and no A2
  loan/receipt; the unrestricted control activated A2.
- Read complete production stories (including authored premise/ending) and
  focused authority QA for both values of `unrestricted` in
  `harbor_scoped_lending_story` and `harbor_scoped_return_story`. Text correctly
  distinguishes lending/return at the bench from aboard, preserves ownership,
  and identifies the accepted second return offer as settling A1. Authority
  answers explicitly distinguish bench-only from unrestricted authorization.
- For all four variants, individually masked every statement in the authority
  answer's support set: each mask made that answer unsupported. Replayed from
  **only `collect2:1` or `finish2:1`**, respectively: retained rendering equaled
  full-trace rendering restricted to retained events, and the authority answer
  was identical. The return replay retained both offers and their responses,
  as well as the relevant travel.
- For both unrestricted fixtures, JSON-round-tripped the spec, removed `place`
  from every serialized grant, and loaded/replayed again. Every omitted value
  defaulted to `None`; final fingerprints and rendered documents matched the
  explicit-null controls. This verifies behavior, not just successful loading.

## Scope And Limits

Read `final_review.md`, current `physical.py`, `returns.py`, `realize.py`, and
`test_capability_sites.py`; consulted the JSON codec, Reader support closure,
and the Harbor proposal for this bounded question. No implementation, tests,
or old reports were edited. No paid calls, commit, push, other-slice re-audit,
full-suite run, v4 evidence audit, or completion-document work was performed.
Parent owns those broader checks. The workspace is concurrent, not frozen;
later changes are outside this result.

Reviewed source SHA-256 values (relative to `storyscenes/`):

```text
capabilities/physical.py  133380f32d5addcc01f964e3c81f49415a5118094041cb002b5dd9bf835164d2
capabilities/returns.py   2164bb85d4717dc0405ccc8ff3e91b72ab610b7e4cfb4de9177f7c24625a2b8c
capabilities/realize.py   e924b14a6a77d689e09d0bddf81c04e1d6a977bef67cb081d2f5b5fa0036292e
test_capability_sites.py 9c48853d47303df42ac86b8ca8b3079bb2935f192006bb9d7ab34b7e9da2f608
capabilities/codec.py    7b13c7302648b2ed249a23a8d1a08e51d0eea063c0a379b84f470d4bc50e7b9d
```
