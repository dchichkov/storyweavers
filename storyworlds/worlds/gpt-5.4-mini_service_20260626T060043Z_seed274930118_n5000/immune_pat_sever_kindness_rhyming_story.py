#!/usr/bin/env python3
"""
storyworlds/worlds/immune_pat_sever_kindness_rhyming_story.py
==============================================================

A small standalone storyworld built from the seed words:
immune, pat, sever

Premise:
- A kind child wants to play with a little pet in a rhyming, child-facing tale.
- A sudden problem severs a ribbon on the pet's kite-harness.
- The grown-up worries, but kindness and a gentle pat help the child choose a safe fix.
- The ending proves the change in state: the pet is calm, the ribbon is mended, and
  kindness wins.

This world keeps the story style close to a rhyming story while still using a
stateful simulation with meters and memes.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"


@dataclass
class Pet:
    label: str
    phrase: str
    type: str
    immune: str
    rhymes_with: str


@dataclass
class Ribbon:
    label: str
    phrase: str
    severed_by: str
    repair_tool: str


@dataclass
class StoryParams:
    pet: str
    ribbon: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


SETTINGS = {"garden": Setting(place="the garden")}

PETS = {
    "pup": Pet(
        label="pup",
        phrase="a bright little pup",
        type="dog",
        immune="immune to a few tiny garden germs",
        rhymes_with="cup",
    ),
    "duck": Pet(
        label="duck",
        phrase="a fluffy little duck",
        type="duck",
        immune="immune to cold pond splashes",
        rhymes_with="luck",
    ),
    "kitten": Pet(
        label="kitten",
        phrase="a sleepy little kitten",
        type="cat",
        immune="immune to a chilly breeze",
        rhymes_with="mitten",
    ),
}

RIBBONS = {
    "red": Ribbon(
        label="red ribbon",
        phrase="a shiny red ribbon",
        severed_by="thorn",
        repair_tool="needle and thread",
    ),
    "blue": Ribbon(
        label="blue ribbon",
        phrase="a soft blue ribbon",
        severed_by="snip",
        repair_tool="needle and thread",
    ),
    "gold": Ribbon(
        label="gold ribbon",
        phrase="a bright gold ribbon",
        severed_by="branch",
        repair_tool="needle and thread",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ruby", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Owen", "Theo", "Ben"]
PARENTS = ["mother", "father"]
TRAITS = ["kind", "gentle", "cheery", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    return [("garden", pet_id) for pet_id in PETS]


@dataclass
class ASPFactSet:
    facts: list[str]


ASP_RULES = r"""
pet(P).
ribbon(R).
valid(garden,P,R) :- pet(P), ribbon(R).
"""


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("setting", "garden"))
    for pid in PETS:
        lines.append(asp.fact("pet", pid))
    for rid in RIBBONS:
        lines.append(asp.fact("ribbon", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(("garden", p, r) for p, r in valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about kindness.")
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--ribbon", choices=RIBBONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    if args.gender and args.name is None:
        pass
    pet = args.pet or rng.choice(list(PETS))
    ribbon = args.ribbon or rng.choice(list(RIBBONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(pet=pet, ribbon=ribbon, name=name, gender=gender, parent=parent)


def _warn_if_severed(world: World, child: Entity, ribbon: Entity) -> None:
    if ribbon.meters.get("severed", 0) >= THRESHOLD:
        world.say(
            f"Then a thorn had a nip, and the {ribbon.label} was cut in two; "
            f"that made the little play thing wobble and droop in view."
        )
        child.memes["worry"] = child.memes.get("worry", 0) + 1


def tell_story(params: StoryParams) -> World:
    pet_cfg = PETS[params.pet]
    ribbon_cfg = RIBBONS[params.ribbon]
    world = World(SETTINGS["garden"])

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    pet = world.add(Entity(id="Pet", kind="character", type=pet_cfg.type, label=pet_cfg.label))
    ribbon = world.add(Entity(id="Ribbon", type="thing", label=ribbon_cfg.label, phrase=ribbon_cfg.phrase))

    child.memes["kindness"] = 1.0
    pet.memes["trust"] = 1.0
    pet.meters["immune"] = 1.0
    ribbon.meters["whole"] = 1.0

    world.say(f"{child.id} was a {params.gender} child with a {child.memes['kindness']:.0f}-bright heart,")
    world.say(
        f"who loved the {pet.label} with {pet_cfg.immune}, and liked to pat the fluff so smart."
    )
    world.say(
        f"The {pet.label} wore {ribbon_cfg.phrase}, like a ribbon that shimmered and shone;"
    )
    world.say(
        f"together they twirled in {world.setting.place}, and the day felt sweet as scone."
    )

    world.para()
    world.say(
        f"One day in {world.setting.place}, a sharp little thorn made a quick little sever;"
    )
    ribbon.meters["severed"] = 1.0
    pet.meters["startled"] = 1.0
    child.memes["sad"] = 1.0
    _warn_if_severed(world, child, ribbon)
    world.say(
        f"the ribbon came loose on one side, and the game stopped cold in the weather."
    )
    world.say(
        f"{params.parent.capitalize()} said, \"No racing now, dear; let's be safe and clever.\""
    )

    world.para()
    child.memes["kindness"] += 1.0
    child.meters["pat"] = child.meters.get("pat", 0.0) + 1.0
    pet.meters["calm"] = pet.meters.get("calm", 0.0) + 1.0
    world.say(
        f"But {child.id} leaned close with a gentle pat, and the {pet.label} felt calm and kind;"
    )
    world.say(
        f"{params.parent} found the {ribbon_cfg.repair_tool}, then tied the ends in line."
    )
    ribbon.meters["severed"] = 0.0
    ribbon.meters["whole"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    world.say(
        f"So the ribbon was mended again, and the little pair ran on in time;"
    )
    world.say(
        f"the {pet.label} stayed immune and snug, and {child.id} laughed in rhyme."
    )

    world.facts.update(
        child=child,
        parent=parent,
        pet=pet,
        ribbon=ribbon,
        pet_cfg=pet_cfg,
        ribbon_cfg=ribbon_cfg,
        resolved=True,
        severed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about kindness, a pat, and a severed ribbon.',
        f"Tell a gentle rhyme where {f['child'].id} gives a kind pat to the {f['pet'].label} after the {f['ribbon'].label} is severed.",
        f'Write a child-friendly story that includes the words "immune", "pat", and "sever".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    pet: Entity = f["pet"]
    ribbon: Entity = f["ribbon"]
    return [
        QAItem(
            question=f"What did {child.id} do to help the {pet.label} feel safe?",
            answer=f"{child.id} gave the {pet.label} a gentle pat and stayed kind when the ribbon was severed.",
        ),
        QAItem(
            question=f"What happened to the {ribbon.label} in the garden?",
            answer=f"A thorn severed the {ribbon.label}, and then the grown-up mended it with care.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the {pet.label}?",
            answer=f"They were happy again, because the ribbon was fixed and the {pet.label} stayed calm and immune.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pet_cfg: Pet = f["pet_cfg"]
    ribbon_cfg: Ribbon = f["ribbon_cfg"]
    return [
        QAItem(
            question="What does immune mean?",
            answer=f"Immune means protected from a certain thing, like how the {pet_cfg.label} is described as {pet_cfg.immune}.",
        ),
        QAItem(
            question="What does it mean to pat something gently?",
            answer="To pat gently means to touch with a soft hand, usually to comfort or show care.",
        ),
        QAItem(
            question="What does sever mean?",
            answer=f"To sever means to cut or split apart, like when a thorn severed the {ribbon_cfg.label}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for pet_id in PETS:
            params = StoryParams(
                pet=pet_id,
                ribbon="red",
                name="Mia",
                gender="girl",
                parent="mother",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
