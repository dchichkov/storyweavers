#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tidal_foreshadowing_folk_tale.py
=================================================================

A standalone story world for a small folk-tale domain built around a
tidal shoreline, a quiet warning, and a foreshadowed rescue.

Premise:
- A child and a guardian live near the sea.
- The child wants to visit a tidal path, reef, or cove at the wrong time.
- Small clues foreshadow that the water is changing.
- The guardian notices the signs, warns in time, and the pair choose a safer way.
- The ending proves what changed: the sea still moves, but the children learned
  to read it and keep their lantern, boots, and basket dry.

This script follows the Storyweavers contract:
- stdlib only
- StoryParams, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- Python reasonableness gate plus inline ASP twin
- three Q&A sets grounded in simulated state
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
    shore: str
    safe_way: str
    foreshadow: str
    tide_word: str = "tidal"
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
class TideHazard:
    id: str
    label: str
    danger: str
    warning_sign: str
    catches: set[str] = field(default_factory=set)
    pulls: int = 1
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
class SafeAction:
    id: str
    label: str
    phrase: str
    result: str
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["water"] < THRESHOLD:
            continue
        sig = ("wet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["unease"] += 1
        out.append("__wet__")
    return out


def _r_rise(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["alert"] < THRESHOLD:
            continue
        sig = ("rise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["clarity"] += 1
        out.append("__rise__")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("rise", "social", _r_rise)]


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


def tide_at_risk(place: Place, hazard: TideHazard) -> bool:
    return bool(place.shore in hazard.catches)


def sensible_actions() -> list[SafeAction]:
    return [a for a in ACTIONS.values() if a.id in {"wait_high_tide", "take_high_path", "mark_stone"}]


def best_action() -> SafeAction:
    return max(ACTIONS.values(), key=lambda a: a.tags.__len__())


def tide_strength(delay: int, moon: str) -> int:
    return delay + (2 if moon == "full" else 1)


def can_reach_safely(action: SafeAction, delay: int, moon: str) -> bool:
    return action.id != "cross_bare_reef" and tide_strength(delay, moon) <= 2


def would_listen(guardian_trait: str, child_age: int, guardian_age: int) -> bool:
    return guardian_trait in {"wise", "careful", "patient"} and guardian_age > child_age


def predict_tide(world: World, place_id: str) -> dict:
    sim = world.copy()
    _do_tide(sim, narrate=False)
    place = sim.get(place_id)
    return {"wet": place.meters["water"] >= THRESHOLD, "alert": sim.get("child").memes["alert"]}


def _do_tide(world: World, narrate: bool = True) -> None:
    for eid in ("path", "basket", "boots"):
        if eid in world.entities:
            world.get(eid).meters["water"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, guardian: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    guardian.memes["watchful"] += 1
    world.say(
        f"In a little village by the gray sea, {child.id} and {guardian.id} lived "
        f"beside {place.label}. The old lantern hung by the door, and the wind knew "
        f"their names."
    )
    world.say(
        f"{place.foreshadow} {place.safe_way}."
    )


def want_adventure(world: World, child: Entity, place: Place, hazard: TideHazard) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} pointed to the shore and said, 'I want to go to the {place.shore}.' "
        f"{child.pronoun().capitalize()} liked the place where the shells clicked and the water made a tidal song."
    )
    world.say(
        f"But the tide was famous for {hazard.warning_sign}; even the gulls seemed to know it."
    )


def warn(world: World, guardian: Entity, child: Entity, place: Place, hazard: TideHazard, moon: str) -> None:
    pred = predict_tide(world, "path")
    guardian.memes["clarity"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{guardian.id} looked at the moon and the dark line on the water. "
        f"'{child.id}, do not cross the {place.shore} now,' {guardian.pronoun()} said. "
        f"'The {hazard.label} is pulling in, and the stones may grow slick.'"
    )


def disregard_or_listen(world: World, child: Entity, guardian: Entity, hazard: TideHazard) -> bool:
    if would_listen("wise", child.age, guardian.age):
        child.memes["trust"] += 1
        guardian.memes["peace"] += 1
        world.say(
            f"{child.id} heard the warning and held still. The little basket stayed by the door, and the boots waited in a dry row."
        )
        return True
    child.memes["stubborn"] += 1
    world.say(
        f"{child.id} tried to hurry toward the shore anyway, but the old warning still echoed in {child.pronoun('possessive')} ears."
    )
    return False


def tide_rolls(world: World, hazard: TideHazard, place: Place) -> None:
    _do_tide(world)
    world.say(
        f"Then the tide came in with a soft rush. It reached the {place.shore}, touched the path, and wrapped the stones in cold water."
    )


def rescue(world: World, guardian: Entity, child: Entity, action: SafeAction, place: Place) -> None:
    world.say(
        f"{guardian.id} took {child.pronoun('possessive')} hand and led {child.pronoun('object')} to the {action.label}. "
        f"{action.phrase.capitalize()}, and soon the pair were safe above the wet line."
    )
    world.say(
        f"The sea kept moving, but {place.label} stayed dry where they had chosen to stand."
    )


def ending_image(world: World, child: Entity, guardian: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    guardian.memes["joy"] += 1
    world.say(
        f"At sunset, {child.id} hung the lantern high and watched the bright water from the safe hill. "
        f"{place.label.capitalize()} glimmered below like a silver ribbon, and {child.id} remembered the warning before the wave."
    )


def tell(place: Place, hazard: TideHazard, action: SafeAction, moon: str,
         child_name: str = "Mina", child_gender: str = "girl",
         guardian_name: str = "Grandmother", guardian_gender: str = "woman",
         guardian_trait: str = "wise", delay: int = 0,
         child_age: int = 6, guardian_age: int = 58) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=child_age))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_gender, role="guardian", age=guardian_age,
                                traits=[guardian_trait]))
    world.add(Entity(id="path", type="thing", label="the path"))
    world.add(Entity(id="boots", type="thing", label="the boots"))
    world.add(Entity(id="basket", type="thing", label="the basket"))

    opening(world, child, guardian, place)
    world.para()
    want_adventure(world, child, place, hazard)
    warn(world, guardian, child, place, hazard, moon)
    listened = disregard_or_listen(world, child, guardian, hazard)
    world.para()
    if not listened:
        tide_rolls(world, hazard, place)
        world.say(
            f"{child.id} stopped at the last moment and stared at the water. The foreshadowing had been true."
        )
    rescue(world, guardian, child, action, place)
    world.para()
    ending_image(world, child, guardian, place)
    world.facts.update(
        child=child, guardian=guardian, place=place, hazard=hazard, action=action,
        moon=moon, delay=delay, outcome="safe", listened=listened
    )
    return world


