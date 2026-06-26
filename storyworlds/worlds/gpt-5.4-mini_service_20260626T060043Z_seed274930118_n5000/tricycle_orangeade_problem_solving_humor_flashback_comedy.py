#!/usr/bin/env python3
"""
Story world: tricycle + orangeade problem solving comedy with a flashback.

A small, self-contained classical simulation for a TinyStories-style domain:
a child wants to ride a tricycle, a spill creates a problem, humor keeps the
tone light, and a flashback explains why the child is careful with orangeade.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sidewalk"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemSpec:
    label: str
    phrase: str
    region: str
    type: str = "thing"
    plural: bool = False


@dataclass
class ProblemSpec:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixSpec:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    avoids: set[str]


@dataclass
class StoryParams:
    place: str
    problem: str
    item: str
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
        self.facts: dict = {}
        self.flashback_done = False

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_done = self.flashback_done
        return clone


SETTINGS = {
    "sidewalk": Setting("the sidewalk", False, {"ride"}),
    "driveway": Setting("the driveway", False, {"ride"}),
    "porch": Setting("the porch", False, {"ride"}),
}

PROBLEMS = {
    "ride": ProblemSpec(
        id="ride",
        verb="ride the tricycle",
        gerund="riding the tricycle",
        rush="zoom down the path",
        mess="wobble",
        soil="squished orangeade",
        zone={"floor"},
        keyword="tricycle",
        tags={"tricycle", "ride", "humor", "flashback"},
    ),
    "spill": ProblemSpec(
        id="spill",
        verb="sip the orangeade",
        gerund="sipping orangeade",
        rush="reach too fast for the cup",
        mess="sticky",
        soil="orangeade-splashed",
        zone={"floor", "hands"},
        keyword="orangeade",
        tags={"orangeade", "spill", "humor"},
    ),
}

ITEMS = {
    "tricycle": ItemSpec(
        label="tricycle",
        phrase="a shiny red tricycle with a bell",
        region="floor",
        type="tricycle",
    ),
    "cup": ItemSpec(
        label="orangeade",
        phrase="a cool cup of orangeade with a striped straw",
        region="hands",
        type="cup",
    ),
}

FIXES = [
    FixSpec(
        id="towel",
        label="a towel",
        phrase="put a towel under the orangeade cup",
        prep="put a towel under the orangeade cup first",
        tail="set a towel under the cup",
        avoids={"sticky"},
    ),
    FixSpec(
        id="tray",
        label="a tray",
        phrase="set the orangeade on a tray",
        prep="set the orangeade on a tray first",
        tail="moved the cup onto a tray",
        avoids={"sticky"},
    ),
]

NAMES = {
    "girl": ["Mia", "Ruby", "Nora", "Lily", "Ada"],
    "boy": ["Finn", "Leo", "Max", "Theo", "Ben"],
}
TRAITS = ["silly", "curious", "cheerful", "lively", "goofy"]


def reasonableness_gate(place: str, problem: ProblemSpec, item: ItemSpec) -> bool:
    if place not in SETTINGS:
        return False
    if problem.id == "ride" and item.type != "tricycle":
        return False
    if problem.id == "spill" and item.type != "cup":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for iid, item in ITEMS.items():
                if reasonableness_gate(place, prob, item):
                    combos.append((place, pid, iid))
    return combos


def select_fix(problem: ProblemSpec) -> Optional[FixSpec]:
    for fix in FIXES:
        if problem.mess not in fix.avoids:
            continue
        return fix
    return None


def flashback(world: World, hero: Entity) -> None:
    if world.flashback_done:
        return
    world.flashback_done = True
    world.say(
        f"Once, {hero.id} had tried to balance orangeade and a tricycle bell at the same time, "
        f"and the orangeade had won. The memory made {hero.pronoun('object')} giggle and pause."
    )


def tell_story(setting: Setting, problem: ProblemSpec, item: ItemSpec, hero: Entity, parent: Entity, prize: Entity) -> World:
    world = World(setting)
    world.add(hero)
    world.add(parent)
    world.add(prize)

    world.say(
        f"{hero.id} was a {hero.meters.get('age_word', 'little')} {hero.type} who loved fun things that made people laugh."
    )
    world.say(
        f"{hero.id} loved {problem.gerund} and making jokes with {hero.pronoun('possessive')} {parent.label or parent.type}."
    )
    world.say(
        f"One bright day, {hero.id} found {prize.phrase} beside {world.setting.place}."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {problem.verb}, but the day had a tiny snag: {problem.soil} was one wobble away."
    )
    flashback(world, hero)
    world.say(
        f"{hero.id} almost {problem.rush}, then stopped and looked at the cup like it was a very serious joke."
    )

    fix = select_fix(problem)
    if not fix:
        raise StoryError("No reasonable fix exists for this problem.")
    world.say(
        f"Then {hero.id}'s {parent.label or parent.type} smiled and said, "
        f'"Let’s {fix.prep}."'
    )
    world.say(
        f"{hero.id} nodded, because that was the sort of idea that felt smart and a little funny at once."
    )

    world.para()
    world.say(
        f"So {hero.id} {fix.tail}, climbed onto the tricycle, and rolled away without tipping a drop."
    )
    world.say(
        f"The orangeade stayed safe, the tricycle bell went ding-ding, and {hero.id} laughed so hard that even {hero.pronoun('possessive')} {parent.label or parent.type} snorted."
    )
    world.say(
        f"By the end, the little problem was solved, the orangeade was still neat, and the driveway had become a comedy stage."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        problem=problem,
        fix=fix,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    prize = f["prize"]
    return [
        f'Write a funny story for a young child about {hero.id}, a tricycle, and orangeade.',
        f"Tell a comedy story where {hero.id} wants to {problem.verb} but keeps the orangeade safe.",
        f'Write a short story with a flashback that helps solve a tricycle-and-orangeade problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {problem.verb}.",
        ),
        QAItem(
            question=f"What was the tricky thing that could have caused a mess?",
            answer=f"The tricky thing was the orangeade, because it could turn into {problem.soil}.",
        ),
        QAItem(
            question=f"What idea helped {hero.id} solve the problem?",
            answer=f"{hero.id} solved it by using {fix.label} and following {parent.id}'s gentle idea.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause before rushing ahead?",
            answer="A flashback reminded the child that mixing tricycle fun and orangeade can make a sticky mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tricycle?",
            answer="A tricycle is a small ride with three wheels that a child can pedal.",
        ),
        QAItem(
            question="What is orangeade?",
            answer="Orangeade is a sweet orange drink, like lemonade made with oranges.",
        ),
        QAItem(
            question="Why do people sometimes stop and think before solving a problem?",
            answer="Stopping first can help someone choose a safer and smarter fix.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
place(sidewalk). place(driveway). place(porch).
problem(ride). problem(spill).
item(tricycle). item(cup).

reasonable(P, ride, tricycle) :- place(P).
reasonable(P, spill, cup) :- place(P).

#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: tricycle and orangeade problem solving with a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place or args.problem or args.item:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.problem is None or c[1] == args.problem)
            and (args.item is None or c[2] == args.item)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, item = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    item = ITEMS[params.item]
    hero = Entity(id=params.name, kind="character", type=params.gender, meters={"age_word": 1.0}, memes={"joy": 1.0})
    parent = Entity(id=params.parent.title(), kind="character", type=params.parent, label=params.parent)
    prize = Entity(id=item.label, type=item.type, label=item.label, phrase=item.phrase, owner=hero.id, caretaker=parent.id)

    world = tell_story(setting, problem, item, hero, parent, prize)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="sidewalk", problem="ride", item="tricycle", name="Mia", gender="girl", parent="mother", trait="silly"),
    StoryParams(place="driveway", problem="spill", item="cup", name="Finn", gender="boy", parent="father", trait="goofy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/3."))
        for t in sorted(set(asp.atoms(model, "reasonable"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
