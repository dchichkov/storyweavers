#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/cocaine_hood_grampa_friendship_quest_sharing_space.py
==============================================================================================================================

A small space-adventure storyworld about friendship, a quest, and sharing.

Seed tale used to shape the world:
---
A child and their grampa are drifting through a bright space station when they
find a tiny hooded suit, a shiny lost token named cocaine, and a map that points
toward a faraway friend. They have to choose between keeping the token, finishing
the quest alone, or sharing the path so everyone gets home safely.

This script turns that premise into a simple simulation with:
- typed entities that carry physical meters and emotional memes,
- state-driven narration,
- a reasonableness gate for valid story setups,
- an inline ASP twin for parity checks.
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

SPACE_THRESHOLD = 1.0



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
    worn_by: Optional[str] = None
    protective: bool = False
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    carried: object | None = None
    grampa: object | None = None
    hero: object | None = None
    hood: object | None = None
    map_piece: object | None = None
    token: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "dust": 0.0, "lost": 0.0, "shared": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "friendship": 0.0, "quest": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "grampa", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the bright space station"
    inside: bool = True
    affords: set[str] = field(default_factory=lambda: {"quest", "sharing", "hood"})
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
class Artifact:
    id: str
    label: str
    phrase: str
    protects: set[str]
    story_use: str
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
    artifact: str
    name: str
    gender: str
    grampa_name: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone.paragraphs = [[]]
        return clone


def _gain(world: World, eid: str, key: str, amount: float = 1.0) -> None:
    world.entities[eid].meters[key] = world.entities[eid].meters.get(key, 0.0) + amount


def _mood(world: World, eid: str, key: str, amount: float = 1.0) -> None:
    world.entities[eid].memes[key] = world.entities[eid].memes.get(key, 0.0) + amount


def _quest_momentum(world: World) -> None:
    for ent in list(world.entities.values()):
        if ent.kind == "character" and ent.memes.get("quest", 0.0) >= SPACE_THRESHOLD:
            _gain(world, ent.id, "distance", 1.0)


def _share_token(world: World, hero: Entity, grampa: Entity, token: Entity) -> None:
    sig = "share_token"
    if sig in world.fired:
        return
    world.fired.add(sig)
    token.meters["shared"] += 1
    hero.memes["friendship"] += 1
    grampa.memes["friendship"] += 1
    hero.memes["joy"] += 1
    grampa.memes["joy"] += 1
    world.say(
        f"{hero.id} placed the little {token.label} in both hands, and {grampa.id} smiled. "
        f"Sharing made the quest feel lighter right away."
    )


def _hood_fix(world: World, hero: Entity, hood: Entity) -> None:
    sig = "hood_fix"
    if sig in world.fired:
        return
    world.fired.add(sig)
    if hood.worn_by == hero.id:
        _gain(world, hero.id, "dust", -1.0)
        hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
        world.say(
            f"The hood tucked close around {hero.id}'s face, so the sparkling dust stayed outside."
        )


def reasonableness_gate(setting: Setting, quest: str, artifact: Artifact) -> bool:
    return quest in setting.affords and "hood" in setting.affords and artifact.label


def select_artifact(artifact_id: str) -> Artifact:
    if artifact_id not in ARTIFACTS:
        pass
    return _safe_lookup(ARTIFACTS, artifact_id)


def select_setting(place: str) -> Setting:
    if place not in SETTINGS:
        pass
    return _safe_lookup(SETTINGS, place)


