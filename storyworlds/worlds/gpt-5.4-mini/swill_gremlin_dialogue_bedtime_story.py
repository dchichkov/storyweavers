#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swill_gremlin_dialogue_bedtime_story.py
========================================================================

A standalone bedtime storyworld about a small child, a mischievous gremlin,
and the soft, calming power of dialogue.

This world is built from the seed words:
- swill
- gremlin

Style goals:
- bedtime-story warmth
- concrete, state-driven changes
- dialogue that moves the plot
- a clear turn from worry to comfort

The tiny domain:
- A child is getting ready for bed.
- A gremlin appears near the wash bowl and wants to make a messy "swill".
- The child wants to avoid the mess and the noise.
- A calm caregiver uses dialogue to redirect the gremlin and settle the room.
- The ending shows what changed: the room is tidy, the gremlin is soothed,
  and the child falls asleep with a gentle light.

The story engine models typed entities with physical meters and emotional memes.
It also includes a Python reasonableness gate and an inline ASP twin.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/swill_gremlin_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/swill_gremlin_dialogue_bedtime_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/swill_gremlin_dialogue_bedtime_story.py --verify
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
    darkness: float = 0.0
    tidy: float = 1.0

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
class BedtimeObject:
    id: str
    label: str
    phrase: str
    cozy: bool = False
    messy: bool = False
    wettable: bool = False
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
class BedtimeWish:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
        self.entities: dict[str, Entity | Room | BedtimeObject] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_swirl(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if isinstance(e, BedtimeObject) and e.meters["swill"] >= THRESHOLD:
            sig = ("swirl", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            room = world.get("room")
            if isinstance(room, Room):
                room.tidy = max(0.0, room.tidy - 0.5)
                room.darkness = min(1.0, room.darkness + 0.1)
            out.append("__swill__")
    return out


def _r_fret(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if isinstance(child, Entity) and child.meters["spill"] >= THRESHOLD:
        sig = ("fret", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    gremlin = world.get("gremlin")
    if isinstance(gremlin, Entity) and gremlin.memes["heard_kind_words"] >= THRESHOLD:
        sig = ("settle", gremlin.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        gremlin.memes["calm"] += 1
        out.append("__settle__")
    return out


RULES = [
    Rule("swirl", "physical", _r_swirl),
    Rule("fret", "social", _r_fret),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend([b for b in bits if not b.startswith("__")])
    if narrate:
        for bit in produced:
            world.say(bit)
    return produced


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    caregiver: str
    caregiver_gender: str
    gremlin_name: str
    swill_source: str
    wish: str
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


CHILDREN = {
    "Luna": "girl",
    "Milo": "boy",
    "Nora": "girl",
    "Theo": "boy",
    "Ada": "girl",
    "Ben": "boy",
}

CAREGIVERS = {
    "mom": "mother",
    "dad": "father",
}

GREMLIN_NAMES = ["Gremlin", "Nib", "Mottle", "Pip", "Scruff"]

SOURCES = {
    "bath bowl": BedtimeObject("bath_bowl", "bath bowl", "a little bath bowl", messy=True, wettable=True),
    "teacup": BedtimeObject("teacup", "teacup", "a tiny teacup", messy=True, wettable=True),
    "wash cloth": BedtimeObject("cloth", "wash cloth", "a soft wash cloth", messy=True, wettable=True),
}

WISHES = {
    "sip": BedtimeWish(
        "sip",
        3,
        3,
        "poured the swill into a tiny cup and took one careful sip",
        "tried to pour the swill into a cup, but the cup tipped and the room stayed messy",
        "poured the swill into a tiny cup and took one careful sip",
    ),
    "pour": BedtimeWish(
        "pour",
        3,
        2,
        "poured the swill into the sink and rinsed the bowl clean",
        "poured too little to help, and the swill still sloshed around",
        "poured the swill away and rinsed the bowl clean",
    ),
    "hide": BedtimeWish(
        "hide",
        2,
        1,
        "covered the swill with a towel and tucked it out of sight",
        "covered it, but the damp smell still made the room frown",
        "covered the swill with a towel and tucked it out of sight",
    ),
}

CURATED = [
    StoryParams("Luna", "girl", "mom", "mother", "Gremlin", "bath bowl", "pour"),
    StoryParams("Milo", "boy", "dad", "father", "Nib", "teacup", "sip"),
    StoryParams("Nora", "girl", "mom", "mother", "Scruff", "wash cloth", "hide"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in CHILDREN:
        for source in SOURCES:
            for wish in WISHES:
                combos.append((child, source, wish))
    return combos


def reasonableness_gate(source: BedtimeObject, wish: BedtimeWish) -> bool:
    return source.messy and wish.sense >= SENSE_MIN


def explain_rejection(source: BedtimeObject, wish: BedtimeWish) -> str:
    return (
        f"(No story: the chosen bedtime move doesn't fit the small world. "
        f"Try a messier swill source, or choose a calmer wish with enough sense.)"
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    caregiver = world.add(Entity(id=params.caregiver, kind="character", type=params.caregiver_gender, role="caregiver"))
    gremlin = world.add(Entity(id=params.gremlin_name, kind="character", type="gremlin", role="mischief"))
    room = world.add(Room(id="room", label="the bedroom", darkness=0.7, tidy=1.0))
    swill = world.add(BedtimeObject(id="swill", label="swill", phrase="the swill", messy=True, wettable=True))
    source = world.add(copy.deepcopy(SOURCES[params.swill_source]))
    wish = WISHES[params.wish]

    child.memes["sleepy"] = 1.0
    caregiver.memes["calm"] = 1.0
    gremlin.memes["restless"] = 1.0
    world.facts["source"] = source
    world.facts["wish"] = wish

    world.say(
        f"It was a soft bedtime, and {params.child} was under the quilt while the bedroom "
        f"glowed with a small lamp. On the bedside table sat {source.phrase}."
    )
    world.say(
        f'"What is that smell?" {params.child} whispered.'
        f' "{params.child}, that is not for drinking," said {params.caregiver}.'
    )
    world.say(
        f"From the shadow by the chair, {params.gremlin_name} poked out a round nose and said, "
        f'"I like swill," in a squeaky voice.'
    )

    world.para()
    child.meters["spill"] += 1
    source.meters["swill"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Please do not swill that around," said {params.caregiver}. '
        f'"The floor is sleepy, and so is the rest of the room."'
    )
    child.memes["worry"] += 1
    gremlin.memes["greedy"] += 1
    world.say(f'"But it looks funny," said {params.gremlin_name}. "I want one little swill."')

    world.para()
    if wish.sense < SENSE_MIN:
        raise StoryError("The bedtime choice is too silly for this gentle story.")
    if wish.id == "sip":
        child.memes["caution"] += 1
    elif wish.id == "pour":
        child.memes["helpfulness"] += 1
    else:
        child.memes["care"] += 1

    world.say(
        f'"How about we talk first?" said {params.caregiver}. '
        f'"We can make the room clean, and the gremlin can still feel welcome."'
    )
    if wish.id == "sip":
        world.say(
            f'"A tiny cup?" asked {params.child}. "A tiny cup," said {params.caregiver}, '
            f'"and only after we wipe the table and put the swill away."'
        )
    elif wish.id == "pour":
        world.say(
            f'"Can we pour it out?" asked {params.child}. "Yes," said {params.caregiver}, '
            f'"and then we can rinse the bowl and read one last story."'
        )
    else:
        world.say(
            f'"Can we hide it until morning?" asked {params.child}. "Yes," said {params.caregiver}, '
            f'"and we will tuck it neatly under the sink."'
        )

    greedy_move = source
    greedy_move.meters["swill"] = 0.0
    room.tidy = 1.0
    room.darkness = 0.3
    gremlin.memes["heard_kind_words"] += 1
    propagate(world, narrate=False)

    world.para()
    if wish.id == "sip":
        world.say(
            f"{params.child} took one careful sip and made a face, then laughed. "
            f"{params.gremlin_name} laughed too, but in a softer way."
        )
    elif wish.id == "pour":
        world.say(
            f"{params.child} poured the swill into the sink, and the bowl shone clean again. "
            f"{params.gremlin_name} blinked at the empty table and smiled."
        )
    else:
        world.say(
            f"{params.child} covered the swill with a towel, and the room felt tidy at once. "
            f"{params.gremlin_name} curled up beside the lamp and stopped fidgeting."
        )

    child.memes["relief"] += 1
    child.memes["joy"] += 1
    caregiver.memes["pride"] += 1
    gremlin.memes["calm"] += 1
    room.darkness = 0.1

    world.para()
    world.say(
        f'Then {params.caregiver} kissed {params.child} good night and said, '
        f'"Sweet dreams. No more swill tonight."'
    )
    world.say(
        f'{params.gremlin_name} tucked its little hands under its chin and yawned. '
        f'{params.child} shut {child.pronoun("possessive")} eyes, and the bedroom stayed '
        f'clean, warm, and very quiet.'
    )

    world.facts.update(
        child=child,
        caregiver=caregiver,
        gremlin=gremlin,
        room=room,
        source=source,
        wish=wish,
        outcome="settled",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "swill" and "gremlin" and uses dialogue to calm a small problem.',
        f"Tell a cozy story where {f['child'].id} meets a gremlin near some swill, and a caregiver solves the trouble with gentle words.",
        f'Write a soft, child-facing bedtime scene with a noisy gremlin, a bit of swill, and a calm ending after everyone talks kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    gremlin = f["gremlin"]
    source = f["source"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {caregiver.id}, and a small {gremlin.type} named {gremlin.id}. They are in a bedtime scene where everyone is trying to settle down."
        ),
        QAItem(
            question="Why did the room feel tense at first?",
            answer=f"The room felt tense because {source.label} became swill and the gremlin wanted to make a messy game of it. {child.id} worried the mess would wake the whole room."
        ),
        QAItem(
            question="How did the caregiver help?",
            answer=f"{caregiver.id} used calm dialogue and offered a safer plan instead of scolding anyone. That helped the swill get cleaned up and helped the gremlin grow quiet."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, the bedroom was clean and dim, and {child.id} could fall asleep peacefully. The gremlin was still there, but it was no longer making trouble."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is swill?",
            answer="Swill is messy, sloppy liquid or drink that is not neat to spill around. In a story, it can make a room feel sticky or untidy."
        ),
        QAItem(
            question="What is a gremlin?",
            answer="A gremlin is a tiny imaginary troublemaker from stories and jokes. A gremlin often causes a little mess or mischief before the trouble is solved."
        ),
        QAItem(
            question="Why are bedtime stories often calm?",
            answer="Bedtime stories are calm because they help a child feel safe, quiet, and ready to sleep. Gentle words, soft lights, and a tidy ending all help."
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
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if isinstance(e, Room):
            bits.append(f"darkness={e.darkness:.2f}")
            bits.append(f"tidy={e.tidy:.2f}")
        if isinstance(e, BedtimeObject):
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({getattr(e, 'type', 'thing'):8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is not calm enough for a bedtime story.)"


def valid_story_params() -> list[StoryParams]:
    out = []
    for child, source, wish in valid_combos():
        out.append(StoryParams(
            child=child,
            child_gender=CHILDREN[child],
            caregiver="mom",
            caregiver_gender=CAREGIVERS["mom"],
            gremlin_name="Gremlin",
            swill_source=source,
            wish=wish,
        ))
    return out


ASP_RULES = r"""
swill_source(S) :- source(S), messy(S).
quiet_end :- child(C), caregiver(G), gremlin(X), settled(X), tidy_room.
settled(X) :- heard_kind_words(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for child, gender in CHILDREN.items():
        lines.append(asp.fact("child", child))
        lines.append(asp.fact("gender", child, gender))
    for caregiver, gender in CAREGIVERS.items():
        lines.append(asp.fact("caregiver", caregiver))
        lines.append(asp.fact("gender", caregiver, gender))
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if src.messy:
            lines.append(asp.fact("messy", sid))
    for wid, wish in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("sense", wid, wish.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))

    # smoke test: ensure generation works
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with swill and a gremlin.")
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--swill-source", dest="swill_source", choices=SOURCES)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--gremlin-name", dest="gremlin_name", choices=GREMLIN_NAMES)
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
    if args.wish and WISHES[args.wish].sense < SENSE_MIN:
        raise StoryError(explain_response(args.wish))
    combos = [c for c in valid_combos()
              if (args.child is None or c[0] == args.child)
              and (args.swill_source is None or c[1] == args.swill_source)
              and (args.wish is None or c[2] == args.wish)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    child, source, wish = rng.choice(sorted(combos))
    gender = CHILDREN[child]
    caregiver = args.gremlin_name and "mom" or "mom"
    return StoryParams(
        child=child,
        child_gender=gender,
        caregiver=caregiver,
        caregiver_gender=CAREGIVERS[caregiver],
        gremlin_name=args.gremlin_name or rng.choice(GREMLIN_NAMES),
        swill_source=source,
        wish=wish,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
