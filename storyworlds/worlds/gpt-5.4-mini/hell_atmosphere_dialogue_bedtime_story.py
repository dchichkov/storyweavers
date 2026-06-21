#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hell_atmosphere_dialogue_bedtime_story.py
=========================================================================

A standalone storyworld for a bedtime tale about a child, a stuffy room, and a
grown-up who changes the atmosphere before sleep. The story uses dialogue and
keeps the tone gentle, concrete, and child-facing.

Seed words:
- hell
- atmosphere

The world model treats the bedroom atmosphere as a real, changing condition:
the room can grow hot, stale, and grumpy, then become cool, calm, and sleepy.
A small tension builds when the child cannot rest, and it resolves when a parent
opens the window, fans fresh air in, and settles the room for bedtime.

This file is self-contained and stdlib-only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Room:
    id: str
    label: str
    atmosphere: str
    window_open: bool = False
    fan_on: bool = False
    curtains_closed: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BedtimeItem:
    id: str
    label: str
    kind: str
    effect: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    item: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room: Optional[Room] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.room = copy.deepcopy(self.room)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_stuffy(world: World) -> list[str]:
    out: list[str] = []
    room = world.room
    if room is None:
        return out
    if room.meters["stuffy"] < THRESHOLD:
        return out
    sig = ("stuffy", room.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.memes["grumpy"] += 1
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["sleepy"] -= 1
            e.memes["fuss"] += 1
    out.append("__atmosphere__")
    return out


def _r_fresh(world: World) -> list[str]:
    out: list[str] = []
    room = world.room
    if room is None:
        return out
    if room.meters["fresh"] < THRESHOLD:
        return out
    sig = ("fresh", room.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.memes["calm"] += 1
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["sleepy"] += 1
            e.memes["peace"] += 1
    out.append("__soft__")
    return out


CAUSAL_RULES = [Rule("stuffy", "atmosphere", _r_stuffy), Rule("fresh", "atmosphere", _r_fresh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Thing:
    id: str
    label: str
    action: str
    effect: str
    heat: float = 0.0
    fresh: float = 0.0
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


ROOMS = {
    "bedroom": Room("bedroom", "the bedroom", "stuffy", window_open=False, fan_on=False, curtains_closed=True),
    "nursery": Room("nursery", "the nursery", "stuffy", window_open=False, fan_on=False, curtains_closed=True),
    "attic_room": Room("attic_room", "the attic room", "stuffy", window_open=False, fan_on=False, curtains_closed=True),
}

ITEMS = {
    "window": BedtimeItem("window", "the window", "window", "open the window", safe=True, tags={"fresh"}),
    "fan": BedtimeItem("fan", "the little fan", "fan", "turn on the fan", safe=True, tags={"fresh"}),
    "blanket": BedtimeItem("blanket", "the soft blanket", "blanket", "tuck in the blanket", safe=True, tags={"sleep"}),
    "nightlight": BedtimeItem("nightlight", "the night-light", "light", "click on the night-light", safe=True, tags={"sleep"}),
}

HELLISH = {
    "hell": "hell",
    "atmosphere": "atmosphere",
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Nora", "Leo", "Ella"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in ROOMS:
        for item in ITEMS:
            combos.append((room, item))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a stuffy room and a calm fix.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    room = args.room or rng.choice(list(ROOMS))
    item = args.item or rng.choice(list(ITEMS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(child, child_gender, parent, parent_gender, item)


def _do_item(world: World, item: BedtimeItem, narrate: bool = True) -> None:
    room = world.room
    if room is None:
        return
    if item.id == "window":
        room.window_open = True
        room.meters["fresh"] += 1
        room.meters["stuffy"] = max(0.0, room.meters["stuffy"] - 1)
        world.say("The window opened wide, and fresh air slipped in.")
    elif item.id == "fan":
        room.fan_on = True
        room.meters["fresh"] += 1
        room.meters["stuffy"] = max(0.0, room.meters["stuffy"] - 1)
        world.say("The little fan hummed softly and pushed the warm air away.")
    elif item.id == "blanket":
        world.say("The soft blanket made the bed feel cozy and safe.")
    elif item.id == "nightlight":
        world.say("The night-light made a tiny golden puddle of light near the bed.")


def predict_atmosphere(world: World, item: BedtimeItem) -> dict:
    sim = world.copy()
    _do_item(sim, item, narrate=False)
    propagate(sim, narrate=False)
    return {
        "fresh": sim.room.meters["fresh"] if sim.room else 0,
        "calm": sim.room.memes["calm"] if sim.room else 0,
        "sleepy": sum(e.memes["sleepy"] for e in sim.entities.values() if e.kind == "character"),
    }


def tell(child: str, child_gender: str, parent: str, parent_gender: str, item: BedtimeItem, room: Room) -> World:
    world = World()
    world.room = copy.deepcopy(room)
    kid = world.add(Entity(child, "character", child_gender, traits=["small"], role="child"))
    adult = world.add(Entity(parent, "character", parent_gender, role="parent"))
    kid.memes["sleepy"] = 0.0
    adult.memes["care"] = 1.0

    world.say(
        f"At bedtime, {child} slipped under the covers in {world.room.label}. "
        f"The room had a weird, hot atmosphere, and {child} wriggled and sighed."
    )
    world.say(f'"{parent}," {child} whispered, "why does it feel so stuffy in here?"')
    world.para()
    world.say(f'"Because the air is stuck," {parent} said, smoothing the blanket. "Let me fix the atmosphere."')

    pred = predict_atmosphere(world, item)
    world.facts["pred"] = pred
    world.facts["room_id"] = room.id
    world.facts["item_id"] = item.id

    if item.id in {"window", "fan"}:
        _do_item(world, item)
        propagate(world)
        world.para()
        if item.id == "window":
            world.say(f'"That is better," {child} said. "The air feels less like a little hell."')
        else:
            world.say(f'"That is better," {child} said. "Now the room feels soft and sleepy."')
        world.say(f'"Good," {parent} said. "A kind atmosphere helps little dreams come right on time."')
        world.say(f"{child} yawned, hugged the blanket, and drifted off while the night-light glowed like a tiny moon.")
    else:
        world.say(f'"How about we open the window first?" {parent} asked.')
        world.say(f'"Or turn on the fan?" {child} asked, half asleep already.')
        world.para()
        _do_item(world, ITEMS["window"])
        _do_item(world, ITEMS["fan"])
        propagate(world)
        world.say(f'"There," {parent} said. "Now the atmosphere is gentle again."')
        world.say(f"{child} smiled, curled up, and let the soft cool air rock {child} to sleep.")
    world.facts.update(child=kid, parent=adult, room=world.room, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story for a young child that includes the words "hell" and "atmosphere" and has gentle dialogue.',
        f"Tell a cozy story where {world.facts['child'].id} cannot sleep because the atmosphere in {world.facts['room'].label} feels stuffy, and a parent helps.",
        "Write a small bedtime tale about changing a room from hot and grumpy to cool and sleepy, with spoken lines.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    room = world.facts["room"]
    pred = world.facts["pred"]
    return [
        QAItem(
            question=f"Why did {child.id} have trouble falling asleep?",
            answer=f"{child.id} had trouble sleeping because {room.label} felt stuffy and hot. The atmosphere was grumpy, so {child.id} kept wriggling instead of settling down."
        ),
        QAItem(
            question=f"What did {parent.id} do to help?",
            answer=f"{parent.id} opened the window and/or turned on the fan, which brought in fresh air. That changed the room from a hot, sticky place into a calm bedtime place."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The room stopped feeling like a little hell of heat and became soft and sleepy instead. The child could rest because the atmosphere turned fresh and kind."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a fan do?",
            answer="A fan moves air around. It can help a room feel cooler and less stuffy."
        ),
        QAItem(
            question="What is atmosphere?",
            answer="Atmosphere means the feeling of a place or the air around you. A room can have a calm atmosphere or a grumpy one."
        ),
        QAItem(
            question="What helps a child fall asleep at bedtime?",
            answer="A quiet room, a cozy blanket, and fresh air can all help. Soft light and a gentle voice can make bedtime feel safe too."
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
    lines = ["--- world model state ---"]
    if world.room:
        lines.append(
            f"  room: {world.room.label} stuffy={world.room.meters['stuffy']} fresh={world.room.meters['fresh']} "
            f"window_open={world.room.window_open} fan_on={world.room.fan_on}"
        )
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k,v) for k,v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k,v) for k,v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Mom", "mother", "window"),
    StoryParams("Noah", "boy", "Dad", "father", "fan"),
    StoryParams("Lily", "girl", "Mama", "mother", "fan"),
]


def explain_rejection(item: BedtimeItem) -> str:
    return f"(No story: {item.label} does not fit the bedtime fix this world is built to tell.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, I) :- room(R), item(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python combo gates.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params.child, params.child_gender, params.parent, params.parent_gender, ITEMS[params.item], ROOMS["bedroom"])
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for r, i in asp_valid_combos():
            print(r, i)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
