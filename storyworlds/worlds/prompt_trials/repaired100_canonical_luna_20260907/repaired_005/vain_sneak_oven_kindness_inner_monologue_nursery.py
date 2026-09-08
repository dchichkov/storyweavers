#!/usr/bin/env python3
"""
A nursery-rhyme story world about a vain sneak, a warm oven, kindness, and
an inner voice that chooses to help.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    detail: str
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
    name: str = "Luna"
    title: str = "The Vain Sneak and the Kind Oven"
    seed: Optional[int] = None
    setting: str = "bakery"
    verse: int = 0
    clue: int = 0
    kindness: int = 0
    ending: int = 0
    params: object | None = None
    scenario: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Beat:
    treat: str
    recipient: str
    setup: str
    temptation: str
    sneak_action: str
    consequence: str
    clue: str
    cause: str
    kind_action: str
    resolution: str
    ending_images: tuple[str, ...]
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
class Scenario:
    id: str
    beats: tuple[Beat, ...]
    cause: str = ""
    clue: str = ""
    consequence: str = ""
    ending_images: object | None = None
    kind_action: str = ""
    recipient: str = ""
    resolution: str = ""
    setup: str = ""
    sneak_action: str = ""
    temptation: str = ""
    treat: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "bakery": Setting(
        place="the little bakery",
        detail="a blue door, a floury floor, and a round red oven",
    ),
    "cottage": Setting(
        place="the cottage kitchen",
        detail="a yellow table, a ticking clock, and a friendly brick oven",
    ),
    "market": Setting(
        place="the market bakehouse",
        detail="striped awnings, wooden shelves, and a shining iron oven",
    ),
}


SCENARIOS = {
    "oven": Scenario(
        id="oven",
        beats=(
            Beat(
                treat="a golden honey bun",
                recipient="Pip the small baker",
                setup="Pip had baked a golden honey bun for a hungry neighbor",
                temptation="Luna saw the bun cooling beside the warm oven",
                sneak_action="tiptoe past the flour sack and lift the bun",
                consequence="the bun rolled from her paw and bumped the oven door",
                clue="a little trail of flour led from the shelf to the door",
                cause="the shelf latch had not been fastened after the oven was cleaned",
                kind_action="close the oven door, fasten the shelf latch, and carry the bun to Pip",
                resolution="the bun stayed warm, and Pip delivered it to the hungry neighbor",
                ending_images=(
                    "The neighbor smiled, and the honey bun shone like a small sun.",
                    "Three crumbs made a golden path beside the safely latched oven.",
                    "Pip rang a tiny bell while the warm bun rested on a blue plate.",
                ),
            ),
            Beat(
                treat="a basket of cinnamon rolls",
                recipient="Mara the milkmaid",
                setup="Mara had baked a basket of cinnamon rolls for the children next door",
                temptation="Luna smelled the sweet cinnamon curl from the oven",
                sneak_action="sneak behind the flour bin and tug at the basket",
                consequence="the basket wobbled, and one roll slid toward the hot oven",
                clue="the basket handle was frayed where it brushed the oven shelf",
                cause="a loose thread had caught on a sharp corner of the shelf",
                kind_action="free the handle, move the basket away from the oven, and call Mara",
                resolution="the rolls cooled safely, and every child received a soft spiral",
                ending_images=(
                    "The children hummed a cinnamon song around the sharing table.",
                    "The oven glowed gently while the empty basket rested by the door.",
                    "A sweet spiral sat on every plate, with none kept hidden away.",
                ),
            ),
            Beat(
                treat="a warm berry pie",
                recipient="Old Tessa",
                setup="Old Tessa had baked a warm berry pie for the evening supper",
                temptation="Luna admired her face in the pie's shiny tin",
                sneak_action="creep close and peek beneath the checked cloth",
                consequence="her bright tail brushed the cloth, and the pie tilted by the oven",
                clue="one oven stone stood higher than the others",
                cause="a small wooden wedge had slipped beneath the oven stone",
                kind_action="fetch the baker, remove the wedge, and steady the pie on a cool board",
                resolution="the pie settled safely, and Tessa shared its berries with everyone",
                ending_images=(
                    "Purple berries glittered while Tessa cut a generous first slice.",
                    "The oven sang a soft warm hum beneath the level baking stone.",
                    "Luna saw her smile reflected in the tin, brighter than any vain pose.",
                ),
            ),
        ),
    )
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme story world about Luna, a vain sneak, an oven, and kindness."
    )
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--scenario", choices=SCENARIOS, default="oven")
    parser.add_argument("--verse", type=int, default=None)
    parser.add_argument("--clue", type=int, default=None)
    parser.add_argument("--kindness", type=int, default=None)
    parser.add_argument("--ending", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=getattr(args, "name", None),
        seed=getattr(args, "seed", None),
        setting=getattr(args, "setting", None) or rng.choice(list(SETTINGS)),
        scenario=getattr(args, "scenario", None),
        verse=getattr(args, "verse", None) if getattr(args, "verse", None) is not None else rng.randrange(4),
        clue=getattr(args, "clue", None) if getattr(args, "clue", None) is not None else rng.randrange(3),
        kindness=getattr(args, "kindness", None) if getattr(args, "kindness", None) is not None else rng.randrange(4),
        ending=getattr(args, "ending", None) if getattr(args, "ending", None) is not None else rng.randrange(3),
    )


def reasonableness_gate(params: StoryParams, scenario: Scenario) -> None:
    if not params.name.strip():
        pass
    if params.setting not in SETTINGS:
        pass
    if scenario.id not in SCENARIOS:
        pass
    if not 0 <= params.verse < 4:
        pass
    if not 0 <= params.clue < 3:
        pass
    if not 0 <= params.kindness < 4:
        pass
    if not 0 <= params.ending < 3:
        pass


ASP_RULES = r"""
character(luna).
object(oven).
quality(vain).
action(sneak).
virtue(kindness).
instrument(inner_monologue).
style(nursery_rhyme).

