"""Token-cost estimates, not invoice reconciliation, for canonical trials."""

from __future__ import annotations

PRICING_DATE = "2026-09-07"
PRICING_URL = "https://developers.openai.com/api/docs/pricing"
# USD / million tokens: ordinary input, cache reads, cache writes, output.
FLEX_RATES = {
    "gpt-5.6-luna": (0.10, 0.01, 0.125, 0.60),
    "gpt-5.6-terra": (1.00, 0.10, 1.25, 6.00),
}


def token_cost(model: str, usage: dict, tier: str = "flex") -> dict:
    name = next((name for name in FLEX_RATES if model == name or model.startswith(name + "-")), None)
    if name is None or tier not in ("flex", "default", "standard"):
        return dict(known=False, reason="unpriced model or service tier")
    if "input_tokens" not in usage or "output_tokens" not in usage:
        return dict(known=False, reason="missing usage")
    inputs, outputs = usage["input_tokens"], usage["output_tokens"]
    details = usage.get("input_tokens_details") or {}
    cached = details.get("cached_tokens", 0)
    writes = details.get("cache_write_tokens", 0)
    if any(type(n) is not int or n < 0 for n in (inputs, outputs, cached, writes)) or cached + writes > inputs:
        return dict(known=False, reason="invalid usage breakdown")
    if inputs > 128000:
        return dict(known=False, reason="long-context pricing not implemented")
    rates = FLEX_RATES[name]
    factor = 1 if tier == "flex" else 2
    base = factor * ((inputs - cached - writes) * rates[0] + cached * rates[1]
                     + writes * rates[2] + outputs * rates[3]) / 1e6
    # Older response schemas omit cache writes. Bound the unreported premium.
    premium = (factor * (inputs - cached) * (rates[2] - rates[0]) / 1e6
               if "cache_write_tokens" not in details else 0)
    return dict(known=True, input_tokens=inputs, cached_input_tokens=cached,
                cache_write_tokens=writes if "cache_write_tokens" in details else None,
                output_tokens=outputs, usd_low=base, usd_high=base + premium)


def summarize(rows: list[dict]) -> dict:
    costs = []
    for row in rows:
        response = row.get("response") or {}
        body = response.get("body") or response
        # Use the actual returned model/tier, never assume the requested tier was served.
        costs.append(token_cost(body.get("model") or "", body.get("usage") or {},
                                body.get("service_tier") or "unknown"))
    known = [cost for cost in costs if cost["known"]]
    return dict(pricing_date=PRICING_DATE, pricing_url=PRICING_URL, requests=len(rows),
                priced_requests=len(known), unpriced_requests=len(rows) - len(known),
                input_tokens=sum(cost["input_tokens"] for cost in known),
                output_tokens=sum(cost["output_tokens"] for cost in known),
                usd_low=sum(cost["usd_low"] for cost in known),
                usd_high=sum(cost["usd_high"] for cost in known),
                note="Returned-usage estimate only; unknown outcomes/retries may add cost. Missing cache writes are bounded.")


def estimate(model: str, inputs: int, outputs: int) -> dict:
    return token_cost(model, dict(input_tokens=inputs, output_tokens=outputs))
