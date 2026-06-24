#!/usr/bin/env python3
"""
storyworlds/worlds/vendor_ail_sharing_bedtime_story.py
======================================================

A small bedtime-story world about a vendor and Ail sharing something kind
when the night feels long.

Seed tale:
---
A little vendor was closing a tiny stall when Ail came along looking chilly and
sleepy. The vendor only had one soft blanket and one warm cup left. Instead of
keeping everything for the end of the day, the vendor shared the blanket, the
cup, and a quiet place to rest. Ail felt better, the vendor felt glad, and the
night became gentle.

World idea:
---
This script models a tiny sharing story with:
- one vendor
- one friend named Ail
- one shareable comforting item
- physical meters like warmth, sleepiness, and fullness
- emotional memes like kindness, trust, and ease

The story is generated from world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
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
    shared_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("warmth", "sleepiness", "fullness", "tiredness", "comfort"):
            self.meters.setdefault(k, 0.0)
        for k in ("kindness", "trust", "peace", "relief", "worry"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"vendor", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little night market"
    cozy: bool = True


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    gives_warmth: float
    gives_comfort: float
    shareable: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(setting: Setting, item: Thing) -> World:
    world = World(setting)
    vendor = world.add(Entity(
        id="Vendor",
        kind="character",
        type="vendor",
        label="vendor",
        phrase="a kind little vendor",
        meters={"warmth": 1.0, "sleepiness": 0.2, "fullness": 0.2},
        memes={"kindness": 1.0, "trust": 0.2, "peace": 0.5},
    ))
    ail = world.add(Entity(
        id="Ail",
        kind="character",
        type="child",
        label="Ail",
        phrase="Ail",
        meters={"warmth": 0.2, "sleepiness": 1.0, "comfort": 0.2},
        memes={"worry": 0.8, "trust": 0.1, "relief": 0.0},
    ))
    gift = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=vendor.id,
        meters={"warmth": item.gives_warmth, "comfort": item.gives_comfort},
    ))
    world.facts.update(vendor=vendor, ail=ail, item=gift, item_def=item)
    return world


def _share_item(world: World) -> None:
    vendor = world.get("Vendor")
    ail = world.get("Ail")
    item = world.get(world.facts["item"].id)
    sig = ("share", item.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    ail.meters["warmth"] += item.meters["warmth"]
    ail.meters["comfort"] += item.meters["comfort"]
    ail.memes["relief"] += 1.0
    ail.memes["trust"] += 0.6
    vendor.memes["kindness"] += 0.7
    vendor.memes["peace"] += 0.5
    vendor.meters["fullness"] += 0.1


def tell(setting: Setting, item: Thing) -> World:
    world = build_world(setting, item)
    vendor = world.get("Vendor")
    ail = world.get("Ail")
    thing = world.get(item.id)

    world.say(
        f"At {setting.place}, a kind little vendor was finishing the last small jobs of the evening."
    )
    world.say(
        f"Near the quiet stall, Ail came in with cold hands and sleepy eyes, looking like {ail.pronoun('subject')} might need a soft place to rest."
    )
    world.para()
    if ail.meters["warmth"] < THRESHOLD:
        world.say(
            f"The vendor saw that {ail.pronoun('possessive')} {thing.label} could help, because it was warm and gentle."
        )
    world.say(
        f"Instead of keeping {thing.it()} all to {vendor.pronoun('possessive')}self, the vendor shared {thing.it()} with Ail."
    )
    _share_item(world)
    world.say(
        f"Ail wrapped up in the {thing.label} and felt the chill fade from {ail.pronoun('possessive')} fingers."
    )
    world.say(
        f"The vendor smiled, and the little stall grew quiet and cozy as the two of them rested under the night sky."
    )

    world.facts.update(shared=True)
    return world


SETTINGS = {
    "market": Setting(place="the little night market", cozy=True),
    "stall": Setting(place="the warm corner stall", cozy=True),
    "road": Setting(place="the lantern-lit road", cozy=False),
}

ITEMS = {
    "blanket": Thing(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        gives_warmth=1.0,
        gives_comfort=0.8,
    ),
    "mug": Thing(
        id="mug",
        label="warm mug",
        phrase="a warm mug of milk",
        gives_warmth=0.7,
        gives_comfort=0.6,
    ),
    "bun": Thing(
        id="bun",
        label="bun",
        phrase="a warm bun",
        gives_warmth=0.3,
        gives_comfort=0.9,
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="market", item="blanket"),
    StoryParams(setting="stall", item="mug"),
    StoryParams(setting="market", item="bun"),
]


ASP_RULES = r"""
shared(I) :- item(I), shareable(I), need_warmth(ail), gives_warmth(I, W), W > 0.
calm(ail) :- shared(I), gives_comfort(I, C), C > 0.
kind(vendor) :- shared(I).
valid_story(S, I) :- setting(S), item(I), shared(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("shareable", iid))
        lines.append(asp.fact("gives_warmth", iid, int(item.gives_warmth * 10)))
        lines.append(asp.fact("gives_comfort", iid, int(item.gives_comfort * 10)))
    lines.append(asp.fact("need_warmth", "ail"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a vendor and Ail sharing kindly.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, i) for s in SETTINGS for i in ITEMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, item = rng.choice(sorted(combos))
    return StoryParams(setting=setting, item=item)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story about a vendor and Ail sharing a {f['item'].label} at {world.setting.place}.",
        f"Tell a gentle story where the vendor notices Ail is chilly and decides to share a {f['item'].label}.",
        f"Create a soft nighttime tale about kindness, rest, and sharing at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    return [
        QAItem(
            question="Who shared the comforting thing with Ail?",
            answer=f"The vendor shared the {item.label} with Ail.",
        ),
        QAItem(
            question="Why did Ail feel better by the end?",
            answer=f"Ail felt better because the {item.label} was warm and comforting, and the vendor shared it kindly.",
        ),
        QAItem(
            question="Where did the story take place?",
            answer=f"The story took place at {world.setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else so both people can enjoy it or use it.",
        ),
        QAItem(
            question="Why can a blanket help at bedtime?",
            answer="A blanket can help because it keeps a person warm and makes a resting place feel cozy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
