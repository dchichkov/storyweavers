#!/usr/bin/env python3
"""
storyworlds/worlds/jowl_quest_slice_of_life.py
==============================================

A tiny slice-of-life story world built from the seed words:
- jowl
- Quest

Premise:
A child and a small dog go on a gentle quest to find a lost charm or snack
that matters to the child. Along the way, the dog's floppy jowl gets messy,
and a parent helps turn the search into a calm, ordinary success.

This world keeps the scale domestic and concrete: a room, a yard, a path, a
small task, a little worry, and a happy ending image that proves something
changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "pet"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    verb: str
    gerund: str
    search_spot: str
    clue: str
    trouble: str
    resolution: str
    mess: str
    emotional_note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    place: str
    plural: bool = False
    precious: bool = True


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", indoors=True, allows={"search", "snack"}),
    "garden": Place("garden", "the garden path", indoors=False, allows={"search"}),
    "porch": Place("porch", "the porch", indoors=False, allows={"search", "snack"}),
}

QUESTS = {
    "find-ball": Quest(
        id="find-ball",
        name="ball quest",
        verb="find the red ball",
        gerund="looking for the red ball",
        search_spot="under the bench",
        clue="a little paw-print trail",
        trouble="the ball rolled into a wet patch",
        resolution="the ball was waiting under the bench",
        mess="muddy",
        emotional_note="hopeful",
        tags={"dog", "ball", "mud"},
    ),
    "find-biscuit": Quest(
        id="find-biscuit",
        name="biscuit quest",
        verb="find the missing biscuit tin",
        gerund="searching for the biscuit tin",
        search_spot="by the pantry door",
        clue="a crumb line on the floor",
        trouble="the biscuit tin had slid behind a chair",
        resolution="the tin was tucked safely behind the chair",
        mess="dusty",
        emotional_note="curious",
        tags={"snack", "kitchen", "crumbs"},
    ),
    "find-key": Quest(
        id="find-key",
        name="key quest",
        verb="find the small house key",
        gerund="hunting for the small house key",
        search_spot="near the shoes",
        clue="a jingling sound near the mat",
        trouble="the key had slipped under a coat",
        resolution="the key was caught in a coat sleeve",
        mess="dusty",
        emotional_note="calm",
        tags={"key", "coat", "home"},
    ),
}

PRIZES = {
    "ball": Prize("ball", "a red ball", "the red ball", "floor"),
    "biscuit": Prize("biscuit", "a tin of biscuits", "the biscuit tin", "kitchen"),
    "key": Prize("key", "a small house key", "the small house key", "porch"),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava"],
    "boy": ["Leo", "Finn", "Noah", "Theo"],
}
PARENTS = ["mother", "father"]


class ReasonableGate:
    @staticmethod
    def valid_combo(place: Place, quest: Quest, prize: Prize) -> bool:
        if prize.place == "kitchen" and not place.indoors:
            return False
        if quest.id == "find-biscuit" and place.id not in {"kitchen", "porch"}:
            return False
        if quest.id == "find-ball" and place.id not in {"garden", "porch"}:
            return False
        if quest.id == "find-key" and place.id not in {"kitchen", "porch"}:
            return False
        return True


ASP_RULES = r"""
#show valid/3.

valid(P,Q,R) :- place(P), quest(Q), prize(R), allowed(P,Q), fits(Q,R).

% A place is allowed when the quest can plausibly happen there.
allowed(kitchen, find-biscuit).
allowed(porch, find-biscuit).
allowed(garden, find-ball).
allowed(porch, find-ball).
allowed(kitchen, find-key).
allowed(porch, find-key).

