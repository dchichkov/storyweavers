# The Honest Mark

A standard-library-only fruit-market adventure. Nella borrows a dial scale while filling Mrs. Vale’s apple order, finds that the scale adds weight, and must choose whether to disclose the short measure. The `kite` package name is only the isolated harness path; this pack has no kite plot.

## Run it

From the repository root:

```text
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py /path/to/repository
```

The `--params` option accepts a path to a JSON object of parameter overrides. For example, a file containing `{"scale_bias_units":2,"order_units":12,"apples_stock_units":11,"scale_wobbles":false,"neighbor_will_mix":true}` gives the scale an error, a twelve-unit order, eleven apple units, a steady dial, and a neighbor willing to accept a blend. The command-line generator chooses a compatible decision and route; use `replay` for an exact chosen route.

## Explicit ending recipes

Amounts are in 100-gram units. These short recipes use a seven-scene route without optional vignettes; append either vignette immediately after `market_order` for an eight-scene version.

```python
from storyscenes.mini_adventures.kite.world import Parameters, replay

prefix = ('market_order', 'fill_order', 'inspect_scale')
suffix = ('settle_order', 'return_scale', 'ending')

# Correct all-apple order, disclosed before the neighbor has to ask.
p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20,
               neighbor_will_mix=False)
full = replay(p, prefix + ('tell_neighbor',) + suffix)
assert full[-1].after['story.outcome'] == 'honest_full'

# One apple unit is unavailable; the neighbor accepts enough pears to complete the weight.
p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
               neighbor_will_mix=True)
mixed = replay(p, prefix + ('tell_neighbor',) + suffix)
assert mixed[-1].after['story.outcome'] == 'honest_mixed'

# Same shortage, but the neighbor declines pears: payment is returned and the sale ends.
p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
               neighbor_will_mix=False)
refunded = replay(p, prefix + ('tell_neighbor',) + suffix)
assert refunded[-1].after['story.outcome'] == 'honest_refunded'

# Enough stock remains to correct a concealed error after Mrs. Vale catches it.
p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20,
               neighbor_will_mix=False)
repaired = replay(p, prefix + ('conceal_error',) + suffix)
assert repaired[-1].after['story.outcome'] == 'repaired_after_concealment_full'
```

The concealment route does not quietly succeed: Mrs. Vale reweighs the basket, returns, and the helper apologizes. If the order cannot be completed, the refund ending is a completed loss rather than a promise that something might be fixed later. In every ending Nella resets, verifies, and returns the borrowed scale.

## Design and limitations

`world.py` owns strict keyword-only parameters, world validation, guarded scene selection, exact replay, and the command line. `prose.py` renders from the enacted state and outcome. Every committed local action uses the supplied `storyscenes.mini_adventures.local_play.LocalPlay`; candidate paths are bounded and discarded branches do not mutate their caller.

Seven scenes use the six required encounter steps and one ending. Eight scenes add exactly one of two optional vignettes: sharing a bruised apple consumes one apple, and offering a pear sample consumes one pear and can change the neighbor’s preference. The scale bias, scale wobble, order size, stock, and neighbor preference are validated parameters. The inventory maps consolidated reference beats to executable scenes rather than claiming each beat is independently playable.

This is a small scenario-specific model, not a general market simulator. It models whole 100-gram units, one scale error direction, a fixed pear reserve, one neighbor, and one order. Text is authored locally; there is no LLM, network access, or runtime API. The generated routes vary in enacted choices and consequences, not names or synonym swaps. Prose quality and route diversity still require human reading.

Reference story length: approximately 1,000 prose words, excluding its heading. This count is not machine-verified.

## Verification status

Tests were **not run**: this single-response run had no execution tools. In particular, neither the unit-test command nor the supplied read-only `check_pack.py` integration check was executed. The test file includes both scene lengths over 100 seeds, replay and trace reconstruction, parameter validation, failed-action atomicity, optional-scene effects, object/inventory continuity, and paired counterfactuals. Those are test intentions, not claimed results.
