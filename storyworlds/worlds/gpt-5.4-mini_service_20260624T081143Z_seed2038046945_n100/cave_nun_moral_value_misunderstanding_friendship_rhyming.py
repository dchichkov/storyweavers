#!/usr/bin/env python3
"""
storyworlds/worlds/cave_nun_moral_value_misunderstanding_friendship_rhyming.py
===============================================================================

A standalone story world for a small rhyming tale in a cave: a nun, a friend,
a misunderstanding, and a moral-value turn toward friendship.

The domain keeps the prose simple and child-facing while the world state drives
the narration. The core premise is:

- A kind nun goes into a cave with a friend.
- A misunderstanding makes someone think the other hid a bright moral prize.
- The friend briefly feels hurt.
- A gentle explanation reveals the truth.
- Friendship and moral value are restored through a shared act of care.

The script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results eagerly
- lazily imports storyworlds/asp inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"nun", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    label: str
    mood: str
    features: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    key: str
    label: str
    phrase: str
    value: str
    shine: str
    owner: str = ""
    hidden: bool = False


@dataclass
class StoryParams:
    place: str
    nun_name: str
    friend_name: str
    object_kind: str
    misunderstanding: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectItem] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectItem) -> ObjectItem:
        self.objects[obj.key] = obj
        return obj

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
        w.objects = copy.deepcopy(self.objects)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "cave": Place(
        key="cave",
        label="the cave",
        mood="cool and echoing",
        features={"echo", "stone", "dark"},
    ),
    "grotto": Place(
        key="grotto",
        label="the grotto",
        mood="small and shining",
        features={"echo", "water", "stone"},
    ),
}

OBJECTS = {
    "lantern": ObjectItem(
        key="lantern",
        label="lantern",
        phrase="a small lantern",
        value="light",
        shine="glowed softly",
    ),
    "pearl": ObjectItem(
        key="pearl",
        label="pearl",
        phrase="a bright pearl",
        value="kindness",
        shine="shone like a moon drop",
    ),
    "bell": ObjectItem(
        key="bell",
        label="bell",
        phrase="a little silver bell",
        value="peace",
        shine="rang like a tiny song",
    ),
}

MISUNDERSTANDINGS = {
    "hid": {
        "setup": "hid a shiny prize",
        "turn": "thought the other had tucked the treasure away",
        "fix": "showed the prize was safe in the open",
    },
    "borrowed": {
        "setup": "borrowed a bright prize",
        "turn": "thought the other had taken it without asking",
        "fix": "explained it was only borrowed with care",
    },
    "lost": {
        "setup": "lost a treasured prize",
        "turn": "thought the other had made it disappear",
        "fix": "found the prize waiting near the stone wall",
    },
}

NUN_NAMES = ["Clare", "Mina", "Anna", "Ruth", "Iris", "Lena"]
FRIEND_NAMES = ["Ben", "Milo", "Tess", "June", "Ned", "Lia"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, obj) for place in PLACES for obj in OBJECTS]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
        for feat in sorted(p.features):
            lines.append(asp.fact("has_feature", p.key, feat))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.key))
        lines.append(asp.fact("value", o.key, o.value))
    for k in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", k))
    return "\n".join(lines)


ASP_RULES = r"""
good_story(Place, Obj, M) :- place(Place), object(Obj), misunderstanding(M),
    has_feature(Place, echo), value(Obj, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set((p, o, m) for p, o in valid_combos() for m in MISUNDERSTANDINGS)
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print(" only in asp:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming cave tale about a nun, a misunderstanding, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_kind", choices=OBJECTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--nun-name")
    ap.add_argument("--friend-name")
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
    if args.object_kind and args.misunderstanding:
        if args.misunderstanding not in MISUNDERSTANDINGS:
            raise StoryError("Unknown misunderstanding.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_kind:
        combos = [c for c in combos if c[1] == args.object_kind]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    return StoryParams(
        place=place,
        nun_name=args.nun_name or rng.choice(NUN_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        object_kind=obj,
        misunderstanding=misunderstanding,
    )


def _rhyming_opening(place: Place, nun: Entity, friend: Entity) -> str:
    return (
        f"In {place.label}, cool and still, {nun.name} walked with a kind small will. "
        f"By stone and shade, {friend.name} came near, and both felt safe and bright and clear."
    )


def _rhyming_middle(world: World, nun: Entity, friend: Entity, obj: ObjectItem, mkey: str) -> None:
    data = MISUNDERSTANDINGS[mkey]
    nun.memes["care"] += 1
    friend.memes["trust"] += 1
    world.say(_rhyming_opening(world.place, nun, friend))
    world.say(
        f"They found {obj.phrase} where shadows lay; {obj.shine}, a little light for play."
    )
    world.para()
    friend.memes["hurt"] += 1
    friend.memes["misunderstanding"] += 1
    world.say(
        f"But then {friend.name} frowned and felt unsure: {friend.name} {data['turn']}, that's for sure."
    )
    world.say(
        f"{friend.pronoun('subject').capitalize()} thought the prize was hidden away, and the cave grew quiet in a lonely way."
    )
    world.para()
    world.facts["misunderstanding"] = mkey
    world.facts["turn_text"] = data["setup"]


def _resolve(world: World, nun: Entity, friend: Entity, obj: ObjectItem) -> None:
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 1)
    friend.memes["trust"] += 2
    nun.memes["friendship"] += 2
    nun.memes["moral_value"] += 1
    obj.hidden = False
    world.say(
        f"Then {nun.name} spoke soft and slow, to let the true small reason show."
    )
    world.say(
        f"She said the prize was safe and near, and kindness made the truth grow clear."
    )
    world.say(
        f"They shared the {obj.label}, side by side, and friendship warmed the cave inside."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    nun = world.add_entity(Entity(id=params.nun_name, kind="character", type="nun", name=params.nun_name))
    friend = world.add_entity(Entity(id=params.friend_name, kind="character", type="friend", name=params.friend_name))
    obj = world.add_object(OBJECTS[params.object_kind])

    world.say(
        f"{nun.name} the nun went in the cave, with {friend.name} brave and mild and brave."
    )
    world.say(
        f"She carried {obj.phrase}, a gentle gleam, a moral little treasure in a dream."
    )
    world.para()
    _rhyming_middle(world, nun, friend, obj, params.misunderstanding)
    _resolve(world, nun, friend, obj)
    world.facts.update(nun=nun, friend=friend, obj=obj, params=params, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short rhyming story for a child about a nun in a cave, a misunderstanding, and friendship.",
        f"Tell a gentle rhyming tale where {p.nun_name} and {p.friend_name} are in {world.place.label} and a small mistake must be fixed.",
        f"Write a cave story with a bright moral value object, a misunderstanding, and a happy friendship ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    nun = world.facts["nun"]
    friend = world.facts["friend"]
    obj = world.facts["obj"]
    return [
        QAItem(
            question=f"Who went into {world.place.label} together?",
            answer=f"{nun.name} the nun and {friend.name} went into {world.place.label} together.",
        ),
        QAItem(
            question=f"What did {friend.name} misunderstand about the {obj.label}?",
            answer=f"{friend.name} thought {nun.name} had {MISUNDERSTANDINGS[p.misunderstanding]['setup']} and that it was being hidden or taken away.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The truth was explained, the worry faded, and the two friends shared the {obj.label} with happy hearts.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cave?",
            answer="A cave is a hollow space in rock, often dark and cool inside.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between people who help and trust each other.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="A moral value is a good idea like kindness, honesty, or fairness that helps people choose well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} memes={dict(e.memes)}")
    for o in world.objects.values():
        lines.append(f"  {o.key}: hidden={o.hidden} owner={o.owner}")
    lines.append(f"  place={world.place.key}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", nun_name="Clare", friend_name="Ben", object_kind="pearl", misunderstanding="hid"),
    StoryParams(place="grotto", nun_name="Mina", friend_name="Tess", object_kind="bell", misunderstanding="borrowed"),
]


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/3."))
        print(sorted(set(asp.atoms(model, "good_story"))))
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
