#!/usr/bin/env python3
"""
A tiny mystery-style story world about a puny item, a washing problem, a
compress, a twist, a misunderstanding, and a careful solution.

The world premise:
- A small, tired child notices something "puny" and wrong in the laundry room.
- A washing mishap creates a mystery: a cloth, sleeve, or soft bundle seems ruined.
- A compress can help, but only if used in the right way.
- A twist reveals the real cause of the problem.
- A misunderstanding creates tension.
- Problem solving ends the story with a gentle fix and a clearer scene.

This file follows the storyworld contract and is self-contained.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
    place: str = "the laundry room"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
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
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


OBJECTS = {
    "shirt": ObjectCfg(label="shirt", phrase="a tiny white shirt", type="shirt", region="torso"),
    "sock": ObjectCfg(label="sock", phrase="a small striped sock", type="sock", region="feet"),
    "cloth": ObjectCfg(label="cloth", phrase="a soft washing cloth", type="cloth", region="torso"),
    "pouch": ObjectCfg(label="pouch", phrase="a little canvas pouch", type="pouch", region="torso"),
}

SETTINGS = {
    "laundry": Setting(place="the laundry room", affords={"washing", "compress"}),
    "porch": Setting(place="the porch", affords={"washing", "compress"}),
    "bathroom": Setting(place="the bathroom", affords={"washing", "compress"}),
}

TRAITS = ["quiet", "curious", "careful", "shy", "bright", "stern"]
GIRL_NAMES = ["Mina", "June", "Ivy", "Lena", "Nia", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Eli", "Milo", "Nico"]


def pronoun_name(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj in OBJECTS:
            combos.append((place, obj))
    return combos


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: {obj} does not fit this mystery setup at {place}.)"


def build_reasonable_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(pronoun_name(gender))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, gender=gender, parent=parent, trait=trait)


def puzzle_text(obj: ObjectCfg) -> str:
    return {
        "shirt": "The shirt looked smaller than it should have, as if the wash had pinched it tight.",
        "sock": "The sock looked puny and curled, like it had lost a bit of its shape.",
        "cloth": "The cloth had a strange twist in one corner, like it was hiding a clue.",
        "pouch": "The pouch sagged oddly, as if something inside had been moved twice.",
    }[obj.type]


def twist_clue(obj: ObjectCfg) -> str:
    return {
        "shirt": "A tiny knot had been tied inside the hem.",
        "sock": "A second sock had been tucked into the first one.",
        "cloth": "A cleaning clip was pinching the cloth from behind.",
        "pouch": "A button had caught on the pouch's seam.",
    }[obj.type]


def compress_help(obj: ObjectCfg) -> str:
    return {
        "shirt": "They pressed a cool compress against the wrinkled spot so the fabric could settle.",
        "sock": "They wrapped the sock around a cool compress, and the shape loosened a little.",
        "cloth": "They laid the cloth over a cool compress so the twist could soften.",
        "pouch": "They set a cool compress under the pouch so the bent seam could relax.",
    }[obj.type]


def generate_story_text(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    obj: Entity = f["object"]
    obj_cfg: ObjectCfg = f["object_cfg"]

    world.say(
        f"{hero.id} was a {hero.pronoun('subject')} little {hero.traits[0]} child who noticed "
        f"everything in {world.setting.place}."
    )
    world.say(
        f"One day, {hero.id} saw {hero.pronoun('possessive')} {obj.label} and frowned. "
        f"{puzzle_text(obj_cfg)}"
    )

    world.para()
    world.say(
        f"{hero.id} thought the washing had gone wrong, so {hero.pronoun('subject')} hurried to "
        f"{hero.pronoun('possessive')} {parent.type}."
    )
    world.say(
        f'"{hero.id} said the {obj.label} was ruined," {parent.pronoun("subject")} said, '
        f"but {parent.pronoun('subject')} was not sure."
    )

    world.para()
    world.say(
        f"Together they looked closer. That was the twist: {twist_clue(obj_cfg)}"
    )
    world.say(
        f"It was not a broken wash at all. It was a misunderstanding about what had made the {obj.label} look puny."
    )

    world.para()
    world.say(
        f"{hero.id} and {parent.id} used problem solving instead of worry. {compress_help(obj_cfg)}"
    )
    world.say(
        f"In the end, the {obj.label} looked steady again, and {hero.id} could smile at the clean, quiet answer."
    )


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "small"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(
        id="Object",
        type=obj_cfg.type,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, parent=parent, object=obj, object_cfg=obj_cfg)
    generate_story_text(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    obj: Entity = f["object"]
    return [
        f'Write a short mystery story for a young child about a puny {obj.label} and a washing problem.',
        f"Tell a gentle story where {hero.id} thinks something went wrong during washing, then discovers a twist.",
        f"Write a simple story with a misunderstanding, a cool compress, and a problem solved by looking closely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    obj: Entity = f["object"]
    obj_cfg: ObjectCfg = f["object_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} think was wrong with the {obj.label}?",
            answer=f"{hero.id} thought the washing had gone wrong and that the {obj.label} had been ruined.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that a small hidden thing, like a knot, clip, or caught seam, had made the {obj.label} look puny.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.id} solve the problem?",
            answer=f"They used problem solving and a cool compress to calm the {obj.label} and understand what was really happening.",
        ),
        QAItem(
            question=f"Why was this a misunderstanding?",
            answer=f"It was a misunderstanding because the {obj.label} looked wrong, but the washing was not the true cause.",
        ),
        QAItem(
            question=f"What did the compress help with?",
            answer=f"The compress helped soften the wrinkled or bent spot so the {obj_cfg.label} could settle back into shape.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compress?",
            answer="A compress is a cool or warm cloth placed on a spot to help it feel better or relax.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone thinks something is true, but they have the wrong idea.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully, thinking step by step, and trying a smart fix.",
        ),
        QAItem(
            question="What does it mean if something is puny?",
            answer="If something is puny, it is small, weak, or less strong than expected.",
        ),
        QAItem(
            question="Why do people wash clothes?",
            answer="People wash clothes to remove dirt, smells, and stains so the clothes are clean again.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_setting(laundry).
mystery_setting(porch).
mystery_setting(bathroom).

known_problem(washing).
known_solution(compress).
known_theme(twist).
known_theme(misunderstanding).
known_theme(problem_solving).

valid_story(Place,Object) :- mystery_setting(Place), object(Object).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("mystery_setting", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    try:
        asp_set = set(valid_combos_asp())
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    if asp_set == python_set:
        print(f"OK: ASP matches python valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and python.")
    print("only in ASP:", sorted(asp_set - python_set))
    print("only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about washing, a compress, and a twist.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--object", choices=OBJECTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    return build_reasonable_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(place="laundry", object="shirt", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bathroom", object="sock", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="porch", object="cloth", name="Ivy", gender="girl", parent="mother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, obj in combos:
            print(f"  {place:9} {obj}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
