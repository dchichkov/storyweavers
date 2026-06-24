#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
===================================================================

A standalone story world for a small ghost-story-style mystery:
a curious child hears a spooky buzz in a soggy house, follows clues,
and learns that the "ghost" is only a wasp and a leaking old shotgun case
making odd sounds in the wet walls.

The world is intentionally child-facing: eerie atmosphere, but a safe solve.
Physical state is tracked with meters and emotional state with memes.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "buzz": 0.0, "rust": 0.0, "mystery": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "relief": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dim: str
    floor: str
    smell: str
    sound: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    eerie_line: str
    solve_line: str
    reveal_line: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    kind: str
    safe: bool = True
    wettable: bool = False
    buzzable: bool = False
    lockable: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["mystery"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    out.append("__reveal__")
    return out


def _r_wet_buzz(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("shotgun_case")
    wasp = world.get("wasp")
    if case.meters["wet"] < THRESHOLD or wasp.meters["buzz"] < THRESHOLD:
        return out
    sig = ("wet_buzz",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("house").meters["mystery"] += 1
    world.get("child").memes["fear"] += 1
    out.append("The house still felt haunted.")
    return out


CAUSAL_RULES = [(_r_wet_buzz), (_r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__reveal__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, mystery: Mystery, child_name: str, parent_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label=parent_name))
    house = world.add(Entity(id="house", kind="place", type="house", label=setting.place))
    wasp = world.add(Entity(id="wasp", kind="thing", type="wasp", label="wasp", kind="animal"))
    shotgun = world.add(Entity(id="shotgun_case", kind="thing", type="object", label="shotgun"))
    puddle = world.add(Entity(id="puddle", kind="thing", type="water", label="soggy puddle"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="light", label="lantern"))
    for e in (child, parent, house, wasp, shotgun, puddle, lantern):
        e.meters["wet"] = 0.0
        e.meters["buzz"] = 0.0
        e.meters["rust"] = 0.0
        e.meters["mystery"] = 0.0
        e.memes["curiosity"] = 0.0
        e.memes["fear"] = 0.0
        e.memes["relief"] = 0.0
        e.memes["bravery"] = 0.0

    child.memes["curiosity"] += 2
    child.meters["mystery"] += 1
    wasp.meters["buzz"] += 1
    shotgun.meters["rust"] += 1
    shotgun.meters["wet"] += 1
    house.meters["mystery"] += 1
    puddle.meters["wet"] += 1

    world.say(
        f"{child_name} lived in {setting.place}, where the air smelled {setting.smell} "
        f"and the floor went {setting.floor} after the rain."
    )
    world.say(
        f"At night, {child_name} heard a tiny buzz from a soggy corner and saw a shadow "
        f"near an old shotgun case."
    )
    world.para()
    world.say(
        f"{child_name} tiptoed closer, because {child_name} was full of curiosity and "
        f"wanted to solve the mystery."
    )
    world.say(
        f"The wasp kept humming above the soggy puddle, and the wet shotgun case made a "
        f"soft clack-clack sound when the house floor shifted."
    )

    world.para()
    world.say(
        f"{parent_name} came with a lantern and said, \"Let's look carefully.\""
    )
    world.say(
        f"They noticed that the wasp had nested near a leaky window, and rainwater had "
        f"made the shotgun case damp and creaky."
    )
    child.meters["mystery"] += 1
    propagate(world, narrate=True)

    world.para()
    child.memes["bravery"] += 1
    world.say(
        f"{child_name} stayed calm, helped guide the wasp out the open door, and let "
        f"{parent_name} dry the shotgun case by the stove."
    )
    world.say(
        f"By morning, the house felt quiet again, and the scary little mystery had become "
        f"a simple answer."
    )
    world.say(
        f"It was not a ghost at all. It was only a wasp, a soggy floor, and a wet old "
        f"shotgun case making strange house sounds."
    )
    child.meters["mystery"] = 0.0
    child.memes["relief"] += 2
    parent.memes["relief"] += 1
    world.facts.update(
        child=child,
        parent=parent,
        house=house,
        wasp=wasp,
        shotgun=shotgun,
        puddle=puddle,
        lantern=lantern,
        mystery=mystery,
        setting=setting,
        solved=True,
    )
    return world


SETTINGS = {
    "old_house": Setting(
        place="the old house",
        dim="dim",
        floor="squishy",
        smell="of rain and dust",
        sound="drippy",
        affords={"mystery"},
    ),
    "boathouse": Setting(
        place="the boathouse",
        dim="shadowy",
        floor="wet",
        smell="of salt and moss",
        sound="creaky",
        affords={"mystery"},
    ),
    "farmhouse": Setting(
        place="the farmhouse",
        dim="soft",
        floor="soggy",
        smell="of hay and rain",
        sound="hush-hush",
        affords={"mystery"},
    ),
}

MYSTERIES = {
    "wasp_case": Mystery(
        id="wasp_case",
        clue="a tiny buzz in a soggy room",
        eerie_line="It sounded like a ghost whispering through the walls.",
        solve_line="The child followed the buzzing and the wet clack of the case.",
        reveal_line="A wasp had hidden near the window, and rain had made the old case rattle.",
        cause="a wasp nest by a leaky window and a wet shotgun case",
        tags={"wasp", "soggy", "shotgun"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    child_name: str
    parent_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery with curiosity and a safe solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    names = ["Mina", "Lena", "Ruby", "Nina", "Iris", "Tess"]
    parents = ["Mom", "Mum", "Mother"]
    return StoryParams(
        setting=setting,
        mystery=mystery,
        child_name=args.name or rng.choice(names),
        parent_name=args.parent or rng.choice(parents),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.child_name, params.parent_name)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f'Write a ghost-story-style mystery for a young child about "{mystery.clue}" that gets solved with curiosity.',
        f"Tell a spooky but safe story where {child.label} follows a buzz, finds a wasp, and learns why a soggy shotgun case made the house sound haunted.",
        f'Write a gentle mystery story that includes the words "soggy", "wasp", and "shotgun" and ends with a clear, comforting answer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Why did {child.label} go looking around the old place?",
            answer=f"{child.label} was curious and wanted to solve the mystery of the strange buzz in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was making the spooky sound near the soggy floor?",
            answer="It was a wasp buzzing near a leaky window, while the wet shotgun case made soft clacking sounds.",
        ),
        QAItem(
            question=f"What did {parent.label} bring to help?",
            answer=f"{parent.label} brought a lantern so they could look carefully and safely in the dark.",
        ),
        QAItem(
            question=f"What was the mystery's answer?",
            answer=f"The answer was that a wasp, rainwater, and a soggy shotgun case made the house sound haunted.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{child.label} felt brave and relieved after the mystery was solved and the house felt quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soggy mean?",
            answer="Soggy means very wet and soft, like something soaked by rain.",
        ),
        QAItem(
            question="What is a wasp?",
            answer="A wasp is a flying insect that can buzz loudly and build a nest.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask questions, and learn what is going on.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} {e.type:10} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% Minimal twin: the mystery is considered solvable when curiosity is present
% and the world contains the wet-buzz clue.
solvable :- curious(C), C >= 1, clue(wet_buzz).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("curious", 1), asp.fact("clue", "wet_buzz")]
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/0."))
    ok = any(sym.name == "solvable" for sym in model)
    if ok:
        print("OK: ASP twin says the mystery is solvable.")
        return 0
    print("MISMATCH: ASP twin did not find solvable.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {section} ==")
            if section == "Prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="old_house", mystery="wasp_case", child_name="Mina", parent_name="Mom"),
    StoryParams(setting="boathouse", mystery="wasp_case", child_name="Iris", parent_name="Mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show solvable/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
