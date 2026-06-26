#!/usr/bin/env python3
"""
A standalone storyworld for a Tall Tale-style mystery: a stubborn nag, a
booming clamor, and a small puzzle that gets solved by watching the world
closely instead of guessing.

The seed premise:
- A child and a grown-up hear a clamor.
- Someone nags and nags about the noise.
- The mystery is solved by tracing a physical cause.
- The ending should feel tall-tale-ish: big, playful, and concrete.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bell: object | None = None
    clue: object | None = None
    goat: object | None = None
    helper: object | None = None
    hero: object | None = None
    jar: object | None = None
    source: object | None = None
    wagon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    place: str
    indoors: bool = False
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
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    fix: str
    noise: str
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
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _parrot_clamor(world: World) -> None:
    for e in world.characters():
        if e.memes.get("clamor", 0) >= THRESHOLD:
            e.memes["fright"] = e.memes.get("fright", 0) + 1
            e.memes["curiosity"] = e.memes.get("curiosity", 0) + 1


def _solve_by_listening(world: World) -> None:
    for e in world.characters():
        if e.memes.get("curiosity", 0) >= THRESHOLD and e.memes.get("fright", 0) < 2:
            e.memes["understanding"] = 1


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = [(e.id, dict(e.memes)) for e in world.entities.values()]
        _parrot_clamor(world)
        _solve_by_listening(world)
        after = [(e.id, dict(e.memes)) for e in world.entities.values()]
        if after != before:
            changed = True


SETTINGS = {
    "barn": Setting(place="the big red barn", indoors=True),
    "town": Setting(place="the little town square", indoors=False),
    "porch": Setting(place="the front porch", indoors=False),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        clue="a ringing clamor that bounced off the boards",
        cause="a goat had snagged the dinner bell rope and was tugging it with all its might",
        reveal="the bell was not haunted at all; it was only a goat with a crooked grin",
        fix="the rope was tied up high and the bell was hung where the goat could not reach",
        noise="clamor",
        tags={"goat", "bell", "noise"},
    ),
    "wagon": Mystery(
        id="wagon",
        clue="a rattling clamor that rolled through the yard",
        cause="a wagon wheel had a loose bolt and tapped the axle like a drumstick",
        reveal="the wagon was not singing for no reason; one wheel had come loose",
        fix="the bolt was tightened and the wheel went quiet as moonlight",
        noise="clamor",
        tags={"wagon", "wheel", "noise"},
    ),
    "jar": Mystery(
        id="jar",
        clue="a clanking clamor from the pantry shelf",
        cause="two tin spoons had slid into a jar and knocked together like tiny hammers",
        reveal="the pantry was not full of goblins; it was full of spoons arguing in a jar",
        fix="the jar was moved and the spoons were laid flat",
        noise="clamor",
        tags={"jar", "spoon", "noise"},
    ),
}

HELPERS = {
    "grandmother": Entity(id="Grandmother", kind="character", type="woman", label="grandmother"),
    "uncle": Entity(id="Uncle", kind="character", type="man", label="uncle"),
    "sister": Entity(id="Sister", kind="character", type="girl", label="sister"),
}

HEROES = {
    "girl": ["Ada", "Molly", "June", "Nell", "Ruby"],
    "boy": ["Bo", "Eli", "Toby", "Otis", "Sam"],
}

TRAITS = ["brave", "curious", "stubborn", "quick-footed", "wide-eyed"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery storyworld about a nag and a clamor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[1] == getattr(args, "mystery", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mystery = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(HEROES, gender))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label="child"))
    helper_template = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(
        id=helper_template.id, kind="character", type=helper_template.type, label=helper_template.label
    ))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    clue = world.add(Entity(id="Clue", kind="thing", type="clue", label="clue", phrase=mystery.clue))
    source = world.add(Entity(id="Source", kind="thing", type="cause", label="cause", phrase=mystery.cause))
    bell = world.add(Entity(id="Bell", kind="thing", type="bell", label="bell", phrase="a dinner bell"))
    goat = world.add(Entity(id="Goat", kind="thing", type="goat", label="goat", phrase="a goat"))
    wagon = world.add(Entity(id="Wagon", kind="thing", type="wagon", label="wagon", phrase="a wagon"))
    jar = world.add(Entity(id="Jar", kind="thing", type="jar", label="jar", phrase="a pantry jar"))

    # Setup
    world.say(
        f"In {world.setting.place}, {hero.id} was a {rng_word(hero, 'trait')} little {params.gender} who liked to listen for strange things."
    )
    world.say(
        f"{helper.id} told {hero.id} that every mystery leaves tracks, even when it makes a mighty {mystery.noise}."
    )
    world.para()

    # Tension
    hero.memes["curiosity"] = 1
    hero.memes["clamor"] = 1
    helper.memes["nag"] = 1
    world.say(
        f"One day a great {mystery.noise} rose up like thunder in a teacup, and {helper.id} began to nag, "
        f'"Find the cause! Find the cause!"'
    )
    world.say(
        f"The whole place shook with the {mystery.noise}, and {hero.id} looked around while {helper.id} kept on nagging."
    )

    # Investigation
    world.para()
    world.say(f"{hero.id} listened first. That was smarter than guessing, because the sound had a rhythm.")
    world.say(f"{hero.id} followed the clue: {mystery.clue}.")
    if params.mystery == "bell":
        world.say("The clue pointed high as a kite string. The bell rope had been tugged again and again.")
    elif params.mystery == "wagon":
        world.say("The clue pointed down at a wheel track, where one wheel kissed the road with every bump.")
    else:
        world.say("The clue pointed to the pantry shelf, where the jars shivered when the floorboards hummed.")
    hero.memes["curiosity"] = 2
    propagate(world)

    # Reveal and resolution
    world.para()
    world.say(f"At last {hero.id} found the truth: {mystery.cause}.")
    world.say(f"{mystery.reveal.capitalize()}.")
    world.say(f"{mystery.fix.capitalize()}.")
    hero.memes["understanding"] = 1
    helper.memes["nag"] = 0
    helper.memes["joy"] = 1
    hero.memes["joy"] = 1
    world.say(
        f"{helper.id} stopped nagging at last and laughed so hard the rafters seemed to grin."
    )
    world.say(
        f"{hero.id} stood tall in the quiet afterward, as proud as a fence post wearing a sunset."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "mystery": mystery,
        "setting": world.setting,
        "clue": clue,
        "source": source,
        "bell": bell,
        "goat": goat,
        "wagon": wagon,
        "jar": jar,
    }
    return world


def rng_word(hero: Entity, kind: str) -> str:
    return "brave"


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for a child about a "{f["mystery"].noise}" and a mystery to solve.',
        f"Tell a playful story where {f['hero'].id} hears a {f['mystery'].noise}, ignores the nag for a moment, and solves the puzzle.",
        f'Write a mystery story for young children that includes the words "nag" and "clamor".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What did {hero.id} hear in {world.setting.place}?",
            answer=f"{hero.id} heard a mighty {mystery.noise} that filled the place like a big drum.",
        ),
        QAItem(
            question=f"Who kept nagging about the noise?",
            answer=f"{helper.id} kept nagging and told {hero.id} to find the cause of the clamor.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"It was solved by following the clue and discovering that {mystery.cause}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The clamor stopped, the nagging stopped, and everyone could laugh in the quiet afterward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clamor?",
            answer="A clamor is a loud, busy noise, like a clanking, rattling, or booming racket.",
        ),
        QAItem(
            question="What does it mean to nag?",
            answer="To nag means to keep saying the same complaint or reminder over and over.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues so they can figure out what caused the problem instead of guessing.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% This world is intentionally tiny: a valid story exists for every setting/mystery pair.
valid_story(P,M) :- place(P), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        cl = set(asp_valid())
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="barn", mystery="bell", name="Ada", gender="girl", helper="grandmother"),
    StoryParams(place="town", mystery="wagon", name="Bo", gender="boy", helper="uncle"),
    StoryParams(place="porch", mystery="jar", name="Ruby", gender="girl", helper="sister"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
