#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ball_small_traumatize_mystery_to_solve_twist.py
================================================================================

A standalone storyworld sketch for a small, slice-of-life mystery about a
missing ball, a tiny misunderstanding, and a magical twist that turns worry into
a gentle solution.

Seed words and features:
- ball
- small
- traumatize
- Mystery to Solve
- Twist
- Magic
- Slice of Life

This world models a child, a caregiver, a small setting, a beloved ball, and a
few plausible outcomes:
1) The ball is simply found in an ordinary place.
2) The search uncovers a harmless magic twist: the ball moved in a playful,
   surprising way because of a little household magic.
3) The search includes a scary moment, but an adult helps the child recover and
   the ending proves the day became safe again.

The simulation keeps the story grounded in physical state (meters) and emotional
state (memes), and the prose is generated from those state changes.
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
MOOD_CALM = 0.0
MOOD_WORRIED = 1.0
MOOD_RELIEVED = 1.5
MOOD_SCARED = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Setting:
    id: str
    place: str
    small_space: str
    cozy_detail: str
    hiding_places: list[str]
    magic_tone: str
    indoors: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Ball:
    id: str
    label: str
    phrase: str
    color: str
    size: str
    special: str
    plural: bool = False
    can_roll: bool = True
    can_hide: bool = True
    can_glow: bool = False
    can_animate: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class MysteryHint:
    id: str
    clue: str
    place: str
    reason: str
    truth: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class MagicTwist:
    id: str
    source: str
    effect: str
    reveal: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ball = world.get("ball")
    if ball.meters["missing"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    out.append("__worry__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    ball = world.get("ball")
    if ball.meters["glowing"] < THRESHOLD and ball.meters["missing"] >= THRESHOLD:
        return out
    if ball.meters["glowing"] < THRESHOLD:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["sparkle"] += 1
    out.append("__magic__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD or child.meters["found"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("magic", "physical", _r_magic),
    Rule("relief", "social", _r_relief),
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


def reasonable_combo(ball: Ball, mystery: MysteryHint, twist: MagicTwist) -> bool:
    return ball.can_hide and twist.safe and mystery.place in {"behind the couch", "under the table", "in the toy basket", "by the hallway mat"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for bid, ball in BALLS.items():
            for hid, hint in HINTS.items():
                for tid, twist in TWISTS.items():
                    if reasonable_combo(ball, hint, twist):
                        combos.append((sid, bid, hid))
    return combos


def search_prediction(world: World, hint: MysteryHint, twist: MagicTwist) -> dict:
    sim = world.copy()
    _search(sim, sim.get("child"), hint, twist, narrate=False)
    return {
        "found": sim.get("ball").meters["found"] >= THRESHOLD,
        "scary": sim.get("child").memes["scared"],
        "sparkle": sim.get("room").meters["sparkle"],
    }


def _search(world: World, child: Entity, hint: MysteryHint, twist: MagicTwist, narrate: bool = True) -> None:
    child.meters["looking"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, ball: Ball) -> None:
    child.memes["love"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {parent.id} stayed in {setting.place}. "
        f"The room felt small and cozy, with {setting.cozy_detail}."
    )
    world.say(
        f"{child.id} loved {ball.phrase}, a {ball.size} {ball.color} {ball.label} that rolled so well across the floor."
    )


def mystery(world: World, child: Entity, parent: Entity, hint: MysteryHint, ball: Ball, setting: Setting) -> None:
    child.meters["looking"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then one day, the ball was missing. {child.id} looked in {hint.place}, "
        f"but there was only {hint.reason}."
    )
    world.say(
        f'"Where did my ball go?" {child.id} asked. {parent.id} listened and smiled gently, '
        f"because little mysteries can feel big when something special is gone."
    )


def search(world: World, child: Entity, parent: Entity, hint: MysteryHint, ball: Ball, twist: MagicTwist) -> None:
    pred = search_prediction(world, hint, twist)
    world.facts["predicted"] = pred
    world.say(
        f"So they started to look together. {child.id} checked the {hint.place} again, "
        f"then the {world.get('room').attrs['next_spot']}, and then the {world.get('room').attrs['last_spot']}."
    )
    if pred["scary"] >= THRESHOLD:
        child.memes["scared"] += 1
        world.say(
            f"For a moment, {child.id} felt small and scared, almost as if the mystery was trying to swallow the whole day."
        )


def twist_reveal(world: World, child: Entity, parent: Entity, ball: Ball, twist: MagicTwist) -> None:
    ball.meters["glowing"] += 1
    ball.meters["found"] += 1
    world.get("room").meters["sparkle"] += 1
    world.say(
        f"Then came the twist: {twist.reveal}. A soft glow blinked from behind {world.get('room').attrs['twist_spot']}, "
        f"and there was the ball, tucked away like a tiny secret."
    )
    world.say(
        f"It was not lost at all; it had been {twist.effect}. {child.id} blinked, then laughed in surprise."
    )
    propagate(world, narrate=False)


def comfort(world: World, child: Entity, parent: Entity, ball: Ball) -> None:
    child.memes["scared"] = 0.0
    child.memes["relief"] += 1
    child.meters["found"] += 1
    world.say(
        f'{parent.id} knelt down and hugged {child.id}. "It is okay to feel upset," {parent.id} said softly. '
        f'"We found it, and nothing bad happened."'
    )
    world.say(
        f"{child.id} held the ball close. The small worry in {child.id}'s chest melted away."
    )


def ending(world: World, child: Entity, parent: Entity, ball: Ball, twist: MagicTwist) -> None:
    child.memes["joy"] += 1
    world.say(
        f"By evening, {child.id} was rolling the ball across the floor again, while {parent.id} watched with a smile."
    )
    world.say(
        f"This time the little ball seemed extra bright in the warm room, as if the day's mystery had turned into a game."
    )


def tell(setting: Setting, ball: Ball, hint: MysteryHint, twist: MagicTwist,
         child_name: str = "Maya", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label=setting.place, attrs={
        "next_spot": setting.hiding_places[1],
        "last_spot": setting.hiding_places[2],
        "twist_spot": setting.hiding_places[0],
    }))
    b = world.add(Entity(id="ball", type="toy", label=ball.label))
    b.meters["found"] = 0.0
    setup(world, child, parent, setting, ball)
    world.para()
    mystery(world, child, parent, hint, ball, setting)
    search(world, child, parent, hint, ball, twist)
    world.para()
    twist_reveal(world, child, parent, ball, twist)
    comfort(world, child, parent, ball)
    world.para()
    ending(world, child, parent, ball, twist)
    world.facts.update(child=child, parent=parent, room=room, ball=b, setting=setting, hint=hint, twist=twist)
    return world


SETTINGS = {
    "living_room": Setting("living_room", "the living room", "a small living room", "the couch had one saggy cushion", ["behind the couch", "under the table", "in the toy basket"], "soft and cozy"),
    "kitchen": Setting("kitchen", "the kitchen", "a small kitchen", "the curtains smelled like toast", ["by the fridge", "under the chair", "in a basket"], "bright and warm"),
    "bedroom": Setting("bedroom", "the bedroom", "a small bedroom", "the blanket was folded on the bed", ["under the bed", "behind the curtain", "in the toy box"], "quiet and sleepy"),
}

BALLS = {
    "red_ball": Ball("red_ball", "ball", "their favorite ball", "red", "small", "it had a white stripe", tags={"ball"}),
    "blue_ball": Ball("blue_ball", "ball", "their favorite ball", "blue", "small", "it had a tiny bell inside", tags={"ball"}),
    "green_ball": Ball("green_ball", "ball", "their favorite ball", "green", "small", "it felt soft and bouncy", tags={"ball", "small"}),
}

HINTS = {
    "behind_couch": MysteryHint("behind_couch", "under the couch", "behind the couch", "a little gap in the wall", "rolled there by accident", tags={"mystery"}),
    "under_table": MysteryHint("under_table", "under the table", "under the table", "a dropped napkin and a spoon", "rolled there during play", tags={"mystery"}),
    "toy_basket": MysteryHint("toy_basket", "in the toy basket", "in the toy basket", "a jumble of stuffed animals", "got tucked away by mistake", tags={"mystery"}),
}

TWISTS = {
    "glow_twist": MagicTwist("glow_twist", "a tiny house charm", "glowing all by itself", "a little sparkle had been guiding the search", safe=True, tags={"magic", "twist"}),
    "wind_twist": MagicTwist("wind_twist", "a playful breeze", "blown across the room", "the open window had nudged the ball along", safe=True, tags={"twist"}),
    "toy_twist": MagicTwist("toy_twist", "a wind-up toy", "singing a tiny tune", "the ball was following the toy's funny song", safe=True, tags={"magic", "twist"}),
}

GIRL_NAMES = ["Maya", "Nina", "Luna", "Mina", "Ivy", "Sora", "Ada", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo", "Ari", "Ben", "Milo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    ball: str
    hint: str
    twist: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    return [
        f'Write a slice-of-life mystery story for a 3-to-5-year-old that includes the words "ball", "small", and "mystery".',
        f"Tell a gentle story where {f['child'].id} cannot find {f['ball'].label}, searches a small room, and discovers a magical twist.",
        f'Write a cozy story about a missing ball, a tiny worry, and a kind surprise that makes the day feel safe again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    ball = f["ball"]
    hint = f["hint"]
    twist = f["twist"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, who spend a quiet day in {setting.place}. The story follows them as they solve a small mystery together."),
        ("What was missing?",
         f"{child.id}'s {ball.label} was missing. {child.id} looked all over the small room because the ball was the one thing that did not seem to be where it should be."),
        ("Where did they look first?",
         f"They looked {hint.place} first. That was the most likely place because it matched the clue they had, even though it turned out to be only a part of the answer."),
    ]
    if f["twist"]:
        qa.append((
            "What was the twist?",
            f"The twist was that {twist.reveal}. The ball was not gone forever; it had been moved in a surprising but safe way."
        ))
    if f["ball"].meters["found"] >= THRESHOLD:
        qa.append((
            "How did the story end?",
            f"It ended with the ball found and the worry gone. {child.id} got to play again, and the small scare turned into relief."
        ))
    if f["child"].memes["scared"] >= THRESHOLD:
        qa.append((
            "How did {child.id} feel when the mystery seemed big?".format(child=child),
            f"{child.id} felt small and scared for a moment. {parent.id} helped {child.id} calm down, and that made the mystery easier to face."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a ball?",
         "A ball is a round toy or object that can roll, bounce, or be tossed. Many children use balls for simple games."),
        ("What does small mean?",
         "Small means little in size. A small thing does not take up much space."),
        ("What is a mystery?",
         "A mystery is something you do not understand yet, so you try to find clues and solve it."),
        ("What is magic in a story?",
         "Magic is a story idea where something surprising happens that would not happen in real life. It can make a story feel wonder-filled."),
    ]
    if world.facts["twist"].safe:
        out.append(("Why can a gentle magic twist be nice in a story?",
                    "A gentle magic twist can turn a worry into a surprise without making anyone unsafe. It adds wonder while still keeping the story cozy."))
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("living_room", "red_ball", "behind_couch", "glow_twist", "Maya", "girl", "Mom", "woman"),
    StoryParams("kitchen", "blue_ball", "toy_basket", "wind_twist", "Noah", "boy", "Dad", "man"),
    StoryParams("bedroom", "green_ball", "under_table", "toy_twist", "Ivy", "girl", "Mom", "woman"),
]


def explain_rejection(setting: Setting, ball: Ball, hint: MysteryHint, twist: MagicTwist) -> str:
    return "(No story: this combination does not make a reasonable small mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BALLS:
        lines.append(asp.fact("ball", bid))
    for hid in HINTS:
        lines.append(asp.fact("hint", hid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    lines.append(asp.fact("small_story", 1))
    lines.append(asp.fact("magic_story", 1))
    lines.append(asp.fact("slice_of_life", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,H,T) :- setting(S), ball(B), hint(H), twist(T), small_story(1), magic_story(1), slice_of_life(1).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((s, b, h) for s, b, h in valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, ball=None, hint=None, twist=None,
                                                             child_name=None, child_gender=None, parent_name=None,
                                                             parent_gender=None, seed=None), random.Random(777)))
        assert sample.story
        print("OK: smoke generation produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small magical mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    ball = args.ball or rng.choice(list(BALLS))
    hint = args.hint or rng.choice(list(HINTS))
    twist = args.twist or rng.choice(list(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "woman" else "Dad")
    if not reasonable_combo(BALLS[ball], HINTS[hint], TWISTS[twist]):
        raise StoryError(explain_rejection(SETTINGS[setting], BALLS[ball], HINTS[hint], TWISTS[twist]))
    return StoryParams(setting, ball, hint, twist, child_name, child_gender, parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BALLS[params.ball], HINTS[params.hint], TWISTS[params.twist],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story kernels")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
