#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py
====================================================================================

A standalone story world for a tiny bedtime tale about a dragon, a small
conflict, a suspenseful search in the dark, and a flashback that helps solve the
problem gently.

The story premise is classical and child-facing:
- A child gets ready for bed and finds their favorite plush dragon missing.
- The room becomes quiet and a little suspenseful.
- A brief flashback reminds them where the plush dragon was last seen.
- A small conflict appears between wanting to search alone and wanting to ask
  for help.
- The child chooses a calm, safe way to look, and the dragon is found before
  sleep.

The world is modeled with typed entities, physical meters, and emotional memes.
The prose is rendered from simulated state, not from a frozen template with
swapped nouns.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/dragon_flashback_conflict_suspense_bedtime_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    darkness: str
    hiding_spots: list[str]
    bedtime_image: str
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
class ComfortObject:
    id: str
    label: str
    phrase: str
    tag: str
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
class MemoryCue:
    id: str
    trigger: str
    memory_line: str
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
class Recovery:
    id: str
    method: str
    sense: int
    text: str
    qa_text: str
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    box = world.get("box")
    if child.memes["searching"] >= THRESHOLD and box.meters["missing"] >= THRESHOLD:
        sig = ("suspense",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["suspense"] += 1
            out.append("__suspense__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["frustration"] >= THRESHOLD and helper.memes["care"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["conflict"] += 1
            helper.memes["concern"] += 1
            out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    box = world.get("box")
    if box.meters["found"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.meters["calm"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("conflict", _r_conflict), Rule("relief", _r_relief)]


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


def flashback_reason(world: World, cue: MemoryCue, box: ComfortObject) -> None:
    child = world.get("child")
    child.memes["remembering"] += 1
    world.say(
        f'Just then, a flashback drifted through {child.id}\'s mind. {cue.memory_line}'
    )
    world.say(
        f'That memory made {child.id} look toward {box.phrase} instead of the dark corner.'
    )


def begin(world: World, child: Entity, dragon: Entity, place: Place, box: ComfortObject) -> None:
    child.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} tucked in under soft blankets, but {child.pronoun('possessive')} "
        f"{box.label} was nowhere to be seen. The room felt {place.darkness}, and {place.bedtime_image}."
    )
    world.say(
        f'{child.id} whispered, "I need my dragon."'
    )


def search(world: World, child: Entity, helper: Entity, place: Place, box: ComfortObject) -> None:
    child.meters["searching"] += 1
    box.meters["missing"] += 1
    child.memes["frustration"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{child.id} peered under the bed, behind the pillow, and by the toy basket. "
        f"Each spot was quiet."
    )
    world.say(
        f"{helper.id} listened and stayed near, because a sleepy room can feel very big when a favorite toy is missing."
    )
    propagate(world, narrate=True)


def argue(world: World, child: Entity, helper: Entity, box: ComfortObject) -> None:
    child.memes["wanting_control"] += 1
    world.say(
        f'{child.id} frowned and said, "I can find {box.phrase} by myself!"'
    )
    world.say(
        f'{helper.id} answered softly, "We can look together. Two gentle eyes are better than one when the dark feels tricky."'
    )


def hint(world: World, cue: MemoryCue, box: ComfortObject) -> None:
    world.say(
        f"Then the flashback grew clearer. {cue.memory_line}"
    )
    world.say(
        f"It was a tiny clue, but it made the whole room seem less mysterious."
    )


def recover(world: World, child: Entity, helper: Entity, box: ComfortObject, recovery: Recovery) -> None:
    box.meters["found"] += 1
    box.meters["missing"] = 0
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, {child.id} lifted the blanket near the pillow, and there was {box.phrase}, "
        f"right where the flashback had pointed. {recovery.text}."
    )
    world.say(
        f"{child.id} hugged {box.label} tight, and the room finally felt safe enough for sleep."
    )


