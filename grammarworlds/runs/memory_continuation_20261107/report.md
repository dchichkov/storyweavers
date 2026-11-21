# Sampled continuation from intact story memory

Memory: one intact annotated source sample (seed 3000) from each of the seven worlds. This uses the 17-rule mapping bank; it does not expose all 119 source event kinds for execution. Sources are references into whole stories, not detached prose snippets.

The receiver is the explicit paper-repair fixture: Ada holds a torn paper book, tape is on the bench, and Ada/Omar have paper-repair ability. No missing entities or capabilities are imported.

The main comparison supplies one repair-intent event. Its repaired-state goal is inferred by a small explicit intent rule. Every later action, binding and STOP is sampled; no fetch/repair/return sequence is supplied. Plain sampling uses mapping weights. Contextual sampling adds manual state-progress, goal-progress, one-step goal-enabling, actor-continuity and repetition factors. Words and attributes are then sampled conditionally.

| Experiment | N | Book repaired | Sampled stop | Event limit | Mean events after prefix | Repeated actions | Distinct chains |
|---|---:|---:|---:|---:|---:|---:|---:|
| plain | 20 | 7 | 12 | 8 | 7.10 | 39 | 19 |
| contextual | 20 | 20 | 20 | 0 | 2.45 | 0 | 5 |
| dialogue_prefix | 5 | 5 | 5 | 0 | 3.20 | 0 | 3 |
| ending_predicate | 5 | 5 | 5 | 0 | 7.00 | 3 | 4 |
| no_prefix | 5 | 5 | 5 | 0 | 7.20 | 1 | 5 |
| craft_no_plan | 5 | 0 | 5 | 0 | 3.80 | 0 | 5 |

Repeated actions count exact target operation/argument repeats within each continuation. Distinct chains omit STOP and wording. These are mechanical measures, not Luna ratings.

The ending-predicate variant additionally asks for the repaired book to be on the bench. This is a supplied final-state condition, not an inferred literary ending. The dialogue-prefix variant adds Omar offering help. No-prefix variants have no goals. Craft has explicitly declared clay, drum, ladder, broken tap and drawing materials/abilities.

## Samples and latent event streams

### plain, seed 0

Ada said, “I want to repair the book.” She handed Omar the book. Omar gave Ada the book. He fetched the tape from the bench. Ada put the book on the bench. Ada fetched the book from the bench. Omar handed the tape to Ada. Ada gave the book to Omar. Ada gave Omar the tape. Omar placed the book on the bench. He fetched the book from the bench. He handed Ada the book. Omar handed Ada the tape.

`transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → fetch(actor=omar, item=tape, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=ada, item=tape, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=book, recipient=ada) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: limit; goal predicates: [False].

### plain, seed 1

Ada said, “I want to fix the book.” She fetched the tape from the bench. Ada gave the book to Omar. Omar handed Ada the book. Using the tape, Ada repaired the book. She gave Omar the tape. Omar gave Ada the tape. Ada handed the book to Omar. Omar handed the book to Ada. Ada placed the book on the bench. She gave Omar the tape. Omar fetched the book from the bench. He gave Ada the tape.

`fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: limit; goal predicates: [True].

### plain, seed 2

Ada said, “I want to fix the book.”

``

Stop: sampled_stop; goal predicates: [False].

### plain, seed 3

Ada said, “I would like to repair the book.” Omar fetched the tape from the bench. He gave Ada the tape. Ada put the book on the bench. Omar fetched the book from the bench. He handed Ada the book. With the tape, Ada fixed the book. She placed the book on the bench. Omar fetched the book from the bench. Omar put the book on the bench. Ada gave Omar the tape.

`fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=book, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → put_item(actor=omar, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar)`

Stop: sampled_stop; goal predicates: [True].

### plain, seed 4

Ada said, “I want to fix the book.” Omar fetched the tape from the bench. Ada put the book on the bench. She fetched the book from the bench. She placed the book on the bench. Omar gave the tape to Ada. Ada fetched the book from the bench.

