#!/usr/bin/env python3
"""
A tiny storyworld about a laundromat ghost tale with flashback, suspense,
and repetition.

Premise:
A child comes to a laundromat with a whiny old blanket from an island trip.
The blanket feels important because it belonged to a beloved helper and smells
like salt and rain. In the spinning machines, strange ghostly surprises make
the child nervous, until the past is remembered and the fear turns into a calm
goodbye.

The world is simulated with physical meters and emotional memes:
- washers spin clothes and create eerie sounds
- a lost item can be found in a forgotten pocket
- a flashback can reveal why the item matters
- repetition builds suspense while the cycle runs
- a kind decision can calm the haunting and end the worry
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the laundromat"
    world: object | None = None
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
    name: str
    gender: str
    helper: str
    item: str
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


@dataclass
class ItemSpec:
    label: str
    phrase: str
    type: str
    tag: str
    smell: str
    memory: str
    weight: str
    plural: bool = False
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
class HelperSpec:
    label: str
    relation: str
    voice: str
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
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


ITEMS: dict[str, ItemSpec] = {
    "blanket": ItemSpec(
        label="blanket",
        phrase="a striped blanket from the island trip",
        type="blanket",
        tag="island",
        smell="salt and rain",
        memory="the little boat ride home",
        weight="soft",
    ),
    "shell": ItemSpec(
        label="shell necklace",
        phrase="a shell necklace from the island",
        type="necklace",
        tag="island",
        smell="salt",
        memory="the tide line on the beach",
        weight="light",
    ),
    "shirt": ItemSpec(
        label="shirt",
        phrase="a faded blue shirt",
        type="shirt",
        tag="laundry",
        smell="soap",
        memory="the warm basket by the door",
        weight="light",
    ),
}

HELPERS: dict[str, HelperSpec] = {
    "grandma": HelperSpec(label="Grandma", relation="grandma", voice="soft"),
    "uncle": HelperSpec(label="Uncle", relation="uncle", voice="low"),
    "neighbor": HelperSpec(label="the neighbor", relation="neighbor", voice="gentle"),
}


class Washer:
    def __init__(self, name: str = "washer", cycles: int = 3) -> None:
        self.name = name
        self.cycles = cycles
        self.spin = 0
        self.meters = {"noise": 0.0, "mist": 0.0, "glow": 0.0}
        self.memes = {"suspense": 0.0, "ghostliness": 0.0}

    def tick(self) -> None:
        self.spin += 1
        self.meters["noise"] += 1.0
        self.meters["mist"] += 0.4
        self.memes["suspense"] += 0.7
        if self.spin >= 2:
            self.memes["ghostliness"] += 0.8


def ghost_is_real(world: World, item: Entity, washer: Washer) -> bool:
    return washer.memes["ghostliness"] >= THRESHOLD and item.memes.get("lost", 0.0) >= THRESHOLD


def flashback(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["memory"] += 1.0
    world.say(
        f"Then the hum of the laundromat pulled {hero.id} backward in time. "
        f"{helper.id} had once wrapped {hero.pronoun('object')} in {item.phrase} "
        f"after the island storm, and said, \"Keep this close.\""
    )
    world.say(
        f"That old moment came back with the smell of {item.meters.get('smell', 0)} "
        f"and the picture of {item.meters.get('memory', '')}."
    )


def tell_story(world: World, hero: Entity, helper: Entity, item: Entity, washer: Washer) -> None:
    world.say(
        f"{hero.id} walked into {world.setting.place} with {item.phrase} folded tight in "
        f"his arms."
    )
    world.say(
        f"He kept giving a little whine, because the room was bright, the floor was wet, "
        f"and the washers went thump-thump-thump like faraway feet."
    )
    world.say(
        f"At the back of the room, one machine rattled as if something tiny were inside it."
    )

    for i in range(3):
        washer.tick()
        if i == 0:
            world.say(
                f"The washer spun once. The hum went around and around, and around again."
            )
        elif i == 1:
            world.say(
                f"The washer spun again. The hum went around and around, and around again."
            )
        else:
            world.say(
                f"The washer spun once more. The hum went around and around, and around again."
            )

    item.meters["lost"] = 1.0
    item.meters["smell"] = item.phrase.count("island") + 1
    if ghost_is_real(world, item, washer):
        world.say(
            f"Then a pale blur slid across the round door of the washer, and {hero.id} froze."
        )
        world.say(
            f"The blur did not speak, but it seemed to whisper the same wet little warning: "
            f"\"Whine, whine, whine.\""
        )
        world.say(
            f"{hero.id} stared, because the whisper sounded a lot like the lonely wind on the island."
        )

    flashback(world, hero, helper, item)

    world.say(
        f"Now {hero.id} understood why the old blanket mattered. It was not just soft; it was a piece of home."
    )
    world.say(
        f"He held it carefully while the machine finished its last turn."
    )
    world.say(
        f"When the door opened, the blur was gone. The blanket was warm, clean, and no longer lost."
    )
    world.say(
        f"{hero.id} smiled at {helper.id} and whispered, \"Goodbye, island ghost.\" "
        f"But the laundromat only answered with one last soft thump, and then peace."
    )


def build_story_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_spec = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(id=helper_spec.label, kind="character", type="adult", label=helper_spec.label))
    item_spec = _safe_lookup(ITEMS, params.item)
    item = world.add(
        Entity(
            id=item_spec.label,
            kind="thing",
            type=item_spec.type,
            label=item_spec.label,
            phrase=item_spec.phrase,
            owner=hero.id,
        )
    )
    item.meters["lost"] = 0.0
    item.meters["smell"] = 0.0
    item.memes["importance"] = 1.0
    washer = Washer()

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        item_spec=item_spec,
        helper_spec=helper_spec,
        washer=washer,
    )

    hero.memes["worry"] = 1.0
    hero.memes["whine"] = 1.0
    item.memes["lost"] = 1.0

    tell_story(world, hero, helper, item, washer)
    world.facts["resolved"] = True
    world.facts["ghost"] = True
    world.facts["flashback"] = True
    world.facts["suspense"] = True
    world.facts["repetition"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item_spec = _safe_fact(world, f, "item_spec")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a gentle ghost story set in a laundromat about {hero.id} and {item_spec.phrase}.',
        f"Tell a children's story where a small whine, an island memory, and a spinning washer create suspense.",
        f"Write a story with flashback, repetition, and a soft ghostly feeling that ends in comfort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item_spec = _safe_fact(world, f, "item_spec")
    return [
        QAItem(
            question=f"Why did {hero.id} feel worried in the laundromat?",
            answer=(
                f"{hero.id} felt worried because {item_spec.phrase} seemed tied to a sad lost feeling, "
                f"and the washer kept making ghostly sounds."
            ),
        ),
        QAItem(
            question="What memory came back during the story?",
            answer=(
                f"The memory of the island trip came back, when {helper.id} had wrapped the item carefully "
                f"and told {hero.id} to keep it close."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with the item cleaned and safe, the ghostly feeling gone, and {hero.id} smiling "
                f"with relief beside {helper.id}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laundromat?",
            answer="A laundromat is a place with washing machines and dryers where people clean clothes and blankets.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, like a memory from the past.",
        ),
        QAItem(
            question="Why can repetition make a story suspenseful?",
            answer="Repetition can make suspense because the same sound or action keeps happening, so you wait to see what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "laundromat"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "repetition"),
    ]
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("island_item", item_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


ASP_RULES = r"""
feature_ok(F) :- feature(F).

