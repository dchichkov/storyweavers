# Classical grammar autocomplete experiment

This probes the existing **Grammatical Framework (GF)** Phrasebook grammar. It
does not implement a new grammar, add rules to GF, or modify Storyweavers' engines.
It tests the next step beyond `word_distribution_demo.py`: let a real incremental
parser determine the available continuations instead of using eight fixed slots.

The public grammar reported **362 abstract constructors, 49 categories, and 13
languages**. These are grammar metadata counts, **not counts of production rules
or a measured 362x increase in capability**. Only English's `Sentence` category
was tested. This is controlled phrasebook English, not unrestricted story prose.

## Reproduce

From the repository root:

```sh
.venv/bin/python grammar_completion_experiment/probe.py
.venv/bin/python grammar_completion_experiment/probe.py --verify
.venv/bin/python grammar_completion_experiment/probe.py --prefix 'she wants to eat bread' --json
```

These commands replay `observations.json` entirely offline. To repeat the live
experiment or add another prefix:

```sh
.venv/bin/python grammar_completion_experiment/probe.py --refresh
.venv/bin/python grammar_completion_experiment/probe.py --refresh --prefix 'she can'
```

Refresh sends only the synthetic prefixes to the public GF service; availability
and results may change. Raw responses, grammar metadata, and a UTC timestamp are
saved. All requests must succeed before the existing fixture is replaced.

## Observations

| Prefix | Legal next words | Complete sentence already? |
|---|---:|---|
| she | 29 | No |
| she wants | 90 | No |
| she wants to | 14 | No |
| she wants to eat | 91 | Yes |
| she wants to eat the | 46 | No |
| she wants to eat bread | 3 | Yes |
| she are | 0 | No |
| they is | 0 | No |
| she wants to eats | 0 | No |

The grammar permits both `she wants bread` and `she wants to eat`: the next
grammatical category depends on the words selected. It also distinguishes a
complete sentence with optional continuations from an unfinished phrase.

After `she wants to eat bread`, the choices are `and`, `at`, `in`, or stopping.
The probe assigns each 25% as an explicit **uniform baseline**. GF's completion
API supplies legal words, not their probabilities. Full support is retained;
displaying a few examples does not renormalize the distribution over those examples.
Stopping is included only when the separate parse request returns a syntax tree.

The important negative result: **`she wants to eat beer` also parses**. Broadening
syntax does not supply the physical affordances or narrative preferences needed
for story generation. The parser does provide structured output we could align
with executable world events, e.g. an action for a person wanting to eat an object.

## Next measurable experiment

Combine grammar-derived legal continuations with grounded world and prefix scores.
Compare uniform grammar-only sampling against that weighted generator. Measure
completion rate, structural diversity, unsupported entities/actions, latency, and
held-out next-word log loss if reference distributions or observations exist.
Track grammatical coverage separately from calibration and semantic correctness.
This probe establishes reuse feasibility; it is not that integrated generator yet.

## Sources

- [GF completion API](https://cloud.grammaticalframework.org/gf-web-api.html)
- [GF Resource Grammar Library tutorial](https://www.grammaticalframework.org/lib/doc/rgl-tutorial/index.html)
- [Live grammar metadata](https://cloud.grammaticalframework.org/grammars/Phrasebook.pgf?command=grammar)
- [Codeco: controlled language grammars for predictive editors](https://arxiv.org/abs/1103.5676)

Codeco is another classical predictive-grammar approach; it was researched but
not executed in this experiment. LanguageTool's documented proofreading API is
an error-checking interface, not the next-word completion service used here.
