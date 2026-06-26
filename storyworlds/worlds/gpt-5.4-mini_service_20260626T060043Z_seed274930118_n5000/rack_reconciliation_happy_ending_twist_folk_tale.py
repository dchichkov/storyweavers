#!/usr/bin/env python3
"""
A small folk-tale storyworld about a village rack, a quarrel, a twist, and a
reconciliation that ends in a happy image.

Premise:
- In a little village, two kin may argue over a rack used for drying, hanging,
  or sorting treasured things.
- A wise elder or parent sees the trouble before it grows.
- A twist reveals the rack is needed for an unexpected, gentle purpose.
- The characters reconcile and end with a warm, happy ending.

The story is built from a simulated world model with physical meters and
emotional memes. The prose is driven by state changes rather than by swapping
words in a frozen paragraph.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    other: object | None = None
    rack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str = "the little village square"
    indoors: bool = False
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
class RackKind:
    id: str
    label: str
    phrase: str
    purpose: str
    unexpected_use: str
    twist: str
    endings: list[str]
    tags: set[str] = field(default_factory=set)
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
    rack: str
    setting: str
    hero: str
    hero_kind: str
    other: str
    other_kind: str
    elder: str
    elder_kind: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraph_breaks: list[int] = []
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "square": Setting(place="the little village square", indoors=False),
    "barn": Setting(place="the old barn by the lane", indoors=True),
    "cottage": Setting(place="the warm cottage hearth", indoors=True),
}

RACKS = {
    "cloak_rack": RackKind(
        id="cloak_rack",
        label="cloak rack",
        phrase="a sturdy wooden cloak rack",
        purpose="hold cloaks and hats",
        unexpected_use="hang a bundle of wet herbs and keep them safe from the mice",
        twist="the rack was not only for cloaks; it was the best place to dry the healer's herbs",
        endings=["the herbs dried neatly", "the cloak rack stood like a patient helper"],
        tags={"cloak", "herbs", "wood", "dry"},
    ),
    "fish_rack": RackKind(
        id="fish_rack",
        label="fish rack",
        phrase="a salt-scented fish rack",
        purpose="dry fish in the breeze",
        unexpected_use="turn a tearful feast into a shared feast when the fish were ready",
        twist="the rack had been waiting to make a feast, not a fuss",
        endings=["the fish shone silver and ready", "the rack smelled of supper and sea"],
        tags={"fish", "salt", "wood", "dry"},
    ),
    "apple_rack": RackKind(
        id="apple_rack",
        label="apple rack",
        phrase="an apple rack made of bent branches",
        purpose="store apples in tidy rows",
        unexpected_use="save windfallen apples for a sweet pie",
        twist="the rack hid a second purpose: it kept the rescued apples from bruising",
        endings=["the apples rested like little suns", "the rack kept the apples safe and round"],
        tags={"apple", "fruit", "wood", "store"},
    ),
}

# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def valid_combo(rack: RackKind, setting: Setting) -> bool:
    if rack.id == "fish_rack" and setting.indoors:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for rid, r in RACKS.items():
            if valid_combo(r, s):
                out.append((sid, rid))
    return out


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _set(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _bump(e: Entity, key: str, delta: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _mood(e: Entity, key: str, delta: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def introduce(world: World, hero: Entity, other: Entity, elder: Entity, rack: Entity) -> None:
    world.say(
        f"In the little village, {hero.id} was a bright {hero.type} who loved the old {rack.label}."
    )
    world.say(
        f"{other.id} also liked {rack.label}s, because {rack.label}s were useful and neat."
    )
    world.say(
        f"{elder.id}, the village elder, kept a calm eye on all such matters."
    )


def start_need(world: World, rack: Entity, setting: Setting) -> None:
    world.say(
        f"One day, the {rack.label} stood in {setting.place}, waiting for its proper work."
    )


def quarrel(world: World, hero: Entity, other: Entity, rack: Entity) -> None:
    _mood(hero, "want", 1)
    _mood(other, "want", 1)
    _mood(hero, "cross", 1)
    _mood(other, "cross", 1)
    world.say(
        f"{hero.id} wanted the {rack.label} first, but {other.id} wanted it too."
    )
    world.say(
        f"At once their voices rose like sparrows in a roof beam, and the day grew thin with fuss."
    )


def elder_warns(world: World, elder: Entity, hero: Entity, other: Entity, rack: Entity) -> None:
    _mood(elder, "worry", 1)
    world.say(
        f"{elder.id} lifted a hand and said, 'A useful thing can be shared before it is spoiled by sharp words.'"
    )
    world.say(
        f"Still, {hero.id} and {other.id} did not yet see the wisdom in that."
    )


def twist(world: World, rack: Entity, setting: Setting, elder: Entity) -> None:
    _set(rack, "revealed", 1)
    _bump(rack, "special", 1)
    world.say(
        f"Then the twist came. {elder.id} pointed to the {rack.label} and smiled."
    )
    world.say(rack.phrase.capitalize() + " was not just sitting there by chance.")
    world.say(rack.twist + ".")
    world.say(
        f"It was needed for a gentle task: {rack.unexpected_use}."
    )
    world.say(
        f"Now the rack's true purpose was clear, and the quarrel looked small beside it."
    )


def reconcile(world: World, hero: Entity, other: Entity, elder: Entity, rack: Entity) -> None:
    _mood(hero, "shame", 1)
    _mood(other, "shame", 1)
    _mood(hero, "kind", 1)
    _mood(other, "kind", 1)
    _mood(hero, "peace", 1)
    _mood(other, "peace", 1)
    world.say(
        f"{hero.id} looked at {other.id} and said sorry."
    )
    world.say(
        f"{other.id} said sorry too, and the two of them moved the {rack.label} together."
    )
    world.say(
        f"{elder.id} nodded, for the rack was helping them be useful instead of stubborn."
    )


def happy_ending(world: World, hero: Entity, other: Entity, elder: Entity, rack: Entity) -> None:
    _mood(hero, "joy", 2)
    _mood(other, "joy", 2)
    _mood(elder, "joy", 1)
    world.say(
        f"In the end, {hero.id} and {other.id} finished the work side by side."
    )
    world.say(
        f"The {rack.label} held its load neatly, and the village smell was all of wood, clean air, and good hope."
    )
    world.say(
        f"{elder.id} laughed softly, because the happy ending was simple: the same rack that caused the fuss had brought the family together."
    )
    world.say(
        f"Before sunset, everyone was smiling, and the little village seemed kinder than before."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def tell(rack_key: str, setting_key: str, hero_name: str, hero_kind: str,
         other_name: str, other_kind: str, elder_name: str, elder_kind: str) -> World:
    setting = _safe_lookup(SETTINGS, setting_key)
    rack_cfg = _safe_lookup(RACKS, rack_key)
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    other = world.add(Entity(id=other_name, kind="character", type=other_kind))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_kind))
    rack = world.add(Entity(id="rack", kind="thing", type="rack", label=rack_cfg.label, phrase=rack_cfg.phrase))

    world.facts.update(hero=hero, other=other, elder=elder, rack=rack, rack_cfg=rack_cfg, setting=setting)

    introduce(world, hero, other, elder, rack)
    world.para()
    start_need(world, rack, setting)
    quarrel(world, hero, other, rack)
    elder_warns(world, elder, hero, other, rack)
    world.para()
    twist(world, rack, setting, elder)
    reconcile(world, hero, other, elder, rack)
    happy_ending(world, hero, other, elder, rack)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rack_cfg: RackKind = _safe_fact(world, f, "rack_cfg")
    return [
        f'Write a short folk tale about a {rack_cfg.label} that begins with a quarrel and ends in a kind reconciliation.',
        f"Tell a child-friendly story where two village kin both want the {rack_cfg.label}, but a twist reveals its true purpose.",
        f'Write a simple happy-ending tale using the word "{rack_cfg.label}" and a warm village setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, other, elder, rack_cfg = f["hero"], f["other"], f["elder"], f["rack_cfg"]
    return [
        QAItem(
            question=f"Who wanted the {rack_cfg.label} first?",
            answer=f"{hero.id} wanted the {rack_cfg.label} first, and {other.id} wanted it too.",
        ),
        QAItem(
            question="What happened that made the quarrel seem smaller?",
            answer=f"The twist showed that the {rack_cfg.label} had a gentle purpose, so the fuss felt small beside it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The two kin said sorry, shared the work, and ended in a happy ending with smiles all around.",
        ),
        QAItem(
            question=f"What was the rack really for?",
            answer=f"It was really for {rack_cfg.purpose}, even though it looked ordinary at first.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "wood": [
        QAItem(
            question="What is wood used for?",
            answer="Wood can be used to make useful things like tables, racks, and shelves.",
        )
    ],
    "dry": [
        QAItem(
            question="Why do people dry things on a rack?",
            answer="People dry things on a rack so air can reach them all around and they do not stay wet or spoiled.",
        )
    ],
    "fish": [
        QAItem(
            question="Why do people dry fish?",
            answer="People dry fish so it keeps longer and can be saved for later meals.",
        )
    ],
    "herbs": [
        QAItem(
            question="Why are herbs kept safe while drying?",
            answer="Herbs are kept safe while drying so they stay fragrant and good to use in cooking or healing.",
        )
    ],
    "fruit": [
        QAItem(
            question="Why is fruit sometimes stored carefully on a rack?",
            answer="Fruit is stored carefully so it does not bruise and stays fresh and sweet.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rack_cfg"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_rack(R) :- rack(R).

compatible(S,R) :- setting(S), rack(R), not bad_combo(S,R).
bad_combo(barn, fish_rack).

show_valid(S,R) :- compatible(S,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RACKS:
        lines.append(asp.fact("rack", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_valid/2."))
    return sorted(set(asp.atoms(model, "show_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about a rack, a twist, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rack", choices=RACKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy", "mother", "father", "sister", "brother", "woman", "man"])
    ap.add_argument("--other")
    ap.add_argument("--other-kind", choices=["girl", "boy", "mother", "father", "sister", "brother", "woman", "man"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-kind", choices=["woman", "man", "mother", "father", "aunt", "uncle"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "rack", None):
        if (getattr(args, "setting", None), getattr(args, "rack", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)) and (getattr(args, "rack", None) is None or c[1] == getattr(args, "rack", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_key, rack_key = rng.choice(valid)
    rack_cfg = _safe_lookup(RACKS, rack_key)

    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["girl", "boy", "sister", "brother"])
    other_kind = getattr(args, "other_kind", None) or ("boy" if hero_kind in {"girl", "sister"} else "girl")
    elder_kind = getattr(args, "elder_kind", None) or rng.choice(["woman", "man", "aunt", "uncle"])
    hero = getattr(args, "hero", None) or rng.choice(["Mira", "Toma", "Lina", "Ravi", "Nina", "Pavel"])
    other = getattr(args, "other", None) or rng.choice(["Jory", "Sela", "Maren", "Kito", "Edda", "Borin"])
    elder = getattr(args, "elder", None) or rng.choice(["Grandma Wren", "Old Hobb", "Aunt Pina", "Uncle Rook"])

    return StoryParams(
        rack=rack_key,
        setting=setting_key,
        hero=hero,
        hero_kind=hero_kind,
        other=other,
        other_kind=other_kind,
        elder=elder,
        elder_kind=elder_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.rack,
        params.setting,
        params.hero,
        params.hero_kind,
        params.other,
        params.other_kind,
        params.elder,
        params.elder_kind,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show show_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, rack) combos:\n")
        for setting, rack in combos:
            print(f"  {setting:8} {rack}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for sid, rid in valid_combos():
            params = StoryParams(
                rack=rid,
                setting=sid,
                hero="Mira",
                hero_kind="girl",
                other="Jory",
                other_kind="boy",
                elder="Grandma Wren",
                elder_kind="woman",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} / {p.rack} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
