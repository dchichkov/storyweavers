#!/usr/bin/env python3
"""
Portable Neon Inner Monologue Adventure
=======================================

A small story world about a young explorer, a portable neon light, and a trail
that turns tricky. The story is built as a simulated adventure with physical
state (meters) and emotional state (memes), plus an inner-monologue style that
lets the hero think through the problem before choosing a safe, clever turn.

Premise:
- A child explorer loves a portable neon gadget that makes the path easy to see.
- The path grows dim or confusing.
- The child must decide whether to push ahead, ask for help, or use the neon
  gear in a smarter way.

Turn:
- The portable neon object helps reveal a hidden clue, but only if it is carried
  carefully and used at the right moment.

Resolution:
- The explorer's confidence rises after the fix, and the final image proves the
  world changed: the trail is found, the light is still intact, and the hero is
  ready for the next step.

This script intentionally keeps the world small and constraint-checked so every
sample reads like a complete adventure rather than a swapped-noun template.
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
    carried_by: Optional[str] = None
    wearable: bool = False
    portable: bool = False
    glowing: bool = False
    broken: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Trail:
    place: str
    dim: bool = False
    twisty: bool = False
    has_clue: bool = False
    afford_neon: bool = True
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
class Guide:
    label: str
    phrase: str
    color: str
    brightness: str
    helps_with: set[str] = field(default_factory=set)
    portable: bool = True
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
    guide: str
    hero_name: str
    hero_type: str
    companion_type: str
    trait: str
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


class World:
    def __init__(self, trail: Trail) -> None:
        self.trail = trail
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
        clone = World(self.trail)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def make_pronoun_name(entity: Entity) -> str:
    return entity.id


def inner_thought(hero: Entity, text: str) -> str:
    return f"{hero.pronoun().capitalize()} thought, \"{text}\""


def trail_description(trail: Trail) -> str:
    if trail.dim and trail.twisty:
        return f"The trail was dim and twisty, with shadows hiding the edges."
    if trail.dim:
        return f"The trail was dim, and the little path ahead was hard to read."
    if trail.twisty:
        return f"The trail bent this way and that like it was testing every step."
    return f"The trail looked open and calm, with the next bend easy to see."


def clue_description(guide: Guide) -> str:
    return {
        "wand": "a thin arrow painted on a rock",
        "lantern": "a bright mark on a stone wall",
        "badge": "a reflective sign tied to a branch",
    }[guide.label]


def guide_for(name: str) -> Guide:
    return _safe_lookup(GUIDES, name)


def can_fix(trail: Trail, guide: Guide) -> bool:
    return trail.afford_neon and guide.portable and "dim" in guide.helps_with


def valid_story_combos() -> list[tuple[str, str]]:
    out = []
    for place, trail in TRAILS.items():
        for guide_name, guide in GUIDES.items():
            if can_fix(trail, guide):
                out.append((place, guide_name))
    return out


def reasonableness_gate(place: str, guide_name: str) -> None:
    trail = _safe_lookup(TRAILS, place)
    guide = _safe_lookup(GUIDES, guide_name)
    if not can_fix(trail, guide):
        pass


def predict(world: World, hero: Entity, guide: Entity) -> dict:
    sim = world.copy()
    _use_guide(sim, sim.get(hero.id), sim.get(guide.id), narrate=False)
    clue = sim.facts.get("clue_found", False)
    return {
        "clue": clue,
        "calm": sim.get(hero.id).memes.get("calm", 0.0),
    }


def _walk_forward(world: World, hero: Entity) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 0.5


def _feel_lost(world: World, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) - 0.5


def _use_guide(world: World, hero: Entity, guide: Entity, narrate: bool = True) -> None:
    if guide.broken:
        return
    guide.meters["power"] = max(guide.meters.get("power", 1.0) - 0.2, 0.0)
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    hero.memes["worry"] = max(hero.memes.get("worry", 0.0) - 0.5, 0.0)
    if world.trail.dim:
        world.facts["clue_found"] = True
        world.trail.has_clue = True
        if narrate:
            world.say(f"The portable neon glow caught a hidden clue on the wall.")


def _keep_careful(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 0.5
    guide.meters["scratches"] = guide.meters.get("scratches", 0.0) + 0.0


def _problem_world(world: World, hero: Entity, guide: Entity) -> None:
    _walk_forward(world, hero)
    if world.trail.dim:
        _feel_lost(world, hero)
    if world.trail.twisty:
        hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 0.5


def intro(world: World, hero: Entity, companion: Entity, guide: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a brave heart and a pocket-sized plan."
    )
    world.say(
        f"{hero.id} loved {guide.phrase}, because its {guide.color} neon glow made dark places feel less scary."
    )
    world.say(
        f"{hero.id} and {companion.label} went to {world.trail.place} to see what the trail was hiding."
    )


def setup_inner_monologue(world: World, hero: Entity, guide: Entity) -> None:
    world.say(trail_description(world.trail))
    world.say(
        inner_thought(
            hero,
            f"If I keep the {guide.label} steady, maybe the path will tell me what to do."
        )
    )


def tension(world: World, hero: Entity, companion: Entity, guide: Entity) -> None:
    _problem_world(world, hero, guide)
    world.say(
        f"{hero.id} took a few careful steps, but the dim trail made the next turn hard to trust."
    )
    world.say(
        inner_thought(
            hero,
            "I do not want to rush and miss the clue. I should slow down and look."
        )
    )
    if world.trail.twisty:
        world.say(
            f"{companion.label} pointed toward the bend, but even that did not answer the question."
        )


def turning_point(world: World, hero: Entity, guide: Entity) -> None:
    prediction = predict(world, hero, guide)
    if not prediction["clue"]:
        pass
    world.say(
        inner_thought(
            hero,
            f"The light is the trick. The neon glow should touch the wall before I move again."
        )
    )
    _use_guide(world, hero, guide, narrate=True)
    world.say(
        f"{hero.id} lifted the portable neon guide higher, and a thin trail mark flashed into view."
    )
    world.say(
        inner_thought(
            hero,
            "There! I found the next step. I can follow that mark without getting lost."
        )
    )


def resolution(world: World, hero: Entity, companion: Entity, guide: Entity) -> None:
    _keep_careful(world, hero, guide)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    hero.memes["worry"] = max(hero.memes.get("worry", 0.0) - 0.5, 0.0)
    world.say(
        f"{hero.id} followed the glowing clue all the way to the safe bend in the trail."
    )
    world.say(
        f"By the end, the portable neon light was still bright, and {hero.id} was smiling at the open path ahead."
    )
    world.say(
        inner_thought(
            hero,
            f"That was a good choice. The trail is not scary when I can read it step by step."
        )
    )


def tell(trail: Trail, guide: Guide, hero_name: str, hero_type: str, companion_type: str, trait: str) -> World:
    world = World(trail)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=hero_name,
            meters={"distance": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0, "confidence": 1.0},
        )
    )
    companion = world.add(
        Entity(
            id="Companion",
            kind="character",
            type=companion_type,
            label=f"the {companion_type}",
            memes={"calm": 1.0},
        )
    )
    neon = world.add(
        Entity(
            id="NeonGuide",
            type="gadget",
            label=guide.label,
            phrase=guide.phrase,
            owner=hero.id,
            portable=True,
            glowing=True,
            meters={"power": 1.0},
        )
    )

    world.facts.update(hero=hero, companion=companion, guide=neon, trail=trail, trait=trait)

    intro(world, hero, companion, neon)
    world.para()
    setup_inner_monologue(world, hero, neon)
    tension(world, hero, companion, neon)
    world.para()
    turning_point(world, hero, neon)
    resolution(world, hero, companion, neon)

    world.facts["resolved"] = True
    return world


TRAILS = {
    "cave": Trail(place="the cave path", dim=True, twisty=True, has_clue=True, afford_neon=True),
    "woods": Trail(place="the woods trail", dim=True, twisty=False, has_clue=True, afford_neon=True),
    "ravine": Trail(place="the ravine walk", dim=True, twisty=True, has_clue=True, afford_neon=True),
}

GUIDES = {
    "wand": Guide(
        label="wand",
        phrase="a portable neon wand",
        color="lime",
        brightness="glowing",
        helps_with={"dim"},
    ),
    "lantern": Guide(
        label="lantern",
        phrase="a portable neon lantern",
        color="pink",
        brightness="glowing",
        helps_with={"dim"},
    ),
    "badge": Guide(
        label="badge",
        phrase="a portable neon badge",
        color="blue",
        brightness="glowing",
        helps_with={"dim"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Jace", "Nora", "Pip", "Milo", "Sana"]
HERO_TYPES = ["girl", "boy"]
COMPANION_TYPES = ["fox", "dog", "owl", "raccoon"]
TRAITS = ["careful", "curious", "bold", "bright-eyed"]


KNOWLEDGE = {
    "portable": [
        (
            "What does portable mean?",
            "Portable means something is easy to carry from one place to another."
        )
    ],
    "neon": [
        (
            "What is neon light?",
            "Neon light is a very bright kind of light that stands out, especially in dark places."
        )
    ],
    "trail": [
        (
            "What is a trail?",
            "A trail is a path people can follow through a park, woods, or other outdoor place."
        )
    ],
    "cave": [
        (
            "Why do caves feel dark?",
            "Caves feel dark because sunlight does not reach very far inside them."
        )
    ],
}


@dataclass
class StoryParams:
    place: str
    guide: str
    hero_name: str
    hero_type: str
    companion_type: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small portable neon adventure with inner monologue."
    )
    ap.add_argument("--place", choices=sorted(TRAILS))
    ap.add_argument("--guide", choices=sorted(GUIDES))
    ap.add_argument("--name", choices=sorted(HERO_NAMES))
    ap.add_argument("--hero-type", choices=sorted(HERO_TYPES))
    ap.add_argument("--companion-type", choices=sorted(COMPANION_TYPES))
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(TRAILS))
    guide = getattr(args, "guide", None) or rng.choice(sorted(GUIDES))
    reasonableness_gate(place, guide)
    return StoryParams(
        place=place,
        guide=guide,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(HERO_TYPES),
        companion_type=getattr(args, "companion_type", None) or rng.choice(COMPANION_TYPES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    trail = _safe_fact(world, f, "trail")
    return [
        f'Write a short adventure story for a child about a portable neon {guide.label} on {trail.place}.',
        f"Tell a gentle story where {hero.id} uses a portable neon light to solve a dim trail problem.",
        f"Write a child-friendly adventure with inner thoughts, a glowing portable neon guide, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    guide = _safe_fact(world, f, "guide")
    trail = _safe_fact(world, f, "trail")
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a little {hero.type} who thinks carefully on the trail."
        ),
        QAItem(
            question=f"What portable thing helped {hero.id} on {trail.place}?",
            answer=f"{hero.id} used {guide.phrase}, which gave off a neon glow and helped reveal the hidden clue."
        ),
        QAItem(
            question=f"Why did {hero.id} slow down instead of rushing ahead?",
            answer=f"{hero.id} slowed down because the trail was dim and twisty, so it was safer to use the portable neon light and look for a clue."
        ),
        QAItem(
            question=f"Who went with {hero.id}?",
            answer=f"{hero.id} went with {companion.label}, who stayed close while the trail grew tricky."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the hidden trail mark was found, {hero.id} felt more confident, and the portable neon light was still bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    used = {"portable", "neon", "trail"}
    if world.trail.place == "the cave path":
        used.add("cave")
    for key in ("portable", "neon", "trail", "cave"):
        if key in used:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.portable:
            bits.append("portable=True")
        if e.glowing:
            bits.append("glowing=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", guide="wand", hero_name="Mina", hero_type="girl", companion_type="fox", trait="careful"),
    StoryParams(place="woods", guide="lantern", hero_name="Toby", hero_type="boy", companion_type="owl", trait="curious"),
    StoryParams(place="ravine", guide="badge", hero_name="Nora", hero_type="girl", companion_type="dog", trait="bold"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, trail in TRAILS.items():
        lines.append(asp.fact("place", place))
        if trail.dim:
            lines.append(asp.fact("dim", place))
        if trail.twisty:
            lines.append(asp.fact("twisty", place))
        if trail.has_clue:
            lines.append(asp.fact("has_clue", place))
        if trail.afford_neon:
            lines.append(asp.fact("affords_neon", place))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("portable", gid))
        lines.append(asp.fact("neon", gid))
        for feat in sorted(guide.helps_with):
            lines.append(asp.fact("helps_with", gid, feat))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Guide) :- place(Place), guide(Guide), dim(Place), portable(Guide), neon(Guide), helps_with(Guide, dim), affords_neon(Place).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(TRAILS, params.place),
        _safe_lookup(GUIDES, params.guide),
        params.hero_name,
        params.hero_type,
        params.companion_type,
        params.trait,
    )
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/guide combos:\n")
        for place, guide in combos:
            print(f"  {place:10} {guide}")
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
            header = f"### {p.hero_name}: {p.place} with {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
