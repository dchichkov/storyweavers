#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gland_spike_dim_cove_moral_value_transformation.py
================================================================================================

A folk-tale storyworld about a small cove, a strange gland-shaped charm, a dim
spike curse, a moral choice, and a transformation that proves what changed.

Seed image:
---
A child in a misty cove finds a pearl-like gland that can brighten the harbor
lights, but a spike-dim thorn has tangled the tide rope. A greedy impulse says
to keep the charm, yet a wiser voice says the cove belongs to everyone. When
the child returns the charm, the spike-dim loses its hold and something shy and
small transforms into a brave guide for the night.

This script models the tale as a tiny stateful world:
- physical meters: brightness, wetness, thorniness, safety, tide
- emotional memes: greed, care, courage, trust, wonder
- a moral-value turn: taking vs. sharing
- a transformation: a dim creature or object becomes bright/clear when the
  right choice is made
- suspense: the cove's lantern may fail before the tide comes in

The prose is authored from world state, not a frozen template.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    state: str = ""

    def __post_init__(self) -> None:
        for k in ["brightness", "wetness", "thorniness", "safety", "tide", "weight"]:
            self.meters.setdefault(k, 0.0)
        for k in ["greed", "care", "courage", "trust", "wonder", "fear", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cove"
    salt_wind: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str = "hands"


@dataclass
class Curse:
    id: str
    label: str
    phrase: str
    blocks: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relic: str
    curse: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "cove": Setting(place="the cove", salt_wind=True, affords={"gather", "carry"}),
    "shore": Setting(place="the shore", salt_wind=True, affords={"gather", "carry"}),
    "harbor": Setting(place="the harbor", salt_wind=False, affords={"carry"}),
}

RELICS = {
    "gland": Relic(
        id="gland",
        label="gland pearl",
        phrase="a small pearl-like gland that glowed with harbor light",
        region="hands",
    ),
    "lantern": Relic(
        id="lantern",
        label="lantern charm",
        phrase="a little lantern charm with a brass hook",
        region="hands",
    ),
}

