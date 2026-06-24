#!/usr/bin/env python3
"""
A small detective-story world about a taco, a fellow-ship, and a shadow.

Premise:
- A child detective and a loyal fellow-sleuth try to solve a tiny mystery.
- A taco goes missing or looks strange because a shadow makes the scene look
  suspicious.
- The investigation reveals a harmless cause, and the ending is happy.
- The lesson learned is that shadows can trick your eyes, so it's wise to look
  closely before blaming someone.

This world is intentionally tiny and classical: it simulates a few entities,
their physical state in meters, and their emotional state in memes, then turns
that state into a complete child-facing detective story.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "detective_boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    source: str
    truth: str
    mistaken_for: str


@dataclass
class Mystery:
    id: str
    prompt: str
    false_lead: str
    real_cause: str
    solved_by: str
    lesson: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "alley": Setting(place="the little alley behind the taco shop"),
    "market": Setting(place="the busy market street"),
    "kitchen": Setting(place="the sunny kitchen", indoors=True),
}

CHARACTER_TYPES = {
    "detective_boy": "boy",
    "detective_girl": "girl",
    "fellow_boy": "boy",
    "fellow_girl": "girl",
}

NAMES_BOY = ["Milo", "Theo", "Finn", "Noah", "Eli"]
NAMES_GIRL = ["Maya", "Nora", "Ivy", "Luna", "Zoe"]
TRAITS = ["careful", "curious", "brave", "kind", "sharp-eyed"]

MYSTERIES = {
    "shadow_taco": Mystery(
        id="shadow_taco",
        prompt="Why did the taco look like it had vanished?",
        false_lead="a sneaky thief",
        real_cause="a shadow from a tall sign",
        solved_by="looking from the other side of the cart",
        lesson="shadows can make an ordinary thing look mysterious",
    ),
    "stained_taco": Mystery(
        id="stained_taco",
        prompt="Why did the taco shell seem dark and strange?",
        false_lead="burnt food",
        real_cause="a cool shadow from a hanging lantern",
        solved_by="checking the light near the table",
        lesson="you should check the light before jumping to a guess",
    ),
}

CLUES = {
    "shadow": Clue(
        id="shadow",
        label="shadow",
        phrase="a long shadow on the ground",
        kind="shadow",
        source="sign",
        truth="harmless shadow",
        mistaken_for="a clue about a thief",
    ),
    "taco": Clue(
        id="taco",
        label="taco",
        phrase="a warm taco with a folded shell",
        kind="food",
        source="cart",
        truth="the missing-looking taco",
        mistaken_for="something stolen",
    ),
    "lamp": Clue(
        id="lamp",
        label="lamp",
        phrase="a bright lamp above the table",
        kind="light",
        source="table",
        truth="good light for solving puzzles",
        mistaken_for="nothing suspicious",
    ),
}

SCENES = {
    "shadowy_corner": "where the light was uneven and the shadows looked extra long",
    "bright_table": "where the lamp made the whole table easy to inspect",
}


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is suspicious if there is a taco and a shadow in the same scene.
suspicious(M) :- mystery(M), clue(taco), clue(shadow).

% The real cause is safe when it is a shadow from a known object.
safe_cause(M) :- mystery(M), clue(shadow), clue(lamp).

% A story is solvable if there is a clue that explains the false lead.
solvable(M) :- mystery(M), safe_cause(M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show solvable/1. #show suspicious/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "solvable"))
    if ("shadow_taco",) in atoms or ("stained_taco",) in atoms:
        print("OK: ASP rules produce solvable mystery atoms.")
        return 0
    print("MISMATCH: ASP rules did not produce expected solution atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    fellow_name: str
    fellow_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: taco, fellow-ship, shadow, happy ending, lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--fellow-name")
    ap.add_argument("--fellow-gender", choices=["boy", "girl"])
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


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES_BOY if gender == "boy" else NAMES_GIRL)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    hero_type = args.gender or rng.choice(["boy", "girl"])
    hero_name = args.name or choose_name(hero_type, rng)
    fellow_type = args.fellow_gender or ("girl" if hero_type == "boy" else "boy")
    fellow_name = args.fellow_name or choose_name(fellow_type, rng)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        fellow_name=fellow_name,
        fellow_type=fellow_type,
        trait=trait,
    )


def explain_rejection() -> str:
    return "(No story: the requested combination does not form a clear, child-friendly detective mystery.)"


# ---------------------------------------------------------------------------
# Simulation and narration
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    mystery = MYSTERIES[params.mystery]

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=f"detective_{params.hero_type}",
        label=params.hero_name,
        traits=["little", params.trait, "detective"],
        meters={"attention": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    fellow = world.add(Entity(
        id="fellow",
        kind="character",
        type=f"fellow_{params.fellow_type}",
        label=params.fellow_name,
        traits=["loyal", "helpful", "fellow-ship"],
        meters={"attention": 0.0},
        memes={"curiosity": 0.5, "worry": 0.0, "joy": 0.0},
    ))
    taco = world.add(Entity(
        id="taco",
        kind="thing",
        type="taco",
        label="taco",
        phrase="a warm taco with a folded shell",
        owner="cart",
        meters={"visible": 1.0, "shadowed": 0.0},
        memes={"mystery": 0.0},
    ))
    shadow = world.add(Entity(
        id="shadow",
        kind="thing",
        type="shadow",
        label="shadow",
        phrase="a long shadow",
        meters={"visible": 1.0, "length": 1.0},
        memes={"suspicion": 1.0},
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="lamp",
        phrase="a bright lamp",
        meters={"brightness": 1.0},
        memes={"helpful": 1.0},
    ))

    world.facts.update(
        detective=detective,
        fellow=fellow,
        taco=taco,
        shadow=shadow,
        lamp=lamp,
        mystery=mystery,
        setting=world.setting,
    )
    return world


def solve_mystery(world: World) -> None:
    detective = world.facts["detective"]
    fellow = world.facts["fellow"]
    taco = world.facts["taco"]
    shadow = world.facts["shadow"]
    lamp = world.facts["lamp"]
    mystery: Mystery = world.facts["mystery"]

    detective.memes["curiosity"] += 1
    fellow.memes["curiosity"] += 1

    world.say(f"One evening, {detective.label} the little detective and {fellow.label}, their loyal fellow-ship partner, walked into {world.setting.place}.")
    world.say(f"They were looking into a tiny mystery: {mystery.prompt}")

    world.para()
    scene = "shadowy_corner"
    world.say(f"At first, the taco seemed to be gone in {SCENES[scene]}.")
    world.say(f"{shadow.label.capitalize()} stretched across the ground, and it made the taco look suspiciously empty.")
    detective.meters["attention"] += 1
    fellow.meters["attention"] += 1
    detective.memes["worry"] += 1

    world.para()
    world.say(f"{detective.label} said it might be {mystery.false_lead}, but {fellow.label} shook {fellow.pronoun('possessive')} head and asked for one more look.")
    world.say(f"They followed the clue carefully, because a good detective does not blame the first thing that looks strange.")
    taco.meters["shadowed"] = 1.0
    shadow.memes["suspicion"] = 1.0

    world.para()
    world.say(f"Then they moved to the {SCENES['bright_table']}.")
    lamp.meters["brightness"] = 2.0
    taco.meters["visible"] = 2.0
    taco.meters["shadowed"] = 0.0
    shadow.memes["suspicion"] = 0.0
    world.say(f"There was the taco all along, safe and warm near the lamp.")
    world.say(f"It was only a shadow from a tall sign that had fooled everyone for a moment.")

    world.para()
    detective.memes["worry"] = 0.0
    detective.memes["joy"] = 1.0
    fellow.memes["joy"] = 1.0
    world.say(f"{detective.label} laughed with relief, and {fellow.label} laughed too.")
    world.say(f"They shared the taco, and the happy ending felt even sweeter because the mystery was solved kindly.")
    world.say(f"The lesson learned was simple: {mystery.lesson}.")
    world.say(f"From then on, the two friends checked the light before making a guess, and their fellow-ship stayed strong.")

    world.facts["solved"] = True
    world.facts["lesson"] = mystery.lesson
    world.facts["scene"] = scene


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    detective: Entity = world.facts["detective"]
    fellow: Entity = world.facts["fellow"]
    return [
        f"Write a short detective story about {detective.label}, {fellow.label}, a taco, and a shadow.",
        f"Tell a child-friendly mystery where a fellow-ship of two friends solves {mystery.prompt.lower()}",
        f"Write a story with a happy ending and a lesson learned about checking shadows before guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    fellow: Entity = world.facts["fellow"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who solved the mystery with the taco and shadow?",
            answer=f"{detective.label} and {fellow.label} solved it together as a loyal fellow-ship.",
        ),
        QAItem(
            question=f"What made the taco look strange at first?",
            answer=f"A long shadow from a tall sign made the taco look missing for a moment.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that {mystery.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shadow?",
            answer="A shadow is a dark shape that appears when something blocks light.",
        ),
        QAItem(
            question="What is a taco?",
            answer="A taco is a folded food with filling inside a shell or tortilla.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show solvable/1. #show suspicious/1."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_valid_check() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show suspicious/1."))
    return sorted(set(asp.atoms(model, "suspicious")))


# ---------------------------------------------------------------------------
# Main generation API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    solve_mystery(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(setting="alley", mystery="shadow_taco", hero_name="Milo", hero_type="boy",
                    fellow_name="Maya", fellow_type="girl", trait="curious"),
        StoryParams(setting="market", mystery="stained_taco", hero_name="Nora", hero_type="girl",
                    fellow_name="Theo", fellow_type="boy", trait="sharp-eyed"),
    ]


def asp_verify_message() -> int:
    combos = set(asp_valid_stories())
    if ("shadow_taco",) in combos or ("stained_taco",) in combos:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH: ASP parity check failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/1. #show suspicious/1."))
        return
    if args.verify:
        sys.exit(asp_verify_message())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show suspicious/1. #show solvable/1."))
        print("suspicious:", sorted(set(asp.atoms(model, "suspicious"))))
        print("solvable:", sorted(set(asp.atoms(model, "solvable"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in curated():
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
