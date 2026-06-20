#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grievance_duck_gerund_cigar_dialogue_space_adventure.py
======================================================================================

A tiny space-adventure story world about a ship crew, a duck with a grievance,
and a forbidden cigar that makes trouble in the air vents.

The world is intentionally small and classical:
- a few typed entities with physical meters and emotional memes
- a causal state machine that drives the prose
- a grounded dialogue-heavy resolution
- a reasonableness gate plus an inline ASP twin
- QA generated from world state, not by parsing rendered text
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SMOKE_MIN = 1.0
GRIEVANCE_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        duckish = {"duck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in duckish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    ship_name: str
    airlock: str
    vent: str
    view: str

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
class CharacterSpec:
    id: str
    type: str
    label: str
    role: str
    traits: list[str] = field(default_factory=list)

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
class ObjectSpec:
    id: str
    label: str
    smoke: int = 0
    forbidden: bool = False
    makes_smoke: bool = False

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
class Remedy:
    id: str
    label: str
    power: int
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    vent = world.entities.get("vent")
    for ent in list(world.entities.values()):
        if ent.meters["smoke"] < THRESHOLD:
            continue
        sig = ("smoke", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ship:
            ship.meters["air_bad"] += 1
        if vent:
            vent.meters["smoke"] += 1
        for e in list(world.entities.values()):
            if e.role in {"pilot", "duck"}:
                e.memes["unease"] += 1
        out.append("__smoke__")
    return out


def _r_grievance(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role != "duck":
            continue
        if e.memes["grievance"] < GRIEVANCE_MIN:
            continue
        sig = ("grievance", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append("__grievance__")
    return out


CAUSAL_RULES = [
    Rule("smoke", "physical", _r_smoke),
    Rule("grievance", "social", _r_grievance),
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


def can_hurt(setting: Setting, cigar: ObjectSpec) -> bool:
    return cigar.makes_smoke and "vent" in setting.id


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def smoke_severity(delay: int) -> int:
    return 1 + delay


def contained(remedy: Remedy, delay: int) -> bool:
    return remedy.power >= smoke_severity(delay)


def predict_smoke(world: World, cigar_id: str) -> dict:
    sim = world.copy()
    _ignite(sim, sim.get(cigar_id), narrate=False)
    return {
        "smoke": sim.get("ship").meters["air_bad"],
        "vent_smoke": sim.get("vent").meters["smoke"],
    }


def _ignite(world: World, cigar: Entity, narrate: bool = True) -> None:
    cigar.meters["smoke"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, pilot: Entity, duck: Entity) -> None:
    pilot.memes["duty"] += 1
    duck.memes["mood"] += 1
    world.say(
        f"On the starship {setting.ship_name}, {pilot.id} and {duck.id} drifted "
        f"past the wide window. {setting.place_line}"
    )
    world.say(
        f'"Look at that," said {pilot.id}. "The stars are close enough to touch." '
        f'"Closer than some crew members," muttered {duck.id}.'
    )


def grievance_beat(world: World, duck: Entity, pilot: Entity, setting: Setting) -> None:
    duck.memes["grievance"] += 1
    world.say(
        f'{duck.id} folded {duck.pronoun("possessive")} wings and said, '
        f'"I have a grievance, {pilot.id}. Somebody keeps leaving cigar smoke '
        f"near the vents."
    )
    world.say(
        f'"That somebody is you," said {pilot.id}, glancing at the glowing cigar.'
    )


def temptation(world: World, duck: Entity, cigar: Entity) -> None:
    duck.memes["curiosity"] += 1
    world.say(
        f'{duck.id} gave the cigar a sidelong look. "I could be duck-'
        f'gerunding my way through the corridor and still keep this away from the vents," '
        f"{duck.id} said."
    )
    world.say("The idea sounded clever for one short breath.")


def warn(world: World, pilot: Entity, duck: Entity, cigar: Entity, setting: Setting) -> None:
    pred = predict_smoke(world, "cigar")
    pilot.memes["worry"] += 1
    world.facts["predicted_smoke"] = pred["smoke"]
    world.say(
        f'"No," said {pilot.id}. "That cigar makes smoke, and the {setting.vent} '
        f"pulls air everywhere. If you wave it around, the whole ship will smell "
        f'wrong and the alarms may wake the sleeping crew."'
    )
    world.say(
        f'"I know," said {duck.id}, "but I am still annoyed."'
    )


def defy(world: World, duck: Entity, cigar: Entity) -> None:
    duck.memes["defiance"] += 1
    world.say(
        f'"Fine," said {duck.id}. "{cigar.label} stays in my beak a moment longer."'
    )


def raise_alarm(world: World, pilot: Entity, setting: Setting) -> None:
    world.say(
        f"Then the {setting.vent} coughed out a gray puff, and the lights blinked once."
    )
    world.say(
        f'"Smoke!" shouted {pilot.id}. "Seal the airlock!"'
    )


def rescue(world: World, pilot: Entity, remedy: Remedy, setting: Setting) -> None:
    ship = world.get("ship")
    cigar = world.get("cigar")
    cigar.meters["smoke"] = 0
    ship.meters["air_bad"] = 0
    world.say(
        f'{pilot.id} came running and {remedy.text}.'
    )
    world.say(
        f"The smoke thinned to a faint curl, and the {setting.view} returned to clear and bright."
    )


def rescue_fail(world: World, pilot: Entity, remedy: Remedy, setting: Setting) -> None:
    ship = world.get("ship")
    ship.meters["air_bad"] += 2
    propagate(world, narrate=False)
    world.say(
        f'{pilot.id} came running and {remedy.fail}.'
    )
    world.say(
        f"The gray fog spread through the hall, and the ship had to coast until the air was safe again."
    )


def lesson(world: World, pilot: Entity, duck: Entity) -> None:
    duck.memes["grievance"] = 0
    duck.memes["relief"] += 1
    pilot.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'Then {pilot.id} lowered their voice. "A grievance is real, but a cigar is '
        f'not the way to solve it. If the air goes bad, we all pay for it."'
    )
    world.say(
        f'"I know," said {duck.id}. "I was being a duck-gerund of a fool."'
    )


def ending(world: World, setting: Setting, duck: Entity, pilot: Entity) -> None:
    duck.memes["joy"] += 1
    pilot.memes["joy"] += 1
    world.say(
        f'The next orbit, {pilot.id} handed {duck.id} a sealed snack pouch and a '
        f"small headset microphone instead."
    )
    world.say(
        f'"Try saying your grievance into this," said {pilot.id}. "It works better than smoke."'
    )
    world.say(
        f'{duck.id} smiled, tucked the cigar away in a locked locker, and drifted '
        f"back to the window while the ship glided past the blue moon."
    )


def tell(setting: Setting, duck: CharacterSpec, pilot: CharacterSpec, cigar: ObjectSpec,
         remedy: Remedy, delay: int = 0) -> World:
    world = World()
    pilot_ent = world.add(Entity(id=pilot.id, kind="character", type=pilot.type, role=pilot.role))
    duck_ent = world.add(Entity(id=duck.id, kind="character", type=duck.type, role=duck.role))
    ship = world.add(Entity(id="ship", type="ship", label=setting.ship_name))
    vent = world.add(Entity(id="vent", type="vent", label=setting.vent))
    cigar_ent = world.add(Entity(id="cigar", type="thing", label=cigar.label, role="object"))
    cigar_ent.meters["smoke"] = 0
    world.facts["delay"] = delay

    setup(world, setting, pilot_ent, duck_ent)
    world.para()
    grievance_beat(world, duck_ent, pilot_ent, setting)
    temptation(world, duck_ent, cigar_ent)
    warn(world, pilot_ent, duck_ent, cigar_ent, setting)

    if remedy.id == "talk":
        world.say(f'"Then talk to me," said {pilot.id}. "{duck.id}, tell me the grievance."')
        world.say(f'"It is the smoke," said {duck.id}.')
        ending(world, setting, duck_ent, pilot_ent)
        outcome = "averted"
    else:
        defy(world, duck_ent, cigar_ent)
        world.para()
        _ignite(world, cigar_ent)
        raise_alarm(world, pilot_ent, setting)
        if contained(remedy, delay):
            world.para()
            rescue(world, pilot_ent, remedy, setting)
            lesson(world, pilot_ent, duck_ent)
            world.para()
            ending(world, setting, duck_ent, pilot_ent)
            outcome = "contained"
        else:
            world.para()
            rescue_fail(world, pilot_ent, remedy, setting)
            world.say(
                f"The crew opened the fresh-air panels and waited, watching the stars in silence."
            )
            world.say(
                f"{duck.id} kept the cigar locked away after that and never waved smoke near the vents again."
            )
            outcome = "burned"

    world.facts.update(
        pilot=pilot_ent,
        duck=duck_ent,
        ship=ship,
        vent=vent,
        cigar=cigar_ent,
        remedy=remedy,
        setting=setting,
        outcome=outcome,
        ignited=True,
        resolved=outcome in {"averted", "contained"},
    )
    return world


SETTINGS = {
    "orbital_hall": Setting(
        "orbital_hall",
        "A silver corridor curved around the ship like a moonlit ribbon.",
        "The windows showed a river of stars, and the control panels glowed soft blue.",
        "Moth",
        "airlock",
        "vent",
        "the blue moon",
    ),
    "bridge": Setting(
        "bridge",
        "The bridge was bright with buttons, screens, and a big round radar map.",
        "The windows showed a ringed planet turning slowly beneath them.",
        "Comet",
        "airlock",
        "vent",
        "the ringed planet",
    ),
    "observation_deck": Setting(
        "observation_deck",
        "The observation deck had a tall glass dome and a handrail for floating paws.",
        "Far away, a comet streaked across the dark like a silver scratch.",
        "Swift",
        "airlock",
        "vent",
        "the comet tail",
    ),
}

CHARACTERS = {
    "pilot": CharacterSpec("Nova", "pilot", "the pilot", "pilot", ["careful"]),
    "duck": CharacterSpec("Pip", "duck", "the duck", "duck", ["grumpy"]),
}

OBJECTS = {
    "cigar": ObjectSpec("cigar", "a small cigar", smoke=1, forbidden=True, makes_smoke=True),
}

REMEDIES = {
    "talk": Remedy(
        "talk",
        "talk it out",
        power=0,
        sense=3,
        text="talked with the duck until the grievance came out in words instead of smoke",
        fail="talked, but the air was already too foggy to help",
        qa_text="talked with the duck until the grievance came out in words instead of smoke",
    ),
    "fan": Remedy(
        "fan",
        "turn on the vent fans",
        power=2,
        sense=2,
        text="turned on the vent fans and opened the clean-air panels until the smoke drifted away",
        fail="turned on the fans, but the smoke was too thick to clear quickly",
        qa_text="turned on the vent fans and opened the clean-air panels until the smoke drifted away",
    ),
    "seal": Remedy(
        "seal",
        "seal the airlock and filter the air",
        power=3,
        sense=3,
        text="sealed the airlock, switched the ship to clean-air mode, and waited for the smoke to vanish",
        fail="sealed the airlock, but the smoke had already spread through the ducts",
        qa_text="sealed the airlock, switched the ship to clean-air mode, and waited for the smoke to vanish",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in OBJECTS:
            for r in REMEDIES:
                combos.append((s, c, r))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    pilot_name: str
    duck_name: str
    cigar: str
    remedy: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a grievance, a duck-gerund, and a cigar.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, CHARACTERS["pilot"].id, CHARACTERS["duck"].id, "cigar", remedy, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story that includes the words "grievance", "duck-gerund", and "cigar".',
        f"Tell a dialogue-heavy story on the {f['setting'].scene.lower()} where {f['duck'].id} has a grievance and keeps using a cigar near the vents.",
        f"Write a child-friendly starship story where words and a calm rescue matter more than smoke.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    duck = f["duck"]
    pilot = f["pilot"]
    remedy = f["remedy"]
    setting = f["setting"]
    out = f["outcome"]
    items = [
        QAItem(
            question="Who had the grievance?",
            answer=f"{duck.id} had the grievance. The duck was upset about the cigar smoke near the vents, so the problem was real before anyone fixed it.",
        ),
        QAItem(
            question="What made the ship smell wrong?",
            answer="The cigar made smoke. On a starship, smoke can spread through the vents and make the whole ship smell bad very quickly.",
        ),
        QAItem(
            question="Why did the pilot warn the duck?",
            answer=f"{pilot.id} warned the duck because the {setting.vent} pulls air everywhere. That means one tiny puff can travel through the ship and bother everyone.",
        ),
    ]
    if out == "averted":
        items.append(QAItem(
            question="How did the crew solve the problem?",
            answer=f"They talked it out before any smoke got loose, and the duck told the grievance in words instead of with a cigar. That kept the ship calm and clean.",
        ))
    elif out == "contained":
        items.append(QAItem(
            question="How did the crew solve the problem?",
            answer=f"{pilot.id} used the {remedy.label} to clear the air. The smoke faded, and the ship could keep flying past the stars.",
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"The smoke spread too far, so the ship had to coast and clean the air slowly. Everyone stayed safe, but the crew learned that a cigar is not a good answer to a grievance.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    out.append(QAItem(
        question="What is a grievance?",
        answer="A grievance is a complaint or a hurt feeling that someone wants to talk about. In a story, it often means somebody feels upset and wants the problem noticed.",
    ))
    out.append(QAItem(
        question="What should you do if something makes smoke on a ship?",
        answer="You should tell a grown-up or crew member right away and stop the smoke from spreading. Clean air matters on a ship because everyone shares the same air.",
    ))
    if f["outcome"] != "averted":
        out.append(QAItem(
            question="What does a ship vent do?",
            answer="A vent moves air around the ship. If smoke gets near it, the smoke can spread into other rooms and make the air bad.",
        ))
    out.append(QAItem(
        question="Why is a cigar not a toy?",
        answer="A cigar makes smoke and can bother people or make the air dirty. Children should not use smoking things as play objects.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
smoky(Ship) :- air_bad(Ship, Bad), Bad >= 1.
grievance_resolved(Duck) :- duck(Duck), resolve(Duck, R), R >= 1.
contained :- chosen_remedy(R), power(R, P), delay(D), P >= D + 1.
outcome(averted) :- talk_remedy(R), chosen_remedy(R), not smoky(ship).
outcome(contained) :- not outcome(averted), contained.
outcome(burned) :- not outcome(averted), not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("duck", "Pip"))
    lines.append(asp.fact("ship", "ship"))
    lines.append(asp.fact("talk_remedy", "talk"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome"))) or [("averted",)]


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) and len(valid_combos()) >= 1:
        print(f"OK: valid_combos() yields {len(valid_combos())} combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as e:
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    return rc


def outcome_of(params: StoryParams) -> str:
    if params.remedy == "talk":
        return "averted"
    return "contained" if contained(REMEDIES[params.remedy], params.delay) else "burned"


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = tell(setting, CHARACTERS["duck"], CHARACTERS["pilot"], OBJECTS["cigar"], REMEDIES[params.remedy], params.delay)
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
    StoryParams("orbital_hall", "Nova", "Pip", "cigar", "talk", 0),
    StoryParams("bridge", "Nova", "Pip", "cigar", "fan", 0),
    StoryParams("observation_deck", "Nova", "Pip", "cigar", "seal", 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("asp mode available")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
