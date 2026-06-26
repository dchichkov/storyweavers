#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inhabitant_whelm_deaf_bad_ending_repetition_foreshadowing.py
=============================================================================================================

A small folk-tale storyworld about a lonely inhabitant, a swelling danger,
and warnings that go unheard.

Premise:
- A tiny village has one low cottage near a river.
- Its inhabitant is deaf, kind, and used to relying on written signs and clear gestures.
- The river rises after days of rain.
- The tale uses repetition and foreshadowing as a classical folk-story engine.
- The ending is intentionally bad: the warning comes too late, and the cottage is lost.

The world is simulated with typed entities, physical meters, and emotional memes.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "damage": 0.0, "danger": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "fear": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    river_nearby: bool = False
    hill: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    warning: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.weather_days: int = 0
        self.river_level: float = 0.0
        self.signs_seen: int = 0

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.weather_days = self.weather_days
        w.river_level = self.river_level
        w.signs_seen = self.signs_seen
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "riverside": Place(name="the riverside cottage", river_nearby=True, affords={"tale", "warn"}),
    "hill": Place(name="the hill cottage", hill=True, affords={"tale", "warn"}),
}

WARNINGS = {
    "river": "the river was rising",
    "wind": "the wind kept crying at the door",
    "mud": "the path was turning to mud",
}

TRAITS = ["quiet", "patient", "kind", "lonely", "careful"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"There was once a {hero.traits[0]} inhabitant named {hero.id}, "
        f"who lived by {world.place.name}."
    )
    if hero.memes.get("deaf", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} was deaf, so {hero.pronoun()} watched faces, hands, and written signs closely.")


def foreshadow(world: World) -> None:
    if world.place.river_nearby:
        world.say("Each morning the water had crept a little higher, and the reeds bent lower and lower.")
    else:
        world.say("Each morning the clouds sat heavier over the hill, and the crows kept circling the roof.")
    world.say("The old people said, 'When the third warning comes, the little house must be moved.'")


def repeated_warning(world: World, hero: Entity, warning: str) -> None:
    world.signs_seen += 1
    hero.memes["worry"] += 0.5
    if warning == "river":
        world.river_level += 0.7
    elif warning == "wind":
        world.river_level += 0.2
    else:
        world.river_level += 0.3

    if world.signs_seen == 1:
        world.say("Once, then again, the neighbors waved and pointed toward the door.")
    elif world.signs_seen == 2:
        world.say("Again they came, and again they pointed, slower this time, with wide frightened eyes.")
    else:
        world.say("For the third time they came, with ropes in their hands and urgency in their steps.")

    if hero.memes.get("deaf", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.id} could not hear the words, only see the mouths moving and the hands shaking."
        )
    else:
        world.say(f"{hero.id} heard the warning clearly and looked at the door with concern.")


def ignore_or_react(world: World, hero: Entity) -> None:
    if hero.memes.get("deaf", 0.0) >= THRESHOLD:
        hero.memes["hope"] += 0.3
        world.say(
            f"{hero.id} smiled politely and kept on with the chores, thinking the neighbors only meant to visit."
        )
    else:
        hero.memes["fear"] += 0.7
        world.say(f"{hero.id} hurried to gather the blanket and lamp.")


def flood_or_loss(world: World, hero: Entity) -> None:
    if world.signs_seen >= 3:
        hero.meters["danger"] += 1.5
        world.river_level += 1.0
        world.say(
            "By then the river had swollen to the doorstep, and the water licked the threshold like a hungry tongue."
        )
    if world.river_level >= 2.0:
        hero.meters["wet"] += 1.0
        hero.meters["damage"] += 1.0
        hero.memes["hope"] = 0.0
        hero.memes["fear"] += 1.0
        world.say(
            f"The flood came anyway. It slipped under the door, filled the room, and took the little home apart."
        )


