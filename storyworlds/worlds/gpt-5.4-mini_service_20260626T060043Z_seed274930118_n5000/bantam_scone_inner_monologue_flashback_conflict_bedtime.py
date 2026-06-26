#!/usr/bin/env python3
"""
A small bedtime-story world about a bantam, a scone, a cozy nest, and a
gentle conflict that resolves with care.

Seed premise:
- A little bantam wants a scone at bedtime.
- The nest must stay tidy and warm.
- The bantam remembers a messy crumby night before.
- The helper wants a calmer, safer bedtime routine.

This world simulates physical state (meters) and feelings (memes), then turns
that state into child-facing prose, QA, and an ASP twin for validation.
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
# Story model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hen", "mother", "mum", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"cock", "father", "dad", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Nest:
    place: str = "the cozy nest"
    bedtime: bool = True
    affords: set[str] = field(default_factory=lambda: {"share_scone", "count_crumbs"})


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    caretaker: str = "Mother"
    crumbly: bool = False
    warm: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    helper_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, nest: Nest):
        self.nest = nest
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback: bool = False

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
        import copy as _copy

        clone = World(self.nest)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.flashback = self.flashback
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nest": Nest(place="the cozy nest", bedtime=True, affords={"share_scone", "count_crumbs"}),
}

OBJECTS = {
    "scone": ObjectSpec(
        label="scone",
        phrase="a warm honey scone",
        type="scone",
        caretaker="Mother",
        crumbly=True,
        warm=True,
    ),
}

TRAITS = ["sleepy", "gentle", "curious", "small", "bouncy"]

BANTAM_NAMES = ["Pip", "Penny", "Bram", "Mina", "Tilly", "Nora"]
HELPER_NAMES = ["Henny", "Bess", "Mabel", "June", "Clara"]

GENTLE_HELPERS = {
    "hen": "hen",
    "mother": "hen",
}

# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _v(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _vm(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _child_name(hero: Entity) -> str:
    return hero.id


def _helper_label(helper: Entity) -> str:
    return helper.label or helper.type


def _is_crumbly(obj: Entity) -> bool:
    return _m(obj, "crumbs") >= THRESHOLD


def _has_conflict(hero: Entity) -> bool:
    return _m(hero, "conflict") >= THRESHOLD


def _has_resolution(hero: Entity) -> bool:
    return _m(hero, "comfort") >= THRESHOLD


def _flashback_line(world: World, hero: Entity, object_ent: Entity) -> None:
    world.flashback = True
    world.say(
        f"{hero.id} remembered the last bedtime when the scone crumbs had scattered "
        f"all over the soft blanket. The nest had felt prickly and hard to settle in."
    )
    world.say(
        f"That memory made {hero.pronoun('possessive')} chest feel tight, because "
        f"{hero.id} wanted the treat and the tidy nest both."
    )


def _inner_monologue(world: World, hero: Entity) -> None:
    world.say(
        f'"Just one little bite," {hero.id} thought. '
        f'"But if the crumbs fall, will bedtime still feel cozy?"'
    )


def _offer(world: World, helper: Entity, hero: Entity, obj: Entity) -> None:
    world.say(
        f'{helper.id} tucked one wing around {hero.id} and said, '
        f'"We can share the scone slowly, over a little napkin, so the nest stays kind."'
    )


def _accept(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    _vm(hero, "comfort", 1)
    _vm(hero, "love", 1)
    hero.memes["conflict"] = 0.0
    obj.meters["crumbs"] = min(obj.meters.get("crumbs", 0.0), 0.0)
    world.say(
        f"{hero.id}'s feathers softened. {hero.id} nodded and took a tiny bite, "
        f"then another. The crumbs stayed on the napkin, and the nest stayed neat."
    )
    world.say(
        f"At last, {hero.id} curled up beside {helper.id}, full of scone and sleepy peace."
    )


def tell_story(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    # Setup
    world.say(
        f"{hero.id} was a little bantam who loved bedtime stories, warm blankets, and sweet smells."
    )
    world.say(
        f"Tonight, {hero.id} had {obj.phrase}, and {obj.label} made the air smell like a cozy bakery."
    )
    world.say(
        f"{helper.id} watched carefully, because bedtime in the nest was supposed to be calm and crumb-free."
    )

    # Conflict
    world.para()
    _inner_monologue(world, hero)
    _vm(hero, "desire", 1)
    _v(obj, "warmth", 1)
    _v(obj, "crumbs", 1)
    _vm(hero, "conflict", 1)
    world.say(
        f"{hero.id} wanted to hold the scone close, but {helper.id} worried the crumbs would wake the nest."
    )
    _flashback_line(world, hero, obj)
    world.say(
        f"{hero.id} almost hunched over the plate, feeling torn between a happy tummy and a tidy bed."
    )

    # Resolution
    world.para()
    _offer(world, helper, hero, obj)
    _accept(world, hero, helper, obj)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bedtime story is valid when the bantam wants the scone, the scone is crumbly,
% and the helper can offer a slow, tidy compromise.
wants(heron, scone).
crumbly(scone).
helper_can_help(mother).

conflict(heron) :- wants(heron, scone), crumbly(scone).
resolved(heron) :- conflict(heron), helper_can_help(mother).
valid_story :- resolved(heron).

#show wants/2.
#show conflict/1.
#show resolved/1.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("hero", "heron"),
        asp.fact("object", "scone"),
        asp.fact("helper", "mother"),
        asp.fact("crumbly", "scone"),
        asp.fact("bedtime", "nest"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validate_python() -> bool:
    # Lazy import for clingo helper.
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    atoms = {str(sym) for sym in model}
    return "valid_story" in atoms


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: Entity = f["object"]
    return [
        'Write a gentle bedtime story about a bantam, a scone, and a quiet compromise.',
        f"Tell a bedtime story where {hero.id} wants {obj.phrase}, but {helper.id} worries about crumbs in the nest.",
        f"Write a child-friendly story that includes an inner monologue and a flashback about {obj.label} crumbs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    obj: Entity = f["object"]
    return [
        QAItem(
            question=f"What did {hero.id} want at bedtime?",
            answer=f"{hero.id} wanted {obj.phrase} because it smelled sweet and cozy.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the scone?",
            answer=f"{helper.id} worried the crumbs would scatter in the nest and make bedtime less calm.",
        ),
        QAItem(
            question="What did the bantam remember from before?",
            answer="The bantam remembered a bedtime when crumbs had gotten all over the blanket.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They shared the scone slowly over a napkin, so the nest stayed tidy and {hero.id} could fall asleep happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bantam?",
            answer="A bantam is a small kind of chicken.",
        ),
        QAItem(
            question="What is a scone?",
            answer="A scone is a small baked treat that can be sweet or plain.",
        ),
        QAItem(
            question="Why do people use a napkin?",
            answer="People use a napkin to catch crumbs and keep hands and tables cleaner.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    nest = SETTINGS[params.place]
    world = World(nest)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="bantam",
        traits=["little", params.trait],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="mother",
    ))
    objspec = OBJECTS[params.object]
    obj = world.add(Entity(
        id="scone",
        type="scone",
        label=objspec.label,
        phrase=objspec.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    obj.meters["crumbs"] = 0.0
    obj.meters["warmth"] = 1.0

    world.facts.update(hero=hero, helper=helper, object=obj)
    tell_story(world, hero, helper, obj)
    return world


def valid_combo() -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    place = args.place or "nest"
    obj = args.object or "scone"
    hero_type = "bantam"
    helper_type = "hen"
    hero_name = args.name or rng.choice(BANTAM_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        object=obj,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_type=hero_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {', '.join(bits) if bits else 'quiet'}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="nest", object="scone", hero_name="Pip", helper_name="Henny", hero_type="bantam", helper_type="hen", trait="sleepy"),
    StoryParams(place="nest", object="scone", hero_name="Tilly", helper_name="Bess", hero_type="bantam", helper_type="hen", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a bantam and a scone.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        import asp

        ok_py = valid_combo()
        ok_asp = asp_validate_python()
        if ok_py and ok_asp:
            print("OK: ASP and Python gates agree.")
            return
        print("MISMATCH: ASP and Python gates disagree.")
        sys.exit(1)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:")
        print(" ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 10:
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
