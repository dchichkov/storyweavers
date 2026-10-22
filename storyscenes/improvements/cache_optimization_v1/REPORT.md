# Cache optimization with a 7.75 quality target

## Decision

Keep the historical 7.75/9 benchmark and its generators. The default is now
`--cost-profile cache-only`: original world/prose prompts, roles, schemas,
reasoning and output caps, with explicit-only caching and no breakpoints for
one-use requests. It avoids cache-write fees without shortening prose context.
The original world authoring contract is restored byte-for-byte from the
checkpoint. New prefix/contract and factored-prose variants remain opt-in.

This is not a claim that new generations are guaranteed to score 7.75. That
benchmark covers only two worlds and twenty graded stories. The prompt-changing
experiments did not establish that level across the broader trial; their cheaper
output is not promoted.

## Frozen-world prose comparisons

Same library-parade and pond-concert mechanics, same uniform ten sampled
positions per world, same 0–9 Terra/Flex rubric and calibration. All three
original pinned traces per world replayed exactly before grading. These runs
pay for new prose and evaluation, not for new mechanics.

| Prose configuration | Overall /9 | Input tokens | Output tokens | Prose authoring USD |
| --- | ---: | ---: | ---: | ---: |
| Historical full context | 7.75 | 34,697 | 3,337 | 0.006339 |
| Factored v1, low reasoning | 6.65 | 8,356 | 2,807 | 0.002303 |
| Factored v2, explicit conditions + medium reasoning | 7.50 | 17,982 | 3,497 | 0.003813 |
| Full-context repeat, low reasoning | 7.30 | 39,448 | 3,367 | 0.005965 |

The first reduction saved 63.7% of prose authoring cost but introduced wrong
recipient wishes and windy/still contradictions. Restoring explicit conditions
and reasoning improved the inspected branches, without recovering 7.75.

The full-context repeat retains the original prose instructions/model settings.
A stronger ending-guard fix already present before this cache pass adds conditions
compared with the historical request; the repeat is not an exact-byte historical
prompt replay. The first two factored trials also moved unchanged judge
calibration into a developer prefix; the final/default evaluator retains the
original system/user message layout. Both confounds and stochastic grading limit
causal attribution. Actual contradictory prose was inspected, not inferred only
from score differences. See [manual readings](manual_review.md).

## Request-preserving savings

For the historical complete token mix, including failed mechanics and all bounded
recovery requests, disabling cache writes and foregoing old cache reads would
change estimated list-price cost as follows:

| Phase | Recorded baseline USD | Same tokens, cache-only USD | Reduction |
| --- | ---: | ---: | ---: |
| Authoring | 0.020367 | 0.019220 | 5.6% |
| Evaluation | 0.027018 | 0.023880 | 11.6% |
| Combined | 0.047385 | 0.043100 | 9.0% |

This is a counterfactual at the recorded token volumes, not a new billed run or a
promise about future token counts. Full-context trial responses confirm zero
cache-write tokens under the new transport policy. The authoring-equivalence
test executes valid legacy and cache-only worlds and compares entire API request
bodies, ignoring only `prompt_cache_options`; the judge test does the same.

Explicit prefix reuse also works across different worlds: the first ten-world
factored trial read 56,796 cached tokens out of 115,063 authoring inputs (49.4%),
with only 1,444 written tokens and 40/41 requests hitting cache. Those savings
belong to the experimental prompt layout, not to the conservative default.
Do not maximize cache-hit percentage at the expense of story quality.

## Implementation and physical state

- `api_requests.py` separates canonical HTTP JSON from the installed SDK's
  `extra_body` transport, supports stable prefix breakpoints and no-write mode.
- World cache keys include contract/model/schema/reasoning fingerprints. Seeds,
  definitions, repair feedback and prose follow the reusable prefix.
- Default prose retains full world/traces/conditions and original hashed card
  IDs. Experimental aliases map locally back to exact IDs; missing, duplicate
  and unknown IDs fail closed, and text repairs require exact old wording.
- Known simultaneous structural errors are reported together before a paid
  repair. Bounded named null patches can delete mistaken reserved definitions.
- Outcome checks now inspect actual event history, so a loan that is used and
  returned is not rejected just because initial and final ownership agree.

This follows the memeplex north star by using physical carriers and executed
state/history, rather than inventing entities or rewriting English to hide a
failed simulation. Search legality and semantic-diversity gates stay in place.
Runtime generation remains offline. Luna authors and repairs; Terra only grades.
No full Python-script or stronger-model authoring fallback is used.

## Trial accounting and limitations

The low-reasoning pilot stopped after poor mechanics results: six worlds received
API calls, four completed their attempted pipelines, one produced stories; two
were deliberately stopped between stages and four of the planned ten were never
dispatched. Its nineteen returned requests cost $0.018071. Do not report it as
ten failed attempts or hide its cost.

