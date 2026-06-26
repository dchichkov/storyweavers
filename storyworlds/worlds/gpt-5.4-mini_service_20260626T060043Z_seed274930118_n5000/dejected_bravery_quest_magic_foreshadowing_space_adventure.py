#!/usr/bin/env python3
"""
Storyworld: dejected_bravery_quest_magic_foreshadowing_space_adventure

A small space-adventure storyworld with a quest, a touch of magic, and
foreshadowing that changes what the characters choose to do.

Seed premise:
- A dejected young space traveler must finish a quest.
- A magic object gives a warning about what is ahead.
- Bravery grows when the traveler chooses the safe, clever path.

The world is intentionally compact:
- one hero
- one guide
- one magical tool
- one quest object
- one outer-space setting
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Station:
    place: str = "the starlit docking bay"
    danger: str = "the dark drift beyond the bay"
    affords: set[str] = field(default_factory=lambda: {"quest", "fly", "scan"})
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    turn: str
    keyword: str
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
class Magic:
    id: str
    label: str
    phrase: str
    warning: str
    aid: str
    covers: set[str] = field(default_factory=set)
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
    def __init__(self, station: Station) -> None:
        self.station = station
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _push(state: World, text: str) -> None:
    state.say(text)


def propagate(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    guide = _safe_fact(world, world.facts, "guide")
    quest = _safe_fact(world, world.facts, "quest")
    magic = _safe_fact(world, world.facts, "magic")
    relic = _safe_fact(world, world.facts, "relic")

    if hero.memes.get("dejected", 0.0) >= THRESHOLD and ("foreshadow", hero.id) not in world.fired:
        world.fired.add(("foreshadow", hero.id))
        _push(
            world,
            f"The {magic.label} gave a small, shimmering warning: {magic.warning}. "
            f"That made {hero.id} look down at {hero.pronoun('possessive')} boots."
        )

    if hero.memes.get("bravery", 0.0) >= THRESHOLD and ("courage", hero.id) not in world.fired:
        world.fired.add(("courage", hero.id))
        _push(
            world,
            f"Then {hero.id} straightened up. {hero.pronoun().capitalize()} took a slow breath, "
            f"because bravery felt bigger when the stars were watching."
        )

    if quest.id == "rescue_beacon" and relic.meters.get("powered", 0.0) >= THRESHOLD and (
        "quest_done", relic.id
    ) not in world.fired:
        world.fired.add(("quest_done", relic.id))
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
        _push(
            world,
            f"The little beacon blinked awake again, and the bay lights glowed warm gold. "
            f"{guide.id} smiled, because the quest had worked."
        )


def start_story(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    guide = _safe_fact(world, world.facts, "guide")
    quest = _safe_fact(world, world.facts, "quest")
    magic = _safe_fact(world, world.facts, "magic")
    relic = _safe_fact(world, world.facts, "relic")

    _push(
        world,
        f"{hero.id} was a small space cadet with a dejected heart after the last launch went wrong."
    )
    _push(
        world,
        f"Still, {hero.pronoun()} loved {quest.gerund}, and {guide.id} said the ship needed "
        f"{hero.pronoun('possessive')} brave hands."
    )
    _push(
        world,
        f"On the table near the hatch, {magic.phrase} waited like a moonbeam in a bottle."
    )
    _push(
        world,
        f"It belonged to {hero.id}, and everyone called it the {magic.label}."
    )

    world.para()

    _push(
        world,
        f"One evening in {world.station.place}, {hero.id} and {guide.id} prepared for the quest."
    )
    _push(
        world,
        f"The job was to {quest.verb} before the station drifted too far from the safe route."
    )
    _push(
        world,
        f"{hero.id} reached for the {magic.label}, and its glow whispered about {quest.risk}."
    )
    hero.memes["dejected"] = hero.memes.get("dejected", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 0.5
    world.facts["foreshadow"] = quest.risk
    propagate(world)

    world.para()

    _push(
        world,
        f"Outside, the stars looked tiny and sharp, and the next corridor twisted toward {world.station.danger}."
    )
    _push(
        world,
        f"{hero.id} almost turned back, but {guide.id} pointed at the warning glow and said, "
        f'"That is not a stop sign. That is a clue."'
    )
    hero.memes["dejected"] = max(0.0, hero.memes.get("dejected", 0.0) - 0.5)
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(f"{hero.id} nodded and lifted {hero.pronoun('possessive')} chin.")
    propagate(world)

    world.para()

    _push(
        world,
        f"They followed the clue to the broken beacon room, where {relic.phrase} had gone dark."
    )
    _push(
        world,
        f"The {magic.label} showed the exact slot that needed fixing, and {hero.id} slipped the crystal key into place."
    )
    relic.meters["powered"] = 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    guide.memes["pride"] = guide.memes.get("pride", 0.0) + 1.0
    propagate(world)

    _push(
        world,
        f"At last, the beacon shone again. {hero.id} was no longer dejected; {hero.pronoun()} was brave enough to lead the way home."
    )

    world.facts.update(hero=hero, guide=guide, quest=quest, magic=magic, relic=relic)
    world.facts["resolved"] = True


SETTINGS = {
    "docking_bay": Station(place="the starlit docking bay", danger="the dark drift beyond the bay"),
    "moon_base": Station(place="the moon base corridor", danger="the black crater edge"),
    "space_station": Station(place="the spinning space station", danger="the silent outer hatch"),
}

QUESTS = {
    "rescue_beacon": Quest(
        id="rescue_beacon",
        verb="fix the broken beacon",
        gerund="fixing broken beacons",
        risk="a warning from the dark drift",
        turn="find the beacon room",
        keyword="beacon",
        tags={"beacon", "light", "space"},
    ),
    "deliver_map": Quest(
        id="deliver_map",
        verb="deliver the star map",
        gerund="delivering star maps",
        risk="a gap in the route",
        turn="cross the quiet tunnel",
        keyword="map",
        tags={"map", "stars", "space"},
    ),
}

MAGICS = {
    "moon_glass": Magic(
        id="moon_glass",
        label="Moon Glass",
        phrase="a round crystal that glowed like milk-blue starlight",
        warning="the next corridor would rattle like thunder in a tin cup",
        aid="pointing to the right path",
        covers={"choice"},
    ),
    "star_lantern": Magic(
        id="star_lantern",
        label="Star Lantern",
        phrase="a tiny lantern with a soft gold flame",
        warning="one doorway would lead to a dead end of cold air",
        aid="lighting the safer turn",
        covers={"choice"},
    ),
}

RELICS = {
    "beacon": Entity(id="beacon", type="thing", label="beacon", phrase="the station beacon"),
    "map_case": Entity(id="map_case", type="thing", label="map case", phrase="the sealed star map case"),
}

HEROES = [
    ("Ari", "girl"),
    ("Nova", "girl"),
    ("Finn", "boy"),
    ("Jett", "boy"),
]

GUIDES = [
    ("Captain Vale", "captain"),
    ("Rin", "woman"),
    ("Orlo", "man"),
]

TRAITS = ["curious", "careful", "bold", "gentle", "quick-thinking"]

@dataclass
class StoryParams:
    place: str
    quest: str
    magic: str
    hero: str
    gender: str
    guide: str
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


CURATED = [
    StoryParams(place="docking_bay", quest="rescue_beacon", magic="moon_glass", hero="Ari", gender="girl", guide="Captain Vale", trait="curious"),
    StoryParams(place="moon_base", quest="deliver_map", magic="star_lantern", hero="Finn", gender="boy", guide="Orlo", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld with quest, magic, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--trait", choices=TRAITS)
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
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    hero, gender = (getattr(args, "hero", None), getattr(args, "gender", None))
    if hero is None or gender is None:
        hero, gender = rng.choice(HEROES)
    guide = getattr(args, "guide", None) or rng.choice([g for g, _ in GUIDES])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, magic=magic, hero=hero, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    quest = _safe_lookup(QUESTS, params.quest)
    magic = _safe_lookup(MAGICS, params.magic)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    guide = world.add(Entity(id=params.guide, kind="character", type="captain"))
    relic = world.add(RELICS["beacon"] if quest.id == "rescue_beacon" else RELICS["map_case"])

    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["quest"] = quest
    world.facts["magic"] = magic
    world.facts["relic"] = relic

    hero.memes["dejected"] = 1.0
    hero.memes["bravery"] = 0.0
    guide.memes["pride"] = 0.0

    start_story(world)

    prompts = [
        f"Write a short space adventure about {params.hero}, a {params.gender} cadet, who needs a quest, magic, and a brave choice.",
        f"Tell a child-friendly story where {params.hero} feels dejected at first, then grows brave after a magical warning.",
        f"Make a tiny starship tale with foreshadowing that helps the hero finish {quest.gerund}.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.hero} seem dejected at the start of the story?",
            answer=f"{params.hero} seemed dejected because the last launch had gone wrong, and {params.hero} worried about the quest.",
        ),
        QAItem(
            question=f"What did the {magic.label} warn them about?",
            answer=f"The {magic.label} warned them about {quest.risk}, so the warning helped them choose the safer path.",
        ),
        QAItem(
            question=f"What did {params.hero} do to show bravery?",
            answer=f"{params.hero} listened to the warning, kept going, and fixed the problem instead of turning back.",
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"The quest ended when the beacon or map was set right, and the ship was safe again.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints at something important that will happen later.",
        ),
        QAItem(
            question="What does a magic object often do in a story?",
            answer="A magic object can help characters, warn them, or show them a hidden truth.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find, fix, or deliver something important.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
kind(hero;guide;quest;magic;relic).

resolved :- powered(relic), bravery(hero).
foreshadowed :- warning(magic), dejected(hero).
brave_turn :- foreshadowed, resolved.

#show resolved/0.
#show foreshadowed/0.
#show brave_turn/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("dejected", "hero"),
        asp.fact("bravery", "hero"),
        asp.fact("warning", "magic"),
        asp.fact("powered", "relic"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show foreshadowed/0.\n#show brave_turn/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"resolved/0", "foreshadowed/0", "brave_turn/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def asp_valid() -> list[tuple[str, str, str]]:
    return [(p, q, m) for p in SETTINGS for q in QUESTS for m in MAGICS]


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
        print(asp_program("#show resolved/0.\n#show foreshadowed/0.\n#show brave_turn/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid())} compatible combinations:")
        for p, q, m in asp_valid():
            print(f"  {p:12} {q:14} {m}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
