#!/usr/bin/env python3
"""
storyworlds/worlds/attic_happy_ending_sound_effects_folk_tale.py
===============================================================

A small, self-contained folk-tale storyworld set in an attic.

Premise:
A child hears strange sound effects in the attic and climbs up to see what is
making the rattle, tap, creak, and thump.

Turn:
The child fears the attic is haunted, but the sounds come from a small helper
creature and a loose treasure that has been trapped in old boxes.

Resolution:
The child and the helper sort the attic together, the scary noise becomes a
friendly rhythm, and everyone ends with warmth, laughter, and a happy ending.

The world is intentionally narrow: it generates a few tightly reasoned variants
rather than a large but flimsy set of outcomes.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    contains: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    dusty: bool = False
    hidden: bool = False
    old: bool = False
    helper: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the attic"
    smells: str = "dust and cedar"
    affordance: str = "listening"
    mood: str = "dim"
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
class SoundThing:
    id: str
    label: str
    sound: str
    cause: str
    risk: str
    friendly: bool = False
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    owner: str
    old: bool = False
    dusty: bool = False
    hidden: bool = True
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _noise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.entities.get("helper")
    treasure = world.entities.get("treasure")
    if child.memes.get("fear", 0.0) >= THRESHOLD and not world.facts.get("calmed"):
        if helper and helper.meters.get("alive", 1.0) >= 0:
            sig = ("fear",)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("The attic gave a long creak, and the child’s heart gave a little jump.")
    if helper and helper.meters.get("drum", 0.0) >= THRESHOLD:
        sig = ("drum",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("Tap-tap, thump-thump—the tiny rhythm sounded brave instead of strange.")
    if treasure and treasure.hidden is False and not world.facts.get("found"):
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("Under the boxes, a lost ribbon and a silver bell were waiting to be found.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _noise(world):
            changed = True
            if s:
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"The {setting.place.removeprefix('the ')} smelled of {setting.smells}, and old beams stood like watchful tree trunks."


def intro_child(world: World, hero: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.traits[0]} {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved quiet corners, warm bread, and the stories that lived inside old houses."
    )


def hear_sound(world: World, hero: Entity, sound: SoundThing) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"One evening, when the floor below was still, {hero.id} heard {sound.sound} from the attic above."
    )
    world.say(f"{sound.sound.capitalize()}! The sound went, like a pebble rolling inside a wooden chest.")
    world.say(setting_detail(world.setting))


def climb_up(world: World, hero: Entity) -> None:
    hero.meters["stairs"] = hero.meters.get("stairs", 0.0) + 1
    world.say(f"{hero.id} took a candle and climbed the narrow stairs to the attic door.")


def worry(world: World, hero: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"The child whispered, 'What if a grumpy spirit is rattling the rafters?'")


def discover_helper(world: World, hero: Entity, helper: Entity, sound: SoundThing, treasure: Treasure) -> None:
    world.facts["found"] = True
    helper.meters["alive"] = 1.0
    helper.memes["kind"] = helper.memes.get("kind", 0.0) + 1
    world.say(
        f"Then a little {helper.type} peeked from behind a trunk, holding a bent spoon like a drumstick."
    )
    world.say(
        f'"I am not a ghost," said {helper.id}. "I was trying to make {sound.sound} so the boxes would shake loose."'
    )
    if treasure.hidden:
        treasure.hidden = False
    world.say(
        f"Inside the trunk, the child saw {treasure.phrase}, tucked under a blanket of dust."
    )


def solve_problem(world: World, hero: Entity, helper: Entity, sound: SoundThing, treasure: Treasure) -> None:
    helper.meters["drum"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.facts["calmed"] = True
    world.say(
        f"{hero.id} laughed, because the attic noise was only a helper making brave little sounds."
    )
    world.say(
        f"Together they lifted the lid, swept away the dust, and tied {treasure.phrase} with a fresh ribbon."
    )
    world.say(
        f"Tap-tap, thunk-thunk, went the spoon on the trunk, and the attic echoed like a friendly song."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"At last {hero.id} carried the found treasure downstairs, and {helper.id} came too, smiling in the candle glow."
    )
    world.say(
        f"That night the old house felt smaller and kinder, and the attic was no longer a place of fear but a place of secrets found."
    )
    world.say(
        f"{hero.id} kept the bell by the bed, and whenever it jingled, {hero.id} remembered that some scary sounds are only stories asking to be heard."
    )


def tell(hero_name: str = "Mara", hero_type: str = "girl", helper_type: str = "mouse",
         sound_id: str = "rattle") -> World:
    world = World(Setting())
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["curious", "little"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        traits=["tiny", "kind"],
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="bell",
        label="bell",
        phrase="a silver bell and a faded ribbon",
        owner=hero.id,
        old=True,
        dusty=True,
        hidden=True,
    ))
    sound = _safe_lookup(SOUND_THINGS, sound_id)

    intro_child(world, hero)
    world.para()
    hear_sound(world, hero, sound)
    climb_up(world, hero)
    worry(world, hero)
    world.para()
    discover_helper(world, hero, helper, sound, treasure)
    propagate(world)
    solve_problem(world, hero, helper, sound, treasure)
    world.para()
    happy_ending(world, hero, helper, treasure)

    world.facts.update(hero=hero, helper=helper, treasure=treasure, sound=sound)
    return world


SOUND_THINGS = {
    "rattle": SoundThing(
        id="rattle",
        label="rattle",
        sound="rattle-rattle",
        cause="a spoon tapping a trunk latch",
        risk="it sounds like a ghost",
        friendly=False,
    ),
    "creak": SoundThing(
        id="creak",
        label="creak",
        sound="creak-creak",
        cause="a loose board and a swinging lantern",
        risk="it sounds like a tired giant",
        friendly=False,
    ),
    "thump": SoundThing(
        id="thump",
        label="thump",
        sound="thump-thump",
        cause="a ball rolling behind a blanket chest",
        risk="it sounds like a hidden footstep",
        friendly=False,
    ),
}

NAMES = ["Mara", "Lina", "Pip", "Hugo", "Nell", "Anya", "Bram", "Tessa"]
TRAITS = ["curious", "brave", "gentle", "clever", "patient"]


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    sound: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("attic", sid, helper) for sid in SOUND_THINGS for helper in ["mouse", "bird", "cat"]]


ASP_RULES = r"""
sound(attack) :- false.
setting(attic).
sound_type(rattle). sound_type(creak). sound_type(thump).
helper(mouse). helper(bird). helper(cat).

