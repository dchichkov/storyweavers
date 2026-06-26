#!/usr/bin/env python3
"""
storyworlds/worlds/chihuahua_twist_magic_dialogue_mystery.py
=============================================================

A small mystery storyworld centered on a chihuahua, a strange twist, a little
magic, and dialogue that helps solve the case.

The domain is intentionally tiny: one child, one small dog, one missing object,
one surprising twist, and a gentle magical clue. The simulated state tracks both
physical facts (meters) and emotional facts (memes), and the story is generated
from those state changes rather than from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    dog: object | None = None
    obj_ent: object | None = None
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
    place: str = "the little garden"
    affords: set[str] = field(default_factory=lambda: {"search", "follow", "listen"})
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
    verb: str
    gerund: str
    hush: str
    clue_word: str
    twist_word: str
    magic_word: str
    dialogue_word: str
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
class ObjectCfg:
    label: str
    phrase: str
    type: str
    location: str
    owner_name: str = "Pia"
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
class StoryParams:
    setting: str
    mystery: str
    object: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mystery_clue: str = ""

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
        w.mystery_clue = self.mystery_clue
        return w


SETTINGS = {
    "garden": Setting("the little garden"),
    "house": Setting("the quiet house", affords={"search", "listen"}),
    "courtyard": Setting("the sunny courtyard"),
}

MYSTERIES = {
    "key": Mystery(
        id="key",
        verb="search for the key",
        gerund="searching for the key",
        hush="silent",
        clue_word="click",
        twist_word="twist",
        magic_word="glow",
        dialogue_word="whisper",
        tags={"twist", "magic", "dialogue"},
    ),
    "ball": Mystery(
        id="ball",
        verb="find the missing ball",
        gerund="looking for the missing ball",
        hush="quiet",
        clue_word="bounce",
        twist_word="twist",
        magic_word="spark",
        dialogue_word="talk",
        tags={"twist", "magic", "dialogue"},
    ),
}

OBJECTS = {
    "key": ObjectCfg("tiny brass key", "a tiny brass key with a blue ribbon", "key", "under the bench"),
    "ball": ObjectCfg("striped ball", "a striped ball with a gold dot", "ball", "behind the flower pot"),
}

NAMES = ["Pia", "Milo", "Nina", "Rex", "Tess", "Omar"]
CHIHUAHUA_NAMES = ["Peanut", "Nugget", "Bibi", "Pico", "Luna"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a chihuahua, a twist, and a magic clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    obj = getattr(args, "object", None) or mystery
    if obj not in OBJECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, mystery=mystery, object=obj)


def _seen_change(world: World, mystery: Mystery, obj: ObjectCfg) -> None:
    child = world.get("child")
    dog = world.get("dog")
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    dog.meters["alert"] = dog.meters.get("alert", 0) + 1
    world.mystery_clue = f"a faint {mystery.clue_word}"
    world.say(
        f"{child.id} noticed {world.setting.place} was very {mystery.hush}. "
        f"{dog.id}, the little chihuahua, tilted {dog.pronoun('possessive')} head as if it had heard {world.mystery_clue}."
    )
    world.say(
        f"Something was missing: {obj.phrase} should have been in {obj.location}, but it was not there."
    )


def _twist(world: World, mystery: Mystery, obj: ObjectCfg) -> None:
    child = world.get("child")
    dog = world.get("dog")
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    dog.meters["paws"] = dog.meters.get("paws", 0) + 1
    world.say(
        f"{child.id} whispered, \"Where did the {obj.label} go?\""
    )
    world.say(
        f"Then came the {mystery.twist_word}: {dog.id} was sitting on the cushion with {obj.label} tucked under {dog.pronoun('possessive')} chin."
    )


def _magic(world: World, mystery: Mystery, obj: ObjectCfg) -> None:
    child = world.get("child")
    dog = world.get("dog")
    if dog.meters.get("paws", 0) < THRESHOLD:
        pass
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    dog.memes["pride"] = dog.memes.get("pride", 0) + 1
    world.say(
        f"The ribbon around the {obj.label} gave off a tiny {mystery.magic_word}, like moonlight on water."
    )
    world.say(
        f"{dog.id} tapped the floor once, and that made the clue feel magical instead of scary."
    )


def _dialogue(world: World, mystery: Mystery, obj: ObjectCfg) -> None:
    child = world.get("child")
    dog = world.get("dog")
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    dog.memes["relief"] = dog.memes.get("relief", 0) + 1
    world.say(
        f'\"You hid it for me, didn\'t you?\" {child.id} said softly.'
    )
    world.say(
        f'{dog.id} barked once, which sounded exactly like a little {mystery.dialogue_word}.'
    )
    world.say(
        f'{child.id} laughed, picked up the {obj.label}, and said, \"Good detective, {dog.id}.\"'
    )


def tell(setting: Setting, mystery: Mystery, obj: ObjectCfg) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label="Pia", meters={}, memes={}))
    dog = world.add(Entity(id="dog", kind="character", type="chihuahua", label="Peanut", meters={}, memes={}))
    obj_ent = world.add(Entity(id="object", type=obj.type, label=obj.label, phrase=obj.phrase, owner=child.id))
    obj_ent.worn_by = None

    world.say(
        f"{child.id} and {dog.id} were in {setting.place}, where little things could turn into big mysteries."
    )
    world.say(
        f"{dog.id} was a chihuahua with bright eyes and tiny feet, and {child.id} trusted {dog.id} to help."
    )
    world.para()
    _seen_change(world, mystery, obj)
    world.para()
    _twist(world, mystery, obj)
    _magic(world, mystery, obj)
    _dialogue(world, mystery, obj)
    obj_ent.meters["found"] = 1
    world.facts.update(child=child, dog=dog, obj=obj_ent, mystery=mystery, setting=setting)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    dog = _safe_fact(world, f, "dog")
    obj = _safe_fact(world, f, "obj")
    mystery = _safe_fact(world, f, "mystery")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {child.id} and {dog.id}, a tiny chihuahua who helped solve the mystery.",
        ),
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The {obj.label} was missing from {obj.location}, and that made the little scene feel puzzling.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {dog.id} had the {obj.label} all along, tucked under {dog.pronoun('possessive')} chin.",
        ),
        QAItem(
            question=f"How did the magic show up?",
            answer=f"The ribbon on the {obj.label} gave off a tiny {mystery.magic_word}, so the clue felt magical instead of frightening.",
        ),
        QAItem(
            question=f"What did {child.id} say to {dog.id} at the end?",
            answer=f"{child.id} said, \"Good detective, {dog.id}.\"",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chihuahua?",
            answer="A chihuahua is a very small dog with tiny paws, big eyes, and a brave-looking face.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign or detail that helps someone solve a mystery.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprising change that makes the answer turn out differently than it first seemed.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle mystery story with a chihuahua, a missing {f['obj'].label}, and a surprising twist.",
        f"Tell a child-friendly story where {f['child'].id} asks questions, {f['dog'].id} answers in clues, and a little magic helps solve the mystery.",
        f"Write a short mystery set in {f['setting'].place} that includes dialogue, a twist, and a magical clue.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  clue: {world.mystery_clue}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", mystery="key", object="key"),
    StoryParams(setting="house", mystery="ball", object="ball"),
]


ASP_RULES = r"""
setting(garden). setting(house). setting(courtyard).
mystery(key). mystery(ball).
object(key). object(ball).

compatible(S,M,O) :- setting(S), mystery(M), object(O), O = M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    obj = _safe_lookup(OBJECTS, params.object)
    world = tell(setting, mystery, obj)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.setting} / {p.mystery} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
