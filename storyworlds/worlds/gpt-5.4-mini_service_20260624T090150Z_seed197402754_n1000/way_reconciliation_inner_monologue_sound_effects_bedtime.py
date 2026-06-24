#!/usr/bin/env python3
"""
A tiny bedtime storyworld about a child, a way, and a reconciliation.

The seed image:
A child does not want to go to bed yet. Along the way to bedtime, a small
spat happens over how to do things, and the child thinks quietly to themself.
There are soft sound effects in the room, and the ending should feel calm,
reconciled, and sleepy.

This script models that with a few grounded world-state variables:
- a child and a caregiver
- a path/way to bed
- bedtime objects and lights
- a small disagreement and a repaired relationship
- sound effects and inner monologue as explicit story instruments
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    cozy: bool = True
    darkens: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    helpful_for: str
    sound: str
    place: str


@dataclass
class StoryParams:
    room: str
    object: str
    name: str
    gender: str
    caregiver: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.sound_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        w = World(self.room)
        w.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.sound_log = list(self.sound_log)
        return w


ROOMS = {
    "nursery": Room(name="the nursery", cozy=True, darkens=True, affords={"bedtime"}),
    "bedroom": Room(name="the bedroom", cozy=True, darkens=True, affords={"bedtime"}),
    "shared_room": Room(name="the shared room", cozy=True, darkens=True, affords={"bedtime"}),
}

OBJECTS = {
    "bear": ObjectCfg(
        id="bear",
        label="bear",
        phrase="a soft brown bear",
        kind="toy",
        helpful_for="cuddle",
        sound="flop",
        place="bed",
    ),
    "blanket": ObjectCfg(
        id="blanket",
        label="blanket",
        phrase="a warm blue blanket",
        kind="blanket",
        helpful_for="comfort",
        sound="swish",
        place="bed",
    ),
    "lamp": ObjectCfg(
        id="lamp",
        label="lamp",
        phrase="a little lamp with a yellow shade",
        kind="light",
        helpful_for="soft light",
        sound="click",
        place="desk",
    ),
    "book": ObjectCfg(
        id="book",
        label="book",
        phrase="a bedtime storybook",
        kind="book",
        helpful_for="calm",
        sound="page",
        place="bedside",
    ),
}

GENDERS = {"girl", "boy"}
BOY_NAMES = ["Leo", "Ben", "Noah", "Theo", "Finn", "Max"]
GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "June"]
CAREGIVERS = ["mother", "father"]


def inner_monologue(child: Entity, goal: str, worry: str) -> str:
    return f"{child.id} thought, “I want to {goal}, but maybe {worry}.”"


def sound(word: str) -> str:
    return {
        "click": "click",
        "swish": "swish",
        "page": "shhff",
        "flop": "flop",
        "bump": "thump",
        "tap": "tap",
        "whisper": "soft whisper",
    }.get(word, word)


def setup_story(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleepy": 0.0},
        memes={"stubborn": 1.0, "tired": 0.0, "calm": 0.0, "reconciled": 0.0},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=params.caregiver,
        label=f"the {params.caregiver}",
        meters={"patience": 2.0},
        memes={"love": 1.0, "worry": 1.0},
    ))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(
        id=obj_cfg.id,
        kind="thing",
        type=obj_cfg.kind,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=caregiver.id,
    ))
    child.used_by = obj.id
    return child, caregiver, obj


def pick_sound_effects(world: World, obj: Entity) -> list[str]:
    cfg = OBJECTS[obj.id]
    effects = [sound(cfg.sound)]
    if cfg.id == "book":
        effects.append("shhff")
    elif cfg.id == "blanket":
        effects.append("swish")
    elif cfg.id == "bear":
        effects.append("flop")
    elif cfg.id == "lamp":
        effects.append("click")
    world.sound_log.extend(effects)
    return effects


def advance_sleepiness(child: Entity, amount: float) -> None:
    child.meters["sleepy"] = child.meters.get("sleepy", 0.0) + amount
    if child.meters["sleepy"] > 2:
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0


def validate_params(args: argparse.Namespace) -> None:
    if args.gender and args.gender not in GENDERS:
        raise StoryError("Invalid gender.")
    if args.room and args.room not in ROOMS:
        raise StoryError("Unknown room.")
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown bedtime object.")
    if args.room and args.object:
        if args.room not in ROOMS or "bedtime" not in ROOMS[args.room].affords:
            raise StoryError("That room cannot host bedtime.")
    if args.gender and args.name:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    validate_params(args)
    room = args.room or rng.choice(list(ROOMS))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(room=room, object=obj, name=name, gender=gender, caregiver=caregiver)


def generate_story_world(params: StoryParams) -> World:
    world = World(ROOMS[params.room])
    child, caregiver, obj = setup_story(world, params)
    cfg = OBJECTS[params.object]

    world.say(f"It was bedtime in {world.room.name}, and {child.id} was not quite ready for sleep.")
    world.say(f"Near the bed sat {cfg.phrase}, waiting like a small, quiet friend.")
    world.say(f"{child.id} liked {cfg.helpful_for} and wanted one more little turn before bed.")
    world.para()

    world.say(f"The caregiver pointed to the way to bed and said it was time to follow the bedtime way.")
    world.say(inner_monologue(child, f"stay up a little longer", f"{cfg.label} can wait"))
    advance_sleepiness(child, 0.5)
    pick_sound_effects(world, obj)
    world.say(f"{sound(cfg.sound).capitalize()}! {cfg.phrase} made a soft {cfg.sound} sound as {child.id} hugged {obj.it()}.")
    world.para()

    child.memes["stubborn"] += 1.0
    caregiver.memes["worry"] += 1.0
    world.say(f"“Just one more minute,” {child.id} said, though {child.pronoun('subject')} could feel the yawn hiding behind {child.pronoun('possessive')} teeth.")
    world.say(f"The caregiver smiled, but {caregiver.pronoun('subject')} also worried that the longer the night stayed awake, the harder sleep would be.")
    world.say(inner_monologue(child, "keep playing", "my eyes are getting heavy anyway"))
    advance_sleepiness(child, 1.0)

    world.para()
    world.say(f"Then came a tiny disagreement about the way to end the night: {child.id} wanted to keep holding {obj.it()}, and the caregiver wanted to tuck {child.id} in first.")
    child.memes["friction"] = 1.0
    caregiver.memes["friction"] = 1.0
    world.say(f"{child.id} felt a little cross. {caregiver.label} felt patient, but careful, like a hand holding a nightlight.")
    world.say(f"{sound('tap').capitalize()}, {sound('tap').capitalize()} went the small footsteps as they paused at the side of the bed.")
    world.say(inner_monologue(child, "be brave about bedtime", "I might miss the fun"))
    advance_sleepiness(child, 0.5)

    world.para()
    world.say(f"At last, the caregiver knelt and said, “We can do this the gentle way. We can make a better way together.”")
    child.memes["reconciled"] += 1.0
    caregiver.memes["reconciled"] = caregiver.memes.get("reconciled", 0.0) + 1.0
    world.say(f"{child.id} listened, then looked down at {cfg.phrase} and finally nodded.")
    world.say(f"“I can hold {obj.it()} after story time,” {child.id} whispered.")
    world.say(f"{sound('swish').capitalize()}, {sound('page').capitalize()} — blanket, book, and a quiet little turn of the night all slid into place.")
    world.say(f"{child.id} tucked {obj.it()} beside {child.pronoun('possessive')} pillow, and the room grew soft and still.")
    advance_sleepiness(child, 1.0)

    world.para()
    world.say(f"The caregiver read one last page, and the lamp gave a tiny {sound('click')} before the room turned dim.")
    world.say(f"{child.id} yawned a huge yawn and smiled at the end of the page.")
    world.say(f"The bedtime way had led to peace after all: no more fuss, just a warm bed, a calm heart, and {cfg.phrase} waiting for morning.")
    world.facts.update(
        child=child,
        caregiver=caregiver,
        obj=obj,
        room=world.room,
        object_cfg=cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cfg = f["object_cfg"]
    return [
        f'Write a short bedtime story for a young child named {child.id} that includes the word "way".',
        f"Tell a cozy story where {child.id} wants to keep {cfg.label} one more minute, but the caregiver helps with bedtime.",
        f"Write a gentle bedtime story with inner thoughts and soft sound effects like {sound(cfg.sound)} and click.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    cfg = f["object_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} want to do before bedtime?",
            answer=f"{child.id} wanted to keep holding {cfg.label} and stay up a little longer.",
        ),
        QAItem(
            question=f"Why did {caregiver.label} want bedtime to happen?",
            answer=f"{caregiver.label} wanted {child.id} to follow the bedtime way and get sleepy and rested.",
        ),
        QAItem(
            question=f"How did {child.id} and the caregiver fix their disagreement?",
            answer=f"They talked kindly, agreed on a gentler way, and let {child.id} keep {cfg.label} after story time.",
        ),
        QAItem(
            question=f"What sound effect was part of the bedtime scene?",
            answer=f"The story used soft sounds like {sound(cfg.sound)} and click to make the room feel calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is for resting your body and mind so you can sleep and wake up ready for a new day.",
        ),
        QAItem(
            question="Why can soft voices help at bedtime?",
            answer="Soft voices help because they keep the room calm and make it easier for sleepy children to relax.",
        ),
        QAItem(
            question="What is a blanket for?",
            answer="A blanket helps keep you warm and cozy while you sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"sound_log={world.sound_log}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with reconciliation, inner monologue, and sound effects.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.cozy:
            lines.append(asp.fact("cozy", rid))
        if room.darkens:
            lines.append(asp.fact("darkens", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for oid, cfg in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_kind", oid, cfg.kind))
        lines.append(asp.fact("helps", oid, cfg.helpful_for))
        lines.append(asp.fact("sound", oid, cfg.sound))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, O) :- room(R), object(O), affords(R, bedtime), helps(O, _), sound(O, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(r, o) for r in ROOMS for o in OBJECTS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("Mismatch:")
    print(" only in ASP:", sorted(cl - py))
    print(" only in Python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.object:
        if args.room not in ROOMS or args.object not in OBJECTS:
            raise StoryError("Invalid room/object choice.")
    room = args.room or rng.choice(list(ROOMS))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(room=room, object=obj, name=name, gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
    StoryParams(room="bedroom", object="bear", name="Mia", gender="girl", caregiver="mother"),
    StoryParams(room="nursery", object="blanket", name="Leo", gender="boy", caregiver="father"),
    StoryParams(room="shared_room", object="book", name="Nora", gender="girl", caregiver="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
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
            header = f"### {p.name}: bedtime in {p.room} with {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
