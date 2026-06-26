#!/usr/bin/env python3
"""
Standalone storyworld: a pirate-tale mystery in a community garden.

Premise:
A small garden crew keeps noticing a puzzling drip, a worried committee,
and a shiny jar labeled "reflux". The crew must solve what is happening,
work through repeated checks, and find the real cause in the garden.

The world is built as a tiny simulation with physical meters and emotional
memes, a Python reasonableness gate, and an inline ASP twin.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the community garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    repeat_clue: str
    turn: str
    answer: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    solves: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.clues_seen = list(self.clues_seen)
        return c


@dataclass
class StoryParams:
    mystery: str
    tool: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the community garden", indoors=False, affords={"search", "inspect", "repeat"}),
}

MYSTERIES = {
    "reflux": Mystery(
        id="reflux",
        clue="a shiny drip near the bean trellis",
        repeat_clue="the same shiny drip turned up again by the tomatoes",
        turn="the drip was only garden water sliding off a tilted bottle cap",
        answer="a leaky bottle cap",
        risk="the seedlings might get soggy",
        tags={"reflux", "mystery", "repeat"},
    ),
    "committee": Mystery(
        id="committee",
        clue="a worried committee whispering by the compost bin",
        repeat_clue="the committee asked the same question twice",
        turn="the committee was not arguing at all; they were counting seed packets",
        answer="a seed-counting meeting",
        risk="the garden plan might get mixed up",
        tags={"committee", "mystery", "repeat"},
    ),
    "melanin": Mystery(
        id="melanin",
        clue="a dark stain on a hand-painted sign",
        repeat_clue="the same dark mark showed up on the second signboard",
        turn="the mark came from berry juice and soil, not from trouble",
        answer="berry stain and soil",
        risk="the welcome sign might look ruined",
        tags={"melanin", "mystery", "repeat"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        covers={"light"},
        solves={"mystery"},
        prep="lift the lantern high and look again",
        tail="held the lantern steady",
    ),
    "notebook": Tool(
        id="notebook",
        label="a captain's notebook",
        covers={"record"},
        solves={"repeat"},
        prep="mark each clue in the notebook",
        tail="kept the notebook open",
    ),
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        covers={"hands"},
        solves={"stain"},
        prep="wipe the sign with a clean cloth",
        tail="folded the cloth away",
    ),
}

NAMES = ["Mira", "Toby", "Elio", "Nia", "Penny", "Jasper"]
TRAITS = ["brave", "curious", "cheerful", "stubborn", "steady"]
CAPTAINS = ["captain", "aunt", "uncle", "keeper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mystery_id, myst in MYSTERIES.items():
            for tool_id, tool in TOOLS.items():
                if mystery_id == "reflux" and tool_id != "lantern":
                    continue
                if mystery_id == "committee" and tool_id != "notebook":
                    continue
                if mystery_id == "melanin" and tool_id != "cloth":
                    continue
                combos.append((place, mystery_id, tool_id))
    return combos


def prize_at_risk(mystery: Mystery, tool: Tool) -> bool:
    return True


def select_tool(mystery: Mystery) -> Optional[Tool]:
    if mystery.id == "reflux":
        return TOOLS["lantern"]
    if mystery.id == "committee":
        return TOOLS["notebook"]
    if mystery.id == "melanin":
        return TOOLS["cloth"]
    return None


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return f"(No story: {tool.label} does not honestly help with {mystery.id} in the community garden.)"


def tell(setting: Setting, mystery: Mystery, tool_def: Tool, hero_name: str, hero_type: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="the captain"))
    clue = world.add(Entity(id="Clue", type="thing", label=mystery.id, phrase=mystery.clue))
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, phrase=tool_def.label, owner=hero.id))
    tool.worn_by = hero.id

    world.say(f"In the community garden, {hero.id} was a little {hero_type} with a pirate's grin.")
    world.say(f"{hero.pronoun().capitalize()} and {captain.label} kept watch over the beds, where {mystery.clue} kept appearing.")
    world.say(f"{hero.id} liked the mystery, but {captain.pronoun('possessive')} brow grew tight, for {mystery.risk}.")
    world.para()

    world.say(f"‘Arrr, let us search again,’ said {hero.id}, and {hero.pronoun()} lifted {tool.label}.")
    world.say(f"They {tool_def.prep}, and the same clue showed up once more: {mystery.repeat_clue}.")
    world.clues_seen.append(mystery.clue)
    world.clues_seen.append(mystery.repeat_clue)
    world.say(f"{captain.label} nodded. ‘A repeated clue is a good clue, matey. It means the answer has a pattern.’")
    world.para()

    world.say(f"So they checked the bed edges, the seed tray, and the old bucket again and again.")
    world.say(f"At last, the turn came clear: {mystery.turn}.")
    world.say(f"{hero.id} laughed, because the answer was plain now: {mystery.answer}.")
    world.say(f"{captain.label} smiled as the garden settled, and the last drip was only water shining in the sun.")

    world.facts.update(hero=hero, captain=captain, mystery=mystery, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    hero = world.facts["hero"]
    return [
        f'Write a pirate-tale mystery for a child in a community garden, using the word "{m.id}".',
        f"Tell a story where {hero.id} keeps checking the same clue again and again until the answer is clear.",
        f"Write a gentle problem-solving adventure about a committee, a repeating clue, and a garden mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was the mystery in the community garden?",
            answer=f"The mystery was about {mystery.clue}, and the crew kept checking it until they solved it.",
        ),
        QAItem(
            question=f"How did {hero.id} help solve the problem?",
            answer=f"{hero.id} used {tool.label} and kept looking again and again until the real answer became clear.",
        ),
        QAItem(
            question=f"Why did {captain.label} want the crew to be careful?",
            answer=f"{captain.label} worried that {mystery.risk}, so they needed to solve the mystery before the garden got into trouble.",
        ),
        QAItem(
            question="What was the repeated clue?",
            answer=f"The repeated clue was {mystery.repeat_clue}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a committee?",
            answer="A committee is a group of people who meet to talk, plan, and make decisions together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="Why is repetition useful when solving a problem?",
            answer="Repetition can help because seeing the same clue again and again makes patterns easier to notice.",
        ),
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared place where neighbors grow flowers, vegetables, and other plants together.",
        ),
        QAItem(
            question="What is melanin?",
            answer="Melanin is a natural pigment in living things that helps give skin, hair, and eyes their color.",
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues_seen={world.clues_seen}")
    return "\n".join(lines)


CURATED = [
    StoryParams(mystery="reflux", tool="lantern", hero_name="Mira", hero_type="girl", captain_type="captain"),
    StoryParams(mystery="committee", tool="notebook", hero_name="Toby", hero_type="boy", captain_type="keeper"),
    StoryParams(mystery="melanin", tool="cloth", hero_name="Nia", hero_type="girl", captain_type="aunt"),
]


ASP_RULES = r"""
valid_combo(Place,Mystery,Tool) :- place(Place), mystery(Mystery), tool(Tool), ok(Mystery,Tool).
ok(reflux,lantern).
ok(committee,notebook).
ok(melanin,cloth).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale mystery in a community garden.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
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
    if args.mystery and args.tool:
        m = MYSTERIES[args.mystery]
        t = TOOLS[args.tool]
        if not (args.mystery == "reflux" and args.tool == "lantern"
                or args.mystery == "committee" and args.tool == "notebook"
                or args.mystery == "melanin" and args.tool == "cloth"):
            raise StoryError(explain_rejection(m, t))
    if args.place and args.place != "garden":
        raise StoryError("(No story: this tiny world only lives in the community garden.)")
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery_id, tool_id = rng.choice(combos)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES)
    captain_type = args.captain or rng.choice(CAPTIONS)
    return StoryParams(
        mystery=mystery_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_gender,
        captain_type=captain_type,
    )


CAPTIONS = CAPTAINS


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["garden"], MYSTERIES[params.mystery], TOOLS[params.tool],
                 params.hero_name, params.hero_type, params.captain_type)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
