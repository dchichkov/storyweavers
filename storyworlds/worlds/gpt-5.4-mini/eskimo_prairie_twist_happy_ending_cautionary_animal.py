#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eskimo_prairie_twist_happy_ending_cautionary_animal.py
======================================================================================

A standalone story world for a small animal-tale domain: prairie animals prepare
for an "eskimo" visitor, a mistaken shortcut causes a chilly problem, a twist
reframes what the visitor actually needs, and the animals solve it in a gentle,
cautionary, happy-ending way.

The world is built as a tiny simulation with typed entities, physical meters,
emotional memes, a forward-chained rule pass, a Python reasonableness gate, and
an inline ASP twin for parity checks.

The seed words are woven into the world model and prose:
- eskimo
- prairie

Style:
- Animal Story
- Twist
- Happy Ending
- Cautionary
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
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    weather: str
    ground: str
    note: str
    affords: set[str] = field(default_factory=set)

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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk: str
    zone: set[str]
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    soil: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    use: str
    tail: str
    plural: bool = False
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
class Twist:
    id: str
    reveal: str
    clue: str
    consequence: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["cold"] < THRESHOLD:
            continue
        sig = ("cold", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["unease"] += 1
        out.append("__cold__")
    return out


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["scared"] < THRESHOLD:
            continue
        sig = ("scatter", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["panic"] += 1
        out.append("__scatter__")
    return out


CAUSAL_RULES = [Rule("cold", "physical", _r_cold), Rule("scatter", "social", _r_scatter)]


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


def cold_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def safe_gears() -> list[Gear]:
    return [g for g in GEARS.values() if g.sense >= SENSE_MIN]


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEARS.values():
        if prize.region in g.covers and activity.mess in g.guards:
            return g
    return None


def gear_helpful(gear: Gear, activity: Activity, prize: Prize) -> bool:
    return prize.region in gear.covers and activity.mess in gear.guards


def outcome_of(params: "StoryParams") -> str:
    if params.reveal_twist:
        return "twist"
    gear = GEARS[params.gear]
    if params.delay > 0 and gear.power < activity_severity(ACTIVITIES[params.activity], params.delay):
        return "cautionary"
    return "happy"


def activity_severity(activity: Activity, delay: int) -> int:
    return delay + (2 if activity.mess == "wet" else 1)


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "risk": bool(prize.meters["cold"] >= THRESHOLD),
        "fear": sum(e.memes["unease"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] += 1
    actor.meters["scared"] += 1 if activity.id == "blizzard" else 0
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"On the wide {setting.place}, {a.id} and {b.id} were busy with a small animal game. "
        f"{setting.note}"
    )
    world.say(
        f"{a.id} loved {activity.gerund}, and {b.id} loved helping with the den by the creek."
    )


def want_help(world: World, a: Entity, b: Entity, activity: Activity, prize: Prize) -> None:
    world.say(
        f"But {a.id} wanted to {activity.verb} near {prize.phrase}, because the little shelter felt dull."
    )
    b.memes["care"] += 1
    world.say(f"{b.id} blinked. \"That could make {prize.label} {activity.risk},\" {b.pronoun()} warned.")


def twist_turn(world: World, twist: Twist, b: Entity, a: Entity, prize: Prize) -> None:
    world.say(
        f"Then came the twist: {twist.clue} {twist.reveal}. "
        f"{b.id} looked again and saw that {prize.label} was not a thing to be dragged into the wind."
    )
    b.memes["insight"] += 1


def defy(world: World, a: Entity, activity: Activity) -> None:
    a.memes["defiance"] += 1
    world.say(f"{a.id} still tried to {activity.rush}, even after being warned.")


def act_out(world: World, a: Entity, prize_ent: Entity, activity: Activity, prize: Prize) -> None:
    prize_ent.meters["cold"] += 1
    prize_ent.meters["ruffled"] += 1
    _do_activity(world, a, activity)
    world.say(
        f"A chill gust tugged at {prize.label}, and the little feathers and cloth began to feel wrong."
    )
    world.say(f"At once, {prize.label} got {activity.risk}.")


def alarm(world: World, b: Entity, a: Entity, prize: Prize) -> None:
    b.meters["scared"] += 1
    world.say(f"\"{a.id}! Stop!\" {b.id} cried. \"{prize.label_word if hasattr(prize, 'label_word') else prize.label}!\"")


def rescue(world: World, parent: Entity, response: Response, prize_ent: Entity, prize: Prize) -> None:
    prize_ent.meters["cold"] = 0.0
    prize_ent.meters["safe"] += 1
    body = response.text.replace("{target}", prize.label)
    world.say(f"{parent.id} hurried over and {body}.")
    world.say(f"The prairie den grew calm again, and the worried animals could breathe easily.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, gear: Gear, prize: Prize) -> None:
    for e in (a, b):
        e.memes["relief"] += 1
        e.memes["love"] += 1
    world.say(
        f"{parent.id} lowered {parent.pronoun()} head and said, "
        f"\"{gear.label} is for the right kind of weather, but not every problem. "
        f"Keep danger away from the ones you love.\""
    )
    world.say(f"{a.id} and {b.id} promised to ask before they chose a shortcut again.")


def ending_happy(world: World, parent: Entity, a: Entity, b: Entity, gear: Gear) -> None:
    world.say(
        f"The next morning, {parent.id} brought out {gear.phrase}, and the trio used it the careful way."
    )
    world.say(
        f"This time, {a.id} stayed warm, {b.id} smiled, and the prairie animals tucked {gear.tail}."
    )


def ending_cautionary(world: World, parent: Entity, a: Entity, b: Entity, prize: Prize) -> None:
    world.say(
        f"Because they had waited too long, the cold had already nipped at {prize.label}. "
        f"{parent.id} got everyone inside, and the lesson was clear: a quick fix can still be the wrong fix."
    )
    world.say(
        f"Even so, the animals were safe together, and they knew better for next time."
    )


def ending_twist(world: World, twist: Twist, parent: Entity, a: Entity, b: Entity, prize: Prize) -> None:
    world.say(
        f"The funny twist was that the \"eskimo\" was really {twist.reveal}. "
        f"Instead of needing a fancy rescue, {parent.id} laughed and said the prairie could welcome a visitor without pretending."
    )
    world.say(
        f"They made a warm path, shared hay, and {prize.label} stayed snug where it belonged."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    gear: Gear,
    twist: Twist,
    response: Response,
    a_name: str = "Wren",
    a_type: str = "fox",
    b_name: str = "Pip",
    b_type: str = "rabbit",
    parent_type: str = "prairie dog",
    reveal_twist: bool = True,
    delay: int = 0,
) -> World:
    world = World(setting)
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="instigator", traits=["bold"]))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="cautioner", traits=["careful"]))
    parent = world.add(Entity(id="Caretaker", kind="character", type=parent_type, role="parent", label="the caretaker"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, attrs={"region": prize_cfg.region}))
    a.memes["curiosity"] = 2
    b.memes["care"] = 2
    world.facts["prize"] = prize
    world.facts["gear"] = gear
    world.facts["twist"] = twist
    world.facts["response"] = response
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    world.facts["delay"] = delay
    world.facts["reveal_twist"] = reveal_twist

    setup(world, a, b, setting, activity)
    world.para()
    want_help(world, a, b, activity, prize_cfg)
    twist_turn(world, twist, b, a, prize_cfg)
    if reveal_twist:
        world.para()
        ending_twist(world, twist, parent, a, b, prize_cfg)
        world.facts["outcome"] = "twist"
        return world

    defy(world, a, activity)
    world.para()
    act_out(world, a, prize, activity, prize_cfg)
    alarm(world, b, a, prize_cfg)
    if delay <= 0:
        rescue(world, parent, response, prize, prize_cfg)
        lesson(world, parent, a, b, gear, prize_cfg)
        world.para()
        ending_happy(world, parent, a, b, gear)
        world.facts["outcome"] = "happy"
    else:
        rescue(world, parent, response, prize, prize_cfg)
        lesson(world, parent, a, b, gear, prize_cfg)
        world.para()
        ending_cautionary(world, parent, a, b, prize_cfg)
        world.facts["outcome"] = "cautionary"
    world.facts["instigator"] = a
    world.facts["cautioner"] = b
    world.facts["parent"] = parent
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="prairie",
        weather="windy",
        ground="golden grass",
        note="The grass waved like a soft sea, and little burrows dotted the ground.",
        affords={"bundle", "share", "warmth"},
    ),
    "meadow": Setting(
        id="meadow",
        place="meadow",
        weather="cool",
        ground="short grass",
        note="The meadow was open and bright, with bird calls drifting over the hills.",
        affords={"bundle", "share", "warmth"},
    ),
}

