#!/usr/bin/env python3
"""
A standalone storyworld script for a small space-adventure mystery.

Premise:
A young crew member on a tiny orbital station notices a puzzling problem:
important tools keep disappearing from the cargo bay. The child wants to solve
the mystery right away, but the station's captain insists on careful thinking.
The world model tracks clues, locations, and feelings so the story can turn from
worry to discovery.

The story uses two story-beat words from the seed:
- compulsive
- insinuate

The style stays close to a child-friendly space adventure, with a clear mystery
to solve, a careful investigation, and a resolution image showing what changed.
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
    location: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str = "the little orbital station"
    orbit: str = "above a blue planet"
    places: tuple[str, ...] = ("cargo bay", "observation dome", "maintenance hall", "sleep pod row")


@dataclass
class Clue:
    id: str
    label: str
    place: str
    obvious: bool = False


@dataclass
class Mystery:
    id: str
    problem: str
    culprit: str
    solution: str
    clue_chain: tuple[str, ...]


@dataclass
class StoryParams:
    name: str
    gender: str
    role: str
    captain: str
    setting: str = "station"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _character_names(gender: str) -> list[str]:
    return {
        "girl": ["Nia", "Luna", "Mira", "Zuri", "Ari", "Tess"],
        "boy": ["Owen", "Finn", "Noel", "Kai", "Jett", "Rafi"],
    }.get(gender, ["Nova", "Sky", "Pip", "Echo"])


SETTINGS = {
    "station": Setting(),
}

MYSTERIES = {
    "missing-tool": Mystery(
        id="missing-tool",
        problem="small repair tools keep disappearing from the cargo bay",
        culprit="a curious maintenance drone",
        solution="the drone was nesting the tools in a vent",
        clue_chain=("scratches", "beep", "vent"),
    )
}

CLUES = {
    "scratches": Clue("scratches", "tiny scratch marks", "cargo bay"),
    "beep": Clue("beep", "a soft beep", "maintenance hall"),
    "vent": Clue("vent", "an open vent panel", "cargo bay", obvious=True),
}

GEAR = {
    "flashlight": Entity(id="flashlight", type="tool", label="flashlight", phrase="a small flashlight"),
    "scanner": Entity(id="scanner", type="tool", label="scanner", phrase="a pocket scanner"),
}


def reasonableness_gate(params: StoryParams) -> None:
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The hero gender must be girl or boy for this storyworld.")
    if params.setting != "station":
        raise StoryError("This storyworld only supports the orbital station setting.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain))
    mystery = MYSTERIES["missing-tool"]
    world.facts.update(hero=hero, captain=captain, mystery=mystery)
    return world


def introduce(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"{hero.id} was a little crew member aboard {world.setting.name}, drifting quietly {world.setting.orbit}."
    )
    world.say(
        f"{hero.id} liked the hum of the engines, the silver walls, and the way {captain.label} kept the station steady."
    )


def mystery_starts(world: World, hero: Entity) -> None:
    world.say(
        f"Then a mystery appeared: {MYSTERIES['missing-tool'].problem}."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} felt a compulsive need to solve it at once, as if the question itself were tugging at {hero.id}'s sleeve."
    )


def captain_warns(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    world.say(
        f"{captain.label} did not rush. \"Do not leap to guesses,\" {captain.pronoun()} said. \"A mystery can try to insinuate the wrong answer if you stare too fast.\""
    )
    world.say(
        f"{hero.id} nodded, though {hero.pronoun('possessive')} feet still wanted to run down the hallway."
    )


def investigate(world: World, hero: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} started in the cargo bay and found {CLUES['scratches'].label} near the tool shelf."
    )
    world.say(
        f"That made {hero.id} look toward the maintenance hall, where {CLUES['beep'].label} echoed behind a panel."
    )
    world.say(
        f"At last {hero.id} spotted {CLUES['vent'].label}, and the missing tools suddenly made sense."
    )
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1
    hero.memes["worry"] = 0.0


def reveal(world: World, hero: Entity) -> None:
    world.para()
    mystery = MYSTERIES["missing-tool"]
    world.say(
        f"The mystery was solved: {mystery.solution}."
    )
    world.say(
        f"{hero.id} opened the vent and found the tools stacked neatly inside, like the station had been hiding a tiny secret drawer."
    )
    world.say(
        f"{hero.id} laughed, because the answer was simple after all the looking."
    )


def resolution(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"{captain.label} smiled and said, \"That was careful work.\""
    )
    world.say(
        f"By the end, {hero.id} was carrying the tools back to the cargo bay, and the station felt calm again, bright with solved-mystery relief."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    captain.memes["relief"] = captain.memes.get("relief", 0.0) + 1


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = build_world(params)
    hero = world.get(params.name)
    captain = world.get("captain")
    introduce(world, hero, captain)
    mystery_starts(world, hero)
    captain_warns(world, captain, hero)
    investigate(world, hero)
    reveal(world, hero)
    resolution(world, hero, captain)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    captain = world.facts["captain"]
    return [
        "Write a child-friendly space adventure about a small mystery on an orbital station.",
        f"Tell a story where {hero.id} feels compulsive about solving a problem, but {captain.label} asks for careful clues first.",
        f"Make the story include the word 'insinuate' and end with {mystery.solution}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to search the station right away?",
            answer=f"{hero.id} felt a compulsive need to solve the mystery as soon as {hero.id} heard that the tools were missing.",
        ),
        QAItem(
            question=f"What did {captain.label} warn {hero.id} not to do?",
            answer=f"{captain.label} warned {hero.id} not to leap to guesses, because a mystery can insinuate the wrong answer if you stare too fast.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"It was solved when the missing tools were found in the vent, which matched the clue chain and showed that {mystery.solution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem or question that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="What does a flashlight help you do in the dark?",
            answer="A flashlight helps you see where you are going and notice small things that might be hidden.",
        ),
        QAItem(
            question="Why do people check clues one by one?",
            answer="People check clues one by one so they can find the real answer instead of guessing too quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "station"),
        asp.fact("mystery", "missing-tool"),
    ]
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("at_place", cid, clue.place))
        if clue.obvious:
            lines.append(asp.fact("obvious", cid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("problem", mid))
        for clue in m.clue_chain:
            lines.append(asp.fact("needs_clue", mid, clue))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable if all required clues are present.
solved(M) :- mystery(M), problem(M), not missing_required(M).
missing_required(M) :- needs_clue(M, C), not clue(C).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    solved = set(asp.atoms(model, "solved"))
    expected = {("missing-tool",)}
    if solved == expected:
        print("OK: ASP and Python mystery-resolution logic agree.")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("  ASP:", sorted(solved))
    print("  expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure mystery storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_character_names(gender))
    captain = args.captain or rng.choice(["Captain Rhea", "Captain Sol", "Captain Mira"])
    return StoryParams(name=name, gender=gender, role="crew member", captain=captain, seed=args.seed)


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


CURATED = [
    StoryParams(name="Nia", gender="girl", role="crew member", captain="Captain Rhea"),
    StoryParams(name="Kai", gender="boy", role="crew member", captain="Captain Sol"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print("Solved mysteries:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

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
