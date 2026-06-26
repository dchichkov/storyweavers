#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/simmer_succinct_problem_solving_pirate_tale.py
===========================================================================================================================

A standalone story world for a small pirate-tale problem-solving domain.

Seed premise:
---
A pirate crew is delayed in a quiet cove because their anchor line has snagged
on a reef tooth. While the galley pot sits simmering, the captain gives a
succinct plan: use a hook, free the line, and sail on before supper boils dry.

This script generates a tiny classical simulation with a fixed causal arc:
setup -> problem -> plan -> solution -> closing image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "captain": ("she", "her", "her"),
            "pirate": ("he", "him", "his"),
            "girl": ("she", "her", "her"),
            "boy": ("he", "him", "his"),
        }
        subj, obj, pos = mapping.get(self.type, ("it", "it", "its"))
        return {"subject": subj, "object": obj, "possessive": pos}[case]

    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Ship:
    place: str
    sea: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

    def copy(self) -> "Ship":
        clone = Ship(place=self.place, sea=self.sea)
        clone.entities = {
            k: Entity(
                id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
                owner=v.owner, caretaker=v.caretaker, worn_by=v.worn_by,
                meters=dict(v.meters), memes=dict(v.memes),
            )
            for k, v in self.entities.items()
        }
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str = "quiet cove"
    hero: str = "Mara"
    hero_type: str = "captain"
    helper: str = "Joss"
    helper_type: str = "pirate"
    seed: Optional[int] = None


PLACES = {
    "quiet cove": {"sea": "still water", "descriptor": "quiet"},
    "reef bay": {"sea": "green water", "descriptor": "reef-shadowed"},
    "harbor mouth": {"sea": "blue water", "descriptor": "windy"},
}

HERO_NAMES = ["Mara", "Nell", "Rook", "Ivy", "Bram"]
HELPER_NAMES = ["Joss", "Tamsin", "Finn", "Pip", "Sailor"]

TOOLS = {
    "hook": {
        "label": "boat hook",
        "phrase": "a long boat hook",
        "verb": "hook the anchor line free",
        "method": "reach the snag and tug it loose",
        "covers": "line",
    },
    "knife": {
        "label": "cutting knife",
        "phrase": "a sharp little knife",
        "verb": "slice the rope away",
        "method": "cut the twisted fibers cleanly",
        "covers": "rope",
    },
    "pulley": {
        "label": "deck pulley",
        "phrase": "a sturdy deck pulley",
        "verb": "lift the line with a careful pull",
        "method": "raise the rope until the snag slips off",
        "covers": "line",
    },
}

PROBLEM = {
    "snagged_line": {
        "title": "snagged anchor line",
        "risk": "the ship could not sail until the line was freed",
        "effect": "the crew was stuck in the cove",
    }
}


@dataclass
class World:
    ship: Ship
    hero: Entity
    helper: Entity
    tool: Entity
    anchor_snagged: bool = True
    ship_stuck: bool = True
    supper_simmering: bool = True
    plan_given: bool = False
    problem_solved: bool = False
    fired: set[str] = field(default_factory=set)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale problem-solving storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(place=place, hero=hero, helper=helper, seed=args.seed)


def _tool_choice() -> str:
    return "hook"


def build_world(params: StoryParams) -> World:
    place_cfg = PLACES[params.place]
    ship = Ship(place=params.place, sea=place_cfg["sea"])
    hero = ship.add(Entity(id=params.hero, kind="character", type="captain", label="captain"))
    helper = ship.add(Entity(id=params.helper, kind="character", type="pirate", label="mate"))
    tool_def = TOOLS[_tool_choice()]
    tool = ship.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_def["label"],
        phrase=tool_def["phrase"],
        owner=hero.id,
    ))
    ship.facts.update(
        place=params.place,
        place_descriptor=place_cfg["descriptor"],
        hero=hero,
        helper=helper,
        tool=tool,
        tool_def=tool_def,
    )
    return World(ship=ship, hero=hero, helper=helper, tool=tool)


def predict_solution(world: World) -> bool:
    return world.anchor_snagged and world.ship_stuck and world.tool.label == "boat hook"


