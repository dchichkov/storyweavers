#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swiss_twist_happy_ending_sound_effects_pirate.py
=================================================================================

A small, standalone story world about pirate kids searching for treasure in a
Swiss twist: a cozy mountain map, a squeaky rope bridge, a hidden cheese cave,
and a happy ending with sound effects.

The seed idea is pirate-tale shaped, but the turn is that the "treasure" is not
gold at all. It is a safe, friendly Swiss picnic chest with a lantern, a map,
and a wheel of Swiss cheese for the crew. The children must decide whether to
follow a risky creaky shortcut or listen to a careful helper. The turn happens
when a sound clue reveals the shortcut is not the right path, and the ending
shows they choose the safe route and celebrate together.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven story rendering
- Q&A generated from world state, not by parsing prose
- Python reasonableness gate + inline ASP twin
- --verify smoke-tests generation and checks Python/ASP parity
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_EFFECTS = {
    "squeak": "squeak-squeak",
    "creak": "creak-creak",
    "click": "click!",
    "crunch": "crunch!",
    "whoosh": "whoosh!",
    "drip": "drip-drip",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]
TRAITS = ["careful", "curious", "brave", "thoughtful", "gentle"]


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
class Setting:
    id: str
    place: str
    rig: str
    twist: str
    shadow_spot: str
    scene_word: str
    vibe: str

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
    twist_value: str
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
class Helper:
    id: str
    label: str
    phrase: str
    action: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    risky: bool = True
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


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    prize: str
    helper: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
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

    def chars(self) -> list[Entity]:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "harbor": Setting(
        "harbor",
        "the windy harbor",
        "The deck was a pirate ship, the rope ladder swayed like a mast, and a little crate of maps sat by the rail.",
        "swiss",
        "the dark gap under the dock planks",
        "cove",
        "salt-bright",
    ),
    "alps": Setting(
        "alps",
        "the Swiss mountain pass",
        "The cart was their pirate ship, a wooden pole became a flag, and a wool blanket held their snacks and maps.",
        "swiss",
        "the dark gap beside the stone path",
        "cave",
        "snow-bright",
    ),
}

HAZARDS = {
    "creaky_bridge": Hazard("creaky_bridge", "creaky bridge", "the old bridge", True, {"creak", "bridge"}),
    "dark_dock": Hazard("dark_dock", "dark dock", "the dark dock planks", True, {"dock", "dark"}),
    "snow_tunnel": Hazard("snow_tunnel", "snow tunnel", "the snowy tunnel", True, {"snow", "tunnel"}),
}

PRIZES = {
    "map": Prize("map", "a swiss map", "a swiss map", "hands", "secret"),
    "cheese": Prize("cheese", "a wheel of Swiss cheese", "a wheel of Swiss cheese", "arms", "tasty"),
    "lantern": Prize("lantern", "a lantern", "a lantern with a bright glass", "hands", "glow"),
}

HELPERS = {
    "bell": Helper("bell", "a little bell", "a little bell", "ring it to call for help", {"sound"}),
    "whistle": Helper("whistle", "a whistle", "a whistle", "blow it for a clear signal", {"sound"}),
    "flashlight": Helper("flashlight", "a flashlight", "a flashlight", "switch it on for safe light", {"sound", "light"}),
}

RESPONSES = {
    "guide_home": Response(
        "guide_home", 3, 3,
        "pointed them back to the safe path and led them home by the lantern glow",
        "pointed them the wrong way and the path stayed too risky to cross",
        "pointed them back to the safe path and led them home",
        {"safe"},
    ),
    "wait_and_listen": Response(
        "wait_and_listen", 3, 2,
        "held up a hand, listened for the sound, and chose the bridge with the sturdy ropes",
        "waited, but the creak kept getting louder and the unsafe path still looked bad",
        "held up a hand, listened for the sound, and chose the sturdy bridge",
        {"safe", "sound"},
    ),
    "call_parent": Response(
        "call_parent", 4, 4,
        "rang the bell, called a grown-up, and got help right away",
        "rang the bell too late, and the trouble had already grown big",
        "rang the bell and got help right away",
        {"safe", "sound"},
    ),
}

SENSE_MIN = 2
CAUTIOUS_TRAITS = {"careful", "thoughtful", "gentle"}


def hazard_at_risk(hazard: Hazard, prize: Prize) -> bool:
    return hazard.risky and prize.region in {"hands", "arms"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def would_avert(trait: str, mate_gender: str) -> bool:
    return trait in CAUTIOUS_TRAITS and mate_gender == "girl"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.trait, params.mate_gender):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "burned"


