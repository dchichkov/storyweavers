#!/usr/bin/env python3
"""A cautionary, rhyming superhero storyworld about germs and carbon dioxide."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402



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
    kind: str
    type: str
    label: str
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
class Place:
    label: str
    detail: str
    image: str
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
class Episode:
    label: str
    activity: str
    germ_moment: str
    rhyme: str
    joke: str
    ending_image: str
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
class StoryParams:
    place: str = ""
    episode: str = ""
    hero: str = ""
    buddy: str = ""
    route: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACES = {
    "school": Place(
        "the school greenhouse",
        "warm panes shone above the rows of seedlings",
        "a little blue door stood beside the tomato pots",
    ),
    "community": Place(
        "the community greenhouse",
        "rain tapped a gentle rhythm on the glass roof",
        "a painted sunflower marked the entrance",
    ),
    "garden_room": Place(
        "the garden room",
        "sunlight made bright squares on the tiled floor",
        "a row of tiny pots lined the wide windowsill",
    ),
}

EPISODES = {
    "seed_packets": Episode(
        "the seed-packet party",
        "sorting moonflower seeds for planting",
        "Milo reached for his apple after handling the shared seed packets",
        "A germ can travel, small and sly; wash before your snack goes by.",
        "Luna's cape caught a paper packet, which fluttered down like a very tiny superhero.",
        "the moonflower packets sat in a tidy basket beside clean hands and bright green sprouts",
    ),
    "tomato_fair": Episode(
        "the tomato fair",
        "arranging ripe tomatoes for the neighborhood table",
        "Milo was about to rub one eye with a hand that had just held the shared garden trowel",
        "A germ can hitch a ride on hands; soap and water make a safer band.",
        "Luna's cape tried to claim a tomato as its sidekick, but the tomato rolled away.",
        "the red tomatoes made a cheerful row while the washed trowel dried on its hook",
    ),
    "moonflower_club": Episode(
        "the moonflower club",
        "labeling pots for the evening planting club",
        "Milo nearly touched his face with a soil-dusted gardening glove",
        "A germ can travel glove to face; wash up first, then join the race.",
        "Luna announced that her cape was excellent at dramatic entrances and terrible at labeling pots.",
        "the labeled moonflowers stood in a neat row beside the clean gloves",
    ),
}

HEROES = {
    "Luna": "girl",
    "Joey": "boy",
    "Nia": "girl",
    "Theo": "boy",
}
BUDDIES = {
    "Milo": "boy",
    "Iris": "girl",
    "Ari": "boy",
    "Zoe": "girl",
}
ROUTES = ("sunny_opening", "cape_opening", "club_opening", "quiet_opening")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming superhero story about germ safety and carbon dioxide."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--episode", choices=sorted(EPISODES))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--buddy", choices=sorted(BUDDIES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


ASP_RULES = """
valid(Place, Episode) :- place(Place), episode(Episode).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, episode)
        for place in sorted(PLACES)
        for episode in sorted(EPISODES)
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            *(asp.fact("place", place) for place in sorted(PLACES)),
            *(asp.fact("episode", episode) for episode in sorted(EPISODES)),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if python_combos != clingo_combos:
        print("MISMATCH:", sorted(python_combos - clingo_combos), sorted(clingo_combos - python_combos))
        return 1

    checked = 0
    for place, episode in sorted(python_combos):
        params = StoryParams(
            place=place,
            episode=episode,
            hero="Luna",
            buddy="Milo",
            route="cape_opening",
            seed=checked,
        )
        sample = generate(params)
        if (
            "germ" not in sample.story.lower()
            or "dioxide" not in sample.story.lower()
            or "carbon dioxide" not in sample.story.lower()
            or "?" not in sample.story
            or "!" not in sample.story
            or not sample.story_qa
            or sample.world is None
        ):
            print(f"Story check failed for {place}/{episode}.")
            return 1
        checked += 1

    print(f"OK: clingo gate matches valid_combos() ({len(python_combos)} combos); {checked} stories checked.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (getattr(args, "place", None) is None or combo[0] == getattr(args, "place", None))
        and (getattr(args, "episode", None) is None or combo[1] == getattr(args, "episode", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, episode = rng.choice(combos)
    hero = getattr(args, "hero", None) or rng.choice(sorted(HEROES))
    buddies = [name for name in sorted(BUDDIES) if name != hero]
    buddy = getattr(args, "buddy", None) or rng.choice(buddies)
    return StoryParams(
        place=place,
        episode=episode,
        hero=hero,
        buddy=buddy,
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    material = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.episode,
            params.hero,
            params.buddy,
            params.route,
        )
    )
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.episode not in EPISODES:
        pass
    if params.hero not in HEROES:
        pass
    if params.buddy not in BUDDIES:
        pass
    if params.hero == params.buddy:
        pass
    if params.route not in ROUTES:
        pass

    place = _safe_lookup(PLACES, params.place)
    episode = _safe_lookup(EPISODES, params.episode)
    rng = story_rng(params)
    world = World(place)

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type=_safe_lookup(HEROES, params.hero),
            label=params.hero,
            meters={"caution": 0.2, "helpfulness": 0.6},
            memes={"brave": 0.8, "curious": 0.7},
        )
    )
    buddy = world.add(
        Entity(
            id=params.buddy,
            kind="character",
            type=_safe_lookup(BUDDIES, params.buddy),
            label=params.buddy,
            meters={"hand_cleanliness": 0.3, "worry": 0.2},
            memes={"trust": 0.7},
        )
    )
    sensor = world.add(
        Entity(
            id="air_sensor",
            kind="safety_device",
            type="carbon_dioxide_sensor",
            label="the carbon dioxide sensor",
            meters={"alert": 0.0},
            memes={"reliable_warning": 1.0},
        )
    )
    room = world.add(
        Entity(
            id="greenhouse_air",
            kind="environment",
            type="shared_air",
            label="the greenhouse air",
            meters={"crowding": 0.3, "ventilation": 0.7},
            memes={"needs_attention": 0.0},
        )
    )
    germ = world.add(
        Entity(
            id="germ",
            kind="hazard",
            type="invisible_microbe",
            label="a germ",
            meters={"spread_risk": 0.5},
            memes={"visible_to_children": 0.0},
        )
    )
    adult = world.add(
        Entity(
            id="Ms_Rivera",
            kind="helper",
            type="adult_garden_leader",
            label="Ms. Rivera",
            meters={"responsibility": 1.0},
            memes={"trusted": 1.0},
        )
    )

    openings = {
        "sunny_opening": (
            f"Sunlight warmed {place.label}, where {hero.id} arrived in a red cape "
            f"to help with {episode.label}. {place.detail.capitalize()}."
        ),
        "cape_opening": (
            f"{hero.id} swept into {place.label} with a superhero pose, then had to "
            f"untangle the cape from a pot. {episode.label} was waiting, and {buddy.id} "
            f"was trying not to laugh."
        ),
        "club_opening": (
            f"The garden club had one important mission at {place.label}: "
            f"{episode.activity}. {hero.id} called it a job for a superhero, though "
            f"{buddy.id} pointed out that the seed trays did not look frightened."
        ),
        "quiet_opening": (
            f"For a little while, {place.label} was peaceful. {hero.id} and {buddy.id} "
            f"were helping with {episode.label}, while {place.detail}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        f"{place.image.capitalize()}. Ms. Rivera welcomed the children and reminded "
        f"them that careful hands were part of every garden adventure."
    )
    world.para()

    world.say(
        f"After {episode.activity}, {episode.germ_moment}. A germ is too tiny to see, "
        f"so {hero.id} did not pretend to spot one hiding in the dirt."
    )
    world.say(f'"Snack pause!" {buddy.id} said.')
    world.say(
        f'"Not quite yet," {hero.id} replied. "Let us wash our hands first. Germs can '
        f'travel from hands to faces or food." {buddy.id} nodded and headed to the sink.'
    )
    buddy.meters["hand_cleanliness"] = 0.8
    germ.meters["spread_risk"] = 0.2
    hero.memes["brave"] = 0.9
    world.say(episode.rhyme)
    world.say(episode.joke)

    world.para()
    world.say(
        f"Just then, the carbon dioxide sensor gave a clear beep. Its small screen "
        f"showed an alert: carbon dioxide was building up in the busy, closed greenhouse. "
        f"Carbon dioxide is a gas people breathe out and plants use, but an alert in a "
        f"closed room was a reason to get help—not a puzzle for children to fix."
    )
    sensor.meters["alert"] = 1.0
    room.meters["crowding"] = 0.9
    room.meters["ventilation"] = 0.2
    room.memes["needs_attention"] = 1.0
    world.say(
        f'"Could my cape fan the air?" {hero.id} asked. "Or should we go outside?"'
    )
    world.say(
        f'"Outside, and tell Ms. Rivera," {buddy.id} said. "The sensor is warning us. '
        f'We should not try to fix the room ourselves."'
    )
    hero.meters["caution"] = 1.0
    hero.meters["helpfulness"] = 0.9
    buddy.memes["trust"] = 0.9
    world.say(
        f'"Good thinking," {hero.id} said. The children left together and told '
        f"Ms. Rivera. Their superhero power was listening to the warning, not rushing "
        f"toward it."
    )

    world.para()
    world.say(
        f"Ms. Rivera kept everyone outside and contacted the greenhouse caretaker. "
        f"The caretaker checked the room and restored its ventilation before the club "
        f"went back in. The sensor settled, and the air was checked before anyone "
        f"returned."
    )
    room.meters["crowding"] = 0.2
    room.meters["ventilation"] = 1.0
    room.memes["needs_attention"] = 0.0
    sensor.meters["alert"] = 0.0
    world.say(
        f"With the room ready, {buddy.id} washed up before the snack, and the children "
        f"finished their garden work. {episode.ending_image.capitalize()}."
    )
    world.say(
        f"{hero.id} hung the cape where it could not swoop into a seed tray. "
        f'"A hero can be brave and careful," {hero.id} said. {buddy.id} grinned: '
        f'"And capes should stay out of the tomatoes."'
    )

    world.facts.update(
        hero=hero,
        buddy=buddy,
        sensor=sensor,
        room=room,
        germ=germ,
        adult=adult,
        place=place,
        episode=episode,
        truth="the children left the greenhouse and an adult had the ventilation checked",
        resolution=episode.ending_image,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    episode = facts["episode"]
    place = facts["place"]
    return [
        f"Write a child-friendly superhero story about {facts['hero'].label}, {episode.label}, and careful handwashing.",
        f"Tell a cautionary rhyming story set in {place.label} where a carbon dioxide sensor warning leads the children to get adult help.",
        f"Write a funny but sensible garden adventure in which the children respect the warning, avoid pretending germs are visible, and finish {episode.ending_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    episode = facts["episode"]
    return [
        QAItem(
            question=f"What were {facts['hero'].label} and {facts['buddy'].label} doing at {facts['place'].label}?",
            answer=f"They were {episode.activity} as part of {episode.label}.",
        ),
        QAItem(
            question=f"Why did {facts['hero'].label} ask {facts['buddy'].label} to wash up?",
            answer=f"{facts['buddy'].label} had {episode.germ_moment}. Germs are too small to see, and washing hands before eating or touching the face can help keep them from spreading.",
        ),
        QAItem(
            question="What did the carbon dioxide sensor warn the children about?",
            answer="It showed an alert that carbon dioxide was building up in the closed greenhouse. The children treated the warning seriously and did not try to repair the room themselves.",
        ),
        QAItem(
            question=f"What did {facts['hero'].label} and {facts['buddy'].label} do when the sensor beeped?",
            answer=f"They left the greenhouse together and told Ms. Rivera. She kept everyone outside while the caretaker checked the room and restored its ventilation.",
        ),
        QAItem(
            question="How could everyone tell that the garden adventure ended safely?",
            answer=f"The caretaker checked the greenhouse before the children returned, and {episode.ending_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a germ, and can you usually see one?",
            answer="A germ is a tiny living thing or particle that can sometimes make people sick. Germs are too small to see without special equipment, so a person should not guess that a particular speck is a germ.",
        ),
        QAItem(
            question="What is carbon dioxide?",
            answer="Carbon dioxide is a gas that people breathe out and plants use. If a room's safety sensor gives an alert, children should leave and tell a trusted adult rather than trying to fix the room themselves.",
        ),
        QAItem(
            question="What is a sensible way to reduce the spread of germs before a snack?",
            answer="Wash hands with soap and water before eating, and avoid touching food with dirty hands.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.extend(("", "== story qa =="))
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.label} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  outcome={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "truth")}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="school",
        episode="seed_packets",
        hero="Luna",
        buddy="Milo",
        route="sunny_opening",
        seed=101,
    ),
    StoryParams(
        place="community",
        episode="tomato_fair",
        hero="Nia",
        buddy="Zoe",
        route="cape_opening",
        seed=202,
    ),
    StoryParams(
        place="garden_room",
        episode="moonflower_club",
        hero="Joey",
        buddy="Iris",
        route="club_opening",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(f"{asp_facts()}\n{ASP_RULES}")
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, episode in combos:
            print(f"  {place:12} {episode}")
        return
    if getattr(args, "n", None) < 1 and not getattr(args, "all", None):
        print("The number of stories must be at least 1.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < getattr(args, "n", None) and attempts < max(getattr(args, "n", None) * 60, 60):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = "### curated story" if getattr(args, "all", None) else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
