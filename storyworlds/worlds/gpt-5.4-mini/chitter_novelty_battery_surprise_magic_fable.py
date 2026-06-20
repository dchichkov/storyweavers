#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chitter_novelty_battery_surprise_magic_fable.py
================================================================================

A small standalone story world for a fable-like woodland surprise about
novelty, battery-powered chittering, and a magic-looking turn.

Premise:
- A young woodland creature finds a novelty toy that makes a cheerful chitter.
- The toy runs on a battery, so it works without any flame or danger.
- A surprised friend mistakes the toy for magic, then learns the kinder truth.
- The ending proves the change: the creatures choose the safe, shared wonder.

This script follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    battery: bool = False
    novelty: bool = False
    magical: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_chitter(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["powered"] < THRESHOLD:
            continue
        sig = ("chitter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        out.append("__chitter__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen") and not world.facts.get("surprise_felt"):
        world.facts["surprise_felt"] = True
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["surprise"] += 1
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("chitter", _r_chitter), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Toy:
    id: str
    label: str
    sound: str
    novelty: bool = True
    battery: bool = True
    magical: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    creature1: str
    creature1_type: str
    creature2: str
    creature2_type: str
    elder: str
    elder_type: str
    toy: str
    setting: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class Catalog:
    pass


ANIMALS = {
    "mole": ("mole", "They lived under the old hill."),
    "sparrow": ("sparrow", "They lived in the hedges by the lane."),
    "hare": ("hare", "They lived near the meadow gate."),
    "mouse": ("mouse", "They lived beside the grain shed."),
}

ELDERS = {
    "owl": ("owl", "the wise owl"),
    "turtle": ("turtle", "the patient turtle"),
    "goat": ("goat", "the old goat"),
}

TOYS = {
    "novelty_bell": Toy("novelty_bell", "novelty bell", "chitter"),
    "battery_glowbug": Toy("battery_glowbug", "battery glowbug", "chitter"),
    "novelty_lantern": Toy("novelty_lantern", "novelty lantern", "hum"),
}

SETTINGS = {
    "hedge": "the hedge path by the berry bush",
    "burrow": "the little room under the hill",
    "barn": "the quiet corner of the barn",
    "glade": "the moonlit glade",
}

GIRLISH = ["Lily", "Mina", "Iris", "Ruby", "Tess"]
BOYISH = ["Pip", "Ari", "Finn", "Ned", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for toy in TOYS:
            combos.append((setting, toy, "fable"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world of novelty, battery, surprise, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--creature1")
    ap.add_argument("--creature2")
    ap.add_argument("--elder")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo = [c for c in valid_combos()
             if (args.setting is None or c[0] == args.setting)
             and (args.toy is None or c[1] == args.toy)]
    if not combo:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, _ = rng.choice(sorted(combo))
    c1 = args.creature1 or rng.choice(sorted(ANIMALS))
    c2 = args.creature2 or rng.choice([x for x in sorted(ANIMALS) if x != c1])
    elder = args.elder or rng.choice(sorted(ELDERS))
    return StoryParams(c1, ANIMALS[c1][0], c2, ANIMALS[c2][0], elder, ELDERS[elder][0], toy, setting)


def tell(params: StoryParams) -> World:
    w = World()
    a = w.add(Entity(id=params.creature1, kind="character", type=params.creature1_type, role="young"))
    b = w.add(Entity(id=params.creature2, kind="character", type=params.creature2_type, role="friend"))
    elder = w.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="elder"))
    toy = w.add(Entity(id="toy", kind="thing", type="toy", label=TOYS[params.toy].label,
                       novelty=True, battery=True, magical=TOYS[params.toy].magical))
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    w.say(
        f"In {SETTINGS[params.setting]}, {a.id} and {b.id} found a {toy.label} that looked "
        f"too bright to be plain. {ANIMALS[params.creature1][1]}"
    )
    w.say(
        f"When {a.id} pressed it, the little toy began to {TOYS[params.toy].sound} and glow. "
        f"{b.id} blinked. \"Is that magic?\" {b.id} asked."
    )
    w.para()
    elder.memes["calm"] += 1
    w.facts["surprise_seen"] = True
    toy.meters["powered"] += 1
    propagate(w)
    w.say(
        f"{elder.id} smiled and said, \"It only seems magic. It is a novelty toy with a battery, "
        f"so it can shine and chitter all by itself.\""
    )
    w.say(
        f"The two young ones watched again. The surprise stayed, but the fear left, and their "
        f"wonder grew kinder than before."
    )
    w.para()
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    elder.memes["pride"] += 1
    w.say(
        f"After that, they shared the toy instead of quarrelling over it. In the soft dark, "
        f"the tiny chittering light made their little world feel blessed rather than strange."
    )
    w.facts.update(creature1=a, creature2=b, elder=elder, toy=toy, setting=params.setting, toy_id=params.toy)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story for a young child that includes the words "chitter", "novelty", and "battery".',
        f"Tell a small woodland tale where {f['creature1'].id} and {f['creature2'].id} find a {f['toy'].label} and wonder if it is magic.",
        f"Write a surprise story with a gentle moral: something that seems magical turns out to be a battery-powered novelty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy = f["toy"]
    a = f["creature1"]
    b = f["creature2"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} find?",
            answer=f"They found a {toy.label}. It looked surprising, and it made a little chitter when it was turned on."
        ),
        QAItem(
            question=f"Why did they think it might be magic?",
            answer=f"It shone and made a lively sound without any fire or wind. Because it worked from a battery, it seemed magical at first."
        ),
        QAItem(
            question=f"What did {elder.id} explain about the toy?",
            answer=f"{elder.id} explained that it was not real magic. It was a novelty toy with a battery, so the light and chitter had a simple, safe cause."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a battery?", "A battery stores power for toys and lights, so they can work without a fire."),
        QAItem("What does novelty mean?", "Novelty means something is new, unusual, or made mostly for fun."),
        QAItem("What is surprise?", "Surprise is the feeling you get when something happens that you did not expect."),
        QAItem("What is magic in a story?", "Magic is something wonderful that seems to break the usual rules."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("battery", e.battery), ("novelty", e.novelty), ("magical", e.magical)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
powered(T) :- toy(T), battery(T).
chitters(T) :- powered(T), novelty(T).
surprised(X) :- character(X), sees_magic(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.battery:
            lines.append(asp.fact("battery", tid))
        if toy.novelty:
            lines.append(asp.fact("novelty", tid))
    for name in ANIMALS:
        lines.append(asp.fact("character", name))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show powered/1.\n#show chitters/1."))
    return sorted(set(asp.atoms(model, "powered")))


def asp_verify() -> int:
    rc = 0
    import_error = None
    try:
        import asp  # noqa: F401
    except Exception as err:  # pragma: no cover
        import_error = err
    if import_error is not None:
        print(f"ASP unavailable: {import_error}")
        return 1
    c = set(asp_valid_combos())
    p = {(tid,) for tid, t in TOYS.items() if t.battery}
    if c == p:
        print(f"OK: ASP matches Python battery-power facts ({len(c)} toys).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("mole", "mole", "sparrow", "sparrow", "owl", "owl", "novelty_bell", "hedge"),
    StoryParams("hare", "hare", "mouse", "mouse", "turtle", "turtle", "battery_glowbug", "glade"),
    StoryParams("mouse", "mouse", "sparrow", "sparrow", "goat", "goat", "novelty_lantern", "barn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show powered/1.\n#show chitters/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("battery-powered toys:")
        for tid, toy in TOYS.items():
            if toy.battery:
                print(f"  {tid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.creature1} and {p.creature2}: {p.toy} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