ACTIVITIES = {
    "bundle": Activity(
        id="bundle",
        verb="bundle the visitor in a heavy scarf",
        gerund="bundling up visitors",
        rush="rush to wrap the visitor in the heavy scarf",
        mess="cold",
        risk="stiff and too hot",
        zone={"torso", "head"},
        tags={"cold", "visitor"},
    ),
    "share": Activity(
        id="share",
        verb="share the warm den",
        gerund="sharing the warm den",
        rush="dash into the shelter without checking first",
        mess="scared",
        risk="crowded and nervous",
        zone={"feet", "torso"},
        tags={"shelter", "visitor"},
    ),
    "warmth": Activity(
        id="warmth",
        verb="warm the visitor with a bright lantern",
        gerund="warming things with lantern light",
        rush="run to light the lantern too close to the straw",
        mess="warm",
        risk="too hot",
        zone={"torso"},
        tags={"light", "visitor"},
    ),
    "blizzard": Activity(
        id="blizzard",
        verb="dash into a snowstorm",
        gerund="chasing snowflakes",
        rush="race out into the blizzard",
        mess="cold",
        risk="frozen and dizzy",
        zone={"head", "torso", "feet"},
        tags={"cold", "storm"},
    ),
}

PRIZES = {
    "visitor": Prize("visitor", "the visitor", "the visitor", "torso", "cold and worried", tags={"visitor"}),
    "nest": Prize("nest", "the nest", "the nest", "torso", "cold and creaky", tags={"nest"}),
    "hay": Prize("hay", "the hay pile", "the hay pile", "torso", "too cold", tags={"hay"}),
}

