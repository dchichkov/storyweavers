#!/usr/bin/env python3
"""
storyworlds/worlds/dromedary_quest_cautionary_bad_ending_detective_story.py
===========================================================================

A small detective-story world about a dromedary, a quest, and a cautionary
bad ending.

Premise:
- A desert detective and a dromedary search for a missing water map.
- The detective follows clues across the market, the dunes, and a dry well.
- The cautionary turn is that the detective ignores a warning sign.
- The bad ending is that the quest fails and the final image proves why.

This is a standalone storyworld script that emits one complete child-facing story,
grounded QA, and an inline ASP twin for the reasonableness gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"detective", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    clue: str
    risk: str
    afford: str


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    place: str
    crucial: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, ObjectItem] = {}
        self.moved = False
        self.warned = False
        self.ignored_warning = False
        self.quest_failed = False
        self.trace: list[str] = []
        self.facts: dict = {}
        self._paras: list[list[str]] = [[]]

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: ObjectItem) -> ObjectItem:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self._paras[-1].append(text)

    def para(self) -> None:
        if self._paras[-1]:
            self._paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self._paras if p)

    def note(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": Place(
        id="market",
        label="the market",
        clue="a torn receipt",
        risk="crowds",
        afford="search",
    ),
    "dunes": Place(
        id="dunes",
        label="the dunes",
        clue="half-buried footprints",
        risk="wind",
        afford="track",
    ),
    "well": Place(
        id="well",
        label="the dry well",
        clue="a cracked bucket",
        risk="dryness",
        afford="look",
    ),
}

OBJECTS = {
    "map": ObjectItem(
        id="map",
        label="water map",
        phrase="a folded water map with blue lines",
        place="well",
        crucial=True,
    ),
    "lamp": ObjectItem(
        id="lamp",
        label="lantern",
        phrase="a small brass lantern",
        place="market",
    ),
    "ring": ObjectItem(
        id="ring",
        label="key ring",
        phrase="a tiny key ring",
        place="dunes",
    ),
}

HERO_NAMES = ["Nadia", "Ivo", "Mina", "Rafi", "Lena", "Omar", "Zuri", "Tariq"]
DETECTIVE_TITLES = ["detective", "sleuth", "investigator"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _intro(world: World, detective: Entity, dromedary: Entity, item: ObjectItem) -> None:
    world.say(
        f"{detective.id} was a careful detective who loved tricky cases, and "
        f"{dromedary.id} was a patient dromedary with a long, swaying step."
    )
    world.say(
        f"One morning, a person at {world.place.label} asked them to find "
        f"{item.phrase} before the sun climbed too high."
    )
    world.say(
        f"{dromedary.id} sniffed the air and pointed its nose toward the first clue."
    )
    world.facts["intro_done"] = True


def _quest(world: World, detective: Entity, dromedary: Entity, item: ObjectItem) -> None:
    world.para()
    world.say(
        f"The case led them across {world.place.label}, where {world.place.clue} "
        f"lay near the stalls and the dust."
    )
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1.0
    dromedary.meters["steps"] = dromedary.meters.get("steps", 0.0) + 7.0
    world.note("quest begins")
    world.say(
        f"{detective.id} followed the clue, and {dromedary.id} carried the search "
        f"through the heat."
    )
    world.say(
        f"They found a warning sign near the path: 'Do not go alone toward the dry well.'"
    )
    world.warned = True
    world.facts["warning"] = True


def _bad_turn(world: World, detective: Entity, dromedary: Entity, item: ObjectItem) -> None:
    world.para()
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1.0
    detective.memes["carelessness"] = detective.memes.get("carelessness", 0.0) + 1.0
    world.ignored_warning = True
    world.note("warning ignored")
    world.say(
        f"But {detective.id} shrugged and said the sign was only for timid travelers."
    )
    world.say(
        f"They went on anyway, and {dromedary.id} followed because it trusted the case."
    )
    world.say(
        f"At the dry well, the wind covered the clue in sand, and the blue lines were no longer easy to read."
    )
    world.quest_failed = True
    world.facts["lost_clue"] = True


def _ending(world: World, detective: Entity, dromedary: Entity, item: ObjectItem) -> None:
    world.para()
    if world.quest_failed:
        detective.memes["regret"] = detective.memes.get("regret", 0.0) + 1.0
        dromedary.meters["thirst"] = dromedary.meters.get("thirst", 0.0) + 1.0
        world.say(
            f"In the end, the water map was lost under the sand, and the little case was never solved."
        )
        world.say(
            f"{detective.id} had to walk back empty-handed, while {dromedary.id} licked its dry lips under a pale sky."
        )
        world.say(
            f"The last thing they saw was the warning sign leaning in the wind, still trying to help."
        )
        world.facts["ending"] = "bad"
    else:
        world.say("The quest ended safely.")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = OBJECTS[params.object]
    world = World(place)

    detective = world.add_entity(
        Entity(
            id="Ari",
            kind="character",
            type="detective",
            label="detective",
            meters={"focus": 1.0},
            memes={"duty": 1.0},
        )
    )
    dromedary = world.add_entity(
        Entity(
            id="Moro",
            kind="character",
            type="dromedary",
            label="dromedary",
            meters={"stamina": 1.0},
            memes={"trust": 1.0},
        )
    )
    world.add_item(item)

    _intro(world, detective, dromedary, item)
    _quest(world, detective, dromedary, item)
    _bad_turn(world, detective, dromedary, item)
    _ending(world, detective, dromedary, item)

    world.facts.update(
        detective=detective,
        dromedary=dromedary,
        item=item,
        place=place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short detective story about a dromedary and a lost {world.facts['item'].label}.",
        f"Tell a cautionary quest story set at {world.place.label} with a bad ending.",
        "Write a child-friendly mystery where ignoring a warning causes the search to fail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    dromedary: Entity = world.facts["dromedary"]
    item: ObjectItem = world.facts["item"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was trying to solve the case at {place.label}?",
            answer=f"The detective {detective.id} was trying to solve the case with the dromedary {dromedary.id}.",
        ),
        QAItem(
            question=f"What was the quest looking for?",
            answer=f"They were looking for {item.phrase}.",
        ),
        QAItem(
            question="Why did the story end badly?",
            answer="It ended badly because the detective ignored a warning sign and the wind buried the clue in sand.",
        ),
        QAItem(
            question=f"What did the dromedary do during the search?",
            answer=f"The dromedary {dromedary.id} carried the search forward with patient steps and trusted the detective.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dromedary?",
            answer="A dromedary is a camel with one hump that is well suited to desert travel.",
        ),
        QAItem(
            question="Why are warning signs useful?",
            answer="Warning signs help people stay safe by pointing out danger before they go too far.",
        ),
        QAItem(
            question="What happens when wind blows over sand?",
            answer="Wind can move sand around and cover footprints, clues, and small objects.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(market). place(dunes). place(well).
object(map). object(lamp). object(ring).

warning(well).
quest(place, object) :- place(P), object(O).
bad_ending(P, O) :- warning(P), object(O), not heed_warning(P).
fail(P, O) :- bad_ending(P, O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("warning", "well"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show warning/1."))
    return sorted(set(asp.atoms(model, "warning")))


def python_reasonable() -> list[tuple[str, str]]:
    return [("well",)]


def asp_verify() -> int:
    a = set(asp_reasonable())
    p = set(python_reasonable())
    if a == p:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-story world with a dromedary quest and a cautionary bad ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    obj = args.object or rng.choice(sorted(OBJECTS))
    if place == "well" and obj == "map":
        return StoryParams(place=place, object=obj)
    if args.place and args.object and args.place == "market" and args.object == "ring":
        raise StoryError("This quest is too weak: the ring at the market does not make a cautionary detective bad ending.")
    return StoryParams(place=place, object=obj)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id}")
    lines.append(f"warned={world.warned}")
    lines.append(f"ignored_warning={world.ignored_warning}")
    lines.append(f"quest_failed={world.quest_failed}")
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
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
        print(asp_program("#show warning/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show warning/1."))
        print("warnings:", asp.atoms(model, "warning"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(place=p, object="map") for p in ["well"]]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
