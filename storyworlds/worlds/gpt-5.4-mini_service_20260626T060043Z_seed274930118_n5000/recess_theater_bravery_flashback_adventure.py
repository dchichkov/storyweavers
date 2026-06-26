#!/usr/bin/env python3
"""
storyworlds/worlds/recess_theater_bravery_flashback_adventure.py
===============================================================

A small adventure storyworld about recess, theater, bravery, and a flashback.

Premise:
- A child loves to put on a tiny theater show at recess.
- Something from before makes the child hesitate.
- A kind helper turns the memory into courage.
- The story ends with a brave performance that changes the child's feelings.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["tired", "safe", "notice", "stage_ready"]:
            self.meters.setdefault(k, 0.0)
        for k in ["bravery", "fear", "joy", "hope", "flashback", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    texture: str = ""
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
class Scene:
    id: str
    label: str
    verb: str
    gerund: str
    stage_prop: str
    risk: str
    mood: str
    keyword: str
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
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    boosts: set[str] = field(default_factory=set)
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["flashback"] < THRESHOLD or actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("flashback_sentence", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["bravery"] += 0.5
        out.append(
            f"An old memory flashed through {actor.pronoun('possessive')} mind, "
            f"but it also showed how {actor.pronoun()} had made it through before."
        )
    return out


def _r_stage_ready(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["stage_ready"] < THRESHOLD:
            continue
        sig = ("stage_ready", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        actor.memes["pride"] += 1
        out.append(f"The little stage felt ready for a real show.")
    return out


CAUSAL_RULES = [
    Rule("flashback", _r_flashback),
    Rule("stage_ready", _r_stage_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_show(world: World, actor: Entity, scene: Scene) -> dict:
    sim = world.copy()
    _do_scene(sim, sim.get(actor.id), scene, narrate=False)
    hero = sim.get(actor.id)
    return {
        "brave": hero.memes["bravery"] >= THRESHOLD,
        "fear": hero.memes["fear"],
        "joy": hero.memes["joy"],
    }


def _do_scene(world: World, actor: Entity, scene: Scene, narrate: bool = True) -> None:
    if scene.id not in world.setting.affords:
        pass
    actor.meters["stage_ready"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "recess-yard": Setting(
        place="the schoolyard at recess",
        affords={"recess"},
        texture="The playground was loud with sneakers and bright chatter.",
    ),
    "theater-corner": Setting(
        place="the little theater corner",
        affords={"theater"},
        texture="The curtain looked small, but it still felt like a real stage.",
    ),
}

SCENES = {
    "recess": Scene(
        id="recess",
        label="recess",
        verb="put on a play",
        gerund="putting on a play",
        stage_prop="cardboard masks",
        risk="freeze up",
        mood="busy",
        keyword="recess",
        tags={"recess", "adventure"},
    ),
    "theater": Scene(
        id="theater",
        label="theater",
        verb="perform a tiny show",
        gerund="performing a tiny show",
        stage_prop="paper crowns",
        risk="forget the lines",
        mood="brave",
        keyword="theater",
        tags={"theater", "adventure"},
    ),
}

PROPS = {
    "mask": Prop(
        id="mask",
        label="a cardboard mask",
        phrase="a shiny cardboard mask with a painted smile",
        type="mask",
        boosts={"bravery"},
    ),
    "script": Prop(
        id="script",
        label="a tiny script",
        phrase="a tiny script with three easy lines",
        type="script",
        boosts={"focus", "bravery"},
    ),
    "cape": Prop(
        id="cape",
        label="a red cape",
        phrase="a red cape that fluttered like a flag",
        type="cape",
        boosts={"bravery", "joy"},
    ),
}

NAMES = ["Maya", "Leo", "Nina", "Owen", "Pia", "Theo", "Rosa", "Ben"]
TRAITS = ["curious", "spirited", "quiet", "bold", "playful", "dreamy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s.place, sc.id) for s in SETTINGS.values() for sc in SCENES.values() if sc.id in s.affords]


@dataclass
class StoryParams:
    place: str
    scene: str
    name: str
    gender: str
    parent: str
    trait: str
    prop: str
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
    ap = argparse.ArgumentParser(description="A small storyworld about recess, theater, bravery, and flashbacks.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "they"])
    ap.add_argument("--parent", choices=["mother", "father", "teacher"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--prop", choices=PROPS)
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "scene", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "scene", None) is None or c[1] == getattr(args, "scene", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, scene = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy", "they"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "teacher"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    return StoryParams(place=place, scene=scene, name=name, gender=gender, parent=parent, trait=trait, prop=prop)


def tell(setting: Setting, scene: Scene, prop: Prop, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["small", trait]))
    helper = world.add(Entity(id="helper", kind="character", type=parent, label=parent))
    item = world.add(Entity(id="prop", type=prop.type, label=prop.label, phrase=prop.phrase, owner=hero.id, caretaker=helper.id))
    hero.memes["hope"] += 1

    world.say(
        f"{hero.id} was a {trait} child who loved the idea of {scene.gerund} at {setting.place}."
    )
    world.say(
        f"At home, {hero.id} kept {hero.pronoun('possessive')} {item.label} near the bed and imagined "
        f"{scene.label} feeling as big as a true adventure."
    )

    world.para()
    world.say(setting.texture)
    world.say(
        f"At recess, {hero.id} wanted to {scene.verb}, but {hero.pronoun('possessive')} thoughts snagged on an old flashback."
    )
    hero.memes["flashback"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} remembered a time when {hero.pronoun()} had almost {scene.risk}, and {hero.pronoun('possessive')} knees turned wobbly."
    )
    propagate(world)

    world.para()
    hero.memes["bravery"] += 1
    world.say(
        f"Then {parent} knelt beside {hero.id} and pointed to the {item.label}, saying, "
        f'\"You already got through the hard part once. Let the memory turn into bravery.\"'
    )
    world.say(
        f"{hero.id} took a slow breath, held the {item.label}, and stepped toward the little stage."
    )
    _do_scene(world, hero, scene, narrate=True)

    world.para()
    helper.meters["notice"] += 1
    world.say(
        f"{hero.id} used {hero.pronoun('possessive')} clear voice to begin the show, and the {item.label} made the performance shine."
    )
    world.say(
        f"When the last line landed, the whole recess seemed to pause, and then {parent} clapped first."
    )
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["flashback"] = 0.0

    world.facts.update(hero=hero, helper=helper, item=item, scene=scene, prop=prop, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write a short adventure story for a young child about {hero.id} and a {scene.label} show at recess.',
        f'Tell a gentle story where a child faces a flashback, finds bravery, and performs at {world.setting.place}.',
        f'Write a small story that includes recess, theater, bravery, and a helpful memory turning into courage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    scene = _safe_fact(world, f, "scene")
    item = _safe_fact(world, f, "item")
    parent = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {scene.verb}.",
        ),
        QAItem(
            question=f"What memory made {hero.id} hesitate before the show?",
            answer=f"{hero.id} had a flashback about almost {scene.risk}, so {hero.id} felt scared for a moment.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} become brave?",
            answer=f"{parent.label} reminded {hero.id} that the hard part had happened before, and that turned the memory into bravery.",
        ),
        QAItem(
            question=f"What helped the performance feel special in the end?",
            answer=f"The {item.label} and {hero.id}'s brave voice helped the show feel special at recess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is recess?",
            answer="Recess is a break at school when children can run, play, and talk with friends.",
        ),
        QAItem(
            question="What is theater?",
            answer="Theater is a place where people act out a story for others to watch.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a memory from before pops into your mind very suddenly.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    lines.append(f"  fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(S) :- setting(S), afford(S,recess).
prize_at_risk(S) :- setting(S), afford(S,theater).
valid_story(S, Sc) :- setting(S), afford(S,Sc).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", sid, a))
    for scid, sc in SCENES.items():
        lines.append(asp.fact("scene", scid))
        for t in sorted(sc.tags):
            lines.append(asp.fact("tag", scid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    found = set(asp.atoms(model, "valid_story"))
    expected = set((p, sc) for p, sc in valid_combos())
    if found == expected:
        print(f"OK: clingo gate matches valid_combos() ({len(found)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(found - expected))
    print(" only in python:", sorted(expected - found))
    return 1


CURATED = [
    StoryParams(place="recess-yard", scene="recess", name="Maya", gender="girl", parent="teacher", trait="curious", prop="script"),
    StoryParams(place="theater-corner", scene="theater", name="Leo", gender="boy", parent="mother", trait="bold", prop="cape"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SCENES, params.scene), _safe_lookup(PROPS, params.prop), params.name, params.gender, params.parent, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.name}: {p.scene} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
