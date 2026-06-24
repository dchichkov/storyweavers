#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/girl_heart_lmnop_bravery_sharing_quest_slice.py
========================================================================================================

A small slice-of-life storyworld about a girl, a heart, and lmnop:
a child wants to go on a tiny quest, finds a little bravery, and learns
that sharing makes an ordinary day feel special.

Seed impression used to build the world:
---
A girl notices a heart-shaped charm with the letters lmnop on it.
She feels shy about asking to join a small quest with her friend.
The quest is simple: carry a note, share a snack, and help set up a table.
By being brave enough to ask, she gets to share the task and the fun.

World model:
---
- girl: a child with two numeric dimensions: meters and memes
- heart: a physical keepsake that can be held, worn, or shared
- lmnop: a small letter card, tag, or charm connected to the keepsake
- bravery: a meme that rises when the child speaks up despite shyness
- sharing: a meme that rises when the child offers, divides, or lends
- quest: a small errand or helpful mission in an ordinary place

Story shape:
---
1) Setup: the girl notices the heart/lmnop object and the day she wants.
2) Tension: she is shy about joining the quest or asking to share.
3) Turn: a gentle prompt gives her bravery, and she offers to help.
4) Resolution: the quest finishes, and the final image shows what changed.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    girl: object | None = None
    heart: object | None = None
    lmnop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
        return None


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    takes: set[str] = field(default_factory=set)
    shares_well: bool = True
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
class QuestCfg:
    id: str
    action: str
    gerund: str
    goal: str
    requires: set[str]
    outcome: str
    place_tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    quest: str
    object: str
    name: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _brave(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes.get("bravery", 0.0) >= THRESHOLD:
            sig = ("brave", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["shy"] = max(0.0, ent.memes.get("shy", 0.0) - 1)
            out.append(f"{ent.id} took a steady breath and felt braver.")
    return out


def _share(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        sig = ("share", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} offered to share the task.")
    return out


def _quest(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.meters.get("quest_step", 0.0) < THRESHOLD:
            continue
        sig = ("quest", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} finished the little quest.")
    return out


CAUSAL_RULES = [
    _brave,
    _share,
    _quest,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"share_snack", "find_card", "prepare_table"}),
    "classroom": Setting(place="the classroom", indoors=True, affords={"share_snack", "find_card", "prepare_table"}),
    "library": Setting(place="the library corner", indoors=True, affords={"find_card", "prepare_table"}),
    "porch": Setting(place="the porch", indoors=False, affords={"share_snack", "find_card"}),
}

OBJECTS = {
    "heart_card": ObjectCfg(
        id="heart_card",
        label="heart card",
        phrase="a little heart card with the letters lmnop on it",
        type="card",
        takes={"hold", "share"},
        shares_well=True,
    ),
    "heart_charm": ObjectCfg(
        id="heart_charm",
        label="heart charm",
        phrase="a small heart charm stamped with lmnop",
        type="charm",
        takes={"wear", "hold"},
        shares_well=True,
    ),
    "note": ObjectCfg(
        id="note",
        label="note",
        phrase="a folded note for a friend",
        type="note",
        takes={"hold", "pass"},
        shares_well=True,
    ),
}

QUESTS = {
    "share_snack": QuestCfg(
        id="share_snack",
        action="share a snack",
        gerund="sharing a snack",
        goal="make room for everyone",
        requires={"sharing"},
        outcome="the snack was split neatly into two friendly halves",
        place_tags={"kitchen", "classroom", "porch"},
    ),
    "find_card": QuestCfg(
        id="find_card",
        action="look for the lmnop card",
        gerund="looking for the lmnop card",
        goal="bring back the heart card",
        requires={"bravery"},
        outcome="the heart card was found under a book and set safely on the table",
        place_tags={"kitchen", "classroom", "library", "porch"},
    ),
    "prepare_table": QuestCfg(
        id="prepare_table",
        action="set up the table",
        gerund="setting up the table",
        goal="make a tidy place for the quest",
        requires={"sharing", "bravery"},
        outcome="the table ended up tidy, with space for every little thing",
        place_tags={"kitchen", "classroom", "library"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ada", "Maya", "Ivy", "Sofia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id, q in QUESTS.items():
            if place not in q.place_tags:
                continue
            for obj_id in OBJECTS:
                combos.append((place, quest_id, obj_id))
    return combos


def explain_rejection(place: str, quest: QuestCfg, obj: ObjectCfg) -> str:
    return (
        f"(No story: {quest.action} doesn't fit naturally at {place}, or the {obj.label} "
        f"doesn't make a clear little slice-of-life quest there.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.shares_well:
            lines.append(asp.fact("shares_well", oid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for p in sorted(q.place_tags):
            lines.append(asp.fact("quest_place", qid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Quest, Obj) :- affords(Place, _), quest_place(Quest, Place), object(Obj).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: girl, heart, lmnop, bravery, sharing, quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
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
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None)
              and getattr(args, "object", None) is None or c[2] == getattr(args, "object", None)]
    if getattr(args, "place", None) and getattr(args, "quest", None) and getattr(args, "object", None):
        if (getattr(args, "place", None), getattr(args, "quest", None), getattr(args, "object", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, obj = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    return StoryParams(place=place, quest=quest, object=obj, name=name)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    girl = world.add(Entity(id=params.name, kind="character", type="girl", meters={}, memes={"shy": 1.0}))
    heart = world.add(Entity(id="heart", type="heart", label="heart", phrase=_safe_lookup(OBJECTS, params.object).phrase, owner=girl.id))
    lmnop = world.add(Entity(id="lmnop", type="letters", label="lmnop", phrase="the letters lmnop", owner=girl.id))
    quest = _safe_lookup(QUESTS, params.quest)

    world.say(f"{girl.id} was a little girl who liked quiet mornings and tidy little plans.")
    world.say(f"She kept {heart.phrase} near her, and the heart always reminded her of lmnop.")

    world.para()
    world.say(f"That day, {girl.id} wanted to {quest.action} at {world.setting.place}.")
    if params.object == "heart_card":
        world.say(f"The {heart.label} felt important, because it held the bright letters lmnop.")
    else:
        world.say(f"The {heart.label} was small enough to fit in her palm, and lmnop shone on it like a tiny sign.")

    world.para()
    girl.memes["shy"] += 1
    world.say(f"At first, she felt shy about asking to join the quest.")
    if quest.id == "share_snack":
        world.say(f"She had a snack, but she did not want to keep it all to herself.")
    elif quest.id == "find_card":
        world.say(f"She knew the heart card was missing, and she worried someone might need a brave helper.")
    else:
        world.say(f"The table needed hands, and she wondered if she could help without making a fuss.")

    world.para()
    girl.memes["bravery"] += 1
    girl.memes["sharing"] += 1
    girl.meters["quest_step"] = 1
    propagate(world)
    world.say(f"Then {girl.id} took a breath and asked kindly if she could help.")
    world.say(f"She offered to share the work, which made the room feel warmer right away.")

    world.para()
    world.say(quest.outcome + ".")
    world.say(f"In the end, {girl.id} felt proud of being brave enough to speak up and kind enough to share.")
    world.say(f"The little heart with lmnop stayed close by, and the whole day felt simple and sweet.")

    world.facts.update(girl=girl, heart=heart, lmnop=lmnop, quest=quest, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    girl = f["girl"]
    quest = f["quest"]
    return [
        f'Write a gentle slice-of-life story about a girl named {girl.id} who notices a heart with lmnop and learns bravery while doing a small quest.',
        f"Tell a short story where {girl.id} wants to {quest.action}, feels shy, and then learns to share and help.",
        f'Write a child-friendly story using the words "girl", "heart", and "lmnop" that ends with a calm, happy quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    girl = f["girl"]
    quest = f["quest"]
    heart = f["heart"]
    return [
        QAItem(
            question=f"What did {girl.id} want to do in the story?",
            answer=f"{girl.id} wanted to {quest.action} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {girl.id} feel shy at first?",
            answer=f"She felt shy because she wanted to ask for help and join the quest, but she was not sure at first.",
        ),
        QAItem(
            question=f"What special thing did the heart have on it?",
            answer=f"The heart had the letters lmnop on it, which made it feel like a tiny special keepsake.",
        ),
        QAItem(
            question=f"How did {girl.id} change by the end?",
            answer=f"She became more brave, shared the work, and felt proud after helping finish the quest.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps you do something kind or hard even when you feel shy or worried.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing is when you let someone else use, have, or help with something too.",
        ),
        QAItem(
            question="What is a quest in an everyday story?",
            answer="A quest can be a small helpful job, like finding something, setting a table, or carrying a note.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", quest="share_snack", object="heart_card", name="Mina"),
    StoryParams(place="classroom", quest="prepare_table", object="heart_card", name="Lila"),
    StoryParams(place="library", quest="find_card", object="heart_charm", name="Nora"),
    StoryParams(place="porch", quest="share_snack", object="note", name="Maya"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, object) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
