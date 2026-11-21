# Port provenance and reference fixtures

`upstream/` contains unmodified GF RGL English source files downloaded from tag
`20260403`. `manifest.json` records their URLs and SHA-256 hashes.
`GF-RGL-LICENSE` retains the complete upstream license/copyright notice.
The Python modules are selected, explicitly restricted adaptations, not a
translation of every case in these files.

Codeco mechanisms were independently implemented from the description in
Tobias Kuhn, *A Principled Approach to Grammars for Controlled Natural Languages
and Predictive Editors*: https://arxiv.org/abs/1211.3643. No ACE rule inventory
or Codeco implementation was copied.

`oracle/` contains the small GF application grammar used **offline** to produce
the 51 reference cases in `gf_oracle.json`. With GF 3.12 and RGL 20260403 installed,
compile `oracle/StoryLexEng.gf` against the RGL's `alltenses` and `prelude` paths.
Linearize the stored `gf_expression` values using its `StoryLexEng` concrete.
The stored PGF hash identifies the reference binary; the binary is not shipped.
The oracle stubs are test fixtures, not part of the Python generation path and
not examples of a fully validated GF application lexicon. Tests normalize only
capitalization and seven standard negative contractions.

`pre_holdout_freeze.json` records the development/held-out boundary. Future
intentional shared-rule changes should establish a new transfer experiment;
do not silently rewrite this result's provenance to make a changed port pass.
