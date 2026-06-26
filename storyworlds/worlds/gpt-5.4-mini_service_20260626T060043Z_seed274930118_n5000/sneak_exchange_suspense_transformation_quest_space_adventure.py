#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale built around
sneaking, an exchange, suspense, transformation, and a quest.

Premise:
- A child crewmate sneaks through a space station to exchange a small package.
- The package turns out to be an alien seed that transforms something on board.
- A suspenseful quest follows to restore the ship's map beacon and save the route home.

The world model tracks physical meters and emotional memes, and the prose is
driven by simulated state rather than a fixed paragraph template.
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


# ---------------------------------------------------------------------------
# Core entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Location:
    id: str
    label: str
    space: bool = True
    connects_to: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    protects: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "station"
    name: str = "Mila"
    gender: str = "girl"
    companion: str = "fox"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Location):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "station": Location(
        id="station",
        label="the star station",
        space=True,
        connects_to={"hangar", "corridor", "garden_bay", "map_room"},
        affords={"sneak", "exchange", "quest"},
    ),
    "hangar": Location(
        id="hangar",
        label="the hangar",
        space=True,
        connects_to={"station", "dock"},
        affords={"sneak", "exchange"},
    ),
    "corridor": Location(
        id="corridor",
        label="the long corridor",
        space=True,
        connects_to={"station", "map_room", "garden_bay"},
        affords={"sneak", "quest"},
    ),
    "garden_bay": Location(
        id="garden_bay",
        label="the glass garden bay",
        space=True,
        connects_to={"station", "corridor"},
        affords={"transformation", "quest"},
    ),
    "map_room": Location(
        id="map_room",
        label="the map room",
        space=True,
        connects_to={"station", "corridor"},
        affords={"quest"},
    ),
    "dock": Location(
        id="dock",
        label="the moonlit dock",
        space=True,
        connects_to={"hangar"},
        affords={"exchange"},
    ),
}

TOOLS = {
    "gloves": Tool(
        id="gloves",
        label="gravity gloves",
        phrase="a pair of gravity gloves",
        use="grip",
        protects={"spark"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a pocket lantern",
        phrase="a tiny pocket lantern",
        use="light",
        protects=set(),
    ),
    "kit": Tool(
        id="kit",
        label="a repair kit",
        phrase="a small repair kit",
        use="fix",
        protects={"glitch"},
    ),
}

ITEMS = {
    "seed": Entity(
        id="seed",
        type="thing",
        label="star seed",
        phrase="a star seed sealed in a glass pod",
        meters={"glow": 0.0},
    ),
    "map_chip": Entity(
        id="map_chip",
        type="thing",
        label="map chip",
        phrase="a narrow map chip",
        meters={"glow": 0.0},
    ),
    "vine": Entity(
        id="vine",
        type="thing",
        label="moon vine",
        phrase="a silver moon vine",
        meters={"growth": 0.0},
    ),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def choice_reasonable(setting: Location, params: StoryParams) -> bool:
    return setting.id in LOCATIONS and params.gender in {"girl", "boy"}


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, g) for sid in LOCATIONS for g in ("girl", "boy")]


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def _move(world: World, actor: Entity, dest: str) -> None:
    actor.location = dest


def _sneak(world: World, actor: Entity, target: Entity, dest: str) -> None:
    actor.memes["suspense"] = actor.memes.get("suspense", 0.0) + 1.0
    actor.meters["quiet_steps"] = actor.meters.get("quiet_steps", 0.0) + 1.0
    actor.location = dest
    target.location = dest
    world.facts["sneak_done"] = True
    world.say(f"{actor.id} slipped through the {world.setting.label} without a sound.")


def _exchange(world: World, actor: Entity, other: Entity, item_a: Entity, item_b: Entity) -> None:
    item_a.carried_by = other.id
    item_b.carried_by = actor.id
    world.facts["exchange_done"] = True
    world.say(
        f"{actor.id} and {other.id} made the exchange carefully, palm to palm, "
        f"while the ship hummed like it was holding its breath."
    )


def _transformation(world: World, vine: Entity, room: Entity) -> None:
    if vine.meters.get("growth", 0.0) >= THRESHOLD:
        return
    vine.meters["growth"] = 1.0
    room.meters["glow"] = room.meters.get("glow", 0.0) + 1.0
    world.facts["transformed"] = True
    world.say(
        f"In the glass garden bay, the moon vine shimmered and began to grow "
        f"into a bright silver braid around the support rail."
    )


def _quest(world: World, actor: Entity, tool: Entity, room: Entity) -> None:
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1.0
    world.facts["quest_done"] = True
    world.say(
        f"{actor.id} followed the glowing trail to the map room, used {tool.label} "
        f"to repair the beacon, and the route home lit up again."
    )