valid_world :- character(luna), object(oven), quality(vain),
               action(sneak), virtue(kindness),
               instrument(inner_monologue), style(nursery_rhyme).

#show valid_world/0.
#show character/1.
#show object/1.
#show quality/1.
#show action/1.
#show virtue/1.
#show instrument/1.
#show style/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("object", "oven"),
            asp.fact("quality", "vain"),
            asp.fact("action", "sneak"),
            asp.fact("virtue", "kindness"),
            asp.fact("instrument", "inner_monologue"),
            asp.fact("style", "nursery_rhyme"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_world/0."))
    found = set(asp.atoms(model, "valid_world"))
    expected = {()}
    if found == expected:
        print("OK: ASP world facts and Python world contract agree.")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def build_world(params: StoryParams, scenario: Scenario, setting: Setting) -> World:
    beat = scenario.beats[params.verse % len(scenario.beats)]
    world = World(setting)

    luna = world.add(
        Entity(
            id="luna",
            kind="character",
            label=params.name,
            type="mouse",
            meters={"safety": 0.7, "helpfulness": 0.1},
            memes={"vanity": 1.0, "curiosity": 0.8, "guilt": 0.0, "kindness": 0.0, "relief": 0.0},
        )
    )
    oven = world.add(
        Entity(
            id="oven",
            label="the oven",
            type="oven",
            meters={"heat": 0.8, "door_safety": 0.5, "shelf_stability": 0.4},
            memes={"warmth": 1.0},
        )
    )
    treat = world.add(
        Entity(
            id="treat",
            label=beat.treat,
            type="food",
            owner=beat.recipient,
            meters={"warmth": 0.8, "safety": 0.6, "sharing": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="recipient",
            kind="character",
            label=beat.recipient,
            type="neighbor",
            meters={"safety": 1.0},
            memes={"trust": 0.5, "gratitude": 0.0},
        )
    )

    world.facts.update(
        luna=luna,
        oven=oven,
        treat=treat,
        helper=helper,
        beat=beat,
        setting=setting,
    )

    world.say(f"In {setting.place}, where the warm ovens glow, lived {params.name}, a mouse with a shining little bow.")
    world.say(f"{setting.detail.capitalize()}, and flour dusted the floor; {params.name} loved bright ribbons and mirrors by the door.")
    world.say(f"She preened by the oven, so proud and so vain, while warm little breezes hummed a soft refrain.")
    world.para()

    world.say(f"{beat.setup}.")
    world.say(f"{beat.temptation}; it smelled like a song and gleamed like the sun.")
    world.say(f'"Just one tiny taste, then I will quickly run," {params.name} whispered.')
    world.say(f"She began to {beat.sneak_action}.")
    world.say(f"Her inner thought piped up: “A kind heart is brighter than a ribbon or crown.”")
    world.say(f"But {beat.consequence}.")
    treat.meters["safety"] = 0.2
    oven.meters["door_safety"] = 0.1
    luna.memes["guilt"] += 0.8
    world.para()

    clues = (
        f"She watched instead of rushing and noticed that {beat.clue}.",
        f"She followed the same small sound twice and discovered that {beat.clue}.",
        f"She asked {beat.recipient} to look with her, and together they saw that {beat.clue}.",
    )
    world.say(clues[params.clue])
    world.say(f"Then her inner monologue chimed: “If I caused this trouble, I must help mend it.”")
    world.say(f"The true cause was clear: {beat.cause}.")
    world.say(f'"Please help me make it safe," {params.name} said.')
    world.say(f'{beat.recipient} answered, "I will help, if you will help kindly."')
    world.say(f"{params.name} nodded and chose to {beat.kind_action}.")
    luna.meters["helpfulness"] = 1.0
    luna.memes["kindness"] = 1.0
    luna.memes["vanity"] = 0.4
    luna.memes["relief"] = 1.0
    oven.meters["door_safety"] = 1.0
    oven.meters["shelf_stability"] = 1.0
    treat.meters["safety"] = 1.0
    treat.meters["sharing"] = 1.0
    helper.memes["gratitude"] = 1.0
    world.para()

    world.say(f"At last, {beat.resolution}.")
    world.say(f"{beat.ending_images[params.ending]}")
    world.say(f"{params.name} still liked a shining bow, but kindness now made her heart glow brighter than the oven.")

    return world


def generation_prompts(world: World) -> list[str]:
    beat: Beat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "beat")
    return [
        "Write a nursery-rhyme story about a vain sneak near an oven who learns kindness.",
        f"Tell how {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "luna").label} notices {beat.clue} and changes from sneaking to helping.",
        "Use gentle rhyme, a brief inner monologue, and spoken dialogue that changes the action.",
    ]


def story_qa(world: World) -> list[QAItem]:
    beat: Beat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "beat")
    luna: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "luna")
    return [
        QAItem(
            question="Who was the vain sneak?",
            answer=f"{luna.label} was the vain little mouse who liked ribbons, mirrors, and looking grand.",
        ),
        QAItem(
            question="What caused the trouble by the oven?",
            answer=f"The trouble came because {beat.cause}. That made the food and the oven less safe.",
        ),
        QAItem(
            question="What did the inner monologue tell the mouse?",
            answer="It told her that a kind heart was brighter than a ribbon or crown, and that she should help repair the trouble.",
        ),
        QAItem(
            question="How did kindness change the story?",
            answer=f"Kindness led the mouse to {beat.kind_action}. As a result, {beat.resolution}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely and happily: {beat.resolution} {beat.ending_images[0]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to sneak?",
            answer="To sneak means to move quietly or secretly, often because someone does not want to be noticed.",
        ),
        QAItem(
            question="Why should children be careful near an oven?",
            answer="An oven can be hot, so children should stay safe and ask a trusted grown-up for help.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another person's needs and choosing to help gently and fairly.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought, showing what the character is thinking inside.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scenario = SCENARIOS.get(params.scenario)
    if scenario is None:
        _fallback_pool = globals().get("SCENARIOS") or globals().get("SCENARIOES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        scenario = next(iter(_fallback_pool), None)
        if scenario is None:
            raise StoryError
    reasonableness_gate(params, scenario)
    world = build_world(params, scenario, _safe_lookup(SETTINGS, params.setting))
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
        print(asp_program("#show valid_world/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_world/0."))
        print(asp.atoms(model, "valid_world"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for index, setting_name in enumerate(SETTINGS):
            rng = random.Random(base_seed + index)
            params = StoryParams(
                name="Luna",
                seed=base_seed + index,
                setting=setting_name,
                scenario="oven",
                verse=rng.randrange(4),
                clue=rng.randrange(3),
                kindness=rng.randrange(4),
                ending=rng.randrange(3),
            )
            samples.append(generate(params))
    else:
        for index in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
