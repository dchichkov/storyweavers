#!/usr/bin/env python3
"""
storyworlds/worlds/breast_suspense_space_adventure.py
=====================================================

A small standalone storyworld about a tiny space adventure with suspense:
a child astronaut loses a breast patch from a spacesuit, a careful search
begins, and the story turns on a risky choice before a safe resolution.

The domain stays small on purpose:
- one space setting
- one suspenseful problem
- one helpful fix
- one ending image proving what changed

The word "breast" appears in a child-safe, concrete way as part of a spacesuit's
breast patch, a visible badge on the front of the suit.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    location: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    id: str
    name: str
    loss: str
    risk_zone: str
    suspense_line: str


@dataclass
class Fix:
    id: str
    name: str
    phrase: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "orbital_hall": Setting(
        place="the orbital hall",
        detail="The hall window glowed blue, and the stars hung still beyond it.",
    ),
    "dock": Setting(
        place="the docking bay",
        detail="The docking bay hummed softly, and a silver rover waited by the wall.",
    ),
}

PROBLEMS = {
    "breast_patch": Problem(
        id="breast_patch",
        name="breast patch",
        loss="stuck in the air vent",
        risk_zone="vent",
        suspense_line="The missing breast patch could drift deeper into the station.",
    )
}

FIXES = {
    "magnet_stick": Fix(
        id="magnet_stick",
        name="magnet stick",
        phrase="a long magnet stick",
        effect="pulled the patch back without touching the vent",
    ),
    "glove_reach": Fix(
        id="glove_reach",
        name="gloved reach",
        phrase="gloved hands and a slow careful reach",
        effect="brought the patch back with a careful hand",
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Rhea"]
BOY_NAMES = ["Kai", "Jett", "Orin", "Tao", "Pax"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(problem: Problem, fix: Fix) -> bool:
    return problem.id == "breast_patch" and fix.id in FIXES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "breast_patch", fix) for place in SETTINGS for fix in FIXES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful space-adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["robot", "captain"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix and not reasonableness_gate(PROBLEMS[args.problem], FIXES[args.fix]):
        raise StoryError("That problem and fix do not make a plausible space story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["robot", "captain"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, fix=fix, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    suit = world.add(Entity(
        id="suit",
        type="thing",
        label="spacesuit",
        phrase="a bright spacesuit with a front breast patch",
        owner=child.id,
    ))
    patch = world.add(Entity(
        id="patch",
        type="thing",
        label="breast patch",
        phrase="a small breast patch that matched the suit",
        owner=child.id,
        caretaker=helper.id,
    ))
    vent = world.add(Entity(id="vent", type="thing", label="air vent"))
    child.worn_by = None
    child.memes["hope"] += 1
    world.say(
        f"{child.id} was a {params.trait} little astronaut in {world.setting.place}. "
        f"{world.setting.detail}"
    )
    world.say(
        f"{child.id} loved {suit.phrase}, and {child.id} especially liked the little breast patch on the front."
    )
    world.para()
    world.say(
        f"Then the breast patch slipped off and skated toward the air vent. "
        f"{PROBLEMS[params.problem].suspense_line}"
    )
    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"{params.helper.capitalize()} held up a hand and said, "
        f"\"Easy now. We can still save it.\""
    )
    world.para()
    if params.fix == "magnet_stick":
        world.say(
            f"They used {FIXES[params.fix].phrase}, and it {FIXES[params.fix].effect}."
        )
        patch.location = "back on the suit"
        child.memes["relief"] += 2
        child.memes["worry"] = 0
        world.say(
            f"The breast patch clicked back into place, and {child.id} smiled at the shiny front of the suit."
        )
    else:
        world.say(
            f"They tried {FIXES[params.fix].phrase}, and it {FIXES[params.fix].effect}."
        )
        patch.location = "back on the suit"
        child.memes["relief"] += 1
        child.memes["worry"] = 0
        world.say(
            f"At last, the breast patch was safe again, and the suit looked neat and ready for the next launch."
        )
    world.facts.update(
        child=child,
        helper=helper,
        suit=suit,
        patch=patch,
        vent=vent,
        problem=PROBLEMS[params.problem],
        fix=FIXES[params.fix],
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short space adventure for a child named {p.name} who loses a breast patch and has to find it before it drifts away.',
        f'Tell a suspenseful story set in {world.setting.place} where {p.name} and {p.helper} save a breast patch from an air vent.',
        f'Write a gentle suspense story in space that includes the words "breast patch" and ends with the suit ready again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, a little {p.trait} astronaut, and {helper.label} helping in {world.setting.place}.",
        ),
        QAItem(
            question=f"What went missing from the spacesuit?",
            answer="A breast patch slipped off the front of the suit and drifted toward the air vent.",
        ),
        QAItem(
            question=f"How did they keep the breast patch from getting lost?",
            answer=f"They stayed calm, used {world.facts['fix'].phrase}, and brought it back before it drifted farther away.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and happy because the breast patch was back on the suit and everything was ready for the next trip.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a breast patch on a spacesuit?",
            answer="A breast patch is a small front piece on a suit, like a badge or marker, that sits on the chest area and helps the suit look complete.",
        ),
        QAItem(
            question="Why can an air vent be tricky in a spaceship?",
            answer="An air vent moves air through the ship, so tiny things can drift into it and become hard to reach.",
        ),
        QAItem(
            question="What does a magnet stick do?",
            answer="A magnet stick can pull back metal things from a place that is hard to reach, which makes it useful for careful rescue jobs.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem, Fix) :- setting(Place), problem(Problem), fix(Fix).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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
        for i, item in enumerate(sample.prompts, 1):
            print(f"{i}. {item}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for fix in FIXES:
                params = StoryParams(place=place, problem="breast_patch", fix=fix,
                                     name="Nova", gender="girl", helper="robot", trait="careful")
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