def predict_transformation(world: World, actor: Entity) -> bool:
    sim = world.copy()
    vine = sim.get("vine")
    room = sim.get("garden_bay")
    _transformation(sim, vine, room)
    return bool(vine.meters.get("growth", 0.0) >= THRESHOLD)


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    setting = LOCATIONS[params.setting]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        location=setting.id,
        meters={"courage": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "hope": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion,
        label=f"little {params.companion}",
        location=setting.id,
        meters={"trust": 1.0},
        memes={"watchful": 1.0},
    ))
    guard = world.add(Entity(
        id="guard",
        kind="character",
        type="captain",
        label="Captain Rhea",
        location="dock",
        meters={"patience": 1.0},
        memes={"worry": 1.0},
    ))
    seed = world.add(copy.deepcopy(ITEMS["seed"]))
    chip = world.add(copy.deepcopy(ITEMS["map_chip"]))
    vine = world.add(copy.deepcopy(ITEMS["vine"]))
    vine.location = "garden_bay"

    # Act 1: setup
    world.say(
        f"{hero.id} lived aboard {setting.label} and loved the hush of space, "
        f"where every hallway felt like a secret."
    )
    world.say(
        f"{hero.id} and the little {params.companion} watched the stars and dreamed "
        f"of a quest that could save something important."
    )
    world.say(
        f"One evening, {guard.label} asked {hero.id} to carry {chip.phrase} to the dock "
        f"without anyone noticing."
    )
    world.para()

    # Act 2: sneaking exchange
    _sneak(world, hero, companion, "corridor")
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} breath, because the wrong light "
        f"could wake the whole station."
    )
    world.say(
        f"In the hangar, the package opened by mistake, and the glass pod showed "
        f"{seed.phrase} inside."
    )
    _exchange(world, hero, companion, seed, chip)
    world.say(
        f"The swap felt strange, and {hero.id} wondered whether the station was hiding "
        f"a bigger secret."
    )
    world.para()

    # Act 3: suspenseful transformation and quest
    if predict_transformation(world, hero):
        world.say(
            f"Following a thin green glow, {hero.id} tiptoed into the garden bay."
        )
        _transformation(world, vine, world.get("garden_bay"))
    world.say(
        f"Then the glow led {hero.id} to the map room, where the beacon blinked weakly."
    )
    tool = world.add(Entity(
        id="repair_tool",
        kind="thing",
        type="tool",
        label="the repair kit",
        phrase="the repair kit",
        carried_by=hero.id,
    ))
    _quest(world, hero, tool, world.get("map_room"))
    world.say(
        f"At the end, the station was quiet again, but now the hallway plants "
        f"curled into silver shapes, and the stars on the map pointed safely home."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        guard=guard,
        seed=seed,
        chip=chip,
        vine=vine,
        tool=tool,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a child-friendly space adventure about {hero.id} who must sneak through a star station.",
        "Tell a suspenseful story where a small exchange changes the mission on a space station.",
        "Write a quest story with a surprising transformation in a glass garden under the stars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    vine = f["vine"]
    return [
        QAItem(
            question=f"Why did {hero.id} sneak through the station?",
            answer=(
                f"{hero.id} sneaked through the station because {guard_name := f['guard'].label} "
                f"asked for a careful exchange, and the mission had to stay quiet."
            ),
        ),
        QAItem(
            question="What changed after the exchange in the hangar?",
            answer=(
                f"After the exchange, the glass pod was opened and the star seed began to matter "
                f"more, because it led {hero.id} toward the garden bay and the map room."
            ),
        ),
        QAItem(
            question="What was transformed in the garden bay?",
            answer=(
                f"The moon vine was transformed into a bright silver braid around the support rail, "
                f"which showed that the station was changing in a strange but helpful way."
            ),
        ),
        QAItem(
            question=f"How did the quest end for {hero.id} and the little {comp.type}?",
            answer=(
                f"The quest ended when {hero.id} repaired the beacon in the map room and the route home lit up again, "
                f"with the little {comp.type} watching beside {hero.id}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a star map for?",
            answer="A star map helps travelers find where they are in space and which way to go next.",
        ),
        QAItem(
            question="Why do spaceships use beacons?",
            answer="A beacon sends out a signal so a ship can be found or can find its way home.",
        ),
        QAItem(
            question="What does it mean to sneak?",
            answer="To sneak means to move quietly and carefully so nobody notices you right away.",
        ),
        QAItem(
            question="What is an exchange?",
            answer="An exchange is when two people give things to each other and take the other person's item.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form or becomes noticeably different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(station;hangar;corridor;garden_bay;map_room;dock).

affords(station,sneak). affords(station,exchange). affords(station,quest).
affords(hangar,sneak). affords(hangar,exchange).
affords(corridor,sneak). affords(corridor,quest).
affords(garden_bay,transformation). affords(garden_bay,quest).
affords(map_room,quest).
affords(dock,exchange).

feature(sneak). feature(exchange). feature(suspense). feature(transformation). feature(quest).

valid(Setting) :- setting(Setting).

#show valid/1.
"""

def asp_facts() -> str:
    import asp  # lazy
    lines = []
    for sid in LOCATIONS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(LOCATIONS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for feat in ("sneak", "exchange", "suspense", "transformation", "quest"):
        lines.append(asp.fact("feature", feat))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[str]:
    import asp  # lazy
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted({a[0] for a in asp.atoms(model, "valid")})


def asp_verify() -> int:
    python_set = {sid for sid in LOCATIONS}
    clingo_set = set(asp_valid_settings())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python settings ({len(python_set)} settings).")
        return 0
    print("MISMATCH between ASP and Python settings:")
    print("  only in ASP:", sorted(clingo_set - python_set))
    print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Space Adventure storyworld.")
    ap.add_argument("--setting", choices=sorted(LOCATIONS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["fox", "cat", "mouse", "robot"])
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
    setting = args.setting or rng.choice(sorted(LOCATIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if not choice_reasonable(LOCATIONS[setting], StoryParams(setting=setting, gender=gender)):
        raise StoryError("No reasonable story matches the requested options.")
    return StoryParams(
        setting=setting,
        name=args.name or rng.choice(["Mila", "Nia", "Kai", "Tess", "Rin", "Luna"]),
        gender=gender,
        companion=args.companion or rng.choice(["fox", "cat", "mouse", "robot"]),
    )


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
    StoryParams(setting="station", name="Mila", gender="girl", companion="fox"),
    StoryParams(setting="hangar", name="Kai", gender="boy", companion="robot"),
    StoryParams(setting="corridor", name="Luna", gender="girl", companion="cat"),
    StoryParams(setting="garden_bay", name="Rin", gender="boy", companion="mouse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid settings:")
        for (sid,) in vals:
            print(f"  {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
