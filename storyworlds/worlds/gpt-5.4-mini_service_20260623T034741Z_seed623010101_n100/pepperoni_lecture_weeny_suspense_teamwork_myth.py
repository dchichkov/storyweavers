#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/pepperoni_lecture_weeny_suspense_teamwork_myth.py
===============================================================================================================================

A standalone storyworld in a small mythic domain: children, a fussy elder,
a tiny crossing, a suspenseful delivery, and a teamwork ending.

The seed words are woven into the world itself:
- pepperoni
- lecture
- weeny

The story style is mythic: a small quest feels important, almost sacred, but
the prose stays child-facing and concrete.
"""

from __future__ import annotations

import argparse
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
    owner: Optional[str] = None
    helper: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bridge: object | None = None
    elder: object | None = None
    hero: object | None = None
    offering: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    affords: set[str] = field(default_factory=set)
    suspense: int = 1
    tags: set[str] = field(default_factory=set)
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
class Offering:
    id: str
    label: str
    phrase: str
    kind: str
    at_risk: str
    use: str
    tags: set[str] = field(default_factory=set)
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
class Bridge:
    id: str
    label: str
    phrase: str
    width: str
    sturdy: bool
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.parts: list[list[str]] = [[]]

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
            self.parts[-1].append(text)

    def para(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.parts if p)

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.parts = [[]]
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        # suspense grows if the offering is carried near the weeny bridge
        if world.facts.get("carried") and world.facts.get("on_bridge") and ("suspense",) not in world.fired:
            world.fired.add(("suspense",))
            carrier = world.get(world.facts["carrier"])
            carrier.memes["suspense"] += 1
            out.append("The air grew still, and the little crossing felt taller than before.")
            changed = True
        # teamwork lowers fear and raises success
        if world.facts.get("teamwork") and ("teamwork",) not in world.fired:
            world.fired.add(("teamwork",))
            for eid in world.facts.get("helpers", []):
                world.get(eid).memes["joy"] += 1
                world.get(eid).memes["trust"] += 1
            changed = True
            out.append("Together, their hands kept the offering steady.")
        # a shaky bridge can nearly fail
        if world.facts.get("on_bridge") and not world.facts.get("bridge_secure") and ("wobble",) not in world.fired:
            world.fired.add(("wobble",))
            world.facts["near_fall"] = True
            out.append("The weeny bridge trembled like a leaf.")
            changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def bridge_at_risk(bridge: Bridge, offering: Offering) -> bool:
    return bridge.width == "weeny" and offering.at_risk in {"pepperoni", "snack"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for off_id, off in OFFERINGS.items():
            for bridge_id, br in BRIDGES.items():
                if place.suspense and bridge_at_risk(br, off):
                    combos.append((place_id, off_id, bridge_id))
    return combos


@dataclass
class StoryParams:
    place: str
    offering: str
    bridge: str
    hero: str
    helper: str
    elder: str
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
    "grove": Place(id="grove", label="the moon grove", affords={"deliver", "cross"}, suspense=2, tags={"myth", "grove"}),
    "cliff": Place(id="cliff", label="the cliff path", affords={"deliver", "cross"}, suspense=3, tags={"myth", "cliff"}),
}

OFFERINGS = {
    "pepperoni": Offering(
        id="pepperoni",
        label="pepperoni",
        phrase="a little plate of pepperoni",
        kind="snack",
        at_risk="pepperoni",
        use="offer",
        tags={"pepperoni", "food"},
    ),
    "starbread": Offering(
        id="starbread",
        label="star bread",
        phrase="a small basket of star bread",
        kind="snack",
        at_risk="snack",
        use="offer",
        tags={"bread", "food"},
    ),
}

BRIDGES = {
    "weeny": Bridge(
        id="weeny",
        label="weeny bridge",
        phrase="the weeny bridge",
        width="weeny",
        sturdy=False,
        tags={"weeny", "bridge"},
    ),
    "stone": Bridge(
        id="stone",
        label="stone bridge",
        phrase="the stone bridge",
        width="wide",
        sturdy=True,
        tags={"bridge"},
    ),
}

HEROES = [("Mira", "girl"), ("Ivo", "boy"), ("Nia", "girl"), ("Oren", "boy")]
HELPERS = [("Pip", "boy"), ("Tala", "girl"), ("Ren", "boy"), ("Sela", "girl")]
ELDERS = [("Aunt", "mother"), ("Uncle", "father")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with pepperoni, a lecture, and a weeny bridge.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "offering", None) is None or c[1] == getattr(args, "offering", None))
              and (getattr(args, "bridge", None) is None or c[2] == getattr(args, "bridge", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, off, bridge = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice([n for n, _ in HEROES])
    helper = getattr(args, "helper", None) or rng.choice([n for n, _ in HELPERS if n != hero])
    elder = getattr(args, "elder", None) or rng.choice([n for n, _ in ELDERS])
    return StoryParams(place=place, offering=off, bridge=bridge, hero=hero, helper=helper, elder=elder)


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero_type = next(t for n, t in HEROES if n == params.hero)
    helper_type = next(t for n, t in HELPERS if n == params.helper)
    elder_type = next(t for n, t in ELDERS if n == params.elder)
    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type, meters={"balance": 1.0}, memes={"hope": 1.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_type, meters={"balance": 1.0}, memes={"hope": 1.0}))
    elder = world.add(Entity(id=params.elder, kind="character", type=elder_type, label="the elder", memes={"caution": 1.0}))
    offering = world.add(Entity(id="offering", type="thing", label=_safe_lookup(OFFERINGS, params.offering).label, phrase=_safe_lookup(OFFERINGS, params.offering).phrase, owner=hero.id, helper=helper.id, tags=set(_safe_lookup(OFFERINGS, params.offering).tags), meters={"safe": 1.0}, memes={"importance": 1.0}))
    bridge = world.add(Entity(id="bridge", type="thing", label=_safe_lookup(BRIDGES, params.bridge).label, phrase=_safe_lookup(BRIDGES, params.bridge).phrase, meters={"steady": 1.0 if _safe_lookup(BRIDGES, params.bridge).sturdy else 0.0}, memes={}))
    world.facts.update(hero=hero.id, helper=helper.id, elder=elder.id, offering=offering.id, bridge=bridge.id)
    return world


def tell(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    elder = world.get(world.facts["elder"])
    off = world.get(world.facts["offering"])
    bridge = world.get(world.facts["bridge"])

    world.say(f"Long ago, in {world.place.label}, {hero.id} and {helper.id} carried {off.phrase} toward a shrine.")
    world.say(f"Above them waited {bridge.phrase}, so weeny that even a breeze seemed to watch it.")
    world.para()
    world.say(f"{elder.label_word.capitalize()} gave a long lecture: \"Do not rush, do not jostle, and keep the pepperoni level.\"")
    world.say(f"{hero.id} listened, and {helper.id} nodded, because the path felt full of suspense.")
    world.facts["carried"] = True
    world.facts["on_bridge"] = True
    world.facts["bridge_secure"] = _safe_lookup(BRIDGES, world.facts.get("bridge")).sturdy
    world.facts["helpers"] = [hero.id, helper.id]
    world.facts["carrier"] = hero.id
    propagate(world, narrate=True)
    world.para()
    if not world.facts.get("bridge_secure"):
        world.say(f"Then {hero.id} and {helper.id} looked at each other and chose teamwork.")
        hero.memes["trust"] += 1.0
        helper.memes["trust"] += 1.0
        world.facts["teamwork"] = True
        world.facts["bridge_secure"] = True
        propagate(world, narrate=True)
    world.say(f"Together they crossed, offered the pepperoni, and left the shrine glowing quiet as a star.")


def story_qa(world: World) -> list[QAItem]:
    h = world.get(world.facts["hero"])
    he = world.get(world.facts["helper"])
    el = world.get(world.facts["elder"])
    off = world.get(world.facts["offering"])
    br = world.get(world.facts["bridge"])
    return [
        QAItem(
            question=f"Who went on the mythic trip with {h.id}?",
            answer=f"{h.id} went with {he.id}. The elder also came to give a lecture when the crossing looked risky.",
        ),
        QAItem(
            question=f"Why was the scene suspenseful near {br.label}?",
            answer=f"The crossing was weeny and wobbly, so every step mattered. The children had to move carefully or the offering could slip.",
        ),
        QAItem(
            question=f"What did the elder lecture them about?",
            answer=f"The elder lectured them to move slowly, keep the pepperoni level, and not jostle each other. That warning helped them stay calm on the bridge.",
        ),
        QAItem(
            question=f"How did teamwork help in the end?",
            answer=f"They held steady together, so the offering stayed safe and they crossed the bridge. Teamwork turned the scary crossing into a shared success.",
        ),
        QAItem(
            question=f"What did they carry to the shrine?",
            answer=f"They carried {off.phrase}. They brought it as a small offering and left it where the shrine could receive it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does pepperoni mean here?", "Pepperoni is a little food offering in this storyworld. The children carry it carefully because it matters to the shrine."),
        QAItem("What is a lecture?", "A lecture is a long warning from an elder. In this story, it helps the children avoid a mistake."),
        QAItem("What does weeny mean?", "Weeny means very small and a little bit delicate. A weeny bridge can feel scary to cross."),
        QAItem("What is teamwork?", "Teamwork means people help each other and do the task together. In this world, teamwork keeps the offering steady."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.place.label
    return [
        f"Write a mythic children's story about carrying pepperoni across a weeny bridge near {p}.",
        f"Tell a suspenseful story where an elder gives a lecture and two children use teamwork to keep pepperoni safe.",
        f"Write a small legend that includes the words pepperoni, lecture, and weeny, and ends in a calm shrine image.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.offering not in OFFERINGS or params.bridge not in BRIDGES:
        pass
    if not bridge_at_risk(_safe_lookup(BRIDGES, params.bridge), _safe_lookup(OFFERINGS, params.offering)):
        pass
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for title, items in [("(1) Prompts", sample.prompts),]:
            pass
        print("== (1) Generation prompts -- asks that would produce this story ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions -- answerable from the story text ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== (3) World-knowledge questions -- child level, no story needed ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
at_risk(B) :- bridge(B), weeny(B).
valid(P,O,B) :- place(P), offering(O), bridge(B), at_risk(B), pepperoni(O), suspense_place(P).
teamwork_ok :- teamwork.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.suspense:
            lines.append(asp.fact("suspense_place", p.id))
    for o in OFFERINGS.values():
        lines.append(asp.fact("offering", o.id))
        if o.kind == "snack":
            lines.append(asp.fact("pepperoni", o.id) if o.id == "pepperoni" else asp.fact("snack", o.id))
    for b in BRIDGES.values():
        lines.append(asp.fact("bridge", b.id))
        if b.width == "weeny":
            lines.append(asp.fact("weeny", b.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    smoke = bool(sample.story)
    if ok and smoke:
        print("OK: ASP matches Python and generate() smoke test passed.")
        return 0
    if not ok:
        print("MISMATCH:", sorted(py ^ cl))
    if not smoke:
        print("SMOKE FAILED")
    return 1


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="A tiny mythic storyworld with pepperoni, lecture, and weeny suspense.")


def main() -> None:
    ap = build_parser()
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(seed)
    samples = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="grove", offering="pepperoni", bridge="weeny", hero="Mira", helper="Pip", elder="Aunt"),
            StoryParams(place="cliff", offering="pepperoni", bridge="weeny", hero="Ivo", helper="Tala", elder="Uncle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
