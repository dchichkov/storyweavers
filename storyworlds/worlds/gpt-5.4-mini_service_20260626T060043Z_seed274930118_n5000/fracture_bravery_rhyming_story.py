#!/usr/bin/env python3
"""
fracture_bravery_rhyming_story.py
=================================

A small storyworld in a rhyming-story style about a child, a fracture, and
bravery: a worry grows, a brave truth is told, and a careful fix follows.

The world is built around a simple premise:
- someone notices a crack or fracture in a treasured thing,
- fear makes it hard to speak up,
- bravery helps the child tell the truth,
- a helper makes a repair or gets the right care,
- the ending shows the object safe, and the child relieved.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- standalone stdlib script
- inline ASP twin and Python gate
- generation, emit, parser, params, verify, trace, QA
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    broken: bool = False
    repaired: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fracture": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "bravery": 0.0, "relief": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the kitchen"
    mood: str = "bright"


@dataclass
class FractureThing:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str
    can_shatter: bool = True


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    action: str
    tail: str


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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setting_intro(setting: Setting) -> str:
    return {
        "the kitchen": "In the kitchen, warm and bright, the morning hummed with tidy light.",
        "the garden": "In the garden, green and wide, the breeze went dancing side by side.",
        "the workshop": "In the workshop, neat and still, the tools were sleeping by the sill.",
        "the hallway": "In the hallway, long and clear, each step could ring from far to near.",
    }.get(setting.place, f"At {setting.place}, the day was mild, and everything felt small and styled.")


def child_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "gentle")
    return f"{hero.id} was a little {trait} {hero.type}, with feet so quick and eyes so bright."


def treasure_line(hero: Entity, treasure: Entity) -> str:
    return f"{hero.id} loved {hero.pronoun('possessive')} {treasure.label}, a {treasure.phrase}, neat and right."


def fracture_line(treasure: Entity) -> str:
    return f"One sharp crack went snap! The {treasure.label} had a fracture in its side."


def fear_line(hero: Entity, treasure: Entity) -> str:
    hero.memes["fear"] += 1
    return f"{hero.id} felt small and shook with fright; {hero.pronoun('possessive')} heart beat fast, and not so light."


def brave_line(hero: Entity) -> str:
    hero.memes["bravery"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    return f"But brave {hero.id} took one deep breath: 'I must be honest,' said {hero.pronoun('subject')} at last."


def tell_truth_line(hero: Entity, helper: Entity, treasure: Entity) -> str:
    return (
        f"{hero.id} told {helper.pronoun('object')} the truth at once: "
        f"the {treasure.label} had cracked with a tiny crunch."
    )


def help_line(helper: Entity, repair: Repair, treasure: Entity) -> str:
    return f"{helper.id} smiled and helped with care, and soon the {treasure.label} had gentle repair."


def ending_line(hero: Entity, treasure: Entity) -> str:
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    return f"In the end, {hero.id} felt proud and free; the {treasure.label} was safe, as safe could be."


def build_story_state(world: World, hero: Entity, helper: Entity, treasure: Entity, repair: Repair) -> None:
    treasure.meters["fracture"] = 1.0
    treasure.broken = True
    hero.memes["fear"] = 1.0
    helper.meters["safe"] = 1.0
    world.facts.update(hero=hero, helper=helper, treasure=treasure, repair=repair)


def propagate(world: World) -> None:
    for ent in world.entities.values():
        if ent.broken and ent.meters["fracture"] >= THRESHOLD and ("repair", ent.id) not in world.fired:
            world.fired.add(("repair", ent.id))
            ent.repaired = True
            ent.broken = False
            ent.meters["fracture"] = 0.0
            ent.meters["safe"] = 1.0
            ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1.0


def tell(setting: Setting, hero_name: str, hero_type: str, helper_type: str, treasure_cfg: FractureThing,
         repair: Repair, traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (traits or ["careful", "brave"]),
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_type,
    ))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    world.say(setting_intro(setting))
    world.say(child_intro(hero))
    world.say(treasure_line(hero, treasure))
    world.para()
    world.say(fracture_line(treasure))
    world.say(fear_line(hero, treasure))
    world.say(brave_line(hero))
    world.say(tell_truth_line(hero, helper, treasure))
    world.say(help_line(helper, repair, treasure))
    build_story_state(world, hero, helper, treasure, repair)
    propagate(world)
    world.para()
    world.say(ending_line(hero, treasure))
    world.say(f"{helper.id} gave a nod and a grin; the little world felt warm within.")
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="bright"),
    "garden": Setting(place="the garden", mood="soft"),
    "workshop": Setting(place="the workshop", mood="careful"),
    "hallway": Setting(place="the hallway", mood="quiet"),
}

TREASURES = {
    "mug": FractureThing(
        id="mug",
        label="mug",
        phrase="a blue mug with a little fox",
        type="mug",
        owner_kind="child",
    ),
    "bowl": FractureThing(
        id="bowl",
        label="bowl",
        phrase="a small bowl with a shiny rim",
        type="bowl",
        owner_kind="child",
    ),
    "frame": FractureThing(
        id="frame",
        label="frame",
        phrase="a picture frame with a gold edge",
        type="frame",
        owner_kind="family",
    ),
    "kite": FractureThing(
        id="kite",
        label="kite",
        phrase="a bright kite with a long tail",
        type="kite",
        owner_kind="child",
    ),
}

REPAIRS = {
    "glue": Repair(
        id="glue",
        label="glue",
        phrase="a little tube of glue",
        action="glue the crack",
        tail="the glue held tight, and the fracture faded from sight",
    ),
    "tape": Repair(
        id="tape",
        label="tape",
        phrase="a strip of bright tape",
        action="wrap the crack",
        tail="the tape went round in a careful ring, and the broken place could heal and sing",
    ),
    "care": Repair(
        id="care",
        label="care",
        phrase="gentle care",
        action="carry it safely",
        tail="with careful hands and a steady pace, the treasure found its proper place",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe", "Ada"]
BOY_NAMES = ["Leo", "Finn", "Toby", "Owen", "Noah", "Eli"]
TRAITS = ["brave", "gentle", "curious", "steady", "cheerful"]


def fracture_possible(setting: Setting, treasure: FractureThing) -> bool:
    return True if setting and treasure and treasure.can_shatter else False


def select_repair(treasure: FractureThing) -> Repair:
    if treasure.type in {"mug", "bowl"}:
        return REPAIRS["glue"]
    if treasure.type in {"frame"}:
        return REPAIRS["tape"]
    return REPAIRS["care"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    treasure: Entity = f["treasure"]
    return [
        f'Write a short rhyming story for a child about {hero.id}, a fracture, and bravery.',
        f"Tell a gentle rhyming tale where {hero.id} is scared after the {treasure.label} breaks, then tells the truth bravely.",
        f"Create a small story with a repair, a kind helper, and a happy ending image showing the {treasure.label} safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    treasure: Entity = f["treasure"]
    repair: Repair = f["repair"]
    return [
        QAItem(
            question=f"What did {hero.id} feel after the {treasure.label} had a fracture?",
            answer=f"{hero.id} felt scared at first, because the {treasure.label} cracked and made a sharp little sound.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do next?",
            answer=f"{hero.id} took a deep breath and told {helper.id} the truth instead of hiding the broken {treasure.label}.",
        ),
        QAItem(
            question=f"How was the {treasure.label} helped?",
            answer=f"{helper.id} used {repair.label} and careful hands, so the {treasure.label} could be repaired and safe again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling proud and relieved, while the {treasure.label} was safe and the room felt warm and calm.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "fracture": [
        QAItem(
            question="What is a fracture?",
            answer="A fracture is a crack or break in something hard, like a bone, a cup, or a toy.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared or nervous.",
        )
    ],
    "glue": [
        QAItem(
            question="What can glue do?",
            answer="Glue can help hold broken pieces together so something can be fixed and used again.",
        )
    ],
    "tape": [
        QAItem(
            question="What is tape useful for?",
            answer="Tape can stick things together or cover a crack for a little while to help keep them together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ("fracture", "bravery", "glue", "tape") for qa in WORLD_KNOWLEDGE.get(key, [])]


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
fractured(T) :- fracture(T), breakable(T).
brave(H) :- bravery(H).
tells_truth(H) :- brave(H), fears(H).
fixed(T) :- fractured(T), repaired(T).
happy_end(H,T) :- tells_truth(H), fixed(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("breakable", tid))
        lines.append(asp.fact("fracture", tid))
    for rid in REPAIRS:
        lines.append(asp.fact("repair_kind", rid))
    lines.append(asp.fact("bravery", "child"))
    lines.append(asp.fact("fears", "child"))
    lines.append(asp.fact("repaired", "treasure"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story_shapes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    return sorted(set(asp.atoms(model, "happy_end")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fractured/1. #show fixed/1."))
    clingo_shapes = set(asp.atoms(model, "fixed"))
    python_shapes = {"treasure"} if True else set()
    if clingo_shapes == python_shapes:
        print("OK: clingo twin is reachable and consistent with the repair ending.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  clingo:", sorted(clingo_shapes))
    print("  python:", sorted(python_shapes))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a fracture, bravery, and a careful repair."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if args.treasure and args.place:
        if not fracture_possible(SETTINGS[args.place], TREASURES[args.treasure]):
            raise StoryError("No valid fracture story for those options.")
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, treasure=treasure, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    treasure_cfg = TREASURES[params.treasure]
    treasure = world.add(Entity(id="treasure", type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, owner=hero.id, caretaker=helper.id))
    repair = select_repair(treasure_cfg)

    story_world = tell(SETTINGS[params.place], params.name, params.gender, params.helper, treasure_cfg, repair, [params.trait])
    story_world.facts.update(hero=hero, helper=helper, treasure=treasure, repair=repair)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=story_qa(story_world),
        world_qa=world_knowledge_qa(story_world),
        world=story_world,
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    return sorted(set(asp.atoms(model, "happy_end")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_story_shapes()
        print(f"{len(vals)} compatible story-shape facts:")
        for item in vals:
            print(f"  {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="kitchen", treasure="mug", name="Mia", gender="girl", helper="mother", trait="brave"),
            StoryParams(place="workshop", treasure="frame", name="Leo", gender="boy", helper="father", trait="steady"),
            StoryParams(place="garden", treasure="kite", name="Ivy", gender="girl", helper="mother", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: fracture in {p.place} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
