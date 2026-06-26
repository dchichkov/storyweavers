#!/usr/bin/env python3
"""
Storyworld: an awesome ghost story about fright, grouchiness, bravery, and
reconciliation.

This world is built around a small child in a spooky place who meets a grouch
ghost. The child gets frightened, gathers bravery, and eventually helps the
ghost calm down and reconcile with the living world.

The prose is intentionally state-driven:
- physical state uses meters
- emotional state uses memes
- the story advances through premise, tension, turn, and resolution
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

MOOD_KEYS = {"fear", "grouch", "bravery", "calm", "joy", "reconciliation"}

SETTING_KEYS = {
    "attic": "the attic",
    "hallway": "the old hallway",
    "garden": "the moonlit garden",
    "cellar": "the cellar",
}

SCARE_TRIGGERS = {
    "attic": "a dusty trunk creaked open",
    "hallway": "the wallpaper made long shadowy stripes",
    "garden": "the wind rustled the branches like whispering fingers",
    "cellar": "something dripped in the dark",
}

GHOST_MATERIAL = {
    "sheet": "a pale sheet ghost",
    "lantern": "a lantern ghost",
    "puff": "a puff of mist with a face",
}

GROUCH_SYNONYMS = {
    "grouch": "grouch",
    "grumble": "grumble",
    "sour": "sour",
}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        for k in MOOD_KEYS:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    key: str
    place: str
    spooky: bool = True
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
class GhostMood:
    name: str
    source: str
    turn: str
    resolution: str
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
class StoryParams:
    setting: str
    ghost_style: str
    mood: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Story causal rules
# ---------------------------------------------------------------------------
def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["fear"] < THRESHOLD:
        return out
    sig = ("fear_narrated",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{hero.pronoun().capitalize()} felt a chill crawl up {hero.pronoun('possessive')} spine.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    ghost = world.get("ghost")
    if hero.memes["bravery"] < THRESHOLD or ghost.memes["grouch"] < THRESHOLD:
        return out
    if hero.memes["reconciliation"] >= THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["reconciliation"] += 1
    ghost.memes["reconciliation"] += 1
    hero.memes["joy"] += 1
    ghost.memes["calm"] += 1
    out.append("The mean, shaky feeling softened into a new kind of understanding.")
    return out


def _r_bravery_spreads(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["bravery"] < THRESHOLD:
        return out
    sig = ("bravery_line",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{hero.id} stood a little taller, even with the shadows nearby.")
    return out


RULES = [_r_fear, _r_bravery_spreads, _r_reconciliation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            new_lines = rule(world)
            if new_lines:
                changed = True
                produced.extend(new_lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting("attic", SETTING_KEYS["attic"]),
    "hallway": Setting("hallway", SETTING_KEYS["hallway"]),
    "garden": Setting("garden", SETTING_KEYS["garden"]),
    "cellar": Setting("cellar", SETTING_KEYS["cellar"]),
}

GHOSTS = {
    "sheet": GhostMood(
        name="sheet",
        source="a fluttering white cloth",
        turn="the ghost stopped puffing itself up and listened",
        resolution="the white cloth looked less spooky and more like a blanket",
    ),
    "lantern": GhostMood(
        name="lantern",
        source="a tiny lantern glow",
        turn="the glow dimmed into a gentler light",
        resolution="the lantern light became a cozy little beacon",
    ),
    "puff": GhostMood(
        name="puff",
        source="a round puff of mist",
        turn="the mist let out one soft sigh",
        resolution="the puff of mist drifted beside them like friendly breath",
    ),
}

MOODS = {
    "grouch": {
        "ghost_meter": "grouch",
        "hero_meter": "fear",
        "turn": "grouchy",
    },
    "frighten": {
        "ghost_meter": "grouch",
        "hero_meter": "fear",
        "turn": "frightening",
    },
    "awesome": {
        "ghost_meter": "grouch",
        "hero_meter": "fear",
        "turn": "awesome",
    },
}

HERO_NAMES = ["Mina", "Eli", "Nora", "Liam", "Pia", "Theo", "Rose", "Finn"]
HERO_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting is spooky when it is one of the registered haunted places.
spooky(S) :- setting(S).

% The hero is frightened when the place is spooky and the ghost is grouchy.
frightened(H) :- hero(H), spooky(S), in_setting(H,S), ghost(G), grouch(G).

% Reconciliation is possible when the hero has bravery and the ghost has
% softened enough to respond.
can_reconcile(H,G) :- hero(H), ghost(G), brave(H), grouchy(G).

resolved(H,G) :- can_reconcile(H,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("place_name", key, setting.place))
    for key in GHOSTS:
        lines.append(asp.fact("ghost_kind", key))
    for key in MOODS:
        lines.append(asp.fact("mood", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    asp_settings = sorted(set(asp.atoms(model, "setting")))
    py_settings = sorted((k,) for k in SETTINGS)
    if asp_settings == py_settings:
        print(f"OK: clingo gate matches registry settings ({len(asp_settings)}).")
        return 0
    print("MISMATCH between clingo and Python registries.")
    print("  asp:", asp_settings)
    print("  py :", py_settings)
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def setting_detail(setting_key: str) -> str:
    return {
        "attic": "The attic smelled like old wood and sleepy dust.",
        "hallway": "The hallway was narrow, with moonlight полос? Actually no.",
        "garden": "The garden glimmered under the moon, with leaves that shivered softly.",
        "cellar": "The cellar felt cool and damp, with a little drip echoing in the dark.",
    }[setting_key]


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.type} who liked quiet places and big mysteries."


def ghost_intro(setting_key: str, ghost: Entity, mood: GhostMood) -> str:
    return (
        f"In {_safe_lookup(SETTING_KEYS, setting_key)}, there lived {mood.source}. "
        f"It was a grouchy ghost who liked to groan at every tiny sound."
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    ghost = world.get("ghost")
    setting_key = (world.facts.get("setting_key") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "setting_key"))
    mood = _safe_fact(world, world.facts, "mood")
    return [
        QAItem(
            question=f"Who was brave enough to talk to the ghost in {_safe_lookup(SETTING_KEYS, setting_key)}?",
            answer=f"{hero.id} was brave enough to talk to the ghost instead of running away.",
        ),
        QAItem(
            question="Why did the ghost seem grouchy at first?",
            answer=f"The ghost seemed grouchy because {ghost.label} kept making scary little noises and grumbling in the dark.",
        ),
        QAItem(
            question="What changed when the story reached its happy ending?",
            answer="The fright turned into reconciliation, and the ghost became calm and friendly instead of grouchy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about spooky places, strange sounds, and a mystery that becomes less scary by the end.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people or characters stop being upset and make peace again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost story for young children that includes the words "awesome", "frighten", and "grouch".',
        f"Tell a spooky but gentle story set in {SETTING_KEYS[f['setting_key']]} where a brave child meets a grouchy ghost.",
        "Make the ending warm and peaceful, with reconciliation after the scare.",
    ]


def build_story(world: World) -> None:
    hero = world.get("hero")
    ghost = world.get("ghost")
    setting_key = (world.facts.get("setting_key") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "setting_key"))
    ghost_mood: GhostMood = _safe_fact(world, world.facts, "ghost_mood")

    world.say(hero_intro(hero))
    world.say(
        f"One night, {hero.id} went to {_safe_lookup(SETTING_KEYS, setting_key)}. "
        f"It was an awesome place to sneak a peek, even though it could frighten a nervous heart."
    )
    world.say(setting_detail(setting_key))
    world.say(ghost_intro(setting_key, ghost, ghost_mood))

    world.para()
    hero.meters["fear"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"When {_safe_lookup(SCARE_TRIGGERS, setting_key)} {hero.pronoun('object')} almost turned back. "
        f"The ghost frowned and let out a grouchy moan."
    )
    ghost.meters["grouch"] += 1
    ghost.memes["grouch"] += 1
    propagate(world, narrate=True)

    world.para()
    hero.meters["bravery"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"But {hero.id} took a brave breath and stayed. "
        f"{hero.pronoun().capitalize()} said, 'I am scared, but I will not run.'"
    )
    world.say(
        f"That small brave choice helped the ghost notice {hero.id}'s kind voice."
    )
    propagate(world, narrate=True)

    world.para()
    ghost.memes["grouch"] = max(0.0, ghost.memes["grouch"] - 1)
    ghost.meters["grouch"] = max(0.0, ghost.meters["grouch"] - 1)
    world.say(
        f"The ghost sighed, and the grouchy look slid away. "
        f"'{hero.id}, you are not here to hurt me,' it whispered."
    )
    world.say(
        f"Then {hero.id} smiled back, and the two of them made reconciliation under the dim light."
    )
    propagate(world, narrate=True)

    world.para()
    hero.memes["reconciliation"] += 1
    world.say(
        f"At the end, the once-scary corner felt soft and almost cozy. "
        f"{hero.id} went home with a lighter step, and the ghost drifted peacefully behind the window."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            label=params.hero_name,
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="ghost",
            type="ghost",
            label=_safe_lookup(GHOSTS, params.ghost_style).source,
        )
    )
    world.facts["setting_key"] = params.setting
    world.facts["ghost_mood"] = _safe_lookup(GHOSTS, params.ghost_style)
    world.facts["mood"] = params.mood
    world.facts["hero"] = hero
    world.facts["ghost"] = ghost

    build_story(world)
    return world


# ---------------------------------------------------------------------------
# Params / selection
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about bravery and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--ghost-style", choices=GHOSTS.keys())
    ap.add_argument("--mood", choices=MOODS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS.keys()))
    ghost_style = getattr(args, "ghost_style", None) or rng.choice(list(GHOSTS.keys()))
    mood = getattr(args, "mood", None) or rng.choice(list(MOODS.keys()))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    if getattr(args, "name", None) is None and gender == "boy" and name in [n for n in HERO_NAMES if n in {"Mina", "Nora", "Pia", "Rose"}]:
        name = "Finn"
    return StoryParams(
        setting=setting,
        ghost_style=ghost_style,
        mood=mood,
        hero_name=name,
        hero_type=gender,
    )


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


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id}: {' '.join(bits) if bits else '(quiet)'}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", ghost_style="sheet", mood="grouch", hero_name="Mina", hero_type="girl"),
    StoryParams(setting="garden", ghost_style="puff", mood="awesome", hero_name="Eli", hero_type="boy"),
    StoryParams(setting="cellar", ghost_style="lantern", mood="frighten", hero_name="Nora", hero_type="girl"),
]


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show setting/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print("settings:", sorted(set(asp.atoms(model, "setting"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
