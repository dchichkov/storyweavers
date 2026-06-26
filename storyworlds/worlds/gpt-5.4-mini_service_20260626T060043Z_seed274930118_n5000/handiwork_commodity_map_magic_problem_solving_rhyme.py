#!/usr/bin/env python3
"""
Standalone storyworld: handiwork, commodity, map, with Magic, Problem Solving,
and Rhyme in an adventure style.

Premise:
- A young helper makes or mends a map with careful handiwork.
- A needed commodity is missing, traded, or misused.
- Magic makes the map respond, but only if the child solves a problem.
- A rhyme becomes the key to finishing the quest.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- story-driven simulation
- Python reasonableness gate plus inline ASP twin
- generation, Q&A, trace, JSON, verify, show-asp, all
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    magic: bool = False
    worn_by: Optional[str] = None
    location: str = ""

    def __post_init__(self):
        if not self.meters:
            self.meters = {"damage": 0.0, "value": 0.0, "missing": 0.0, "cleverness": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "joy": 0.0, "confusion": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    detail: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Commodity:
    id: str
    label: str
    phrase: str
    kind: str
    scarcity: str
    useful_for: str
    price: int
    plural: bool = False


@dataclass
class Problem:
    id: str
    title: str
    verb: str
    obstacle: str
    clue: str
    consequence: str
    requires: str


@dataclass
class Magic:
    id: str
    label: str
    effect: str
    cost: str
    trigger: str
    rhyme_hint: str


@dataclass
class Rhyme:
    id: str
    couplet: str
    key_word: str
    helps_with: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(
        place="the harbor market",
        indoors=False,
        detail="Salt wind tugged at awnings, and bright stalls bobbed like little ships.",
        affordances={"mending", "trading", "mapping"},
    ),
    "library": Setting(
        place="the lantern library",
        indoors=True,
        detail="Tall shelves made narrow lanes, and a round table waited under a brass lamp.",
        affordances={"mending", "mapping"},
    ),
    "canyon": Setting(
        place="the red canyon camp",
        indoors=False,
        detail="Cliffs glowed like embers, and paths curled between stones and scrub.",
        affordances={"mapping", "trading"},
    ),
}

COMMODITIES = {
    "thread": Commodity("thread", "spool of thread", "a spool of strong thread", "thread", "rare", "mending a torn map edge", 2),
    "wax": Commodity("wax", "wax seal", "a little wax seal", "wax", "common", "holding folded pages together", 1),
    "ink": Commodity("ink", "ink bottle", "a small bottle of blue ink", "ink", "limited", "drawing clear map marks", 3),
    "lampoil": Commodity("lampoil", "lamp oil", "a tin of lamp oil", "oil", "scarce", "lighting the map room", 4),
}

PROBLEMS = {
    "torn_map": Problem(
        "torn_map",
        "torn map",
        "mend",
        "the map had a rip across the river path",
        "the torn edge made the trail hard to follow",
        "the way to the hidden cove could not be read",
        "thread",
    ),
    "smudged_route": Problem(
        "smudged_route",
        "smudged route",
        "trace",
        "salt spray had blurred the compass marks",
        "the route points kept sliding into one dark streak",
        "the secret turn to the bridge was lost",
        "ink",
    ),
    "stuck_fold": Problem(
        "stuck fold",
        "unfold",
        "the map was sealed shut with old wax",
        "the page would not open at the center crease",
        "the clue near the old tower could not be seen",
        "wax",
    ),
}

MAGICS = {
    "glow": Magic(
        "glow",
        "glow spell",
        "the map shimmered and the hidden path appeared in silver lines",
        "a brave voice and steady hands",
        "the child spoke the rhyme while holding the map near the lamp",
        "shine",
    ),
    "wind": Magic(
        "wind",
        "wind spell",
        "a warm breeze lifted the page corners and showed the next clue",
        "a careful breath and a clear rhyme",
        "the child tapped the map three times and sang the lines",
        "breeze",
    ),
}

RHYMES = {
    "shine": Rhyme(
        "shine",
        "When the way is hard to find, keep your hands both brave and kind.",
        "shine",
        "glow spell",
    ),
    "breeze": Rhyme(
        "breeze",
        "If the lines hide what you see, sing it out and let it be.",
        "breeze",
        "wind spell",
    ),
}

NAMES = ["Mina", "Arlo", "Tess", "Pip", "Nori", "Jude", "Lina", "Omar"]
KINDS = ["girl", "boy"]
PARENT_KINDS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    commodity: str
    problem: str
    magic: str
    rhyme: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reason_ok(problem: Problem, commodity: Commodity, magic: Magic, rhyme: Rhyme, setting: Setting) -> bool:
    if problem.requires != commodity.id:
        return False
    if setting.indoors and problem.id == "smudged_route":
        return True
    if not setting.indoors and problem.id == "torn_map":
        return True
    return problem.id in {"torn_map", "smudged_route", "stuck_fold"} and commodity.id in COMMODITIES and magic.id in MAGICS and rhyme.id in RHYMES


def explain_rejection(problem: Problem, commodity: Commodity) -> str:
    return (
        f"(No story: {commodity.label} cannot honestly solve the {problem.title}; "
        f"the problem needs a different commodity.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    commodity = COMMODITIES[params.commodity]
    magic = MAGICS[params.magic]
    rhyme = RHYMES[params.rhyme]

    if not reason_ok(problem, commodity, magic, rhyme, setting):
        raise StoryError(explain_rejection(problem, commodity))

    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    map_item = world.add(Entity(
        id="map",
        type="map",
        label="map",
        phrase="an old folded map",
        owner=child.id,
        caretaker=parent.id,
        magic=True,
        location=setting.place,
    ))
    com = world.add(Entity(
        id=commodity.id,
        type=commodity.kind,
        label=commodity.label,
        phrase=commodity.phrase,
        owner=parent.id,
        caretaker=parent.id,
        location=setting.place,
    ))

    # Setup
    world.say(f"{child.id} was a quick-handed little adventurer who loved making careful handiwork.")
    world.say(f"At {setting.place}, {child.id} carried {map_item.phrase} and hoped to use it on a real quest.")
    world.say(f"{child.id}'s {params.parent} had brought {com.phrase}, a handy commodity for the day's work.")
    world.para()

    # Conflict
    world.say(setting.detail)
    world.say(
        f"But the map had a problem: {problem.obstacle}, and {problem.clue}."
    )
    world.say(
        f"{child.id} frowned, because {problem.consequence}."
    )
    child.memes["worry"] += 1
    child.memes["hope"] += 1
    world.say(
        f"Still, {child.id} did not give up. {child.id} chose to solve the problem with handiwork first."
    )
    world.para()

    # Problem solving with handiwork and commodity
    if problem.id == "torn_map":
        map_item.meters["damage"] += 1
        com.meters["value"] += 1
        world.say(f"Carefully, {child.id} threaded the torn edge and patched the map with {com.label}.")
        world.say(f"The rip held together better with every neat stitch.")
    elif problem.id == "smudged_route":
        map_item.meters["damage"] += 1
        world.say(f"{child.id} wiped the smudged route clean and retraced the lines with fresh {com.label}.")
        world.say(f"The path stopped wobbling and became sharp again.")
    else:
        map_item.meters["damage"] += 1
        world.say(f"{child.id} warmed the sealed fold and loosened it with a little {com.label}.")
        world.say(f"The map opened at last, as if it had been waiting to breathe.")

    child.meters["cleverness"] += 1
    child.memes["joy"] += 1
    world.para()

    # Magic + rhyme
    world.say(
        f"Then {child.id} lifted the map, whispered a magic spell, and spoke the rhyme:"
    )
    world.say(f'"{rhyme.couplet}"')
    world.say(
        f"At once, {magic.effect}."
    )
    world.say(
        f"The spell worked because the rhyme fit the trick, and the trick fit the map."
    )
    child.memes["pride"] += 1
    world.para()

    # Resolution and ending image
    world.say(
        f"{child.id} and {parent.label} followed the shining clue to the right path."
    )
    world.say(
        f"In the end, the map was whole, the commodity had done its job, and {child.id} had turned a problem into an adventure."
    )
    world.say(
        f"{child.id} tucked the map away like treasure, smiling at the neat handiwork and the bright magic that had guided the way."
    )

    world.facts = {
        "child": child,
        "parent": parent,
        "map": map_item,
        "commodity": com,
        "problem": problem,
        "magic": magic,
        "rhyme": rhyme,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    com = f["commodity"]
    magic = f["magic"]
    rhyme = f["rhyme"]
    return [
        f'Write an adventure story for a young child where {child.id} uses handiwork to solve a map problem with a {com.label}.',
        f'Create a short tale about a damaged map, a useful commodity, and a magic rhyme that helps {child.id} finish the quest.',
        f'Write a child-friendly adventure with a map, problem solving, and magic, ending in a rhyme that makes the path appear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    problem = f["problem"]
    com = f["commodity"]
    magic = f["magic"]
    rhyme = f["rhyme"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What was {child.id} trying to fix at {setting.place}?",
            answer=f"{child.id} was trying to fix an {problem.title} so the map could be used on the quest.",
        ),
        QAItem(
            question=f"What commodity helped {child.id} solve the map problem?",
            answer=f"The helpful commodity was {com.phrase}, which {child.id} used with careful handiwork.",
        ),
        QAItem(
            question=f"How did the magic and rhyme help at the end?",
            answer=f"{child.id} spoke the rhyme and used the magic spell, and then {magic.effect}.",
        ),
        QAItem(
            question=f"Who went with {child.id} on the adventure?",
            answer=f"{child.id} went with {parent.label}, who brought the commodity and watched the plan work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is handiwork?",
            answer="Handiwork is careful work made by hands, like sewing, fixing, drawing, or building something neatly.",
        ),
        QAItem(
            question="What is a commodity?",
            answer="A commodity is a useful thing that people can buy, trade, or use because it has value.",
        ),
        QAItem(
            question="What is a map for?",
            answer="A map helps people find places and choose the right path when they travel.",
        ),
        QAItem(
            question="Why do people use rhymes?",
            answer="People use rhymes because the repeating sounds make words easy to remember and fun to say.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a commodity matches the problem and the magic/rhyme pair is known.
matched(P, C) :- problem(P), commodity(C), requires(P, C).
valid_story(S, P, C, M, R) :- setting(S), problem(P), commodity(C), magic(M), rhyme(R), matched(P, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("requires", pid, p.requires))
    for cid in COMMODITIES:
        lines.append(asp.fact("commodity", cid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set()
    for s in SETTINGS:
        for p in PROBLEMS:
            for c in COMMODITIES:
                for m in MAGICS:
                    for r in RHYMES:
                        if reason_ok(PROBLEMS[p], COMMODITIES[c], MAGICS[m], RHYMES[r], SETTINGS[s]):
                            python_set.add((s, p, c, m, r))
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} valid stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for cid, commodity in COMMODITIES.items():
                for mid, magic in MAGICS.items():
                    for rid, rhyme in RHYMES.items():
                        if reason_ok(problem, commodity, magic, rhyme, setting):
                            out.append((sid, pid, cid, mid, rid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: handiwork, commodity, map, magic, problem solving, rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--commodity", choices=COMMODITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--parent", choices=PARENT_KINDS)
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
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.commodity is None or c[2] == args.commodity)
        and (args.magic is None or c[3] == args.magic)
        and (args.rhyme is None or c[4] == args.rhyme)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, commodity, magic, rhyme = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_KINDS)
    return StoryParams(place=place, commodity=commodity, problem=problem, magic=magic, rhyme=rhyme, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={ {k: v for k, v in e.meters.items() if v} } memes={ {k: v for k, v in e.memes.items() if v} }"
        )
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for s in stories:
            print("  ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, problem, commodity, magic, rhyme in valid_combos():
            params = StoryParams(
                place=place,
                commodity=commodity,
                problem=problem,
                magic=magic,
                rhyme=rhyme,
                name=NAMES[0],
                gender="girl",
                parent="mother",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
