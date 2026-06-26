#!/usr/bin/env python3
"""
storyworlds/worlds/curlicue_coyote_sound_effects_bad_ending_nursery.py
======================================================================

A tiny nursery-rhyme storyworld with a curlicue, a coyote, sound effects,
and a bad ending.

Seed tale shape:
- A small curlicue thing is loved and carried on a windy path.
- A coyote appears, drawn in by the sound effects of play.
- The wind and the chasing make the curlicue slip away.
- The ending image is sad and concrete: the coyote is left alone, and the
  curlicue is lost beyond reach.

This script keeps the world small on purpose. It still models state:
- physical meters: wind, wobble, lostness, distance
- emotional memes: delight, worry, longing, regret

The prose is deliberately nursery-rhyme-like, with repeating sounds and
simple beats, but the story ends badly.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wind", "wobble", "distance", "lostness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["delight", "worry", "longing", "regret", "alarm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "coyote":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the meadow"
    feature: str = "a curlicue gate"


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def story_sound(action: str) -> str:
    return {
        "run": "tap-tap",
        "chase": "yip-yip",
        "wind": "whoosh",
        "twist": "swish-swish",
        "snap": "snap!",
        "fall": "thump",
    }.get(action, "la-la")


def reasonableness_gate(place: str, item: str) -> bool:
    return place in SETTINGS and item in ITEMS


def expected_loss(world: World, item: Entity, coyote: Entity) -> bool:
    return item.meters["wind"] >= THRESHOLD and coyote.memes["longing"] >= THRESHOLD


def wind_up(world: World, item: Entity) -> None:
    item.meters["wind"] += 1
    item.meters["wobble"] += 1
    world.say(f"The wind went {story_sound('wind')} over the meadow, and the {item.noun()} began to wobble.")


def coyote_listens(world: World, coyote: Entity, item: Entity) -> None:
    coyote.memes["delight"] += 1
    coyote.memes["longing"] += 1
    world.say(
        f'A coyote came by and heard the little sound, "{story_sound("run")}." '
        f'{coyote.pronoun("subject").capitalize()} liked the tune at once and wanted the {item.noun()}.'
    )


def chase(world: World, coyote: Entity, item: Entity) -> None:
    coyote.meters["distance"] += 1
    item.meters["wobble"] += 1
    world.say(
        f'{coyote.pronoun("subject").capitalize()} ran with a "{story_sound("chase")}," '
        f"and the {item.noun()} swayed and swayed."
    )


def bad_turn(world: World, coyote: Entity, item: Entity) -> None:
    if expected_loss(world, item, coyote):
        item.meters["distance"] += 2
        item.meters["lostness"] += 1
        item.lost = True
        coyote.memes["worry"] += 1
        coyote.memes["regret"] += 1
        world.say(
            f'Then came a sharp "{story_sound("snap")}" from the string, and the {item.noun()} slipped away.'
        )


def ending(world: World, coyote: Entity, item: Entity) -> None:
    if item.lost:
        world.say(
            f'The {item.noun()} floated off and out of sight. The coyote stood still under the gray sky, '
            f"and the meadow went quiet after the last soft {story_sound('fall')}."
        )
    else:
        world.say(f"The {item.noun()} stayed near, but the night felt too quiet anyway.")


def tell(setting: Setting, item_cfg: dict, name: str = "Milo") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    coyote = world.add(Entity(id="coyote", kind="character", type="coyote", label="a coyote"))
    item = world.add(
        Entity(
            id="curlicue",
            kind="thing",
            type=item_cfg["type"],
            label=item_cfg["label"],
            phrase=item_cfg["phrase"],
            owner=child.id,
        )
    )

    child.memes["delight"] += 1
    world.say(
        f"{child.id} had a {item.noun()}, all curly and bright, like a little curlicue in the grass."
    )
    world.say(
        f"{child.id} loved it and held it close while the meadow sang with {story_sound('twist')} and {story_sound('wind')}."
    )

    world.para()
    wind_up(world, item)
    coyote_listens(world, coyote, item)
    chase(world, coyote, item)
    bad_turn(world, coyote, item)

    world.para()
    ending(world, coyote, item)

    world.facts.update(child=child, coyote=coyote, item=item, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", feature="a curlicue of grass"),
    "hill": Setting(place="the hill", feature="a curlicue path"),
    "lane": Setting(place="the lane", feature="a curlicue fence"),
}

ITEMS = {
    "ribbon": {
        "type": "ribbon",
        "label": "curlicue ribbon",
        "phrase": "a shiny curlicue ribbon",
    },
    "kite": {
        "type": "kite",
        "label": "curlicue kite",
        "phrase": "a bright curlicue kite",
    },
    "shell": {
        "type": "shell",
        "label": "curlicue shell",
        "phrase": "a little curlicue shell",
    },
}

CURATED = [
    StoryParams(place="meadow", item="ribbon", name="Mia"),
    StoryParams(place="hill", item="kite", name="Ned"),
    StoryParams(place="lane", item="shell", name="Lily"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, i) for p in SETTINGS for i in ITEMS]


def explain_rejection(place: str, item: str) -> str:
    return f"(No story: I do not know a tale for place={place!r} and item={item!r}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with curlicue, coyote, and a bad ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--name")
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
    place = args.place or rng.choice(sorted(SETTINGS))
    item = args.item or rng.choice(sorted(ITEMS))
    if not reasonableness_gate(place, item):
        raise StoryError(explain_rejection(place, item))
    name = args.name or rng.choice(["Mia", "Ned", "Lily", "Owen", "June"])
    return StoryParams(place=place, item=item, name=name)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    coyote = f["coyote"]
    child = f["child"]
    return [
        QAItem(
            question=f"What did {child.id} have at the start of the story?",
            answer=f"{child.id} had a {item.label}, and it was described as curly and bright.",
        ),
        QAItem(
            question=f"Who heard the little sound and came by?",
            answer=f"A coyote heard the little sound and came by because {coyote.pronoun('subject')} wanted the {item.label}.",
        ),
        QAItem(
            question=f"What happened after the sharp snap?",
            answer=f"The {item.label} slipped away, and the coyote was left standing still in the quiet meadow.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does whoosh mean?",
            answer="Whoosh is a word for a fast rushing sound, like wind going past your ears.",
        ),
        QAItem(
            question="What is a coyote?",
            answer="A coyote is a wild animal that looks a little like a dog and can move very quickly.",
        ),
        QAItem(
            question="What is a curlicue?",
            answer="A curlicue is a curly twist or loop, like a spiral line or ribbon shape.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short nursery rhyme about a curlicue in {f['setting'].place} with sound effects and a sad ending.",
        f"Tell a gentle little tale where a coyote hears '{story_sound('run')}' and the curlicue gets lost.",
        f"Make a child-facing rhyme with whoosh, yip-yip, and snap, ending with the coyote alone.",
    ]


ASP_RULES = r"""
place(meadow).
place(hill).
place(lane).

item(ribbon).
item(kite).
item(shell).

valid(P,I) :- place(P), item(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.lost:
            bits.append("lost=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for p, i in combos:
            print(f"  {p:8} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
