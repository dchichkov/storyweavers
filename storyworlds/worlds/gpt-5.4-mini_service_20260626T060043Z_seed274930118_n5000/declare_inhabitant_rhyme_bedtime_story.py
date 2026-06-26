#!/usr/bin/env python3
"""
storyworlds/worlds/declare_inhabitant_rhyme_bedtime_story.py
=============================================================

A tiny bedtime-story world about a child, a shy inhabitant, and a rhymed
declaration that helps a place feel like home.

Premise:
- A child discovers that a small night-dwelling inhabitant has moved into a cozy
  place.
- The child feels unsure at first, because the new inhabitant is strange and
  quiet and makes the room feel different.
- The child declares a gentle rhyme to welcome the inhabitant.
- That rhymed welcome changes the emotional weather: worry softens into
  belonging, and the inhabitant settles in.

This world is intentionally small and constraint-checked. It models a bedtime
scene with physical state ("meters") and emotional state ("memes"), and it
supports a reasonableness gate plus an ASP twin for parity checks.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
    afford: set[str] = field(default_factory=set)


@dataclass
class Inhabitant:
    id: str
    label: str
    phrase: str
    type: str
    habitat: str
    sound: str
    size: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Declaration:
    id: str
    line: str
    rhyme: str
    effect: str
    settle: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "bedroom": Setting("the bedroom", {"night", "cozy", "sleep"}),
    "nursery": Setting("the nursery", {"night", "cozy", "sleep"}),
    "attic": Setting("the attic nook", {"night", "cozy", "sleep"}),
}

INHABITANTS = {
    "owl": Inhabitant(
        id="owl",
        label="a sleepy owl",
        phrase="a small sleepy owl with soft feathers",
        type="owl",
        habitat="nights",
        sound="hoot",
        size="small",
        mood="shy",
        tags={"night", "feathers", "moon"},
    ),
    "mouse": Inhabitant(
        id="mouse",
        label="a tiny mouse",
        phrase="a tiny mouse with a warm nose",
        type="mouse",
        habitat="corners",
        sound="squeak",
        size="tiny",
        mood="shy",
        tags={"night", "whiskers", "crumbs"},
    ),
    "cat": Inhabitant(
        id="cat",
        label="a quiet cat",
        phrase="a quiet cat with a curled tail",
        type="cat",
        habitat="soft beds",
        sound="purr",
        size="small",
        mood="gentle",
        tags={"night", "paws", "purr"},
    ),
}

DECLARATIONS = {
    "welcome": Declaration(
        id="welcome",
        line="I declare a rhyme to make you feel at home",
        rhyme="Soft little night guest, rest in your nest; cozy and calm is the best of the best.",
        effect="belonging",
        settle="settled",
        tags={"rhyme", "welcome", "home"},
    ),
    "moon": Declaration(
        id="moon",
        line="I declare a rhyme for the moonlit room",
        rhyme="Moon above the pillow, moon above the bed; shine your silver laughter on the sleepy head.",
        effect="calm",
        settle="gentle",
        tags={"rhyme", "moon", "sleep"},
    ),
    "nest": Declaration(
        id="nest",
        line="I declare a rhyme for a cozy nest",
        rhyme="Nest beside the blanket, nest beside the wall; little night friend, you are welcome after all.",
        effect="belonging",
        settle="snug",
        tags={"rhyme", "nest", "welcome"},
    ),
}

CHILDREN = {
    "girl": ["Lily", "Mina", "Ada", "Nora", "Ivy", "Maya"],
    "boy": ["Theo", "Eli", "Finn", "Noah", "Leo", "Ben"],
}

TRAITS = ["gentle", "curious", "quiet", "brave", "kind"]


@dataclass
class StoryParams:
    place: str
    inhabitant: str
    declaration: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(place: str, inhabitant: Inhabitant, decl: Declaration) -> bool:
    if "rhyme" not in decl.tags:
        return False
    if "sleep" not in SETTINGS[place].afford:
        return False
    if inhabitant.type == "owl":
        return True
    if inhabitant.type == "mouse":
        return True
    if inhabitant.type == "cat":
        return True
    return False


def explain_rejection(place: str, inhabitant: Inhabitant, decl: Declaration) -> str:
    return (
        f"(No story: {inhabitant.label} does not fit the bedtime nook at {place}, "
        f"or the declaration is not a gentle rhyme that can help them settle.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child declares a rhyme for a shy inhabitant."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--inhabitant", choices=INHABITANTS)
    ap.add_argument("--declaration", choices=DECLARATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    inhabitant_id = args.inhabitant or rng.choice(list(INHABITANTS))
    decl_id = args.declaration or rng.choice(list(DECLARATIONS))
    inhabitant = INHABITANTS[inhabitant_id]
    decl = DECLARATIONS[decl_id]
    if not reasonableness_gate(place, inhabitant, decl):
        raise StoryError(explain_rejection(place, inhabitant, decl))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILDREN[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, inhabitant=inhabitant_id, declaration=decl_id, name=name, gender=gender, trait=trait)


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    inhabitant = INHABITANTS[params.inhabitant]
    decl = DECLARATIONS[params.declaration]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleepy": 0.2, "curiosity": 0.9},
        memes={"worry": 0.0, "delight": 0.0, "belonging": 0.0, "confidence": 0.0},
    ))
    adult = world.add(Entity(
        id="grownup",
        kind="character",
        type="mother",
        label="the grown-up",
        meters={"quiet": 0.7},
        memes={"calm": 0.8},
    ))
    guest = world.add(Entity(
        id=inhabitant.id,
        kind="character",
        type=inhabitant.type,
        label=inhabitant.label,
        phrase=inhabitant.phrase,
        meters={"shyness": 1.0, "restlessness": 0.4, "coziness": 0.0},
        memes={"worry": 0.4, "trust": 0.0, "belonging": 0.0},
    ))

    world.say(f"On a quiet night, {child.id} padded into {setting.place}.")
    world.say(f"That was where {guest.phrase} had become the newest inhabitant.")
    world.say(f"{child.id} had {params.trait} eyes, and {child.pronoun().capitalize()} looked at the little visitor with a mix of wonder and worry.")

    world.para()
    child.memes["worry"] += 1.0
    guest.memes["worry"] += 0.2
    world.say(f"{child.id} whispered, \"What if the room feels too strange for a {guest.type}?\"")
    world.say(f"The {guest.type} answered with a soft {inhabitant.sound}, and that made the pillows seem even quieter.")

    world.para()
    child.memes["confidence"] += 0.7
    child.meters["breath"] = 1.0
    guest.meters["coziness"] += 0.3
    world.say(f"Then {child.id} took a breath, stood by the bed, and declared a rhyme.")
    world.say(f'"{decl.rhyme}"')
    world.say(f"The words were small, but they sounded like a blanket being folded carefully around the dark.")

    world.para()
    child.memes["worry"] = max(0.0, _mem(child, "worry") - 0.8)
    child.memes["belonging"] += 1.0
    guest.memes["trust"] += 1.0
    guest.memes["belonging"] += 1.0
    guest.meters["coziness"] += 1.0
    world.say(f"The inhabitant listened, and the shyness began to melt.")
    world.say(f"{guest.label.capitalize()} blinked, then tucked in close to the soft little place.")
    world.say(f"{child.id} smiled, because the rhyme had turned a strange room into a shared one.")
    world.say(f"By the end of the night, the inhabitant was {decl.settle} and {child.id} was sleepy too, with the moon keeping watch outside.")

    world.facts.update(
        child=child,
        adult=adult,
        guest=guest,
        inhabitant_cfg=inhabitant,
        decl_cfg=decl,
        params=params,
        setting=setting,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guest = f["guest"]
    decl = f["decl_cfg"]
    return [
        f'Write a bedtime story for a preschooler where {child.id} meets {guest.label} in {world.setting.place}.',
        f'Write a gentle story that includes a rhyme and the word "inhabitant" as {child.id} welcomes the new inhabitant.',
        f'Tell a cozy bedtime tale in which a child declares "{decl.line.lower()}" and helps a shy guest feel at home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guest = f["guest"]
    decl = f["decl_cfg"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about in the {place}?",
            answer=f"It was about {child.id}, a little {child.type}, and {guest.label}, the new inhabitant in the room.",
        ),
        QAItem(
            question=f"What did {child.id} do to help the inhabitant feel safe?",
            answer=f"{child.id} declared a rhyme: \"{decl.rhyme}\". The gentle words helped the guest feel at home.",
        ),
        QAItem(
            question=f"How did the inhabitant feel after the rhyme?",
            answer=f"The inhabitant felt calmer and more welcome. The shyness faded, and the little guest settled down.",
        ),
        QAItem(
            question=f"Why did the room feel different at the beginning?",
            answer=f"The room felt different because a new inhabitant had arrived, and {child.id} felt a little worried at first.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the ends, and people often use rhymes in songs and bedtime stories.",
        ),
        QAItem(
            question="What does inhabitant mean?",
            answer="An inhabitant is a living thing that lives in a place, like a bird in a tree or a person in a house.",
        ),
        QAItem(
            question="Why are bedtime stories often gentle?",
            answer="Bedtime stories are often gentle because they help children feel calm, safe, and ready for sleep.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", inhabitant="owl", declaration="welcome", name="Mina", gender="girl", trait="gentle"),
    StoryParams(place="nursery", inhabitant="mouse", declaration="nest", name="Theo", gender="boy", trait="curious"),
    StoryParams(place="attic", inhabitant="cat", declaration="moon", name="Lily", gender="girl", trait="quiet"),
]


ASP_RULES = r"""
bedtime_place(P) :- setting(P).
bedtime_inhabitant(I) :- inhabitant(I).
gentle_declaration(D) :- declaration(D), rhyme_decl(D).
valid_story(P,I,D) :- bedtime_place(P), bedtime_inhabitant(I), gentle_declaration(D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for iid, inh in INHABITANTS.items():
        lines.append(asp.fact("inhabitant", iid))
        lines.append(asp.fact("habitat", iid, inh.habitat))
        lines.append(asp.fact("sound", iid, inh.sound))
    for did, decl in DECLARATIONS.items():
        lines.append(asp.fact("declaration", did))
        lines.append(asp.fact("rhyme_decl", did))
        lines.append(asp.fact("effect", did, decl.effect))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for iid, inh in INHABITANTS.items():
            for did, decl in DECLARATIONS.items():
                if reasonableness_gate(place, inh, decl):
                    combos.append((place, iid, did))
    return combos


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    inhabitant_id = args.inhabitant or rng.choice(list(INHABITANTS))
    decl_id = args.declaration or rng.choice(list(DECLARATIONS))
    if not reasonableness_gate(place, INHABITANTS[inhabitant_id], DECLARATIONS[decl_id]):
        raise StoryError(explain_rejection(place, INHABITANTS[inhabitant_id], DECLARATIONS[decl_id]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILDREN[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, inhabitant=inhabitant_id, declaration=decl_id, name=name, gender=gender, trait=trait)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible (place, inhabitant, declaration) combos:\n")
        for place, iid, did in vals:
            print(f"  {place:10} {iid:12} {did}")
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
            try:
                params = build_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.inhabitant} in {p.place} ({p.declaration})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
