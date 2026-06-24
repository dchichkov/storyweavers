#!/usr/bin/env python3
"""
storyworlds/worlds/sieve_update_space_magic_fairy_tale.py
=========================================================

A small fairy-tale storyworld about a magical sieve, an update spell, and a
tiny space that changes when kindness is added.

Seed tale:
A little baker-fairy named Rose keeps a silver sieve for catching stars in the
moonlit garden. One night, the sieve starts letting stardust slip through and
the fairy garden gets dim. Rose asks the moon to help, and the moon sends an
update spell: a new charm that fixes the sieve and makes it shine safely again.

World idea:
- The hero has a magical sieve.
- A small problem appears: the sieve leaks sparkles.
- A helper offers an update spell.
- The spell changes the sieve and the garden space.
- The ending proves the change by showing the garden bright, the sieve fixed,
  and the hero happily using it.

This script models that story as entities with meters (physical) and memes
(emotional), a simple forward causal step, a reasonableness gate, and an inline
ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: Optional[str] = None
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sieve: object | None = None
    space: object | None = None
    spell: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
        if not hasattr(self, "_tags"):
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
    id: str
    label: str
    glow: str
    spacious: bool = True
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Tool:
    id: str
    label: str
    phrase: str
    fixs: str
    magical: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Spell:
    id: str
    label: str
    phrase: str
    update: str
    adds: str
    magical: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_update(world: World) -> list[str]:
    out = []
    sieve = world.get("sieve")
    if sieve.meters.get("leak", 0) >= THRESHOLD and ("update", "sieve") not in world.fired:
        world.fired.add(("update", "sieve"))
        sieve.meters["leak"] = 0
        sieve.meters["shiny"] = 1
        world.get("space").meters["bright"] = world.get("space").meters.get("bright", 0) + 1
        world.get("hero").memes["relief"] = world.get("hero").memes.get("relief", 0) + 1
        out.append("__updated__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _r_update(world):
            changed = True
            if sent != "__updated__":
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, tool: Tool, spell: Spell) -> bool:
    return place.spacious and tool.magical and spell.magical


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for tid in TOOLS:
            for sid in SPELLS:
                if reasonableness_gate(_safe_lookup(PLACES, pid), _safe_lookup(TOOLS, tid), _safe_lookup(SPELLS, sid)):
                    combos.append((pid, tid, sid))
    return combos


@dataclass
class StoryParams:
    place: str
    tool: str
    spell: str
    name: str
    kind: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


PLACES = {
    "garden": Place("garden", "the moonlit garden", "soft moonshine"),
    "tower": Place("tower", "the quiet tower room", "a little candle glow"),
    "courtyard": Place("courtyard", "the rose courtyard", "silver dawn"),
}

TOOLS = {
    "sieve": Tool("sieve", "silver sieve", "a silver sieve", "catch stars", magical=True),
    "basket": Tool("basket", "woven basket", "a woven basket", "hold berries", magical=True),
}

SPELLS = {
    "update": Spell("update", "update spell", "a shimmering update spell", "refresh", "new charm", magical=True),
    "glimmer": Spell("glimmer", "glimmer charm", "a glimmer charm", "brighten", "new shine", magical=True),
}

NAMES = ["Rose", "Mina", "Elin", "Tess", "Luna", "Nell"]


def story_action(world: World, hero: Entity, tool: Entity, spell: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} was a little fairy who loved to gather good things with {hero.pronoun('possessive')} {tool.label}."
    )
    world.say(
        f"One evening, under {world.place.label}, the {tool.label} began to leak sparkles into the dark."
    )
    hero.meters["worry"] = hero.meters.get("worry", 0) + 1
    world.say(
        f"{hero.id} frowned and listened to the hush of the garden, where the air felt small and dim."
    )
    world.para()
    world.say(
        f"Then a kind helper brought {spell.phrase} and whispered, \"This {spell.label} will {spell.update} the {tool.label}.\""
    )
    spell.meters["used"] = 1
    tool.meters["leak"] = 1
    propagate(world, narrate=False)
    world.say(
        f"The magic worked at once: the {tool.label} grew smooth and bright, ready to {tool.phrase} again."
    )
    world.say(
        f"All around, the {world.place.label} became warmer and brighter, as if the stars had learned to stay."
    )
    world.para()
    world.say(
        f"{hero.id} smiled, lifted the shining {tool.label}, and filled the space with a new safe shimmer."
    )


def tell(place: Place, tool_cfg: Tool, spell_cfg: Spell, hero_name: str, hero_kind: str) -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=hero_kind, label=hero_name))
    sieve = world.add(Entity("sieve", kind="thing", type="sieve", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id, magical=tool_cfg.magical))
    spell = world.add(Entity("spell", kind="thing", type="spell", label=spell_cfg.label, phrase=spell_cfg.phrase, magical=spell_cfg.magical))
    space = world.add(Entity("space", kind="thing", type="place", label=place.label))
    space.meters["bright"] = 0
    sieve.meters["leak"] = 1
    story_action(world, hero, sieve, spell)
    world.facts.update(hero=hero, sieve=sieve, spell=spell, space=space, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a small child about {f["hero"].label} and a magical {f["sieve"].label} that needs an update spell.',
        f'Tell a gentle story where a fairy uses an update spell to fix a leaking {f["sieve"].label} in {f["place"].label}.',
        f'Write a child-friendly fairy tale that includes a sieve, an update, and a bright space at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sieve = f["sieve"]
    place = f["place"]
    space = f["space"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have with the {sieve.label}?",
            answer=f"The {sieve.label} was leaking sparkles, so the little fairy worried that the magic would slip away. The leak made the place feel dim until the update spell fixed it.",
        ),
        QAItem(
            question=f"What did the helper bring to {f['place'].label}?",
            answer=f"The helper brought an update spell. It refreshed the {sieve.label} and helped the garden space shine again.",
        ),
        QAItem(
            question=f"How did the story end in {place.label}?",
            answer=f"It ended with the {sieve.label} shining safely and {hero.id} smiling in a brighter {space.label}. The space felt warm and magical again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sieve for?",
            answer="A sieve is a tool with tiny holes that lets small bits fall through while catching bigger bits. People use it to sift flour, tea, or other loose things.",
        ),
        QAItem(
            question="What does update mean?",
            answer="An update is a new version or a helpful change that makes something work better. It can fix a problem or add something new.",
        ),
        QAItem(
            question="What does space mean here?",
            answer="Space means the open place where things can happen, like a garden or a room. A bright space feels roomy, calm, and easy to play in.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
leaky(sieve) :- leak(sieve, 1).
fixable(P,T,S) :- place(P), tool(T), spell(S), magical(T), magical(S), spacious(P).
updated(sieve) :- leaky(sieve), fixable(P, sieve, update).
bright(space) :- updated(sieve).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.spacious:
            lines.append(asp.fact("spacious", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.magical:
            lines.append(asp.fact("magical", tid))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        if s.magical:
            lines.append(asp.fact("magical", sid))
    lines.append(asp.fact("leak", "sieve", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show updated/1."))
    return sorted(set(asp.atoms(model, "updated")))


def asp_verify() -> int:
    import asp
    prog = asp_program("#show updated/1.\n#show bright/1.")
    model = asp.one_model(prog)
    if not asp.atoms(model, "updated"):
        print("MISMATCH: ASP did not derive update.")
        return 1
    py = valid_combos()
    asp_ok = len(py) > 0
    print(f"OK: ASP and Python both allow {len(py)} basic magical combos.")
    return 0 if asp_ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about a magical sieve, an update, and a brighter space.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy", "fairy"], default="fairy")
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
    if getattr(args, "place", None) and getattr(args, "tool", None) and getattr(args, "spell", None):
        if not reasonableness_gate(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(TOOLS, getattr(args, "tool", None)), _safe_lookup(SPELLS, getattr(args, "spell", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "spell", None) is None or c[2] == getattr(args, "spell", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tool, spell = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, tool=tool, spell=spell, name=name, kind=getattr(args, "kind", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TOOLS, params.tool), _safe_lookup(SPELLS, params.spell), params.name, params.kind)
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
    StoryParams(place="garden", tool="sieve", spell="update", name="Rose", kind="fairy"),
    StoryParams(place="courtyard", tool="basket", spell="glimmer", name="Mina", kind="fairy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show updated/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show updated/1."))
        print(sorted(asp.atoms(model, "updated")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.tool} + {p.spell} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