PLACES = {
    "harbor": Place("harbor", "the harbor", "harbor steps", "the high stone lane",
                    "At dawn, the tide left a wet lace on the harbor steps, as if the sea were writing a warning.", tags={"harbor"}),
    "cove": Place("cove", "the cove", "cove path", "the cliff road",
                  "Before noon, the gulls cried and the pool at the cove rose twice, as though the water were remembering something.", tags={"cove"}),
    "bridge": Place("bridge", "the river mouth bridge", "bridge stones", "the watch path",
                    "In the moonlight, the reeds bent one way and the water whispered under the bridge, setting up a warning.", tags={"bridge"}),
}

HAZARDS = {
    "incoming_tide": TideHazard("incoming_tide", "incoming tide", "wet stones and trapped feet",
                                "the shore rising fast", catches={"harbor steps", "cove path", "bridge stones"},
                                pulls=2, tags={"tide", "water"}),
    "sudden_wave": TideHazard("sudden_wave", "sudden wave", "a rush of water",
                              "a white line far out at sea", catches={"harbor steps", "cove path"},
                              pulls=3, tags={"wave", "water"}),
}

ACTIONS = {
    "wait_high_tide": SafeAction("wait_high_tide", "the high lane", "waited until the tide turned",
                                 "the path cleared again", tags={"wait"}),
    "take_high_path": SafeAction("take_high_path", "the high path", "climbed to the high path",
                                 "the shoes stayed dry", tags={"path"}),
    "mark_stone": SafeAction("mark_stone", "the marker stone", "placed a shell by the marker stone",
                             "the warning would be remembered", tags={"mark"}),
    "cross_bare_reef": SafeAction("cross_bare_reef", "the reef", "crossed the reef",
                                  "the feet would get soaked", tags={"risk"}),
}

MOONS = ["new", "half", "full"]

