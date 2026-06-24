#!/usr/bin/env python3
"""
storyworlds/worlds/spunky_nipple_reconciliation_bedtime_story.py
===============================================================

A tiny bedtime-story world about a spunky child, a missing bottle nipple,
and a gentle reconciliation before sleep.

The domain is intentionally small:
- a child with a bright, spunky mood
- a baby who needs a bottle nipple at bedtime
- a parent who notices the problem
- a soft apology, a returned object, and a calm ending image

The prose is driven by the world state, not a frozen paragraph template.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    in_hand_of: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    place: str = "the nursery"
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ChildConfig:
    name: str
    gender: str
    trait: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str = "shelf"
    plural: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def clone(self) -> "World":
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", cozy=True, affords={"bedtime"}),
    "bedroom": Setting(place="the bedroom", cozy=True, affords={"bedtime"}),
    "hall": Setting(place="the hallway", cozy=False, affords={"bedtime"}),
}

CHILD_TRAITS = ["spunky", "curious", "cheerful", "lively", "brave"]

NAMES_GIRL = ["Mia", "Nora", "Ivy", "Lena", "Ada"]
NAMES_BOY = ["Noah", "Theo", "Eli", "Max", "Ben"]

BEDTIME_ITEMS = {
    "bottle_nipple": Prize(
        label="bottle nipple",
        phrase="a clean bottle nipple",
        type="bottle_nipple",
        location="counter",
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a soft blanket",
        type="blanket",
        location="chair",
    ),
    "night_light": Prize(
        label="night light",
        phrase="a tiny night light",
        type="night_light",
        location="shelf",
    ),
}

ASP_RULES = r"""
#show valid/2.

valid(P, I) :- place(P), item(I), needs_bedtime(I), place_cozy(P).
valid(P, I) :- place(P), item(I), item_small(I), place_cozy(P).

% A bottle nipple matters at bedtime because the baby needs it to drink calmly.
needs_bedtime(bottle_nipple).
item_small(bottle_nipple).
item_small(blanket).
item_small(night_light).

