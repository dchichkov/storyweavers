#!/usr/bin/env python3
"""
A small storyworld for a sleepy animal tale with repetition and a bad ending.

The world is built from a tiny source premise:
a sleepy little animal tries to keep going, repeats the same effort, and
eventually loses the thing it wanted because it is too sleepy to manage it.

The prose is intentionally concrete and child-facing, with a clear turn and an
ending image that shows what changed, even though the ending is not happy.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "rabbit", "mouse", "fox", "bear", "dog", "bird"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "tree": Setting(place="the big tree", indoors=False, affords={"climb", "watch"}),
    "barn": Setting(place="the warm barn", indoors=True, affords={"count", "nap"}),
    "porch": Setting(place="the porch", indoors=False, affords={"watch", "count"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb the tree",
        gerund="climbing the tree",
        rush="clamber up again",
        result="slipped back down",
        keyword="sleepy",
        tags={"sleepy", "repetition"},
    ),
    "watch": Activity(
        id="watch",
        verb="watch the fireflies",
        gerund="watching the fireflies",
        rush="look up once more",
        result="missed another blink",
        keyword="sleepy",
        tags={"sleepy", "repetition"},
    ),
    "count": Activity(
        id="count",
        verb="count the stars",
        gerund="counting the stars",
        rush="count them again",
        result="lost track again",
        keyword="sleepy",
        tags={"sleepy", "repetition"},
    ),
    "nap": Activity(
        id="nap",
        verb="take a nap",
        gerund="napping",
        rush="curl up again",
        result="fell asleep at once",
        keyword="sleepy",
        tags={"sleepy"},
    ),
}

PRIZES = {
    "lantern": Prize("lantern", "a little lantern", "lantern", "paws"),
    "berry": Prize("berry", "a red berry snack", "berry", "mouth"),
    "blanket": Prize("blanket", "a soft blanket", "blanket", "body"),
}

NAMES = ["Milo", "Pip", "Nina", "Otis", "Luna", "Toby", "Wren", "Benny"]
ANIMALS = ["rabbit", "kitten", "mouse", "fox", "bear", "dog", "bird"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "nap" and prize != "blanket":
                    continue
                combos.append((place, act, prize))
    return combos


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        meters={"sleepy": 0.0, "tired": 0.0},
        memes={"hope": 1.0, "frustration": 0.0, "sad": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    helper = world.add(Entity(
        id="moon",
        kind="thing",
        type="moon",
        label="the moon",
        meters={"bright": 1.0},
    ))
    world.facts.update(hero=hero, prize=prize, helper=helper, activity=ACTIVITIES[params.activity])
    return world


def _repeat_line(world: World, hero: Entity, act: Activity, prize: Entity, count: int) -> None:
    world.say(f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} eyes were getting heavy.")
    if count == 1:
        world.say(f"{hero.id} tried to {act.rush}, and then {act.result}.")
    else:
        world.say(f"Again {hero.id} tried to {act.rush}, and again {act.result}.")


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero: Entity = world.facts["hero"]
    prize: Entity = world.facts["prize"]
    act: Activity = world.facts["activity"]

    world.say(f"{hero.id} was a little {hero.type} who loved quiet evening games.")
    world.say(f"{hero.id} had {prize.phrase}, and {hero.pronoun('subject')} did not want to put {prize.it()} down.")
    world.para()
    world.say(f"At {world.setting.place}, the air was still and soft.")
    world.say(f"{hero.id} started {act.gerund} with {prize.it()}, then yawned once.")
    hero.meters["sleepy"] += 1
    hero.meters["tired"] += 1

    world.para()
    _repeat_line(world, hero, act, prize, 1)
    hero.meters["sleepy"] += 1
    hero.memes["frustration"] += 1

    _repeat_line(world, hero, act, prize, 2)
    hero.meters["sleepy"] += 1
    hero.meters["tired"] += 1
    hero.memes["frustration"] += 1

    world.say(f"{hero.id} blinked hard, but {hero.pronoun('subject')} still wanted to keep going.")
    world.say(f"Then {hero.id} tried one more time, and {act.result}.")
    hero.meters["sleepy"] += 1
    hero.memes["sad"] += 1

    world.para()
    if params.activity == "nap":
        world.say(f"{hero.id} curled up beside {prize.it()} for a nap.")
        world.say(f"But the nap came too late, and {hero.id} slept through the warm blanket time.")
        hero.memes["sad"] += 1
    else:
        world.say(f"{hero.id} sat down with {prize.it()} and yawned so wide that {prize.it()} slipped away.")
        world.say(f"The little prize rolled off into the dark, and {hero.id} was too sleepy to chase it.")
        hero.memes["sad"] += 2
        prize.meters["lost"] = 1.0

    world.say(f"In the end, {hero.id} lay still at {world.setting.place}, very sleepy and a little sad.")
    world.say(f"The moon shone over {hero.id}, and the game was over for the night.")
    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    return [
        f"Write a short animal story for young children about {hero.id}, who is sleepy and keeps trying to {act.verb}.",
        f"Tell a gentle but sad story where a {hero.type} named {hero.id} repeats the same try again and again and loses {prize.phrase}.",
        f"Write a simple story with the word 'sleepy' that ends with an animal still tired after trying to {act.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    return [
        QAItem(
            question=f"Who is the sleepy animal in the story?",
            answer=f"The sleepy animal is {hero.id}, a little {hero.type} who keeps trying to {act.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep trying to do?",
            answer=f"{hero.id} kept trying to {act.verb}, but {hero.pronoun('subject')} got sleepier each time.",
        ),
        QAItem(
            question=f"What did {hero.id} want to keep with {hero.pronoun('object')}?",
            answer=f"{hero.id} wanted to keep {prize.phrase} with {hero.pronoun('object')} while playing.",
        ),
        QAItem(
            question=f"Why was the ending bad for {hero.id}?",
            answer=(
                f"The ending was bad because {hero.id} became too sleepy to finish the game, "
                f"and {prize.phrase} slipped away before {hero.pronoun('subject')} could save it."
            ),
        ),
        QAItem(
            question=f"What repeated part happened more than once?",
            answer=(
                f"{hero.id} tried to {act.rush} more than once, and each time "
                f"the result was the same: {act.result}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sleepy mean?",
            answer="Sleepy means tired and ready to sleep, so your eyes may feel heavy and you may yawn a lot.",
        ),
        QAItem(
            question="Why might an animal repeat the same try when it is sleepy?",
            answer="A sleepy animal may keep repeating the same try because it is still hoping to finish, even though it is getting slower and clumsier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
sleepy(A) :- character(A), sleepy_level(A,L), L >= 2.
repeating(A) :- tried(A,T), T >= 2.
bad_ending(A) :- sleepy(A), repeating(A).
valid_story(Place, Act, Prize) :- affords(Place, Act), allowed_prize(Act, Prize), bad_ending(Act).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act_id, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", act_id))
        lines.append(asp.fact("keyword", act_id, act.keyword))
        if "sleepy" in act.tags:
            lines.append(asp.fact("sleepy_action", act_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("allowed_prize", "nap", prize_id) if prize_id == "blanket" else "")
    lines.append(asp.fact("character", "hero"))
    lines.append(asp.fact("sleepy_level", "hero", 3))
    lines.append(asp.fact("tried", "hero", 2))
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A sleepy animal story with repetition and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(place="tree", activity="climb", prize="lantern", name="Milo", animal="rabbit"),
    StoryParams(place="porch", activity="watch", prize="berry", name="Pip", animal="kitten"),
    StoryParams(place="barn", activity="nap", prize="blanket", name="Luna", animal="mouse"),
    StoryParams(place="tree", activity="count", prize="lantern", name="Otis", animal="fox"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
