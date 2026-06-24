#!/usr/bin/env python3
"""
storyworlds/worlds/popular_ize_difficulty_liberal_teamwork_happy_ending.py
=========================================================================

A small detective-story world about a missing clue, a hard case, and a team
that solves it with teamwork, liberal thinking, foreshadowing, and a happy
ending.

The seed tale behind this world:
---
A child hears that a "popularize" poster vanished from the community hall.
The hall keeper thinks the theft is hard to understand because the room was
locked, and a note hints that a liberal visitor had asked about the poster
earlier. A young detective follows the foreshadowing signs, works with a
friend, and finds the poster tucked safely in the library display where it can
be shared with everyone. In the end, the team turns a difficult mystery into a
happy ending by setting up a new public display.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "woman", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    place: str
    helps_with: set[str] = field(default_factory=set)
    notable: str = ""


@dataclass
class Mission:
    id: str
    label: str
    difficulty: str
    foreshadow: str
    resolution: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone = World(self.place)
        import copy as _copy

        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
PLACES = {
    "community_hall": Place("community_hall", "the community hall", indoor=True, affords={"search", "display"}),
    "library": Place("library", "the library", indoor=True, affords={"search", "display"}),
    "market": Place("market", "the market", indoor=False, affords={"search"}),
    "courtyard": Place("courtyard", "the courtyard", indoor=False, affords={"search", "display"}),
}

MISSIONS = {
    "popularize_poster": Mission(
        id="popularize_poster",
        label="a popularize poster",
        difficulty="hard to explain",
        foreshadow="a slipped note near the door",
        resolution="a bright public display",
        keyword="popularize",
        tags={"popularize", "poster", "public"},
    ),
    "difficulty_case": Mission(
        id="difficulty_case",
        label="a difficult case",
        difficulty="hard to follow",
        foreshadow="a trail of small clues",
        resolution="a clear answer",
        keyword="difficulty",
        tags={"difficulty", "mystery"},
    ),
    "liberal_notice": Mission(
        id="liberal_notice",
        label="a liberal notice",
        difficulty="hard to pin down",
        foreshadow="a kind request in neat handwriting",
        resolution="a fair and open solution",
        keyword="liberal",
        tags={"liberal", "note", "public"},
    ),
}

CLUES = {
    "note": Clue("note", "a note", "paper", "community_hall", helps_with={"difficulty_case", "liberal_notice"}, notable="it was written in neat, calm letters"),
    "stamp": Clue("stamp", "a library stamp", "ink", "library", helps_with={"popularize_poster"}, notable="it marked where the poster had been sorted"),
    "thread": Clue("thread", "a blue thread", "fiber", "market", helps_with={"difficulty_case"}, notable="it matched the edge of a display cloth"),
    "key": Clue("key", "a spare key", "metal", "community_hall", helps_with={"popularize_poster", "liberal_notice"}, notable="it opened a side cabinet"),
}

# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    detective_name: str
    partner_name: str
    keeper_name: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Reasoning and narration helpers
# -----------------------------------------------------------------------------
def reasonableness_check(place: Place, mission: Mission) -> bool:
    return "search" in place.affords and bool(mission.keyword)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("keyword", mid, mission.keyword))
        for tag in sorted(mission.tags):
            lines.append(asp.fact("tag", mid, tag))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("helps", cid, clue.helps_with and sorted(clue.helps_with)[0] or ""))
    return "\n".join(lines)


ASP_RULES = r"""
% A mission is compatible when the place supports searching.
compatible(P, M) :- affords(P, search), mission(M), keyword(M, _).

% A clue helps a mission when its registry says so.
useful(C, M) :- clue(C), mission(M), helps(C, M).

