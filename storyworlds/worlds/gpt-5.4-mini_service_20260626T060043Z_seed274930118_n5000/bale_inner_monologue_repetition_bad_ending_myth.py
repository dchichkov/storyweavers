#!/usr/bin/env python3
"""
storyworlds/worlds/bale_inner_monologue_repetition_bad_ending_myth.py
======================================================================

A small myth-style story world about a bale, a worried helper, and a stubborn
choice that echoes in a harsh ending.

The seed image is simple:
- A great bale lies in a field like a golden stone.
- A child or a small keeper wants to move it.
- The world answers with signs, a warning, and a repeated thought.
- The ending is not kind: the bale rolls where it should not, and the lesson
  lands like dust in the mouth.

This world is designed to support:
- Inner monologue
- Repetition
- Bad ending
- Mythic tone
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    height: str
    has_stone_road: bool = False


@dataclass
class Bale:
    label: str
    phrase: str
    weight: int
    roll_distance: int
    can_block_path: bool
    can_fall_in_water: bool
    can_attract_hive: bool = False


@dataclass
class StoryParams:
    place: str
    bale: str
    hero_name: str
    hero_kind: str
    guide_kind: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    omen: str = ""

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
        clone.omen = self.omen
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "field": Setting(place="the field", kind="open", height="low"),
    "hillside": Setting(place="the hillside", kind="open", height="high"),
    "granary-yard": Setting(place="the granary yard", kind="workyard", height="low", has_stone_road=True),
    "riverbank": Setting(place="the riverbank", kind="water", height="low"),
}

BALES = {
    "straw-bale": Bale(
        label="straw bale",
        phrase="a round straw bale",
        weight=3,
        roll_distance=2,
        can_block_path=True,
        can_fall_in_water=True,
    ),
    "hay-bale": Bale(
        label="hay bale",
        phrase="a tall hay bale",
        weight=4,
        roll_distance=3,
        can_block_path=True,
        can_fall_in_water=True,
        can_attract_hive=True,
    ),
}

HERO_NAMES = ["Ari", "Nera", "Ivo", "Mira", "Tarin", "Leto", "Sera", "Korin"]
GUIDE_NAMES = ["Old Reed", "The Keeper", "Aunt Vale", "The Ferryman"]

KINDS = ["girl", "boy", "farmer", "shepherd", "child"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(place: str, bale_id: str) -> bool:
    setting = SETTINGS[place]
    bale = BALES[bale_id]
    if setting.kind == "water" and not bale.can_fall_in_water:
        return False
    if setting.kind == "workyard" and not setting.has_stone_road:
        return False
    return True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(field). place(hillside). place(granary_yard). place(riverbank).
bale(straw_bale). bale(hay_bale).

water_place(riverbank).
workyard(granary_yard).
has_stone_road(granary_yard).

can_fall_in_water(straw_bale).
can_fall_in_water(hay_bale).
can_block_path(straw_bale).
can_block_path(hay_bale).
can_attract_hive(hay_bale).

reasonable(P,B) :- place(P), bale(B), not water_conflict(P,B), not workyard_conflict(P,B).
water_conflict(P,B) :- water_place(P), not can_fall_in_water(B).
workyard_conflict(P,_) :- workyard(P), not has_stone_road(P).

#show reasonable/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid.replace("-", "_")))
    for bid, bale in BALES.items():
        b = bid.replace("-", "_")
        lines.append(asp.fact("bale", b))
        if bale.can_fall_in_water:
            lines.append(asp.fact("can_fall_in_water", b))
        if bale.can_block_path:
            lines.append(asp.fact("can_block_path", b))
        if bale.can_attract_hive:
            lines.append(asp.fact("can_attract_hive", b))
    for pid, s in SETTINGS.items():
        if s.kind == "water":
            lines.append(asp.fact("water_place", pid.replace("-", "_")))
        if s.kind == "workyard":
            lines.append(asp.fact("workyard", pid.replace("-", "_")))
        if s.has_stone_road:
            lines.append(asp.fact("has_stone_road", pid.replace("-", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {
        (place, bale_id)
        for place in SETTINGS
        for bale_id in BALES
        if story_is_reasonable(place, bale_id)
    }
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story machinery
# ---------------------------------------------------------------------------
def choose_omen(setting: Setting, bale: Bale) -> str:
    if setting.kind == "water":
        return "The river sang below the bank, and the bale smelled of rain."
    if setting.kind == "workyard":
        return "The stones were laid tight underfoot, and the carts waited like silent beasts."
    if bale.can_attract_hive:
        return "A small swarm turned and turned above the grass, as if the bale had a secret."
    return "The field was quiet, and even the crows seemed to watch."


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.bale not in BALES:
        raise StoryError(f"Unknown bale: {params.bale}")
    if not story_is_reasonable(params.place, params.bale):
        raise StoryError("That bale cannot plausibly be troubled in that place.")

    setting = SETTINGS[params.place]
    bale = BALES[params.bale]
    world = World(setting)
    world.omen = choose_omen(setting, bale)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        label=params.hero_name,
        meters={"tired": 0.0, "distance": 0.0},
        memes={"fear": 0.0, "hope": 1.0, "resolve": 1.0},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=params.guide_kind,
        label=random.choice(GUIDE_NAMES),
        meters={"distance": 0.0},
        memes={"worry": 1.0},
    ))
    bale_ent = world.add(Entity(
        id="bale",
        kind="thing",
        type="bale",
        label=bale.label,
        phrase=bale.phrase,
        owner=None,
        caretaker="guide",
        meters={"weight": float(bale.weight), "rolled": 0.0, "wet": 0.0, "blocked": 0.0},
        memes={"dread": 0.0},
        location=setting.place,
    ))

    world.facts.update(hero=hero, guide=guide, bale=bale_ent, bale_cfg=bale, setting=setting)
    return world


def _move_bale(world: World, step: int) -> None:
    bale = world.get("bale")
    bale.meters["rolled"] += step
    if world.setting.kind == "water":
        bale.meters["wet"] += 1
    if world.setting.kind == "workyard":
        bale.meters["blocked"] += 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    guide = world.get("guide")
    bale = world.get("bale")
    cfg = world.facts["bale_cfg"]

    world.say(
        f"At {world.setting.place}, there lay {bale.phrase}, round as an old moon "
        f"and heavy as a promise."
    )
    world.say(
        f"{hero.label} looked at it and thought, in a small private voice, "
        f"that one strong pull would be enough."
    )
    world.say(world.omen)

    world.para()
    world.say(
        f"{hero.label} wanted to move the bale, because it seemed to ask for a road."
    )
    world.say(
        f"Again and again, {hero.label} whispered the same brave thought: "
        f"'I can do it. I can do it. I can do it.'"
    )
    hero.memes["resolve"] += 1
    hero.memes["hope"] += 1
    _move_bale(world, 1)
    hero.meters["distance"] += 1
    hero.meters["tired"] += 1

    if cfg.can_attract_hive:
        world.say(
            f"A hush of bees rose from the grass, and {hero.label} felt the first sting of doubt."
        )
        hero.memes["fear"] += 1

    world.para()
    world.say(
        f"{guide.label} saw the trouble and called out, 'Leave the bale, little one. "
        f"It is not a toy for the road.'"
    )
    world.say(
        f"In the guide's heart there was worry, because a bale that rolls once may roll again."
    )
    guide.memes["worry"] += 1

    if world.setting.kind == "water":
        world.say(
            f"But {hero.label} kept pulling, thinking the river would not mind."
        )
        world.say(
            f'The thought came back like a drum: "I can do it. I can do it. I can do it."'
        )
        hero.memes["fear"] += 1
        _move_bale(world, 2)
        if cfg.can_fall_in_water:
            bale.location = "the water"
            bale.meters["wet"] += 2
            world.say(
                f"The bale slipped at the bank, rolled with a blunt and muddy sigh, and dropped into the river."
            )
            world.say(
                f"{hero.label} reached out too late, and the water took the bale away from the shore."
            )
            hero.memes["resolve"] = 0.0
            hero.memes["hope"] = 0.0
            hero.memes["fear"] += 2
        else:
            world.say("The bank held, but the effort left everyone shaking.")
    elif world.setting.kind == "workyard":
        world.say(
            f"But the bale snagged against the stone road, and the wheel-ruts held it fast."
        )
        _move_bale(world, 1)
        bale.meters["blocked"] += 2
        world.say(
            f"{hero.label} pulled harder and harder until the rope burned the palms and the bale would not budge."
        )
        world.say(
            f"The guide had to call for help, and the day grew long and sour."
        )
        hero.memes["fear"] += 1
    else:
        world.say(
            f"{hero.label} pulled at the bale until it rolled, slowly at first and then all at once."
        )
        _move_bale(world, cfg.roll_distance)
        if cfg.can_attract_hive:
            world.say(
                f"It rolled straight into a low nest in the grass, and bees rose in a black ribbon."
            )
            hero.memes["fear"] += 2
        else:
            world.say(
                f"It rolled past the fence and into the ditch, where no hand could hold it."
            )

    world.para()
    if world.setting.kind == "water":
        world.say(
            f"{hero.label} stood by the water and understood the end of the thing."
        )
        world.say(
            f"The bale was gone, and the field had not been made better by wanting."
        )
    elif world.setting.kind == "workyard":
        world.say(
            f"{hero.label} stood beside the stalled bale, shame warm as summer dust."
        )
        world.say(
            f"The road stayed blocked, and the guide's work waited heavier than before."
        )
    else:
        world.say(
            f"{hero.label} watched the bale disappear beyond reach and felt the world grow stern."
        )
        world.say(
            f"The road was open, but it had been opened the wrong way."
        )

    world.facts["ending_bad"] = True
    world.facts["ending_image"] = (
        "bale in the river" if world.setting.kind == "water"
        else "bale blocking the road" if world.setting.kind == "workyard"
        else "bale gone beyond the fence"
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    bale = f["bale_cfg"]
    return [
        f'Write a short mythic story for a child about a {bale.label} and a brave but mistaken choice.',
        f"Tell a story where {hero.label} keeps thinking 'I can do it' while trying to move a {bale.label}.",
        f"Write a myth-style tale with a repeated inner thought, a bale, and a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    bale = f["bale"]
    cfg = f["bale_cfg"]
    setting = f["setting"]

    qas = [
        QAItem(
            question=f"Where did {hero.label} see the {bale.label}?",
            answer=f"{hero.label} saw the {bale.label} at {setting.place}, where it lay heavy and still.",
        ),
        QAItem(
            question=f"What repeated thought kept running through {hero.label}'s mind?",
            answer=f"{hero.label} kept thinking, 'I can do it. I can do it. I can do it.'",
        ),
        QAItem(
            question=f"Who warned {hero.label} to leave the {bale.label} alone?",
            answer=f"{guide.label} warned {hero.label} and said the bale was not a toy for the road.",
        ),
        QAItem(
            question=f"What happened to the {bale.label} at the end?",
            answer=(
                "The ending was sad: "
                + ("it slipped into the river and was taken away." if setting.kind == "water"
                   else "it stayed stuck and blocked the way." if setting.kind == "workyard"
                   else "it rolled out of reach and was lost beyond the fence.")
            ),
        ),
    ]
    if cfg.can_attract_hive:
        qas.append(
            QAItem(
                question=f"What extra trouble came from the {bale.label}?",
                answer=f"The {bale.label} stirred up bees, which made {hero.label} even more afraid.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bale?",
            answer="A bale is a tightly bound bundle of straw or hay, pressed into a heavy shape that can be moved or stacked.",
        ),
        QAItem(
            question="Why can a bale be hard to move?",
            answer="A bale can be hard to move because it is heavy and bulky, so it takes strength or tools to roll or lift it.",
        ),
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land next to a river, where water can be close and the ground may be slippery.",
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
            f"  {e.id:10} ({e.kind:8}) type={e.type:10} "
            f"loc={e.location or '-':14} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  omen: {world.omen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for bale in BALES:
            if story_is_reasonable(place, bale):
                combos.append((place, bale))
    return combos


def explain_rejection(place: str, bale: str) -> str:
    return f"(No story: the {bale} cannot plausibly be troubled in {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic bale story world with an inner monologue and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bale", choices=BALES)
    ap.add_argument("--name")
    ap.add_argument("--hero-kind", choices=KINDS)
    ap.add_argument("--guide-kind", choices=KINDS)
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
    combos = [
        (p, b)
        for p, b in valid_combos()
        if (args.place is None or p == args.place)
        and (args.bale is None or b == args.bale)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bale = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(KINDS)
    guide_kind = args.guide_kind or rng.choice(KINDS)
    return StoryParams(
        place=place,
        bale=bale,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_kind=hero_kind,
        guide_kind=guide_kind,
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


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="field", bale="straw-bale", hero_name="Ari", hero_kind="child", guide_kind="farmer"),
    StoryParams(place="riverbank", bale="hay-bale", hero_name="Nera", hero_kind="girl", guide_kind="shepherd"),
    StoryParams(place="granary-yard", bale="straw-bale", hero_name="Ivo", hero_kind="boy", guide_kind="farmer"),
    StoryParams(place="hillside", bale="hay-bale", hero_name="Mira", hero_kind="child", guide_kind="shepherd"),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, bale) combos:\n")
        for place, bale in combos:
            print(f"  {place:12} {bale}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.bale} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