`fetch(actor=omar, item=tape, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=ada, item=book, source=bench)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 5

Ada said, “I would like to repair the book.” She put the book on the bench. Omar fetched the book from the bench. He handed the book to Ada.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=book, recipient=ada)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 6

Ada said, “I want to repair the book.” She gave Omar the book. Omar handed the book to Ada. Ada placed the book on the bench. Omar fetched the tape from the bench. He handed the tape to Ada. He fetched the book from the bench. Ada handed Omar the tape. Omar handed Ada the book. Omar handed the tape to Ada. Ada handed Omar the book. Omar placed the book on the bench. Omar fetched the book from the bench.

`transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=omar, item=book, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench)`

Stop: limit; goal predicates: [False].

### plain, seed 7

Ada said, “I would like to repair the book.” Omar fetched the tape from the bench. Ada put the book on the bench. Omar fetched the book from the bench. Using the tape, Omar repaired the book. He handed Ada the tape. Ada gave Omar the tape. Omar placed the book on the bench. Ada fetched the book from the bench. She placed the book on the bench. She fetched the book from the bench. Ada put the book on the bench. Omar gave Ada the tape.

`fetch(actor=omar, item=tape, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=ada, item=tape, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: limit; goal predicates: [True].

### plain, seed 8

Ada said, “I want to repair the book.” Omar fetched the tape from the bench.

`fetch(actor=omar, item=tape, source=bench)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 9

Ada said, “I would like to repair the book.” She placed the book on the bench. Omar fetched the tape from the bench. He gave Ada the tape.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 10

Ada said, “I would like to fix the book.” She placed the book on the bench. Omar fetched the tape from the bench. He fetched the book from the bench. With the tape, he fixed the book. He handed Ada the book. Ada handed the book to Omar. Omar gave the book to Ada. Ada put the book on the bench. She fetched the book from the bench. Omar handed the tape to Ada. Ada placed the book on the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape) → transfer(actor=omar, item=book, recipient=ada) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=ada, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [True].

### plain, seed 11

Ada said, “I would like to fix the book.” Ada placed the book on the bench. She fetched the book from the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 12

Ada said, “I would like to repair the book.” She put the book on the bench. Ada fetched the book from the bench. She put the book on the bench. She fetched the tape from the bench. She gave the tape to Omar. She fetched the book from the bench. She placed the book on the bench. Omar fetched the book from the bench. He gave the tape to Ada. He handed Ada the book. Ada handed Omar the tape. Ada gave the book to Omar.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=omar, item=book, recipient=ada) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=ada, item=book, recipient=omar)`

Stop: limit; goal predicates: [False].

### plain, seed 13

Ada said, “I want to repair the book.” Omar fetched the tape from the bench. Ada gave Omar the book. Omar gave Ada the tape. Omar gave the book to Ada. With the tape, Ada fixed the book. She put the book on the bench. She gave Omar the tape. Omar gave the tape to Ada. He fetched the book from the bench. He placed the book on the bench. Ada fetched the book from the bench. She put the book on the bench.

`fetch(actor=omar, item=tape, source=bench) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=omar, item=book, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=omar, item=book, source=bench) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench)`

Stop: limit; goal predicates: [True].

### plain, seed 14

Ada said, “I want to fix the book.” She fetched the tape from the bench. She handed Omar the tape. She handed the book to Omar.

`fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=ada, item=book, recipient=omar)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 15

Ada said, “I would like to fix the book.”

``

Stop: sampled_stop; goal predicates: [False].

### plain, seed 16

Ada said, “I would like to fix the book.” Omar fetched the tape from the bench. He handed the tape to Ada. Ada placed the book on the bench. She fetched the book from the bench. She put the book on the bench. Omar fetched the book from the bench. He placed the book on the bench. He fetched the book from the bench. He put the book on the bench. Ada fetched the book from the bench. She used the tape to repair the book. She placed the book on the bench.

`fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench)`

Stop: limit; goal predicates: [True].

### plain, seed 17

Ada said, “I would like to fix the book.” Ada put the book on the bench. Omar fetched the book from the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench)`

Stop: sampled_stop; goal predicates: [False].

### plain, seed 18

