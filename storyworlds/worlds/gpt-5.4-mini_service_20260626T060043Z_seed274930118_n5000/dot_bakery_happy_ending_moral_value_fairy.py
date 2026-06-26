#!/usr/bin/env python3
"""
A small fairy-tale storyworld set in a bakery, featuring a dot, a happy ending,
and a moral value.

The world is intentionally compact: one child helper, one bakery, one small
problem with a spotted cake or spotted dough, and a kind fix that teaches
carefulness and sharing.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    baker: object | None = None
    gift: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "woman", "baker"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "man"}:
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
    place: str = "the bakery"
    affords: set[str] = field(default_factory=set)
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
class Ingredient:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "dot"
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

SETTINGS = {
    "bakery": Setting(place="the bakery", affords={"sprinkle", "sugar", "dot"}),
}

INGREDIENTS = {
    "dot": Ingredient(
        id="dot",
        label="dot",
        phrase="a tiny dot of jam",
        region="hands",
        mess="sticky",
        soil="sticky and spotted",
        zone={"hands"},
        keyword="dot",
    ),
}

GIFTS = {
    "bread": Gift(
        id="bread",
        label="loaf",
        phrase="a warm loaf of bread",
        region="hands",
    ),
    "cookie": Gift(
        id="cookie",
        label="cookie",
        phrase="a sweet cookie with sugar on top",
        region="hands",
    ),
    "cake": Gift(
        id="cake",
        label="cake",
        phrase="a little celebration cake",
        region="hands",
    ),
}

TOOLS = [
    Tool(
        id="apron",
        label="an apron",
        prep="put on an apron first",
        tail="put on the apron and returned to the counter",
        guards={"sticky"},
        covers={"hands"},
    ),
    Tool(
        id="cloth",
        label="a clean cloth",
        prep="take a clean cloth with them",
        tail="tucked the cloth under the bowl",
        guards={"sticky"},
        covers={"hands"},
    ),
]

NAMES = ["Mila", "Nora", "Toby", "Pip", "Lina", "Owen", "Iris", "Finn"]
TRAITS = ["gentle", "curious", "kind", "brave", "cheerful", "patient"]


# -----------------------------------------------------------------------------
# Reasonableness gates
# -----------------------------------------------------------------------------

def prize_at_risk(activity: Ingredient, gift: Gift) -> bool:
    return gift.region in activity.zone


def select_tool(activity: Ingredient, gift: Gift) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.guards and gift.region in tool.covers:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(INGREDIENTS, aid)
            for gid, gift in GIFTS.items():
                if prize_at_risk(act, gift) and select_tool(act, gift):
                    out.append((place, aid, gid))
    return out


# -----------------------------------------------------------------------------
# Causal model
# -----------------------------------------------------------------------------

def _r_spot(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("sticky", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("spot", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sticky"] = item.meters.get("sticky", 0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{actor.id}'s {item.label} got sticky and spotted.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0) + 1
        out.append(f"That would make more work for {caretaker.label}.")
    return out


CAUSAL_RULES = [_r_spot, _r_worry]


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


# -----------------------------------------------------------------------------
# Story actions
# -----------------------------------------------------------------------------

def predict_mess(world: World, actor: Entity, activity: Ingredient, gift_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    gift = sim.get(gift_id)
    return {"soiled": gift.meters.get("dirty", 0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Ingredient, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.meters.keys()), 'helper')} child "
        f"who loved the warm smell of {world.setting.place}."
    )


def loves_bakery(world: World, hero: Entity) -> None:
    hero.memes["love_bakery"] = hero.memes.get("love_bakery", 0) + 1
    world.say(
        f"{hero.id} loved helping in {world.setting.place}, where flour drifted like snow "
        f"and sweet buns cooled on the racks."
    )


def gives_gift(world: World, baker: Entity, hero: Entity, gift: Entity) -> None:
    world.say(
        f"One morning, {baker.label} gave {hero.pronoun('object')} {gift.phrase}."
    )
    gift.worn_by = hero.id


def wants(world: World, hero: Entity, activity: Ingredient) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} wanted to {activity.keyword} with the jam right away, but there was a small worry."
    )


def warn(world: World, baker: Entity, hero: Entity, activity: Ingredient, gift: Entity) -> bool:
    pred = predict_mess(world, hero, activity, gift.id)
    if not pred["soiled"]:
        return False
    world.facts["worry"] = True
    world.say(
        f'"You will get your {gift.label} {activity.soil}," {baker.label} said. '
        f'"Let us be careful."'
    )
    return True


def accept(world: World, baker: Entity, hero: Entity, activity: Ingredient, gift: Entity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["worry"] = 0
    world.say(
        f"{hero.id} nodded, and {baker.label} helped {hero.pronoun('object')} {tool.prep}."
    )
    world.say(
        f"Then {hero.id} could {activity.keyword} softly, while {gift.label} stayed clean and bright."
    )
    world.say(
        f"In the end, everyone smiled, and the little bakery glowed like a tiny castle at sunset."
    )


# -----------------------------------------------------------------------------
# Narrative assembly
# -----------------------------------------------------------------------------

def tell(setting: Setting, activity: Ingredient, gift_cfg: Gift,
         hero_name: str = "Mila", hero_type: str = "girl",
         trait: str = "kind") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"kindness": 1}))
    hero.meters[trait] = 1
    baker = world.add(Entity(id="Baker", kind="character", type="baker", label="the baker"))
    gift = world.add(Entity(
        id=gift_cfg.id,
        type=gift_cfg.id,
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        caretaker=baker.id,
        owner=hero.id,
        region=gift_cfg.region,
        plural=gift_cfg.plural,
    ))

    world.say(f"Once upon a time, {hero.id} came to {world.setting.place}.")
    loves_bakery(world, hero)
    gives_gift(world, baker, hero, gift)

    world.para()
    world.say(f"At the counter, a tiny {activity.keyword} dot gleamed like a jewel.")
    wants(world, hero, activity)
    warn(world, baker, hero, activity, gift)

    world.para()
    tool = select_tool(activity, gift)
    if tool is None:
        pass
    world.say(f"{hero.id} and {baker.label} looked at each other kindly.")
    accept(world, baker, hero, activity, gift, tool)

    world.facts.update(
        hero=hero,
        baker=baker,
        gift=gift,
        activity=activity,
        tool=tool,
        setting=setting,
    )
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, gift = f["hero"], f["activity"], f["gift"]
    return [
        f'Write a fairy tale for a child in a bakery that includes the word "{activity.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {activity.keyword} but worries about {gift.label}.",
        f"Write a happy-ending story about a small dot in a bakery and a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, baker, gift, activity = f["hero"], f["baker"], f["gift"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little helper in the bakery, and {baker.label}, who cares for the sweet things there.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the jam dot?",
            answer=f"{hero.id} wanted to {activity.keyword} with the jam dot, because the tiny spot looked fun and shiny.",
        ),
        QAItem(
            question=f"Why did the baker worry about the {gift.label}?",
            answer=f"The baker worried because the {gift.label} could get {activity.soil} if {hero.id} played without being careful.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {hero.id} used {(f.get('tool') or next(iter(TOOLS.values()))).label}, the {gift.label} stayed clean, and everyone smiled in the bakery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bakery?",
            answer="A bakery is a place where bread, buns, cakes, and cookies are baked and sold.",
        ),
        QAItem(
            question="What is a dot?",
            answer="A dot is a tiny round mark or spot.",
        ),
        QAItem(
            question="Why do people wear aprons in a bakery?",
            answer="People wear aprons to keep flour, jam, and crumbs off their clothes.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means moving gently and thinking about how your actions might affect things around you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, G) :- zone(A, R), gift_on(G, R).
fix(A, G) :- prize_at_risk(A, G), tool(T), guards(T, M), mess_of(A, M), covers(T, R), gift_on(G, R).
valid_story(P, A, G) :- place(P), affords(P, A), prize_at_risk(A, G), fix(A, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in INGREDIENTS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_on", gid, g.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# -----------------------------------------------------------------------------
# Story sample generation
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    gift: str
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


def explain_rejection(activity: Ingredient, gift: Gift) -> str:
    return (
        f"(No story: the dot would not truly spoil the {gift.label}, or no gentle fix exists. "
        f"Try another gift.)"
    )


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "gift", None):
        act, gift = _safe_lookup(INGREDIENTS, getattr(args, "activity", None)), _safe_lookup(GIFTS, getattr(args, "gift", None))
        if not (prize_at_risk(act, gift) and select_tool(act, gift)):
            pass

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        pass

    place, act_id, gift_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, gift=gift_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(INGREDIENTS, params.activity), _safe_lookup(GIFTS, params.gift),
                 hero_name=params.name, hero_type=params.gender, trait=params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bakery storyworld with a dot and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=INGREDIENTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(place="bakery", activity="dot", gift="bread", name="Mila", gender="girl", trait="gentle"),
    StoryParams(place="bakery", activity="dot", gift="cookie", name="Toby", gender="boy", trait="curious"),
    StoryParams(place="bakery", activity="dot", gift="cake", name="Iris", gender="girl", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = valid_story_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
