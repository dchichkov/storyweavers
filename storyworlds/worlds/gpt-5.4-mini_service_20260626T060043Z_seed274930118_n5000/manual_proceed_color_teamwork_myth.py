#!/usr/bin/env python3
"""
storyworlds/worlds/manual_proceed_color_teamwork_myth.py
========================================================

A small mythic story world about a shared manual, a careful proceeding, and
the colors that return when helpers work together.

Premise:
- A shrine or story-stone has lost its color.
- A manual gives the proper sequence for the remedy.
- The work cannot be done by one person alone; teamwork is the turning point.

The world is intentionally narrow so the stories stay coherent:
a few roles, a few places, a few objects, and one central task.
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
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
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
        female = {"girl", "woman", "sister", "mother", "priestess"}
        male = {"boy", "man", "brother", "father", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    sacred: bool = False
    shelter: bool = False


@dataclass
class Manual:
    id: str
    label: str
    steps: list[str]
    requires_teamwork: bool = True
    color_key: str = "color"


@dataclass
class Pigment:
    id: str
    label: str
    color: str
    shines: str
    can_mix: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    manual: str
    pigment: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "temple": Place("temple", "the temple hall", sacred=True),
    "courtyard": Place("courtyard", "the sunlit courtyard", sacred=False),
    "shore": Place("shore", "the sea-shore shrine", sacred=True),
}

MANUALS = {
    "ritual": Manual(
        id="ritual",
        label="the old manual of restoration",
        steps=["gather the bowls", "mix the color", "proceed in order", "lift the brush together"],
        requires_teamwork=True,
        color_key="color",
    ),
    "mosaic": Manual(
        id="mosaic",
        label="the manual of the broken mosaic",
        steps=["sort the stones", "share the pattern", "proceed carefully", "press the pieces into place"],
        requires_teamwork=True,
        color_key="color",
    ),
}

PIGMENTS = {
    "red": Pigment("red", "red ochre", "red", "warm like embers"),
    "blue": Pigment("blue", "blue lapis", "blue", "cool like deep water"),
    "gold": Pigment("gold", "gold dust", "gold", "bright like sunrise"),
}

NAMES = {
    "hero": ["Ari", "Nara", "Soren", "Mina", "Tavi", "Iria"],
    "helper": ["Belen", "Kio", "Rami", "Luma", "Oren", "Sela"],
}
TRAITS = ["brave", "steady", "curious", "gentle", "patient", "bright"]


# ---------------------------------------------------------------------------
# Story gate / reasoning
# ---------------------------------------------------------------------------

def manual_needs_teamwork(manual: Manual) -> bool:
    return manual.requires_teamwork


def is_reasonable(place: Place, manual: Manual, pigment: Pigment) -> bool:
    # The myth needs a place where a shared restoration makes sense.
    return place.sacred and manual_needs_teamwork(manual) and pigment.can_mix


def explain_rejection(place: Place, manual: Manual, pigment: Pigment) -> str:
    if not place.sacred:
        return "(No story: the task needs a sacred place, where restoring lost color feels like a real mythic duty.)"
    if not manual.requires_teamwork:
        return "(No story: this manual would not need teamwork, so there would be no shared turning point.)"
    if not pigment.can_mix:
        return "(No story: that color cannot be mixed into the restoration.)"
    return "(No story: this combination is not reasonable for the myth.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place is suitable when it is sacred.
suitable_place(P) :- sacred(P).

% A manual is suitable when it requires teamwork.
suitable_manual(M) :- teamwork_manual(M).

% A pigment is suitable when it can be mixed.
suitable_pigment(G) :- mixable(G).

% A complete story exists when all three are suitable.
valid_story(P, M, G) :- suitable_place(P), suitable_manual(M), suitable_pigment(G).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
        if place.shelter:
            lines.append(asp.fact("shelter", pid))
    for mid, manual in MANUALS.items():
        lines.append(asp.fact("manual", mid))
        if manual.requires_teamwork:
            lines.append(asp.fact("teamwork_manual", mid))
        for step in manual.steps:
            lines.append(asp.fact("step", mid, step))
    for gid, pigment in PIGMENTS.items():
        lines.append(asp.fact("pigment", gid))
        lines.append(asp.fact("mixable", gid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(
        (p, m, g)
        for p, place in PLACES.items()
        for m, manual in MANUALS.items()
        for g, pigment in PIGMENTS.items()
        if is_reasonable(place, manual, pigment)
    )
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid story triples).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(py - cl))
    print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def maybe_team_up(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.say(
        f"{hero.id} knew the work could not be done alone. "
        f"{helper.id} came beside {hero.pronoun('object')}, and the two of them began to think as one."
    )


def open_manual(world: World, manual: Manual) -> None:
    world.say(
        f"They opened {manual.label}, and the pages told them to proceed in order."
    )


def gather_color(world: World, pigment: Pigment) -> None:
    world.say(
        f"In a small bowl, they gathered {pigment.label}, shining {pigment.shines}."
    )


def proceed_steps(world: World, manual: Manual, hero: Entity, helper: Entity, pigment: Pigment) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    helper.memes["resolve"] = helper.memes.get("resolve", 0) + 1
    world.say(
        f"First they followed the manual and proceeded step by step: "
        f"gathering the bowls, mixing the color, and lifting the brush together."
    )
    world.say(
        f"Because {hero.id} held the bowl while {helper.id} steadied the ladder, the color did not spill."
    )
    world.facts["proceeded"] = True
    world.facts["color"] = pigment.color


def restore_myth(world: World, hero: Entity, helper: Entity, pigment: Pigment) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    helper.memes["joy"] = helper.memes.get("joy", 0) + 2
    world.say(
        f"At last the wall drank in {pigment.label}, and the faded sign blazed with new life."
    )
    world.say(
        f"The shrine looked older than the hills and brighter than sunrise, as if the day itself had remembered its name."
    )


def tell(place: Place, manual: Manual, pigment: Pigment, hero_name: str, helper_name: str,
         hero_type: str = "girl", helper_type: str = "boy") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "steady"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["little", "bright"]))
    plaque = world.add(Entity(id="plaque", kind="thing", type="plaque", label="the color-plaque", phrase="a faded color-plaque"))
    world.facts.update(hero=hero, helper=helper, manual=manual, pigment=pigment, place=place, plaque=plaque)

    world.say(
        f"In {place.label}, {hero.id} found a fading sacred sign and knew it was no ordinary stain."
    )
    world.say(
        f"{hero.id} carried {manual.label}, a careful manual for when old things must be made new."
    )
    world.para()
    maybe_team_up(world, hero, helper)
    open_manual(world, manual)
    gather_color(world, pigment)
    world.para()
    proceed_steps(world, manual, hero, helper, pigment)
    restore_myth(world, hero, helper, pigment)

    world.facts["ended"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    manual = f["manual"]
    pigment = f["pigment"]
    place = f["place"]
    return [
        f"Write a short myth about {hero.id} and {helper.id} using {manual.label} to restore color at {place.label}.",
        f"Tell a child-friendly legend where two helpers proceed together and bring back {pigment.label}.",
        f"Write a small teamwork story that includes a manual, the word 'proceed', and a return of color.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    manual: Manual = f["manual"]
    pigment: Pigment = f["pigment"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who worked together in the myth at {place.label}?",
            answer=f"{hero.id} and {helper.id} worked together as a team to restore the sacred color.",
        ),
        QAItem(
            question=f"What did they use to know how to proceed?",
            answer=f"They used {manual.label}, which told them to proceed step by step.",
        ),
        QAItem(
            question=f"What color did they bring back?",
            answer=f"They brought back {pigment.label}, and the old sign shone again.",
        ),
        QAItem(
            question=f"Why did the work need teamwork?",
            answer=(
                f"The task needed teamwork because the manual said to proceed in order, "
                f"with one helper holding things steady while the other mixed and painted."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    manual: Manual = f["manual"]
    pigment: Pigment = f["pigment"]
    return [
        QAItem(
            question="What is a manual?",
            answer="A manual is a guide that tells people how to do a task in the right order.",
        ),
        QAItem(
            question="What does proceed mean?",
            answer="Proceed means to move forward and continue with the next step.",
        ),
        QAItem(
            question="Why can color matter in a story?",
            answer="Color can show life, beauty, and whether something has been restored or left faded.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and do a job together.",
        ),
        QAItem(
            question=f"What kind of color was {pigment.label}?",
            answer=f"{pigment.label.capitalize()} was a shining {pigment.color} color that looked {pigment.shines}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic teamwork story world about a manual, proceeding, and color.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--manual", choices=MANUALS.keys())
    ap.add_argument("--pigment", choices=PIGMENTS.keys())
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
    place = args.place or rng.choice(list(PLACES.keys()))
    manual = args.manual or rng.choice(list(MANUALS.keys()))
    pigment = args.pigment or rng.choice(list(PIGMENTS.keys()))
    if not is_reasonable(PLACES[place], MANUALS[manual], PIGMENTS[pigment]):
        raise StoryError(explain_rejection(PLACES[place], MANUALS[manual], PIGMENTS[pigment]))
    hero = args.hero or rng.choice(NAMES["hero"])
    helper = args.helper or rng.choice(NAMES["helper"])
    return StoryParams(place=place, hero=hero, helper=helper, manual=manual, pigment=pigment)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MANUALS[params.manual],
        PIGMENTS[params.pigment],
        params.hero,
        params.helper,
    )
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if bits:
                print(f"{e.id}: " + " ".join(bits))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def asp_verify_command() -> int:
    return asp_verify()


def asp_list() -> None:
    triples = asp_valid_stories()
    print(f"{len(triples)} valid story combinations:\n")
    for p, m, g in triples:
        print(f"  {p}  {m}  {g}")


def asp_show() -> None:
    print(asp_program())


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        asp_show()
        return
    if args.verify:
        sys.exit(asp_verify_command())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for m in MANUALS:
                for g in PIGMENTS:
                    if is_reasonable(PLACES[p], MANUALS[m], PIGMENTS[g]):
                        params = StoryParams(place=p, hero="Ari", helper="Belen", manual=m, pigment=g)
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
