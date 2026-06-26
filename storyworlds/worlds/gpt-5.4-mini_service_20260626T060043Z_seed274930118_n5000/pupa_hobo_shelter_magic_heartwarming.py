#!/usr/bin/env python3
"""
A small heartwarming story world about a pupa, a hobo, a shelter, and a little
bit of magic.

The world model is simple: a pupa is vulnerable, a hobo needs warmth and safety,
and a shelter can be improved by magical care. The story turns when the hobo
uses magic to help the pupa through a storm and makes the shelter gentler and
safer for both of them.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    sheltered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("warmth", 0.0)
        self.meters.setdefault("dry", 0.0)
        self.meters.setdefault("safety", 0.0)
        self.meters.setdefault("magic", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("care", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hobo", "man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Setting:
    place: str = "the old shelter"
    weather: str = "rain"
    has_fire: bool = False


@dataclass
class Magic:
    id: str
    label: str
    verb: str
    effect: str
    requires: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "shelter"
    magic: str = "warmth"
    name: str = "Milo"
    hobo_label: str = "kind hobo"
    pupa_label: str = "tiny pupa"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTING = Setting()
MAGICS = {
    "warmth": Magic(
        id="warmth",
        label="warmth magic",
        verb="kindle",
        effect="make the shelter warm",
        requires={"cold", "wet"},
    ),
    "glow": Magic(
        id="glow",
        label="glow magic",
        verb="glow",
        effect="soften the dark corners",
        requires={"dark"},
    ),
}

THRESHOLD = 1.0


def _is_needy(pupa: Entity) -> bool:
    return pupa.meters["warmth"] < THRESHOLD or pupa.meters["dry"] < THRESHOLD


def _apply_magic(world: World) -> list[str]:
    out: list[str] = []
    hobo = world.get("hobo")
    pupa = world.get("pupa")
    magic = MAGICS[world.facts["magic"]]
    if "magic_used" in world.fired:
        return out
    if not _is_needy(pupa):
        return out
    world.fired.add("magic_used")
    hobo.meters["magic"] += 1
    if "cold" in magic.requires:
        world.setting.has_fire = True
    pupa.meters["warmth"] += 1
    pupa.meters["dry"] += 1
    pupa.meters["safety"] += 1
    pupa.memes["hope"] += 1
    hobo.memes["care"] += 1
    hobo.memes["hope"] += 1
    out.append(
        f"{hobo.label.capitalize()} whispered a little magic and {magic.verb}d "
        f"a gentle light through the shelter."
    )
    out.append("The shelter felt warmer at once.")
    out.append(f"{hobo.label.capitalize()} tucked the tiny pupa into a dry, safe corner.")
    out.append("The pupa stopped trembling and settled down.")
    return out


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hobo = world.add(Entity(
        id="hobo",
        kind="character",
        type="hobo",
        label=params.hobo_label,
        phrase="a kindly hobo",
    ))
    pupa = world.add(Entity(
        id="pupa",
        kind="character",
        type="pupa",
        label=params.pupa_label,
        phrase="a tiny pupa",
        caretaker="hobo",
    ))
    shelter = world.add(Entity(
        id="shelter",
        kind="thing",
        type="shelter",
        label="shelter",
        phrase="an old shelter",
        owner="hobo",
        sheltered=True,
    ))

    world.facts["magic"] = params.magic
    magic = MAGICS[params.magic]

    world.say(
        f"At {world.setting.place}, {hobo.label} cared for a tiny pupa that had been "
        f"caught by the rain."
    )
    world.say(
        f"The pupa was small and fragile, and the shelter had cracks that let in the cold."
    )

    world.para()
    world.say(
        f"{hobo.label.capitalize()} saw the pupa shiver and knew it needed more than a dry leaf."
    )
    world.say(
        f"So {hobo.pronoun()} decided to use {magic.label} to {magic.effect}."
    )
    _apply_magic(world)

    world.para()
    world.say(
        f"After that, the shelter felt cozy, the pupa was safe, and {hobo.label} smiled "
        f"because kindness had changed the whole night."
    )
    world.say(
        f"The little pupa rested quietly while {hobo.label} kept watch beside the warm shelter."
    )

    world.facts.update(hobo=hobo, pupa=pupa, shelter=shelter, setting=world.setting, magic_def=magic)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about a hobo, a pupa, and a shelter, with a little magic.",
        "Tell a gentle story where a hobo helps a tiny pupa stay safe in a shelter.",
        "Write a cozy story in which magic makes an old shelter warm and kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hobo: Entity = world.facts["hobo"]
    pupa: Entity = world.facts["pupa"]
    return [
        QAItem(
            question="Who helped the tiny pupa in the shelter?",
            answer=f"{hobo.label.capitalize()} helped the tiny pupa and used magic to keep it safe.",
        ),
        QAItem(
            question="What changed in the shelter after the magic?",
            answer="The shelter became warmer and cozier, so the pupa could rest without shivering.",
        ),
        QAItem(
            question="How did the pupa feel at the end?",
            answer="The pupa felt safe and calm because the hobo made the shelter gentle and warm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shelter?",
            answer="A shelter is a place that gives protection from rain, wind, cold, or other rough weather.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special kind of helpful power that can do wonderful things that normal people cannot do by themselves.",
        ),
        QAItem(
            question="What is a pupa?",
            answer="A pupa is a stage in the life of some insects when they are changing into an adult insect.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  setting.has_fire={world.setting.has_fire}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show compatible/1.
#show helpful_story/0.

compatible(M) :- magic(M).
helpful_story :- compatible(M), magic(M), setting_place(shelter).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting_place", "shelter"))
    lines.append(asp.fact("setting_weather", "rain"))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    found = sorted(set(asp.atoms(model, "compatible")))
    expected = sorted([(m,) for m in MAGICS])
    if found != expected:
        print("MISMATCH between ASP and Python registry.")
        print("ASP:", found)
        print("PY :", expected)
        return 1
    print(f"OK: ASP matches Python registry ({len(found)} magic options).")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.magic not in MAGICS:
        raise StoryError("Unknown magic option.")
    magic = args.magic or rng.choice(list(MAGICS))
    name = args.name or rng.choice(["Milo", "Toby", "Rae", "Nina", "Iris"])
    hobo_label = args.hobo_label or rng.choice(["kind hobo", "gentle hobo", "soft-spoken hobo"])
    pupa_label = args.pupa_label or rng.choice(["tiny pupa", "small pupa", "little pupa"])
    return StoryParams(
        seed=args.seed,
        place="shelter",
        magic=magic,
        name=name,
        hobo_label=hobo_label,
        pupa_label=pupa_label,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: a pupa, a hobo, a shelter, and magic.")
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--name")
    ap.add_argument("--hobo-label")
    ap.add_argument("--pupa-label")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible magic options:")
        for (m,) in asp_list():
            print(f"  {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for magic in sorted(MAGICS):
            params = StoryParams(seed=base_seed, place="shelter", magic=magic)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
