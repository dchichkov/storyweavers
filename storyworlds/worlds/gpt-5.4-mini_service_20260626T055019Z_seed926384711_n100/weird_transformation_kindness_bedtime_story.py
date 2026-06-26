#!/usr/bin/env python3
"""
storyworlds/worlds/weird_transformation_kindness_bedtime_story.py
=================================================================

A small bedtime-story world about a weird little transformation that only
settles down when someone chooses kindness.

Seed idea:
---
At bedtime, a strange speck in the room begins to change shape in a weird way.
The child is startled, but instead of being scared, they speak softly, share a
blanket, and offer a cup of water. The weird thing relaxes and transforms into a
gentle night companion. Kindness makes the room calm enough for sleep.

World model:
---
- A child, a caregiver, and one unusual bedtime object.
- The object has a "strangeness" meter that can flare up or settle.
- Kindness lowers fear and strangeness; roughness raises both.
- A successful bedtime resolution transforms the object into a cozy, harmless
  form that helps the child fall asleep.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample imported eagerly
- ASP helper imported lazily inside ASP functions
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed_into: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def touch(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def feel(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=lambda: {"mystery", "transform"})


@dataclass
class MagicThing:
    id: str
    label: str
    phrase: str
    first_form: str
    second_form: str
    third_form: str
    trigger: str
    soothing_action: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortGear:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
    setting: str
    magic: str
    comfort: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"mystery", "transform"}),
}

MAGICS = {
    "moonpebble": MagicThing(
        id="moonpebble",
        label="moon pebble",
        phrase="a weird little moon pebble",
        first_form="a chilly pebble",
        second_form="a wobbling silver seed",
        third_form="a sleepy glow-mouse",
        trigger="kind words",
        soothing_action="spoken to softly",
        keyword="weird",
        tags={"weird", "moon", "transform"},
    ),
    "starbutton": MagicThing(
        id="starbutton",
        label="star button",
        phrase="a weird star button",
        first_form="a flat button",
        second_form="a spinning star wheel",
        third_form="a tiny lantern bird",
        trigger="a gentle hug",
        soothing_action="held with care",
        keyword="weird",
        tags={"weird", "star", "transform"},
    ),
    "cloudspool": MagicThing(
        id="cloudspool",
        label="cloud spool",
        phrase="a weird cloud spool",
        first_form="a soft spool",
        second_form="a puffed-up cloud nest",
        third_form="a little dream sheep",
        trigger="a blanket",
        soothing_action="tucked in kindly",
        keyword="weird",
        tags={"weird", "cloud", "transform"},
    ),
}

COMFORTS = {
    "blanket": ComfortGear(
        id="blanket",
        label="blanket",
        phrase="a warm blanket",
        effect="made the room feel snug",
        tags={"soft", "warm"},
    ),
    "water": ComfortGear(
        id="water",
        label="cup of water",
        phrase="a tiny cup of water",
        effect="helped the magic settle",
        tags={"kindness", "calm"},
    ),
    "lamp": ComfortGear(
        id="lamp",
        label="night lamp",
        phrase="a small night lamp",
        effect="kept the shadows gentle",
        tags={"light", "calm"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Ella", "Ada"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Max", "Noah", "Eli", "Ben"]
TRAITS = ["gentle", "curious", "sleepy", "brave", "soft-spoken", "kind"]


def transformable(magic: MagicThing, comfort: ComfortGear) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MAGICS:
            for c in COMFORTS:
                combos.append((s, m, c))
    return combos


def explain_rejection(magic: MagicThing, comfort: ComfortGear) -> str:
    return (
        f"(No story: the {magic.label} and {comfort.label} do not make a coherent "
        f"bedtime kindness-to-transformation arc.)"
    )


def explain_gender(gender: str) -> str:
    return f"(No story: please choose a supported gender for this bedtime tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about weird transformation and kindness."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=["transform"])
    ap.add_argument("--prize", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.gender))
    place = args.place or "bedroom"
    magic = args.magic or rng.choice(list(MAGICS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=place,
        magic=magic,
        comfort=comfort,
        name=name,
        gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleepy": 0.2},
        memes={"wonder": 1.0, "worry": 0.0, "kindness": 1.0},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=params.caregiver,
        label=f"the {params.caregiver}",
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    magic = world.add(Entity(
        id=params.magic,
        type="thing",
        label=MAGICS[params.magic].label,
        phrase=MAGICS[params.magic].phrase,
        owner=child.id,
        caretaker=caregiver.id,
        meters={"strangeness": 1.0, "glow": 0.4},
        memes={"restless": 1.0},
        transformed_into=MAGICS[params.magic].third_form,
    ))
    comfort = world.add(Entity(
        id=params.comfort,
        type="thing",
        label=COMFORTS[params.comfort].label,
        phrase=COMFORTS[params.comfort].phrase,
        meters={"softness": 1.0},
        memes={"calm": 1.0},
    ))
    world.facts.update(
        child=child, caregiver=caregiver, magic=magic, comfort=comfort, params=params
    )
    return world


def introduce(world: World) -> None:
    f = world.facts
    child = f["child"]
    magic = f["magic"]
    world.say(
        f"{child.id} was a little {child.memes and ''}".strip()
    )
    world.paragraphs[-1].clear()
    world.say(
        f"{child.id} was a {f['params'].trait} {f['params'].gender} who liked quiet bedtime things."
    )
    world.say(
        f"In {world.setting.place}, there was a {magic.phrase} on the shelf."
    )
    world.say(
        f"It looked weird, but in a sleepy, interesting way."
    )


def begin_transform(world: World) -> None:
    magic = world.facts["magic"]
    world.say(
        f"At bedtime, the {magic.label} began to change."
    )
    magic.touch("strangeness", 1.0)
    magic.touch("glow", 0.5)
    world.trace.append("magic began transforming")


def fear_reaction(world: World) -> None:
    child = world.facts["child"]
    magic = world.facts["magic"]
    child.feel("worry", 0.8)
    world.say(
        f"{child.id} blinked at the weird sight and hugged the quilt a little tighter."
    )
    world.say(
        f"The {magic.label} wobbled from a pebble into a silver seed."
    )
    magic.transformed_into = "a wobbling silver seed"
    magic.touch("strangeness", 0.5)
    world.trace.append("child worried")


def kindness_action(world: World) -> None:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    comfort = world.facts["comfort"]
    magic = world.facts["magic"]
    world.say(
        f"Then {child.id} remembered to be kind."
    )
    world.say(
        f"{child.id} spoke softly to the {magic.label}, and {caregiver.label} offered {comfort.phrase}."
    )
    world.say(
        f"That gentle choice made the room feel warm and safe."
    )
    child.feel("kindness", 1.0)
    child.feel("worry", -0.5)
    magic.touch("strangeness", -0.8)
    magic.touch("glow", 0.2)
    comfort.touch("softness", 0.5)
    world.trace.append("kindness lowered strangeness")


def complete_transformation(world: World) -> None:
    magic = world.facts["magic"]
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    comfort = world.facts["comfort"]
    magic.transformed_into = MAGICS[world.facts["params"].magic].third_form
    magic.touch("strangeness", -0.2)
    world.say(
        f"The weird thing finally finished transforming."
    )
    world.say(
        f"It became {MAGICS[world.facts['params'].magic].third_form}, "
        f"small and friendly and ready to rest."
    )
    world.say(
        f"{child.id} smiled, and {caregiver.label} tucked the blanket around them both."
    )
    world.say(
        f"By the end, the room was quiet, the {magic.label} was calm, and kindness had done the hardest part."
    )
    child.feel("sleepy", 1.0)
    child.feel("worry", -0.2)
    comfort.touch("softness", 0.2)
    world.trace.append("transformation finished")


def tell_story(world: World) -> None:
    introduce(world)
    world.para()
    begin_transform(world)
    fear_reaction(world)
    world.para()
    kindness_action(world)
    complete_transformation(world)


def story_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    magic = f["magic"]
    comfort = f["comfort"]
    child = f["child"]
    return [
        "Write a gentle bedtime story about a weird transformation that settles when someone chooses kindness.",
        f"Tell a sleepy story where {child.id} watches a weird {magic.label} change shape, then uses kindness to calm it.",
        f"Write a short bedtime tale featuring a {params.trait} {params.gender}, a {magic.label}, and {comfort.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    magic = f["magic"]
    comfort = f["comfort"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who saw the weird thing begin to change at bedtime?",
            answer=f"{child.id} saw the {magic.label} begin to change in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} do that helped the strange object settle down?",
            answer=f"{child.id} chose kindness by speaking softly, and {caregiver.label} offered {comfort.phrase}.",
        ),
        QAItem(
            question=f"What did the {magic.label} turn into by the end of the story?",
            answer=f"It transformed into {MAGICS[params.magic].third_form}, which felt friendly and calm.",
        ),
        QAItem(
            question=f"Why was the bedtime moment weird at first?",
            answer=f"It was weird because the {magic.label} started changing shape before anyone expected it to, and that made the room feel surprising.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, comfort, or speak gently to someone or something that needs care.",
        ),
        QAItem(
            question="What happens when a room gets sleepy and quiet at bedtime?",
            answer="A sleepy quiet room helps bodies rest, slow down, and get ready for sleep.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or state.",
        ),
        QAItem(
            question="Why can gentle words help?",
            answer="Gentle words can calm fear and make a scary moment feel safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v:.2f}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v:.2f}' for k, v in e.memes.items())}}}")
        if e.transformed_into:
            bits.append(f"becomes={e.transformed_into}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.extend(world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
magic_changes(M) :- magic(M).
kindness_helps(C, M) :- child(C), magic(M), kindness(C).
resolved(M) :- kindness_helps(_, M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("kindness", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show magic_changes/1.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    expected = {("child",)} if True else set()
    if atoms == expected:
        print("OK: ASP gate matches the Python reasonableness story.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


def asp_valids() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show magic_changes/1.\n"))
    return sorted(set(asp.atoms(model, "magic_changes")))


CURATED = [
    StoryParams(setting="bedroom", magic="moonpebble", comfort="blanket", name="Mia", gender="girl", caregiver="mother", trait="gentle"),
    StoryParams(setting="bedroom", magic="starbutton", comfort="water", name="Leo", gender="boy", caregiver="father", trait="curious"),
    StoryParams(setting="bedroom", magic="cloudspool", comfort="lamp", name="Ivy", gender="girl", caregiver="mother", trait="sleepy"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show magic_changes/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valids())} magic changes are available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.magic} with {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
