#!/usr/bin/env python3
"""
A tiny mythic storyworld about a hollow place, an iridescent treasure, repeated
warnings, and a brave choice made with care.
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



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Chamber:
    place: str = "the hollow hill"
    echoing: bool = True
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    risk: str
    ward: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Omen:
    id: str
    line: str
    warning: str
    tag: str
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


class World:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Chamber(place="the hollow hill", echoing=True, affords={"descent", "listen", "carry"})
RELICS = {
    "gem": Relic(
        id="gem",
        label="iridescent gem",
        phrase="an iridescent gem from the old shrine",
        risk="shadow-wear",
        ward="lamplight",
        genders={"girl", "boy"},
    ),
    "cup": Relic(
        id="cup",
        label="iridescent cup",
        phrase="an iridescent cup with a thin gold rim",
        risk="crack-wear",
        ward="careful hands",
        genders={"girl", "boy"},
    ),
}
OMENS = {
    "echo": Omen(id="echo", line="The hollow hill answered with its own voice.", warning="listen twice", tag="repetition"),
    "mist": Omen(id="mist", line="A pale mist curled around the steps like a sleeping snake.", warning="go slowly", tag="cautionary"),
}
NAMES = {
    "girl": ["Mira", "Nia", "Lena", "Tala"],
    "boy": ["Eli", "Soren", "Kian", "Orin"],
}
TRAITS = ["quiet", "stern", "curious", "gentle", "patient"]
RITES = ["descend", "listen", "carry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, chamber in {"hill": SETTING}.items():
        for act in chamber.affords:
            for relic_id, relic in RELICS.items():
                combos.append((place, act, relic_id))
    return combos


@dataclass
class StoryParams:
    place: str
    rite: str
    relic: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic hollow-hill storyworld with iridescent relics.")
    ap.add_argument("--place", choices=["hill"])
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(rite: str, relic: Relic) -> str:
    return f"(No story: {rite} would not endanger the {relic.label}, so there is no true cautionary choice.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    rite = getattr(args, "rite", None) or rng.choice(RITES)
    relic_id = getattr(args, "relic", None) or rng.choice(list(RELICS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    relic = _safe_lookup(RELICS, relic_id)
    if gender not in relic.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "rite", None) and getattr(args, "relic", None) and rite not in RITES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place="hill", rite=rite, relic=relic_id, name=name, gender=gender, trait=trait)


def _narrate_repeat(world: World, hero: Entity) -> None:
    world.say("Twice the old warning was spoken, and twice the hollow hill answered back.")
    hero.memes["attention"] += 1


def _narrate_caution(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["caution"] += 1
    world.say(f'"Go slowly," the whisper said. "The {relic.label} is bright, but the path is narrow."')


def _narrate_bravery(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(f"{hero.pronoun().capitalize()} took a steady breath and stepped on anyway, brave but careful.")


def _resolve(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["peace"] += 1
    world.say(
        f"At last {hero.id} lifted the {relic.label} with careful hands, and its colors moved like fish in sunlight."
    )
    world.say(f"The hollow hill grew quiet, as if it had been waiting for a brave listener all along.")


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type="elder"))
    relic = world.add(Entity(id="relic", type=_safe_lookup(RELICS, params.relic).id, label=_safe_lookup(RELICS, params.relic).label, phrase=_safe_lookup(RELICS, params.relic).phrase))
    world.facts.update(hero=hero, elder=elder, relic=relic, params=params)

    world.say(f"In the days when the hollow hill still remembered names, there lived a {params.trait} child named {hero.id}.")
    world.say(f"{hero.id} loved to go to {SETTING.place} and {params.rite} where the old songs made the stones glow.")
    world.say(f"One evening, the elders showed {hero.id} {relic.phrase}.")

    world.para()
    _narrate_repeat(world, hero)
    _narrate_caution(world, hero, relic)
    world.say(f"{hero.id} wanted to {params.rite} deeper into the cave, even though the shadowed floor looked slick and strange.")
    _narrate_bravery(world, hero, relic)
    world.say(f"Still, {hero.id} remembered the warning and held the lantern close.")

    world.para()
    world.say(f"Then the way narrowed, and the {relic.label} began to gleam with iridescent fire.")
    _resolve(world, hero, relic)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    return [
        'Write a short myth about a hollow hill, an iridescent treasure, and a child who listens to warnings.',
        f"Tell a gentle mythic story about {p.name}, who wants to {p.rite} in the hollow hill but learns caution before bravery.",
        f'Write a child-friendly myth that includes the words "hollow" and "iridescent" and ends in a quiet, shining discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    relic: Entity = _safe_fact(world, f, "relic")
    p: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {p.trait} {p.gender} child who visits the hollow hill.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the hill?",
            answer=f"{hero.id} wanted to {p.rite} deeper into the hollow hill and come close to the iridescent {relic.label}.",
        ),
        QAItem(
            question=f"Why was the warning important?",
            answer=f"The warning mattered because the path was narrow and strange, so {hero.id} needed caution before bravery.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.id} handled the {relic.label} carefully, and the hollow hill became quiet instead of fearful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does hollow mean?", answer="Hollow means empty inside, like a cave or a tree trunk with space in it."),
        QAItem(question="What does iridescent mean?", answer="Iridescent means shining with changing colors, like a soap bubble or a beetle shell."),
        QAItem(question="Why are warnings useful?", answer="Warnings help people avoid danger and make safer choices."),
        QAItem(question="What is bravery?", answer="Bravery is doing something hard or scary while still being careful and strong."),
        QAItem(question="Why can repetition matter in a story?", answer="Repetition can make an important message easier to remember."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,R,G) :- place(P), rite(R), relic(RL), gender(G), permits(R,RL,G), available(P,R,RL).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "hill"))
    for rite in RITES:
        lines.append(asp.fact("rite", rite))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for g in sorted(relic.genders):
            lines.append(asp.fact("gender", g))
        lines.append(asp.fact("permits", "descend", rid, "girl"))
        lines.append(asp.fact("permits", "descend", rid, "boy"))
        lines.append(asp.fact("permits", "listen", rid, "girl"))
        lines.append(asp.fact("permits", "listen", rid, "boy"))
        lines.append(asp.fact("permits", "carry", rid, "girl"))
        lines.append(asp.fact("permits", "carry", rid, "boy"))
        lines.append(asp.fact("available", "hill", "descend", rid))
        lines.append(asp.fact("available", "hill", "listen", rid))
        lines.append(asp.fact("available", "hill", "carry", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {( "hill", r, g) for _, r, g in [(p[0], p[1], p[2]) for p in valid_combos()]}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(python_set - clingo_set))
    print(" only in ASP:", sorted(clingo_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for rite in RITES:
        for relic_id, relic in RELICS.items():
            for g in relic.genders:
                out.append(("hill", rite, relic_id))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(World(SETTING), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="hill", rite="listen", relic="gem", name="Mira", gender="girl", trait="curious"),
    StoryParams(place="hill", rite="carry", relic="cup", name="Orin", gender="boy", trait="gentle"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "gender", None) and getattr(args, "relic", None) and getattr(args, "gender", None) not in _safe_lookup(RELICS, getattr(args, "relic", None)).genders:
        pass
    return StoryParams(
        place="hill",
        rite=getattr(args, "rite", None) or rng.choice(RITES),
        relic=getattr(args, "relic", None) or rng.choice(list(RELICS)),
        name=getattr(args, "name", None) or rng.choice(NAMES[getattr(args, "gender", None) or rng.choice(['girl', 'boy'])]),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
