#!/usr/bin/env python3
"""
A standalone storyworld for a tiny nursery-rhyme quest about a lost fiddle,
foreshadowed clues, and teamwork.

The world model is small and simulated:
- a child hero wants to bring music back to a little place
- a fiddle is missing
- scattered hints foreshadow where it went
- helpers team up to fetch it
- the ending proves the change by returning the music and the style of play

The script supports:
- random generation with reproducible seeds
- QA output
- JSON output
- trace output
- ASP parity verification
- a show-ASP mode
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    team: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    scent: str
    sound: str
    clue: str


@dataclass
class Quest:
    id: str
    goal: str
    missing: str
    method: str
    ending: str
    keyword: str = "fiddle"
    style: str = "nursery rhyme"


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []

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

    def trace(self) -> str:
        lines = [f"place={self.place.name!r}"]
        for ent in self.entities.values():
            bits = []
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.team:
                bits.append(f"team={ent.team}")
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            lines.append(f"{ent.id}: {ent.type} " + " ".join(bits))
        lines.append(f"steps={self.steps}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "green": Place(
        id="green",
        name="the green",
        scent="sweet grass",
        sound="a hush of wind",
        clue="a ribbon of red cloth",
    ),
    "lantern_lane": Place(
        id="lantern_lane",
        name="Lantern Lane",
        scent="warm bread",
        sound="tiny bell chimes",
        clue="a shoe-print in chalk",
    ),
    "brook": Place(
        id="brook",
        name="the brook",
        scent="wet reeds",
        sound="water whispering",
        clue="a bright blue feather",
    ),
}

QUESTS = {
    "find_fiddle": Quest(
        id="find_fiddle",
        goal="bring music back",
        missing="the fiddle",
        method="follow the clues and work together",
        ending="the song was bright again",
        keyword="fiddle",
        style="nursery rhyme",
    ),
    "style_show": Quest(
        id="style_show",
        goal="save the song style",
        missing="the fiddle",
        method="mix careful steps with kind help",
        ending="the merry style lived again",
        keyword="style",
        style="nursery rhyme",
    ),
}

HERO_NAMES = ["Molly", "Poppy", "Elsie", "Nell", "Tilly", "Annie"]
HELPER_NAMES = ["Ben", "Wren", "Tom", "Milo", "Rose", "Jude"]


# ---------------------------------------------------------------------------
# Rhythm / prose helpers
# ---------------------------------------------------------------------------
def intro_line(hero: Entity, quest: Quest) -> str:
    return f"Little {hero.id} loved a bright old tune, and wished to {quest.goal}."


def foreshadow_line(place: Place) -> str:
    return f"On the way, {place.clue} hinted that something small and special was near."


def teamwork_line(hero: Entity, helper: Entity) -> str:
    return f"{hero.id} and {helper.id} did not rush alone; they held hands and shared the search."


def ending_line(hero: Entity, helper: Entity, quest: Quest) -> str:
    return (
        f"{hero.id} found the {quest.missing}, and {helper.id} helped carry it home, "
        f"so {quest.ending}."
    )


def nursery_refrain(place: Place) -> str:
    return f"{place.sound} went the world, and {place.scent} rode the air."


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def run_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")

    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="hero",
        location="home",
        memes={"hope": 1.0, "worry": 0.2},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="helper",
        location="home",
        memes={"kindness": 1.0},
    ))
    fiddle = world.add(Entity(
        id="fiddle",
        kind="thing",
        type="fiddle",
        label="fiddle",
        phrase="a little fiddle with a bright bow",
        owner=hero.id,
        location=place.id,
        meters={"gleam": 1.0},
    ))

    # Act 1: setup and foreshadowing
    world.say(intro_line(hero, quest))
    world.say(f"The {quest.missing} was missing, and nobody knew yet where it had gone.")
    world.say(nursery_refrain(place))
    world.para()

    # Act 2: clues and teamwork
    hero.memes["hope"] += 0.5
    helper.memes["kindness"] += 0.5
    world.say(foreshadow_line(place))
    world.say(teamwork_line(hero, helper))
    world.steps.extend(["look", "listen", "share"])
    world.say(f"{hero.id} looked for a small sign, and {helper.id} listened for a hidden tune.")
    world.say(f"Together they followed the clue to {place.name}.")
    world.para()

    # Turn: the missing fiddle is found by cooperation
    fiddle.location = "with_heroes"
    world.steps.append("find")
    world.say(f"A soft sparkle showed the {quest.missing} tucked where the clue had promised.")
    world.say(f"{hero.id} reached first, but {helper.id} steadied the box so it would not tumble.")
    world.say(ending_line(hero, helper, quest))
    world.say(f"At last, the {quest.style} style of music danced through the little place again.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "fiddle": fiddle,
        "quest": quest,
        "place": place,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    return [
        f"Write a nursery-rhyme style story about {hero.id} who goes on a quest at {place.name} to find a fiddle.",
        f"Tell a gentle story where {hero.id} and {helper.id} use teamwork and clues to bring back the missing fiddle.",
        f"Write a short children’s story with foreshadowing, a lost fiddle, and a happy ending at {place.name}.",
        f"Make the style feel like a nursery rhyme while the characters solve a small quest together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {quest.goal} by finding the missing fiddle.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They used teamwork, followed the clue, and looked together at {place.name}.",
        ),
        QAItem(
            question="What was the foreshadowing clue?",
            answer=f"The story foreshadowed the ending with {place.clue}, which pointed toward the hidden fiddle.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The fiddle was found, and the music style became lively and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fiddle?",
            answer="A fiddle is a small stringed instrument that people can play with a bow to make music.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something well.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints about what might happen later.",
        ),
        QAItem(
            question="What is a nursery rhyme style?",
            answer="A nursery rhyme style sounds gentle, rhythmic, and playful, with simple words and a sing-song feel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
quest(Q) :- quest_fact(Q).

resolved(P, Q) :- place_fact(P), quest_fact(Q), clue(P, _), teamwork(Q).
valid_story(P, Q) :- resolved(P, Q).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        lines.append(asp.fact("clue", pid, p.clue))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_fact", qid))
        lines.append(asp.fact("teamwork", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_pairs = set(asp.atoms(model, "valid_story"))
    py_pairs = {(p, q) for p in PLACES for q in QUESTS}
    if asp_pairs == py_pairs:
        print(f"OK: ASP and Python agree on {len(py_pairs)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_pairs - py_pairs:
        print("Only in ASP:", sorted(asp_pairs - py_pairs))
    if py_pairs - asp_pairs:
        print("Only in Python:", sorted(py_pairs - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme quest about a lost fiddle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--helper-type", choices=["girl", "boy"], dest="helper_type")
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        quest=quest,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = run_story(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="green", quest="find_fiddle", hero_name="Molly", hero_type="girl", helper_name="Ben", helper_type="boy"),
    StoryParams(place="lantern_lane", quest="style_show", hero_name="Poppy", hero_type="girl", helper_name="Wren", helper_type="girl"),
    StoryParams(place="brook", quest="find_fiddle", hero_name="Tilly", hero_type="girl", helper_name="Tom", helper_type="boy"),
]


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
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for place, quest in pairs:
            print(f"{place} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} on quest {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
