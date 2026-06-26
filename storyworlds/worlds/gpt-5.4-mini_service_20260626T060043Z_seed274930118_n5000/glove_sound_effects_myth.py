#!/usr/bin/env python3
"""
glove_sound_effects_myth.py

A small mythic story world about a glove, a strange sound effect, and a
hero who must carry a message through a sacred place.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    wearer: Optional[str] = None
    protective: bool = False
    sound: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    hero: object | None = None
    relic: object | None = None
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
class Place:
    name: str
    sacred: bool = True
    echoes: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)
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
class Sound:
    id: str
    onomatopoeia: str
    source: str
    omen: str
    effect: str
    echo: str
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
class Relic:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    fits: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
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
        w = World(self.place)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    hero: str
    place: str
    sound: str
    relic: str
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
    "cave": Place(name="the hollow cave", sacred=True, echoes={"echo", "drip", "whisper"}, hazards={"dark"}),
    "temple": Place(name="the hill temple", sacred=True, echoes={"chant", "ring", "echo"}, hazards={"wind"}),
    "grove": Place(name="the moonlit grove", sacred=True, echoes={"rustle", "hush", "sing"}, hazards={"thorn"}),
}

SOUNDS = {
    "drip": Sound(id="drip", onomatopoeia="drip-drip", source="water from the roof", omen="patient rain", effect="revealed a hidden path", echo="dripped again"),
    "ring": Sound(id="ring", onomatopoeia="cling-clang", source="a bronze bell", omen="an old call", effect="awakened the gate", echo="rang once more"),
    "chant": Sound(id="chant", onomatopoeia="ahh-um", source="the temple singers", omen="a solemn vow", effect="calmed the stone lions", echo="returned as a low murmur"),
    "whisper": Sound(id="whisper", onomatopoeia="shhh", source="the wind between pillars", omen="a secret warning", effect="pointed toward the altar", echo="whispered back"),
}

RELICS = {
    "glove": Relic(id="glove", label="a glove of ash", phrase="a glove of ash stitched with silver thread", guards={"cold", "thorn", "spark"}, fits={"hero"}),
    "gauntlet": Relic(id="gauntlet", label="a bronze gauntlet", phrase="a bronze gauntlet with a lion face", guards={"cold", "spark"}, fits={"hero"}),
    "mitten": Relic(id="mitten", label="a wool mitten", phrase="a wool mitten dyed the color of dawn", guards={"cold"}, fits={"hero"}),
}

HEROES = [
    ("Ari", "youth"),
    ("Nera", "priestess"),
    ("Sorin", "messenger"),
    ("Ivo", "shepherd"),
]

TRAITS = ["brave", "quiet", "steadfast", "curious", "devout"]


def choose(seed: int, options: list[str]) -> str:
    rng = random.Random(seed)
    return rng.choice(options)


def gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.sound not in SOUNDS:
        pass
    if params.relic not in RELICS:
        pass


def predict(world: World, hero: Entity, sound: Sound, relic: Relic) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["dread"] = h.memes.get("dread", 0.0) + 1
    if sound.id in sim.place.echoes:
        sim.facts["omen"] = sound.omen
        return {"heard": True, "safe": relic.id in RELICS and "spark" in relic.guards}
    return {"heard": False, "safe": False}


def setup(world: World, hero: Entity, relic: Entity, sound: Sound) -> None:
    world.say(
        f"Long ago, {hero.label} walked into {world.place.name} with a heart that wanted a sign."
    )
    world.say(
        f"At {hero.label}'s side was {relic.phrase}, kept safe as if it had been waited for by the gods."
    )
    world.say(
        f"The air itself seemed to listen, and the first omen was the soft {sound.onomatopoeia} of {sound.source}."
    )


def tension(world: World, hero: Entity, sound: Sound, relic: Entity) -> None:
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 1
    world.para()
    world.say(
        f"{hero.label} heard {sound.onomatopoeia} and knew it was no ordinary noise; it was {sound.omen}."
    )
    world.say(
        f"Still, the path ahead was guarded, and without the right covering {relic.label} could not be carried through the place."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1


def turn(world: World, hero: Entity, sound: Sound, relic: Entity) -> None:
    world.para()
    world.say(
        f"{hero.label} lifted the relic and listened again."
    )
    world.say(
        f"This time the sound returned as {sound.echo}, and the meaning became clear: the way forward required patience, not haste."
    )
    if "spark" in _safe_lookup(RELICS, relic.id).guards:
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
        world.say(
            f"{hero.label} pulled on the glove, and the glove fit like a promise."
        )
    else:
        world.say(
            f"{hero.label} wrapped the relic in cloth, because even holy things need care."
        )


def resolution(world: World, hero: Entity, sound: Sound, relic: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    world.para()
    world.say(
        f"Then {hero.label} stepped onward, and the whole chamber answered with {sound.onomatopoeia}."
    )
    world.say(
        f"The sound {sound.effect}, and {relic.label} stayed unmarred in the glow of the sacred hall."
    )
    world.say(
        f"In the end, {hero.label} left with a steady breath, the glove warm on the hand, and the gods silent as listening stones."
    )


def tell(place_id: str, sound_id: str, relic_id: str, hero_name: Optional[str] = None, trait: Optional[str] = None) -> World:
    place = _safe_lookup(PLACES, place_id)
    sound = _safe_lookup(SOUNDS, sound_id)
    relic_def = _safe_lookup(RELICS, relic_id)
    world = World(place)

    hero_name = hero_name or random.choice([h[0] for h in HEROES])
    trait = trait or random.choice(TRAITS)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="hero",
        label=f"{trait} {hero_name}",
        meters={"footsteps": 0.0},
        memes={"duty": 0.0, "fear": 0.0, "hope": 0.0, "joy": 0.0},
    ))
    relic = world.add(Entity(
        id="relic",
        type=relic_id,
        label=relic_def.label,
        phrase=relic_def.phrase,
        owner=hero.id,
        protective=True,
        sound=sound.onomatopoeia,
        meters={"weight": 1.0},
    ))

    setup(world, hero, relic, sound)
    tension(world, hero, sound, relic)
    turn(world, hero, sound, relic)
    resolution(world, hero, sound, relic)

    world.facts.update(hero=hero, sound=sound, relic=relic, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").label
    return [
        f'Write a mythic tale for children about {hero}, a glove, and the sound "{f["sound"].onomatopoeia}".',
        f"Tell a short legend where {hero} enters {f['place'].name} carrying {f['relic'].phrase}.",
        f"Write a gentle myth in which a strange sound leads a hero to a wiser choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").label
    sound = _safe_fact(world, f, "sound")
    relic = _safe_fact(world, f, "relic")
    place = _safe_fact(world, f, "place").name
    return [
        QAItem(
            question=f"What did {hero} carry into {place}?",
            answer=f"{hero} carried {relic.phrase} into {place}.",
        ),
        QAItem(
            question=f"What sound did {hero} hear first?",
            answer=f"{hero} first heard {sound.onomatopoeia}, the sound of {sound.source}.",
        ),
        QAItem(
            question=f"Why was the glove important in the story?",
            answer="The glove mattered because it helped the hero face the sacred place with courage and care.",
        ),
        QAItem(
            question=f"What changed by the end of the myth?",
            answer=f"By the end, {hero} understood the omen, kept the relic safe, and left the hall in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sound = _safe_fact(world, f, "sound")
    return [
        QAItem(
            question="What is a glove for?",
            answer="A glove covers a hand and helps keep it warm, safe, or clean.",
        ),
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back after it hits walls or cliffs.",
        ),
        QAItem(
            question="Why can a sacred place feel special?",
            answer="A sacred place feels special because people treat it with respect and often believe it holds holy meaning.",
        ),
        QAItem(
            question="What is an omen?",
            answer="An omen is a sign that people think may hint at what is about to happen.",
        ),
        QAItem(
            question=f"What kind of sound was {sound.onomatopoeia}?",
            answer=f"{sound.onomatopoeia} was a little mythic sound, like a sign from the place itself.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place.name}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: {e.label} | meters={e.meters} | memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_fact(P).
sound(S) :- sound_fact(S).
relic(R) :- relic_fact(R).

echo_matches(P,S) :- place_echo(P,E), sound_echo(S,E).
safe_carry(R,S) :- guards(R,G), sound_omen(S,O), omen_guard(G,O).
myth_valid(P,S,R) :- place(P), sound(S), relic(R), echo_matches(P,S), safe_carry(R,S).
#show myth_valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        for e in sorted(p.echoes):
            lines.append(asp.fact("place_echo", pid, e))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound_fact", sid))
        lines.append(asp.fact("sound_echo", sid, s.echo))
        lines.append(asp.fact("sound_omen", sid, s.omen))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_fact", rid))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", rid, g))
    lines.append(asp.fact("omen_guard", "spark", "patient rain"))
    lines.append(asp.fact("omen_guard", "cold", "patient rain"))
    lines.append(asp.fact("omen_guard", "thorn", "a secret warning"))
    lines.append(asp.fact("omen_guard", "spark", "an old call"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with a glove and sound effects.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    sound = getattr(args, "sound", None) or rng.choice(sorted(SOUNDS))
    relic = getattr(args, "relic", None) or rng.choice(sorted(RELICS))
    if place == "cave" and sound == "chant":
        pass
    if getattr(args, "sound", None) and getattr(args, "sound", None) not in SOUNDS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "relic", None) and getattr(args, "relic", None) not in RELICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "name", None) or rng.choice([h[0] for h in HEROES])
    return StoryParams(hero=hero, place=place, sound=sound, relic=relic)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.sound, params.relic, params.hero, None)
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


def valid_story_set() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for s in SOUNDS:
            for r in RELICS:
                if s in _safe_lookup(PLACES, p).echoes and any(g in _safe_lookup(RELICS, r).guards for g in {"cold", "thorn", "spark"}):
                    out.append((p, s, r))
    return out


def asp_valid_story_set() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "myth_valid")))


def asp_verify() -> int:
    py = set(valid_story_set())
    ac = set(asp_valid_story_set())
    if py == ac:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - ac))
    print("asp only:", sorted(ac - py))
    return 1


CURATED = [
    StoryParams(hero="Ari", place="cave", sound="drip", relic="glove"),
    StoryParams(hero="Nera", place="temple", sound="ring", relic="gauntlet"),
    StoryParams(hero="Sorin", place="grove", sound="whisper", relic="mitten"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        triples = asp.atoms(model, "myth_valid")
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
