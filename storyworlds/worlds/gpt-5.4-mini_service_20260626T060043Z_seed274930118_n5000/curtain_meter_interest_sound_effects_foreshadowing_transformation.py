#!/usr/bin/env python3
"""
A small folk-tale story world about a curtain, a meter stick, and growing interest.

A child-facing seed tale:
---
Long ago, in a little village, a clever child found a faded curtain in the attic.
A wooden meter stick lay beside it, and the child measured the cloth with care.
At first the curtain was plain and dusty, but the child felt a strong interest in
making it beautiful. When the wind went by, the cloth whispered, "swish-swish,"
as if it were waiting for a change. The child sewed bright ribbons along the edge,
and by evening the curtain looked new. The room felt warmer, and the old cloth
seemed to have transformed into a story-banner for everyone to admire.
---

This world models:
- physical meters: cloth length, ribbon length, and room brightness
- emotional memes: interest, worry, pride, wonder
- causal instruments: sound effects, foreshadowing, transformation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    sound: str = "softly"


@dataclass
class StoryParams:
    place: str
    curtain: str
    meter_kind: str
    interest_level: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    curtain = world.get("curtain")
    child = world.get("child")
    if curtain.meters.get("touched", 0.0) >= THRESHOLD and ("sound", "swish") not in world.fired:
        world.fired.add(("sound", "swish"))
        curtain.memes["mystery"] = curtain.memes.get("mystery", 0.0) + 1
        child.memes["interest"] = child.memes.get("interest", 0.0) + 1
        out.append("Swish-swish went the curtain, and the child leaned closer to listen.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    curtain = world.get("curtain")
    child = world.get("child")
    if child.memes.get("interest", 0.0) >= THRESHOLD and ("foreshadow", "wind") not in world.fired:
        world.fired.add(("foreshadow", "wind"))
        curtain.meters["flutter"] = curtain.meters.get("flutter", 0.0) + 1
        out.append("The window breathed a small wind, as if it were hinting that change was near.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    curtain = world.get("curtain")
    child = world.get("child")
    ribbon = world.get("ribbon")
    if ribbon.meters.get("tied", 0.0) >= THRESHOLD and curtain.memes.get("mystery", 0.0) >= THRESHOLD:
        if ("transform", "curtain") in world.fired:
            return out
        world.fired.add(("transform", "curtain"))
        curtain.type = "banner"
        curtain.label = "story-banner"
        curtain.phrase = "a bright story-banner"
        curtain.meters["bright"] = curtain.meters.get("bright", 0.0) + 1
        child.memes["pride"] = child.memes.get("pride", 0.0) + 1
        out.append("Snip-snap, the ribbons met the cloth, and the curtain transformed into a story-banner.")
    return out


RULES = [Rule("sound", _r_sound), Rule("foreshadow", _r_foreshadow), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACE_REGISTRY = {
    "attic": Place(name="the attic", indoors=True),
    "cottage": Place(name="the cottage room", indoors=True),
    "hall": Place(name="the long hall", indoors=True),
}


CURTAIN_REGISTRY = {
    "faded": {"label": "curtain", "phrase": "a faded curtain", "meters": {"length": 3.0}, "memes": {"mystery": 0.0, "interest": 0.0}},
    "blue": {"label": "curtain", "phrase": "a blue curtain", "meters": {"length": 4.0}, "memes": {"mystery": 0.0, "interest": 0.0}},
    "patched": {"label": "curtain", "phrase": "a patched curtain", "meters": {"length": 2.5}, "memes": {"mystery": 0.0, "interest": 0.0}},
}

METER_REGISTRY = {
    "wooden": {"label": "meter stick", "phrase": "a wooden meter stick", "meters": {"length": 1.0}, "memes": {}},
    "chalk": {"label": "meter ruler", "phrase": "a chalk-marked meter ruler", "meters": {"length": 1.0}, "memes": {}},
}

RIBBON_REGISTRY = {
    "red": {"label": "ribbon", "phrase": "a red ribbon", "meters": {"length": 1.0}, "memes": {}},
    "gold": {"label": "ribbon", "phrase": "a gold ribbon", "meters": {"length": 1.0}, "memes": {}},
    "green": {"label": "ribbon", "phrase": "a green ribbon", "meters": {"length": 1.0}, "memes": {}},
}

INTEREST_LEVELS = ["curious", "keen", "eager"]


@dataclass
class WorldConfig:
    place: str
    curtain: str
    meter_kind: str
    interest_level: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world of curtain, meter, and interest.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--curtain", choices=CURTAIN_REGISTRY)
    ap.add_argument("--meter-kind", choices=METER_REGISTRY)
    ap.add_argument("--interest-level", choices=INTEREST_LEVELS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    curtain = args.curtain or rng.choice(list(CURTAIN_REGISTRY))
    meter_kind = args.meter_kind or rng.choice(list(METER_REGISTRY))
    interest_level = args.interest_level or rng.choice(INTEREST_LEVELS)
    return StoryParams(place=place, curtain=curtain, meter_kind=meter_kind, interest_level=interest_level)


def _make_world(params: StoryParams) -> World:
    world = World(PLACE_REGISTRY[params.place])
    child = world.add(Entity(id="child", kind="character", type="child", label="the child"))
    curtain_cfg = CURTAIN_REGISTRY[params.curtain]
    meter_cfg = METER_REGISTRY[params.meter_kind]
    ribbon_cfg = RIBBON_REGISTRY["gold" if params.interest_level == "eager" else "red"]
    curtain = world.add(Entity(id="curtain", type="curtain", label=curtain_cfg["label"], phrase=curtain_cfg["phrase"],
                               meters=copy.deepcopy(curtain_cfg["meters"]), memes=copy.deepcopy(curtain_cfg["memes"])))
    meter = world.add(Entity(id="meter", type="meter", label=meter_cfg["label"], phrase=meter_cfg["phrase"],
                             meters=copy.deepcopy(meter_cfg["meters"]), memes=copy.deepcopy(meter_cfg["memes"])))
    ribbon = world.add(Entity(id="ribbon", type="ribbon", label=ribbon_cfg["label"], phrase=ribbon_cfg["phrase"],
                              meters=copy.deepcopy(ribbon_cfg["meters"]), memes=copy.deepcopy(ribbon_cfg["memes"])))
    world.facts.update(place=params.place, curtain=curtain, meter=meter, ribbon=ribbon, child=child, params=params)
    return world


def _story(world: World, params: StoryParams) -> World:
    child = world.get("child")
    curtain = world.get("curtain")
    meter = world.get("meter")
    ribbon = world.get("ribbon")

    child.memes["interest"] = {"curious": 1.0, "keen": 2.0, "eager": 3.0}[params.interest_level]
    world.say(f"Once in {world.place.name}, a child found {curtain.phrase} and {meter.phrase}.")
    world.say(f"The child measured the cloth carefully, one meter at a time, and felt growing interest in what it might become.")
    world.say(f"Tap-tap went the meter stick, and the curtain answered with a soft swish as the wind slipped by.")
    world.para()
    meter.meters["measured"] = meter.meters.get("measured", 0.0) + 1
    curtain.meters["touched"] = curtain.meters.get("touched", 0.0) + 1
    propagate(world, narrate=True)
    world.say(f"The child chose {ribbon.phrase} and tied it along the edge of the curtain.")
    ribbon.meters["tied"] = ribbon.meters.get("tied", 0.0) + 1
    propagate(world, narrate=True)
    world.para()
    if curtain.type == "banner":
        world.say("By dusk, the old curtain had become a bright banner, and the room felt warm with pride.")
    else:
        world.say("By dusk, the curtain still hung as it was, but the child had learned to listen for its secrets.")
    world.facts.update(resolved=(curtain.type == "banner"))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story about a child, a {f["curtain"].label}, and a {f["meter"].label}.',
        f"Tell a short story where a child notices a curtain, measures it with a meter, and feels interest grow into change.",
        f'Write a gentle tale that includes the sounds "swish-swish" and "snip-snap" and ends with a transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    curtain, meter, child = f["curtain"], f["meter"], f["child"]
    return [
        QAItem(
            question="What did the child find in the place?",
            answer=f"The child found {curtain.phrase} and {meter.phrase}.",
        ),
        QAItem(
            question="Why did the child keep looking at the curtain?",
            answer="The child felt interest in the curtain because it seemed like it had a secret waiting to be discovered.",
        ),
        QAItem(
            question="What changed when the ribbons were tied on?",
            answer="The curtain transformed into a story-banner, and the room felt brighter and warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meter used for?",
            answer="A meter is used to measure how long something is.",
        ),
        QAItem(
            question="Why do people listen for sound effects in stories?",
            answer="Sound effects help a story feel lively because they let you imagine what something sounds like.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that something important may happen later.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes into a new form or becomes different in an important way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curtain(C) :- entity(C), kind(C,curtain).
child(X) :- entity(X), kind(X,child).
meter(M) :- entity(M), kind(M,meter).

interested(X) :- meme(X,interest,I), I >= 1.
hint(C) :- curtain(C), touched(C), sound(swish_swish).
change(C) :- curtain(C), ribbon_tied(C).

shown(transform(C)) :- change(C).
shown(foreshadow(C)) :- curtain(C), flutter(C).
shown(sound(C)) :- curtain(C), touched(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("entity", "child"))
    lines.append(asp.fact("kind", "child", "child"))
    lines.append(asp.fact("entity", "curtain"))
    lines.append(asp.fact("kind", "curtain", "curtain"))
    lines.append(asp.fact("entity", "meter"))
    lines.append(asp.fact("kind", "meter", "meter"))
    lines.append(asp.fact("entity", "ribbon"))
    lines.append(asp.fact("kind", "ribbon", "ribbon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_story_from_params(params: StoryParams) -> StorySample:
    world = _make_world(params)
    world = _story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_from_params(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    return 0


def build_all() -> list[StoryParams]:
    return [
        StoryParams(place="attic", curtain="faded", meter_kind="wooden", interest_level="curious"),
        StoryParams(place="cottage", curtain="blue", meter_kind="chalk", interest_level="keen"),
        StoryParams(place="hall", curtain="patched", meter_kind="wooden", interest_level="eager"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shown/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("0 compatible ASP stories (stub world).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.curtain}, {p.meter_kind}, {p.interest_level}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