The first fresh ten-world trial completed 4/10 worlds, generated 400 stories and
graded forty: 7.20/9. Authoring cost $0.046208 including failures/repairs;
evaluation $0.043794; total $0.090002. The later structural preflight, clarified
contract and history-based outcome fix were not in that frozen run.

Final ten-world results and complete campaign accounting are appended below.
Prices throughout are returned-usage list-price estimates, not invoice
reconciliation. Response payer metadata varies. Flex is required with no standard
fallback. Unknown outcomes retain conservative reservations and are never priced
as zero. The campaign limit is $15; all attempts use the existing ledger.

Pricing and cache policy references: [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), and
[Flex processing](https://developers.openai.com/api/docs/guides/flex-processing).
Machine-readable evidence: [ablations.json](ablations.json),
[first ten-world comparison](intermediate_v2/comparison.json).

## Final ten-world trial: full prose context

`compact_cached_v3` uses the clarified experimental world contract, medium Luna
world reasoning, full-context low-reasoning prose, and request-preserving Terra
evaluation. It generated **8/10 worlds**, 800 saved stories and **80 judged stories**.
The exact original design briefs/seeds are preserved for the baseline theaters.

| Measurement | Result |
| --- | ---: |
| Overall quality, all eight worlds | 7.1875/9 |
| Same two baseline theaters | 7.95/9 (baseline 7.75) |
| Diversity, all eight | 2.375/9 |
| Stories below 6 | 11/80 |
| Fresh-seed verification | 7/8 completed worlds |
| Authoring, returned usage including repairs/failures | $0.052181 |
| Evaluation | $0.097155 |
| Total returned-usage estimate | $0.149336 |
| Additional unresolved reservation | $0.020002 |

| World | Quality /9 | Fresh seeds |
| --- | ---: | --- |
| roof_post | 7.00 | 100 passed |
| library_parade | 8.00 | 100 passed |
| pond_concert | 7.90 | 100 passed |
| night_garden | 7.10 | 100 passed |
| bakery_exchange | 7.20 | failed ending coverage |
| museum_of_small_things | 8.00 | 100 passed |
| hill_picnic | 7.40 | 100 passed |
| clocktower_club | 4.90 | 100 passed |

The matched pair clears 7.75 in this particular fresh-world draw; this is useful
evidence, but its regenerated mechanics differ from the frozen prose ablations.
The broader set remains below the desired level. Do not compare the overall
eight-world mean directly with the original two-world mean as a matched quality
regression, or conceal the clocktower (4.90) to make the mean look better.
The conservative cache-only default stays selected.

Kite-workshop has an unanswered connection-error request; its $0.020002 local
reservation remains in the ledger. Puppet-weather exhausted its three bounded
mechanics patches. No extra paid retry or stronger-model fallback followed.
Bakery completed its saved pool but failed fresh-seed ending coverage. Its grade
and cost remain in the totals, while unrestricted generation is not accepted.

The 24 returned authoring calls used 196,390 input and 57,282 output tokens
(23,620 reasoning tokens included). There were 21,697 cached reads (11.05%) and
5,007 cache writes; the eight evaluation calls had zero cache writes. Full prose
dominates this input mix, so overall cache fraction is lower than the factored
experiment even though the world prefix is reused.

Authoring cost per generated world is $0.006523 before the unknown
charge. Per fresh-verified world it is $0.007454, or
$0.010312 including the full conservative reservation.
These are mechanical completion costs, not costs per literary acceptance or
reliable projections for 20,000 good worlds.

## Complete development accounting and checks

All six new run directories total **$0.340305** in returned-usage estimates
plus **$0.020002** reserved for one uncertain outcome. This includes the stopped
low-reasoning pilot, rejected intermediate ten-world trial, all three prose
comparisons, final ten-world trial, all bounded repairs and all eighteen set
judges. All **108 returned responses** report Flex; the unanswered request’s
returned service tier and usage are unknown.

The campaign ledger now commits **$1.764083 of $15**, including
earlier work and historical unknown-outcome reservations.

- **72 offline tests pass**, including exact cache-only/legacy request comparison,
  canonical SDK HTTP transport, stable cache keys, alias integrity, stale repairs,
  named deletion, and actual loan/return history.
- New final-run verification: seven worlds each pass three exact pinned replays
  plus 100 fresh seeds. Bakery fails closed on an unrepresented ending state;
  this known limitation is not counted as a passing check.
- The full-context two-world comparison passes six pins and 200 fresh seeds.
- Earlier ten-world generators passed 30 pins and 1,000 fresh seeds; they were
  not rewritten. The original benchmark replay result is also saved separately.
- Python compilation and whitespace checks passed. Changes are confined to
  Storyscenes; unrelated workspace changes were left alone.

Detailed evidence: [final comparison](final_v3/comparison.json),
[full accounting](accounting.json), [quality decision](quality_gate.json),
[baseline replays](baseline_replays.json), and [test log](tests.txt).