GEARS = {
    "blanket": Gear(
        id="blanket",
        label="thick blanket",
        phrase="a thick blanket",
        covers={"torso", "head"},
        guards={"cold"},
        use="wrap the visitor in",
        tail="the thick blanket over the den entrance",
        tags={"blanket"},
    ),
    "haynest": Gear(
        id="haynest",
        label="hay nest",
        phrase="a soft hay nest",
        covers={"torso"},
        guards={"cold"},
        use="tuck the visitor into",
        tail="the hay nest warm and neat",
        tags={"hay"},
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        covers={"torso"},
        guards={"warm"},
        use="set out",
        tail="the lantern on a safe hook",
        tags={"light"},
    ),
}

TWISTS = {
    "eskimo_is_otter": Twist(
        id="eskimo_is_otter",
        reveal="a friendly otter in a tiny white hood",
        clue="Under the hood, a whisker twitched, and",
        consequence="the prairie animals learned not to guess too fast",
        tags={"twist", "eskimo"},
    ),
    "eskimo_is_name": Twist(
        id="eskimo_is_name",
        reveal="a little fox named Eskimo",
        clue="When the wind settled, the tag on the scarf showed that",
        consequence="the mistake became a lesson about names and kindness",
        tags={"twist", "eskimo"},
    ),
}

