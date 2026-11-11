# Per-token events and physical locations

Contract `storyformers-annotation-v2` adds `location` and copies the event label
onto participating entity tokens. Event IDs and one action trigger still support
validation; noun dictionaries can be read directly without joining to a verb.
Six authored examples teach consistent roles, locations and event names.

Two completed Luna/Flex/low requests passed validation and were read with the
original stories. Both arrays reconstruct their complete input exactly.

| Story | Words | Cached tokens | Cache writes |
| --- | ---: | ---: | ---: |
| Lily obtains tools and mends her coat | 18 | 0 | 8,639 |
| Ben gives Ava a needle, which Ava returns | 11 | 8,639 | 0 |

Actual selected fields from the first story:

```json
{
  "token": "scissors",
  "pos": "n",
  "entity": "scissors",
  "role": "patient",
  "location": "Lily",
  "event": "obtain repair tool"
}
```

Needle and thread also have Lily as holder. The repair event links its actor,
instruments and coat while leaving unsupported physical locations null. In the
transfer story, the first needle mention has location Ava and event give object;
the second has location Ben and event return object. Both refer to the same
entity. Later locations are not backfilled onto earlier mentions.

All 47 tests passed across the annotation, predictor and grammarworlds baseline
suites. New checks cover the requested scissors fields, changing holders,
unknown/corrupted holder names, participant-label drift and event trigger checks.
Historical v1 request/response evidence remains untouched in earlier directories.

This verifies two short development cases and shared prefix-cache reuse, not
general annotation accuracy. Labels are full-story offline supervision.

## Local positional overlay

The saved annotation arrays and derived metadata now also contain deterministic
zero-based token, sentence and within-sentence positions. All tokens, including
spaces and punctuation, count. Scissors has position
`{"token":10,"sentence":0,"in_sentence":10}`. The two needle mentions in the
transfer story have positions `{"token":8,"sentence":0,"in_sentence":8}` and
`{"token":17,"sentence":1,"in_sentence":6}`.

This overlay used the existing responses without a model call; both original
request and provider-response hashes were verified unchanged. All 53 tests pass,
including local position, sentence boundary, quotation, decimal/abbreviation,
prefix independence and annotation integration checks.
