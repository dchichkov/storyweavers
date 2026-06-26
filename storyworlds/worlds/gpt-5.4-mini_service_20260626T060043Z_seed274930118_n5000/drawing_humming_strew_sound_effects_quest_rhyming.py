#!/usr/bin/env python3
"""
Story world: a Rhyming Story about drawing, humming, and a small quest with sound effects.

This world simulates a child who wants to draw a picture, but must first complete a tiny
quest to gather and strew the right art pieces in the right place. The story turns on
sound effects, a little rhyme, and the emotional shift from stuck to delighted.
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
# Core model
# ---------------------------------------------------------------------------
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    task: str
    gerund: str
    sound: str
    rhyme: str
    result: str
    keyword: str
    requires: set[str] = field(default_factory=set)
    mess: str = "scattered"


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "studio": Place(name="the studio", indoors=True, affords={"draw"}),
    "porch": Place(name="the porch", indoors=False, affords={"draw"}),
    "classroom": Place(name="the classroom", indoors=True, affords={"draw"}),
    "table": Place(name="the kitchen table", indoors=True, affords={"draw"}),
}

QUESTS = {
    "crayon_trail": Quest(
        id="crayon_trail",
        task="find the lost crayons",
        gerund="hunting for the crayons",
        sound="scribble-scrabble",
        rhyme="crayons away, then back to play",
        result="all lined up in a bright row",
        keyword="crayon",
        requires={"crayon", "paper"},
    ),
    "paper_stack": Quest(
        id="paper_stack",
        task="stack the paper pages",
        gerund="stacking the paper pages",
        sound="flip-flap",
        rhyme="paper neat, ready to greet",
        result="stacked into a tidy pile",
        keyword="paper",
        requires={"paper", "pencil"},
    ),
    "sparkle_boxes": Quest(
        id="sparkle_boxes",
        task="gather the sparkle boxes",
        gerund="gathering the sparkle boxes",
        sound="clink-clank",
        rhyme="boxes bright, snug and light",
        result="strewed into a shiny corner",
        keyword="sparkle",
        requires={"sparkle", "marker"},
    ),
    "color_bundles": Quest(
        id="color_bundles",
        task="collect the color bundles",
        gerund="collecting the color bundles",
        sound="rumble-rum",
        rhyme="colors near, drawing clear",
        result="spread out beside the page",
        keyword="color",
        requires={"color", "brush"},
    ),
}

PRIZES = {
    "paper": Prize(label="paper", phrase="a fresh sheet of paper", region="hands"),
    "markers": Prize(label="markers", phrase="a box of bright markers", region="hands", plural=True),
    "crayons": Prize(label="crayons", phrase="a little bundle of crayons", region="hands", plural=True),
    "stickers": Prize(label="stickers", phrase="a pouch of shiny stickers", region="hands", plural=True),
}

HELPERS = {
    "mom": ("mother", "Mom"),
    "dad": ("father", "Dad"),
    "aunt": ("aunt", "Aunt June"),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Owen"]
TRAITS = ["cheerful", "curious", "bouncy", "gentle", "spry"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is reasonable when the place affords drawing and the prize fits the quest.
draw_story(P, Q, R) :- place(P), affords(P, draw), quest(Q), prize(R), quest_needs(Q, R), helper(H), helper_ok(H).

#show draw_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for r in sorted(q.requires):
            lines.append(asp.fact("quest_needs", qid, r))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_ok", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show draw_story/3."))
    return sorted(set(asp.atoms(model, "draw_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, p in PLACES.items():
        if "draw" not in p.affords:
            continue
        for qid, q in QUESTS.items():
            for rid, prize in PRIZES.items():
                if prize.region == "hands":
                    combos.append((place_id, qid, rid))
    return combos


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
# Story shaping
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved drawing and humming soft little tunes."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {quest.task}, and {helper.label} was nearby with a smile."
    )
    world.say(
        f"On the table sat {prize.phrase}, waiting for a picture to begin."
    )


def setup_rhythm(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} hummed, “{quest.rhyme},” and tapped a tiny beat: "
        f"tick-tick, tap-tap, flip-flip-flap."
    )


def quest_problem(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    if quest.id == "crayon_trail":
        world.say(
            f"But the crayons were nowhere near the page. They had been strewed under a pillow, behind a book, and by the rug."
        )
    elif quest.id == "paper_stack":
        world.say(
            f"But the paper pages were mixed up and strewed in a wobbly heap."
        )
    elif quest.id == "sparkle_boxes":
        world.say(
            f"But the sparkle boxes had been strewed all around the room, and nobody could find the shiny corner."
        )
    else:
        world.say(
            f"But the color bundles were strewed from chair to chair, and the drawing space looked lonely."
        )
    world.say(
        f"{helper.label} said, “First the quest, then the sketch.”"
    )


def do_quest(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1
    if quest.id == "crayon_trail":
        world.say(f"{hero.id} went looking with a soft {quest.sound}: scribble-scrabble, under-chair and behind-door.")
        world.say(f"{helper.label} helped with a gentle shake, and soon the crayons were {quest.result}.")
    elif quest.id == "paper_stack":
        world.say(f"{hero.id} gathered pages with a quick {quest.sound}: flip-flap, lift-lift.")
        world.say(f"{helper.label} straightened the edges, and soon the paper was {quest.result}.")
    elif quest.id == "sparkle_boxes":
        world.say(f"{hero.id} followed the bright {quest.sound}: clink-clank, search-search.")
        world.say(f"{helper.label} pointed to the shelves, and soon the sparkle boxes were {quest.result}.")
    else:
        world.say(f"{hero.id} gathered the colors with a rolling {quest.sound}: rumble-rum, hum-hum.")
        world.say(f"{helper.label} held the tray, and soon the color bundles were {quest.result}.")
    prize.meters["ready"] = 1


def resolve(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"Then {hero.id} sat down to draw. {hero.pronoun().capitalize()} hummed, “{quest.rhyme},” and the pencil went zip-zip-zing."
    )
    world.say(
        f"With {prize.phrase} ready at hand, {hero.id} drew a happy picture, and the room felt bright and warm."
    )
    world.say(
        f"{helper.label} laughed at the finished page, where the little lines looked like music."
    )


def tell(place: Place, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=HELPERS[helper_name][0], label=HELPERS[helper_name][1]))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural))
    world.facts.update(hero=hero, helper=helper, quest=quest, prize=prize, place=place)

    introduce(world, hero, helper, quest, prize)
    world.para()
    setup_rhythm(world, hero, quest)
    quest_problem(world, hero, helper, quest, prize)
    world.para()
    do_quest(world, hero, helper, quest, prize)
    resolve(world, hero, helper, quest, prize)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize"]
    place = f["place"].name
    return [
        f'Write a rhyming story for a small child about drawing at {place}, with humming and a little quest.',
        f"Tell a story where {hero.id} wants to {quest.task} but must first gather {prize.phrase} and hear sound effects.",
        f'Create a short, child-friendly rhyming tale that includes "{quest.keyword}", humming, and a happy drawing ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    prize = f["prize"]
    place = f["place"].name
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {quest.task} and make a drawing with {prize.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the quest?",
            answer=f"{helper.label} helped {hero.id}, so the little quest could be finished with a smile.",
        ),
        QAItem(
            question=f"What sound did the story use while {hero.id} searched?",
            answer=f"The story used {quest.sound}, along with humming and little beat sounds.",
        ),
        QAItem(
            question=f"What changed after the quest was done?",
            answer=f"After the quest, the {prize.label} was ready, and {hero.id} could draw happily instead of feeling stuck.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "draw": [
        QAItem(
            question="What do people use drawing for?",
            answer="People use drawing to make pictures, tell stories, and show ideas with lines and colors.",
        )
    ],
    "humming": [
        QAItem(
            question="What is humming?",
            answer="Humming is making a soft musical sound with your voice while keeping your lips mostly closed.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a small adventure where someone looks for something, solves a problem, or finishes a mission.",
        )
    ],
    "sound effects": [
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make actions feel lively, so readers can almost hear the clinks, taps, and scritches.",
        )
    ],
    "rhyming": [
        QAItem(
            question="What does it mean when a story rhymes?",
            answer="A rhyming story uses words that sound alike at the end, like cat and hat, to make the story sing a little.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["draw"],
        *WORLD_KNOWLEDGE["humming"],
        *WORLD_KNOWLEDGE["quest"],
        *WORLD_KNOWLEDGE["sound effects"],
        *WORLD_KNOWLEDGE["rhyming"],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Serialization / tracing
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="studio", quest="crayon_trail", prize="crayons", name="Lily", gender="girl", helper="mom"),
    StoryParams(place="classroom", quest="paper_stack", prize="paper", name="Theo", gender="boy", helper="dad"),
    StoryParams(place="table", quest="sparkle_boxes", prize="markers", name="Mina", gender="girl", helper="aunt"),
    StoryParams(place="porch", quest="color_bundles", prize="stickers", name="Ben", gender="boy", helper="mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about drawing, humming, and a tiny quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, params.helper)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show draw_story/3."))
    return sorted(set(asp.atoms(model, "draw_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show draw_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, prize) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
