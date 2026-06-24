#!/usr/bin/env python3
"""
Storyworld: campground mystery with teamwork, a crook, and an odometer.

A small, self-contained TinyStories-style simulation:
- Setting: campground
- Style: Mystery
- Feature: Teamwork
- Seed words: crook, odometer

A child-facing story is generated from world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the campground"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_by: str
    recovered_by_team: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTING = Setting(place="the campground")

CHARACTER_TYPES = {
    "girl": ["Maya", "Lena", "Nora", "Ivy", "Zoe"],
    "boy": ["Theo", "Finn", "Noah", "Eli", "Max"],
}

CROOK_NAMES = ["Crook", "Sneak", "Milo", "Pip"]

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        use="shine under the benches",
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a little magnifying glass",
        use="look at tiny marks",
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a short rope",
        use="tie a simple search line",
    ),
}

CLUES = {
    "odometer": Clue(
        id="odometer",
        label="odometer",
        phrase="the little odometer from the bike cart",
        hidden_by="mud",
    ),
    "wheelprint": Clue(
        id="wheelprint",
        label="wheel print",
        phrase="a round wheel print in the dirt",
        hidden_by="leaves",
    ),
    "crook_note": Clue(
        id="crook_note",
        label="note",
        phrase="a folded note with a crooked arrow",
        hidden_by="a rock",
    ),
}

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "campground"
    clue: str = "odometer"
    tool: str = "magnifier"
    hero_name: str = "Maya"
    hero_gender: str = "girl"
    helper_name: str = "Theo"
    helper_gender: str = "boy"
    crook_name: str = "Crook"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for clue_id in CLUES:
        for tool_id in TOOLS:
            out.append((SETTING.place, clue_id, tool_id))
    return out


def explain_invalid(clue_id: str, tool_id: str) -> str:
    clue = CLUES[clue_id]
    tool = TOOLS[tool_id]
    return (
        f"(No story: {tool.label} does not help find {clue.label} in a clear way. "
        f"Try the magnifying glass for tiny clues, the flashlight for dark spots, "
        f"or the rope for a search line.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Clue, Tool) :- place(Place), clue(Clue), tool(Tool).

useful(Tool, Clue) :- tool(Tool), clue(Clue), pair(Tool, Clue).
valid_story(Place, Clue, Tool) :- valid(Place, Clue, Tool), useful(Tool, Clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", SETTING.place))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("pair", "magnifier", "odometer"))
    lines.append(asp.fact("pair", "flashlight", "wheelprint"))
    lines.append(asp.fact("pair", "rope", "crook_note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _add_meme(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _add_meter(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def describe_setting() -> str:
    return "The campground was quiet, with tents, pine trees, and a dusty path between the sites."


def predict_clue(world: World, clue: Clue, tool: Tool) -> bool:
    return {
        ("magnifier", "odometer"): True,
        ("flashlight", "wheelprint"): True,
        ("rope", "crook_note"): True,
    }.get((tool.id, clue.id), False)


def solve_mystery(world: World, hero: Entity, helper: Entity, crook: Entity, clue: Clue, tool: Tool) -> None:
    _add_meme(hero, "curiosity", 1)
    _add_meme(helper, "helpfulness", 1)
    _add_meme(helper, "teamwork", 1)
    _add_meme(hero, "teamwork", 1)
    world.say(
        f"{hero.id} noticed that something small was missing from a camp wagon: {clue.phrase}."
    )
    world.say(
        f"{hero.id} and {helper.id} decided to work as a team. They used {tool.phrase} to {tool.use}."
    )
    if clue.id == "odometer":
        world.say(
            f"The tiny marks on the wagon wheel led them to a muddy patch near a tree stump."
        )
    elif clue.id == "wheelprint":
        world.say(
            f"The round print in the dirt pointed them toward a blanket pile by the campfire."
        )
    else:
        world.say(
            f"The crooked arrow on the note sent them to the quiet tent at the edge of the path."
        )

    _add_meter(crook, "worry", 1)
    _add_meter(hero, "confidence", 1)
    _add_meter(helper, "confidence", 1)
    clue.recovered_by_team = True
    world.say(
        f"Behind a stack of firewood, they found {crook.id}, who had taken the clue and tried to hide it."
    )
    _add_meme(crook, "caught", 1)
    _add_meme(crook, "embarrassed", 1)
    world.say(
        f"{hero.id} asked a gentle question, and {crook.id} gave the clue back without a fuss."
    )
    world.say(
        f"In the end, the team solved the mystery together, and the campground felt calm again."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender))
    crook = world.add(Entity(id=params.crook_name, kind="character", type="person"))
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]

    world.facts.update(hero=hero, helper=helper, crook=crook, clue=clue, tool=tool, params=params)

    world.say(describe_setting())
    world.say(
        f"{hero.id} and {helper.id} were exploring the campground when they noticed a strange empty spot."
    )
    world.say(
        f"Something important was gone, and even the crook's tracks seemed to point toward a secret."
    )
    world.para()
    if not predict_clue(world, clue, tool):
        raise StoryError(explain_invalid(clue.id, tool.id))
    solve_mystery(world, hero, helper, crook, clue, tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    tool: Tool = f["tool"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short mystery story for a young child set at a campground with teamwork, a crook, and an {clue.label}.',
        f"Tell a gentle campground mystery where {hero.id} and {helper.id} use {tool.label} to solve what the crook hid.",
        f'Write a simple story that includes the word "{clue.label}" and ends with friends solving the mystery together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    crook: Entity = f["crook"]
    clue: Clue = f["clue"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at the campground, where {hero.id} and {helper.id} were exploring together.",
        ),
        QAItem(
            question=f"What clue went missing in the story?",
            answer=f"The missing clue was {clue.phrase}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the mystery?",
            answer=f"They worked as a team and used {tool.phrase} to follow the trail and find the crook.",
        ),
        QAItem(
            question=f"Who had taken the clue?",
            answer=f"{crook.id} had taken it and tried to hide it, but the team found the clue and got it back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people can stay in tents or campers and spend time outdoors.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the job so they can solve a problem together.",
        ),
        QAItem(
            question="What is an odometer?",
            answer="An odometer is a small device that shows how far something has traveled.",
        ),
        QAItem(
            question="What does a magnifying glass help you do?",
            answer="A magnifying glass helps you look closely at small details.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    clue: Clue = world.facts["clue"]
    lines.append(f"  clue recovered: {clue.recovered_by_team}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground mystery storyworld with teamwork.")
    ap.add_argument("--place", choices=["campground"], default="campground")
    ap.add_argument("--clue", choices=sorted(CLUES), default=None)
    ap.add_argument("--tool", choices=sorted(TOOLS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--crook")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-gender", choices=["girl", "boy"], default=None)
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
    clue = args.clue or rng.choice(sorted(CLUES))
    tool = args.tool or {
        "odometer": "magnifier",
        "wheelprint": "flashlight",
        "crook_note": "rope",
    }[clue]
    if args.clue and args.tool and not predict_clue(World(SETTING), CLUES[clue], TOOLS[tool]):
        raise StoryError(explain_invalid(clue, tool))

    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    hero_name = args.name or rng.choice(CHARACTER_TYPES[gender])
    helper_name = args.helper or rng.choice(CHARACTER_TYPES[helper_gender])
    crook_name = args.crook or rng.choice(CROOK_NAMES)

    return StoryParams(
        place="campground",
        clue=clue,
        tool=tool,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        crook_name=crook_name,
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


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos_py() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories_py() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_py() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos_py())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_py())
    if args.asp:
        triples = asp_valid_combos_py()
        stories = asp_valid_stories_py()
        print(f"{len(triples)} compatible (place, clue, tool) combos ({len(stories)} with valid_story):\n")
        for place, clue, tool in triples:
            print(f"  {place:12} {clue:10} {tool:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="campground", clue="odometer", tool="magnifier", hero_name="Maya", hero_gender="girl", helper_name="Theo", helper_gender="boy", crook_name="Crook"),
            StoryParams(place="campground", clue="wheelprint", tool="flashlight", hero_name="Nora", hero_gender="girl", helper_name="Finn", helper_gender="boy", crook_name="Sneak"),
            StoryParams(place="campground", clue="crook_note", tool="rope", hero_name="Eli", hero_gender="boy", helper_name="Ivy", helper_gender="girl", crook_name="Pip"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
