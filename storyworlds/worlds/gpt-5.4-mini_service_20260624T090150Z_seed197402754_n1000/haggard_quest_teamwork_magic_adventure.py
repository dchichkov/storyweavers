#!/usr/bin/env python3
"""
A small Adventure-style storyworld about a quest, teamwork, and a little magic.

Seed tale:
- A haggard keeper has lost a magic key / lantern / map.
- A small team must cross a place, solve a problem, and use teamwork.
- A little magic helps, but only after the team works together.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero1: object | None = None
    hero2: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["dusty", "lost", "found", "blocked"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "bravery", "teamwork", "relief", "magic"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "keeper"}
        male = {"boy", "father", "dad", "man", "king", "guide"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    features: set[str] = field(default_factory=set)
    hazard: str = ""
    magic_kind: str = ""
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
class QuestItem:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    magic: bool = False
    needed_feature: str = ""
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
class StoryParams:
    place: str
    quest: str
    relic: str
    hero1: str
    hero2: str
    guide: str
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


PLACES = {
    "forest": Place(name="the forest", features={"path", "bridge", "glow"}, hazard="thorny brambles", magic_kind="moonlight"),
    "cave": Place(name="the cave", features={"dark", "echo", "door"}, hazard="slippery stones", magic_kind="sparkle"),
    "hill": Place(name="the hill", features={"wind", "gate", "stone"}, hazard="steep steps", magic_kind="warm light"),
}

QUESTS = {
    "find_map": "find the lost map",
    "open_gate": "open the old gate",
    "wake_lantern": "wake the sleepy lantern",
}

RELICS = {
    "map": QuestItem(id="map", label="map", phrase="a magic map", magic=True, needed_feature="glow"),
    "key": QuestItem(id="key", label="key", phrase="a silver key", magic=True, needed_feature="door"),
    "lantern": QuestItem(id="lantern", label="lantern", phrase="a small lantern", magic=True, needed_feature="dark"),
}

GIRL_NAMES = ["Maya", "Nina", "Luna", "Ada", "Iris", "Zoe"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Leo", "Eli", "Noah"]
GUIDES = ["keeper", "guide", "elder"]
TRAITS = ["haggard", "brave", "curious", "kind", "steady"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _apply_teamwork(world: World) -> list[str]:
    out = []
    team = [e for e in world.entities.values() if e.kind == "character" and e.memes["teamwork"] >= THRESHOLD]
    if len(team) < 2:
        return out
    sig = "teamwork_bridge"
    if sig in world.fired:
        return out
    if world.place.hazard:
        world.fired.add(sig)
        world.facts["teamwork_used"] = True
        out.append("Together, they found a way forward.")
    return out


def _apply_magic(world: World) -> list[str]:
    out = []
    relic = world.facts.get("relic")
    if not relic:
        return out
    if relic.meters["found"] < THRESHOLD:
        return out
    sig = "magic_bloom"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["magic"] += 1
            e.memes["hope"] += 1
    out.append("The magic brightened the path.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_apply_teamwork, _apply_magic):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def resolve_problem(world: World, hero1: Entity, hero2: Entity, guide: Entity, relic: Entity) -> None:
    guide.memes["worry"] += 1
    world.say(f"{guide.id} looked haggard and said the {relic.label} had gone missing.")
    world.say(f"{hero1.id} and {hero2.id} promised to help on the quest.")
    hero1.memes["bravery"] += 1
    hero2.memes["bravery"] += 1
    hero1.memes["teamwork"] += 1
    hero2.memes["teamwork"] += 1
    world.say(f"They set out through {world.place.name}, where the air was full of {world.place.hazard}.")
    if world.place.magic_kind:
        world.say(f"At one bend, a little {world.place.magic_kind} shimmered on the stones.")
    relic.meters["lost"] = 1.0
    world.say(f"Their quest was to {world.facts['quest_text']}.")
    if world.place.features:
        feature = relic.needed_feature
        if feature in world.place.features:
            world.say(f"They followed the sign of {feature} and searched carefully together.")
    relic.meters["found"] = 1.0
    guide.memes["worry"] = 0.0
    guide.memes["relief"] += 1
    world.say(f"At last, they found {relic.phrase}.")
    propagate(world, narrate=True)
    world.say(f"{guide.id} smiled at the two friends, and the haggard look was gone.")


def tell(place: Place, quest_key: str, relic_key: str, hero1_name: str, hero2_name: str, guide_type: str) -> World:
    world = World(place)
    quest_text = _safe_lookup(QUESTS, quest_key)
    relic = _safe_lookup(RELICS, relic_key)
    hero1 = world.add(Entity(id=hero1_name, kind="character", type="girl" if hero1_name in GIRL_NAMES else "boy"))
    hero2 = world.add(Entity(id=hero2_name, kind="character", type="girl" if hero2_name in GIRL_NAMES else "boy"))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="the haggard guide"))
    item = world.add(Entity(id=relic.id, type=relic.type, label=relic.label, phrase=relic.phrase, owner=guide.id))

    world.facts.update(quest_text=quest_text, relic=item, hero1=hero1, hero2=hero2, guide=guide, place=place)

    world.say(f"{guide.label.capitalize()} stood by {place.name} with a worried face.")
    world.say(f"The guide told {hero1.id} and {hero2.id} that a {relic.phrase} was missing.")
    world.say(f"The two friends loved quests, and they wanted to help.")
    world.para()
    resolve_problem(world, hero1, hero2, guide, item)
    world.para()
    world.say(f"In the end, the friends walked home together, and the guide carried {item.it()} safely.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short Adventure story about a haggard {f['guide'].type} who needs help on a quest.",
        f"Tell a child-friendly tale where {f['hero1'].id} and {f['hero2'].id} use teamwork and magic to {f['quest_text']}.",
        f"Write a simple story set in {f['place'].name} with a lost magical object and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    guide = _safe_fact(world, f, "guide")
    hero1 = _safe_fact(world, f, "hero1")
    hero2 = _safe_fact(world, f, "hero2")
    relic = _safe_fact(world, f, "relic")
    return [
        QAItem(
            question=f"Who asked {hero1.id} and {hero2.id} for help?",
            answer=f"{guide.label.capitalize()} asked them for help because the guide was haggard and worried about the missing {relic.label}.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {f['quest_text']}.",
        ),
        QAItem(
            question=f"How did {hero1.id} and {hero2.id} solve the problem?",
            answer=f"They used teamwork, searched carefully in {world.place.name}, and found {relic.phrase}.",
        ),
        QAItem(
            question=f"What changed for the guide at the end?",
            answer=f"The guide felt relief, and the haggard look was gone after the friends brought back the {relic.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together on the same goal.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful and unusual that can make surprising things happen in a story.",
        ),
        QAItem(
            question="What does haggard mean?",
            answer="Haggard means looking very tired and worn out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "forest": PLACES["forest"],
    "cave": PLACES["cave"],
    "hill": PLACES["hill"],
}

QUESTS_ORDER = list(QUESTS)
RELICS_ORDER = list(RELICS)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_key, place in SETTINGS.items():
        for q in globals().get("QUESTS_ORDER", sorted(globals().get("QUESTS", []))):
            for r in globals().get("RELICS_ORDER", sorted(globals().get("RELICS", []))):
                if _safe_lookup(RELICS, r).needed_feature in place.features:
                    combos.append((place_key, q, r))
    return combos


def explain_rejection(place: Place, quest: str, relic: QuestItem) -> str:
    return f"(No story: {place.name} does not fit the quest for {relic.phrase}; the place lacks the needed sign.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a haggard guide, a quest, teamwork, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--guide", choices=GUIDES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, relic = rng.choice(list(combos))
    h1 = getattr(args, "hero1", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    h2 = getattr(args, "hero2", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != h1])
    guide = getattr(args, "guide", None) or rng.choice(GUIDES)
    return StoryParams(place=place, quest=quest, relic=relic, hero1=h1, hero2=h2, guide=guide)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.quest, params.relic, params.hero1, params.hero2, params.guide)
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


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_kind(Q).
relic(R) :- relic_kind(R).

compatible(P,Q,R) :- setting(P), quest_kind(Q), relic_kind(R), needs_feature(R,F), has_feature(P,F).

show_combo(P,Q,R) :- compatible(P,Q,R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k, p in SETTINGS.items():
        lines.append(asp.fact("setting", k))
        for f in sorted(p.features):
            lines.append(asp.fact("has_feature", k, f))
    for k in QUESTS:
        lines.append(asp.fact("quest_kind", k))
    for k, r in RELICS.items():
        lines.append(asp.fact("relic_kind", k))
        lines.append(asp.fact("needs_feature", k, r.needed_feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show show_combo/3."))
    return sorted(set(asp.atoms(model, "show_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show show_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="forest", quest="find_map", relic="map", hero1="Maya", hero2="Theo", guide="keeper"),
            StoryParams(place="cave", quest="wake_lantern", relic="lantern", hero1="Luna", hero2="Finn", guide="guide"),
            StoryParams(place="hill", quest="open_gate", relic="key", hero1="Ada", hero2="Leo", guide="elder"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