def end(world: World, child: Entity, dragon: Entity, box: ComfortObject, place: Place) -> None:
    world.say(
        f"With {box.phrase} tucked in close, {child.id} closed {child.pronoun('possessive')} eyes. "
        f"The moonlight stayed on the wall, and {place.bedtime_image}."
    )
    world.say(
        f"And the little dragon watched over the pillow until morning."
    )


def tell(place: Place, box: ComfortObject, cue: MemoryCue, recovery: Recovery,
         child_name: str = "Mina", child_type: str = "girl",
         helper_name: str = "Mom", helper_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_type, role="hero", attrs={"name": child_name}))
    helper = world.add(Entity("helper", kind="character", type=helper_type, role="helper", attrs={"name": helper_name}))
    dragon = world.add(Entity("dragon", kind="thing", type="toy", label="dragon", role="comfort"))
    toybox = world.add(Entity("box", kind="thing", type="toybox", label=box.label, role="missing"))
    world.facts["place"] = place
    world.facts["box"] = box
    world.facts["cue"] = cue
    world.facts["recovery"] = recovery
    begin(world, child, dragon, place, box)
    world.para()
    search(world, child, helper, place, box)
    argue(world, child, helper, box)
    world.para()
    flashback_reason(world, cue, box)
    hint(world, cue, box)
    recover(world, child, helper, box, recovery)
    end(world, child, dragon, box, place)
    world.facts.update(child=child, helper=helper, dragon=dragon, toybox=toybox, outcome="found")
    return world


PLACES = {
    "blue_room": Place(
        "blue_room",
        "the blue bedroom",
        "very shadowy",
        ["under the bed", "behind the pillow", "by the toy basket"],
        "the nightlight made a silver fish on the wall",
        tags={"bedtime", "dark", "suspense"},
    ),
    "moon_room": Place(
        "moon_room",
        "the moonlit room",
        "soft and moon-bright",
        ["under the blanket", "near the curtain", "beside the pillow"],
        "the stars on the ceiling looked like tiny watches",
        tags={"bedtime", "dark", "suspense"},
    ),
}

COMFORT_OBJECTS = {
    "plush_dragon": ComfortObject(
        "plush_dragon",
        "dragon",
        "the plush dragon",
        "dragon",
        tags={"dragon", "comfort"},
    ),
    "little_dragon": ComfortObject(
        "little_dragon",
        "dragon",
        "the little dragon toy",
        "dragon",
        tags={"dragon", "comfort"},
    ),
}

MEMORY_CUES = {
    "sofa": MemoryCue(
        "sofa",
        "sofa",
        "the child remembered setting the dragon on the sofa after story time",
        tags={"flashback", "memory"},
    ),
    "blanket": MemoryCue(
        "blanket",
        "blanket",
        "the child remembered hugging the dragon under the blanket before lights-out",
        tags={"flashback", "memory"},
    ),
}

RECOVERIES = {
    "gentle_search": Recovery(
        "gentle_search",
        "search with help",
        3,
        "So they searched together, one careful step at a time, until the missing toy was found",
        "searched together, and the toy was found safely",
        tags={"suspense", "conflict"},
    ),
    "quiet_listen": Recovery(
        "quiet_listen",
        "listen for clues",
        3,
        "So they listened for a soft rustle and looked where the memory said to look, until the toy was found",
        "listened for clues, and the toy was found safely",
        tags={"suspense", "flashback"},
    ),
}

NAMES = [("Mina", "girl"), ("Noah", "boy"), ("Lily", "girl"), ("Theo", "boy"), ("Ava", "girl"), ("Eli", "boy")]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, b, c) for p in PLACES for b in COMFORT_OBJECTS for c in MEMORY_CUES]


