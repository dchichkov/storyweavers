# Online teacher prototype: preparation and offline control

The implementation is ready for a live teacher run, but no paid model calls
were made. On 2026-11-13 the API returned `404 model_not_found` for the requested
`gpt-6.1-luna`; `gpt-6-luna` was available. Model substitution is awaiting the
user's choice. The read-only availability probes did not generate tokens.

The first request was prepared with the requested model ID, Flex service tier,
an explicit cache breakpoint after stable instructions and vocabulary, and
changing per-example evidence after the breakpoint. This is configuration
verification, not evidence of actual cache hits.

A 24-position integration control ran through the first presentation training
story with a no-op teacher. It tested the real causal prefixes, backward steps,
replay gates, checkpoint writes, and independent weight-only control. It made
zero LLM calls and proposed no learned grammar edits. Its pre-update mean NLL
was 4.3164 nats and accuracy 20.8%; these are baseline observations, not results
of LLM generalization. All 24 selected updates were weight-only.

Artifacts:

- [Protocol and implementation](../../ONLINE.md)
- [Model availability](model_availability.json)
- [Prepared request](prepared_request.json)
- [Immutable input manifest](manifest.json)
- [Offline control report](offline_control/report.json)
- Offline per-position evidence, decisions, and checkpoints under `offline_control/`.

The prior sentence and presentation datasets/checkpoints were not modified.
API spend: **$0**. Live quality, cached-token counts, and API cost measurements
remain pending an available model choice.