Ada said, “I want to repair the book.” She fetched the tape from the bench. She gave the tape to Omar. Omar handed the tape to Ada. Using the tape, Ada fixed the book. She gave the tape to Omar. Omar gave the tape to Ada. Ada gave Omar the tape. Omar gave Ada the tape. Ada placed the book on the bench. She handed Omar the tape. Omar fetched the book from the bench. He gave Ada the tape.

`fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: limit; goal predicates: [True].

### plain, seed 19

Ada said, “I want to repair the book.” She handed Omar the book. Omar handed Ada the book. Ada put the book on the bench. Ada fetched the book from the bench. Omar fetched the tape from the bench.

`transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=book, recipient=ada) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=book, source=bench) → fetch(actor=omar, item=tape, source=bench)`

Stop: sampled_stop; goal predicates: [False].

### contextual, seed 0

Ada said, “I want to repair the book.” She put the book on the bench. Omar fetched the book from the bench. He fetched the tape from the bench. Using the tape, Omar fixed the book.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → fetch(actor=omar, item=tape, source=bench) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 1

Ada said, “I want to fix the book.” She fetched the tape from the bench. Ada used the tape to repair the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 2

Ada said, “I want to fix the book.” She handed Omar the book. Omar put the book on the bench. Ada fetched the tape from the bench. Ada gave Omar the tape. Omar fetched the book from the bench. He fixed the book with the tape.

`transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 3

Ada said, “I would like to repair the book.” She fetched the tape from the bench. She used the tape to repair the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 4

Ada said, “I want to fix the book.” She fetched the tape from the bench. Using the tape, she repaired the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 5

Ada said, “I would like to repair the book.” She fetched the tape from the bench. She fixed the book with the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 6

Ada said, “I want to repair the book.” Omar fetched the tape from the bench. Ada handed the book to Omar. Omar used the tape to repair the book.

`fetch(actor=omar, item=tape, source=bench) → transfer(actor=ada, item=book, recipient=omar) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 7

Ada said, “I would like to repair the book.” Ada fetched the tape from the bench. Using the tape, she fixed the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 8

Ada said, “I want to repair the book.” She fetched the tape from the bench. She used the tape to repair the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 9

Ada said, “I would like to repair the book.” She fetched the tape from the bench. With the tape, Ada fixed the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 10

Ada said, “I would like to fix the book.” She fetched the tape from the bench. She used the tape to repair the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 11

Ada said, “I would like to fix the book.” Ada fetched the tape from the bench. Using the tape, Ada fixed the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 12

Ada said, “I would like to repair the book.” She fetched the tape from the bench. With the tape, Ada fixed the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 13

Ada said, “I want to repair the book.” She fetched the tape from the bench. Using the tape, she repaired the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 14

Ada said, “I want to fix the book.” She fetched the tape from the bench. She repaired the book with the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 15

Ada said, “I would like to fix the book.” She gave Omar the book. Ada fetched the tape from the bench. Omar gave Ada the book. Using the tape, Ada fixed the book.

`transfer(actor=ada, item=book, recipient=omar) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=omar, item=book, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 16

Ada said, “I would like to fix the book.” She fetched the tape from the bench. Using the tape, she fixed the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 17

Ada said, “I would like to fix the book.” Ada fetched the tape from the bench. She fixed the book with the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 18

Ada said, “I want to repair the book.” She fetched the tape from the bench. With the tape, she repaired the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### contextual, seed 19

Ada said, “I want to repair the book.” She fetched the tape from the bench. She fixed the book with the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### dialogue_prefix, seed 0

Ada said, “I want to repair the book.” Omar said, “I could help you.” Ada placed the book on the bench. Omar fetched the book from the bench. He fetched the tape from the bench. Omar fixed the book with the tape.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → fetch(actor=omar, item=tape, source=bench) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### dialogue_prefix, seed 1

Ada said, “I want to fix the book.” Omar said, “I can help you.” Ada fetched the tape from the bench. Using the tape, she repaired the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### dialogue_prefix, seed 2

Ada said, “I want to fix the book.” Omar said, “I could help you.” Ada handed the book to Omar. Omar placed the book on the bench. Ada fetched the tape from the bench. She handed Omar the tape. Omar fetched the book from the bench. With the tape, Omar repaired the book.

`transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### dialogue_prefix, seed 3

Ada said, “I would like to repair the book.” Omar told Ada, “I can help you.” Ada fetched the tape from the bench. She repaired the book with the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### dialogue_prefix, seed 4

Ada said, “I want to fix the book.” Omar said, “Let me help you.” Ada fetched the tape from the bench. She used the tape to repair the book.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [True].

### ending_predicate, seed 0

Ada said, “I want to repair the book.” She put the book on the bench. Omar fetched the tape from the bench. He gave Ada the tape. Ada fetched the book from the bench. Ada fixed the book with the tape. She put the book on the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=ada, item=book, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [True, True].

### ending_predicate, seed 1

Ada said, “I want to fix the book.” She placed the book on the bench. Omar fetched the tape from the bench. He handed Ada the tape. Ada fetched the book from the bench. Using the tape, Ada fixed the book. She placed the book on the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=ada, item=book, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [True, True].

### ending_predicate, seed 2

Ada said, “I want to fix the book.” She handed Omar the book. Omar put the book on the bench. Ada fetched the tape from the bench. Ada gave Omar the tape. Omar fetched the book from the bench. He fixed the book with the tape. Omar gave the tape to Ada. Omar put the book on the bench.

`transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=omar, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [True, True].

### ending_predicate, seed 3