% A prize fits the quest when the clue and ending make sense.
fits(find-ball, ball).
fits(find-biscuit, biscuit).
fits(find-key, key).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.allows):
            lines.append(asp.fact("supports", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("located", rid, r.place))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for rid, prize in PRIZES.items():
                if ReasonableGate.valid_combo(place, quest, prize):
                    out.append((pid, qid, rid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life quest storyworld with a jowl-sized problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
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


def _reject_reason(place: Place, quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: {quest.name} does not fit naturally at {place.label} with {prize.label}. "
        f"Try a place and prize that match the search.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        if args.place and args.quest and args.prize:
            raise StoryError(_reject_reason(PLACES[args.place], QUESTS[args.quest], PRIZES[args.prize]))
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent)


def _start(world: World, child: Entity, parent: Entity, pet: Entity, quest: Quest, prize: Prize) -> None:
    world.say(f"{child.id} was a small {child.type} with a big idea for a little quest.")
    world.say(f"{child.pronoun().capitalize()} wanted to {quest.verb}, and {pet.id} trotted along with a floppy jowl and bright eyes.")
    world.say(f"At home, {child.pronoun('possessive')} {parent.type} had set aside {prize.phrase} because it mattered to the whole day.")


def _turn(world: World, child: Entity, parent: Entity, pet: Entity, quest: Quest, prize: Prize) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.para()
    world.say(f"One day, they went to {world.place.label} for the quest.")
    world.say(f"Then {pet.id} sniffed near {quest.search_spot}, where there was {quest.clue}.")
    world.say(f"But {quest.trouble}, and that made {child.id} pause.")
    if quest.mess == "muddy":
        pet.meters["muddy"] = pet.meters.get("muddy", 0) + 1
        world.say(f"{pet.id}'s jowl brushed a damp patch, and its fur got a little muddy.")
    else:
        pet.meters["dusty"] = pet.meters.get("dusty", 0) + 1
        world.say(f"{pet.id}'s jowl nudged a dusty corner, and its whiskers looked a little gray.")


def _resolve(world: World, child: Entity, parent: Entity, pet: Entity, quest: Quest, prize: Prize) -> None:
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.para()
    world.say(f"{parent.id} smiled and pointed to the right spot.")
    world.say(f"Together they looked where the clue led, and {quest.resolution}.")
    world.say(f"{child.id} found {prize.phrase}, and {pet.id} sat close by with a proud, messy jowl.")
    world.say(f"By the end, the little quest felt complete, and the room was calm again.")


def _trace_world(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f"Write a short slice-of-life story about {child.id} on a quest to {quest.verb}.",
        f"Tell a gentle everyday story where a small dog with a jowl helps {child.id} find {prize.phrase}.",
        f"Write a simple story about a household quest, a clue, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, pet, quest, prize = f["child"], f["parent"], f["pet"], f["quest"], f["prize"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do?",
            answer=f"{child.id} was trying to {quest.verb}.",
        ),
        QAItem(
            question=f"Who went along on the quest with {child.id}?",
            answer=f"{pet.id} went along too, with a floppy jowl and a happy, curious nose.",
        ),
        QAItem(
            question=f"What did they find at the end?",
            answer=f"They found {prize.phrase} after following the clue with {parent.id}'s help.",
        ),
        QAItem(
            question=f"Why did the quest feel a little tricky?",
            answer=f"It felt tricky because {quest.trouble}, so everyone had to slow down and look carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a trip or search to find something or solve a small problem."),
        QAItem(question="What is a jowl?", answer="A jowl is the loose skin or cheek area on the side of an animal's face, like a dog or a pig."),
        QAItem(question="What does a clue do?", answer="A clue is a small hint that helps someone know where to look next."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, label=params.parent))
    pet = world.add(Entity(id="Milo", kind="pet", type="dog", label="Milo"))
    prize_ent = world.add(Entity(id=prize.id, kind="thing", type="object", label=prize.label, phrase=prize.phrase, owner=child.id, caregiver=parent.id, plural=prize.plural))
    world.facts.update(child=child, parent=parent, pet=pet, quest=quest, prize=prize_ent, place=place)

    _start(world, child, parent, pet, quest, prize)
    _turn(world, child, parent, pet, quest, prize)
    _resolve(world, child, parent, pet, quest, prize)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(_trace_world(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="garden", quest="find-ball", prize="ball", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="kitchen", quest="find-biscuit", prize="biscuit", name="Leo", gender="boy", parent="father"),
    StoryParams(place="porch", quest="find-key", prize="key", name="Nora", gender="girl", parent="mother"),
]


def explain_rejection(place: Place, quest: Quest, prize: Prize) -> str:
    return _reject_reason(place, quest, prize)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