def ending(world: World, hero: Entity) -> None:
    world.para()
    if hero.meters["damage"] >= THRESHOLD:
        world.say(
            f"In the end, {hero.id} stood in cold water with nothing dry left but {hero.pronoun('possessive')} hands."
        )
        world.say(
            "The neighbors rebuilt higher on the hill, but the old cottage stayed behind, broken and empty by the river."
        )
    else:
        world.say(
            f"In the end, {hero.id} managed to reach safety, though the night left a scar on the little place."
        )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="inhabitant",
        traits=[params.trait],
        memes={"worry": 0.0, "hope": 1.0, "fear": 0.0, "relief": 0.0, "deaf": 1.0},
    ))
    helper = world.add(Entity(
        id="Neighbor",
        kind="character",
        type=params.parent,
        label="neighbor",
        memes={"worry": 0.0, "hope": 0.0, "fear": 0.0, "relief": 0.0},
    ))

    world.say("In a small folk-tale village, people said the river listened to no one.")
    introduce(world, hero)
    foreshadow(world)

    world.para()
    repeated_warning(world, hero, params.warning)
    ignore_or_react(world, hero)

    world.para()
    repeated_warning(world, hero, params.warning)
    ignore_or_react(world, hero)

    world.para()
    repeated_warning(world, hero, params.warning)
    world.say(f"{helper.id} grabbed a rope and pointed hard at the hill road.")
    ignore_or_react(world, hero)

    flood_or_loss(world, hero)
    ending(world, hero)

    world.facts.update(
        hero=hero,
        helper=helper,
        warning=params.warning,
        place=place,
        bad_ending=hero.meters["damage"] >= THRESHOLD,
        repeated=world.signs_seen,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a folk tale about an inhabitant named {hero.id} who is deaf and keeps missing repeated warnings.',
        f'Tell a short story where the river rises three times and the ending is bad because the warning is not understood.',
        f'Write a simple tale with foreshadowing, repetition, and a sad ending about a cottage by water.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.traits[0]} inhabitant who lived near {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {hero.id} miss the warning three times?",
            answer=f"{hero.id} missed it because {hero.pronoun()} was deaf, so the words did not reach {hero.pronoun('object')} the usual way.",
        ),
        QAItem(
            question="What happened after the repeated warnings?",
            answer="The river rose too high, the cottage flooded, and the ending was sad because the home was lost.",
        ),
        QAItem(
            question="What was the foreshadowing in the tale?",
            answer="The foreshadowing was the river creeping higher and the old people saying the third warning would matter most.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inhabitant?",
            answer="An inhabitant is a living being that stays in a place and makes it its home.",
        ),
        QAItem(
            question="What does deaf mean?",
            answer="Deaf means a person cannot hear sounds in the usual way.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints about something that will happen later.",
        ),
        QAItem(
            question="What is repetition in a folk tale?",
            answer="Repetition is when a story says or does something again and again to make the pattern easy to notice.",
        ),
        QAItem(
            question="What does it mean when water whelms a house?",
            answer="It means the water rises over it and overwhelms it, so the place can no longer stand safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
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
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.name}")
    lines.append(f"river_level={world.river_level}")
    lines.append(f"signs_seen={world.signs_seen}")
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place can host the river-warning tale and the
% warning actually repeats enough times to make the ending plausible.
repeated(3).

valid_place(P) :- place(P), affords(P, tale), affords(P, warn).
valid_story(P, W) :- valid_place(P), warning(W), repeated(3).

#show valid_place/1.
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.river_nearby:
            lines.append(asp.fact("river_nearby", pid))
        if place.hill:
            lines.append(asp.fact("hill", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    stories = set(asp.atoms(model, "valid_story"))
    python = {(p, w) for p in PLACES for w in WARNINGS if "tale" in PLACES[p].affords and "warn" in PLACES[p].affords}
    if stories == python:
        print(f"OK: clingo gate matches Python gate ({len(stories)} stories).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", sorted(stories))
    print("python:", sorted(python))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: inhabitant, whelm, deaf, repetition, foreshadowing, bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["neighbor", "mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, w) for p in PLACES for w in WARNINGS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.warning:
        combos = [c for c in combos if c[1] == args.warning]
    if not combos:
        raise StoryError("No valid place/warning combination matches the options.")
    place, warning = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mara", "Anya", "Old Tom", "Nell", "Ivo"])
    parent = args.parent or rng.choice(["neighbor", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, warning=warning, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for p, w in stories:
            print(p, w)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PLACES:
            for w in WARNINGS:
                params = StoryParams(place=p, warning=w, name="Mara", parent="neighbor", trait="careful")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
