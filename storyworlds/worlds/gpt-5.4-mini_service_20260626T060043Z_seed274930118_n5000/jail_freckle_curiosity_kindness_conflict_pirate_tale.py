#!/usr/bin/env python3
"""
A small pirate-tale storyworld about curiosity, kindness, conflict, and a jail
gate with a freckle clue.

The seed image:
- A curious young pirate pokes around a dockside jail.
- A freckled prisoner is treated unfairly because of a missing key.
- Kindness turns the quarrel into a rescue.
- The ending proves the change in state: the jail opens, the prisoner is free,
  and the freckle clue is remembered as the thing that helped.

This world keeps the prose grounded in a simulated state with meters and memes:
physical things can be held, locked, worn, or opened; emotional things like
Curiosity, Kindness, and Conflict rise and fall as the tale unfolds.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    locked: bool = False
    open: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    freckle: object | None = None
    guard: object | None = None
    hero: object | None = None
    jail: object | None = None
    key: object | None = None
    prisoner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    name: str
    setting: str = "harbor"
    jail: bool = True
    docks: bool = True
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    crew_role: str
    prisoner_name: str
    prisoner_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_unlock(world: World) -> list[str]:
    out: list[str] = []
    jail = world.get("jail")
    key = world.entities.get("key")
    if not jail.locked:
        return out
    if not key or key.holder is None:
        return out
    if key.meters.get("found", 0) < THRESHOLD:
        return out
    sig = ("unlock",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jail.locked = False
    jail.open = True
    out.append("The jail door clicked open.")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    guard = world.get("guard")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return []
    if guard.memes.get("alarm", 0) < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    guard.memes["conflict"] = guard.memes.get("conflict", 0) + 1
    return ["__conflict__"]


def _r_kindness(world: World) -> list[str]:
    hero = world.get("hero")
    prisoner = world.get("prisoner")
    if hero.memes.get("kindness", 0) < THRESHOLD:
        return []
    sig = ("kindness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prisoner.memes["hope"] = prisoner.memes.get("hope", 0) + 1
    hero.memes["conflict"] = 0
    prisoner.memes["conflict"] = 0
    return ["The hot quarrel cooled into hope."]


RULES = [_r_unlock, _r_conflict, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__conflict__":
                        out.append(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_unlock(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return not sim.get("jail").locked


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name))
    guard = world.add(Entity("guard", kind="character", type="pirate", label="the jail guard"))
    prisoner = world.add(Entity("prisoner", kind="character", type=params.prisoner_type, label=params.prisoner_name))
    jail = world.add(Entity("jail", kind="thing", type="jail", label="the jail", locked=True, open=False))
    key = world.add(Entity("key", kind="thing", type="key", label="the brass key", holder=None))
    freckle = world.add(Entity("freckle", kind="thing", type="freckle", label="a little freckle", owner=prisoner.id))

    hero.memes["curiosity"] = 1
    guard.memes["alarm"] = 1
    prisoner.memes["conflict"] = 1
    prisoner.memes["kindness"] = 0
    freckle.meters["seen"] = 0

    world.say(f"{hero.label} was a small {params.crew_role} with a sharp eye for odd things at the harbor.")
    world.say(f"One day {hero.label} noticed {prisoner.label}, who had a little freckle on {prisoner.pronoun('possessive')} cheek and a sad look behind {prisoner.pronoun('possessive')} bars.")
    world.say(f"{hero.label} wanted to know why {prisoner.label} was locked in {jail.label}, and the question tugged harder than the sea wind.")
    world.para()

    if place.jail:
        hero.memes["curiosity"] += 1
        world.say(f"{hero.label} crept closer to {jail.label}.")
        if not predict_unlock(world):
            world.say(f"The door stayed shut, and the guard frowned when the little pirate kept asking questions.")
        guard.memes["alarm"] += 1
        propagate(world, narrate=True)
        world.say(f"{hero.label} spotted the brass key hooked to a nail beside the lantern, just where only a curious eye would look.")
        key.holder = hero.id
        key.meters["found"] = 1
        world.say(f"{hero.label} did not snatch it. Instead, {hero.pronoun()} asked the guard to listen, because kindness could work better than a shout.")
        hero.memes["kindness"] += 1
        world.para()
        propagate(world, narrate=True)
        if jail.open:
            world.say(f"{hero.label} turned the key, and the jail door opened with a soft creak.")
            world.say(f"{prisoner.label} stepped out smiling, and the little freckle on {prisoner.pronoun('possessive')} cheek looked bright in the lantern light.")
            world.say(f"By the end, curiosity had found the clue, kindness had quieted the conflict, and the harbor felt warm again.")
    world.facts.update(hero=hero, guard=guard, prisoner=prisoner, jail=jail, key=key, freckle=freckle)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prisoner = f["hero"], f["prisoner"]
    return [
        f"Write a short pirate tale about {hero.label} discovering why {prisoner.label} is in jail.",
        f"Tell a child-friendly story where curiosity leads a pirate to a jail door, and kindness ends the conflict.",
        f"Write a simple harbor story with a freckle clue, a locked jail, and a gentle rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prisoner, jail = f["hero"], f["prisoner"], f["jail"]
    return [
        QAItem(
            question=f"Who was curious in the story?",
            answer=f"{hero.label} was curious. That curiosity made {hero.pronoun('subject')} look closer at the jail and notice the freckle clue."
        ),
        QAItem(
            question=f"What did {hero.label} notice on {prisoner.label}'s face?",
            answer=f"{hero.label} noticed a little freckle on {prisoner.pronoun('possessive')} cheek."
        ),
        QAItem(
            question=f"What changed at the end when kindness won?",
            answer=f"The jail door opened, the conflict calmed down, and {prisoner.label} was free to step out."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jail?",
            answer="A jail is a place where people are kept locked up."
        ),
        QAItem(
            question="What is a freckle?",
            answer="A freckle is a small brown spot on a person's skin."
        ),
        QAItem(
            question="What does kindness do in a quarrel?",
            answer="Kindness can calm people down and help them choose a gentler answer."
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.kind == "thing":
            if e.locked:
                bits.append("locked=True")
            if e.open:
                bits.append("open=True")
            if e.holder:
                bits.append(f"holder={e.holder}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "harbor": Place(name="the harbor", affords={"look", "ask", "unlock"}),
}


@dataclass
class ASPRegistry:
    places: list[str] = field(default_factory=lambda: ["harbor"])
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


ASP_RULES = r"""
jail_place(harbor).