CURSES = {
    "spike-dim": Curse(
        id="spike-dim",
        label="spike-dim thorn",
        phrase="a thorny spike-dim that drank the light",
        blocks={"brightness"},
    ),
    "mist-hush": Curse(
        id="mist-hush",
        label="mist-hush knot",
        phrase="a knot of mist-hush that hid the way",
        blocks={"safety"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Sana", "Tove", "Nell"]
BOY_NAMES = ["Pip", "Rowan", "Milo", "Ansel", "Tobin"]
TRAITS = ["kind", "curious", "steady", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for relic in RELICS:
            for curse in CURSES:
                if place == "harbor" and curse == "mist-hush":
                    continue
                combos.append((place, relic, curse))
    return combos


def _pronoun_word(gender: str) -> dict[str, str]:
    return {"girl": "she", "boy": "he"}[gender]


def _poss_word(gender: str) -> dict[str, str]:
    return {"girl": "her", "boy": "his"}[gender]


def _subject_name(hero: Entity) -> str:
    return hero.id


def _do_suspense(world: World, hero: Entity, relic: Entity, curse: Entity) -> None:
    world.say(
        f"At {world.setting.place}, the tide started to climb, and the little light by the rocks grew dim."
    )
    if curse.id == "spike-dim":
        world.say(
            f"A {curse.label} had twisted around the rope, and its sharp shadow made the {relic.label} flicker."
        )
        hero.memes["fear"] += 1
        hero.memes["wonder"] += 1
        relic.meters["brightness"] -= 1


def _moral_turn(world: World, hero: Entity, helper: Entity, relic: Entity, curse: Entity) -> None:
    hero.memes["greed"] += 1
    world.say(
        f"{hero.id} held the {relic.label} tight and thought about keeping it."
    )
    world.say(
        f"Then {helper.id} said, 'The cove gives to many hands, not only to one.'"
    )
    hero.memes["trust"] += 1
    hero.memes["care"] += 1
    hero.memes["greed"] = 0.0
    world.say(
        f"{hero.id} looked at the dark water, then at the waiting boats, and chose to share."
    )


def _transform(world: World, hero: Entity, relic: Entity, curse: Entity) -> None:
    relic.meters["brightness"] += 2
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    if curse.id == "spike-dim":
        curse.state = "broken"
        world.say(
            f"When {hero.id} placed the {relic.label} on the rock, the spike-dim snapped like dry seaweed."
        )
        world.say(
            f"The same tide that had looked frightening a moment before turned the cove clear and bright."
        )
    else:
        curse.state = "dissolved"
        world.say(
            f"When {hero.id} returned the charm, the mist-hush knot loosened and drifted away."
        )


def tell(setting: Setting, relic_cfg: Relic, curse_cfg: Curse,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Aunt", kind="character", type=helper_type, label="the old aunt"))
    relic = world.add(Entity(id="relic", type="thing", label=relic_cfg.label, phrase=relic_cfg.phrase))
    curse = world.add(Entity(id="curse", type="thing", label=curse_cfg.label, phrase=curse_cfg.phrase))

    hero.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, there lived a {trait} {hero_type} named {hero_name} who loved the sea foam and the gull songs."
    )
    world.say(
        f"One day {hero_name} found {relic_cfg.phrase} near the stones."
    )
    world.say(
        f"That charm could help the lanterns, but {curse_cfg.phrase} had made the cove uneasy."
    )
    world.para()
    _do_suspense(world, hero, relic, curse)
    world.say(
        f"{hero_name} wanted to keep the {relic.label} for { _poss_word(hero_type) if False else 'own' } hands, but the old aunt was already watching the dark water."
    )
    _moral_turn(world, hero, helper, relic, curse)
    world.para()
    _transform(world, hero, relic, curse)
    world.say(
        f"By the end, {hero_name} was no longer thinking about taking. {hero_name} was helping the cove shine."
    )
    world.facts.update(hero=hero, helper=helper, relic=relic, curse=curse, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short folk tale about {hero.id} in {world.setting.place} with a {f['relic'].label} and a {f['curse'].label}.",
        f"Tell a child-friendly story where a {hero.type} learns a moral value by sharing something magical in a cove.",
        f"Write a gentle suspense story that ends with a transformation, using the words gland, spike-dim, and cove.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Who is the folk tale mainly about?",
            answer=f"It is about {hero.id}, a {hero.type} who lives by {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} find near the stones?",
            answer=f"{hero.id} found {f['relic'].phrase}.",
        ),
        QAItem(
            question=f"Why was the cove in suspense?",
            answer=f"The cove was in suspense because {f['curse'].phrase} was making the light grow dim before the tide climbed in.",
        ),
        QAItem(
            question=f"What moral choice did {hero.id} make?",
            answer=f"{hero.id} chose to share the {f['relic'].label} instead of keeping it.",
        ),
        QAItem(
            question=f"What changed after the choice?",
            answer=f"After the choice, the cove grew bright again and the curse broke apart or drifted away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cove?",
            answer="A cove is a small, curved inlet by the sea, often sheltered by rocks.",
        ),
        QAItem(
            question="What does it mean when something is dim?",
            answer="Dim means it is not bright, so it is harder to see.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice like kindness, honesty, or sharing that helps people live well together.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes into a new state, shape, or feeling by the end of the tale.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.state:
            bits.append(f"state={e.state}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
relevant(Place,Relic,Curse) :- place(Place), relic(Relic), curse(Curse), compatible(Place,Relic,Curse).
compatible(cove,gland,spike_dim).
compatible(shore,gland,spike_dim).
compatible(cove,lantern,spike_dim).
compatible(shore,lantern,spike_dim).
compatible(shore,gland,mist_hush).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for c in CURSES:
        lines.append(asp.fact("curse", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/3."))
    return sorted(set(asp.atoms(model, "relevant")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - ac:
        print(" only in python:", sorted(py - ac))
    if ac - py:
        print(" only in asp:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: cove, gland, spike-dim, moral choice, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)
              and (args.curse is None or c[2] == args.curse)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, relic, curse = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, curse=curse, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RELICS[params.relic], CURSES[params.curse],
                 params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="cove", relic="gland", curse="spike-dim", name="Mara", gender="girl", helper="aunt", trait="kind"),
    StoryParams(place="shore", relic="lantern", curse="spike-dim", name="Pip", gender="boy", helper="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show relevant/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relevant/3."))
        print(sorted(set(asp.atoms(model, "relevant"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.place}, {p.relic}, {p.curse}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
