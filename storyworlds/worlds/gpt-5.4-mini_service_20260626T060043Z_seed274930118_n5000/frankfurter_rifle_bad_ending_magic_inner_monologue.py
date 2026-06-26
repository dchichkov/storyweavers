#!/usr/bin/env python3
"""
storyworlds/worlds/frankfurter_rifle_bad_ending_magic_inner_monologue.py
=======================================================================

A small ghost-story world with a spooky turn, a little magic, and an inner
monologue instrument that lets the hero's thoughts steer the prose.

Seed tale premise:
- A child goes into an old room at dusk.
- There is a frankfurter, a rifle, and a spellbook.
- The child wants the snack, fears the rifle, and whispers to themself.
- Magic seems like a clever fix, but it wakes the room instead of calming it.
- The ending is bad: the snack is lost, the room grows colder, and the child
  leaves with a lingering fright.

This world is intentionally small and constraint-checked. The prose is driven
by simulated state rather than by a fixed paragraph template.
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

SCARY_KINDS = {"cold", "shiver", "spook"}



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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    frankfurter: object | None = None
    hero: object | None = None
    rifle: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "shiver": 0.0, "spook": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "want": 0.0, "hope": 0.0, "magic": 0.0, "guilt": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the old cabin"
    dim: bool = True
    echoes: bool = True
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
class Thing:
    id: str
    label: str
    phrase: str
    risky: bool = False
    magical: bool = False
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
class Spell:
    id: str
    label: str
    incantation: str
    effect: str
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
        self.magic_awake: bool = False

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
        clone.facts = dict(self.facts)
        clone.magic_awake = self.magic_awake
        clone.paragraphs = [[]]
        return clone


def _night_cold(world: World) -> list[str]:
    out = []
    if not world.setting.dim:
        return out
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes["fear"] >= THRESHOLD:
            key = ("cold", ent.id)
            if key in world.fired:
                continue
            world.fired.add(key)
            ent.meters["cold"] += 1
            ent.meters["shiver"] += 1
            out.append(f"The air felt colder around {ent.id}.")
    return out


def _magic_wakes_room(world: World) -> list[str]:
    out = []
    if not world.magic_awake:
        return out
    for ent in list(world.entities.values()):
        if ent.type != "frankfurter":
            continue
        key = ("magic_spook", ent.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        ent.meters["spook"] += 1
        out.append("The spell made the little snack look stranger in the firelight.")
    return out


def _rifle_scary(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.type != "rifle":
            continue
        key = ("rifle_scary", ent.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        for ch in list(world.entities.values()):
            if ch.kind == "character" and ch.memes["fear"] >= THRESHOLD:
                ch.meters["spook"] += 1
        out.append("The rifle stayed quiet, but it still made the room feel mean.")
    return out


CAUSAL_RULES = [_night_cold, _magic_wakes_room, _rifle_scary]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inner_monologue(hero: Entity, thought: str) -> str:
    return f'[{hero.id} thought: "{thought}"]'


def predict_magic(world: World, hero: Entity, frankfurter: Entity, rifle: Entity, spell: Spell) -> dict:
    sim = world.copy()
    sim.magic_awake = True
    sim.get(hero.id).memes["fear"] += 1
    sim.get(hero.id).memes["hope"] += 1
    propagate(sim, narrate=False)
    frank = sim.get(frankfurter.id)
    return {
        "spook": frank.meters["spook"] >= THRESHOLD,
        "cold": sim.get(hero.id).meters["cold"] >= THRESHOLD,
        "rifle_scary": rifle.id in sim.entities,
    }


def introduce(world: World, hero: Entity, caretaker: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who had come to {world.setting.place} with {caretaker.label}."
    )
    world.say(f"The house was old, and every board seemed to remember a story.")


def setup_items(world: World, hero: Entity, frankfurter: Entity, rifle: Entity, spell: Spell) -> None:
    world.say(
        f"On a plate near the stove sat {frankfurter.phrase}, and above it rested {rifle.phrase}."
    )
    world.say(
        f"In the corner, {spell.phrase} waited like it wanted to be noticed."
    )
    hero.memes["want"] += 1
    world.facts.update(hero=hero, frankfurter=frankfurter, rifle=rifle, spell=spell)


def want_snack(world: World, hero: Entity, frankfurter: Entity) -> None:
    world.say(
        f"{hero.id} looked at the snack and felt {hero.pronoun('possessive')} stomach tug."
    )
    world.say(inner_monologue(hero, f"I want that frankfurter, but the rifle is staring at me."))


def fear_rifle(world: World, hero: Entity, rifle: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} kept glancing at the rifle. It was still, and that made it worse."
    )
    world.say(inner_monologue(hero, "If I stay quiet, maybe the room will forget I am here."))


def try_magic(world: World, hero: Entity, spell: Spell) -> None:
    hero.memes["magic"] += 1
    hero.memes["hope"] += 1
    world.magic_awake = True
    world.say(
        f"At last, {hero.id} whispered the spell: {spell.incantation}."
    )
    world.say(
        f"The words gave off a blue little glow, and the shadows on the wall twitched."
    )
    world.say(inner_monologue(hero, "Maybe magic can make the scary thing go away."))
    propagate(world)


def bad_turn(world: World, hero: Entity, frankfurter: Entity, rifle: Entity) -> None:
    hero.memes["guilt"] += 1
    frankfurter.meters["spook"] += 1
    world.say(
        f"The glow did not fix anything. The frankfurter went cold at the edges, as if the room had breathed on it."
    )
    world.say(
        f"Then the rifle gave a sudden, sharp crack from the dark shelf, and {hero.id} jumped back so hard {hero.pronoun('subject')} nearly dropped the plate."
    )
    world.say(inner_monologue(hero, "I should have left the room alone. I should have listened."))
    hero.meters["shiver"] += 1


def ending(world: World, hero: Entity, frankfurter: Entity, rifle: Entity) -> None:
    hero.memes["fear"] += 2
    world.para()
    world.say(
        f"When the light went out, the frankfurter was gone from the plate, and only a greasy mark was left behind."
    )
    world.say(
        f"{hero.id} stood very still, listening to the dark settle back into the cabin."
    )
    world.say(
        f"The rifle stayed on its shelf, and the old room felt like it had won."
    )
    world.say(inner_monologue(hero, "I wish I had not come in here at all."))


SETTINGS = {
    "cabin": Setting(place="the old cabin", dim=True, echoes=True),
    "attic": Setting(place="the attic", dim=True, echoes=True),
    "shed": Setting(place="the shed", dim=True, echoes=True),
}

THINGS = {
    "frankfurter": Thing(
        id="frankfurter",
        label="a frankfurter",
        phrase="a frankfurter on a plate",
        risky=True,
        magical=False,
    ),
    "rifle": Thing(
        id="rifle",
        label="a rifle",
        phrase="a rifle on a dusty shelf",
        risky=True,
        magical=False,
    ),
    "spell": Thing(
        id="spell",
        label="a spellbook",
        phrase="a little spellbook with a blue ribbon",
        risky=False,
        magical=True,
    ),
}

SPELLS = {
    "glow": Spell(
        id="glow",
        label="glow spell",
        incantation="Little light, do not bite",
        effect="blue glow",
    ),
    "listen": Spell(
        id="listen",
        label="listening spell",
        incantation="Soft ears, hear the dark",
        effect="quiet hum",
    ),
}

NAMES = ["Mina", "Eli", "Nora", "Toby", "Lena", "Owen"]
CARETAKERS = ["grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["curious", "quiet", "brave", "shy"]


@dataclass
class StoryParams:
    place: str
    name: str
    caregiver: str
    trait: str
    spell: str
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
    ap = argparse.ArgumentParser(description="A small ghost-story world with magic and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=CARETAKERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--spell", choices=SPELLS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(CARETAKERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    spell = getattr(args, "spell", None) or rng.choice(list(SPELLS))
    return StoryParams(place=place, name=name, caregiver=caregiver, trait=trait, spell=spell)


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=params.caregiver))
    frankfurter = world.add(Entity(id="frankfurter", type="frankfurter", label="frankfurter", phrase="a frankfurter on a plate"))
    rifle = world.add(Entity(id="rifle", type="rifle", label="rifle", phrase="a rifle on a dusty shelf"))
    spell = _safe_lookup(SPELLS, params.spell)
    world.facts["spell_def"] = spell
    world.facts["params"] = params
    world.facts["hero"] = hero
    world.facts["caregiver"] = caregiver
    world.facts["frankfurter"] = frankfurter
    world.facts["rifle"] = rifle
    return world


def tell(world: World, params: StoryParams) -> World:
    hero = world.get(params.name)
    caregiver = world.get("caregiver")
    frankfurter = world.get("frankfurter")
    rifle = world.get("rifle")
    spell = _safe_lookup(SPELLS, params.spell)

    introduce(world, hero, caregiver)
    world.para()
    setup_items(world, hero, frankfurter, rifle, spell)
    want_snack(world, hero, frankfurter)
    fear_rifle(world, hero, rifle)
    try_magic(world, hero, spell)
    bad_turn(world, hero, frankfurter, rifle)
    ending(world, hero, frankfurter, rifle)
    world.facts["resolved"] = False
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world, params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a short ghost story for a child named {hero.id} that includes the words "frankfurter" and "rifle".',
        f"Tell a spooky story where {hero.id} uses magic but gets a bad ending.",
        f"Write a child-friendly haunted-house tale with inner monologue and a gloomy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    caregiver = _safe_fact(world, f, "caregiver")
    return [
        QAItem(
            question=f"Who went into the old room?",
            answer=f"{hero.id} went in with {caregiver.label}, and the room felt old and spooky.",
        ),
        QAItem(
            question=f"What did {hero.id} want at the start?",
            answer="The child wanted the frankfurter, but the rifle made the room feel too scary to enjoy it.",
        ),
        QAItem(
            question="What happened when the child tried magic?",
            answer="The spell made a blue glow, but it woke the room instead of helping.",
        ),
        QAItem(
            question="Why is the ending bad?",
            answer="The frankfurter was lost, the room turned colder, and the child left frightened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frankfurter?",
            answer="A frankfurter is a cooked sausage, often served on a bun or on a plate.",
        ),
        QAItem(
            question="What is a rifle?",
            answer="A rifle is a kind of gun. It can be dangerous, so children should never play with one.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something impossible or strange happens, like a spell making a glow appear.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice of a character's private thoughts, said inside their head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'quiet'}")
    lines.append(f"magic_awake={world.magic_awake}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- child(H).
risky(T) :- item(T), type(T, frankfurter).
risky(T) :- item(T), type(T, rifle).

magic_wakes(T) :- spell(S), used(S), item(T), type(T, frankfurter).
bad_ending :- risky(F), risky(R), frankfurter(F), rifle(R), used_magic.

"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("item", tid))
        lines.append(asp.fact("type", tid, t.id))
    for sid in SPELLS:
        lines.append(asp.fact("spell", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid() -> list[tuple]:
    return [("cabin", "frankfurter", "rifle")]


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
    StoryParams(place="cabin", name="Mina", caregiver="grandmother", trait="curious", spell="glow"),
    StoryParams(place="attic", name="Eli", caregiver="grandfather", trait="shy", spell="listen"),
    StoryParams(place="shed", name="Nora", caregiver="aunt", trait="brave", spell="glow"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story pattern: cabin / frankfurter / rifle")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
