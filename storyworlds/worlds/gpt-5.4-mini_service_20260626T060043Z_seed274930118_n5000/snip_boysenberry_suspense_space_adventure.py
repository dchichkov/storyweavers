#!/usr/bin/env python3
"""
snip_boysenberry_suspense_space_adventure.py
============================================

A small space-adventure storyworld about a child crew member, a tricky
boysenberry vine, and a suspenseful choice that changes the ship's evening.

Seed premise:
- A child aboard a little ship wants to help a glowing boysenberry plant.
- The plant starts to tangle around a vent and threatens the air supply.
- The crew must decide whether to snip the vine and save the ship.

The story is generated from world state, not from a frozen template:
meters track physical amounts; memes track feelings and tension.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the little ship"
    place: str = "the greenhouse bay"
    route: str = "near the silver rings"
    hull: str = "bright and humming"
    affords: set[str] = field(default_factory=lambda: {"tend", "snip"})


@dataclass
class Tool:
    id: str
    label: str
    action: str
    careful: bool = True


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    scent: str
    tangles: bool = True


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.threat: float = 0.0

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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    crew = world.entities.get("hero")
    if not plant or not crew:
        return out
    if plant.meters.get("tangle", 0.0) >= THRESHOLD and world.threat < THRESHOLD:
        sig = ("suspense", "rising")
        if sig not in world.fired:
            world.fired.add(sig)
            crew.memes["worry"] = crew.memes.get("worry", 0.0) + 1
            out.append("A tense hush filled the bay.")
    return out


def _r_air_risk(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if not plant:
        return out
    if plant.meters.get("tangle", 0.0) < THRESHOLD:
        return out
    sig = ("air_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.threat = 1.0
    out.append("The vine was edging toward the vent.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_air_risk, _r_suspense):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_tend(world: World, hero: Entity, plant: Entity) -> None:
    hero.meters["care"] = hero.meters.get("care", 0.0) + 1
    plant.meters["tangle"] = plant.meters.get("tangle", 0.0) + 1
    plant.memes["comfort"] = plant.memes.get("comfort", 0.0) + 1
    propagate(world, narrate=False)


def _do_snip(world: World, hero: Entity, plant: Entity) -> None:
    hero.meters["care"] = hero.meters.get("care", 0.0) + 1
    if plant.meters.get("tangle", 0.0) >= THRESHOLD:
        plant.meters["tangle"] = 0.0
        plant.meters["safe"] = 1.0
        world.threat = 0.0
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        plant.memes["relief"] = plant.memes.get("relief", 0.0) + 1
    propagate(world, narrate=False)


SHIP = Ship()

TOOLS = {
    "snips": Tool(id="snips", label="tiny snips", action="snip", careful=True),
    "gloves": Tool(id="gloves", label="soft gloves", action="tend", careful=True),
}

PLANTS = {
    "boysenberry": Plant(
        id="boysenberry",
        label="boysenberry",
        phrase="a curly boysenberry vine",
        scent="sweet and green",
        tangles=True,
    )
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Aria"]
BOY_NAMES = ["Finn", "Jules", "Oren", "Pax", "Toby"]
TRAITS = ["brave", "curious", "gentle", "bright", "steady"]


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    tool: str
    plant: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: snip, boysenberry, suspense.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plant", choices=PLANTS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        name=name,
        gender=gender,
        trait=args.trait or rng.choice(TRAITS),
        tool=args.tool or rng.choice(list(TOOLS)),
        plant=args.plant or "boysenberry",
    )


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def generate(params: StoryParams) -> StorySample:
    world = World(SHIP)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=_hero_type(params.gender),
        label=params.name,
        owner="crew",
        meters={"care": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "wonder": 1.0},
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label="Captain Mira",
        meters={"watch": 1.0},
        memes={"calm": 1.0},
    ))
    plant = world.add(Entity(
        id="plant",
        type="plant",
        label="boysenberry",
        phrase=PLANTS[params.plant].phrase,
        owner="ship",
        caretaker="hero",
        meters={"tangle": 1.0},
        memes={"thirst": 1.0},
    ))
    tool = world.add(Entity(
        id=params.tool,
        type="tool",
        label=TOOLS[params.tool].label,
        phrase=TOOLS[params.tool].label,
        owner="hero",
        protective=True,
    ))

    world.say(
        f"{hero.label} was a {params.trait} {params.gender} aboard {world.ship.name}, "
        f"where the windows showed the dark curve of space."
    )
    world.say(
        f"{hero.label} loved the greenhouse bay because the air was warm there and "
        f"the {plant.label} smelled sweet and green."
    )
    world.say(
        f"One evening, {hero.label} found the curly boysenberry vine snaking toward a vent."
    )

    world.para()
    world.say(
        f"The red vent light blinked faster and faster, and the ship's whisper-soft fan grew loud enough to feel."
    )
    world.say(
        f"{hero.label} held {tool.label} close and listened while the vine curled tighter."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Captain Mira said, \"If that vine blocks the vent, our air will get thin.\""
    )
    world.say(
        f"{hero.label} looked at the boysenberry vine, then at the little snips."
    )
    _do_snip(world, hero, plant)

    world.para()
    world.say(
        f"{hero.label} made one careful snip."
    )
    if world.threat >= THRESHOLD:
        world.say("The vine fell away from the vent, and the blinking light slowed.")
        world.say(
            f"Fresh air rushed back through the bay, and the boysenberry leaves stopped trembling."
        )
    else:
        world.say("The vine settled down before trouble could grow, and the bay stayed calm.")
    world.say(
        f"{hero.label} smiled as the {plant.label} kept its soft shape, and the ship hummed gently beside the stars."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        plant=plant,
        tool=tool,
        params=params,
        resolved=world.threat == 0.0,
        threatened=True,
    )

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
    plant = f["plant"]
    return [
        f'Write a short space adventure story for a child named {hero.label} that includes the word "snip".',
        f"Tell a suspenseful story where {hero.label} must protect a boysenberry plant on a ship.",
        f"Write a gentle starship story about a boysenberry vine, a tense vent, and one careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    plant = f["plant"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {hero.type} crew member on the ship.",
        ),
        QAItem(
            question=f"What plant caused the suspense?",
            answer=f"The boysenberry plant caused the suspense because its vine curled toward a vent.",
        ),
        QAItem(
            question=f"What did {hero.label} use to fix the problem?",
            answer=f"{hero.label} used {tool.label} to make a careful snip and keep the ship safe.",
        ),
        QAItem(
            question=f"Why did Captain Mira warn {hero.label}?",
            answer="Captain Mira warned them because the vine could block the vent and make the ship's air thin.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the vent clear, the boysenberry safe, and the ship humming quietly beside the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boysenberry?",
            answer="A boysenberry is a dark berry that grows on a vine and can taste sweet and a little tart.",
        ),
        QAItem(
            question="What does snip mean?",
            answer="To snip means to cut something with a quick, small cut.",
        ),
        QAItem(
            question="Why can a blocked vent be a problem on a ship?",
            answer="A blocked vent can stop fresh air from moving through the ship, which makes the air less safe and less comfortable.",
        ),
        QAItem(
            question="Why can suspense make a story exciting?",
            answer="Suspense makes a story exciting because the reader wonders what will happen next and hopes things turn out well.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"threat={world.threat}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A boysenberry vine is at risk when it tangles near the vent.
at_risk(plant) :- tangles(plant), near_vent(plant).

% Snipping is a reasonable fix when the tool is careful and the plant is at risk.
reasonable_fix(snips, plant) :- at_risk(plant), careful(snips), can_snip(snips).

% The suspense story is valid if there is an at-risk plant and a fix.
valid_story(plant, snips) :- at_risk(plant), reasonable_fix(snips, plant).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("tangles", "plant"),
        asp.fact("near_vent", "plant"),
        asp.fact("careful", "snips"),
        asp.fact("can_snip", "snips"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("plant", "snips")}
    asp_set = set(asp_valid())
    if asp_set == py:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str]]:
    return [("boysenberry", "snips")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.tool != "snips":
        raise StoryError("Only snips make sense for this boysenberry suspense story.")
    if args.plant and args.plant != "boysenberry":
        raise StoryError("This world is built around a boysenberry plant.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait, tool="snips", plant="boysenberry")


def build_story_params_list(args: argparse.Namespace, base_seed: int, n: int) -> list[StoryParams]:
    out: list[StoryParams] = []
    for i in range(n):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        out.append(params)
    return out


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    for params in build_story_params_list(args, base_seed, args.n):
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
        if len(samples) >= args.n:
            break
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story combo:")
        print("  boysenberry + snips")
        return

    if args.all:
        args.n = 1

    samples = generate_many(args) if not args.all else [generate(StoryParams(
        name="Nova", gender="girl", trait="brave", tool="snips", plant="boysenberry", seed=args.seed
    ))]

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