def explain_rejection(hazard: Hazard, prize: Prize) -> str:
    return (
        f"(No story: {hazard.label} does not actually threaten {prize.label} here. "
        f"Pick a prize in the hands or arms, so the pirate twist has a real choice.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is below the common-sense floor of {SENSE_MIN}.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for hid, hz in HAZARDS.items():
            for pid, pr in PRIZES.items():
                if hazard_at_risk(hz, pr):
                    combos.append((sid, hid, pid))
    return combos


def _r_raise_sound(world: World) -> list[str]:
    out: list[str] = []
    if "scene" in world.entities and world.get("scene").meters["alarm"] >= THRESHOLD:
        if ("sound", "alarm") not in world.fired:
            world.fired.add(("sound", "alarm"))
            for e in world.chars():
                e.memes["fear"] += 1
            out.append("__sound__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _r_raise_sound(world):
            changed = True
            if not s.startswith("__"):
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_twist(world: World, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(prize_id).meters["risk"] += 1
    sim.get("scene").meters["alarm"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sum(c.memes["fear"] for c in sim.chars()),
        "risk": sim.get(prize_id).meters["risk"],
    }


def setup(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright day, {hero.id} and {mate.id} turned {setting.place} into a pirate deck. "
        f"{setting.rig}"
    )
    world.say(
        f'Then {hero.id} pointed at the dark spot. "{setting.twist}, matey! The treasure must be there!"'
    )


def need_clue(world: World, mate: Entity, setting: Setting) -> None:
    world.say(
        f"But {setting.shadow_spot} looked black as a boot. {mate.id} peered in and whispered, "
        f'"We need a clue, not a rush."'
    )


def tempt(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} grinned. "{hazard.label.title()}! That shortcut sounds faster than a seagull."'
    )
    world.say("The rope above them went creak-creak in the wind.")


def warn(world: World, mate: Entity, hero: Entity, hazard: Hazard, prize: Prize, parent: Entity) -> None:
    pred = predict_twist(world, "scene")
    mate.memes["caution"] += 1
    world.get("scene").meters["alarm"] = pred["fear"]
    world.say(
        f'{mate.id} bit {mate.pronoun("possessive")} lip. "{hero.id}, that path is risky. '
        f"{parent.label_word.capitalize()} said to keep away from {hazard.phrase}, and "
        f"{prize.phrase} could be lost if we slip."
    )


def defy(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["defiance"] += 1
    world.say(f'"Nay," {hero.id} said, and they scampered toward the risky path.')
    world.say(f"Above them the rope went {SOUND_EFFECTS['creak']}.")


def avert(world: World, hero: Entity, mate: Entity, parent: Entity) -> None:
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.say(
        f'"Nay, you are right," {hero.id} said at last. {mate.id} was the careful one, '
        f"so the captain listened and turned back."
    )
    world.say(f"They went to tell {parent.label_word.capitalize()} about the dark spot instead.")


def do_risk(world: World, prize: Entity, hazard: Hazard) -> None:
    prize.meters["risk"] += 1
    world.get("scene").meters["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{SOUND_EFFECTS['creak'].capitalize()}! The risky path shivered, and the treasure chest tipped."
    )


def alarm(world: World, mate: Entity, parent: Entity, prize: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {mate.id} shouted. "{prize.label}!"')


def rescue(world: World, parent: Entity, response: Response, prize: Entity, hazard: Hazard) -> None:
    prize.meters["risk"] = 0
    world.get("scene").meters["alarm"] = 0
    world.say(
        f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} {response.text}."
    )
    world.say(
        f"The dark spot stopped looking scary, and the pirate crew kept {prize.label} safe."
    )


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, hazard: Hazard) -> None:
    for kid in (hero, mate):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0
    world.say("For a moment, everyone listened to the wind.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt and hugged them both. "
        f'"A pirate can be brave and still choose the safe route," {parent.pronoun()} said. '
        f'"{hazard.label.title()} is not a toy."'
    )
    world.say(f'"We promise," whispered {mate.id} and {hero.id}.')
    world.say("The lantern glowed warm in their hands like a tiny moon.")


def safe_ending(world: World, parent: Entity, hero: Entity, mate: Entity, prize: Entity, helper: Helper, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} brought out {helper.phrase} and smiled. "
        f'"Now we have a better clue," {parent.pronoun()} said.'
    )
    world.say(
        f'{hero.id} clicked it on. {helper.action.capitalize()}, and the dark spot turned bright.'
    )
    world.say(
        f"{mate.id} laughed, {prize.label} stayed safe, and the Swiss twist became a happy ending."
    )
    world.say("With a whoosh of cheer, the little pirates sailed home for cheese and stories.")


def tell(setting: Setting, hazard: Hazard, prize: Prize, helper: Helper, response: Response,
         hero: str = "Lily", hero_gender: str = "girl",
         mate: str = "Tom", mate_gender: str = "boy",
         trait: str = "careful", parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    scene = world.add(Entity("scene", type="scene", label=setting.place))
    a = world.add(Entity(hero, kind="character", type=hero_gender, role="hero", traits=[trait]))
    b = world.add(Entity(mate, kind="character", type=mate_gender, role="mate", traits=["bold"]))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="parent"))
    prize_ent = world.add(Entity("prize", type="thing", label=prize.label))
    helper_ent = world.add(Entity("helper", type="thing", label=helper.label))
    world.facts["setting"] = setting
    world.facts["hazard"] = hazard
    world.facts["prize"] = prize
    world.facts["helper"] = helper
    world.facts["response"] = response
    world.facts["scene"] = scene

    setup(world, a, b, setting)
    need_clue(world, b, setting)
    world.para()
    tempt(world, a, hazard)
    warn(world, b, a, hazard, prize, parent)
    if would_avert(trait, mate_gender):
        avert(world, a, b, parent)
        world.para()
        safe_ending(world, parent, a, b, prize_ent, helper, setting)
        outcome = "averted"
    else:
        defy(world, a, hazard)
        world.para()
        do_risk(world, prize_ent, hazard)
        alarm(world, b, parent, prize_ent)
        if is_contained(response, delay):
            world.para()
            rescue(world, parent, response, prize_ent, hazard)
            lesson(world, parent, a, b, hazard)
            world.para()
            safe_ending(world, parent, a, b, prize_ent, helper_ent, setting)
            outcome = "contained"
        else:
            world.say("Too late! The shortcut was a jumble of swaying boards.")
            world.say("The crew had to back away and find the safe path in the end.")
            outcome = "burned"
    world.facts.update(hero=a, mate=b, parent=parent, prize_ent=prize_ent, outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    hazard = f["hazard"]
    prize = f["prize"]
    return [
        f'Write a pirate-style story for a small child that includes the word "swiss" and ends happily.',
        f"Tell a pirate tale with a Swiss twist: {f['hero'].id} and {f['mate'].id} hear a creaky clue, avoid {hazard.label}, and keep {prize.label} safe.",
        f"Write a gentle story with sound effects like squeak and creak, a careful warning, and a happy ending in {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    hazard = f["hazard"]
    prize = f["prize"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {mate.id}, two little pirates who were exploring a Swiss place together. {parent.label_word.capitalize()} was the grown-up who helped them keep the adventure safe.",
        ),
        QAItem(
            question="Why did they slow down near the dark spot?",
            answer=f"They heard a creaky sound and saw that {hazard.phrase} looked risky. That warning made them stop and choose a safer way instead of rushing in.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            QAItem(
                question="What did they do instead of taking the risky shortcut?",
                answer=f"{hero.id} listened to {mate.id}, turned back, and used the safe path. The happy ending came from choosing caution before anything went wrong.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What happened after the risky choice?",
                answer=f"The crew got scared, but the grown-up helped fast enough to keep {prize.label} safe. The story still ended happily because help arrived and everyone chose safety after the twist.",
            )
        )
    qa.append(
        QAItem(
            question="How did the story end?",
            answer="It ended happily: the children kept their treasure safe, heard the sound clues, and went home smiling. The final image is of a bright lantern and a cheerful pirate crew.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do in a dark place?",
            answer="A lantern makes a warm light so you can see where you are going. It is safer than guessing in the dark.",
        ),
        QAItem(
            question="What does a creaky sound usually mean?",
            answer="A creaky sound often means something old is moving or bending. It can be a clue to slow down and be careful.",
        ),
        QAItem(
            question="What is Swiss cheese?",
            answer="Swiss cheese is a type of cheese with a mild taste and holes in it. People often eat it in sandwiches or snacks.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.risky:
            lines.append(asp.fact("risky", hid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
risk(H, P) :- hazard(H), risky(H), prize(P), region(P, R), (R = hands; R = arms).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, H, P) :- setting(S), hazard(H), prize(P), risk(H, P).
contained :- chosen_response(R), delay(D), power(R, P), P >= 1 + D.
outcome(averted) :- chosen_trait(T), chosen_mate_gender(girl), T = careful.
outcome(contained) :- not outcome(averted), contained.
outcome(burned) :- not outcome(averted), not contained.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_mate_gender", params.mate_gender),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    sens_py = {r.id for r in sensible_responses()}
    sens_cl = set(asp_sensible())
    if sens_py == sens_cl:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    cases = [CURATED[0], CURATED[1], CURATED[2]]
    rng = random.Random(777)
    for _ in range(20):
        try:
            cases.append(resolve_params(argparse.Namespace(
                setting=None, hazard=None, prize=None, helper=None, response=None,
                hero=None, hero_gender=None, mate=None, mate_gender=None,
                parent=None, trait=None, delay=None, seed=None
            ), rng))
        except Exception:
            pass
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} cases.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate() and serialization smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("harbor", "creaky_bridge", "map", "bell", "guide_home", "Lily", "girl", "Tom", "boy", "mother", "careful", 0),
    StoryParams("alps", "snow_tunnel", "cheese", "whistle", "wait_and_listen", "Max", "boy", "Nora", "girl", "father", "thoughtful", 0),
    StoryParams("harbor", "dark_dock", "lantern", "flashlight", "call_parent", "Ava", "girl", "Ben", "boy", "mother", "brave", 1),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with a Swiss twist, happy ending, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, prize = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(s.id for s in sensible_responses()))
    helper = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, hazard, prize, helper, response, hero, hero_gender, mate, mate_gender, parent, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], PRIZES[params.prize],
                 HELPERS[params.helper], RESPONSES[params.response], params.hero,
                 params.hero_gender, params.mate, params.mate_gender, params.trait,
                 params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in world_knowledge_qa(world)]],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(" ".join(row))
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