% Only cozy places are reasonable for the reconciliation bedtime story.
place_cozy(nursery).
place_cozy(bedroom).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.cozy:
            lines.append(asp.fact("place_cozy", pid))
    for iid in BEDTIME_ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("needs_bedtime", "bottle_nipple"))
    lines.append(asp.fact("item_small", "bottle_nipple"))
    lines.append(asp.fact("item_small", "blanket"))
    lines.append(asp.fact("item_small", "night_light"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime reconciliation story world with a spunky child and a bottle nipple."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=CHILD_TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or "spunky"
    return StoryParams(name=name, gender=gender, trait=trait, place=place)


def _do_bedtime(world: World, child: Entity, baby: Entity, parent: Entity, item: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    child.memes["spunky"] = child.memes.get("spunky", 0) + 1
    world.say(
        f"{child.id} was a {child.memes.get('trait', 'spunky')} little {child.type} who did everything with a bounce."
    )
    world.say(
        f"At bedtime, {child.id} noticed the {item.label} on the counter and picked {item.it()} up to look at {item.it()}."
    )
    child.in_hand_of = child.id
    item.in_hand_of = child.id
    child.meters["curiosity"] = child.meters.get("curiosity", 0) + 1
    world.para()
    world.say(
        f"{baby.id} made a tiny sleepy sound, because {baby.pronoun('possessive')} bottle was waiting for {baby.pronoun('object')}, and the {item.label} was missing."
    )
    world.say(
        f"{parent.id} looked around the room and said, \"We need that {item.label} back so {baby.id} can rest.\""
    )
    child.memes["defiance"] = child.memes.get("defiance", 0) + 1
    world.say(
        f"{child.id} clutched {item.it()} for a moment, then frowned. {child.pronoun().capitalize()} wanted to keep playing, but {baby.id} looked tired."
    )
    world.para()
    child.memes["conflict"] = 1
    world.say(
        f"Then {child.id} took a breath and held the {item.label} out to {parent.id}. \"I'm sorry,\" {child.pronoun()} said. \"I can share it.\""
    )
    item.in_hand_of = parent.id
    child.memes["conflict"] = 0
    child.memes["love"] = child.memes.get("love", 0) + 1
    parent.memes["warmth"] = parent.memes.get("warmth", 0) + 1
    world.say(
        f"{parent.id} smiled, and the room felt soft again. {parent.id} gave the {item.label} back where it belonged, and {baby.id} drank спокойно and quietly."
    )
    world.say(
        f"{child.id} tucked {baby.id}'s blanket in and climbed into bed too, feeling proud that {child.pronoun()} had fixed the problem."
    )


def tell(setting: Setting, child_cfg: ChildConfig) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_cfg.name,
        kind="character",
        type=child_cfg.gender,
        traits=[child_cfg.trait, "spunky"],
        meters={"curiosity": 0.0},
        memes={"spunky": 1.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="mom"))
    baby = world.add(Entity(id="Baby", kind="character", type="girl", label="baby sister"))
    item = world.add(Entity(
        id="nipple",
        kind="thing",
        type="bottle_nipple",
        label="bottle nipple",
        phrase="a clean bottle nipple",
        location="counter",
        owner=baby.id,
        caretaker=parent.id,
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a soft blanket",
        owner=baby.id,
        caretaker=parent.id,
        location="crib",
    ))

    world.say(
        f"{child.id} was a {child_cfg.trait} little {child_cfg.gender} who lived in {setting.place} and liked bedtime stories."
    )
    world.say(
        f"{baby.id} had a favorite bottle, and the little bottle nipple had to be clean and ready before sleep."
    )
    world.para()
    _do_bedtime(world, child, baby, parent, item)
    world.para()
    world.say(
        f"By the end, the nursery was quiet, the blanket was tucked in, and {child.id} was yawning beside the crib."
    )
    world.facts.update(
        child=child,
        parent=parent,
        baby=baby,
        item=item,
        blanket=blanket,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f'Write a bedtime story about a {child_cfg_phrase(child)} and a missing {item.label} that ends in reconciliation.',
        f"Tell a gentle story where {child.id} is spunky at bedtime, but learns to share the {item.label}.",
        f'Write a short bedtime story that includes the word "spunky" and the word "nipple" in a child-friendly way.',
    ]


def child_cfg_phrase(child: Entity) -> str:
    trait = child.traits[0] if child.traits else "spunky"
    return f"{trait} little {child.type}"


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    baby = f["baby"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a {child_cfg_phrase(child)} who had to make a bedtime choice about the {item.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label} want the {item.label} back?",
            answer=f"{parent.label.capitalize()} wanted the {item.label} back because {baby.id} needed it for the bottle at bedtime.",
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=f"{child.id} apologized, gave the {item.label} back, and the family settled down peacefully for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word spunky mean?",
            answer="Spunky means lively, brave, and full of energy.",
        ),
        QAItem(
            question="What is a bottle nipple for?",
            answer="A bottle nipple is the soft part a baby drinks through on a bottle.",
        ),
        QAItem(
            question="Why is bedtime usually calm?",
            answer="Bedtime is usually calm because people slow down, get cozy, and rest for the night.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.in_hand_of:
            bits.append(f"in_hand_of={e.in_hand_of}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8} {e.type:14}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def validate_params(params: StoryParams) -> None:
    if params.trait != "spunky":
        raise StoryError("This world is designed around the seed word spunky; keep trait=spunky.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy.")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    setting = SETTINGS[params.place]
    world = tell(setting, ChildConfig(name=params.name, gender=params.gender, trait=params.trait))
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


def resolve_all() -> list[StoryParams]:
    out: list[StoryParams] = []
    for place in SETTINGS:
        for gender, names in [("girl", NAMES_GIRL), ("boy", NAMES_BOY)]:
            out.append(StoryParams(name=names[0], gender=gender, trait="spunky", place=place))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        atoms = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(atoms)} valid (place, item) combos:")
        for place, item in atoms:
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in resolve_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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


def asp_facts_wrapper() -> str:
    return asp_facts()


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(p, i) for p in SETTINGS for i in BEDTIME_ITEMS if SETTINGS[p].cozy}
    clingo_set = set(asp_valid_pairs())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python ({len(python_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


if __name__ == "__main__":
    main()
