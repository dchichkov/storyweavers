#!/usr/bin/env python3
"""
croissant_dialogue_slice_of_life.py
===================================

A small slice-of-life storyworld about a croissant, a gentle conversation, and
a nearby choice that changes the mood of a quiet morning.

The world model tracks:
- physical meters: warmth, crumbs, fullness, tidiness
- emotional memes: hunger, delight, worry, closeness

The story is built from a simple premise:
someone wants the croissant now, someone else has a practical concern, and
they find a kind compromise through dialogue.
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

# Physical and emotional thresholds for narration.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"warmth": 0.0, "crumbs": 0.0, "fullness": 0.0, "tidiness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hunger": 0.0, "worry": 0.0, "delight": 0.0, "closeness": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    table: bool = True
    quiet: bool = True


@dataclass
class Treat:
    label: str
    phrase: str
    warmth: float
    crumbs: float
    fills: float
    fragile: bool = True
    needs_plate: bool = True


@dataclass
class StoryParams:
    setting: str
    treat: str
    hero_name: str
    hero_type: str
    other_name: str
    other_type: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "cafe": Setting(place="a small cafe"),
    "balcony": Setting(place="the balcony"),
    "table": Setting(place="the breakfast table"),
}

TREATS = {
    "croissant": Treat(
        label="croissant",
        phrase="a warm croissant from the bakery",
        warmth=1.0,
        crumbs=1.0,
        fills=1.0,
        fragile=True,
        needs_plate=True,
    ),
    "pain_au_chocolat": Treat(
        label="pain au chocolat",
        phrase="a chocolate croissant",
        warmth=1.0,
        crumbs=0.8,
        fills=1.0,
        fragile=True,
        needs_plate=True,
    ),
    "bun": Treat(
        label="bun",
        phrase="a soft butter bun",
        warmth=0.7,
        crumbs=0.4,
        fills=0.8,
        fragile=False,
        needs_plate=True,
    ),
}

GENDER_NAMES = {
    "girl": ["Mia", "Nora", "Lena", "Ivy", "Zoe"],
    "boy": ["Theo", "Ben", "Arlo", "Finn", "Leo"],
}

OTHER_TYPES = ["mother", "father", "friend", "sibling"]


def family_label(t: str) -> str:
    return {"mother": "mom", "father": "dad", "friend": "friend", "sibling": "sibling"}.get(t, t)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life croissant dialogue storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATDS := list(TREATS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--other-name")
    ap.add_argument("--other-type", choices=OTHER_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(TREATS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GENDER_NAMES[hero_type])
    other_type = args.other_type or rng.choice(OTHER_TYPES)
    other_name = args.other_name or rng.choice(["Ari", "Sam", "June", "Pip", "Noa"])
    return StoryParams(setting, treat, hero_name, hero_type, other_name, other_type)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.needs_plate:
            lines.append(asp.fact("needs_plate", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,T) :- setting(S), treat(T), needs_plate(T), fragile(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, t) for s in SETTINGS for t in TREATS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")


def compose_story(world: World) -> None:
    hero = world.get("hero")
    other = world.get("other")
    treat = world.get("treat")

    world.say(f"{hero.id} was at {world.setting.place} when the morning felt soft and still.")
    world.say(f"On the table sat {treat.phrase}, and {hero.id} stared at it with bright eyes.")
    world.say(f'"Can I have the {treat.label}?" {hero.id} asked.')
    world.say(f'"Maybe," said {other.id}, "but it will make crumbs if we rush."')
    hero.memes["hunger"] += 1
    hero.memes["delight"] += 0.5
    other.memes["worry"] += 1
    treat.meters["crumbs"] += 0.5

    world.para()
    world.say(f'"I know," {hero.id} said, "but it smells so warm."')
    world.say(f'"It does," {other.id} said. "Let’s make it nice, not messy."')
    hero.memes["worry"] += 0.2
    other.memes["closeness"] += 0.5

    world.para()
    world.say(f"{hero.id} found a plate and a napkin.")
    treat.meters["tidiness"] += 1
    world.say(f'"What if we split it?" {hero.id} asked. "You can have the first half."')
    world.say(f'{other.id} smiled. "That works. We can eat it slowly together."')
    hero.memes["delight"] += 1
    hero.memes["closeness"] += 1
    other.memes["delight"] += 1
    other.memes["worry"] = 0
    treat.meters["crumbs"] = 0.0
    treat.meters["fullness"] += 1.0
    world.facts.update(hero=hero, other=other, treat=treat)


def story_text(world: World) -> str:
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    o = world.facts["other"]
    t = world.facts["treat"]
    return [
        QAItem(
            question=f"What did {h.id} want at first?",
            answer=f"{h.id} wanted the {t.label} that was waiting on the table.",
        ),
        QAItem(
            question=f"Why did {o.id} hesitate?",
            answer=f"{o.id} worried that the {t.label} would make crumbs if they rushed.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They put the {t.label} on a plate, used a napkin, and split it so they could eat it slowly together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a croissant?",
            answer="A croissant is a buttery pastry with a flaky shape, often eaten warm for breakfast.",
        ),
        QAItem(
            question="Why do people use a napkin with pastries?",
            answer="People use a napkin to catch crumbs and keep the table and hands tidier.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle slice-of-life story with dialogue about a croissant at breakfast.",
        f"Tell a short story where someone asks for a croissant, another person worries about crumbs, and they agree on a calm solution at {world.setting.place}.",
        "Write a cozy morning story that ends with two people sharing a croissant kindly.",
    ]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    treat_cfg = TREATDS = TREATDS if False else None  # no-op to satisfy linters? not used
    treat_cfg = TREATS[params.treat]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    other = world.add(Entity(id=params.other_name, kind="character", type=params.other_type, label=params.other_name))
    treat = world.add(Entity(id="treat", kind="thing", type=params.treat, label=treat_cfg.label, phrase=treat_cfg.phrase))
    compose_story(world)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(setting="kitchen", treat="croissant", hero_name="Mia", hero_type="girl", other_name="Mom", other_type="mother"),
    StoryParams(setting="cafe", treat="pain_au_chocolat", hero_name="Theo", hero_type="boy", other_name="Ari", other_type="friend"),
    StoryParams(setting="balcony", treat="bun", hero_name="Nora", hero_type="girl", other_name="Dad", other_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid (setting, treat) combos:")
        for s, t in combos:
            print(f"  {s}  {t}")
        return

    if args.treat and args.treat not in TREATS:
        raise StoryError("Unknown treat.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")

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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            reasonableness_gate(params)
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
            header = f"### {p.hero_name}: {p.treat} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
