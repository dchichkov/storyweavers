"""Luna/Flex teacher with a reusable prefix and a persistent $10 ceiling."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path

from .annotation import fingerprint
from .annotate import freeze, read
from .annotate_prefixes import dispatch


PROMPT = Path(__file__).resolve().parent / "prompts/online_teacher_v1.txt"
# USD / million tokens, GPT-6 Luna Flex, checked 2026-11-13.
# Cache writes replace the ordinary input rate; they are not an extra charge.
RATES = dict(input=.05, cached=.005, write=.0625, output=.25)


class BudgetExceeded(RuntimeError):
    pass


class TeacherResponseError(ValueError):
    """A paid response completed but cannot supply a usable proposal."""


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


class Budget:
    """Reserve before dispatch; unknown outcomes retain their entire reservation.

    The async lock covers concurrent requests in one process. Each run directory
    must have a single owner. Completed receipts survive restart; SDK retries
    are disabled, and the dispatcher only retries definite free Flex rejections.
    """

    def __init__(self, path, limit=10.):
        if type(limit) not in (int, float) or not 0 < limit <= 10:
            raise ValueError("experiment budget must be within (0, $10]")
        self.path, self.lock = Path(path), asyncio.Lock()
        self.data = read(self.path) if self.path.exists() else dict(limit_usd=limit, calls={})
        if self.data["limit_usd"] != limit:
            raise ValueError("cannot change a run's budget on resume")

    async def reserve(self, identifier, body):
        async with self.lock:
            digest = fingerprint(body)
            existing = self.data["calls"].get(identifier)
            if existing:
                if existing["request_sha256"] != digest:
                    raise ValueError("request changed under an existing budget reservation")
                return
            # UTF-8 byte count is a deliberately loose token bound. Extra
            # framing allowance and $1/$5 rates greatly exceed Luna Flex rates.
            size = len(json.dumps(body, ensure_ascii=False).encode()) + 4096
            if size > 120000 or body["max_output_tokens"] > 8192:
                raise ValueError("request exceeds this experiment's input/output budget bounds")
            reserve = (size + 5 * body["max_output_tokens"]) / 1_000_000
            used = sum(row["accounted_usd"] for row in self.data["calls"].values())
            if used + reserve > self.data["limit_usd"]:
                raise BudgetExceeded("budget exhausted before dispatch")
            self.data["calls"][identifier] = dict(request_sha256=digest, state="reserved",
                                                  reserved_usd=reserve, accounted_usd=reserve)
            atomic_json(self.path, self.data)

    async def settle(self, identifier, raw):
        async with self.lock:
            entry = self.data["calls"][identifier]
            usage = raw.get("usage") or {}
            details = usage.get("input_tokens_details") or {}
            incoming, outgoing = usage.get("input_tokens"), usage.get("output_tokens")
            cached, written = details.get("cached_tokens", 0), details.get("cache_write_tokens", 0)
            model = raw.get("model", "")
            if (model == "gpt-6-luna" or model.startswith("gpt-6-luna-")) and raw.get("service_tier") == "flex" and all(
                    type(n) is int and n >= 0 for n in (incoming, outgoing, cached, written)) and cached + written <= incoming:
                cost = ((incoming - cached - written) * RATES["input"] + cached * RATES["cached"] +
                        written * RATES["write"] + outgoing * RATES["output"]) / 1_000_000
                # Keep an upper estimate even if a provider omits cache-write
                # detail: price every noncached input token at the write rate.
                upper = ((incoming - cached) * RATES["write"] + cached * RATES["cached"] +
                         outgoing * RATES["output"]) / 1_000_000
                if upper > entry["reserved_usd"]:
                    entry.update(state="reservation_exceeded", accounted_usd=upper,
                                 estimated_cost_usd=cost, usage=usage, response_id=raw.get("id"))
                    atomic_json(self.path, self.data)
                    raise BudgetExceeded("reported usage exceeded conservative reservation; halt")
                entry.update(state="settled", accounted_usd=upper, estimated_cost_usd=cost)
            # Incomplete/invalid responses still cost money: account usage before
            # parsing. Unknown model/tier/usage retains the conservative amount.
            entry.update(response_id=raw.get("id"), model=model, service_tier=raw.get("service_tier"), usage=usage)
            atomic_json(self.path, self.data)


class Teacher:
    def __init__(self, client, root, model, vocabulary, *, budget=10., max_output_tokens=4096,
                 dispatch_fn=None):
        self.client, self.root, self.model = client, Path(root), model
        self.budget = Budget(self.root / "budget.json", budget)
        self.maximum = max_output_tokens
        self.dispatch = dispatch_fn or dispatch
        # Stable grammar language + examples + declared vocabulary go FIRST.
        self.prefix = PROMPT.read_text() + "\nDECLARED VOCABULARY (not outcome frequencies):\n" + json.dumps(vocabulary, sort_keys=True)
        self.key = "storyformers-online-v1:" + fingerprint([self.prefix, model])[:24]

    def request(self, packet):
        return dict(model=self.model, service_tier="flex", store=False,
                    reasoning={"effort": "medium"}, max_output_tokens=self.maximum,
                    text={"format": {"type": "json_object"}}, prompt_cache_key=self.key,
                    prompt_cache_options={"mode": "explicit", "ttl": "30m"},
                    input=[dict(role="developer", content=[dict(type="input_text", text=self.prefix,
                                prompt_cache_breakpoint={"mode": "explicit"})]),
                           dict(role="user", content=json.dumps(packet, ensure_ascii=False, separators=(",", ":")))])

    async def __call__(self, packet, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        identifier = str(directory.relative_to(self.root))
        body = self.request(packet)
        freeze(directory / "request.json", body)
        await self.budget.reserve(identifier, body)
        raw = await self.dispatch(directory, body, self.client, retries=2)
        await self.budget.settle(identifier, raw)
        atomic_json(directory / "receipt.json", deepcopy(self.budget.data["calls"][identifier]))
        served = raw.get("model", "")
        if (served != self.model and not served.startswith(self.model + "-")) or raw.get("service_tier") != "flex":
            raise RuntimeError("unexpected served model/tier; no fallback is authorized")
        if raw.get("status") != "completed":
            raise TeacherResponseError("teacher response incomplete; usage recorded, no patch accepted")
        parts = [part for item in raw.get("output", []) if item.get("type") == "message" for part in item.get("content", [])]
        if any(part.get("type") == "refusal" for part in parts):
            raise TeacherResponseError("teacher refused the revision")
        try:
            patch = json.loads("".join(part["text"] for part in parts if part.get("type") == "output_text"))
        except json.JSONDecodeError as exc:
            raise TeacherResponseError(str(exc)) from exc
        atomic_json(directory / "proposal.json", patch)
        return patch