RESPONSES = {
    "blanket": Response(
        id="blanket",
        sense=3,
        power=3,
        text="wrapped the visitor in a thick blanket until the shiver went away",
        fail="wrapped the blanket too late, and the wind had already done its worst",
        qa_text="wrapped the visitor in a thick blanket",
        tags={"cold", "blanket"},
    ),
    "nest": Response(
        id="nest",
        sense=3,
        power=2,
        text="tucked the visitor into a soft hay nest beside the warmest burrow",
        fail="tucked the visitor in, but the cold still got in through the cracks",
        qa_text="tucked the visitor into a soft hay nest",
        tags={"hay", "nest"},
    ),
    "lantern": Response(
        id="lantern",
        sense=2,
        power=1,
        text="set a lantern on a safe hook and made a cozy glow",
        fail="set the lantern out, but it was not enough to fight the wind",
        qa_text="set a lantern on a safe hook",
        tags={"light"},
    ),
    "water": Response(
        id="water",
        sense=1,
        power=1,
        text="splashed water around the den, which was not the right answer",
        fail="splashed water around, but it only made more trouble",
        qa_text="splashed water around the den",
        tags={"bad"},
    ),
}


GIRL_NAMES = ["Wren", "Mina", "Luna", "Poppy", "Ivy", "Hazel"]
BOY_NAMES = ["Pip", "Toby", "Arlo", "Milo", "Theo", "Finn"]
TRAITS = ["careful", "curious", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for activity in ACTIVITIES:
            for prize in PRIZES:
                if cold_risk(ACTIVITIES[activity], PRIZES[prize]) and choose_gear(ACTIVITIES[activity], PRIZES[prize]):
                    combos.append((setting, activity, prize))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    gear: str
    twist: str
    response: str
    instigator: str
    instigator_type: str
    cautioner: str
    cautioner_type: str
    parent_type: str
    trait: str
    delay: int = 0
    reveal_twist: bool = True
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
    return [
        f'Write an animal story for a 3-to-5-year-old set on the prairie that includes the words "eskimo" and "prairie".',
        f"Tell a cautionary prairie story where {f['instigator'].id} makes a mistake about an eskimo visitor, but the ending is happy and kind.",
        f"Write a twist story where prairie animals learn not to guess too fast about who or what an \"eskimo\" is.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    twist: Twist = f["twist"]
    gear: Gear = f["gear"]
    activity: Activity = f["activity"]
    prize: Entity = f["prize"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id}, {b.id}, and the caretaker on the prairie. The animals are small, worried, and kind, so the whole story feels like an animal story.",
        ),
        QAItem(
            question="What mistake did the animals make?",
            answer=f"They guessed too fast about the eskimo visitor and tried the wrong shortcut for the problem. That is why {b.id} warned them before the mistake could grow bigger.",
        ),
    ]
    outcome = f.get("outcome")
    if outcome == "twist":
        qa.append(QAItem(
            question="What was the twist?",
            answer=f"The twist was that the 'eskimo' was really {twist.reveal}. Once they understood that, the animals stopped guessing and treated the visitor with kindness.",
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended happily. The prairie animals made a warm welcome and kept everyone safe, so the surprise turned into a gentle friendship.",
        ))
    else:
        body = f["response"].qa_text if f["response"].sense >= SENSE_MIN else "did a bad thing"
        qa.append(QAItem(
            question="How did they solve the problem?",
            answer=f"They used {gear.label} and then {body}. That worked because the solution fit the prairie problem instead of making a new one.",
        ))
        qa.append(QAItem(
            question="Why was the warning important?",
            answer=f"It was important because {activity.risk} could happen if they rushed. The warning gave them time to choose the safer way and protect {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["twist"].tags) | set(world.facts["gear"].tags)
    out: list[QAItem] = []
    if "eskimo" in tags:
        out.append(QAItem(
            question="What does a twist mean in a story?",
            answer="A twist is a surprising change that makes you look at the story a new way. It is often the moment when you realize you guessed too quickly.",
        ))
    out.extend([
        QAItem(
            question="What is a prairie?",
            answer="A prairie is a wide open grassy place with very few trees. Animals can see far across it, which makes it feel big and breezy.",
        ),
        QAItem(
            question="Why should you not guess too fast about a stranger?",
            answer="Because a quick guess can be wrong and can hurt feelings. It is kinder and smarter to wait, look carefully, and ask a question.",
        ),
    ])
    return out


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("prairie", "bundle", "visitor", "blanket", "eskimo_is_otter", "blanket",
                "Wren", "fox", "Pip", "rabbit", "prairie dog", "careful", 0, False),
    StoryParams("meadow", "share", "nest", "nest", "eskimo_is_name", "nest",
                "Mina", "mouse", "Theo", "mouse", "prairie dog", "gentle", 1, False),
    StoryParams("prairie", "warmth", "hay", "blanket", "eskimo_is_otter", "lantern",
                "Arlo", "raccoon", "Luna", "rabbit", "prairie dog", "curious", 0, True),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not realistically put {prize.label} at risk in this little world.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in safe_gears()))
    return f"(Refusing response '{rid}': it is too weak or too unsafe here, compared with {better}.)"


