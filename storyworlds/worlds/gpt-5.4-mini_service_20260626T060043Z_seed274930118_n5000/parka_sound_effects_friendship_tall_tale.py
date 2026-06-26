#!/usr/bin/env python3
"""
A standalone storyworld for a small Tall Tale domain:
a child, a parka, sound effects, and friendship.
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    parka: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the windy hill"
    weather: str = "windy"
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
class SoundEffect:
    id: str
    onomatopoeia: str
    cause: str
    delight: str
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
class FriendScene:
    id: str
    place: str
    together_line: str
    rescue_line: str
    ending_line: str
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
        self.lines: list[str] = []
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    effect: str
    scene: str
    name: str
    friend: str
    gender: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "hill": Setting(place="the windy hill", weather="windy"),
    "harbor": Setting(place="the harbor path", weather="breezy"),
    "yard": Setting(place="the backyard", weather="windy"),
}

EFFECTS = {
    "swish": SoundEffect(
        id="swish",
        onomatopoeia="swish-swish",
        cause="the long parka sleeves brushed the air",
        delight="it sounded like a train racing through a cloud",
        tags={"wind", "parka", "sound"},
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        onomatopoeia="whoosh",
        cause="the parka hood flipped up in the breeze",
        delight="it sounded like a secret kite taking off",
        tags={"wind", "parka", "sound"},
    ),
    "flap": SoundEffect(
        id="flap",
        onomatopoeia="flap-flap",
        cause="the hem of the parka danced at the knees",
        delight="it sounded like a happy flag saying hello",
        tags={"wind", "parka", "sound"},
    ),
}

SCENES = {
    "share_sound": FriendScene(
        id="share_sound",
        place="the windy hill",
        together_line="The two friends listened to the funny parka sounds and laughed until their cheeks were pink.",
        rescue_line="Then they made their own sound effects together, louder than the breeze.",
        ending_line="Soon the hill was full of swish-swish and whoosh, and nobody felt alone anymore.",
    ),
    "echo_game": FriendScene(
        id="echo_game",
        place="the harbor path",
        together_line="The friends played an echo game, and every parka sound bounced off the water like a tiny trumpet.",
        rescue_line="One friend took the lead and taught the other the next sound.",
        ending_line="Before long, the harbor path rang with flap-flap and laughter as bright as lantern light.",
    ),
    "march_tall": FriendScene(
        id="march_tall",
        place="the backyard",
        together_line="They marched in giant steps, and the parka made each step sound bigger than a drum parade.",
        rescue_line="When the wind tried to blow the tune away, the friends held hands and marched harder.",
        ending_line="At the end, the backyard echoed with a brave swish-swish march and a friendship that stood tall.",
    ),
}

GENDER_NAMES = {
    "girl": ["Maya", "Luna", "Nina", "Ivy", "Ada", "Pia"],
    "boy": ["Finn", "Theo", "Eli", "Noah", "Max", "Leo"],
}

FRIEND_NAMES = ["Jo", "Kai", "Milo", "Tess", "June", "Pip", "Ari", "Bea"]

TRAITS = ["bold", "bright", "curious", "cheerful", "spunky", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for effect in EFFECTS:
            for scene in SCENES:
                combos.append((place, effect, scene))
    return combos


def explain_invalid() -> str:
    return "(No story: this world needs a place, a sound effect, and a friendship scene.)"


def build_reasonable_story(world: World, hero: Entity, friend: Entity, effect: SoundEffect, scene: FriendScene) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait_word', 'little')} {hero.type} who loved a bright red parka.")
    world.say(f"{hero.pronoun().capitalize()} loved how {effect.onomatopoeia} the parka sounded, because {effect.cause}.")
    world.say(f"One day at {world.setting.place}, {hero.id} met {friend.id}, and the wind was tossing leaves like little boats.")
    world.para()
    world.say(f"{hero.id} pulled up the hood. {effect.onomatopoeia}! {effect.delight}.")
    friend = world.get(friend.id)
    friend.memes["left_out"] += 1
    world.say(f"At first, {friend.id} only watched, because {friend.pronoun('possessive')} own shoes felt too quiet for such a big sound.")
    world.say(f"Then {hero.id} smiled and said they could make the noise together.")
    world.para()
    world.say(scene.together_line)
    friend.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    friend.memes["left_out"] = 0
    world.say(scene.rescue_line)
    world.say(scene.ending_line)
    hero.meters["confidence"] += 1
    friend.meters["confidence"] += 1
    world.facts.update(hero=hero, friend=friend, effect=effect, scene=scene)


def tell(setting: Setting, effect: SoundEffect, scene: FriendScene, hero_name: str, gender: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    friend = world.add(Entity(id=friend_name, kind="character", type="child"))
    parka = world.add(Entity(id="parka", type="parka", label="parka", phrase="a bright red parka", owner=hero.id, worn_by=hero.id))
    hero.memes["trait_word"] = "tall-tale"
    hero.memes["friendship"] = 1
    hero.meters["warmth"] = 1
    parka.meters["dry"] = 1
    build_reasonable_story(world, hero, friend, effect, scene)
    world.facts["parka"] = parka
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    effect = _safe_fact(world, f, "effect")
    return [
        f'Write a tall-tale style story for a young child about a parka that goes "{effect.onomatopoeia}".',
        f"Tell a friendship story where {hero.id} shares a noisy parka moment with {friend.id}.",
        f"Write a short, cheerful story with sound effects, a parka, and two friends who end up laughing together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    effect = _safe_fact(world, f, "effect")
    scene = _safe_fact(world, f, "scene")
    return [
        QAItem(
            question=f"What made {hero.id}'s parka sound so funny?",
            answer=f"It sounded funny because the parka moved in the wind, making {effect.onomatopoeia} sounds when sleeves and the hood brushed the air.",
        ),
        QAItem(
            question=f"How did {hero.id} help {friend.id} stop feeling left out?",
            answer=f"{hero.id} invited {friend.id} to join the sound game, so they could make the parka noises together instead of listening alone.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{scene.ending_line} That showed the friends were happy and the lonely feeling was gone.",
        ),
        QAItem(
            question=f"Why is this story a friendship story?",
            answer=f"It is a friendship story because {hero.id} and {friend.id} chose to play together, share the noisy game, and finish smiling side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parka?",
            answer="A parka is a warm coat with a hood that people wear when the weather is cold or windy.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that copy noises, like swish or whoosh, so the story feels lively and easy to hear in your head.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, share play, and help each other feel included.",
        ),
        QAItem(
            question="Why do people wear a parka when it is windy?",
            answer="People wear a parka in windy weather because it helps keep them warm and comfortable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
selected_place(P) :- place(P).
selected_effect(E) :- effect(E).
selected_scene(S) :- scene(S).
valid_story(P,E,S) :- selected_place(P), selected_effect(E), selected_scene(S).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for e in EFFECTS:
        lines.append(asp.fact("effect", e))
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with parka sound effects and friendship.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--effect", choices=EFFECTS.keys())
    ap.add_argument("--scene", choices=SCENES.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "effect", None) and getattr(args, "effect", None) not in EFFECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "scene", None) and getattr(args, "scene", None) not in SCENES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    candidates = [c for c in combos if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None)) and (not getattr(args, "effect", None) or c[1] == getattr(args, "effect", None)) and (not getattr(args, "scene", None) or c[2] == getattr(args, "scene", None))]
    if not candidates:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, effect, scene = rng.choice(candidates)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(place=place, effect=effect, scene=scene, name=name, friend=friend, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EFFECTS, params.effect), _safe_lookup(SCENES, params.scene), params.name, params.gender, params.friend)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, e, s in valid_combos():
            params = StoryParams(place=p, effect=e, scene=s, name="Maya", friend="Kai", gender="girl")
            samples.append(generate(params))
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