def tell(world: World) -> None:
    s = world.ship
    hero = world.hero
    helper = world.helper
    tool = world.tool
    tool_def = s.facts["tool_def"]
    place_descriptor = s.facts["place_descriptor"]

    s.say(f"{hero.id} was the captain of a small pirate ship resting in a {place_descriptor} cove.")
    s.say(f"{helper.id} was the mate, quick with knots and quick with a grin.")
    s.say(f"Below deck, supper was simmering in a pot, and the smell of onions drifted up the stairs.")
    s.say(f"Then the ship gave a small jerk. The anchor line had snagged on a reef tooth, and the ship could not sail.")

    s.para()
    s.say(f"{helper.id} peered over the rail and frowned. \"The line is caught hard,\" {helper.pronoun('subject')} said.")
    s.say(f"{hero.id} looked at the water, then at the deck, and gave a succinct nod.")
    s.say(f"\"One tool, one pull, no fuss,\" {hero.pronoun('subject')} said. \"{tool_def['verb'].capitalize()}.\"")
    world.plan_given = True

    s.para()
    if predict_solution(world):
        s.say(f"{helper.id} fetched {tool.phrase}, and the two pirates worked together.")
        s.say(f"{helper.id} {tool_def['method']}. {hero.id} braced the rail and pulled at the right moment.")
        world.anchor_snagged = False
        world.ship_stuck = False
        world.problem_solved = True
        s.say(f"The snag slipped free with a wet pop. The ship rocked once, then drifted forward at last.")
        s.say(f"From below deck came a happy bubble from the simmering pot, as if the soup knew the bad part was done.")
    else:
        raise StoryError("The chosen tool cannot solve the snagged-line problem in this storyworld.")

    s.para()
    s.say(f"{hero.id} smiled at the open water and called for the sails.")
    s.say(f"The crew sailed out of the cove just in time for supper, with the little pot still simmering and the deck clear.")


def story_qa(world: World) -> list[QAItem]:
    s = world.ship
    hero = world.hero
    helper = world.helper
    tool = world.tool
    place = world.ship.place
    return [
        QAItem(
            question=f"Why were {hero.id} and the crew stuck in the cove?",
            answer=f"They were stuck because the anchor line had snagged on a reef tooth, so the ship could not sail yet.",
        ),
        QAItem(
            question=f"What kind of plan did {hero.id} give to solve the problem?",
            answer=f"{hero.id} gave a succinct plan: use {tool.label}, free the line, and get the ship moving again.",
        ),
        QAItem(
            question=f"What did {helper.id} do to help?",
            answer=f"{helper.id} fetched the {tool.label} and helped {hero.id} work the snag loose.",
        ),
        QAItem(
            question=f"What was happening below deck while they solved the problem?",
            answer="Supper was simmering in a pot, and the smell of it drifted up while the crew worked.",
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place in {place}, where the ship waited in the water near the shore.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does simmering mean?",
            answer="Something that is simmering is cooking with small gentle bubbles just below a full boil.",
        ),
        QAItem(
            question="What does succinct mean?",
            answer="Succinct means brief and clear, with only the important parts.",
        ),
        QAItem(
            question="What is a boat hook for?",
            answer="A boat hook is a long tool used to reach, pull, or guide things on and near a boat.",
        ),
        QAItem(
            question="Why do pirates use teamwork on a ship?",
            answer="Pirates use teamwork because many ship jobs need more than one set of hands.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    s = world.ship
    hero = world.hero
    tool = world.tool
    return [
        f"Write a pirate tale where {hero.id} gives a succinct plan to solve a ship problem.",
        f"Tell a short story with the words simmer and succinct, and include {tool.label}.",
        "Write a child-friendly pirate story about a problem on a ship and how the crew fixes it together.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.ship.place}")
    lines.append(f"anchor_snagged={world.anchor_snagged}")
    lines.append(f"ship_stuck={world.ship_stuck}")
    lines.append(f"supper_simmering={world.supper_simmering}")
    lines.append(f"plan_given={world.plan_given}")
    lines.append(f"problem_solved={world.problem_solved}")
    for e in world.ship.entities.values():
        lines.append(f"  {e.id}: kind={e.kind}, type={e.type}, label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(snagged_line).
tool(hook).
solves(hook,snagged_line).
valid_story(Place,Problem,Tool) :- place(Place), problem(Problem), tool(Tool), solves(Tool,Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("problem", "snagged_line"))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    lines.append(asp.fact("solves", "hook", "snagged_line"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, "snagged_line", "hook") for p in PLACES}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.ship.render(),
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_asp_output() -> str:
    return asp_program("#show valid_story/3.")


CURATED = [
    StoryParams(place="quiet cove", hero="Mara", helper="Joss"),
    StoryParams(place="reef bay", hero="Nell", helper="Pip"),
    StoryParams(place="harbor mouth", hero="Rook", helper="Tamsin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_output())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
