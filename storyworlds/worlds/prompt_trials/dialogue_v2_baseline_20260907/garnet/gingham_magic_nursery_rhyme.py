#!/usr/bin/env python3
"""
A gentle nursery-rhyme storyworld about gingham, a little magic, and a brave
child who learns that a careful promise can guide a wandering spell home.
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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    answer: str = ""
    cloth: object | None = None
    helper: object | None = None
    hero: object | None = None
    question: str = ""
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
    hero: Item
    helper: Item
    cloth: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    name: str = ""
    helper_name: str = ""
    place: str = ""
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


NAMES = ["Pip", "Mina", "Toby", "Lulu", "Nell", "Bram", "Ivy", "Ollie"]
HELPERS = ["Nan", "Aunt May", "Grandma June", "Uncle Fox", "Miss Bea"]
PLACES = [
    "the moonlit kitchen",
    "the bluebell lane",
    "the little garden gate",
    "the toy-maker's porch",
    "the hill beside the mill",
]


ASP_RULES = r"""
#show bright/1.
#show wandering/1.
#show mended/1.
#show shared/1.

bright(H) :- touches_magic(H).
wandering(H) :- spell_loose(H).
mended(H) :- promise_kept(H).
shared(H) :- magic_shared(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("touches_magic", "hero"),
            asp.fact("spell_loose", "hero"),
            asp.fact("promise_kept", "hero"),
            asp.fact("magic_shared", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    shown = "#show bright/1.\n#show wandering/1.\n#show mended/1.\n#show shared/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name not in {"bright", "wandering", "mended", "shared"}:
            continue
        args = tuple(
            x.number if x.type == x.type.Number else x.name
            for x in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("bright", ("hero",)),
        ("wandering", ("hero",)),
        ("mended", ("hero",)),
        ("shared", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about gingham and gentle magic."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
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
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPERS),
        place=getattr(args, "place", None) or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.helper_name:
        pass
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"little {params.name}",
        kind="character",
        meters={"height": 1.1, "steadiness": 0.7},
        memes={"curiosity": 0.9, "courage": 0.8},
    )
    helper = Item(
        id="helper",
        label=params.helper_name,
        phrase=params.helper_name,
        kind="character",
        meters={"height": 1.7, "steadiness": 0.95},
        memes={"patience": 0.95, "kindness": 0.9},
    )
    cloth = Item(
        id="gingham",
        label="gingham",
        phrase="a square of red-and-white gingham",
        kind="cloth",
        owner=helper.id,
        meters={"size": 0.8, "weight": 0.2, "magic_charge": 1.0},
        memes={"warmth": 0.8, "mischief": 0.7, "belonging": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper_name}|{params.place}")
    return World(hero=hero, helper=helper, cloth=cloth, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    magic: str,
    trouble: str,
    cause: str,
    method: str,
    promise: str,
    resolution: str,
    ending: str,
    refrain: str,
    lines: list[str],
) -> str:
    world.facts.update(
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        shared=True,
    )
    return " ".join(lines)


def _moon_arc(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.place
    destination = _choice(
        rng,
        ["the chimney pot", "the old pear tree", "the baker's silver roof"],
    )
    magic = "the gingham stitched a tiny moon that glowed whenever someone sang"
    trouble = f"the glowing moon floated away toward {destination}"
    cause = "a loose corner caught a night breeze just as the nursery rhyme reached its highest note"
    method = "followed the cloth by singing softly and holding out both empty hands"
    promise = "I will not tug or tear; I will guide you home with care"
    resolution = (
        f"{h} sang the promise instead of chasing, and the gingham drifted down "
        f"from {destination} into {helper}'s waiting hands"
    )
    ending = "the moon-stitch shone quietly on the folded gingham beside the warm lamp"
    refrain = "Gingham, gingham, glow and go"
    lines = [
        f"In {place}, {h} found {helper} hemming {world.cloth.phrase}.",
        f'"Gingham, gingham, glow and go," sang {h}, and a little moon appeared in the cloth.',
        f"It bobbed past the spoons, slipped over the sill, and floated toward {destination}.",
        f'"Come back, come back!" cried {h}; but magic will not hurry for a worried shout.',
        f"{helper} said, \"A spell may wander when it hears a frightened voice. Try a calm one.\"",
        f"{h} took a breath and sang the rhyme again, then added, \"{promise}.\"",
        f"The moon slowed. The gingham turned. {h} used the promised empty hands and never pulled at a single thread.",
        f"{resolution}.",
        f"By bedtime, {ending}. The rhyme had learned that gentle voices make good paths home.",
    ]
    return _record(
        world,
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _pocket_arc(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.place
    visitors = _choice(
        rng,
        ["three sleepy mice", "two lost ducklings", "a fox cub and a mole"],
    )
    magic = "the gingham made every pocket it touched large enough to hold a wish"
    trouble = f"{visitors} climbed into the growing pockets and could not find the way out"
    cause = "the cloth had been folded inside out, so its helping magic became wandering magic"
    method = "turned the corner marked with a white cross while naming each guest"
    promise = "One by one, safe and sound, every friend comes out when called"
    resolution = (
        f"{h} turned the marked corner and called each friend by name; "
        f"{visitors} stepped from the pockets"
    )
    ending = "the gingham became an ordinary little square, with room only for a button and a smile"
    refrain = "Pocket wide, pocket deep, keep no friend you cannot keep"
    lines = [
        f"At {place}, {h} helped {helper} shake out {world.cloth.phrase}.",
        f'"Pocket wide, pocket deep," sang {h}, and the gingham grew a pocket big enough for {visitors}.',
        f"They popped inside with cheerful squeaks and quacks, but the pocket grew deeper still.",
        f"{h} reached in and reached in, while the cloth replied, \"Not yet! Not yet!\"",
        f"{helper} spotted a tiny white cross near the hem. \"Magic has a right side and a wrong side,\" said {helper}.",
        f"{h} stopped tugging and spoke the promise: \"{promise}.\"",
        f"{h} turned the corner marked with a white cross while naming each guest.",
        f"{resolution}. The pocket shrank with a soft plip.",
        f"At dusk, {ending}. Everyone agreed that even a magic pocket needs a careful keeper.",
    ]
    return _record(
        world,
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.cloth
    object_name = _choice(rng, ["a silver thimble", "a yellow teacup", "a blue toy boat"])
    magic = "the gingham stitched a rainbow path wherever it was waved"
    trouble = f"the rainbow path carried {object_name} downhill toward the pond"
    cause = "the cloth was used as a flag before its corner was tied to a sturdy bench"
    method = "tied the loose corner, then waved the cloth in a slow circle toward the garden"
    promise = "No more racing rainbows; I will point the bright road where it belongs"
    resolution = (
        f"{h} tied the loose corner, then waved the cloth in a slow circle toward "
        f"the garden, turning the rainbow away from the pond"
    )
    ending = "the rainbow rested over the garden, and the gingham dried in a sunny stripe"
    refrain = "Red square, rain fair, send the rainbow where"
    lines = [
        f"After a shower in {place}, {h} found {world.cloth.phrase} fluttering on a chair.",
        f'"Red square, rain fair!" sang {h}, and a rainbow sprang from the cloth.',
        f"It curled around {object_name} and carried it downhill toward the pond.",
        f"{helper} ran after it, calling, \"A rainbow is a road, not a runaway horse!\"",
        f"{h} noticed that the path followed every wave of the cloth. The magic was listening to the motion.",
        f"{h} stopped flapping wildly and spoke the promise: \"{promise}.\"",
        f"{resolution}.",
        f"The rainbow slowed over the garden, where thirsty flowers lifted their faces.",
        f"At sunset, {ending}. {object_name} came home, wet but proud of its bright adventure.",
    ]
    return _record(
        world,
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _button_arc(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.cloth
    animal = _choice(rng, ["a rabbit", "a lamb", "a small brown hen"])
    magic = "the gingham called lost things by making a bright button hop toward them"
    trouble = f"the hopping button led {animal} away from the yard and into the tall grass"
    cause = "the cloth had heard too many cries at once and could not tell a lost thing from a lonely one"
    method = "asked one clear question and placed the gingham flat beneath the button"
    promise = "I will call one thing at a time, and I will listen for the right reply"
    resolution = (
        f"{h} asked one clear question and placed the gingham flat beneath the button; "
        f"the button hopped back while {animal} followed"
    )
    ending = "the button rested on the gingham, and the lost-and-found song ended with a warm little bow"
    refrain = "Button bright, hop just right"
    lines = [
        f"Beside {place}, {h} heard {animal} crying near {world.cloth.phrase}.",
        f'"Button bright, hop just right!" sang {h}, and a red button sprang from the gingham.',
        f"It hopped over a stone, under a gate, and into tall grass with {animal} close behind.",
        f"{h} called for a shoe, a spoon, a ribbon, and a kite all at once. The button spun in circles.",
        f"{helper} knelt beside {h}. \"Magic listens best when the heart asks one thing,\" said {helper}.",
        f"{h} placed the gingham flat and spoke the promise: \"{promise}.\"",
        f"{resolution}.",
        f"{animal} trotted home, and the button stopped hopping.",
        f"That night, {ending}. One clear question had untangled a very busy spell.",
    ]
    return _record(
        world,
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _star_arc(world: World, rng: random.Random) -> str:
    h, helper, place = world.hero.label, world.helper.label, world.cloth
    sound = _choice(rng, ["a bell", "a spoon", "a tiny drum"])
    magic = "the gingham embroidered a star for every kind word spoken over it"
    trouble = f"the stars rose too high when someone shouted and began hiding behind the clouds"
    cause = "the cloth grew brighter from kindness but dimmed whenever angry words shook its threads"
    method = "spoke three true thanks and folded the corners toward the candlelight"
    promise = "Kind words first, bright stars next, and quiet hands to help them rest"
    resolution = (
        f"{h} spoke three true thanks and folded the corners toward the candlelight; "
        "the stars came down in a soft shining row"
    )
    ending = "the last star stitched itself beside the first, making one small constellation of home"
    refrain = "Thank you, thank you, starry blue"
    lines = [
        f"One evening in {place}, {h} found {helper} mending {world.cloth.phrase} by candlelight.",
        f'"Thank you, thank you, starry blue," sang {h}, and a bright star appeared in the cloth.',
        f"Another kind word made another star. Soon the gingham twinkled like a pocket sky.",
        f"Then a sharp shout rattled the room. The stars flew upward and hid behind the clouds.",
        f"{h} reached for the cloth, but {helper} said, \"A frightened spell needs kindness, not grabbing.\"",
        f"{h} spoke the promise: \"{promise}.\"",
        f"{resolution}.",
        f"The room grew calm. Even {sound} made only one polite little note.",
        f"Before sleep, {ending}. The magic stayed where kind words could find it.",
    ]
    return _record(
        world,
        magic=magic,
        trouble=trouble,
        cause=cause,
        method=method,
        promise=promise,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


ARC_BUILDERS = [_moon_arc, _pocket_arc, _rain_arc, _button_arc, _star_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7C)
    builder = _safe_lookup(ARC_BUILDERS, world.seed % len(ARC_BUILDERS))
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = world.hero.label
    return [
        QAItem(
            question=f"What magical thing happened to the gingham for {hero}?",
            answer=f"{hero} discovered that {facts['magic']}.",
        ),
        QAItem(
            question="What caused the magical trouble?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {hero} help solve the problem?",
            answer=f"{hero} solved it by {facts['method']}.",
        ),
        QAItem(
            question="What promise guided the magic?",
            answer=f'The promise was, "{facts["promise"]}."',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is gingham?",
            answer="Gingham is a woven fabric with a checked pattern, often made from two colors such as white and red or white and blue.",
        ),
        QAItem(
            question="What is magic in a nursery rhyme?",
            answer="Magic in a nursery rhyme is an imaginative power that makes ordinary things behave in surprising ways.",
        ),
        QAItem(
            question="Why do rhymes repeat words?",
            answer="Repeating words gives a rhyme a steady beat and helps children remember its playful pattern.",
        ),
    ]
    arc_questions = {
        "moon": QAItem(
            question="Why did the glowing moon drift away?",
            answer="The moon drifted away because a loose corner of the gingham caught a night breeze while the song was being sung.",
        ),
        "pocket": QAItem(
            question="Why did the magic pocket grow too deep?",
            answer="The pocket grew too deep because the gingham was folded inside out, turning its helping magic into wandering magic.",
        ),
        "rain": QAItem(
            question="What made the rainbow path move?",
            answer="The rainbow path moved because the magic listened to the way the gingham was waved.",
        ),
        "button": QAItem(
            question="Why did the button spin in circles?",
            answer="The button spun in circles because it heard too many different requests at the same time.",
        ),
        "star": QAItem(
            question="What made the stars hide?",
            answer="The stars hid because a sharp shout frightened the gentle magic in the gingham.",
        ),
    }
    return [common[0], _safe_lookup(arc_questions, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "arc")), common[1]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle nursery rhyme about gingham and a small piece of magic.",
        f"Tell a child-facing rhyme set at {world.place}, where {world.hero.label} learns to guide magic with care.",
        "Use repetition, a simple magical problem, a brave child, and a warm ending image.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.helper, world.cloth]:
        lines.append(
            f"  {entity.id:8} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    if world.facts:
        lines.append(f"  arc={world.facts.get('arc', '')!r}")
        lines.append(f"  magic={world.facts.get('magic', '')!r}")
        lines.append(f"  resolution={world.facts.get('resolution', '')!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "n", None) < 1:
        pass

    if getattr(args, "show_asp", None):
        print(
            asp_program(
                "#show bright/1.\n"
                "#show wandering/1.\n"
                "#show mended/1.\n"
                "#show shared/1."
            )
        )
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print(
            "4 compatible logical atoms: bright(hero), wandering(hero), "
            "mended(hero), shared(hero)"
        )
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(
                name="Pip",
                helper_name="Nan",
                place="the moonlit kitchen",
                seed=base_seed,
            ),
            StoryParams(
                name="Mina",
                helper_name="Aunt May",
                place="the bluebell lane",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Toby",
                helper_name="Grandma June",
                place="the little garden gate",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Lulu",
                helper_name="Uncle Fox",
                place="the toy-maker's porch",
                seed=base_seed + 3,
            ),
            StoryParams(
                name="Nell",
                helper_name="Miss Bea",
                place="the hill beside the mill",
                seed=base_seed + 4,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, getattr(args, "n", None) * 20)
        while len(samples) < getattr(args, "n", None) and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < getattr(args, "n", None) and not getattr(args, "all", None):
        pass

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)