GIRL_NAMES = ["Mina", "Elsa", "Nora", "Wren", "Lina", "Ada", "Tess", "Ivy"]
BOY_NAMES = ["Pip", "Jory", "Oren", "Finn", "Theo", "Milo", "Ben", "Rafe"]
TRAITS = ["wise", "careful", "patient", "soft-spoken", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for hid, hazard in HAZARDS.items():
            for aid, action in ACTIONS.items():
                if tide_at_risk(place, hazard) and can_reach_safely(action, 0, "new"):
                    combos.append((pid, hid, aid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    hazard: str
    action: str
    child: str
    child_gender: str
    guardian: str
    guardian_gender: str
    guardian_trait: str
    moon: str
    delay: int = 0
    child_age: int = 6
    guardian_age: int = 58
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


KNOWLEDGE = {
    "tide": [("What is a tide?", "A tide is the sea rising and falling each day. It can leave paths wet, then cover them again.")],
    "harbor": [("What is a harbor?", "A harbor is a safe place near the water where boats can stop.")],
    "cove": [("What is a cove?", "A cove is a small, sheltered place by the sea, often with rocks around it.")],
    "bridge": [("Why can bridge stones be slippery?", "Water and sea spray can make stones slick, so it is smart to walk carefully.")],
    "wave": [("What is a wave?", "A wave is a moving rise of water. Big waves can splash far onto the shore.")],
    "water": [("Why do people watch the water near the shore?", "Because the water can change fast, and a careful person wants to stay safe.")],
    "wait": [("Why is waiting sometimes the safest choice?", "Waiting can let danger pass. Then you can do the same thing later, but more safely.")],
    "path": [("What is a path?", "A path is a place to walk. Near the sea, some paths can disappear when the tide comes in.")],
    "mark": [("Why leave a marker?", "A marker helps people remember a warning or a safe way back.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale style story with the word 'tidal' about {f['child'].id}, who wants to go near {f['place'].label}, but a warning sign foreshadows danger.",
        f"Tell a short seaside tale where a {f['guardian'].label_word if f['guardian'].label_word else 'guardian'} notices the changing water before {f['child'].id} reaches the shore.",
        f"Write a gentle story for a young child in which foreshadowing about the {f['hazard'].label} leads to a safe ending by the sea.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guardian, place, hazard, action = f["child"], f["guardian"], f["place"], f["hazard"], f["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {guardian.id}, who live near {place.label} and learn to read the sea together."),
        ("What warning did the story foreshadow?",
         f"The story foreshadowed that {hazard.label} would reach the shore and make the stones wet. That is why the warning signs mattered before anyone stepped onto the path."),
        ("How did {0} and {1} stay safe?".format(child.id, guardian.id),
         f"They stayed safe by choosing {action.label} instead of crossing the dangerous shore. The sea kept moving, but they waited for a better time.")
    ]
    if f["listened"]:
        qa.append(("What did {0} do when warned?".format(child.id),
                   f"{child.id} listened right away and did not rush forward. The calm choice let the foreshadowed danger stay only a warning."))
    else:
        qa.append(("What happened when {0} did not listen at first?".format(child.id),
                   f"{child.id} almost went on, but the tide rolled in and proved the warning true. The story then turned toward safety before anything bad happened."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["hazard"].tags) | set(world.facts["place"].tags) | set(world.facts["action"].tags)
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
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
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "incoming_tide", "wait_high_tide", "Mina", "girl", "Grandmother", "woman", "wise", "full"),
    StoryParams("cove", "sudden_wave", "take_high_path", "Pip", "boy", "Grandfather", "man", "patient", "half"),
    StoryParams("bridge", "incoming_tide", "mark_stone", "Nora", "girl", "Aunt", "woman", "careful", "new"),
]


def explain_rejection(place: Place, hazard: TideHazard, action: SafeAction) -> str:
    return (
        f"(No story: {action.label} does not properly answer the danger at {place.label}. "
        f"This world only tells stories where the foreshadowing points to a real tidal risk and the ending choice fits it.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "safe"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("shore", pid, p.shore))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("catches", hid, *sorted(h.catches)[0:1]) if False else asp.fact("pulls", hid, h.pulls))
        for c in sorted(h.catches):
            lines.append(asp.fact("catches", hid, c))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("safe", aid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, H, A) :- place(P), hazard(H), action(A), shore(P, S), catches(H, S), safe(A).
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    smoke = generate(CURATED[0])
    if not smoke.story or "tidal" not in smoke.story:
        print("MISMATCH: smoke story failed.")
        rc = 1
    else:
        print("OK: smoke story generated.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tidal folk-tale story world with foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--guardian")
    ap.add_argument("--guardian-trait", choices=["wise", "careful", "patient", "soft-spoken", "steady"])
    ap.add_argument("--moon", choices=MOONS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, action = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    guardian_gender = rng.choice(["woman", "man"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["Grandmother", "Grandfather", "Aunt", "Uncle"])
    trait = args.guardian_trait or rng.choice(TRAITS)
    moon = args.moon or rng.choice(MOONS)
    return StoryParams(place, hazard, action, child, child_gender, guardian, guardian_gender, trait, moon)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], HAZARDS[params.hazard], ACTIONS[params.action],
                 params.moon, params.child, params.child_gender, params.guardian,
                 params.guardian_gender, params.guardian_trait, params.delay,
                 params.child_age, params.guardian_age)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.child} at {p.place} ({p.hazard}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
