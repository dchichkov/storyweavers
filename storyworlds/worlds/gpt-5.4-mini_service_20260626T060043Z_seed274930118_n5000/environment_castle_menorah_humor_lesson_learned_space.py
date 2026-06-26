#!/usr/bin/env python3
"""
Standalone storyworld: a small space-adventure castle tale with a menorah,
humor, and a lesson learned.

Premise:
- A child explores an old castle in a space habitat.
- The child finds a menorah and wants to use the castle's shiny "environment"
  deck for a silly light show.
- Careless handling risks the menorah and the castle hall.
- A wiser helper suggests a safer, respectful plan.
- The child learns that jokes are fine, but precious things need care.

This world is intentionally small and constraint-driven.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str
    environment: str
    affords: set[str] = field(default_factory=set)
    mood: str = "bright"
    space_detail: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        return w


# Registries
SCENES = {
    "castle": Scene(
        place="the moon castle",
        environment="castle",
        affords={"decorate", "clean"},
        mood="bright",
        space_detail="The moon castle had silver halls, round windows, and a quiet room full of stars on the walls.",
    )
}

ITEMS = {
    "menorah": Item(
        id="menorah",
        label="menorah",
        phrase="a polished menorah",
        region="table",
        risk="sparkle",
        genders={"girl", "boy"},
    )
}

GEAR = [
    Gear(
        id="tray",
        label="a sturdy tray",
        covers={"table"},
        guards={"sparkle"},
        prep="set the menorah on a sturdy tray first",
        tail="placed the menorah carefully on the tray",
    )
]

NAMES = ["Mina", "Leo", "Tari", "Noah", "Rina", "Zia"]
TRAITS = ["curious", "funny", "bold", "gentle", "cheerful"]


@dataclass
class StoryParams:
    scene: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(scene: Scene, item: Item) -> bool:
    return scene.environment == "castle" and item.id == "menorah"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("environment", sc.environment))
        for a in sorted(sc.affords):
            lines.append(asp.fact("affords", sid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, item.risk))
        lines.append(asp.fact("worn_on", iid, item.region))
        for g in sorted(item.genders):
            lines.append(asp.fact("wears", g, iid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(S, I) :- scene(S), item(I), risk(I, sparkle), environment_castle(S).
has_fix(I) :- gear(G), item(I), guards(G, sparkle), covers(G, table).
valid(S, I) :- at_risk(S, I), has_fix(I).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, sc in SCENES.items():
        for iid, item in ITEMS.items():
            if reasonableness_gate(sc, item):
                combos.append((sid, iid))
    return combos


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - a:
        print("  only in python:", sorted(p - a))
    if a - p:
        print("  only in clingo:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-castle storyworld with a menorah, humor, and a lesson learned.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    scene = args.scene or "castle"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene=scene, name=name, gender=gender, trait=trait)


def generate_story(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    world = World(scene)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Guide", kind="character", type="mother", label="the guide"))
    menorah = world.add(Entity(
        id="menorah",
        kind="thing",
        type="menorah",
        label="menorah",
        phrase="a polished menorah",
        owner=hero.id,
        caretaker=helper.id,
    ))
    tray = world.add(Entity(
        id="tray",
        kind="thing",
        type="tray",
        label="tray",
        phrase="a sturdy tray",
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
    ))

    # Act 1
    world.say(f"{hero.id} was a {params.trait} child who loved space adventures and shiny surprises.")
    world.say(f"On the moon castle, {hero.id} found {menorah.phrase} in a quiet room with starry walls.")
    world.say(f"{hero.id} laughed and said, \"This looks like the tiniest rocket ship with candle spots!\"")

    # Act 2
    world.para()
    world.say(scene.space_detail)
    world.say(f"{hero.id} wanted to put the menorah on the castle's glowing environment deck and make a silly light show.")
    world.say(f"But the guide frowned a little, because a bumpy spill could tip it over and make a mess.")
    world.say(f"{hero.id} tried to spin around too fast, then stopped when {helper.pronoun('subject')} said, \"Funny is good, but careful is better.\"")

    # Act 3
    world.para()
    world.say(f"{helper.pronoun('possessive').capitalize()} {helper.label or 'guide'} smiled and offered a safer plan.")
    world.say(f"\"Let's {GEAR[0].prep}, then we can enjoy the lights without any trouble,\" {helper.pronoun('subject')} said.")
    tray.worn_by = hero.id
    world.say(f"{hero.id} listened, {GEAR[0].tail}, and set the menorah on the tray.")
    world.say(f"Then {hero.id} made a tiny space show with hand shadows instead of wild twirls.")
    world.say(f"{hero.id} giggled, because the joke was better when nothing got broken.")
    world.say(f"By the end, the menorah stayed safe, the castle stayed tidy, and {hero.id} learned that a good laugh can still be a careful one.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "menorah": menorah,
        "tray": tray,
        "scene": scene,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a gentle space adventure story about {hero.id} finding a menorah in a castle on the moon.",
        "Tell a funny child-friendly tale where careful choices protect a special object in a castle environment.",
        "Write a short story with a lesson learned: jokes are fun, but precious things need care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} find in the moon castle?",
            answer="The child found a polished menorah in a quiet room with starry walls.",
        ),
        QAItem(
            question=f"Why did the guide want {hero.id} to slow down?",
            answer="The guide worried that a bump or spill could tip the menorah over and make a mess.",
        ),
        QAItem(
            question=f"What was the safer plan in the end?",
            answer=f"{helper.pronoun('subject').capitalize()} suggested setting the menorah on a sturdy tray first, so the child could enjoy a funny light show without breaking anything.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The child learned that jokes are fun, but careful choices matter when something special needs to stay safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a castle?",
            answer="A castle is a big, strong building with walls and rooms, often from old stories and fairy tales.",
        ),
        QAItem(
            question="What is a menorah?",
            answer="A menorah is a candle holder with several branches that is used in Jewish celebrations.",
        ),
        QAItem(
            question="What is the environment in a story?",
            answer="The environment is the place and surroundings where the story happens, like a room, a castle, or a moon base.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.protective:
            bits.append("protective=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for scene, item in combos:
            print(f"  {scene} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(scene="castle", name=n, gender=g, trait=t) for n, g, t in [
            ("Mina", "girl", "curious"),
            ("Leo", "boy", "funny"),
            ("Rina", "girl", "cheerful"),
        ]]
        samples = [generate_story(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate_story(params)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a castle?",
            answer="A castle is a big, strong building with walls and rooms, often from old stories and fairy tales.",
        ),
        QAItem(
            question="What is a menorah?",
            answer="A menorah is a candle holder with several branches that is used in Jewish celebrations.",
        ),
        QAItem(
            question="What is the environment in a story?",
            answer="The environment is the place and surroundings where the story happens, like a room, a castle, or a moon base.",
        ),
    ]


if __name__ == "__main__":
    main()
