# Complete Luna/Flex causal annotation run

Completed all 753 words of the [trail story](../catalog_annotation_20261107/inputs/18_trail/story.txt).
The assembled stream has 1,673 lossless records: 753 model-annotated words and
920 locally generated spaces/punctuation records. Positions are computed locally.

## Measured usage

| Measurement | Result |
| --- | ---: |
| Accepted words | 753 / 753 |
| Provider responses | 853 |
| Validation correction responses | 100 |
| Words needing correction | 86 (11.4%) |
| Input tokens across all responses | 65,977,432 |
| Cached input tokens | 64,399,448 (97.61%) |
| Cache-write tokens, 30-minute TTL | 114,990 |
| Other uncached input tokens | 1,462,994 |
| Output tokens, including reasoning | 301,467 |
| Reasoning tokens | 206,411 |
| Visible JSON output tokens | 95,056 |
| Calculated API cost | **$0.4777** |
| Peak concurrent requests | 16 |
| First dispatch to last completion, including recovery pause | 17 minutes 25 seconds |
| Definite Flex capacity rejections, retried without changing tier | 56 |

Cost is calculated from recorded usage and the published Luna/Flex prices,
not an account invoice. The USD-per-million rates are $0.05 ordinary input,
$0.005 cached input, $0.0625 for 30-minute cache writes, and $0.25 output.
Cost breakdown: $0.3220 cache reads, $0.0731 ordinary input, $0.0072 cache writes,
and $0.0754 output. Every rejected JSON response and its correction is included.
Source: [OpenAI Flex pricing](https://developers.openai.com/api/docs/pricing?latest-pricing=flex),
checked November 8, 2026.

The earlier $0.35 baseline underestimated correction overhead; the $0.50 planning
allowance covered this run. The full catalog prompt and exact growing prefix
are present in every request. Corrections add a validation error, rejected draft,
and allowed-anchor list after the cached prefix, increasing uncached input usage.

## Attributes

There are 6,008 top-level field occurrences across the word records: **7.98 per
word**, median 7, range 3–18, using **98 distinct field names**. These counts include
`pos`, `lemma`, and `scope_id`, giving about five additional fields per word.
They exclude token text, indices, offsets, positions and reserved supporting
metadata. Nested bundles count as one field rather than counting every leaf.

The prompt offers 1,024 canonical fields plus seven agreed extensions, with no
density quota. No new attribute definitions were proposed in this run. Six
boolean-valued field names were used, including `reference_introduction` and
`reference_unresolved`. Full field frequencies are in the measured metrics.

## Validation and semantic review

All 753 accepted records pass local catalog/type/reference validation. The
assembled text reconstructs the source exactly, and positions align with the
lossless token indices. Every original and correction request was checked against
the exact source prefix ending at its target word. Accepted records match the
saved provider JSON; none was manually rewritten. Supporting references remain
per-prefix snapshots, without retroactively updating earlier words.

Manual inspection of selected records from the beginning, middle and ending
found meaningful semantic defects despite structural validity:

- **Entity IDs drift:** the same named character appears under 8 IDs for Nia,
  7 for Felix, 7 for Leni, and 4 for Ivo across reference snapshots. The earliest
  mention convention is not consistently followed.
- **Speaker/actor confusion:** `Borrow` assigns the likely speaker Ivo as borrower.
- **Scope errors:** desired/negated/conditional content can lose its parent scope;
  one `Not` attaches to an earlier closed quotation.
- **Attribute convention drift:** modal auxiliary classes include `ability_family`,
  `possibility_family` and `possibility` despite the requested lexical convention.
- **Representation confusion:** the ending does not preserve the distinction
  between sketchbook imagery and the physical salamander/trail marker.

Useful behavior also appears: incomplete verbs keep unknown patients empty;
later participants update only their own snapshots; compass references can reuse
the original ID across many sentences; desired proving is not labeled as an
accomplished act; north is treated as direction without inventing travel.

This run establishes end-to-end completion and measured cost. Its labels need
semantic consistency work before being treated as reliable training targets.
The review is a spot-check, not a comprehensive accuracy score.

## Recovery and verification

The initial invocation stopped after its second wave on Flex capacity failures
and an exhausted one-correction limit. Existing responses were retained. The
runner now supports `--validation-repairs N` (default remains one); this run
resumed with a cap of three. Of 753 words, 667 needed no correction, 73 needed
one, 12 needed two, and one needed three. Each correction is journaled separately
and uses the original prefix plus only its latest rejected draft.

Definite `429 flex_unavailable` retries now allow up to five retries with bounded
backoff. Ambiguous dispatch failures, incomplete responses, refusals and wrong
tiers still fail closed. The prompt, model, reasoning effort and original frozen
requests were unchanged during recovery. All 22 prefix/catalog runner tests pass,
including multiple-correction accounting and credential-free response reuse.

## Artifacts

- [Annotations](000000_744d68e4483a/annotations.json): complete residual records.
- [Reference snapshots](000000_744d68e4483a/reference_snapshots.json): per-position supporting tables and evidence.
- [Measured metrics](measured_metrics.json): usage, pricing, attribute frequencies, ID variants and validation results.
- [Semantic review](semantic_review.json): concrete inspected indices and defects.
- `prompt.json`, `manifest.json`, `summary.json`, `run.log`, and each prefix's
  request/response/attempt/correction files retain provenance.

Reproduce the local audit without API calls:

```sh
.venv/bin/python -m storyformers.runs.prefix_catalog_full_story_20261108.audit --verify
```
