#!/usr/bin/env python3
"""
storyworlds/worlds/damper_entrance_couch_inner_monologue_sound_effects.py
==========================================================================

A tiny animal-story world about a damp little pet, an entrance, and a couch.

Seed tale:
---
A small animal comes in from outside with damp paws. It wants to jump to the
couch, but the grown-up worries the couch will get wet. The little animal hears
the worry, thinks hard to itself, and uses a soft damper mat at the entrance to
dry off first. Then it hops onto the couch with happy sound effects.

World idea:
---
- A character has physical wetness in meters and feelings in memes.
- The entrance is where wet paws first arrive.
- The couch is a cozy prize that can be ruined by dampness.
- The damper is a soft pad/mat that both quiets steps and dries paws.
- Inner monologue and sound effects are part of the narration, not just labels.
- The story ends with a visible change: the couch stays dry and the pet feels
  proud and cozy.

The script includes a reasonableness gate plus an inline ASP twin for parity
checks.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"kitten", "cat", "girl", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"puppy", "dog", "boy", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    entrance: str = "the entrance"
    couch: str = "the couch"


@dataclass
class StoryParams:
    animal: str
    name: str
    helper: str
    seed: Optional[int] = None


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


def sound(label: str) -> str:
    return {"wet_steps": "tap-tap", "hop": "boing", "drop": "plip", "dry": "fluff-fluff"}.get(label, "tap")


def inner_monologue(text: str) -> str:
    return f'"{text}"'


def world_knowledge_hint(animal: str) -> str:
    return {
        "kitten": "Kittens like warm, soft places to curl up.",
        "puppy": "Puppies often shake when they are wet.",
        "bunny": "Bunnies have quick feet and soft fur.",
    }.get(animal, "Little animals like cozy places.")


def setting_detail() -> str:
    return "The entrance had a soft mat, and the couch looked extra cozy by the wall."


def reasonableness_gate(params: StoryParams) -> None:
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal choice.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper choice.")


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wet_couch(world: World) -> list[str]:
    out = []
    pet = world.get("pet")
    couch = world.get("couch")
    if pet.meters.get("wet", 0) >= THRESHOLD and pet.props.get("on_couch") == "yes":
        sig = ("wet_couch",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        couch.meters["wet"] = couch.meters.get("wet", 0) + 1
        out.append("The couch got damp.")
    return out


def _r_dry_paws(world: World) -> list[str]:
    out = []
    pet = world.get("pet")
    damper = world.get("damper")
    if pet.meters.get("wet", 0) >= THRESHOLD and pet.props.get("used_damper") == "yes":
        sig = ("dry",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        pet.meters["wet"] = 0
        pet.memes["pride"] = pet.memes.get("pride", 0) + 1
        damper.meters["used"] = 1
        out.append("The damper mat soaked up the wet paws.")
    return out


def _r_cozy(world: World) -> list[str]:
    out = []
    pet = world.get("pet")
    couch = world.get("couch")
    if pet.meters.get("wet", 0) < THRESHOLD and pet.props.get("on_couch") == "yes":
        sig = ("cozy",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        pet.memes["joy"] = pet.memes.get("joy", 0) + 1
        out.append("The little animal settled down happily.")
    return out


RULES = [Rule("wet_couch", _r_wet_couch), Rule("dry_paws", _r_dry_paws), Rule("cozy", _r_cozy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(Setting())
    pet = world.add(Entity(
        id="pet",
        kind="character",
        type=params.animal,
        label=params.name,
        owner=params.helper,
        meters={"wet": 1.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label="the grown-up",
        meters={},
        memes={},
    ))
    damper = world.add(Entity(
        id="damper",
        type="mat",
        label="damper mat",
        phrase="a soft damper mat by the entrance",
        meters={"softness": 1.0},
        props={"place": "entrance"},
    ))
    couch = world.add(Entity(
        id="couch",
        type="couch",
        label="couch",
        phrase="a cozy couch",
        meters={"dry": 1.0},
        caretaker=helper.id,
    ))

    world.facts.update(pet=pet, helper=helper, damper=damper, couch=couch)

    world.say(f"{pet.label} came to {world.setting.entrance} with damp paws.")
    world.say(f"{world_knowledge_hint(params.animal)}")
    world.say(setting_detail())
    world.say(f"*{sound('wet_steps')}* {pet.label} paused beside the damper mat.")

    world.para()
    world.say(
        f"{inner_monologue('I want the couch, but I do not want to leave wet pawprints.')}"
    )
    world.say(
        f"{helper.label.capitalize()} said, 'The couch stays nicer if you dry off first.'"
    )
    world.say(
        f"*{sound('drop')}* {pet.label} looked at the soft mat and thought, "
        f"{inner_monologue('Maybe the damper can help me.')}"
    )

    pet.props["used_damper"] = "yes"
    propagate(world, narrate=True)

    world.para()
    world.say(f"*{sound('dry')}* {pet.label} shook, stepped on the damper, and felt much lighter.")
    world.say(f"Then {pet.label} gave a tiny hop to the couch.")
    pet.props["on_couch"] = "yes"
    pet.meters["wet"] = pet.meters.get("wet", 0)
    propagate(world, narrate=True)

    if couch.meters.get("wet", 0) < THRESHOLD:
        world.say(f"The couch stayed dry, and {pet.label} curled up with a proud little smile.")
    else:
        world.say(f"The couch was damp, and {helper.label} had to fetch a towel.")

    world.facts["resolved"] = couch.meters.get("wet", 0) < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["pet"]
    return [
        f'Write a short animal story for a little child that includes "damper", "entrance", and "couch".',
        f"Tell a gentle story about {p.label} the {p.type} learning to dry off before going onto the couch.",
        f"Write a cozy story with inner monologue and sound effects about a wet pet at the entrance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    pet = world.facts["pet"]
    helper = world.facts["helper"]
    couch = world.facts["couch"]
    resolved = world.facts["resolved"]
    qa = [
        QAItem(
            question=f"Where did {pet.label} come when the story began?",
            answer=f"{pet.label} came to the entrance with damp paws.",
        ),
        QAItem(
            question=f"What did {pet.label} want before drying off?",
            answer=f"{pet.label} wanted to get to the couch and curl up there.",
        ),
        QAItem(
            question=f"Why did the grown-up talk about the couch?",
            answer=f"The grown-up wanted {pet.label} to dry off first so the couch would stay dry.",
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question="How did the damper help?",
            answer="The damper mat soaked up the wet paws, so the little animal could hop onto the couch without making it damp.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    pet = world.facts["pet"]
    return [
        QAItem(
            question="What is a couch for?",
            answer="A couch is a soft place where people or animals can sit, rest, or cuddle.",
        ),
        QAItem(
            question="What does a mat do near an entrance?",
            answer="A mat can help wipe off shoes or paws before someone walks farther inside.",
        ),
        QAItem(
            question="Why do wet paws leave marks?",
            answer="Wet paws can leave little footprints or pawprints because the water touches the floor or furniture.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ANIMALS = {
    "kitten": "kitten",
    "puppy": "puppy",
    "bunny": "bunny",
}
HELPERS = {
    "cat": "cat",
    "dog": "dog",
    "rabbit": "rabbit",
}

CURATED = [
    StoryParams(animal="kitten", name="Milo", helper="cat"),
    StoryParams(animal="puppy", name="Pip", helper="dog"),
    StoryParams(animal="bunny", name="Nini", helper="rabbit"),
]


ASP_RULES = r"""
wet_pet(P) :- pet(P), wet(P).
uses_damper(P) :- pet(P), damp_mat(D), at(D, entrance), uses(P, D).
safe_couch(C) :- couch(C), not wet(C).
wet_couch(C) :- couch(C), pet_on_couch(P, C), wet_pet(P).
resolved :- uses_damper(P), pet_on_couch(P, C), safe_couch(C), not wet_couch(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("entrance", "entrance"),
        asp.fact("couch", "couch"),
    ]
    for a in ANIMALS:
        lines.append(asp.fact("pet", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("damp_mat", "damper"))
    lines.append(asp.fact("at", "damper", "entrance"))
    lines.append(asp.fact("wet", "pet"))
    lines.append(asp.fact("uses", "pet", "damper"))
    lines.append(asp.fact("pet_on_couch", "pet", "couch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    asp_ok = any(sym.name == "resolved" for sym in model)
    py_ok = True
    for p in CURATED:
        w = tell(p)
        py_ok = py_ok and w.facts["resolved"]
    if asp_ok and py_ok:
        print("OK: ASP and Python both support the resolved damper story.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about an entrance, a damper, and a couch.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    animal = args.animal or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice(list(HELPERS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(["Milo", "Pip", "Nini", "Tia", "Bean"])
    return StoryParams(animal=animal, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} the {p.animal}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
