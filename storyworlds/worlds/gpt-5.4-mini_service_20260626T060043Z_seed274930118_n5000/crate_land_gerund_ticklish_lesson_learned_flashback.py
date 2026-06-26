#!/usr/bin/env python3
"""
storyworlds/worlds/crate_land_gerund_ticklish_lesson_learned_flashback.py
=========================================================================

A tiny mythic storyworld about a crate, a landing action, and a ticklish lesson.

The seed tale behind this world:
---
Long ago, on a windy hill above the sea, a young ferry-helper found a sealed crate
washed up near the shore. The helper wanted to land lightly on the stone steps, but
every time they hurried, the crate shivered and made them laugh. An older keeper
remembered a past mistake: once, they had opened a strange crate too quickly and let
a swarm of bright moths escape into the temple hall. In a flashback, the keeper
showed the helper how to land with bent knees, hold the crate steady, and listen
before acting. The helper learned that patience can be stronger than force, and the
crate was carried safely to the shrine.

This script turns that premise into a small simulated world with:
- physical meters and emotional memes
- state-driven narration
- a reasonableness gate for a single mythic lesson
- an inline ASP twin for parity checks
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crate: object | None = None
    hero: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "keeper"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "helper"}:
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
    place: str
    grounded: bool = True
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
class Cargo:
    label: str
    phrase: str
    weight: str
    region: str
    risky: str
    myth_tag: str
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
class Lesson:
    label: str
    flashback_note: str
    guidance: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
    cargo: str
    hero_name: str
    hero_type: str
    keeper_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def carry(self, cargo_id: str, carrier_id: str) -> None:
        self.entities[cargo_id].carried_by = carrier_id

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


CARGOES = {
    "crate": Cargo(
        label="crate",
        phrase="a sealed cedar crate",
        weight="heavy",
        region="arms",
        risky="jolt",
        myth_tag="crate",
    ),
    "relic_crate": Cargo(
        label="crate",
        phrase="a relic crate bound with rope",
        weight="heavy",
        region="arms",
        risky="jolt",
        myth_tag="crate",
    ),
}

LESSONS = {
    "patience": Lesson(
        label="Lesson Learned",
        flashback_note="Flashback",
        guidance="to land softly before lifting what is strange",
    ),
}

SETTINGS = {
    "shore_temple": Setting(place="the shore temple"),
    "hill_gate": Setting(place="the hill gate"),
    "harbor_steps": Setting(place="the harbor steps"),
}


def reasonableness_gate(place: str, cargo: Cargo) -> bool:
    return place in SETTINGS and cargo.label == "crate"


def active_risk(cargo: Cargo) -> bool:
    return cargo.risky == "jolt"


def safe_landing_possible(cargo: Cargo) -> bool:
    return active_risk(cargo)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for cargo_id, cargo in CARGOES.items():
            if reasonableness_gate(place, cargo) and safe_landing_possible(cargo):
                out.append((place, cargo_id))
    return out


def lesson_title() -> str:
    return "Lesson Learned"


def flashback_title() -> str:
    return "Flashback"


def _r_ticklish(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes.get("ticklish", 0) < THRESHOLD:
            continue
        sig = ("ticklish", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["laughter"] = ent.memes.get("laughter", 0) + 1
        out.append(f"{ent.id} had to laugh, for the crate's sway felt ticklish.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("care", 0) < THRESHOLD:
            continue
        sig = ("settle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] = ent.memes.get("calm", 0) + 1
        out.append(f"Their breathing grew even, and the path seemed kinder.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_ticklish, _r_settle):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def tell(setting: Setting, cargo_cfg: Cargo, hero_name: str, hero_type: str, keeper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    keeper = world.add(Entity(id="Keeper", kind="character", type=keeper_type, label="the keeper"))
    crate = world.add(Entity(
        id="Crate",
        kind="thing",
        type="crate",
        label="crate",
        phrase=cargo_cfg.phrase,
        owner=hero.id,
        caretaker=keeper.id,
    ))
    world.facts.update(hero=hero, keeper=keeper, crate=crate, cargo_cfg=cargo_cfg, setting=setting)

    world.say(
        f"At {setting.place}, {hero.id} found {cargo_cfg.phrase} waiting like a quiet omen."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wished to land softly on the stones and carry {crate.label} onward."
    )

    world.para()
    hero.meters["care"] += 1
    hero.memes["ticklish"] = hero.memes.get("ticklish", 0) + 1
    world.say(
        f"But every hurried step made the {crate.label} sway, and the feeling was strangely ticklish."
    )
    propagate(world)

    world.para()
    world.say(
        f"Then the keeper spoke of an older day, and the air itself seemed to open into a flashback."
    )
    world.say(
        f"In that remembered hour, the keeper had once lifted a strange crate too quickly, "
        f"and bright moths had spilled into the temple hall."
    )
    world.say(
        f"Now the keeper pointed to the stones and showed {hero.id} how to bend the knees, "
        f"hold the crate close, and {hero.pronoun('object')} move with care."
    )
    hero.meters["care"] += 1
    hero.memes["lesson_heard"] = 1
    keeper.memes["wisdom"] = keeper.memes.get("wisdom", 0) + 1
    propagate(world)

    world.para()
    world.say(
        f"{hero.id} listened, slowed down, and landed softly at the {setting.place}."
    )
    crate.carried_by = hero.id
    world.say(
        f"The crate stayed steady in {hero.pronoun('possessive')} arms, and the path did not shake."
    )
    world.say(
        f"So the helper learned {LESSONS['patience'].guidance}, and the {crate.label} was carried safely away."
    )

    world.facts.update(resolved=True, lesson=LESSONS["patience"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    crate = _safe_fact(world, f, "crate")
    return [
        f'Write a short myth for children about a {hero.type} who finds a {crate.label} and learns to move with care.',
        f"Tell a gentle legend where {hero.id} must land lightly because the {crate.label} feels ticklish.",
        f"Write a mythic story that includes a flashback and a lesson learned about carrying a crate safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    keeper = _safe_fact(world, f, "keeper")
    crate = _safe_fact(world, f, "crate")
    setting = _safe_fact(world, f, "setting")
    lesson = _safe_fact(world, f, "lesson")
    return [
        QAItem(
            question=f"Who found the crate at {setting.place}?",
            answer=f"{hero.id} found the crate at {setting.place} and wanted to carry it onward.",
        ),
        QAItem(
            question=f"Why did the crate seem ticklish?",
            answer=f"The crate swayed when {hero.id} hurried, so the feeling made {hero.pronoun('object')} laugh and slow down.",
        ),
        QAItem(
            question=f"What did the keeper show {hero.id} in the flashback?",
            answer=f"The keeper showed {hero.id} how to land softly, hold the crate close, and move with care.",
        ),
        QAItem(
            question=f"What lesson was learned by the end?",
            answer=f"The lesson learned was to move gently and listen before lifting what is strange.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crate?",
            answer="A crate is a strong box made for carrying or protecting things.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the story can explain a memory from the past.",
        ),
        QAItem(
            question="What does it mean to land softly?",
            answer="To land softly means to come down with care, using a gentle step or bend so you do not jolt yourself or anything you carry.",
        ),
        QAItem(
            question="What does ticklish mean?",
            answer="Ticklish means a feeling that makes someone want to laugh when something brushes or moves against them.",
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: str, cargo_id: str) -> str:
    cargo = _safe_lookup(CARGOES, cargo_id)
    return (
        f"(No story: the mythic rule only supports a crate that can be landed carefully; "
        f"{cargo.phrase} at {place} would not create a real lesson.)"
    )


ASP_RULES = r"""
valid(Place, Cargo) :- setting(Place), crate(Cargo), supports_landing(Cargo).
story_ok(Place, Cargo) :- valid(Place, Cargo).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("crate", cid))
        if cargo.risky == "jolt":
            lines.append(asp.fact("supports_landing", cid))
        lines.append(asp.fact("myth_tag", cid, cargo.myth_tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a crate, landing softly, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl", "helper"])
    ap.add_argument("--keeper-type", choices=["man", "woman", "keeper"])
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
    if getattr(args, "place", None) and getattr(args, "cargo", None):
        if (getattr(args, "place", None), getattr(args, "cargo", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "cargo", None) is None or c[1] == getattr(args, "cargo", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, cargo = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl", "helper"])
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(["keeper", "man", "woman"])
    name = getattr(args, "name", None) or rng.choice(["Ari", "Mira", "Tovin", "Lina", "Orin", "Sela"])
    return StoryParams(place=place, cargo=cargo, hero_name=name, hero_type=hero_type, keeper_type=keeper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CARGOES, params.cargo), params.hero_name, params.hero_type, params.keeper_type)
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
    StoryParams(place="shore_temple", cargo="crate", hero_name="Ari", hero_type="helper", keeper_type="keeper"),
    StoryParams(place="hill_gate", cargo="relic_crate", hero_name="Mira", hero_type="girl", keeper_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, cargo in combos:
            print(f"  {place:14} {cargo}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.cargo} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