compatible(attic, S, H) :- sound_type(S), helper(H).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "attic")]
    for sid in SOUND_THINGS:
        lines.append(asp.fact("sound_type", sid))
    for h in ["mouse", "bird", "cat"]:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale attic storyworld with sound effects and a happy ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sound", choices=list(SOUND_THINGS))
    ap.add_argument("--helper", choices=["mouse", "bird", "cat"])
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
    sound = getattr(args, "sound", None) or rng.choice(list(SOUND_THINGS))
    helper = getattr(args, "helper", None) or rng.choice(["mouse", "bird", "cat"])
    if getattr(args, "gender", None) == "boy" and getattr(args, "name", None) is None:
        pool = ["Hugo", "Bram", "Pip"]
    elif getattr(args, "gender", None) == "girl" and getattr(args, "name", None) is None:
        pool = ["Mara", "Lina", "Nell", "Anya", "Tessa"]
    else:
        pool = NAMES
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(pool),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        helper=helper,
        sound=sound,
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale set in an attic with gentle sound effects and a happy ending.',
        f"Tell a child-friendly story about {f['hero'].id} hearing {f['sound'].sound} in the attic and discovering the cause.",
        "Write a simple story where a scary attic sound turns out to be friendly and helpful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    sound: SoundThing = _safe_fact(world, f, "sound")
    treasure: Treasure = _safe_fact(world, f, "treasure")
    return [
        QAItem(
            question=f"What did {hero.id} hear in the attic?",
            answer=f"{hero.id} heard {sound.sound} from the attic above.",
        ),
        QAItem(
            question=f"Who was making the attic noise?",
            answer=f"The sound came from {helper.id}, a tiny {helper.type} who was trying to shake loose the old trunk.",
        ),
        QAItem(
            question=f"What was found after the sound was explained?",
            answer=f"They found {treasure.phrase}, which had been hiding under the dust in the attic trunk.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the attic?",
            answer=f"{hero.id} ended the night happy, because the scary noise became a friendly rhythm and the attic felt kind again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an attic?",
            answer="An attic is the space under the roof of a house, often used for storing old things.",
        ),
        QAItem(
            question="Why do old houses sometimes make creaking sounds?",
            answer="Old houses can creak when wood boards move a little, especially when the temperature changes or someone walks nearby.",
        ),
        QAItem(
            question="Why can a sound seem scary before you know what made it?",
            answer="A sound can seem scary when you cannot see the cause, but it often turns ordinary once you understand it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.contains:
            bits.append(f"contains={e.contains}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.helper, params.sound)
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
    StoryParams(name="Mara", gender="girl", helper="mouse", sound="rattle", trait="curious"),
    StoryParams(name="Hugo", gender="boy", helper="cat", sound="creak", trait="brave"),
    StoryParams(name="Nell", gender="girl", helper="bird", sound="thump", trait="gentle"),
]


def explain_asp() -> str:
    return asp_program("#show compatible/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(explain_asp())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible attic combos:\n")
        for place, sound, helper in triples:
            print(f"  {place:6} {sound:8} {helper}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
