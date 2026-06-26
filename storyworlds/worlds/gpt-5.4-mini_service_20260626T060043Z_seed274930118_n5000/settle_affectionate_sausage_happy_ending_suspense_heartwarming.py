#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/settle_affectionate_sausage_happy_ending_suspense_heartwarming.py
===================================================================================================

A small heartwarming story world about a child trying to help an affectionate
sausage dog settle in a new place. The narrative has a little suspense about
whether the pup will calm down, then ends with a cozy happy ending.

The seed words for this world are:
- settle
- affectionate
- sausage

The domain is intentionally compact and simulation-driven:
- a child, a grown-up, a sausage dog, and a cozy place
- a small emotional arc built from unease -> effort -> relief
- prose is produced from world state, not from a frozen template swap
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    soothing: str
    possible: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    child_type: str
    parent_type: str
    dog_name: str
    dog_tempest: str
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_dog_wanders(world: World) -> list[str]:
    out: list[str] = []
    dog = world.get("dog")
    if dog.memes.get("restless", 0.0) < THRESHOLD:
        return out
    if world.setting.indoors:
        sig = ("wander", "indoors")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        dog.meters["distance"] = dog.meters.get("distance", 0.0) + 1.0
        out.append("The little dog kept circling the rug, unable to settle.")
    return out


def _r_calm_from_care(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    dog = world.get("dog")
    if child.memes.get("affection", 0.0) < THRESHOLD:
        return out
    if dog.memes.get("restless", 0.0) < THRESHOLD:
        return out
    sig = ("calm", "care")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dog.memes["restless"] = 0.0
    dog.memes["safe"] = dog.memes.get("safe", 0.0) + 1.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    out.append("That gentle care helped the little dog finally settle.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("dog_wanders", _r_dog_wanders),
    Rule("calm_from_care", _r_calm_from_care),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "cottage": Setting(
        place="the little cottage",
        indoors=True,
        soothing="warm lamplight",
        possible={"settle"},
    ),
    "train": Setting(
        place="the train compartment",
        indoors=True,
        soothing="steady wheels",
        possible={"settle"},
    ),
    "garden": Setting(
        place="the back garden",
        indoors=False,
        soothing="fresh grass",
        possible={"settle"},
    ),
}

NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Toby", "Ella", "Max"]
DOG_NAMES = ["Sausage", "Biscuit", "Muffin", "Pickles", "Pepper", "Poppy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "settle") for place in SETTINGS]


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.dog_name.strip().lower() == params.name.strip().lower():
        raise StoryError("The child and the dog need different names.")
    if params.dog_tempest not in {"restless", "nervous"}:
        raise StoryError("Unsupported dog temperament.")
    if params.place == "garden" and params.dog_tempest == "nervous":
        return


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for act in sorted(setting.possible):
            lines.append(asp.fact("possible", pid, act))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P) :- place(P), possible(P, settle).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = {(p,) for p, a in valid_combos() if a == "settle"}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story about a child and an affectionate sausage dog.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--dog-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    params = StoryParams(
        place=place,
        name=name,
        child_type=child_type,
        parent_type=parent_type,
        dog_name=dog_name,
        dog_tempest="restless",
    )
    reasonableness_check(params)
    return params


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.name,
        meters={"care": 0.0},
        memes={"affection": 1.0, "hope": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=params.parent_type,
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    dog = world.add(Entity(
        id="dog",
        kind="character",
        type="dog",
        label=params.dog_name,
        meters={"wiggles": 1.0},
        memes={"restless": 1.0, "affection": 1.0},
    ))
    world.facts.update(child=child, parent=parent, dog=dog, params=params)
    return world


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    dog: Entity = world.facts["dog"]

    world.say(
        f"{child.label} and {parent.label} arrived at {world.setting.place}, where "
        f"{world.setting.soothing} made the room feel gentle."
    )
    world.say(
        f"{dog.label} was an affectionate sausage dog, but {dog.pronoun()} could not "
        f"quite settle after the trip."
    )
    world.para()
    world.say(
        f"{child.label} noticed the worry in {dog.pronoun('possessive')} little paws "
        f"and sat down beside {dog.it()}."
    )
    child.memes["affection"] += 1.0
    child.meters["care"] += 1.0
    world.say(
        f"{child.label} stroked {dog.pronoun('possessive')} ears and whispered that "
        f"{dog.label} was safe now."
    )
    propagate(world, narrate=True)
    world.para()
    if dog.memes.get("restless", 0.0) >= THRESHOLD:
        world.say(
            f"For one suspenseful moment, it looked as if {dog.label} might keep "
            f"pacing forever."
        )
    else:
        world.say(
            f"Then {dog.label} curled up at last, with a soft sigh that filled the room."
        )
    world.say(
        f"{parent.label.capitalize()} smiled, because the whole place felt warmer "
        f"once {dog.label} had settled beside {child.label}."
    )
    world.say(
        f"In the end, the little sausage dog slept in a cozy heap, and {child.label} "
        f"sat very still so the happy moment would last."
    )


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    dog: Entity = world.facts["dog"]
    return [
        QAItem(
            question=f"Who tried to help {dog.label} settle?",
            answer=f"{child.label} tried to help {dog.label} settle, with {parent.label} nearby."
        ),
        QAItem(
            question=f"Why was there suspense in the story?",
            answer=f"There was suspense because {dog.label} was restless and could not settle right away."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {dog.label} curled up safely and {child.label} feeling warm and glad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to settle down?",
            answer="To settle down means to become calm, stop moving around so much, and rest in one place."
        ),
        QAItem(
            question="What does affectionate mean?",
            answer="Affectionate means warm and loving, like a pet that likes cuddles and gentle attention."
        ),
        QAItem(
            question="What is a sausage dog?",
            answer="A sausage dog is a small dog with a long body and short legs, often called a dachshund."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    return [
        "Write a heartwarming story with a little suspense about helping an affectionate sausage dog settle.",
        f"Tell a child-friendly tale where {params.name} calms a restless sausage dog at {world.setting.place}.",
        "Create a short happy-ending story in which gentle care helps a worried pet settle at last.",
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def asp_valid_places() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_places()
        print(f"{len(vals)} valid places:")
        for (place,) in vals:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                name=NAMES[0],
                child_type="girl",
                parent_type="mother",
                dog_name="Sausage",
                dog_tempest="restless",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
