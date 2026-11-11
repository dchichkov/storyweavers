# Prefix-only Luna/Flex smoke check — November 7, 2026

Command from the repository root:

```sh
.venv/bin/python -m storyformers.annotate_prefixes \
  --story 'Lily took scissors.' \
  --out storyformers/runs/prefix_annotation_live_20261107 --concurrency 2
```

All three responses were completed on `gpt-6-luna`, served on `flex`, and passed
single-record and assembled-stream validation. Frozen requests and raw responses
are under [the story directory](000000_9206fcbbc069/). The examples include this
short scenario, so this is a contract/cache smoke check rather than a held-out
semantic-quality evaluation.

| Prefix | Input tokens | Cached tokens | Cache-write tokens | Output tokens | Request duration |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lily | 3,648 | 0 | 3,628 | 100 | 9.05 s |
| Lily took | 3,690 | 3,628 | 42 | 114 | 9.46 s |
| Lily took scissors | 3,732 | 3,670 | 42 | 105 | 9.55 s |

The first request warmed the cache. The two longer requests started about 0.002
seconds apart and overlapped. End-to-end dispatch/validation took 18.95 seconds;
the sum of the individual observed request durations was 28.06 seconds. This
shows actual overlap, not a controlled comparison with full-story annotation.
Raw `usage.input_tokens_details` records both cache reads and writes. The
longest request reused a prefix through `took`, not only the fixed instructions.

Selected fields from accepted word records:

```json
[
  {"token":"Lily","pos":"n","entity":"person","entity_id":"e1","event":null},
  {"token":"took","pos":"v","event":"obtain object","event_id":"ev3","actor":"Lily","patients":[]},
  {"token":"scissors","pos":"n","entity":"scissors","entity_id":"e5","event":"obtain object","event_id":"ev3","role":"patient","location":"Lily"}
]
```

The verb record contains no future scissors argument. Lily has no future event
link. Scissors links to the preceding event only when it appears, and no repair
purpose is inferred. Two spaces and the final period were synthesized locally,
giving six total records that reconstruct `Lily took scissors.` exactly. Their
global positions are 0 through 5; scissors is position 4. No API request contains
the final period or any other future suffix for its target word.

Repeating the command reuses the saved responses without additional requests.
The original measured timing remains in this report; rerunning updates the
root summary's local revalidation time.
