#!/usr/bin/env python3
"""
storyworlds/worlds/ware_jay_guest_workshop_dialogue_surprise_superhero.py
=========================================================================

A small superhero workshop story world with dialogue and a surprise turn.

Premise:
- Ware is a young superhero who works in a workshop.
- Jay helps by building and testing gadgets.
- A guest arrives, and everyone expects a normal visit.
- A surprise reveals the guest needs help, and the heroes respond with dialogue,
  teamwork, and a clever repair.

The simulation tracks a few simple meters:
- brokenness of a tool or device
- pride, worry, and courage as memes
- repair progress and trust

The story is generated from a small world model so the middle turn and ending
are driven by state changes, not just swapped names.
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
    kind: str = "thing"  # "character" | "thing"
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
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Workshop:
    place: str = "the workshop"
    tools_ready: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    surprise: str
    trouble: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    broken_part: str
    can_fix: set[str] = field(default_factory=set)
    can_surprise: set[str] = field(default_factory=set)
    is_hero_gear: bool = False


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.scene: str = "setup"

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


@dataclass
class StoryParams:
    name: str
    sidekick: str
    guest: str
    mission: str
    gadget: str
    seed: Optional[int] = None


WORKSHOP = Workshop(place="the workshop", tools_ready=True, affords={"repair", "test", "greet"})

MISSIONS = {
    "signal": Mission(
        id="signal",
        verb="fix the signal lamp",
        gerund="repairing the signal lamp",
        surprise="the guest had a cracked beacon strapped to their coat",
        trouble="the lamp would not light",
        fix="swap in a bright lens",
        keyword="signal",
        tags={"light", "repair", "guest"},
    ),
    "wheel": Mission(
        id="wheel",
        verb="repair the rescue wheel",
        gerund="mending the rescue wheel",
        surprise="the guest rolled in with a bent wheel cart",
        trouble="the wheel kept wobbling",
        fix="straighten the axle and tighten the bolts",
        keyword="wheel",
        tags={"repair", "metal", "guest"},
    ),
    "capeclip": Mission(
        id="capeclip",
        verb="replace the cape clip",
        gerund="replacing the cape clip",
        surprise="the guest's cape clip had snapped shut",
        trouble="the cape would not stay in place",
        fix="fasten a new clip and test the clasp",
        keyword="cape",
        tags={"cloth", "repair", "guest"},
    ),
}

GADGETS = {
    "lens": Gadget(
        id="lens",
        label="a bright lens",
        phrase="a bright lens for the lamp",
        broken_part="lens",
        can_fix={"signal"},
        can_surprise={"signal"},
    ),
    "axle_tool": Gadget(
        id="axle_tool",
        label="a sturdy axle tool",
        phrase="a sturdy axle tool from the bench",
        broken_part="axle",
        can_fix={"wheel"},
        can_surprise={"wheel"},
    ),
    "clip_kit": Gadget(
        id="clip_kit",
        label="a clip kit",
        phrase="a clip kit with tiny silver hooks",
        broken_part="clip",
        can_fix={"capeclip"},
        can_surprise={"capeclip"},
    ),
}

NAMES = ["Ware", "Jay", "Mina", "Rex", "Tia", "Nova"]
GUESTS = ["Guest", "Avery", "Pip", "Milo", "June", "Robin"]
SIDEKICKS = ["Jay", "Moss", "Rue", "Bea", "Finn", "Sky"]


def tell(workshop: Workshop, mission: Mission, gadget: Gadget, name: str, sidekick: str, guest: str) -> World:
    world = World(workshop)

    hero = world.add(Entity(id=name, kind="character", type="hero", label=name))
    helper = world.add(Entity(id=sidekick, kind="character", type="sidekick", label=sidekick))
    visitor = world.add(Entity(id=guest, kind="character", type="guest", label=guest))

    tool = world.add(Entity(
        id="tool",
        type="gadget",
        label=gadget.label,
        phrase=gadget.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    hero.memes["pride"] = 1.0
    helper.memes["curiosity"] = 1.0
    visitor.memes["nervous"] = 0.0
    tool.meters["broken"] = 0.0
    tool.meters["fixed"] = 0.0

    world.say(
        f"In {workshop.place}, {hero.id} and {helper.id} were working side by side. "
        f"{helper.id} loved careful jobs, and {hero.id} loved being the one who could make things feel safe again."
    )
    world.say(
        f'"Do you think the day will stay calm?" {helper.id} asked.'
        f' "{hero.id} smiled and said, "Only if the tools behave."'
    )

    world.para()
    world.say(
        f"Then {visitor.id} arrived for a visit, and everyone thought it would be a normal stop. "
        f"'{visitor.id.capitalize()}?' {hero.id} said. 'Welcome to the workshop.'"
    )
    world.say(
        f'"Thanks," {visitor.id} replied, looking around the bright benches and humming wires. '
        f"'{helper.id}, I came because I need help.'"
    )

    world.para()
    world.say(
        f"The surprise was this: {mission.surprise}. "
        f"That meant the real trouble was not a visit at all; {mission.trouble}."
    )
    visitor.memes["worry"] = 1.0
    hero.memes["focus"] = 1.0
    helper.memes["focus"] = 1.0
    tool.meters["broken"] = 1.0
    world.facts["surprise"] = mission.surprise
    world.facts["trouble"] = mission.trouble

    world.say(f'"We can fix it," {helper.id} said, stepping closer to the bench.')
    world.say(f'"With what?" asked {visitor.id}.')
    world.say(f'"With {gadget.phrase}," said {hero.id}. "First we listen, then we repair."')

    tool.meters["fixed"] = 1.0
    tool.meters["broken"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["care"] = 1.0
    helper.memes["curiosity"] = 0.0
    helper.memes["joy"] = 1.0
    visitor.memes["worry"] = 0.0
    visitor.memes["trust"] = 1.0
    world.scene = "resolution"
    world.facts.update(hero=hero, helper=helper, visitor=visitor, mission=mission, gadget=gadget)

    world.para()
    world.say(
        f"{helper.id} handed over {gadget.label}, and {hero.id} used it to {mission.fix}. "
        f"At first there was a tiny spark, then a warm click, and then the workshop light glowed again."
    )
    world.say(
        f'"It works!" said {visitor.id}. "{hero.id}, {helper.id}, you really saved the day." '
        f'{hero.id} laughed and said, "We just made the workshop ready for the next surprise."'
    )
    world.say(
        f"In the end, {visitor.id} left smiling, {helper.id} stood beside the repaired tool, "
        f"and {hero.id} looked like a small superhero whose best power was helping on purpose."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    return [
        f'Write a short superhero story set in a workshop that includes a surprise guest and the word "{mission.keyword}".',
        f"Tell a child-friendly story where {f['hero'].id} and {f['helper'].id} talk with {f['visitor'].id} and repair a broken gadget.",
        f"Write a gentle superhero workshop story with dialogue, a surprise, and a happy ending after a repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    visitor = f["visitor"]
    mission = f["mission"]
    gadget = f["gadget"]
    return [
        QAItem(
            question=f"Who was the superhero in the workshop story?",
            answer=f"{hero.id} was the superhero who stayed calm and helped repair the problem.",
        ),
        QAItem(
            question=f"What surprise did {visitor.id} bring to the workshop?",
            answer=f"{visitor.id} brought a surprise problem, because {f['surprise']} and the tool needed fixing.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the trouble?",
            answer=f"They used {gadget.label} to {mission.fix}, and that made the workshop safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a workshop?",
            answer="A workshop is a place where people build, fix, and test things with tools and careful hands.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special skills to solve problems and protect others.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when people were not ready for it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  scene: {world.scene}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [("workshop", mission_id, gadget_id) for mission_id in MISSIONS for gadget_id in GADGETS if gadget_id.startswith({
        "signal": "lens",
        "wheel": "axle",
        "capeclip": "clip",
    }[mission_id])]


@dataclass
class StoryParams:
    place: str
    mission: str
    gadget: str
    name: str
    sidekick: str
    guest: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="workshop", mission="signal", gadget="lens", name="Ware", sidekick="Jay", guest="Guest"),
    StoryParams(place="workshop", mission="wheel", gadget="axle_tool", name="Ware", sidekick="Jay", guest="Avery"),
    StoryParams(place="workshop", mission="capeclip", gadget="clip_kit", name="Ware", sidekick="Jay", guest="Pip"),
]


ASP_RULES = r"""
compatible(M,G) :- mission(M), gadget(G), can_fix(G,M).
valid_story(P,M,G) :- place(P), compatible(M,G), P = workshop.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "workshop"))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for m in sorted(gadget.can_fix):
            lines.append(asp.fact("can_fix", gid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def explain_rejection(mission_id: str, gadget_id: str) -> str:
    return f"(No story: {gadget_id} does not reasonably solve {mission_id} in the workshop.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero workshop story world with dialogue and surprise.")
    ap.add_argument("--place", choices=["workshop"])
    ap.add_argument("--mission", choices=list(MISSIONS))
    ap.add_argument("--gadget", choices=list(GADGETS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--guest", choices=GUESTS)
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
    if args.mission and args.gadget:
        if args.gadget not in {"lens", "axle_tool", "clip_kit"}:
            raise StoryError(explain_rejection(args.mission, args.gadget))
        if not any(m == args.mission and g == args.gadget for _, m, g in valid_combos()):
            raise StoryError(explain_rejection(args.mission, args.gadget))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, gadget = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mission=mission,
        gadget=gadget,
        name=args.name or "Ware",
        sidekick=args.sidekick or "Jay",
        guest=args.guest or "Guest",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(WORKSHOP, MISSIONS[params.mission], GADGETS[params.gadget], params.name, params.sidekick, params.guest)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, gadget) combos:\n")
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
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.mission} with {p.gadget} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
