# Classic references and composable seed ingredients

The precedent is `storyworlds/seed.py`: deterministic pools of vocabulary,
settings, narrative features and styles. `storyscripts/cautionary.py` and the
other family scripts also vary cast, objects, scenario branches and endings,
but generally render within a fixed story family. The previous Storyscenes
batch instead cycled through ten fixed theater premises.

`seed_mixer.py` extends the pool approach with ten independent lists. All 210
entries are hand-authored hints; the classic references identify familiar
structures without reproducing source passages or importing any catalogue.

Each world draws **three distinct lists uniformly at random**, then **one item
from each selected list**: exactly three ingredients, without mandatory categories.
The author supplies the remaining details. Both authoring stages receive only
those selected ingredients plus the required vocabulary words.

The ten available lists are classic references, motives, kernels, themes, cast
relationships, settings/everyday situations, props, complications, styles, and ending possibilities.

The settings list includes 96 everyday situations alongside the ten original
settings: school, shopping, classic games, videogames, books, home life, visits,
outings, doctor/dentist visits, other appointments, and errands. Everyday situations are optional ingredients, not mandatory lessons
or additional draws. The three-list/one-item sampling rule is unchanged.

Generate briefs locally, without API calls:

```bash
.venv/bin/python storyscenes/seed_mixer.py --seed 20260909 -n 10 \
  --out storyscenes/examples/seed_mix_v5/briefs.json
```

Read the [ten sampled briefs](examples/seed_mix_v5/briefs.md). Their IDs and
chosen hints are also recorded in JSON. Sampling is reproducible; repeated combinations are possible and are not
rejected or silently redrawn.

To use them in a future paid trial:

```bash
.venv/bin/python storyscenes/compact_workshop.py \
  --out storyscenes/runs/classic_mix_trial \
  --seed-source mix --seed 20260909 --count 10 \
  --cost-profile cache-only --evaluate --api-key-file .API_KEY
```

The existing Luna/Flex budget and bounded repairs still apply. `--seed-source
theaters` remains the baseline/default. Source choice and mixer hash are frozen
in mixed-run settings, and `briefs.json` records every draw. Existing runs and
the legacy scripts are unchanged.

The mechanics stage already receives the complete design brief. The prose
stage also receives the same three selected ingredients, including the experimental factored-prose path. This
prevents style choices from disappearing after mechanics generation. Validated
state takes precedence over any requested ending when rendering a given path.

No new worlds were authored for this change. The 138 passing tests verify the
pool sampler, deterministic prefixes, selection structure, legacy behavior and
existing engine tests. They do not establish story quality or style adherence.
Rhyme and first-person narration also need QA evaluation in the next trial.

## Required vocabulary

Each brief also draws **1–3 distinct words** uniformly from the same 8,443-word
CHILDES vocabulary used by `storyworlds/seed.py`. The file is copied into
`storyscenes/childes_eng_na_vocab.txt`, so this mixer does not depend on the
older directory at runtime. The three list selections still happen first and
are unchanged by the additional word draw.

Required words are recorded in `words`, included in the mechanics brief, and
passed explicitly to the prose stage and its repair context (including the
factored-prose path). The instruction asks for every word naturally in every
story. The vocabulary hash is recorded in the brief and mixed-run settings;
the vocabulary is included in the frozen authoring snapshot.

This restores the seed/prompt requirement. No new story-authoring run has been
performed, and word presence in generated stories is not yet an automated
acceptance gate. The existing simulation, prose validation, QA, and evaluation
stages otherwise remain unchanged.