Ada said, “I would like to repair the book.” She put the book on the bench. She fetched the tape from the bench. She handed the tape to Omar. Omar fetched the book from the bench. Using the tape, he repaired the book. He put the book on the bench. He gave Ada the tape.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape) → put_item(actor=omar, item=book, destination=bench) → transfer(actor=omar, item=tape, recipient=ada)`

Stop: sampled_stop; goal predicates: [True, True].

### ending_predicate, seed 4

Ada said, “I want to fix the book.” She placed the book on the bench. She fetched the tape from the bench. She gave the tape to Omar. Omar gave the tape to Ada. Ada fetched the book from the bench. Ada used the tape to repair the book. She gave the book to Omar. Omar placed the book on the bench.

`put_item(actor=ada, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=ada, item=book, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [True, True].

### no_prefix, seed 0

Ada gave the book to Omar. Omar put the book on the bench. Omar fetched the tape from the bench. He gave Ada the tape. He fetched the book from the bench. Omar gave Ada the book. Ada repaired the book with the tape. Ada placed the book on the bench. Ada gave Omar the tape. She fetched the book from the bench.

`transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=omar, item=tape, source=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=omar, item=book, source=bench) → transfer(actor=omar, item=book, recipient=ada) → patch_paper(actor=ada, item=book, tool=tape) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=ada, item=book, source=bench)`

Stop: sampled_stop; goal predicates: [].

### no_prefix, seed 1

Ada fetched the tape from the bench. She placed the book on the bench. Omar fetched the book from the bench. Ada handed Omar the tape. Using the tape, Omar repaired the book. He gave Ada the book. Ada gave Omar the book.

`fetch(actor=ada, item=tape, source=bench) → put_item(actor=ada, item=book, destination=bench) → fetch(actor=omar, item=book, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → patch_paper(actor=omar, item=book, tool=tape) → transfer(actor=omar, item=book, recipient=ada) → transfer(actor=ada, item=book, recipient=omar)`

Stop: sampled_stop; goal predicates: [].

### no_prefix, seed 2

Ada gave the book to Omar. Omar put the book on the bench. Ada fetched the tape from the bench. She gave Omar the tape. Omar fetched the book from the bench. He fixed the book with the tape.

`transfer(actor=ada, item=book, recipient=omar) → put_item(actor=omar, item=book, destination=bench) → fetch(actor=ada, item=tape, source=bench) → transfer(actor=ada, item=tape, recipient=omar) → fetch(actor=omar, item=book, source=bench) → patch_paper(actor=omar, item=book, tool=tape)`

Stop: sampled_stop; goal predicates: [].

### no_prefix, seed 3

Ada fetched the tape from the bench. She repaired the book with the tape. She gave Omar the tape. She handed the book to Omar. Omar gave Ada the tape. He put the book on the bench. Ada handed Omar the tape.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → transfer(actor=ada, item=tape, recipient=omar) → transfer(actor=ada, item=book, recipient=omar) → transfer(actor=omar, item=tape, recipient=ada) → put_item(actor=omar, item=book, destination=bench) → transfer(actor=ada, item=tape, recipient=omar)`

Stop: sampled_stop; goal predicates: [].

### no_prefix, seed 4

Ada fetched the tape from the bench. With the tape, Ada repaired the book. She handed Omar the tape. She placed the book on the bench. Omar gave the tape to Ada. He fetched the book from the bench.

`fetch(actor=ada, item=tape, source=bench) → patch_paper(actor=ada, item=book, tool=tape) → transfer(actor=ada, item=tape, recipient=omar) → put_item(actor=ada, item=book, destination=bench) → transfer(actor=omar, item=tape, recipient=ada) → fetch(actor=omar, item=book, source=bench)`

Stop: sampled_stop; goal predicates: [].

### craft_no_plan, seed 0

With the shaping rib, Ada shaped the cup.

`shape_clay(actor=ada, item=clay, tool=rib)`

Stop: sampled_stop; goal predicates: [].

### craft_no_plan, seed 1

Ada fetched the ladder from the bench. Ada steadied the ladder.

`prepare_support(actor=ada, item=ladder, source=bench)`

Stop: sampled_stop; goal predicates: [].

### craft_no_plan, seed 2

Ada gave the book to Omar. Using the shaping rib, Ada shaped the cup. Ada fetched the ladder from the bench. She steadied the ladder. She played the drum.

`transfer(actor=ada, item=book, recipient=omar) → shape_clay(actor=ada, item=clay, tool=rib) → prepare_support(actor=ada, item=ladder, source=bench) → perform_solo(actor=ada, item=drum)`

Stop: sampled_stop; goal predicates: [].

### craft_no_plan, seed 3

Omar fetched the ladder from the bench. He handed the ladder to Ada. Ada fixed the tap. She shaped the cup with the shaping rib. She held the atlas. She drew the moon on the paper with the pencil. Omar fetched the tape from the bench. Ada put the book on the bench.

`fetch(actor=omar, item=ladder, source=bench) → transfer(actor=omar, item=ladder, recipient=ada) → repair_fixture(actor=ada, item=tap) → shape_clay(actor=ada, item=clay, tool=rib) → sketch_moon(actor=ada, item=sheet, tool=pencil, reference=atlas) → fetch(actor=omar, item=tape, source=bench) → put_item(actor=ada, item=book, destination=bench)`

Stop: sampled_stop; goal predicates: [].

### craft_no_plan, seed 4

Omar fetched the ladder from the bench. Ada placed the book on the bench. She repaired the tap. She played the drum. She placed the drum on the bench. She held the atlas. She drew the moon on the paper with the pencil.

`fetch(actor=omar, item=ladder, source=bench) → put_item(actor=ada, item=book, destination=bench) → repair_fixture(actor=ada, item=tap) → perform_solo(actor=ada, item=drum) → put_item(actor=ada, item=drum, destination=bench) → sketch_moon(actor=ada, item=sheet, tool=pencil, reference=atlas)`

Stop: sampled_stop; goal predicates: [].

## Interpretation and limitations

The loop can make physical progress without an authored suffix. A source-compatible event is still only a candidate: all target guards are checked on the current world after every commit. All selected segments are independently replay-verified.

The policy can still stop early, wander, or hit the cap. A sampled stop is not a solved-world flag. Short successful repairs remain miniature action sequences: thin premise, little emotional development, and usually no concluding image unless a final-state condition is supplied. Unconstrained craft samples may jump between unrelated activities. No prose-quality improvement is claimed from success rates alone.

Attention factors are hand-authored state/history features, not learned heads or corpus trigram statistics. There is no automatic missing-entity import, broad intention understanding, multi-step planning or source-order continuation prior. The one-step lookahead asks only whether a proposed move enables a directly goal-satisfying next event. All event probabilities, factors, source references, word distributions and token attributes are in traces.jsonl.gz.
