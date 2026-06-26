#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tuna_transformation_rhyme_rhyming_story.py
=================================================================================

A standalone storyworld for a tiny rhyming transformation tale about tuna.

Seed tale idea:
---
A little child found a plain tuna tin in a bright kitchen and wished it could
become something fun for lunch. The grown-up said it would need a careful rhyme
and a little mixing to change safely. So the child spoke a silly rhyme, the tuna
swirled and shimmered, and it transformed into a cheerful tuna salad snack.

The storyworld models:
- a child with desire and delight,
- a tuna object with shape, freshness, and "tuna-ness",
- a rhyme spell that can transform tuna into a better lunch form,
- a simple resolution where the new lunch is shared.

The prose is authored from simulated world state rather than from a fixed
template with swapped nouns.
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
# Core data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    forms: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    source_form: str
    target_form: str
    rhyme_word: str
    rhyme_line: str
    helper_item: str
    result_phrase: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"rhyme", "transform"}),
    "picnic": Setting(place="the picnic table", affords={"rhyme", "transform"}),
    "pantry": Setting(place="the pantry", affords={"rhyme", "transform"}),
}

TRANSFORMATIONS = {
    "tuna_to_salad": Transformation(
        id="tuna_to_salad",
        source_form="plain tuna",
        target_form="tuna salad",
        rhyme_word="moon",
        rhyme_line="Tuna, tuna, spin and swoon, turn bright and tasty by the moon!",
        helper_item="bowl",
        result_phrase="a cheerful tuna salad sandwich filling",
        sparkle="silver swirls",
        tags={"tuna", "rhyme", "transform"},
    ),
    "tuna_to_melt": Transformation(
        id="tuna_to_melt",
        source_form="plain tuna",
        target_form="tuna melt",
        rhyme_word="toast",
        rhyme_line="Tuna, tuna, warm and boast, turn into a melty toast!",
        helper_item="pan",
        result_phrase="a warm tuna melt",
        sparkle="golden steam",
        tags={"tuna", "rhyme", "transform"},
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Theo", "Ava", "Finn"]
TRAITS = ["curious", "cheerful", "spirited", "gentle", "playful"]


@dataclass
class StoryParams:
    place: str
    transformation: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
class TunaWorld(World):
    pass


def _do_rhyme(world: TunaWorld, child: Entity, trans: Transformation) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f'{child.id} took a breath and said, "{trans.rhyme_line}"'
    )
    world.say(
        f"The {trans.sparkle} began to dance around the tuna."
    )


def _do_transform(world: TunaWorld, tuna: Entity, trans: Transformation) -> None:
    sig = ("transform", tuna.id, trans.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    tuna.forms.discard(trans.source_form)
    tuna.forms.add(trans.target_form)
    tuna.meters["freshness"] = min(1.0, tuna.meters.get("freshness", 0.0) + 0.4)
    tuna.meters["made_ready"] = 1.0
    world.say(
        f"With one last twirl, the tuna changed from plain to {trans.target_form}."
    )


def tell(
    setting: Setting,
    trans: Transformation,
    hero_name: str,
    hero_type: str,
    hero_traits: list[str],
    parent_type: str,
) -> TunaWorld:
    world = TunaWorld(setting=setting)

    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        forms={"child"},
        memes={"hope": 1.0, "joy": 0.0, "wish": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        forms={"grownup"},
        memes={"calm": 1.0},
    ))
    tuna = world.add(Entity(
        id="Tuna",
        kind="thing",
        type="tuna",
        label="tuna",
        phrase="plain tuna",
        owner=child.id,
        forms={trans.source_form},
        meters={"freshness": 0.6, "ready": 0.0},
        memes={"plain": 1.0},
    ))
    helper = world.add(Entity(
        id=trans.helper_item.title(),
        kind="thing",
        type=trans.helper_item,
        label=trans.helper_item,
        phrase=f"a little {trans.helper_item}",
        owner=child.id,
        forms={trans.helper_item},
    ))

    # Act 1: setup
    world.say(
        f"{child.id} was a {hero_traits[0]} little {hero_type} who liked rhyme-time in {setting.place}."
    )
    world.say(
        f"On the counter sat {tuna.phrase}, and {child.id} wanted it to become something nicer for lunch."
    )
    world.say(
        f"{parent.label_word if hasattr(parent, 'label_word') else parent.label} smiled and said the change would need a careful rhyme and a helper {helper.label}."
    )

    # Act 2: tension
    world.para()
    world.say(
        f"{child.id} felt the wish grow bigger and bigger, because plain tuna seemed too plain for the bright day."
    )
    world.say(
        f"So {child.id} washed {helper.label} clean, set it ready, and looked at the tuna with hopeful eyes."
    )

    # Act 3: rhyme and change
    world.para()
    _do_rhyme(world, child, trans)
    _do_transform(world, tuna, trans)
    world.say(
        f"At last, {tuna.label} was not plain anymore; it was {trans.result_phrase}."
    )
    world.say(
        f"{child.id} grinned, because the new lunch smelled right and the tiny sparkle was gone."
    )
    world.say(
        f"Then {child.id} and {parent.label_word if hasattr(parent, 'label_word') else 'the parent'} shared the {trans.target_form}, and the kitchen felt cozy and warm."
    )

    world.facts.update(
        child=child,
        parent=parent,
        tuna=tuna,
        helper=helper,
        transformation=trans,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tid, trans in TRANSFORMATIONS.items():
            if "rhyme" in setting.affords and "transform" in setting.affords and "tuna" in trans.tags:
                combos.append((place, tid))
    return combos


ASP_RULES = r"""
valid(Place, T) :- setting(Place), transformation(T), affords(Place, rhyme), affords(Place, transform), tuna_transformation(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, trans in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        if "tuna" in trans.tags:
            lines.append(asp.fact("tuna_transformation", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: TunaWorld) -> list[str]:
    f = world.facts
    child = f["child"]
    trans = f["transformation"]
    return [
        f'Write a short rhyming story for a child named {child.id} about tuna and a magic change.',
        f'Help {child.id} make plain tuna turn into {trans.target_form} with a rhyme and a happy ending.',
        f'Write a gentle kitchen story where tuna changes form after a child says a silly rhyme.',
    ]


def story_qa(world: TunaWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    tuna = f["tuna"]
    trans = f["transformation"]
    return [
        QAItem(
            question=f"What did {child.id} want the tuna to become?",
            answer=f"{child.id} wanted the tuna to become {trans.target_form}, because plain tuna felt too plain.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the change?",
            answer=f"{parent.label} helped by reminding {child.id} that the change needed a careful rhyme and a helper {f['helper'].label}.",
        ),
        QAItem(
            question=f"What happened after the rhyme was spoken?",
            answer=f"The tuna changed from plain tuna into {trans.result_phrase}, and {child.id} smiled at the new lunch.",
        ),
    ]


def world_knowledge_qa(world: TunaWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is tuna?",
            answer="Tuna is a fish that people also eat as food, often packed in a can or mixed into lunch dishes.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word or line that sounds like another word or line at the end, like moon and spoon.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one form into another form.",
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


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming tuna transformation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.transformation:
        combos = [c for c in combos if c[1] == args.transformation]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, transformation = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, transformation=transformation, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TRANSFORMATIONS[params.transformation],
        params.name,
        params.gender,
        [params.trait, "kind"],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: TunaWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.forms:
            bits.append(f"forms={sorted(e.forms)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for place, trans in combos:
            print(f"  {place:10} {trans}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, trans in valid_combos():
            params = StoryParams(
                place=place,
                transformation=trans,
                name=random.choice(HERO_NAMES),
                gender="girl",
                parent="mother",
                trait="curious",
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
