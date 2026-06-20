#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reciprocate_sink_dingaling_surprise_flashback_conflict_heartwarming.py
======================================================================================================

A small heartwarming storyworld about a child, a broken little bell, a kitchen
sink, and a kind act that gets reciprocated. The world supports:

- Surprise: a hidden gift appears near the ending.
- Flashback: a remembered earlier moment explains the bell.
- Conflict: two characters want different things.
- Heartwarming tone: the ending is gentle, concrete, and warm.

Seed words required by the prompt:
- reciprocate
- sink
- dingaling

This file is self-contained, stdlib-only, and follows the Storyweavers contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Bell:
    id: str
    label: str
    phrase: str
    sound: str
    broken: bool = False
    treasured: bool = True

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
class Sink:
    id: str
    label: str
    phrase: str
    room: str
    sparkling: bool = False

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
class SurpriseGift:
    id: str
    label: str
    phrase: str
    reveal: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    if child.memes["want_bell"] >= THRESHOLD and parent.memes["wants_sink"] >= THRESHOLD:
        sig = ("conflict",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["conflict"] += 1
        parent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_sink_bells(world: World) -> list[str]:
    out: list[str] = []
    bell = world.facts.get("bell_obj")
    sink = world.facts.get("sink_obj")
    child = world.entities.get("child")
    if not bell or not sink or not child:
        return out
    if child.meters["water"] < THRESHOLD:
        return out
    if sink.id in world.fired:
        return out
    world.fired.add((sink.id,))
    sink.sparkling = True
    bell.broken = True
    out.append("__sink__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.memes["remember"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["softness"] += 1
    out.append("__flashback__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("sink_bells", "physical", _r_sink_bells),
    Rule("flashback", "social", _r_flashback),
]


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


def predict_break(world: World) -> bool:
    sim = world.copy()
    sim.get("child").meters["water"] = 1.0
    propagate(sim, narrate=False)
    bell = sim.facts["bell_obj"]
    return bell.broken


@dataclass
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    house_room: str
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


CHILD_NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Ben", "Nora", "Eli"]
PARENT_NAMES = ["Mom", "Dad"]
ROOMS = ["kitchen", "mudroom", "sunny kitchen", "cozy laundry room"]


def setup_story(world: World, child: Entity, parent: Entity, bell: Bell, sink: Sink, gift: SurpriseGift) -> None:
    child.memes["want_bell"] = 1.0
    parent.memes["wants_sink"] = 1.0
    child.memes["remember"] = 0.0
    world.facts.update(bell_obj=bell, sink_obj=sink, gift_obj=gift)
    world.say(
        f"On a quiet afternoon, {child.id} and {parent.id} were in the {sink.room}. "
        f"A little bell sat on the counter, and the sink nearby shone clean."
    )
    world.say(
        f"{child.id} loved the bell because it made a happy {bell.sound}. "
        f"{parent.id} wanted the sink clear for washing dishes and careful work."
    )


def create_conflict(world: World, child: Entity, parent: Entity, bell: Bell, sink: Sink) -> None:
    world.para()
    world.say(
        f'{child.id} reached for the bell. "{bell.label.capitalize()}!" {child.id} said. '
        f'"I want to keep it by the sink so I can hear it all day."'
    )
    world.say(
        f'{parent.id} shook {parent.pronoun("possessive")} head. '
        f'"The sink is for water and washing. A bell should stay dry."'
    )
    propagate(world, narrate=True)


def flashback_beat(world: World, child: Entity, bell: Bell) -> None:
    child.memes["remember"] += 1
    world.say(
        f"{child.id} paused and remembered yesterday, when {parent_name := world.facts['parent_obj'].id} "
        f"had fixed the loose string on the bell with patient hands."
    )
    world.say(
        f"The bell had been quiet and sad then, but {parent_name} had smiled and said "
        f'"Little things feel better when we take care of them."'
    )


def accident_and_surprise(world: World, child: Entity, parent: Entity, bell: Bell, sink: Sink, gift: SurpriseGift) -> None:
    child.meters["water"] += 1
    child.memes["guilt"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Then there was a tiny splash, and the bell slipped into the sink with a soft dingaling."
    )
    world.say(
        f"{parent.id} reached in carefully and lifted it out. The bell was damp, but still there."
    )
    world.para()
    world.say(
        f"Just then, {parent.id} opened a drawer and found a surprise: {gift.phrase}. {gift.reveal}"
    )
    child.memes["joy"] += 1
    parent.memes["joy"] += 1


def repair_and_reciprocate(world: World, child: Entity, parent: Entity, bell: Bell, gift: SurpriseGift) -> None:
    world.say(
        f"{child.id} blinked, then smiled. {child.id} dried the bell with a towel and said, "
        f'"I will reciprocate. You helped my bell, so I will help you."'
    )
    world.say(
        f"{child.id} carried the towel to {parent.id} and wiped the sink until it sparkled."
    )
    world.say(
        f"{parent.id} laughed softly and hugged {child.id}. In return, {parent.id} placed "
        f"{gift.phrase} in {child.id}'s hands."
    )
    world.say(
        f'The little bell gave one last bright "dingaling," and this time everyone smiled.'
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    sink = Sink(id="sink", label="sink", phrase="the kitchen sink", room=params.house_room)
    bell = Bell(id="bell", label="bell", phrase="the little bell", sound="dingaling")
    gift = SurpriseGift(id="gift", label="gift", phrase="a ribbon-tied sticker book", reveal="It was tucked under a tea towel for later.")
    world.facts["parent_obj"] = parent

    setup_story(world, child, parent, bell, sink, gift)
    create_conflict(world, child, parent, bell, sink)
    flashback_beat(world, child, bell)
    accident_and_surprise(world, child, parent, bell, sink, gift)
    repair_and_reciprocate(world, child, parent, bell, gift)

    world.facts.update(
        child=child,
        parent=parent,
        sink=sink,
        bell=bell,
        gift=gift,
        outcome="repaired",
        conflict=child.memes["conflict"] >= THRESHOLD,
        flashback=child.memes["remember"] >= THRESHOLD,
        surprise=True,
        reciprocated=True,
    )
    return world


def build_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].id
    return [
        f'Write a heartwarming story for a young child that uses the words "{child}", "sink", and "dingaling".',
        f"Tell a gentle story where {child} has a conflict with a parent about a bell near a sink, then everything ends kindly.",
        f"Write a story with a flashback and a surprise where a child learns to reciprocate kindness after a little accident."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].id
    parent = f["parent"].id
    bell = f["bell"]
    gift = f["gift"]
    return [
        QAItem(
            question="Why was there a conflict?",
            answer=f"There was a conflict because {child} wanted the bell near the sink, but {parent} wanted the sink kept clear. They both cared about different things, so they had to slow down and listen."
        ),
        QAItem(
            question="What was the flashback about?",
            answer=f"{child} remembered {parent} fixing the bell the day before. That memory helped {child} remember that {parent} was being careful, not unkind."
        ),
        QAItem(
            question="What surprise happened at the end?",
            answer=f"{parent} found {gift.phrase} and gave it to {child}. It was a surprise because it was hidden until the ending, and it made the whole room feel happier."
        ),
        QAItem(
            question="How did the child reciprocate?",
            answer=f"{child} reciprocated by helping dry the bell and cleaning the sink. The child gave kindness back after being helped."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sink do?",
            answer="A sink is a place where people wash things with water. It helps keep dishes and hands clean."
        ),
        QAItem(
            question="What does the word reciprocate mean?",
            answer="To reciprocate means to give kind help back to someone who helped you first. It is like returning warmth with warmth."
        ),
        QAItem(
            question="What kind of sound can a little bell make?",
            answer='A little bell can make a bright ringing sound, like "dingaling." It is a cheerful sound that can be soft or clear.'
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Mom", "woman", "kitchen"),
    StoryParams("Noah", "boy", "Dad", "man", "cozy laundry room"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p.child_name, p.parent_name, room) for p in CURATED for room in [p.house_room]]


ASP_RULES = r"""
conflict :- child_wants_bell, parent_wants_sink.
flashback :- remember_fix.
surprise :- hidden_gift.
reciprocate :- helped, help_back.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("word", "reciprocate"),
        asp.fact("word", "sink"),
        asp.fact("word", "dingaling"),
        asp.fact("feature", "surprise"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "conflict"),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show word/1.\n#show feature/1."))
    words = sorted(asp.atoms(model, "word"))
    features = sorted(asp.atoms(model, "feature"))
    ok = (words == [("dingaling",), ("reciprocate",), ("sink",)] and
          features == [("conflict",), ("flashback",), ("surprise",)])
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story")
        return 1
    if ok:
        print("OK: ASP twin exposes the required words and features.")
        print("OK: ordinary generation produced a non-empty story.")
        return 0
    print("MISMATCH in ASP facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld with a sink, a dingaling bell, surprise, flashback, and conflict.")
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    room = args.room or rng.choice(ROOMS)
    gender = "girl" if name in {"Mia", "Lily", "Ava", "Nora"} else "boy"
    parent_gender = "woman" if parent == "Mom" else "man"
    return StoryParams(name, gender, parent, parent_gender, room)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show word/1.\n#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world is tiny; it encodes the required words/features directly.")
        print("Words: reciprocate, sink, dingaling")
        print("Features: Surprise, Flashback, Conflict")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
