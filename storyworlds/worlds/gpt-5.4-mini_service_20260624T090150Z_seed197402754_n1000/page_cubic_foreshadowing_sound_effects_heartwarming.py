#!/usr/bin/env python3
"""
A small storyworld about a child, a page, and a cubic little plan.

Seed tale inspiration:
A child wants to make something lovely on a fresh page, but the page is
fragile and the cubic pieces might press too hard. A caring parent notices the
risk, offers a gentler way, and the child ends up with a happy, finished page.

This world supports:
- a foreshadowing-aware safety check
- sound effects in the narration
- a warm, heartwarming resolution
- inline ASP rules mirroring the Python reasonableness gate
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
# Core model
# ---------------------------------------------------------------------------

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
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    protective: bool = False
    protects: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"press": 0.0, "mess": 0.0, "damage": 0.0, "care": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    press_kind: str
    damage: str
    target_zone: set[str]
    sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone

    def items(self) -> list[Entity]:
        return list(self.entities.values())

    def protective_items(self, owner: Entity) -> list[Entity]:
        return [e for e in self.items() if e.owner == owner.id and e.protective]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "craft_table": Setting(place="the craft table", affords={"stack_cubes", "stamp_page", "press_shapes"}),
    "sunny_window": Setting(place="the sunny window seat", affords={"stack_cubes", "stamp_page"}),
    "living_room_floor": Setting(place="the living room floor", affords={"stack_cubes", "press_shapes"}),
}

ACTIVITIES = {
    "stack_cubes": Activity(
        id="stack_cubes",
        verb="stack the cubic blocks",
        gerund="stacking the cubic blocks",
        rush="rush to stack the blocks higher",
        press_kind="heavy",
        damage="creased",
        target_zone={"page"},
        sound="clack-clack",
        keyword="cubic",
        tags={"cubic", "blocks"},
    ),
    "stamp_page": Activity(
        id="stamp_page",
        verb="stamp the page",
        gerund="stamping the page",
        rush="reach for the stamp pad",
        press_kind="ink",
        damage="smudged",
        target_zone={"page"},
        sound="tap-tap",
        keyword="page",
        tags={"page", "ink"},
    ),
    "press_shapes": Activity(
        id="press_shapes",
        verb="press the shapes onto the page",
        gerund="pressing shapes onto the page",
        rush="lean down to press harder",
        press_kind="pressure",
        damage="wavy",
        target_zone={"page"},
        sound="thump-thump",
        keyword="page",
        tags={"page", "shapes"},
    ),
}

PRIZES = {
    "page": Prize(
        id="page",
        label="page",
        phrase="a fresh white page",
        region="page",
    ),
}

GEAR = [
    Gear(
        id="clipboard",
        label="a clipboard",
        covers={"page"},
        guards={"heavy", "pressure"},
        prep="put the page on a clipboard first",
        tail="moved the page to the clipboard and worked more gently",
    ),
    Gear(
        id="wax_paper",
        label="wax paper",
        covers={"page"},
        guards={"ink"},
        prep="place wax paper over the page first",
        tail="slipped the wax paper on top and stamped carefully",
    ),
    Gear(
        id="soft_mat",
        label="a soft mat",
        covers={"page"},
        guards={"heavy", "pressure", "ink"},
        prep="set the page on a soft mat first",
        tail="laid the page on the soft mat and kept the tools light",
    ),
]

CHILD_NAMES = ["Mia", "Noah", "Lily", "Ben", "Ava", "Leo", "Nora", "Finn"]
TRAITS = ["gentle", "curious", "careful", "cheerful", "patient", "spirited"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
target_at_risk(A, P) :- target(A, T), pages(P), zone_of(P, T).
compatible(G, A, P) :- gear(G), target_at_risk(A, P),
                      press_kind(A, K), guards(G, K),
                      covers(G, T), zone_of(P, T).
valid(Place, A, P) :- affords(Place, A), target_at_risk(A, P), compatible(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("target", aid, "page"))
        lines.append(asp.fact("press_kind", aid, a.press_kind))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("pages", pid))
        lines.append(asp.fact("zone_of", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.target_zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.press_kind in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not really put the {prize.label} at risk.)"
    return f"(No story: no gear in this world can safely protect the {prize.label} from that plan.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "damaged": prize.meters["damage"] >= THRESHOLD,
        "care": sum(e.meters["care"] for e in sim.entities.values()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    prize = world.get("page")
    if activity.id not in world.setting.affords:
        return
    actor.meters["press"] += 1
    actor.memes["joy"] += 1
    prize.meters["press"] += 1
    if narrate:
        world.say(f"{activity.sound}! {actor.noun()} started {activity.gerund}.")
    if prize.location == "unprotected":
        prize.meters["damage"] += 1


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a {child.type} who loved quiet afternoons at {world.setting.place} "
        f"and liked making small things feel special."
    )


def foreshadow(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} looked at the {prize.label} and smiled, but {parent.noun()} noticed "
        f"how the little {activity.keyword} pieces made a soft stack beside the paper."
    )
    world.say(
        f'"Careful," {parent.pronoun("subject")} said with a warm smile. '
        f'"Those cubic blocks can press harder than they sound."'
    )


def desire(world: World, child: Entity, activity: Activity) -> None:
    world.say(
        f"{child.id} wanted to {activity.verb}, because the idea in {child.pronoun("possessive")} "
        f"head felt bright and tidy, almost like a tiny picture waiting to happen."
    )


def worry(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_damage(world, child, activity, prize.id)
    if pred["damaged"]:
        child.memes["worry"] += 1
        world.facts["predicted_damage"] = activity.damage
        world.say(
            f'"If we do that, the {prize.label} could get {activity.damage}," '
            f'{parent.noun()} said softly. "Let us keep the nice page safe."'
        )


def offer_fix(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    item = world.add(Entity(
        id=gear.id,
        label=gear.label,
        type="tool",
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        protects=set(gear.covers),
    ))
    if predict_damage(world, child, activity, prize.id)["damaged"]:
        del world.entities[item.id]
        return None
    world.say(
        f"{parent.noun().capitalize()} pointed to {gear.label} and said, "
        f'"How about we {gear.prep}?"'
    )
    return item


def accept_fix(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    prize.meters["damage"] = 0.0
    world.say(
        f'{child.id} grinned and said, "Yes, please!"'
    )
    world.say(
        f"They {gear.tail}, and soon {child.id} was {activity.gerund} again. "
        f'The {prize.label} stayed smooth, and the room felt cozy and kind.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, child_name: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in {"Mia", "Lily", "Ava", "Nora"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type="page",
        label=prize_cfg.label,
        owner=child.id,
        caretaker=parent.id,
        location="unprotected",
    ))

    introduce(world, child)
    desire(world, child, activity)
    foreshadow(world, child, parent, activity, prize)

    world.para()
    worry(world, parent, child, activity, prize)
    gear_item = offer_fix(world, parent, child, activity, prize)

    world.para()
    if gear_item is not None:
        accept_fix(world, child, parent, activity, prize, GEAR[[g.id for g in GEAR].index(gear_item.id)])

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_item,
        resolved=gear_item is not None,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, activity, prize = f["child"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about a child named {child.id} who wants to {activity.verb} but must keep a {prize.label} safe.',
        f"Tell a gentle story with a little foreshadowing and sound effects where {child.id} and {parent.noun()} solve a problem at {world.setting.place}.",
        f'Write a short story that includes the words "{activity.keyword}" and "{prize.label}" and ends with a cozy happy choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, activity = f["child"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do with the {prize.label}?",
            answer=f"{child.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.noun()} worry about the {prize.label}?",
            answer=f"{parent.noun().capitalize()} worried because the {prize.label} could get {activity.damage} if the {activity.keyword} plan pressed too hard.",
        ),
    ]
    if gear is not None:
        qa.append(QAItem(
            question=f"What helped {child.id} keep the {prize.label} safe?",
            answer=f"{gear.label} helped because it kept the pressure away from the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'cubic' mean?",
            answer="Cubic means shaped like a cube, with flat sides and corners.",
        ),
        QAItem(
            question="What is a page?",
            answer="A page is one sheet in a book, notebook, or pad where you can write or draw.",
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    child_name: str
    parent_type: str = "mother"
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


CURATED = [
    StoryParams(place="craft_table", activity="stack_cubes", child_name="Mia", parent_type="mother"),
    StoryParams(place="sunny_window", activity="stamp_page", child_name="Noah", parent_type="father"),
    StoryParams(place="living_room_floor", activity="press_shapes", child_name="Lily", parent_type="mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    if activity not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "prize", None) and not prize_at_risk(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent_type = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, child_name=child_name, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), PRIZES["page"], params.child_name, params.parent_type)
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
        if e.protective:
            bits.append(f"protects={sorted(e.protects)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld: a child, a page, and a cubic plan.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def asp_program_text() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text() + "#show valid/3.\n")
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program_text() + "#show valid/3.\n")
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.child_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
