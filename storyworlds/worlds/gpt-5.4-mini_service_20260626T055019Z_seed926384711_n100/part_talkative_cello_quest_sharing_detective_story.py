#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/part_talkative_cello_quest_sharing_detective_story.py
==============================================================================================================================

A standalone story world for a small detective tale about a quest, sharing,
and a talkative cello part.
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
        female = {"girl", "mother", "mom", "woman", "detective_girl"}
        male = {"boy", "father", "dad", "man", "detective_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    target: str
    clue_word: str
    trail: str
    turn: str
    solution: str
    risk: str
    needed_part: str
    shared_item: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


PLACES = {
    "music_room": Place(id="music_room", label="the music room", mood="quiet", affords={"quest", "sharing"}),
    "hall": Place(id="hall", label="the old hall", mood="echoing", affords={"quest", "sharing"}),
    "library": Place(id="library", label="the library", mood="hushed", affords={"quest", "sharing"}),
}

QUESTS = {
    "missing_part": Quest(
        id="missing_part",
        target="the missing cello part",
        clue_word="part",
        trail="a tiny slip of paper with part numbers on it",
        turn="the clue was tucked inside the cello case",
        solution="the page had been shared and then hidden by accident",
        risk="without the part, the music would sound wrong",
        needed_part="the missing page part",
        shared_item="the music stand",
        tags={"part", "cello", "quest", "sharing"},
    ),
    "talkative_cello": Quest(
        id="talkative_cello",
        target="the talkative cello",
        clue_word="talkative",
        trail="soft words drifting from the cello's body",
        turn="the cello was only talking because a loose peg made it buzz",
        solution="the detective needed to share the sound test with the helper and fix the peg",
        risk="the buzzing hid the real clue",
        needed_part="the loose peg part",
        shared_item="the tuning note",
        tags={"talkative", "cello", "quest", "sharing"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Nora", "Ivy", "Eliya"]
NAMES_BOY = ["Ben", "Leo", "Theo", "Max", "Sam", "Finn"]
TRAITS = ["curious", "brave", "careful", "gentle", "sharp-eyed"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place_id, quest_id) for place_id, place in PLACES.items() for quest_id in QUESTS if {"quest", "sharing"} <= place.affords]


def reasonableness_gate(place: str, quest: str) -> None:
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    if quest not in QUESTS:
        raise StoryError(f"Unknown quest: {quest}")
    if "quest" not in PLACES[place].affords or "sharing" not in PLACES[place].affords:
        raise StoryError("This setting cannot support both the quest and the sharing beat.")
    q = QUESTS[quest]
    if "cello" not in q.tags:
        raise StoryError("This storyworld requires a cello-centered detective mystery.")
    if "part" not in q.tags and "talkative" not in q.tags:
        raise StoryError("The seed requires either the part clue or the talkative cello clue.")


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label="the helper", meters={}, memes={}))
    cello = world.add(Entity(id="Cello", type="cello", label="the cello", phrase="a polished brown cello", meters={}, memes={}))
    part = world.add(Entity(id="Part", type="part", label="part", phrase=quest.needed_part, owner=hero.id, caret
aker=helper.id, meters={}, memes={}))
    stand = world.add(Entity(id="Stand", type="stand", label="music stand", phrase=quest.shared_item, meters={}, memes={}))
    clue = world.add(Entity(id="Clue", type="clue", label="clue", phrase=quest.trail, meters={}, memes={}))

    hero.memes["curiosity"] = 1
    helper.memes["helpfulness"] = 1
    cello.memes["voice"] = 1
    if quest.id == "talkative_cello":
        cello.memes["talkative"] = 1

    world.say(
        f"{hero.id} was a {params.trait} little detective who loved a good Quest."
    )
    world.say(
        f"One quiet afternoon, {hero.id} and {helper.label} went to {place.label}, where a cello waited like a secret."
    )
    world.say(
        f"{hero.id} noticed {quest.trail}, and that made the whole room feel like the start of a mystery."
    )

    world.para()
    world.say(
        f"The detective followed the clue, but {quest.risk}."
    )
    if quest.id == "missing_part":
        world.say(
            f"A page was missing from the music, and without the {part.label}, the tune could not be complete."
        )
        world.say(
            f"{hero.id} asked {helper.label} to share the stand so they could sort the pages together."
        )
        part.meters["lost"] = 1
        stand.memes["shared"] = 1
    else:
        world.say(
            f"The cello sounded chatty, as if it were trying to tell its own side of the story."
        )
        world.say(
            f"{hero.id} shared the listening job with {helper.label} and tapped the cello's side until the buzz gave itself away."
        )
        cello.meters["buzzing"] = 1

    world.para()
    world.say(
        f"At last, {quest.turn}. "
        f"That was the part of the case that changed everything."
    )
    world.say(
        f"{hero.id} and {helper.label} solved it by sharing the answer instead of racing ahead alone."
    )
    world.say(
        f"In the end, {quest.solution}, and the cello could be heard clearly again."
    )
    if quest.id == "missing_part":
        world.say(
            f"{hero.id} tucked {part.phrase} back where it belonged, and the music stand held the pages like a neat little helper."
        )
    else:
        world.say(
            f"{helper.label} fixed the peg, and the cello stopped sounding so talkative and strange."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        cello=cello,
        part=part,
        stand=stand,
        clue=clue,
        quest=quest,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    q: Quest = f["quest"]
    return [
        f'Write a short detective story for a child about a {q.clue_word} clue, a cello, and a Quest.',
        f"Tell a gentle mystery where {hero.id} and {f['helper'].label} solve a {q.id} case by sharing clues.",
        f"Write a simple story that includes the words part, talkative, and cello, and ends with the mystery solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest: Quest = f["quest"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who was the detective in the story at {place.label}?",
            answer=f"It was {hero.id}, a {hero.memes and 'curious' or 'brave'} little detective who led the Quest with {helper.label}.",
        ),
        QAItem(
            question=f"What clue started the mystery about the cello?",
            answer=f"The mystery began with {quest.trail}, which made {hero.id} look closer.",
        ),
        QAItem(
            question="How did the detective and helper solve the case?",
            answer=f"They solved it by sharing the clue work and staying calm until the answer became clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cello?",
            answer="A cello is a large string instrument that people play with a bow, and it makes a deep, warm sound.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to use, give, or think about something together instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a part?",
            answer="A part is one piece of something bigger, like one piece of a machine, a story, or a song.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- mystery(Q).
compatible(P,Q) :- place(P), quest(Q), affords(P,quest), affords(P,sharing), clue_of(Q,part).
compatible(P,Q) :- place(P), quest(Q), affords(P,quest), affords(P,sharing), clue_of(Q,talkative), has(cello,Q).
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("mystery", qid))
        lines.append(asp.fact("clue_of", qid, q.clue_word))
        if "cello" in q.tags:
            lines.append(asp.fact("has", "cello", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about a Quest, Sharing, and a cello.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
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
    if args.place and args.quest:
        reasonableness_gate(args.place, args.quest)
    combos = [
        (p, q) for p, q in combos
        if (args.place is None or p == args.place)
        and (args.quest is None or q == args.quest)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father", "teacher"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params.place, params.quest)
    world = build_world(params)
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


CURATED = [
    StoryParams(place="music_room", quest="missing_part", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="hall", quest="talkative_cello", name="Theo", gender="boy", helper="teacher", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, q in combos:
            print(f"  {p:12} {q}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
