#!/usr/bin/env python3
"""
storyworlds/worlds/hallelujahs_souvlaki_reggae_bad_ending_space_adventure.py
============================================================================

A standalone story world for a tiny **space adventure** with three seed words:
**hallelujahs**, **souvlaki**, and **reggae**.  The stories are child-facing,
state-driven, and deliberately small: a young crew is hungry and excited on a
tiny ship, music and food make the cabin lively, then one risky choice causes a
loss the crew cannot fully fix.  The ending is a **bad ending**: everyone gets
safe, but the mission fails and the ship drifts away from what they hoped to do.

The world model tracks physical meters and emotional memes, uses a simple
reasonableness gate, provides an inline ASP twin, and exposes the standard
storyworld CLI.
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
class Ship:
    id: str
    name: str
    place: str
    docked: bool = True
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
class Tune:
    id: str
    label: str
    phrase: str
    mood: str
    volume: int
    boosts: int
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
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
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
    risk: str
    severity: int
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
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.ship: Optional[Ship] = None
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
        clone.ship = copy.deepcopy(self.ship)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

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


def _r_sing(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["song"] < THRESHOLD:
            continue
        sig = ("sing", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        if world.ship:
            world.ship.memes["cheer"] += 1
        out.append("__sing__")
    return out


def _r_risky_food(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["sauce"] < THRESHOLD:
            continue
        sig = ("sauce", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["messy"] += 1
        if world.ship:
            world.ship.meters["sticky"] += 1
        out.append("__sticky__")
    return out


def _r_hazard(world: World) -> list[str]:
    out: list[str] = []
    if world.ship and world.ship.meters["sticky"] >= THRESHOLD:
        sig = ("hazard", world.ship.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.ship.meters["risk"] += 1
            out.append("__hazard__")
    return out


CAUSAL_RULES = [
    Rule("sing", "social", _r_sing),
    Rule("risky_food", "physical", _r_risky_food),
    Rule("hazard", "physical", _r_hazard),
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


def tune_is_reasonable(tune: Tune, hazard: Hazard) -> bool:
    return tune.boosts >= SENSE_MIN and hazard.severity >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not any(t.boosts >= SENSE_MIN for t in TUNES.values()):
        return combos
    for ship in SHIPS:
        for tune_id, tune in TUNES.items():
            for hazard_id, hz in HAZARDS.items():
                if tune_is_reasonable(tune, hz):
                    combos.append((ship, tune_id, hazard_id))
    return combos


def best_tune() -> Tune:
    return max(TUNES.values(), key=lambda t: t.boosts)


def predict_bad(world: World, tune: Tune, snack: Snack, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_scene(sim, narrate=False, tune=tune, snack=snack, hazard=hazard)
    return {"risk": sim.ship.meters["risk"] if sim.ship else 0, "lost": sim.ship.meters["lost"] if sim.ship else 0}


def _do_scene(world: World, narrate: bool, tune: Tune, snack: Snack, hazard: Hazard) -> None:
    if world.ship:
        world.ship.meters["mission"] += 1
    for ent in list(world.entities.values()):
        ent.memes["joy"] += 1
    world.say(
        f"Deep in the little ship, the crew drifted past the blue stars, "
        f"and {world.facts['hero'].id} turned the cabin into a tiny concert."
    )
    world.say(
        f"{world.facts['hero'].id} sang {tune.phrase} in a bright voice, and "
        f"the whole room answered with hallelujahs."
    )
    world.say(
        f"Then the smell of {snack.smell} floated through the air. "
        f"The crew passed around {snack.phrase}, and the beat of reggae made "
        f"everyone tap their feet."
    )
    world.facts["predicted"] = predict_bad(world, tune, snack, hazard)
    if world.ship:
        world.ship.meters["mission"] += 1


def intro(world: World, hero: Entity, friend: Entity, ship: Ship) -> None:
    hero.memes["curious"] += 1
    friend.memes["curious"] += 1
    ship.meters["distance"] += 1
    world.say(
        f"On a small ship called {ship.name}, {hero.id} and {friend.id} floated "
        f"toward a faraway moon. {ship.place.capitalize()} looked quiet and bright."
    )


def snack_time(world: World, snack: Snack) -> None:
    world.facts["snack"] = snack
    world.say(
        f"They were hungry, so they opened a packet of {snack.label}. "
        f"It smelled warm and a little salty."
    )


def warning(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} pointed at the loose panel near the engine and whispered, "
        f"\"Careful. {hazard.label.capitalize()} could be a problem here.\""
    )


def mistake(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.meters["sauce"] += 1
    hero.memes["bold"] += 1
    world.say(
        f"{hero.id} reached too fast for the sauce, and a sticky drop splashed "
        f"onto the control panel by the engine."
    )
    propagate(world, narrate=False)
    world.say(
        f"{hazard.phrase} had already made the panel slippery, and the buttons "
        f"were not as easy to press anymore."
    )


def fail_turn(world: World, ship: Ship, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    ship.meters["risk"] += 1
    ship.meters["lost"] += 1
    hero.memes["fear"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"Then the ship shuddered. The sticky panel flickered, and the little "
        f"engine coughed instead of humming."
    )
    world.say(
        f"{hero.id} and {friend.id} pressed the stop button, but the ship had "
        f"already slipped off course."
    )
    world.say(
        f"Outside the window, the moon shrank behind them while the music faded "
        f"into the dark."
    )


def ending_bad(world: World, hero: Entity, friend: Entity, ship: Ship) -> None:
    hero.memes["sad"] += 1
    friend.memes["sad"] += 1
    ship.meters["lost"] += 1
    world.say(
        f"They were safe, but the mission was gone. No one got the moon samples, "
        f"and the tiny ship drifted farther and farther from the landing lights."
    )
    world.say(
        f"At the end, the crew sat quietly with cold souvlaki wrappers and a "
        f"silent radio, listening to the last soft reggae beat of the night."
    )


def tell(ship_def: Ship, tune: Tune, snack: Snack, hazard: Hazard,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Sol", friend_gender: str = "boy") -> World:
    world = World()
    world.ship = copy.deepcopy(ship_def)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="pilot"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="helper"))
    world.add(Entity(id="radio", type="thing", label="radio"))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["tune"] = tune
    world.facts["hazard"] = hazard

    intro(world, hero, friend, ship_def)
    world.para()
    snack_time(world, snack)
    warning(world, hero, friend, hazard)
    _do_scene(world, narrate=False, tune=tune, snack=snack, hazard=hazard)
    world.para()
    mistake(world, hero, hazard)
    fail_turn(world, world.ship, hero, friend, hazard)
    world.para()
    ending_bad(world, hero, friend, world.ship)

    world.facts.update(
        outcome="bad",
        mission_lost=True,
        risk=world.ship.meters["risk"] if world.ship else 0,
        song=tune,
        snack=snack,
    )
    return world


SHIPS = {
    "skiff": Ship("skiff", "Star Skiff", "the docking bay"),
    "comet": Ship("comet", "Comet Cart", "the little hangar"),
    "orbiter": Ship("orbiter", "Moon Orbiter", "the night dock"),
}

TUNES = {
    "hallelujahs": Tune("hallelujahs", "a cheerful chorus", "hallelujahs", "bright", 5, 3, {"song", "music"}),
    "reggae": Tune("reggae", "a reggae tune", "reggae", "bouncy", 4, 3, {"song", "music"}),
    "space_song": Tune("space_song", "a space song", "a space song", "glowy", 3, 2, {"song", "music"}),
}

SNACKS = {
    "souvlaki": Snack("souvlaki", "souvlaki", "warm souvlaki wraps", "grilled souvlaki", {"food"}),
    "pita": Snack("pita", "pita pockets", "soft pita pockets", "toasty pita", {"food"}),
}

HAZARDS = {
    "panel": Hazard("panel", "engine panel", "the engine panel", "sticky controls", 2, {"risk"}),
    "button": Hazard("button", "blue button", "the blue button", "a wrong button", 1, {"risk"}),
}


@dataclass
@dataclass
class StoryParams:
    ship: str
    tune: str
    snack: str
    hazard: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


GIRL_NAMES = ["Mina", "Luna", "Nia", "Iris", "Zara"]
BOY_NAMES = ["Sol", "Noah", "Toby", "Milo", "Kai"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short space-adventure story for a little child that includes the words hallelujahs, souvlaki, and reggae.",
        f"Tell a story about {f['hero'].id} and {f['friend'].id} on a tiny ship, with music, snacks, and a bad ending.",
        "Write a simple space story where a happy cabin turns risky and the mission is lost by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    tune = f["tune"]
    snack = f["snack"]
    hazard = f["hazard"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two crew members on a tiny ship. They start out happy, but their trip goes badly at the end."),
        ("What did they hear and sing?",
         f"They sang {tune.phrase}, and the cabin filled with hallelujahs. The music made the ship feel lively for a while."),
        ("What snack did they share?",
         f"They shared {snack.phrase}. It smelled warm and tasty while they floated through space."),
        ("What went wrong?",
         f"{hero.id} made the control panel sticky near {hazard.label}. That made the ship slip off course and the mission failed."),
    ]
    if f.get("outcome") == "bad":
        qa.append((
            "How did the story end?",
            "It ended badly for the mission, even though the children were safe. The tiny ship drifted away, and they could not finish their trip."
        ))
        qa.append((
            "Why was the ending sad?",
            f"Because the ship lost its way and the moon goal was gone. They had music and food, but not a way to fix the damage in time."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tune"].tags) | set(world.facts["snack"].tags) | set(world.facts["hazard"].tags)
    out: list[tuple[str, str]] = []
    if "music" in tags:
        out.append(("What is reggae?", "Reggae is a style of music with a steady beat that makes people want to sway and tap along."))
        out.append(("What are hallelujahs?", "Hallelujahs are joyful shout-like words people sing when they feel happy or thankful."))
    if "food" in tags:
        out.append(("What is souvlaki?", "Souvlaki is a tasty food with grilled meat and bread or wraps. People often eat it as a meal or snack."))
    if "risk" in tags:
        out.append(("Why can a sticky control panel be dangerous?", "A sticky control panel can make buttons hard to use, which can cause a ship to go the wrong way."))
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
    if world.ship:
        lines.append(f"  ship     ({world.ship.name}) meters={dict((k, v) for k, v in world.ship.meters.items() if v)}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("skiff", "hallelujahs", "souvlaki", "panel", "Mina", "girl", "Sol", "boy"),
    StoryParams("comet", "reggae", "souvlaki", "button", "Luna", "girl", "Toby", "boy"),
    StoryParams("orbiter", "hallelujahs", "pita", "panel", "Kai", "boy", "Nia", "girl"),
]


def explain_rejection() -> str:
    return "(No story: the requested combo does not make a reasonable space-adventure risk.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for tid, t in TUNES.items():
        lines.append(asp.fact("tune", tid))
        lines.append(asp.fact("boosts", tid, t.boosts))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hid, h.severity))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(T) :- tune(T), boosts(T, B), sense_min(M), B >= M.
valid(S, T, H) :- ship(S), sensible(T), hazard(H).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
        print("only in ASP:", sorted(a - p))
        print("only in Python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a bad ending.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.tune and TUNES[args.tune].boosts < SENSE_MIN:
        raise StoryError("(No story: that tune is too weak to carry the adventure.)")
    if args.ship and args.tune and args.hazard:
        if (args.ship, args.tune, args.hazard) not in valid_combos():
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.tune is None or c[1] == args.tune)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, tune, hazard = rng.choice(sorted(combos))
    snack = args.snack or rng.choice(sorted(SNACKS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero])
    return StoryParams(ship, tune, snack, hazard, hero, hero_gender, friend, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SHIPS[params.ship], TUNES[params.tune], SNACKS[params.snack], HAZARDS[params.hazard],
                 params.hero, params.hero_gender, params.friend, params.friend_gender)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tunes: {', '.join(asp_sensible())}\n")
        for s, t, h in asp_valid_combos():
            print(f"  {s:8} {t:12} {h}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} on {p.ship}: {p.tune} + {p.snack} ({p.hazard})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
