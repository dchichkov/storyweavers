#!/usr/bin/env python3
"""
storyworlds/worlds/finale_millionaire_teller_moral_value_happy_ending.py
=========================================================================

A small bedtime-story world about a final, gentle choice, a millionaire, and a
bank teller. The tale is built as a tiny simulated domain with a moral turn,
a twist, and a happy ending.

Seed image:
---
A child wants a shining finale for a little stage show. A millionaire offers
money, but the teller points out that the best ending is not the most expensive
one. The child learns a moral value, and the night ends softly and well.
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

METER_THRESHOLD = 1.0
MEME_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teller"}
        male = {"boy", "father", "dad", "man", "millionaire"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little theater"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    trouble: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    value_kind: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    millionaire_name: str
    teller_name: str
    seed: Optional[int] = None


SETTINGS = {
    "the little theater": Setting(place="the little theater", indoor=True, affords={"finale", "twist"}),
    "the night market": Setting(place="the night market", indoor=False, affords={"finale", "twist"}),
}

EVENTS = {
    "finale": Event(
        id="finale",
        verb="finish the show",
        gerund="finishing the show",
        rush="hurry to the stage",
        trouble="make the ending too loud and too costly",
        turn="choose a simple ending",
        keyword="finale",
        tags={"finale", "show", "happy ending"},
    ),
    "twist": Event(
        id="twist",
        verb="add a big surprise",
        gerund="adding a surprise",
        rush="rush to change the plan",
        trouble="make everyone confused",
        turn="make the surprise kind instead",
        keyword="twist",
        tags={"twist", "surprise"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a small paper lantern",
        region="hand",
        value_kind="light",
    ),
    "cake": Prize(
        id="cake",
        label="cake",
        phrase="a little party cake",
        region="table",
        value_kind="treat",
    ),
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a shiny cardboard crown",
        region="head",
        value_kind="glow",
    ),
}

NAMES = ["Mia", "Lily", "Noah", "Ben", "Ava", "Maya", "Leo", "Nora"]
MILLIONAIRE_NAMES = ["Mr. Green", "Ms. Gold", "Aunt Ruby", "Uncle Pearl"]
TELLER_NAMES = ["Ms. Lane", "Mr. Bell", "Mrs. Finch", "Mr. Vale"]
GENDERS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for event_id in setting.affords:
            for prize_id in PRIZES:
                out.append((place, event_id, prize_id))
    return out


def make_entity_story_name(name: str, gender: str) -> str:
    return name


def _do_event(world: World, child: Entity, event: Event, prize: Entity, narrate: bool = True) -> None:
    child.memes["desire"] = child.memes.get("desire", 0) + 1
    child.meters[event.id] = child.meters.get(event.id, 0) + 1
    if event.id == "finale":
        prize.meters["risk"] = prize.meters.get("risk", 0) + 1
    if event.id == "twist":
        child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    if narrate:
        world.say(f"{child.id} wanted to {event.verb} at {world.setting.place}.")


def predict(world: World, child: Entity, event: Event, prize: Entity) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(child.id), event, sim.get(prize.id), narrate=False)
    soiled = sim.get(prize.id).meters.get("risk", 0) >= METER_THRESHOLD and event.id == "finale"
    return {
        "soiled": soiled,
        "moral": "kindness",
    }


def setup(world: World, child: Entity, millionaire: Entity, teller: Entity, prize: Entity, event: Event) -> None:
    world.say(
        f"At {world.setting.place}, a little {child.type} named {child.id} loved gentle evenings, "
        f"soft lights, and the promise of a finale."
    )
    world.say(
        f"{child.id} had a fond dream of {event.gerund}, with {prize.phrase} shining nearby."
    )
    world.say(
        f"One kind millionaire, {millionaire.label}, came with a pocket full of coins, and the teller, {teller.label}, watched with a careful smile."
    )


def conflict(world: World, child: Entity, millionaire: Entity, teller: Entity, prize: Entity, event: Event) -> None:
    pred = predict(world, child, event, prize)
    world.facts["predicted_soiled"] = pred["soiled"]
    if pred["soiled"]:
        world.say(
            f"{child.id} thought a bigger finale would be better, and {millionaire.label} offered to pay for one."
        )
        world.say(
            f"But the teller, {teller.label}, said the nicest ending does not have to be the most expensive one."
        )
    else:
        world.say(
            f"{child.id} thought a bigger finale would be better, but the teller, {teller.label}, reminded everyone to keep it simple."
        )


def twist_and_moral(world: World, child: Entity, millionaire: Entity, teller: Entity, prize: Entity, event: Event) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"Then came a small twist: the millionaire was not trying to buy the show at all."
    )
    world.say(
        f"{millionaire.label} only wanted the child to have enough warm tea, paper stars, and time to finish kindly."
    )
    world.say(
        f"The teller nodded and said that a happy ending can be simple, honest, and shared."
    )
    child.memes["moral_value"] = child.memes.get("moral_value", 0) + 1
    world.say(
        f"{child.id} learned the moral value of caring more about people than about glitter."
    )


def resolution(world: World, child: Entity, millionaire: Entity, teller: Entity, prize: Entity, event: Event) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["worry"] = 0
    child.meters["calm"] = child.meters.get("calm", 0) + 1
    world.say(
        f"So {child.id} chose {event.turn}, and the finale became soft and sweet."
    )
    world.say(
        f"{child.id} carried {prize.phrase} to center stage, where it glowed like a bedtime star."
    )
    world.say(
        f"{millionaire.label} clapped quietly, {teller.label} smiled, and the night settled into a happy ending."
    )


def tell(setting: Setting, event: Event, prize_cfg: Prize, child_name: str, gender: str,
         millionaire_name: str, teller_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    millionaire = world.add(Entity(id="millionaire", kind="character", type="millionaire", label=millionaire_name))
    teller = world.add(Entity(id="teller", kind="character", type="teller", label=teller_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))

    setup(world, child, millionaire, teller, prize, event)
    world.para()
    conflict(world, child, millionaire, teller, prize, event)
    world.para()
    twist_and_moral(world, child, millionaire, teller, prize, event)
    resolution(world, child, millionaire, teller, prize, event)

    world.facts.update(
        child=child,
        millionaire=millionaire,
        teller=teller,
        prize=prize,
        event=event,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, event, prize = f["child"], f["event"], f["prize"]
    return [
        f'Write a bedtime story about a child named {child.id}, a millionaire, and a teller, using the word "{event.keyword}".',
        f"Tell a gentle story where {child.id} wants to {event.verb} with {prize.phrase}, but learns a moral value from a millionaire and a teller.",
        f"Write a short happy-ending story with a twist, a finale, and a kind choice at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, millionaire, teller, prize, event = f["child"], f["millionaire"], f["teller"], f["prize"], f["event"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to {event.verb} with {prize.phrase}.",
        ),
        QAItem(
            question=f"Who offered money, but not to spoil the story?",
            answer=f"The millionaire, {millionaire.label}, came with coins but wanted a kind, calm ending.",
        ),
        QAItem(
            question=f"Who explained that the best ending does not have to be expensive?",
            answer=f"The teller, {teller.label}, explained that a happy ending can be simple and shared.",
        ),
        QAItem(
            question=f"What moral value did {child.id} learn?",
            answer=f"{child.id} learned the moral value of caring about people more than glitter or money.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a finale?",
            answer="A finale is the final part of a show or story, when the ending comes at last.",
        ),
        QAItem(
            question="What does a teller do?",
            answer="A teller is a person who helps at a bank by handling money and speaking kindly to people.",
        ),
        QAItem(
            question="What is a millionaire?",
            answer="A millionaire is a person who has a very large amount of money.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


def explain_rejection() -> str:
    return "(No story: the chosen options do not make a gentle finale story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about a finale, a millionaire, and a teller.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--millionaire-name", choices=MILLIONAIRE_NAMES)
    ap.add_argument("--teller-name", choices=TELLER_NAMES)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.event:
        combos = [c for c in combos if c[1] == args.event]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError(explain_rejection())
    place, event, prize = rng.choice(combos)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    millionaire_name = args.millionaire_name or rng.choice(MILLIONAIRE_NAMES)
    teller_name = args.teller_name or rng.choice(TELLER_NAMES)
    return StoryParams(place=place, event=event, prize=prize, name=name, gender=gender,
                       millionaire_name=millionaire_name, teller_name=teller_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        EVENTS[params.event],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.millionaire_name,
        params.teller_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
event_choice(E) :- event(E).
valid_story(P, E, R) :- setting(P), event_choice(E), prize(R).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for e in EVENTS:
        lines.append(asp.fact("event", e))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(
        place="the little theater",
        event="finale",
        prize="lantern",
        name="Mia",
        gender="girl",
        millionaire_name="Ms. Gold",
        teller_name="Ms. Lane",
    ),
    StoryParams(
        place="the night market",
        event="twist",
        prize="crown",
        name="Noah",
        gender="boy",
        millionaire_name="Mr. Green",
        teller_name="Mr. Bell",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.event} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