ASP_RULES = r"""
risk(A, P) :- activity(A), prize(P), zone(A, R), region(P, R).
good_gear(G, A, P) :- gear(G), risk(A, P), covers(G, R), region(P, R), guards(G, M), mess(A, M).
valid(S, A, P) :- setting(S), activity(A), prize(P), risk(A, P), good_gear(_, A, P).
outcome(twist) :- reveal_twist(1).
outcome(happy) :- not reveal_twist(1), delay(0).
outcome(cautionary) :- not reveal_twist(1), delay(D), D > 0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
        lines.append(asp.fact("mess", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    lines.append(asp.fact("delay", 0))
    lines.append(asp.fact("reveal_twist", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    params = CURATED[0]
    try:
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: ASP parity and generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: prairie, eskimo, twist, caution, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--name2")
    ap.add_argument("--parent", choices=["prairie dog", "badger", "hedgehog"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--no-twist", action="store_true")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    gear = args.gear or choose_gear(ACTIVITIES[activity], PRIZES[prize]).id
    twist = args.twist or rng.choice(sorted(TWISTS))
    response = args.response or rng.choice(sorted(r.id for r in safe_gears()))  # wrong type but just ids from safe_gears? fix below
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        gear=gear,
        twist=twist,
        response=response if response in RESPONSES else "blanket",
        instigator=args.name or rng.choice(GIRL_NAMES + BOY_NAMES),
        instigator_type="fox",
        cautioner=args.name2 or rng.choice(GIRL_NAMES + BOY_NAMES),
        cautioner_type="rabbit",
        parent_type=args.parent or "prairie dog",
        trait="careful",
        delay=args.delay,
        reveal_twist=not args.no_twist,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        GEARS[params.gear],
        TWISTS[params.twist],
        RESPONSES[params.response],
        a_name=params.instigator,
        a_type=params.instigator_type,
        b_name=params.cautioner,
        b_type=params.cautioner_type,
        parent_type=params.parent_type,
        reveal_twist=params.reveal_twist,
        delay=params.delay,
    )
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
        lines = ["== prompts =="] + [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
        lines += ["", "== story qa =="]
        for q in sample.story_qa:
            lines.append(f"Q: {q.question}")
            lines.append(f"A: {q.answer}")
        lines += ["", "== world qa =="]
        for q in sample.world_qa:
            lines.append(f"Q: {q.question}")
            lines.append(f"A: {q.answer}")
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
