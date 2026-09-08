#!/usr/bin/env python3
"""A child-facing transformation fable about a bluff and a changing schedule."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    helper: object | None = None
    hero: object | None = None
    object_entity: object | None = None
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
class Scene:
    place: str
    weather: str
    mood: str
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
    place: str = ""
    transformation: str = ""
    name: str = ""
    helper: str = ""
    bluff: str = ""
    schedule: str = ""
    route: str = ""
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


@dataclass
class Fable:
    object_name: str
    bluff_claim: str
    warning: str
    test: str
    reveal: str
    change: str
    repair: str
    lesson: str
    ending: str
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
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
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


PLACES = {
    "hill": Scene("the hilltop", "a bright wind", "watchful"),
    "harbor": Scene("the harbor steps", "a salty mist", "busy"),
    "orchard": Scene("the old orchard", "a warm breeze", "golden"),
    "meadow": Scene("the meadow gate", "a soft drizzle", "quiet"),
}

TRANSFORMATIONS = {
    "lantern": "a dark paper lantern that could become a guiding star",
    "cart": "a squeaky wooden cart that could become a little stage",
    "clock": "a stopped copper clock that could become a bell for new beginnings",
    "banner": "a faded cloth banner that could become a bright bridge between neighbors",
}

BLUFFS = {
    "brag": "claimed to know the perfect time for every task",
    "hide": "pretended the old schedule was still working",
    "rush": "boasted that rushing would finish everything before sunset",
    "silence": "insisted that no one needed to discuss the changed plan",
}

SCHEDULES = {
    "sunrise": "the sunrise market, the noon meal, and the evening lantern walk",
    "tide": "the low-tide gathering, the boat launch, and the moonlit cleanup",
    "harvest": "the fruit picking, the shared pie, and the dusk song",
    "rain": "the morning planting, the indoor craft hour, and the rain-drum concert",
}

HELPERS = {"Mara": "girl", "Tomas": "boy", "Pip": "child", "Nia": "girl"}
ROUTES = ("notice_first", "dialogue_first", "schedule_first", "bluff_first", "quiet_first", "weather_first")

FABLES = {
    "lantern": Fable(
        "the paper lantern",
        "claimed the lantern would shine at noon even without a candle",
        "the festival schedule had moved the lantern walk before sunset",
        "held the lantern beside a window and compared its shadow with the clock",
        "the lantern was not broken; its folded panels were hiding the wick",
        "unfolded the panels into a star shape and moved the walk to twilight",
        "lit the lantern safely after an adult checked the candle",
        "a confident bluff cannot replace a careful look",
        "the new star lantern glowed while everyone followed the honest twilight schedule",
    ),
    "cart": Fable(
        "the wooden cart",
        "claimed the cart could carry every basket at once",
        "the schedule had added a small stage before the baskets needed moving",
        "counted the baskets and measured the cart's narrow bed",
        "the cart's loose side could fold down and turn it into a stage",
        "unlatched the side, moved the baskets in two trips, and made room for music",
        "tightened the wheel and marked two trips on the schedule",
        "a boast becomes useful only when truth guides it",
        "the cart rolled as a stage while the baskets arrived safely on time",
    ),
    "clock": Fable(
        "the copper clock",
        "claimed the stopped clock still knew the hour",
        "the schedule had changed when clouds hid the sun",
        "compared the clock with shadows, bells, and the harbor tide",
        "the clock's hands were stuck beneath a folded festival ribbon",
        "freed the hands and rewrote the schedule around the true afternoon",
        "cleaned the clock and gave it a gentle bell mark for each new task",
        "a schedule should listen to the world it serves",
        "the copper clock chimed beside a schedule that fit both people and daylight",
    ),
    "banner": Fable(
        "the cloth banner",
        "claimed the faded banner still welcomed everyone equally",
        "the schedule had divided neighbors into separate work times",
        "held the banner between the two paths and read its worn words aloud",
        "a hidden bright side appeared when the cloth was turned around",
        "reversed the banner and joined the work times into one shared celebration",
        "stitched a strong border and wrote the new times on both sides",
        "a changed view can turn a barrier into an invitation",
        "the bright banner stretched across the path as neighbors kept the new schedule together",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A transformation fable about a bluff and a schedule.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--bluff", choices=sorted(BLUFFS))
    parser.add_argument("--schedule", choices=sorted(SCHEDULES))
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [(place, transformation) for place in sorted(PLACES) for transformation in sorted(TRANSFORMATIONS)]


ASP_RULES = """
valid(Place, Transformation) :- place(Place), transformation(Transformation).
compatible(Place, Transformation) :- valid(Place, Transformation).
#show valid/2.
""".strip()


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("place", place) for place in PLACES)
    facts.extend(asp.fact("transformation", transformation) for transformation in TRANSFORMATIONS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} combinations).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(python_pairs - asp_pairs))
    print("ASP only:", sorted(asp_pairs - python_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if not getattr(args, "place", None) or pair[0] == getattr(args, "place", None)
        if not getattr(args, "transformation", None) or pair[1] == getattr(args, "transformation", None)
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, transformation = rng.choice(choices)
    name = getattr(args, "name", None) or "Luna"
    helper_choices = [name_ for name_ in sorted(HELPERS) if name_ != name] or sorted(HELPERS)
    return StoryParams(
        place=place,
        transformation=transformation,
        name=name,
        helper=getattr(args, "helper", None) or rng.choice(helper_choices),
        bluff=getattr(args, "bluff", None) or rng.choice(sorted(BLUFFS)),
        schedule=getattr(args, "schedule", None) or rng.choice(sorted(SCHEDULES)),
        route=getattr(args, "route", None) or rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    raw = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.transformation,
            params.name,
            params.helper,
            params.bluff,
            params.schedule,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = _safe_lookup(PLACES, params.place)
    fable = _safe_lookup(FABLES, params.transformation)
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        meters={"care": 1.0, "certainty": 0.2},
        memes={"honesty": 0.3},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS.get(params.helper, "child"),
        meters={"patience": 0.7},
        memes={"helpfulness": 0.8},
    ))
    object_entity = world.add(Entity(
        id=params.transformation,
        kind="object",
        type="transforming_object",
        label=fable.object_name,
        meters={"usefulness": 0.4, "flexibility": 0.8},
        memes={"promise": 0.6},
    ))

    schedule_text = _safe_lookup(SCHEDULES, params.schedule)
    openings = {
        "notice_first": (
            f"At {scene.place}, {hero.id} found {fable.object_name} beside a board listing "
            f"{schedule_text}. {scene.weather.capitalize()} moved the corners of the schedule."
        ),
        "dialogue_first": (
            f'"The schedule has changed," said {helper.id} at {scene.place}. '
            f'{hero.id} looked at {fable.object_name} while the board listed {schedule_text}.'
        ),
        "schedule_first": (
            f"The board at {scene.place} announced {schedule_text}. "
            f"Then {hero.id} noticed that {fable.object_name} no longer fit the first plan."
        ),
        "bluff_first": (
            f"{hero.id} stood proudly at {scene.place} and made a bluff about {fable.object_name}. "
            f"Behind them, the schedule listed {schedule_text}."
        ),
        "quiet_first": (
            f"Nobody spoke when {hero.id} saw {fable.object_name} beside the schedule at {scene.place}. "
            f"The quiet was deeper than the {scene.weather}."
        ),
        "weather_first": (
            f"The {scene.weather} changed the morning at {scene.place}. "
            f"That small change bent the schedule and left {fable.object_name} in an unexpected place."
        ),
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"{helper.id} carried a pencil for marking honest changes.",
        f"{hero.id} promised to follow the plan, but only after checking it.",
        f"Together, the children read each time aloud instead of trusting a hurried glance.",
    ]))
    world.para()

    world.say(f"{hero.id} {_safe_lookup(BLUFFS, params.bluff)}.")
    world.say(f"{helper.id} frowned. \"That sounds certain, but the schedule says {schedule_text}.\"")
    world.say(f'"A bluff is not a bridge to the truth," {hero.id} replied. "What should we check?"')
    world.say(f'"Check the object, the times, and the people who depend on them," said {helper.id}.')
    hero.memes["bluff"] = 1
    hero.meters["certainty"] = 0.5

    world.para()
    world.say(f"The warning was clear: {fable.warning}.")
    world.say(f"First, the friends {fable.test}.")
    world.say(rng.choice([
        "The first answer did not fit every part of the day.",
        "Their quick guess left one important time uncovered.",
        "The children crossed out the guess without pretending it had been right.",
    ]))
    world.say(f"Then the transformation began: {fable.reveal}.")
    world.say(f"{hero.id} saw that {fable.object_name} could change instead of being thrown away.")
    object_entity.meters["usefulness"] = 1.0
    object_entity.memes["promise"] = 1.0
    hero.meters["certainty"] = 1.0

    world.para()
    world.say(f"Together, {hero.id} and {helper.id} {fable.change}.")
    world.say(f"The schedule became a guide rather than a rule that refused to bend.")
    hero.memes["bluff"] = 0
    hero.memes["honesty"] = 1.0
    world.say(f'"I was bluffing because I wanted to seem ready," {hero.id} admitted. "Now I know that changing a plan can be wise."')
    world.say(f'"And telling the truth lets everyone change with it," {helper.id} said.')
    world.say(f"After that, they {fable.repair}.")
    world.say(f"The fable's lesson was simple: {fable.lesson}.")
    world.say(f"At the end of the day, {fable.ending}.")

    world.facts.update(
        hero=hero,
        helper=helper,
        object=object_entity,
        fable=fable,
        schedule=schedule_text,
        bluff=_safe_lookup(BLUFFS, params.bluff),
        place=scene.place,
        transformation=params.transformation,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    fable: Fable = facts["fable"]
    return [
        f"Write a short fable for a young child about {facts['hero'].id}, a bluff, and a schedule at {facts['place']}.",
        f"Tell a transformation fable in which {fable.object_name} changes after {facts['hero'].id} and {facts['helper'].id} test the schedule.",
        f"Write a gentle story showing that {fable.lesson}, ending with {fable.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    fable: Fable = facts["fable"]
    hero = facts["hero"].id
    helper = facts["helper"].id
    return [
        QAItem(
            question=f"What bluff did {hero} make at {facts['place']}?",
            answer=f"{hero} {facts['bluff']}, but the claim did not account for the schedule, which listed {facts['schedule']}.",
        ),
        QAItem(
            question=f"How did {helper} help {hero} respond to the changed schedule?",
            answer=f"{helper} asked {hero} to check the object, the times, and the people who depended on them instead of trusting the bluff.",
        ),
        QAItem(
            question=f"What transformation happened to {fable.object_name}?",
            answer=f"{fable.reveal.capitalize()} Then {hero} and {helper} {fable.change}.",
        ),
        QAItem(
            question=f"Why did the children change the schedule?",
            answer=f"They changed it because {fable.warning}. The new schedule fit the transformed object and helped everyone take part.",
        ),
        QAItem(
            question=f"What lesson did {hero} learn?",
            answer=f"{hero} learned that {fable.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bluff?",
            answer="A bluff is a claim or show of confidence that may hide uncertainty or lack of proof.",
        ),
        QAItem(
            question="Why might a schedule need to change?",
            answer="A schedule may need to change when weather, materials, people, or new information changes what can happen safely and fairly.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means that a person, object, or situation changes into a new form or gains a new purpose.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")}")
    lines.append(f"  schedule={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "schedule")}")
    lines.append(f"  transformation={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "transformation")}")
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="hill",
        transformation="lantern",
        name="Luna",
        helper="Mara",
        bluff="brag",
        schedule="sunrise",
        route="notice_first",
        seed=101,
    ),
    StoryParams(
        place="harbor",
        transformation="cart",
        name="Luna",
        helper="Tomas",
        bluff="rush",
        schedule="tide",
        route="dialogue_first",
        seed=202,
    ),
    StoryParams(
        place="orchard",
        transformation="banner",
        name="Luna",
        helper="Nia",
        bluff="silence",
        schedule="harvest",
        route="schedule_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combinations:\n")
        for place, transformation in combinations:
            print(f"  {place:10} {transformation}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < getattr(args, "n", None) and attempts < max(getattr(args, "n", None) * 50, 50):
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
