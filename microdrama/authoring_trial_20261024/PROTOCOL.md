# Two-author trial: 24 October 2026

Question: can a narrowly specified authoring assignment produce useful new
microdramas with GPT-6.1 Sol at low reasoning effort, reusing the existing engine?
This is a feasibility trial with two authors, not a cost or scaling benchmark.

## Fixed before dispatch

- Model: `gpt-6.1-sol`; reasoning: `low` (interpreting the user's “light”).
- Fresh agent context (`fork_turns=none`), common saved prompt and engine, separate
  directories. No access to the other candidate requested or needed.
- Shared prompt: `microdrama/AUTHORING_PROMPT.md`.
- Candidate A: a jammed floodgate, threatened grain, a blamed newcomer, an old
  maintenance diagram, and a task requiring practical understanding and help.
- Candidate B: orchard frost, a mistaken explanation for damaged blossoms, a
  field notebook, a shelter trial, and coordinated use of a borrowed resource.
- Shared contract: build world, offer encounters, render committed snapshots,
  produce historical-evidence questions. No changes to engine or evaluator.
- Inputs: access, cooperation, distraction; eight combinations, seeds 0–4.
- Frozen mechanical evaluator: `evaluate.py`. It saves all eight seed-zero texts,
  not just successes chosen for presentation, and records every failed grid case.

Authors may test and revise their own work before first submission. Their notes
should identify those repairs. A “first submission” means the first version they
report complete, not their first code attempt. On completion the parent copies
it into `first_submissions/` before independent inspection or repair requests.

## Parent review, separate from author self-tests

1. Run the common evaluator and candidate self-tests. Inspect the tests before
   accepting their conclusions. Confirm fixed inputs and engine were unchanged.
2. Read a successful, a partial, and a failed case when available, including QA.
   Check premise, causal turn, reference continuity, and a concrete ending image.
3. Inspect actual transmission and trial code: no unembedded knowledge, no
   truth overwritten by a rumor, no possession created by merely mentioning it.
4. Inspect reusable bindings and their tests. Distinguish shared execution
   infrastructure from truly reusable narrative practices and discourse.
5. Check a model-specific intervention independently of the advertised input
   combinations. A physical result must depend on the relevant physical state,
   not solely on an ending label or direct parameter-to-prose selection.
6. Preserve first submissions, list repair requests verbatim, and distinguish
   author repairs from parent repairs. Report limitations even when checks pass.

The evaluator verifies exact facts and exposure annotations, not whether every
English sentence entails the annotation. The parent reading pass addresses that
gap, incompletely. No automatic score is described as literary quality.

## What would justify expanding the experiment

Both authors produce coherent, inspectable stories with useful counterfactuals;
failures require local repair rather than rewriting the whole program. This
supports trying more authors under the same contract. It does not establish
that independent modules compose with one another, that 10,000 authors are
economical, or that their output is valuable training data. A later trial needs
common narrative practices, held-out worlds, and measured integration costs.
