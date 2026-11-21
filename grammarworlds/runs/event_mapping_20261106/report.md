# Event mapping bank experiment

60 complete, replay-verified runs: three configurations × ten seeds × heads off/on.
Ten comparisons against the archived procedural projection preserve prose, physical entities, flags, and word probabilities.

The source is the annotated kite fetch/mend segment. No target bindings are supplied.
The mixed target explicitly contains both a torn book and a torn kite; Ada has both repair capabilities.
The tape and bench are inferred from their affordances; wrong-holder bindings are rejected by simulation.

| Context | Book repair | Kite repair |
|---|---:|---:|
| Only book is compatible | 100% | 0% |
| Book and kite compatible | 66.67% | 33.33% |
| Same world; kite rule ×4 context factor | 33.33% | 66.67% |

These are authored weights, not calibrated likelihoods or learned attention. Samples below use seeds 0 and 7 chosen in advance.

## book_only, seed 0

Ada fetched the tape from the bench. Ada fixed the book with the tape.

Rules: fetch.portable_tool, repair.paper. Target: book.

## book_only, seed 7

Ada fetched the tape from the bench. She used the tape to repair the book.

Rules: fetch.portable_tool, repair.paper. Target: book.

## book_or_kite, seed 0

Ada fetched the tape from the bench. Ada fixed the kite with the tape.

Rules: fetch.portable_tool, repair.kite. Target: kite.

## book_or_kite, seed 7

Ada fetched the tape from the bench. She used the tape to repair the book.

Rules: fetch.portable_tool, repair.paper. Target: book.

## favor_kite, seed 0

Ada fetched the tape from the bench. Ada fixed the kite with the tape.

Rules: fetch.portable_tool, repair.kite. Target: kite.

## favor_kite, seed 7

Ada fetched the tape from the bench. She used the tape to repair the book.

Rules: fetch.portable_tool, repair.paper. Target: book.

## Limits

The resulting text is a short event segment, not a newly authored complete story. This is an architectural and grounding check, not a Luna quality evaluation.
One full mapping is selected before token generation. Entity state is never averaged across alternatives.
