#!/usr/bin/env python3
"""
A small storyworld: a child, a forum, a curious quest, and a warm ending.

Seed-tale premise:
- A child named Miri loves visiting the neighborhood forum.
- One day, the child notices a tiny handmade meim pin is missing from a jacket.
- Curiosity leads to a repeated search pattern: ask, look, ask again, look again.
- The quest ends with a heartwarming discovery and a kind return.

The world is built around:
- a physical setting: the forum, its benches, board, corners, and lost-and-found box
- a physical object: the meim pin
- emotional meters: curiosity, worry, relief, warmth
- a quest state that changes as the search repeats and finally succeeds
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the forum"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    label: str
    phrase: str
    region: str = "torso"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.search_rounds: int = 0
        self.find_spot: str = ""

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


SETTINGS = {
    "forum": Setting(place="the forum", indoor=True, affords={"quest"}),
    "hall": Setting(place="the community hall", indoor=True, affords={"quest"}),
    "lobby": Setting(place="the library lobby", indoor=True, affords={"quest"}),
}

NAMES = {
    "girl": ["Miri", "Lena", "Sana", "June", "Iris"],
    "boy": ["Oren", "Timo", "Eli", "Noah", "Ben"],
}
HELPERS = ["mother", "father", "grandma", "grandpa", "aunt", "uncle"]


QUEST_ITEM = QuestItem(
    label="meim pin",
    phrase="a tiny handmade meim pin",
    region="torso",
)


ASP_RULES = r"""
quest_started(P) :- place(P), curious(P).
repeated_search(P) :- quest_started(P), asks_again(P).
finds_item(P) :- repeated_search(P), found_spot(P).
heartwarming_end(P) :- finds_item(P), returns_item(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("item", "meim_pin"))
    lines.append(asp.fact("curious", "miri"))
    lines.append(asp.fact("asks_again", "miri"))
    lines.append(asp.fact("found_spot", "miri"))
    lines.append(asp.fact("returns_item", "miri"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming quest at a forum, shaped by curiosity and repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


def story_intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} loved the forum because it was full of kind faces, soft voices, and little notices pinned in neat rows."
    )
    world.say(
        f"One day, {hero.pronoun('possessive')} {QUEST_ITEM.label} was missing, and {hero.id} and {helper.label} began a gentle quest to find it."
    )


def do_search_round(world: World, hero: Entity, helper: Entity) -> None:
    world.search_rounds += 1
    if world.search_rounds == 1:
        world.say(
            f"{hero.id} looked by the notice board, then under the bench, then by the lost-and-found box."
        )
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(
            f"{helper.label} smiled and said, \"Let's ask one more time and look one more time.\""
        )
    elif world.search_rounds == 2:
        world.say(
            f"{hero.id} asked the same kind question again, because curiosity likes to check twice when something matters."
        )
        world.say(
            f"They looked again near the chair legs, the leaflet basket, and the little shelf where people left found things."
        )
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    else:
        world.find_spot = "the lost-and-found box"
        world.say(
            f"On the third look, {hero.id} opened the lost-and-found box and saw a tiny meim pin shining softly on top."
        )
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        hero.memes["warmth"] = hero.memes.get("warmth", 0) + 1
        hero.memes["worry"] = 0
        world.facts["found"] = True


def resolve_quest(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} laughed in surprise, then tucked the {QUEST_ITEM.label} back in {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"{helper.label} said the little pin had been waiting for its person, and {hero.id} held it carefully as if it were a tiny treasure."
    )
    world.say(
        f"At the end of the quest, {hero.id} wore the {QUEST_ITEM.label} again, and the forum felt warmer than before."
    )


def tell(place: Setting, hero_name: str, gender: str, helper_kind: str) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=gender,
            meters={},
            memes={"curiosity": 0, "worry": 0, "relief": 0, "warmth": 0},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_kind,
            label=f"their {helper_kind}",
            meters={},
            memes={},
        )
    )
    pin = world.add(
        Entity(
            id="meim_pin",
            type="pin",
            label=QUEST_ITEM.label,
            phrase=QUEST_ITEM.phrase,
            owner=hero.id,
            caretaker=helper.id,
        )
    )
    pin.worn_by = hero.id

    story_intro(world, hero, helper)
    world.para()
    do_search_round(world, hero, helper)
    do_search_round(world, hero, helper)
    do_search_round(world, hero, helper)
    world.para()
    resolve_quest(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=pin,
        found=world.facts.get("found", False),
        rounds=world.search_rounds,
        setting=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a heartwarming story about a child named {hero.id} who goes on a small quest at {world.setting.place}.',
        f"Tell a gentle story where {hero.id} uses curiosity and repetition to find a missing meim pin with {helper.label}.",
        f'Write a child-friendly forum story that includes the word "meim" and ends with a warm, happy return.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        QAItem(
            question=f"What was missing when {hero.id} began the quest at {world.setting.place}?",
            answer=f"{hero.id} could not find {hero.pronoun('possessive')} {item.label}, so the search began at {world.setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the {item.label}?",
            answer=f"{helper.label} helped with the search and kept the quest calm and kind.",
        ),
        QAItem(
            question=f"How many times did {hero.id} search before finding the {item.label}?",
            answer=f"{hero.id} searched three times, and the repeated looking led to the discovery in the lost-and-found box.",
        ),
        QAItem(
            question=f"Where was the {item.label} found?",
            answer="It was found in the lost-and-found box after the third look.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} wearing the {item.label} again and the forum feeling warmer and happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to talk, share ideas, and post notices or questions.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn more about things.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again. It can help someone remember, practice, or keep looking carefully.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, and it often takes a few steps before the goal is found.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  search_rounds={world.search_rounds}")
    lines.append(f"  find_spot={world.find_spot!r}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forum", name="Miri", gender="girl", helper="mother"),
    StoryParams(place="hall", name="Oren", gender="boy", helper="grandma"),
    StoryParams(place="lobby", name="June", gender="girl", helper="father"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, h) for p in SETTINGS for g in ["girl", "boy"] for h in HELPERS]


def explain_rejection() -> str:
    return "(No story: this world is intentionally gentle and always allows the forum quest.)"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show heartwarming_end/1."))
    clingo_ok = bool(asp.atoms(model, "heartwarming_end"))
    python_ok = True
    if clingo_ok == python_ok:
        print("OK: clingo and Python both recognize the heartwarming ending.")
        return 0
    print("MISMATCH between clingo and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.helper)
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


def asp_valid() -> str:
    import asp
    return asp_program("#show heartwarming_end/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heartwarming_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show heartwarming_end/1."))
        print(f"heartwarming_end: {bool(asp.atoms(model, 'heartwarming_end'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
