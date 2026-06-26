#!/usr/bin/env python3
"""
storyworlds/worlds/platform_bad_ending_bedtime_story.py
=======================================================

A small story world in a bedtime-story style, built around a platform and a
misstep that leads to a bad ending.

Seed tale idea:
---
A sleepy child arrives at a quiet platform with a trusted grown-up and a tiny
bag of bedtime things. The child wants one last look at the lights and refuses
to leave when the train comes. The grown-up warns that the train does not wait,
but the child lingers too long. The family misses the train, and the night ends
cold and tired on the platform instead of in a cozy bed.

World shape:
---
- The platform is a place with two safe-ish states: calm and busy.
- A child can be sleepy, stubborn, or comforted.
- A guardian can warn, hurry, or try to soothe.
- A train arrival creates tension: the only reasonable choice is to board
  immediately or miss it.
- This world intentionally supports a "bad ending" branch: if the child delays,
  the train leaves and the bedtime plan fails.

The prose should read like a complete, child-facing story with a clear turn and
an ending image that proves the outcome.
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
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    setting: str = "platform"
    indoors: bool = False
    lights: str = "soft yellow lights"


@dataclass
class Train:
    id: str
    label: str
    arrives_with: str
    leaves_if_waited_for: bool = True
    can_board: bool = True


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.time: str = "night"
        self.train_arrived: bool = False
        self.train_left: bool = False
        self.boarded: bool = False
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.time = self.time
        clone.train_arrived = self.train_arrived
        clone.train_left = self.train_left
        clone.boarded = self.boarded
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    guardian_type: str
    mood: str
    train_label: str
    seed: Optional[int] = None


PLACES = {
    "station_platform": Place(name="the station platform", setting="platform", indoors=False),
    "quiet_platform": Place(name="the quiet platform", setting="platform", indoors=False),
}

TRAINS = {
    "night_train": Train(id="night_train", label="the last train", arrives_with="a soft hiss"),
    "sleep_train": Train(id="sleep_train", label="the sleepy train", arrives_with="a warm clatter"),
}

COMFORT_ITEMS = {
    "blanket": ComfortItem(id="blanket", label="blanket", phrase="a small blue blanket", helps_with={"sleepy", "cold"}),
    "teddy": ComfortItem(id="teddy", label="teddy bear", phrase="a round teddy bear", helps_with={"sleepy", "scared"}),
    "lantern": ComfortItem(id="lantern", label="lantern", phrase="a tiny lantern", helps_with={"dark"}),
}

CHILD_NAMES = ["Mia", "Noah", "Ella", "Leo", "Luna", "Theo", "Ava", "Nina"]
CHILD_TYPES = ["girl", "boy"]
GUARDIANS = ["mother", "father"]
MOODS = ["sleepy", "curious", "stubborn", "dreamy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TRAINS]


def train_at_risk(mood: str) -> bool:
    return mood in {"sleepy", "stubborn", "curious", "dreamy"}


def warn_is_reasonable(mood: str) -> bool:
    return train_at_risk(mood)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.train and args.train not in TRAINS:
        raise StoryError("Unknown train.")
    if args.child_type and args.child_type not in CHILD_TYPES:
        raise StoryError("Unknown child type.")
    if args.guardian_type and args.guardian_type not in GUARDIANS:
        raise StoryError("Unknown guardian type.")
    if args.mood and args.mood not in MOODS:
        raise StoryError("Unknown mood.")

    place = args.place or rng.choice(list(PLACES))
    train = args.train or rng.choice(list(TRAINS))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    guardian_type = args.guardian_type or rng.choice(GUARDIANS)
    mood = args.mood or rng.choice(MOODS)
    child_name = args.child_name or rng.choice(CHILD_NAMES)

    if not warn_is_reasonable(mood):
        raise StoryError("This story needs a mood that makes the child hesitate on the platform.")
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        guardian_type=guardian_type,
        mood=mood,
        train_label=train,
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Train, ComfortItem]:
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian_type, label=params.guardian_type))
    train = TRAINS[params.train_label]
    item = COMFORT_ITEMS["blanket" if params.mood == "sleepy" else "teddy"]
    world.add(Entity(id=item.id, type=item.id, label=item.label, phrase=item.phrase, owner=child.id))
    child.memes["sleepy"] = 1.0 if params.mood == "sleepy" else 0.0
    child.memes["stubborn"] = 1.0 if params.mood == "stubborn" else 0.0
    child.memes["curious"] = 1.0 if params.mood == "curious" else 0.0
    child.memes["dreamy"] = 1.0 if params.mood == "dreamy" else 0.0
    return child, guardian, train, item


def predict_miss(world: World, child: Entity) -> bool:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_child.memes["delay"] = sim_child.memes.get("delay", 0.0) + 1.0
    return True


def introduce(world: World, child: Entity, guardian: Entity, item: ComfortItem) -> None:
    world.say(
        f"{child.id} was a little {child.type} who felt extra small at bedtime."
        f" {child.pronoun().capitalize()} carried {child.pronoun('possessive')} {item.label} everywhere "
        f"because it made the dark feel softer."
    )
    world.say(
        f"{guardian.pronoun().capitalize()} stayed close and walked with {child.pronoun('object')} toward the platform."
    )


def arrive(world: World, child: Entity, guardian: Entity, train: Train) -> None:
    world.train_arrived = True
    world.say(
        f"At the platform, the lights glowed softly, and {train.label} arrived with {train.arrives_with}."
    )
    world.say(
        f"The air smelled like night air and metal rails, and it was time to go home to bed."
    )


def want_to_linger(world: World, child: Entity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1.0
    world.say(
        f"But {child.id} did not want to hurry. {child.pronoun().capitalize()} wanted one more look at the shining tracks."
    )


def warn(world: World, guardian: Entity, child: Entity, train: Train) -> None:
    if not warn_is_reasonable("sleepy"):
        return
    world.say(
        f'"The train will not wait," {guardian.pronoun("subject")} said. "If we miss it, bedtime will feel long and cold."'
    )


def delay(world: World, child: Entity) -> None:
    child.memes["delay"] = child.memes.get("delay", 0.0) + 1.0
    world.say(
        f"{child.id} stared at the dark windows and took one slow step, then another."
    )


def depart(world: World, train: Train) -> None:
    if world.boarded:
        return
    if any(e.memes.get("delay", 0.0) >= THRESHOLD for e in world.characters()):
        world.train_left = True
        world.say(
            f"Then {train.label} gave a gentle hiss, the doors slid shut, and it rolled away into the night."
        )


def bad_ending(world: World, child: Entity, guardian: Entity, item: ComfortItem, train: Train) -> None:
    child.memes["sad"] = 1.0
    guardian.memes["tired"] = 1.0
    world.say(
        f"{child.id} clutched {child.pronoun('possessive')} {item.label} and felt the platform turn chilly."
    )
    world.say(
        f"{guardian.pronoun().capitalize()} wrapped an arm around {child.pronoun('object')}, but the cozy bed was now far away."
    )
    world.say(
        f"That night ended with tired feet, a missed train, and a sleepy child sitting under the platform lights."
    )


def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    child, guardian, train, item = _setup(world, params)

    introduce(world, child, guardian, item)
    world.para()
    arrive(world, child, guardian, train)
    want_to_linger(world, child)
    warn(world, guardian, child, train)
    delay(world, child)
    depart(world, train)
    world.para()
    bad_ending(world, child, guardian, item, train)

    world.facts.update(
        child=child,
        guardian=guardian,
        train=train,
        item=item,
        place=place,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    train = f["train"]
    return [
        "Write a short bedtime story about a child on a platform who makes the wrong choice and misses the train.",
        f"Tell a gentle nighttime story where {child.id} at the platform does not listen when {guardian.pronoun('subject')} warns about {train.label}.",
        f"Write a simple story with the word 'platform' that ends with a missed ride and a sad bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    train: Train = f["train"]
    item: ComfortItem = f["item"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who was the story about on the platform?",
            answer=f"It was about {child.id}, a little {child.type} who was trying to get home to bed with {child.pronoun('possessive')} {item.label}.",
        ),
        QAItem(
            question=f"What did the guardian warn about when {train.label} arrived?",
            answer=f"{guardian.pronoun().capitalize()} warned that the train would not wait and that the family would miss bedtime if they lingered.",
        ),
        QAItem(
            question=f"Why did the story end badly at {place.name}?",
            answer=f"It ended badly because {child.id} kept delaying, so {train.label} left and {child.id} was left tired and chilly on the platform.",
        ),
        QAItem(
            question=f"What stayed with {child.id} at the end?",
            answer=f"{child.pronoun('possessive').capitalize()} {item.label} stayed with {child.id}, but the cozy bed and the train were both gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a platform?",
            answer="A platform is a raised place beside a train track where people wait for trains and get on or off them.",
        ),
        QAItem(
            question="Why do trains have doors?",
            answer="Trains have doors so people can get on and off safely when the train stops.",
        ),
        QAItem(
            question="Why is bedtime important for little children?",
            answer="Bedtime helps little children rest, and sleep gives their bodies and minds time to feel ready for the next day.",
        ),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  train_arrived={world.train_arrived} train_left={world.train_left} boarded={world.boarded}")
    return "\n".join(lines)


ASP_RULES = r"""
train_arrived(T) :- arrive(T).
missed_train(T) :- train_arrived(T), delayed(C).
bad_ending :- missed_train(T).

delayed(C) :- child(C), delay(C, N), N >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting", pid, place.setting))
    for tid, train in TRAINS.items():
        lines.append(asp.fact("train", tid))
    for cid, item in COMFORT_ITEMS.items():
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a platform, a missed train, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--guardian-type", choices=GUARDIANS)
    ap.add_argument("--mood", choices=MOODS)
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show place/1. #show train/1. #show comfort/1."))
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program loads.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this story world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="station_platform", child_name="Mia", child_type="girl", guardian_type="mother", mood="stubborn", train_label="night_train"),
            StoryParams(place="quiet_platform", child_name="Noah", child_type="boy", guardian_type="father", mood="dreamy", train_label="sleep_train"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.mood} at {p.place} (train: {p.train_label})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