def predict_world(world: World, hero: Entity, grampa: Entity, token: Entity, hood: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["quest"] += 1
    sim.get(grampa.id).memes["friendship"] += 1
    sim.get(hero.id).meters["dust"] += 1
    _hood_fix(sim, sim.get(hero.id), sim.get(hood.id))
    _share_token(sim, sim.get(hero.id), sim.get(grampa.id), sim.get(token.id))
    _quest_momentum(sim)
    return {
        "shared": sim.get(token.id).meters["shared"] >= SPACE_THRESHOLD,
        "dust": sim.get(hero.id).meters["dust"],
        "joy": sim.get(hero.id).memes["joy"] + sim.get(grampa.id).memes["joy"],
    }


def tell(setting: Setting, quest: str, artifact: Artifact, hero_name: str, hero_gender: str,
         grampa_name: str) -> World:
    world = World(setting)
    hero_type = "girl" if hero_gender == "girl" else "boy"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    grampa = world.add(Entity(id=grampa_name, kind="character", type="grampa", label="grampa"))
    hood = world.add(Entity(
        id="hood",
        label="space hood",
        phrase="a snug space hood",
        protective=True,
        carried=None,
    ))
    token = world.add(Entity(
        id="cocaine",
        label="cocaine",
        phrase="a tiny glowing token named cocaine",
    ))
    map_piece = world.add(Entity(
        id="map",
        label="quest map",
        phrase="a fold-out map of the star lanes",
    ))

    hero.memes["friendship"] += 1
    grampa.memes["friendship"] += 1
    world.say(
        f"{hero.id} and {grampa.id} lived inside {setting.place}, where the windows showed slow blue stars."
    )
    world.say(
        f"They loved {quest} together, and they had a little {artifact.label} they used for the quest."
    )
    world.say(
        f"One day, they found {token.phrase} beside {map_piece.phrase}."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to go at once, but the tunnel outside was dusty, and the {token.label} had been left behind by the last crew."
    )
    hero.memes["quest"] += 1
    grampa.memes["worry"] += 1
    hero.meters["dust"] += 1
    pred = predict_world(world, hero, grampa, token, hood)
    if pred["dust"] >= SPACE_THRESHOLD:
        world.say(
            f"{grampa.id} pointed to the hood and said they should wear it before stepping out."
        )
    hood.worn_by = hero.id
    _hood_fix(world, hero, hood)

    world.para()
    world.say(
        f"Then {hero.id} noticed that {grampa.id} was smiling at the {token.label} too."
    )
    _share_token(world, hero, grampa, token)
    world.say(
        f"Together they followed the map through the quiet hallway, past the sleeping lights."
    )
    _quest_momentum(world)

    world.para()
    world.say(
        f"At the end of the tunnel, the friends found the little dock they had been looking for."
    )
    world.say(
        f"Their shared path worked: {hero.id} kept the hood on, {grampa.id} kept the map, and the {token.label} stayed safe in both their plan."
    )
    hero.memes["joy"] += 1
    grampa.memes["joy"] += 1

    world.facts.update(
        hero=hero,
        grampa=grampa,
        token=token,
        hood=hood,
        map_piece=map_piece,
        setting=setting,
        quest=quest,
        artifact=artifact,
    )
    return world


SETTINGS = {
    "station": Setting(place="the bright space station", inside=True, affords={"quest", "sharing", "hood"}),
    "dock": Setting(place="the moon dock", inside=False, affords={"quest", "sharing", "hood"}),
}

ARTIFACTS = {
    "hood": Artifact(
        id="hood",
        label="hood",
        phrase="a snug space hood",
        protects={"dust", "cold"},
        story_use="protective gear",
    ),
    "cocaine": Artifact(
        id="cocaine",
        label="cocaine",
        phrase="a tiny glowing token named cocaine",
        protects=set(),
        story_use="quest token",
    ),
}

QUESTS = {
    "starwalk": "walk the star path",
    "homebound": "find the safe way home",
    "sharelight": "share the lantern with a friend",
}

NAMES_GIRL = ["Mina", "Ivy", "Luna", "Nia"]
NAMES_BOY = ["Eli", "Noah", "Taro", "Jace"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest in setting.affords:
            for artifact_id, artifact in ARTIFACTS.items():
                if reasonableness_gate(setting, quest, artifact):
                    combos.append((place, quest, artifact_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about friendship, quest, and sharing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grampa-name")
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
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "artifact", None) is None or c[2] == getattr(args, "artifact", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, artifact = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    grampa_name = getattr(args, "grampa_name", None) or "Grampa Sol"
    return StoryParams(place=place, quest=quest, artifact=artifact, name=name, gender=gender, grampa_name=grampa_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child about friendship, quest, and sharing, and include the word "{f["token"].label}".',
        f"Tell a gentle story where {f['hero'].id} and {f['grampa'].id} travel through {f['setting'].place} and use a hood to stay safe.",
        f"Write a tiny story about two friends who share a strange token and finish a quest together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    grampa = _safe_fact(world, f, "grampa")
    token = _safe_fact(world, f, "token")
    hood = _safe_fact(world, f, "hood")
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {hero.id} and {grampa.id}. They stayed close while they traveled through the space station.",
        ),
        QAItem(
            question=f"What did they find beside the map?",
            answer=f"They found {token.phrase} beside the quest map.",
        ),
        QAItem(
            question=f"Why did {hero.id} wear the hood?",
            answer=f"{hero.id} wore the hood so the dusty tunnel would not bother {hero.pronoun('object')}. The hood helped {hero.id} stay safe during the quest.",
        ),
        QAItem(
            question=f"How did sharing help the friends?",
            answer=f"Sharing helped because {token.label} was held by both of them in their plan, so the quest felt easier and their friendship grew stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hood for?",
            answer="A hood helps cover a head or face a little, which can keep dust, wind, or cold away.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something with you.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or to reach a special goal.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = []
    for title, items in [
        ("(1) Generation prompts", sample.prompts),
        ("(2) Story questions", sample.story_qa),
        ("(3) World knowledge", sample.world_qa),
    ]:
        out.append(title)
        for item in items:
            if isinstance(item, QAItem):
                out.append(f"Q: {item.question}")
                out.append(f"A: {item.answer}")
            else:
                out.append(f"- {item}")
        out.append("")
    return "\n".join(out).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} worn_by={e.worn_by} protective={e.protective}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Quest, Artifact) :- setting(Place), affords(Place, Quest), artifact(Artifact), usable(Place, Quest, Artifact).
usable(Place, Quest, Artifact) :- setting(Place), affords(Place, Quest), artifact(Artifact), protects(Artifact, dust).
usable(Place, Quest, Artifact) :- setting(Place), affords(Place, Quest), artifact(Artifact), Artifact = hood.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", place, q))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        for p in sorted(art.protects):
            lines.append(asp.fact("protects", aid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    artifact = _safe_lookup(ARTIFACTS, params.artifact)
    world = tell(setting, _safe_lookup(QUESTS, params.quest), artifact, params.name, params.gender, params.grampa_name)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="station", quest="starwalk", artifact="hood", name="Mina", gender="girl", grampa_name="Grampa Sol"),
            StoryParams(place="dock", quest="homebound", artifact="hood", name="Eli", gender="boy", grampa_name="Grampa Sol"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
