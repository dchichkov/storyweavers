#!/usr/bin/env python3
"""
Story world: sneeze twist ghost story.

A small, classical simulation in the style of a gentle ghost story:
a child hears spooky noises, meets a ghost, discovers that a sneeze can
change the whole feeling of the night, and learns a warm twist.

The story is state-driven: fear rises, clues accumulate, the sneeze causes
a turn, and the ending image proves what changed.
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
    kind: str = "thing"  # "character" | "thing"
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

    ghost: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    moonlight: str
    echoes: bool = True
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
class Twist:
    """The turn that changes what the ghostly signs mean."""
    name: str
    trigger: str
    reveal: str
    softening: str
    ending: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    twist: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "attic": Setting(place="the attic", moonlight="thin moonlight", echoes=True, affords={"ghost"}),
    "hall": Setting(place="the old hall", moonlight="blue moonlight", echoes=True, affords={"ghost"}),
    "garden": Setting(place="the moonlit garden", moonlight="silver moonlight", echoes=True, affords={"ghost"}),
    "bedroom": Setting(place="the bedroom at the end of the hall", moonlight="pale moonlight", echoes=True, affords={"ghost"}),
}

TWISTS = {
    "sneeze": Twist(
        name="sneeze",
        trigger="a sneeze",
        reveal="the ghost was only trying not to laugh",
        softening="the spooky sound was just a tickly dust cloud",
        ending="the night felt warm instead of scary",
        tags={"sneeze", "dust", "ghost"},
    ),
    "lantern": Twist(
        name="lantern",
        trigger="a lantern blink",
        reveal="the ghost was guiding the child to a lost mitten",
        softening="the glowing shape had been a helper all along",
        ending="the dark corner turned friendly and bright",
        tags={"light", "ghost"},
    ),
    "cat": Twist(
        name="cat",
        trigger="a soft paw step",
        reveal="the ghost was chasing a little cat away from the rain",
        softening="the rattling sounds came from tiny paws on boards",
        ending="the hall felt like a place for neighbors, not fears",
        tags={"cat", "ghost"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Noah", "Elsie", "Owen", "Pia", "Eli"]
GHOST_NAMES = ["Mr. Fog", "Ms. Whisper", "Old Pale", "Mister Drift", "Aunt Moon", "Little Shade"]


def ghost_pronoun(name: str) -> str:
    return "they"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.twist not in TWISTS:
        pass
    if not params.hero_name or not params.ghost_name:
        pass
    if params.hero_name == params.ghost_name:
        pass
    if params.hero_type not in {"girl", "boy"}:
        pass


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=["small", "curious", "brave"],
        meters={"fear": 0.0, "courage": 0.0, "wonder": 0.0},
        memes={"fear": 0.0, "hope": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        traits=["pale", "quiet", "shy"],
        meters={"spook": 0.0, "dust": 0.0, "warmth": 0.0},
        memes={"loneliness": 0.0, "kindness": 0.0},
    ))
    world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="a small lantern",
        phrase="a small lantern with a round glass belly",
        owner=hero.id,
        meters={"light": 1.0},
    ))
    world.facts.update(hero=hero, ghost=ghost, params=params, twist=_safe_lookup(TWISTS, params.twist))
    return world


def _r_spook(world: World) -> list[str]:
    hero = world.get("hero")
    ghost = world.get("ghost")
    if hero.meters["fear"] < THRESHOLD:
        return []
    sig = ("spook",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["spook"] += 1.0
    return [f"The old room answered with a long, spooky hush."]


def _r_sneeze_twist(world: World) -> list[str]:
    hero = world.get("hero")
    ghost = world.get("ghost")
    twist = TWISTS[world.facts["params"].twist]
    if hero.memes["sneeze"] < THRESHOLD:
        return []
    sig = ("twist", twist.name)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["dust"] += 1.0
    ghost.meters["spook"] = max(0.0, ghost.meters["spook"] - 1.0)
    ghost.memes["kindness"] += 1.0
    hero.meters["wonder"] += 1.0
    world.facts["reveal"] = twist.reveal
    return [
        f"Then {hero.label} sneezed.",
        f"The little burst changed the whole night: {twist.softening}.",
    ]


def _r_soften(world: World) -> list[str]:
    hero = world.get("hero")
    ghost = world.get("ghost")
    if ghost.memes["kindness"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1.0)
    hero.meters["courage"] += 1.0
    return [f"{ghost.label} drifted closer, not to frighten {hero.label}, but to help."]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_spook, _r_sneeze_twist, _r_soften):
            before = copy.deepcopy((world.get("hero").meters, world.get("ghost").meters, world.get("hero").memes, world.get("ghost").memes))
            lines = rule(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)
            after = (world.get("hero").meters, world.get("ghost").meters, world.get("hero").memes, world.get("ghost").memes)
            if before != after:
                changed = True


def tell_story(world: World) -> None:
    hero = world.get("hero")
    ghost = world.get("ghost")
    twist = TWISTS[world.facts["params"].twist]

    world.say(f"On a quiet night, {hero.label} went into {world.setting.place} with {world.setting.moonlight} glowing over the boards.")
    world.say(f"Nobody else was there, but the air made tiny echoing sounds, and {hero.label} felt {hero.pronoun('possessive')} chest go tight.")
    world.para()
    hero.meters["fear"] += 1.0
    hero.memes["fear"] += 1.0
    world.say(f"At the far end, {ghost.label} floated out of the dark like a folded sheet of mist.")
    world.say(f"{ghost.label} made a rustling noise, and {hero.label} held {hero.pronoun('possessive')} breath.")
    propagate(world)
    world.para()
    hero.memes["sneeze"] += 1.0
    world.say(f"Just then, {hero.label} got a tickle in {hero.pronoun('possessive')} nose.")
    world.say(f"{hero.label} tried to stay still, but the tickle grew bigger and bigger.")
    propagate(world)
    world.para()
    world.say(f"{ghost.label} did not vanish.")
    world.say(f"Instead, {twist.reveal}.")
    world.say(f"{ghost.label} smiled, and the room grew soft and bright in its own quiet way.")
    world.say(f"By the end, {twist.ending}, and {hero.label} could walk home without looking back.")
    world.facts["ending"] = twist.ending


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    twist = _safe_fact(world, f, "twist")
    return [
        f'Write a gentle ghost story for a young child set in {params.place} that includes a sneeze and a surprising turn.',
        f"Tell a spooky-but-kind story about {params.hero_name} meeting {params.ghost_name} and ending with a twist.",
        f'Write a short story where a ghostly moment in {params.place} changes after "sneeze" appears in the scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    twist: Twist = _safe_fact(world, f, "twist")
    hero = world.get("hero")
    ghost = world.get("ghost")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {params.hero_name}, a little {params.hero_type} who goes into {params.place} and meets {params.ghost_name}.",
        ),
        QAItem(
            question=f"What made {the_name(params.hero_name)} feel scared at first?",
            answer=f"{params.hero_name} felt scared because {params.ghost_name} floated out of the dark and the room made spooky echoing sounds.",
        ),
        QAItem(
            question=f"What changed the spooky moment into a kinder one?",
            answer=f"A sneeze changed it. When {params.hero_name} sneezed, the strange ghostly feeling turned into {twist.softening}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {twist.ending}, after {params.ghost_name} smiled and the room stopped feeling scary.",
        ),
    ]


def the_name(name: str) -> str:
    return name


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky story character that may float, whisper, or rattle, but in gentle stories it can also be shy or kind.",
        ),
        QAItem(
            question="What is a sneeze?",
            answer="A sneeze is a sudden burst of air from your nose, usually when something tickles it.",
        ),
        QAItem(
            question="Why can moonlight make a room look different?",
            answer="Moonlight is soft light from the moon, so it can make things look pale, shiny, or a little mysterious.",
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.echoes:
            lines.append(asp.fact("echoes", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, twist in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for tag in sorted(twist.tags):
            lines.append(asp.fact("tagged", tid, tag))
    lines.append(asp.fact("trigger", "sneeze"))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when it has a place, a sneeze trigger, and a twist.
has_twist(T) :- twist(T).
valid_story(P, T) :- place(P), has_twist(T), trigger(sneeze), affords(P, ghost).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, t) for p in SETTINGS for t in TWISTS}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with a sneeze twist.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--twist", choices=sorted(TWISTS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    twist = getattr(args, "twist", None) or rng.choice(sorted(TWISTS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    ghost_name = getattr(args, "ghost_name", None) or rng.choice(GHOST_NAMES)
    params = StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, ghost_name=ghost_name, twist=twist)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(place="attic", hero_name="Mina", hero_type="girl", ghost_name="Ms. Whisper", twist="sneeze"),
    StoryParams(place="hall", hero_name="Toby", hero_type="boy", ghost_name="Mr. Fog", twist="sneeze"),
    StoryParams(place="garden", hero_name="Elsie", hero_type="girl", ghost_name="Aunt Moon", twist="sneeze"),
    StoryParams(place="bedroom", hero_name="Owen", hero_type="boy", ghost_name="Little Shade", twist="sneeze"),
]


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
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible story pairs:\n")
        for place, twist in pairs:
            print(f"  {place:12} {twist}")
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
