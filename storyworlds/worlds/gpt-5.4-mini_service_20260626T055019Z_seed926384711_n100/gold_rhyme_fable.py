#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/gold_rhyme_fable.py
=================================================================================================

A small fable-like storyworld about finding gold, keeping promises, and learning
that sharing can shine brighter than hoarding.

This world is deliberately tiny and classical:
- one place
- one tempting object: gold
- one moral turn
- one gentle resolution
- lightly rhymed prose for the story text

The world model tracks both physical state (meters) and emotional state (memes)
so the story is driven by simulated change rather than a frozen paragraph swap.
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
# Story data
# ---------------------------------------------------------------------------

PLACE_CHOICES = {
    "meadow": {
        "name": "the meadow",
        "features": {"bird", "stone", "stream", "burrow"},
    },
    "riverbank": {
        "name": "the riverbank",
        "features": {"bird", "reed", "stone", "water"},
    },
    "orchard": {
        "name": "the orchard",
        "features": {"bird", "apple", "branch", "path"},
    },
}

CHARACTER_NAMES = ["Milo", "Lena", "Cora", "Finn", "Nia", "Toby", "Ivy", "Pip"]
CHARACTER_TYPES = ["fox", "hare", "crow", "mole", "mouse", "squirrel"]
TRAITS = ["wise", "bright", "quick", "gentle", "curious", "proud"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str = "gold"
    phrase: str = "a small bright piece of gold"
    sparkle: str = "shone like a tiny sun"
    weight: str = "light"
    value: str = "rare"


@dataclass
class StoryParams:
    place: str
    name: str
    species: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


def soften(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def say_rhyme(world: World, a: str, b: str) -> None:
    world.say(soften(rhyme_pair(a, b)))


def fable_opening(hero: Entity, setting: Setting) -> str:
    return (
        f"Once in {setting.place}, there lived a {hero.meme('trait_word')} {hero.type} named {hero.id}, "
        f"who liked calm paths and morning daft."
    )


def wonder_line(treasure: Treasure, setting: Setting) -> str:
    return (
        f"One dawn, near a stone in {setting.place}, {treasure.sparkle} and made the grass glow bright; "
        f"the little gold looked plain at first, then turned the day to light."
    )


def find_gold(world: World, hero: Entity, treasure: Entity) -> None:
    treasure.owner = hero.id
    treasure.meters["held"] = 1
    hero.meters["delight"] = hero.meter("delight") + 1
    hero.memes["wonder"] = hero.meme("wonder") + 1
    world.say(
        f"{hero.id} found the gold beside a warm old stone, and his heart went quick and light; "
        f"he tucked it in a leaf for safekeeping, proud to keep it out of sight."
    )


def boast(world: World, hero: Entity) -> None:
    hero.memes["greed"] = hero.meme("greed") + 1
    hero.memes["pride"] = hero.meme("pride") + 1
    world.say(
        f"{hero.id} whispered, \"This gold is mine, all mine,\" with a grin so sharp and bold; "
        f"\"I'll hide it near my home and never share the shining gold.\""
    )


def helper_arrives(world: World, helper: Entity, hero: Entity, treasure: Entity) -> None:
    helper.meters["tired"] = helper.meter("tired") + 1
    helper.memes["need"] = helper.meme("need") + 1
    world.say(
        f"Then {helper.id} came by with a torn little pouch, and the pouch had slipped its seam; "
        f"he asked for help to gather seeds, because the wind had stolen his dream."
    )
    world.facts["helper_id"] = helper.id
    world.facts["helper_need"] = "pouch"


def refuse(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["stingy"] = hero.meme("stingy") + 1
    world.say(
        f"{hero.id} looked at the gold and shook his head, though the other asked so mild; "
        f"he clutched the shine and chose to keep it, selfish as a sulky child."
    )


def regret(world: World, hero: Entity) -> None:
    hero.memes["unease"] = hero.meme("unease") + 1
    world.say(
        f"But when the wind ran through the grass, the gold felt heavy in his paw; "
        f"it gleamed less bright inside his pouch, and his joy began to thaw."
    )


def change_mind(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["kindness"] = hero.meme("kindness") + 1
    hero.memes["greed"] = max(0.0, hero.meme("greed") - 1)
    treasure.owner = helper.id
    treasure.meters["held"] = 0
    world.say(
        f"At last {hero.id} sighed, then gave the gold to {helper.id}, and his voice grew warm and true; "
        f"\"A shared bright thing is brighter still,\" he said, \"and now my heart is new.\""
    )


def ending_image(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["peace"] = hero.meme("peace") + 1
    helper.memes["relief"] = helper.meme("relief") + 1
    world.say(
        f"Together they tied the torn pouch tight and seeded it with care; "
        f"the gold still shone, but friendship shone more, and both were glad to share."
    )


def build_world(params: StoryParams) -> World:
    setting = Setting(place=PLACE_CHOICES[params.place]["name"], features=set(PLACE_CHOICES[params.place]["features"]))
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.species,
        label=params.name,
        meters={"delight": 0.0},
        memes={"trait_word": 1.0},
    ))
    helper_name = next(n for n in CHARACTER_NAMES if n != params.name)
    helper_type = "mouse" if params.species != "mouse" else "bird"
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        meters={"tired": 0.0},
        memes={"need": 0.0},
    ))
    treasure = world.add(Entity(
        id="gold",
        kind="thing",
        type="gold",
        label="gold",
        phrase="a small bright piece of gold",
        owner=None,
        meters={"held": 0.0},
        memes={"shine": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, treasure=treasure, setting=setting, params=params)

    # Act 1: opening, discovery
    world.say(fable_opening(hero, setting))
    world.say(wonder_line(Treasure(), setting))
    find_gold(world, hero, treasure)

    # Act 2: temptation and strain
    world.para()
    boast(world, hero)
    helper_arrives(world, helper, hero, treasure)
    refuse(world, hero, helper, treasure)
    regret(world, hero)

    # Act 3: turn and resolution
    world.para()
    change_mind(world, hero, helper, treasure)
    ending_image(world, hero, helper, treasure)

    return world


def generate_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    return [
        f"Write a short fable in rhyme about {hero.id} in {setting.place} finding gold and learning to share.",
        f"Tell a gentle rhyming story where {hero.id} meets {helper.id} and discovers that gold can bring a kinder end.",
        f"Write a child-friendly fable with gold, a worried heart, and a generous turn in {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    treasure: Entity = world.facts["treasure"]
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {setting.place}?",
            answer=f"{hero.id} found {treasure.phrase} near a stone in {setting.place}.",
        ),
        QAItem(
            question=f"Why did {helper.id} ask {hero.id} for help?",
            answer=f"{helper.id} needed help because his little pouch had torn and he wanted to gather seeds safely.",
        ),
        QAItem(
            question=f"What changed when {hero.id} gave the gold away?",
            answer=f"{hero.id} stopped clinging to the gold, felt kinder, and the two friends ended the day sharing and working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gold?",
            answer="Gold is a shiny yellow metal that people often think of as valuable and special.",
        ),
        QAItem(
            question="Why do fables often have a moral?",
            answer="Fables often end with a moral so the story can gently teach a lesson about how to act.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you instead of keeping it only for yourself.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        parts.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_place/1.
#show valid_story/2.

valid_place(P) :- place(P).
valid_story(P, H) :- valid_place(P), hero(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACE_CHOICES:
        lines.append(asp.fact("place", pid))
    for name in CHARACTER_NAMES:
        lines.append(asp.fact("hero", name))
    lines.append(asp.fact("treasure", "gold"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    asp_places = sorted(set(asp.atoms(model, "valid_place")))
    py_places = sorted((p,) for p in PLACE_CHOICES.keys())
    if asp_places != py_places:
        print("MISMATCH between ASP and Python place registry.")
        print("ASP:", asp_places)
        print("PY :", py_places)
        return 1
    print(f"OK: ASP and Python agree on {len(py_places)} places.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about gold and rhyme.")
    ap.add_argument("--place", choices=sorted(PLACE_CHOICES))
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--species", choices=CHARACTER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACE_CHOICES))
    name = args.name or rng.choice(CHARACTER_NAMES)
    species = args.species or rng.choice(CHARACTER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, species=species, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(place="meadow", name="Milo", species="fox", trait="wise"),
    StoryParams(place="riverbank", name="Lena", species="crow", trait="curious"),
    StoryParams(place="orchard", name="Cora", species="hare", trait="gentle"),
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

        model = asp.one_model(asp_program("#show valid_place/1."))
        vals = sorted(set(asp.atoms(model, "valid_place")))
        print("\n".join(str(v) for v in vals))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