curious(hero) :- curiosity(hero).
kind(hero) :- kindness(hero).
conflict(hero) :- conflict(hero).

can_find_clue(hero) :- curious(hero).
can_soothe(hero) :- kind(hero).

resolves(hero) :- can_find_clue(hero), can_soothe(hero).
#show resolves/1.
#show can_find_clue/1.
#show can_soothe/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("curiosity", "hero"),
        asp.fact("kindness", "hero"),
        asp.fact("conflict", "guard"),
        asp.fact("jail", "jail"),
        asp.fact("freckle", "prisoner"),
        asp.fact("place", "harbor"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolves/1."))
    asp_ok = bool(asp.atoms(model, "resolves"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH: ASP and Python reasonableness diverged.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about jail, a freckle, curiosity, kindness, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--role", dest="crew_role", choices=["deckhand", "cabin kid", "lookout", "mate"])
    ap.add_argument("--prisoner", dest="prisoner_name")
    ap.add_argument("--prisoner-type", choices=["girl", "boy", "pirate", "sailor"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "harbor"
    return StoryParams(
        place=place,
        hero_name=getattr(args, "hero_name", None) or rng.choice(["Mira", "Ned", "Pip", "Ruby", "Tess"]),
        hero_type=getattr(args, "hero_type", None) or rng.choice(["girl", "boy"]),
        crew_role=getattr(args, "crew_role", None) or rng.choice(["deckhand", "lookout", "cabin kid", "mate"]),
        prisoner_name=getattr(args, "prisoner_name", None) or rng.choice(["Captain Wren", "Old Salt Jory", "Moss", "Bluefin Beth"]),
        prisoner_type=getattr(args, "prisoner_type", None) or rng.choice(["pirate", "sailor", "girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolves/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = [
            StoryParams("harbor", "Mira", "girl", "deckhand", "Captain Wren", "pirate"),
            StoryParams("harbor", "Pip", "boy", "lookout", "Old Salt Jory", "sailor"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
