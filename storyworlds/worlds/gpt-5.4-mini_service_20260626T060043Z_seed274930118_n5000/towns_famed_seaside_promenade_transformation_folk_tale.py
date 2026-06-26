#!/usr/bin/env python3
"""
Story world: famed seaside promenade transformation folk tale.

A small, self-contained simulation of a folk-tale style story set on a seaside
promenade where two towns decide whether to share a little magic that can
transform ordinary things into something famed and beautiful.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Town:
    id: str
    name: str
    fame: str
    color: str
    mood: str
    promenade_feature: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the seaside promenade"
    sea_breeze: str = "salt-bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    verb: str
    price: str
    condition: str
    turns_into: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    is_shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.towns: dict[str, Town] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_town(self, town: Town) -> Town:
        self.towns[town.id] = town
        return town

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
        clone.towns = copy.deepcopy(self.towns)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "promenade": Setting(place="the seaside promenade", sea_breeze="salt-bright", affords={"festival", "stroll", "repair"}),
}

TOWNS = {
    "harbor": Town(
        id="harbor",
        name="Harbor Town",
        fame="famous for its lantern fishers",
        color="blue",
        mood="proud",
        promenade_feature="a bent old boardwalk rail",
    ),
    "cliff": Town(
        id="cliff",
        name="Cliff Town",
        fame="famous for its cliffside bells",
        color="green",
        mood="stern",
        promenade_feature="a cracked mosaic bench",
    ),
    "shell": Town(
        id="shell",
        name="Shell Town",
        fame="famous for its shell singers",
        color="white",
        mood="hopeful",
        promenade_feature="a weathered shell arch",
    ),
}

MAGIC = {
    "paint": Magic(
        id="paint",
        label="a pot of moon-paint",
        verb="paint",
        price="a little patience",
        condition="needs a steady hand and a shared wish",
        turns_into="bright and famed",
        tags={"paint", "color", "art"},
    ),
    "glass": Magic(
        id="glass",
        label="a sea-glass charm",
        verb="glisten",
        price="a promise to share",
        condition="needs salt water and kind words",
        turns_into="clear and shining",
        tags={"glass", "shine", "sea"},
    ),
    "rope": Magic(
        id="rope",
        label="a singing rope",
        verb="bind",
        price="two hands working together",
        condition="needs a knot and a chorus",
        turns_into="strong and safe",
        tags={"rope", "repair", "song"},
    ),
}

TREASURES = {
    "arch": Treasure(
        id="arch",
        label="shell arch",
        phrase="a shell arch at the promenade",
        type="landmark",
    ),
    "bench": Treasure(
        id="bench",
        label="mosaic bench",
        phrase="a mosaic bench with cracked tiles",
        type="landmark",
    ),
    "rail": Treasure(
        id="rail",
        label="boardwalk rail",
        phrase="a bent boardwalk rail",
        type="landmark",
    ),
}

FOLK_NAMES = ["Mira", "Jon", "Tessa", "Pip", "Anya", "Robin", "Nell", "Bram"]
TRAITS = ["kind", "bold", "quiet", "curious", "steady", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    town_a: str
    town_b: str
    magic: str
    treasure: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def treasure_at_risk(magic: Magic, treasure: Treasure) -> bool:
    if magic.id == "paint":
        return treasure.id in {"bench", "rail"}
    if magic.id == "glass":
        return treasure.id in {"arch", "bench"}
    if magic.id == "rope":
        return treasure.id in {"rail", "arch"}
    return False


def compatible_fix(magic: Magic, treasure: Treasure) -> bool:
    return treasure_at_risk(magic, treasure)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for magic_id, magic in MAGIC.items():
            for treasure_id, treasure in TREASURES.items():
                if treasure_at_risk(magic, treasure) and compatible_fix(magic, treasure):
                    combos.append((place, magic_id, treasure_id))
    return combos


def explain_rejection(magic: Magic, treasure: Treasure) -> str:
    return (
        f"(No story: {magic.label} does not honestly transform {treasure.label} in a way "
        f"that matches the promenade problem, so there is no fair folk-tale turn.)"
    )


# ---------------------------------------------------------------------------
# Tale logic
# ---------------------------------------------------------------------------

def predict_transformation(world: World, magic: Magic, treasure: Treasure) -> dict:
    sim = world.copy()
    t = sim.entities[treasure.id]
    if treasure_at_risk(magic, treasure):
        t.meters["changed"] = 1.0
        t.memes["wonder"] = 1.0
    return {"changed": t.meters.get("changed", 0.0) >= THRESHOLD}


def introduce(world: World, hero: Entity, town_a: Town, town_b: Town) -> None:
    world.say(
        f"Long ago, {hero.id} was a {hero.memes.get('trait_word', 'kind')} child who loved "
        f"the sea wind at {world.setting.place}."
    )
    world.say(
        f"Nearby stood {town_a.name}, {town_a.fame}, and {town_b.name}, {town_b.fame}."
    )


def describe_promenade(world: World, town_a: Town, town_b: Town, treasure: Treasure) -> None:
    world.say(
        f"Between them lay {world.setting.place}, where {town_a.promenade_feature} leaned "
        f"beside {town_b.promenade_feature}."
    )
    world.say(f"The {treasure.label} looked plain, though it had the bones of a proud old tale.")


def wish_for_change(world: World, hero: Entity, magic: Magic, treasure: Treasure) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {magic.verb} the {treasure.label}, for the place felt ready "
        f"for something {magic.turns_into}."
    )


def warn_of_cost(world: World, town_a: Town, town_b: Town, magic: Magic, treasure: Treasure) -> bool:
    pred = predict_transformation(world, world.entities["hero"], magic, treasure)
    if not pred["changed"]:
        return False
    world.facts["warning"] = magic.price
    world.say(
        f'"If we use {magic.label}," said {town_a.name}, "we must pay {magic.price} or the change will fail."'
    )
    world.say(
        f'"And we must do it together," said {town_b.name}, "for {magic.condition}."'
    )
    return True


def quarrel(world: World, town_a: Town, town_b: Town) -> None:
    town_a.memes["pride"] = town_a.memes.get("pride", 0.0) + 1
    town_b.memes["pride"] = town_b.memes.get("pride", 0.0) + 1
    town_b.memes["worry"] = town_b.memes.get("worry", 0.0) + 1
    world.say(
        f"At first the two towns argued, each wanting the fame for itself."
    )


def share_and_transform(world: World, hero: Entity, town_a: Town, town_b: Town, magic: Magic, treasure: Treasure) -> None:
    treasure_ent = world.entities[treasure.id]
    town_a.memes["trust"] = town_a.memes.get("trust", 0.0) + 1
    town_b.memes["trust"] = town_b.memes.get("trust", 0.0) + 1
    treasure_ent.meters["changed"] = 1.0
    treasure_ent.memes["wonder"] = 1.0
    treasure_ent.memes["fame"] = 1.0
    town_a.memes["joy"] = town_a.memes.get("joy", 0.0) + 1
    town_b.memes["joy"] = town_b.memes.get("joy", 0.0) + 1
    world.say(
        f"Then {hero.id} tied the wish together with {magic.label}, and both towns worked as one."
    )
    world.say(
        f"The {treasure.label} began to glow and became {magic.turns_into}; soon it looked famed enough "
        f"for every traveler to remember."
    )


def ending_image(world: World, town_a: Town, town_b: Town, treasure: Treasure) -> None:
    world.say(
        f"By dusk, {world.setting.place} held a new bright center, and the {treasure.label} "
        f"shone between {town_a.name} and {town_b.name} like a shared moon."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale set on a seaside promenade where {f["town_a"].name} and {f["town_b"].name} share a magic that can transform a landmark.',
        f'Tell a child-friendly story about towns, fame, and transformation at {world.setting.place}.',
        f'Write a short seaside folk tale in which {f["hero"].id} helps turn the {f["treasure"].label} into something famed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    town_a: Town = f["town_a"]
    town_b: Town = f["town_b"]
    magic: Magic = f["magic"]
    treasure: Treasure = f["treasure"]
    qa = [
        QAItem(
            question=f"Who helped the two towns at {world.setting.place}?",
            answer=f"{hero.id}, a {f['trait']} child, helped {town_a.name} and {town_b.name} work together.",
        ),
        QAItem(
            question=f"What did the towns want to transform?",
            answer=f"They wanted to transform the {treasure.label} at the promenade.",
        ),
        QAItem(
            question=f"What was special about {magic.label}?",
            answer=f"It was a magic thing that could {magic.verb} the old landmark when the towns shared it properly.",
        ),
        QAItem(
            question="Why did the towns need to be careful?",
            answer=f"They had to pay {magic.price}, because the change only worked when they cooperated.",
        ),
        QAItem(
            question=f"What did the {treasure.label} become by the end?",
            answer=f"It became {magic.turns_into}, and it looked famed enough for the whole seaside to admire.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a promenade?",
            answer="A promenade is a walkway near the water where people can stroll, watch the sea, and enjoy the air.",
        ),
        QAItem(
            question="What does famed mean?",
            answer="Famed means known by many people and remembered with admiration.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means a change from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.treasure:
        m = MAGIC[args.magic]
        t = TREASURES[args.treasure]
        if not treasure_at_risk(m, t):
            raise StoryError(explain_rejection(m, t))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, magic_id, treasure_id = rng.choice(sorted(combos))
    town_ids = list(TOWNS)
    town_a, town_b = rng.sample(town_ids, 2)
    hero_name = args.name or rng.choice(FOLK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        town_a=town_a,
        town_b=town_b,
        magic=magic_id,
        treasure=treasure_id,
        name=hero_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    town_a = TOWNS[params.town_a]
    town_b = TOWNS[params.town_b]
    magic = MAGIC[params.magic]
    treasure = TREASURES[params.treasure]

    hero = world.add_entity(Entity(id="hero", kind="character", label=params.name, type="child"))
    hero.memes["trait_word"] = params.trait

    world.add_entity(Entity(id=treasure.id, kind="thing", label=treasure.label, type=treasure.type))
    world.add_town(town_a)
    world.add_town(town_b)

    world.facts.update(hero=hero, town_a=town_a, town_b=town_b, magic=magic, treasure=treasure, trait=params.trait)

    introduce(world, hero, town_a, town_b)
    world.para()
    describe_promenade(world, town_a, town_b, treasure)
    wish_for_change(world, hero, magic, treasure)
    warn_of_cost(world, town_a, town_b, magic, treasure)
    quarrel(world, town_a, town_b)
    world.para()
    share_and_transform(world, hero, town_a, town_b, magic, treasure)
    ending_image(world, town_a, town_b, treasure)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A treasure is at risk if the magic can change it.
treasure_at_risk(M, T) :- magic(M), treasure(T), risky_pair(M, T).

% A valid story exists when the chosen magic and treasure are compatible.
valid_story(P, M, T) :- setting(P), magic(M), treasure(T), treasure_at_risk(M, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for mid, m in MAGIC.items():
        for tid, t in TREASURES.items():
            if treasure_at_risk(m, t):
                lines.append(asp.fact("risky_pair", mid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about towns, fame, and transformation on a seaside promenade."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--treasure", choices=TREASURES)
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


CURATED = [
    StoryParams(place="promenade", town_a="harbor", town_b="cliff", magic="paint", treasure="bench", name="Mira", trait="kind"),
    StoryParams(place="promenade", town_a="cliff", town_b="shell", magic="glass", treasure="arch", name="Tessa", trait="curious"),
    StoryParams(place="promenade", town_a="harbor", town_b="shell", magic="rope", treasure="rail", name="Bram", trait="steady"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    for t in world.towns.values():
        lines.append(f"{t.id}: fame={t.fame} meters={t.meters} memes={t.memes}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.magic} over {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