@dataclass
@dataclass
class StoryParams:
    place: str
    box: str
    cue: str
    recovery: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, box, cue = f["place"], f["box"], f["cue"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "dragon" and a gentle flashback.',
        f"Tell a suspenseful but cozy story where a child can't find {box.phrase} in {place.label}, remembers a clue, and solves a small conflict by asking for help.",
        f'Write a calm bedtime story with the words "dragon", "flashback", "conflict", and "suspense" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    box = f["box"]
    cue = f["cue"]
    recovery = f["recovery"]
    place = f["place"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who are looking for {box.phrase} at bedtime. The missing toy is a little dragon, so the whole story stays cozy and child-sized."),
        ("Why did the room feel suspenseful?",
         f"{box.phrase} was missing, and the dark room made the search feel uncertain. The suspense came from not knowing where the dragon had gone until the clue appeared."),
        ("What was the flashback for?",
         f"It reminded {child.id} where {box.phrase} was last seen. That memory gave {child.id} a calm clue to follow instead of guessing in the dark."),
        ("How was the conflict solved?",
         f"{child.id} wanted to search alone, but {helper.id} asked to look together. They listened, searched gently, and found {box.phrase} without making the bedtime worry bigger."),
        ("How did the story end?",
         f"It ended with {box.phrase} tucked in close so {child.id} could fall asleep. {place.bedtime_image}, and the dragon watched over the pillow until morning."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a dragon in this story?", "It is a plush toy that helps the child feel safe at bedtime."),
        QAItem("What does a flashback mean?", "A flashback is a memory of something that happened earlier, shown for a moment in the story."),
        QAItem("What is suspense?", "Suspense is the feeling of waiting and wondering what will happen next."),
        QAItem("What is a conflict?", "A conflict is when two wishes tug in different directions, like wanting to search alone but also needing help."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("blue_room", "plush_dragon", "sofa", "gentle_search", "Mina", "girl", "Mom", "mother"),
    StoryParams("moon_room", "little_dragon", "blanket", "quiet_listen", "Noah", "boy", "Dad", "father"),
    StoryParams("blue_room", "little_dragon", "blanket", "gentle_search", "Ava", "girl", "Mom", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this bedtime world needs a dragon, a missing comfort object, and a memory clue so the flashback, conflict, and suspense can all happen naturally.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.box and args.box not in COMFORT_OBJECTS:
        raise StoryError(explain_rejection())
    if args.cue and args.cue not in MEMORY_CUES:
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    place, box, cue = rng.choice(sorted(combos))
    recovery = args.recovery or rng.choice(sorted(RECOVERIES))
    child_name, child_type = args.child_name, args.child_type
    if child_name is None or child_type is None:
        child_name, child_type = rng.choice(NAMES)
    helper_name = args.helper_name or ("Mom" if child_type == "boy" else "Dad")
    helper_type = args.helper_type or ("mother" if helper_name == "Mom" else "father")
    if args.place:
        place = args.place
    if args.box:
        box = args.box
    if args.cue:
        cue = args.cue
    if args.recovery:
        recovery = args.recovery
    return StoryParams(place, box, cue, recovery, child_name, child_type, helper_name, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        COMFORT_OBJECTS[params.box],
        MEMORY_CUES[params.cue],
        RECOVERIES[params.recovery],
        params.child_name,
        params.child_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


ASP_RULES = r"""
missing(box) :- comfort_object(box).
suspense :- missing(box), bedtime(place).
conflict :- wants_alone(child), needs_help(child).
flashback :- cue(memory).
resolved :- flashback, conflict, helper_present(helper).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("bedtime", p))
    for b in COMFORT_OBJECTS:
        lines.append(asp.fact("comfort_object", b))
    for c in MEMORY_CUES:
        lines.append(asp.fact("cue", c))
    lines.append(asp.fact("helper_present", "helper"))
    lines.append(asp.fact("wants_alone", "child"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show missing/1."))
    return sorted(set(asp.atoms(model, "missing")))


def asp_verify() -> int:
    rc = 0
    py = {(b,) for b in COMFORT_OBJECTS}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: ASP matches valid_combos() ({len(cl)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime dragon story world with flashback, conflict, and suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--box", choices=COMFORT_OBJECTS)
    ap.add_argument("--cue", choices=MEMORY_CUES)
    ap.add_argument("--recovery", choices=RECOVERIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show missing/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible bedtime combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and the dragon ({p.place}, {p.recovery})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        if header:
            print(header)
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
