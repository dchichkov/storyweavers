#!/usr/bin/env python3
"""
storyworlds/worlds/chew_fare_indent_bad_ending_pirate_tale.py
==============================================================

A small pirate-tale story world with a bad ending.

Seed tale:
- A little pirate is tempted to chew the ship's fare.
- The captain warns that the fare is all they have left.
- There is an indent in the biscuit chest lid from an old hook.
- The child ignores the warning, chews anyway, and the hardtack cracks open.
- The ship's rations spill out, and the crew ends hungry.

This world keeps the tale tight on purpose:
- one child, one warning, one temptation, one irreversible loss
- a concrete pirate setting
- a bad ending that is driven by simulated state, not a frozen paragraph swap
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.chosen_indent: str = ""

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


SETTING = Setting(place="the little ship", affords={"chew"})
ACTIVITY = Activity(
    id="chew",
    verb="chew the fare",
    gerund="chewing the fare",
    rush="grab the hardtack and chew it anyway",
    mess="crumbled",
    soil="crumbled to bits",
    keyword="chew",
    tags={"chew", "fare", "indent", "pirate"},
)
PRIZE = Prize(
    label="fare",
    phrase="the last hardtack fare in the biscuit chest",
    type="fare",
    plural=False,
)

GIRL_NAMES = ["Mina", "Lulu", "Pia", "Ruby", "Sailor"]
BOY_NAMES = ["Pip", "Jory", "Ned", "Finn", "Toby"]
TRAITS = ["bold", "curious", "cheery", "stubborn", "spry"]

INDENTS = [
    "a small indent from an old hook",
    "a thumb-shaped indent in the lid",
    "a shallow indent near the latch",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("the little ship", "chew", "fare")]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "chew" and prize.label == "fare"


def select_fix(activity: Activity, prize: Prize):
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only works for the ship's fare in this world, "
        f"and the bad ending depends on that exact loss.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: the pirate child here is not restricted by gender for {prize_id}.)"


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    world.chosen_indent = random.Random(params.seed).choice(INDENTS)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "pirate"],
        memes={"hunger": 0.0, "longing": 0.0, "panic": 0.0, "regret": 0.0},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=params.parent,
        label="the captain",
        traits=["weathered", "careful"],
        memes={"worry": 1.0, "patience": 1.0},
    ))
    fare = world.add(Entity(
        id="fare",
        type="fare",
        label="fare",
        phrase="the last hardtack fare in the biscuit chest",
        caretaker=captain.id,
        meters={"whole": 1.0, "crumbles": 0.0},
    ))

    # Act 1: the ship and the tempting fare.
    world.say(
        f"On a little ship with a creaking deck, {hero.id} was a little {params.trait} pirate "
        f"who loved the smell of salty bread."
    )
    world.say(
        f"Next to the mast sat {fare.phrase}, and the chest lid had {world.chosen_indent}."
    )
    world.say(
        f"{hero.id} kept staring at the box and whispering about {ACTIVITY.keyword}ing the fare."
    )

    # Act 2: warning, desire, and the ignored warning.
    world.para()
    hero.memes["longing"] += 1.0
    world.say(
        f"{hero.id} wanted to {ACTIVITY.verb}, but {captain.pronoun('possessive')} {captain.label} shook "
        f"{captain.pronoun().capitalize()} head and said, "
        f"\"No, little matey. That's our fare for the stormy night.\""
    )
    world.say(
        f"{hero.id} saw the indent in the lid and thought it looked like a tiny bite mark."
    )
    hero.memes["panic"] += 0.5
    world.say(
        f"Still, {hero.id} reached for the biscuit chest and tried to {ACTIVITY.rush}."
    )

    # Bad turn: the fare is ruined, and there is no real fix.
    world.para()
    fare.meters["whole"] = 0.0
    fare.meters["crumbles"] = 1.0
    hero.memes["regret"] += 1.0
    captain.memes["worry"] += 1.0
    world.say(
        f"The hardtack cracked, crumbs flew across the boards, and {fare.label} {ACTIVITY.soil}."
    )
    world.say(
        f"By the time {hero.id} froze, the ship's last supper was already sliding into the seam between the planks."
    )

    # Ending image: the bad ending is visible in the world state.
    world.para()
    world.say(
        f"That night, the crew ate thin broth and looked at the empty chest, while {hero.id} "
        f"sat quiet beside the old indent and wished {hero.id} had listened."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        fare=fare,
        activity=ACTIVITY,
        setting=SETTING,
        indent=world.chosen_indent,
        resolved=False,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short pirate tale for a young child that includes the words "chew", "fare", and "indent".',
        f"Tell a little pirate story where {hero.id} wants to chew the ship's fare, but the captain warns {hero.id} not to.",
        "Write a simple pirate story with a bad ending about a child tempting the last rations on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    fare = f["fare"]
    indent = f["indent"]
    return [
        QAItem(
            question=f"What did {hero.id} want to chew?",
            answer=f"{hero.id} wanted to chew the fare, which was the ship's last hardtack in the biscuit chest.",
        ),
        QAItem(
            question=f"Why did {captain.label} warn {hero.id} to stop?",
            answer=f"{captain.label} warned {hero.id} because the fare was all the crew had left for the stormy night.",
        ),
        QAItem(
            question=f"What was special about the chest lid?",
            answer=f"The chest lid had {indent}, which made it look like a tiny bite mark to {hero.id}.",
        ),
        QAItem(
            question=f"What happened after {hero.id} ignored the warning?",
            answer=f"The fare cracked into crumbs and {fare.label} was ruined, so the crew ended the night hungry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fare on a ship?",
            answer="Fare is the food or rations a crew keeps for a trip, like hardtack, bread, or other simple meals.",
        ),
        QAItem(
            question="What is an indent?",
            answer="An indent is a small dent or hollow in a surface, like a mark pressed into a box lid.",
        ),
        QAItem(
            question="Why can hardtack be hard to chew?",
            answer="Hardtack is baked dry so it lasts a long time at sea, which makes it very hard and crunchy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  indent: {world.chosen_indent}")
    return "\n".join(lines)


ASP_RULES = r"""
% The story is valid when the pirate child wants to chew the fare on the ship.
valid_story(P, A, R) :- place(P), activity(A), prize(R), P = ship, A = chew, R = fare.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "ship"),
        asp.fact("activity", "chew"),
        asp.fact("prize", "fare"),
        asp.fact("affords", "ship", "chew"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with a bad ending.")
    ap.add_argument("--place", choices=["ship"], default=None)
    ap.add_argument("--activity", choices=["chew"], default=None)
    ap.add_argument("--prize", choices=["fare"], default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["captain"], default=None)
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
    if args.activity and args.prize:
        act, pr = ACTIVITY, PRIZE
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))
    place = args.place or "ship"
    activity = args.activity or "chew"
    prize = args.prize or "fare"
    if (place, activity, prize) != ("ship", "chew", "fare"):
        raise StoryError("(No valid combination matches the given options.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="ship", activity="chew", prize="fare", name="Pip", gender="boy", parent="captain", trait="bold"),
    StoryParams(place="ship", activity="chew", prize="fare", name="Mina", gender="girl", parent="captain", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible combo:\n  ship  chew  fare")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