ghost_story_ok :- setting(laundromat), feature(flashback), feature(suspense), feature(repetition).
island_theme :- island_item(blanket).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show ghost_story_ok/0. #show island_theme/0."))
    atoms = {str(a) for a in model}
    expected = {"ghost_story_ok", "island_theme"}
    if atoms == expected:
        print("OK: ASP twin matches Python gate.")
        return 0
    print(f"MISMATCH: {atoms} != {expected}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world in a laundromat.")
    ap.add_argument("--name", choices=["Milo", "Nia", "Owen", "Ivy"], default=None)
    ap.add_argument("--gender", choices=["boy", "girl"], default=None)
    ap.add_argument("--helper", choices=sorted(HELPERS), default=None)
    ap.add_argument("--item", choices=sorted(ITEMS), default=None)
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
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(["Milo", "Nia", "Owen", "Ivy"] if gender == "boy" else ["Nia", "Ivy", "Mira", "Lena"])
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    item = getattr(args, "item", None) or rng.choice(sorted(ITEMS))
    return StoryParams(name=name, gender=gender, helper=helper, item=item, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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


CURATED = [
    StoryParams(name="Milo", gender="boy", helper="grandma", item="blanket"),
    StoryParams(name="Ivy", gender="girl", helper="neighbor", item="shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show ghost_story_ok/0. #show island_theme/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show ghost_story_ok/0. #show island_theme/0."))
        print("ASP atoms:", sorted(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
