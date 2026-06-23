#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/pesto_clatter_sharing_repetition_rhyming_story.py
===============================================================================================================

A tiny standalone story world about sharing pesto, a little clatter, and a
rhyming repetition that turns a messy moment into a kind ending.

This world keeps one small premise:
- a child has pesto to share,
- there is a clatter if a bowl is bumped,
- a helper can make sharing fair,
- the ending proves the sharing worked.

The prose is generated from simulated state, not from a fixed paragraph shell.
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
    owner: str = ""
    helper_for: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, object] = field(default_factory=dict)

    bowl: object | None = None
    child: object | None = None
    food: object | None = None
    friend: object | None = None
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
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    surfaces: set[str] = field(default_factory=set)
    crowd_size: int = 2
    has_table: bool = True
    has_cloth: bool = False
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
class Food:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    sticky: bool = True
    smells_good: bool = True
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
class Helper:
    id: str
    label: str
    action: str
    rhyme: str
    can_scoop: bool = True
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_clatter(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    if not bowl or bowl.meters["bumped"] < THRESHOLD:
        return out
    if ("clatter",) in world.fired:
        return out
    world.fired.add(("clatter",))
    bowl.meters["clatter"] += 1
    world.get("child").memes["surprise"] += 1
    out.append("The bowl went clatter-clatter on the table.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    food = world.entities.get("pesto")
    if not bowl or not food:
        return out
    if bowl.meters["clatter"] < THRESHOLD or food.meters["served"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    food.meters["spill"] += 1
    world.get("child").memes["oops"] += 1
    out.append("A little pesto fleck hopped out, so the child wiped it with care.")
    return out


CAUSAL_RULES = [
    _r_clatter,
    _r_spill,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str = "kitchen"
    helper: str = "spoon"
    child_name: str = "Mila"
    child_type: str = "girl"
    helper_name: str = "Pia"
    helper_type: str = "girl"
    seed: Optional[int] = None
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


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", {"table", "stove"}, 3, True, True),
    "picnic": Place("picnic", "the sunny picnic blanket", {"blanket", "basket"}, 2, False, False),
    "garden": Place("garden", "the garden table", {"table", "bench"}, 3, True, False),
}

HELPERS = {
    "spoon": Helper("spoon", "a big spoon", "stirred and shared", "spoon, spoon, swoop and tune", True),
    "ladle": Helper("ladle", "a little ladle", "lifted and split", "ladle, ladle, make it fair", True),
    "plate": Helper("plate", "a round plate", "held and passed", "plate, plate, share with grace", False),
}

NAMES_GIRL = ["Mila", "Lina", "Tia", "Nora", "Rae", "Pia"]
NAMES_BOY = ["Oli", "Finn", "Noah", "Eli", "Kai", "Leo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for helper in HELPERS:
            if place == "picnic" and helper == "plate":
                continue
            combos.append((place, helper))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny rhyming story world about pesto, clatter, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos() if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "helper", None) is None or c[1] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, helper = rng.choice(list(combos))
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(["girl", "boy"])
    friend = getattr(args, "friend", None) or rng.choice([n for n in (NAMES_GIRL if friend_gender == "girl" else NAMES_BOY) if n != child_name])
    return StoryParams(place=place, helper=helper, child_name=child_name, child_type=child_gender, helper_name=friend, helper_type=friend_gender)


def introduce(world: World, child: Entity, friend: Entity, food: Entity, helper: Helper) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    food.meters["ready"] += 1
    world.say(
        f"{child.id} and {friend.id} sat by {world.place.label}, and the green pesto gleamed in the sun."
        f" {child.id} said, \"We share, we share, we share today,\" and {friend.id} said, "
        f"\"We share, we share, we share today.\""
    )
    world.say(
        f"They had {food.phrase}, and {helper.label} ready to make it fair."
    )


def bump(world: World, child: Entity, helper: Helper) -> None:
    child.meters["bump"] += 1
    world.get("bowl").meters["bumped"] += 1
    world.say(
        f"{child.id} gave the bowl a bump-bump-bump, and {helper.label} made a little clatter."
    )
    propagate(world, narrate=True)


def share(world: World, child: Entity, friend: Entity, food: Entity, helper: Helper) -> None:
    food.meters["served"] += 1
    child.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    world.say(
        f"Then {child.id} and {friend.id} shared the pesto, spoon by spoon, with a sing-song tune."
    )
    if helper.id == "plate":
        world.say(f"On the plate, the pesto stayed neat; neat and sweet, neat and sweet.")
    else:
        world.say(f"With {helper.label}, the pesto slid smoothly, and each child got a little spoonful too.")


def end(world: World, child: Entity, friend: Entity, food: Entity, helper: Helper) -> None:
    world.say(
        f"In the end, the bowl sat still-still-still, and the pesto was shared with happy smiles."
    )
    world.say(
        f"{child.id} and {friend.id} licked their lips and laughed, 'More tomorrow, more tomorrow, after a while!'"
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    helper = _safe_lookup(HELPERS, params.helper)
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    friend = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    food = world.add(Entity(id="pesto", kind="thing", type="food", label="pesto", phrase="a bowl of pesto"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label="bowl"))
    world.facts.update(child=child, friend=friend, food=food, bowl=bowl, helper=helper, place=place)
    introduce(world, child, friend, food, helper)
    world.para()
    bump(world, child, helper)
    world.para()
    share(world, child, friend, food, helper)
    end(world, child, friend, food, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    helper: Helper = f["helper"]
    place: Place = f["place"]
    return [
        f'Write a short rhyming story about {child.id} and {friend.id} sharing pesto at {place.label}, with a clatter and a happy ending.',
        f"Tell a gentle story where a bowl makes clatter-clatter, but {child.id} and {friend.id} keep sharing the pesto together.",
        f'Write a simple rhyme that repeats "we share" and ends with pesto being passed kindly from one child to another.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    helper: Helper = f["helper"]
    place: Place = f["place"]
    food: Entity = f["food"]
    qa = [
        QAItem(
            f"Who shared the pesto at {place.label}?",
            f"{child.id} and {friend.id} shared it together. They kept passing the pesto so both could taste it.",
        ),
        QAItem(
            f"What made the little clatter in the story?",
            f"The bowl made the clatter when it got bumped. That clatter showed the sharing scene had a small bouncy mishap.",
        ),
        QAItem(
            f"How did the children keep the pesto fair?",
            f"They used {helper.label} and took turns. The shared spooning made sure each child got a taste.",
        ),
    ]
    if world.get("bowl").meters["clatter"] >= THRESHOLD:
        qa.append(QAItem(
            f"What happened after the bowl went clatter-clatter?",
            f"The children did not stop. They wiped the tiny mess, then kept sharing the pesto with care.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is pesto?",
            "Pesto is a green sauce made by grinding herbs, nuts, oil, and cheese together. People often spread it or stir it into food.",
        ),
        QAItem(
            "What does clatter mean?",
            "Clatter is a loud, bouncy sound made when hard things knock together. A bowl or spoon can clatter on a table.",
        ),
        QAItem(
            "Why do people share food?",
            "People share food so everyone can have some and enjoy it together. Sharing can feel kind and cheerful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H) :- place(P), helper(H), not bad(P,H).
bad(picnic,plate).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH between clingo and valid_combos():")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, helper=None, name=None, gender=None, friend=None, friend_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        ok = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return ok


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="kitchen", helper="spoon", child_name="Mila", child_type="girl", helper_name="Oli", helper_type="boy"),
    StoryParams(place="garden", helper="ladle", child_name="Leo", child_type="boy", helper_name="Pia", helper_type="girl"),
    StoryParams(place="picnic", helper="spoon", child_name="Nora", child_type="girl", helper_name="Kai", helper_type="boy"),
    StoryParams(place="kitchen", helper="plate", child_name="Finn", child_type="boy", helper_name="Rae", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} valid combos:")
        for p, h in asp_valid_combos():
            print(f"  {p:8} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