% A story is good when there is a compatible place and at least one useful clue.
good_story(P, M) :- compatible(P, M), useful(_, M).
"""


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mission = MISSIONS[params.mission]
    world = World(place)

    detective = world.add(Entity(id=params.detective_name, kind="character", type="boy", label=params.detective_name, role="detective"))
    partner = world.add(Entity(id=params.partner_name, kind="character", type="girl", label=params.partner_name, role="partner"))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type="adult", label=params.keeper_name, role="keeper"))

    poster = world.add(Entity(id="poster", type="paper", label="the poster", phrase="the popularize poster", owner=keeper.id, location=place.id))
    note = world.add(Entity(id="note", type="paper", label="the note", owner=keeper.id, location=place.id))
    clue = world.add(Entity(id="clue", type="clue", label="the clue", owner=None, location=place.id))

    world.facts.update(
        detective=detective,
        partner=partner,
        keeper=keeper,
        poster=poster,
        note=note,
        clue=clue,
        mission=mission,
        place=place,
        found=False,
        resolved=False,
    )
    return world


def foreshadow(world: World, mission: Mission) -> None:
    world.say(
        f"Before the case began, {mission.foreshadow} waited by the doorway, as if it wanted to be noticed."
    )


def introduce(world: World, detective: Entity, partner: Entity, keeper: Entity, mission: Mission) -> None:
    world.say(
        f"{detective.id} was a young detective who liked tiny mysteries."
        f" {partner.id} was quick to help, and {keeper.id} watched the room with a worried face."
    )
    world.say(
        f"That day, {keeper.id} said {mission.label} was missing, and everyone agreed it was a difficult case."
    )


def search_scene(world: World, detective: Entity, partner: Entity, mission: Mission) -> str:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    partner.memes["helpful"] = partner.memes.get("helpful", 0) + 1
    clue = next(iter(CLUES.values()))
    world.say(
        f"{detective.id} and {partner.id} searched the room together. {partner.id} checked the tables while {detective.id} studied the floor."
    )
    world.say(
        f"At last, {detective.id} noticed {clue.label} {clue.notable}, and that clue pointed toward the library."
    )
    return clue.id


def trace_to_library(world: World, detective: Entity, partner: Entity, mission: Mission) -> None:
    world.para()
    world.say(
        f"The two friends followed the clue to the library, because the trail looked too careful to be an accident."
    )
    world.say(
        f"There, behind a display board, they found {mission.label} tucked safely where everyone could see it."
    )


def solve_case(world: World, detective: Entity, partner: Entity, keeper: Entity, mission: Mission) -> None:
    detective.memes["pride"] = detective.memes.get("pride", 0) + 1
    partner.memes["joy"] = partner.memes.get("joy", 0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0) + 1
    world.say(
        f"{partner.id} smiled first, and then {detective.id} did too. Together they carried {mission.label} back into the open."
    )
    world.say(
        f"{keeper.id} thanked them, and the team made a new public display so the idea could be shared with everyone."
    )
    world.say(
        f"It was a happy ending: the difficult case became a fair, open answer, and the missing item was no longer hidden."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    mission = world.facts["mission"]
    detective = world.facts["detective"]
    partner = world.facts["partner"]
    keeper = world.facts["keeper"]

    introduce(world, detective, partner, keeper, mission)
    world.para()
    foreshadow(world, mission)
    clue_id = search_scene(world, detective, partner, mission)
    world.facts["found"] = True
    world.facts["clue_id"] = clue_id
    trace_to_library(world, detective, partner, mission)
    world.facts["resolved"] = True
    world.para()
    solve_case(world, detective, partner, keeper, mission)
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        f"Write a detective story set at {place.label} about {mission.label} and a team that solves it.",
        f"Tell a child-friendly mystery where {detective.id} follows foreshadowing and turns a difficult case into a happy ending.",
        f"Write a short story that includes teamwork, a liberal clue, and a poster that gets shared with everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    keeper: Entity = world.facts["keeper"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the difficult case at {place.label}?",
            answer=f"{detective.id} and {partner.id} solved it together, and {keeper.id} was relieved at the end.",
        ),
        QAItem(
            question=f"What clue foreshadowed the answer in the story?",
            answer=f"The clue was the note by the doorway, and it pointed the team toward the library.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the missing {mission.label} was found and put into a public display for everyone.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "popularize": [("What does popularize mean?", "To popularize something means to help more people know about it and like it.")],
    "difficulty": [("What is difficulty?", "Difficulty means something is hard to do or hard to understand.")],
    "liberal": [("What does liberal mean?", "Liberal can mean open-minded and willing to include many people or ideas.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other to reach the same goal.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is a hint that gives a small clue about what will happen later.")],
    "detective": [("What does a detective do?", "A detective looks for clues and solves mysteries.")],
    "happy ending": [("What is a happy ending?", "A happy ending is when a problem gets solved and the story ends well.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    out: list[QAItem] = []
    for key, items in WORLD_KNOWLEDGE.items():
        if key.split()[0] in mission.tags or key in {"teamwork", "foreshadowing", "detective", "happy ending"}:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = set(asp.atoms(model, "good_story"))
    python = {(p, m) for p in PLACES if any(reasonableness_check(PLACES[p], MISSIONS[m]) for m in MISSIONS)}
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("WARN: ASP program produced no shown atoms.")
    return 1


# -----------------------------------------------------------------------------
# Core API
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with teamwork and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--detective-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--keeper-name")
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


NAMES = ["Maya", "Iris", "Lena", "Noah", "Owen", "Ruth", "Eli", "Nia"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    mission = args.mission or rng.choice(list(MISSIONS))
    if not reasonableness_check(PLACES[place], MISSIONS[mission]):
        raise StoryError("This place cannot support a detective search story.")
    detective = args.detective_name or rng.choice([n for n in NAMES if n in {"Maya", "Iris", "Lena", "Noah", "Owen", "Eli", "Nia", "Ruth"}])
    partner = args.partner_name or rng.choice([n for n in NAMES if n != detective])
    keeper = args.keeper_name or rng.choice([n for n in NAMES if n not in {detective, partner}])
    return StoryParams(place=place, mission=mission, detective_name=detective, partner_name=partner, keeper_name=keeper)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"facts: found={world.facts.get('found')} resolved={world.facts.get('resolved')}")
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


CURATED = [
    StoryParams(place="community_hall", mission="popularize_poster", detective_name="Maya", partner_name="Eli", keeper_name="Ruth"),
    StoryParams(place="library", mission="difficulty_case", detective_name="Noah", partner_name="Iris", keeper_name="Lena"),
    StoryParams(place="courtyard", mission="liberal_notice", detective_name="Owen", partner_name="Nia", keeper_name="Maya"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
