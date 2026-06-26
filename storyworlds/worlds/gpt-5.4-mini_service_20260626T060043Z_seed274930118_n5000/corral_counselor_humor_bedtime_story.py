#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/corral_counselor_humor_bedtime_story.py
================================================================================

A small bedtime-story world about a counselor at a corral, with a gentle,
humorous turn that helps a child and a sleepy animal settle down.
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

    animal: object | None = None
    child: object | None = None
    counselor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the corral"
    SETTINGS: set[str] = field(default_factory=set)
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
class Animal:
    id: str
    label: str
    type: str
    sleepy_word: str
    humor: str
    noise: str
    bed: str
    risk: str
    settles_with: str
    tags: set[str] = field(default_factory=set)
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
    animal: str
    child_name: str
    child_type: str
    counselor_name: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_sleepy(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    animal = world.get("animal")
    if child.memes.get("tired", 0.0) >= THRESHOLD and animal.memes.get("noisy", 0.0) >= THRESHOLD:
        sig = ("sleepy_noise",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"The corral grew very sleepy, but the {animal.label} was still making a silly little noise.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    counselor = world.get("counselor")
    if child.memes.get("smile", 0.0) >= THRESHOLD and counselor.memes.get("warmth", 0.0) >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("That made everybody chuckle softly, the way stars seem to twinkle when they are trying not to wake the moon.")
    return out


CAUSAL_RULES = [Rule("sleepy_noise", _r_sleepy), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {"corral": Setting(place="the corral")}

ANIMALS = {
    "pony": Animal(
        id="pony",
        label="pony",
        type="pony",
        sleepy_word="dozing",
        humor="its tail kept flicking like a feather fan",
        noise="a tiny huff",
        bed="hay bed",
        risk="being too awake for bedtime",
        settles_with="a lullaby and a lantern",
        tags={"animal", "sleep", "humor"},
    ),
    "goat": Animal(
        id="goat",
        label="goat",
        type="goat",
        sleepy_word="yawning",
        humor="its beard made it look like a very serious joke",
        noise="a little bleat",
        bed="nest of straw",
        risk="starting a midnight parade",
        settles_with="a bedtime story and a scratch behind the ear",
        tags={"animal", "sleep", "humor"},
    ),
    "donkey": Animal(
        id="donkey",
        label="donkey",
        type="donkey",
        sleepy_word="sleepy",
        humor="its ears looked like two listening umbrellas",
        noise="a funny bray",
        bed="soft straw bed",
        risk="waking up the whole lane",
        settles_with="a quiet song and a blanket",
        tags={"animal", "sleep", "humor"},
    ),
}


GIRL_NAMES = ["Mia", "Nora", "Lily", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Max", "Ben"]


def all_combos() -> list[tuple[str, str]]:
    return [("corral", a) for a in ANIMALS]


def valid_combos() -> list[tuple[str, str]]:
    return all_combos()


ASP_RULES = r"""
setting(corral).
animal(pony). animal(goat). animal(donkey).
valid(Place, Animal) :- setting(Place), animal(Animal).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("setting", "corral")] + [asp.fact("animal", a) for a in ANIMALS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="A bedtime corral story with a counselor and a gentle joke.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--counselor", choices=["counselor"], default="counselor")
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
    combos = valid_combos()
    if getattr(args, "animal", None) and getattr(args, "animal", None) not in ANIMALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    counselor_name = getattr(args, "counselor", None) or "counselor"
    return StoryParams(animal=animal, child_name=name, child_type=gender, counselor_name=counselor_name)


def bedtime_story(world: World, child: Entity, counselor: Entity, animal: Entity) -> None:
    world.say(
        f"At the corral, a little counselor named {counselor.id} kept a lantern low so the shadows could rest."
    )
    world.say(
        f"There was a {animal.label} named {animal.id}, and {animal.humor}; even the fence seemed to smile."
    )
    world.say(
        f"{child.id} had come along in pajamas and slippers, hoping for one last look before sleep."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["corral"])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    counselor = world.add(Entity(id="counselor", kind="character", type="counselor", label="counselor"))
    animal = world.add(Entity(id="animal", kind="character", type=params.animal, label=_safe_lookup(ANIMALS, params.animal).label))
    child.memes["curious"] = 1
    animal.memes["noisy"] = 1
    child.memes["tired"] = 1
    counselor.memes["warmth"] = 1
    counselor.memes["humor"] = 1

    bedtime_story(world, child, counselor, animal)
    world.para()
    world.say(
        f"The {animal.label} was supposed to settle into {_safe_lookup(ANIMALS, params.animal).bed}, but it gave one goofy sound instead."
    )
    world.say(
        f'{child.id} giggled. "That was not a scary sound," {child.pronoun()} whispered. "That was a sleepy joke."'
    )
    propagate(world)
    world.para()
    world.say(
        f'The counselor nodded and said, "Let us try {_safe_lookup(ANIMALS, params.animal).settles_with}."'
    )
    child.memes["smile"] = 1
    animal.memes["calm"] = 1
    animal.memes["noisy"] = 0
    world.say(
        f"Together they did exactly that, and soon the {animal.label} lay still in its {_safe_lookup(ANIMALS, params.animal).bed}."
    )
    world.say(
        f"{child.id} yawned, the lantern glowed like a tiny moon, and the corral grew quiet enough for bedtime."
    )

    world.facts.update(child=child, counselor=counselor, animal=animal)
    prompts = [
        f'Write a bedtime story about a counselor at a corral and a funny {animal.label}.',
        f"Tell a gentle, humorous story where {child.id} hears a silly sound in the corral and everyone ends up sleepy.",
        f'Write a short bedtime story that includes the words "corral" and "counselor".',
    ]
    story_qa = [
        QAItem(
            question=f"Who helped at the corral when {child.id} came to see the {animal.label}?",
            answer=f"The counselor helped at the corral and kept everything calm for {child.id} and the {animal.label}.",
        ),
        QAItem(
            question=f"What funny thing did the {animal.label} do before bedtime?",
            answer=f"The {animal.label} made a silly little sound instead of settling right away, which made {child.id} giggle.",
        ),
        QAItem(
            question=f"How did the story end for the {animal.label}?",
            answer=f"The {animal.label} settled into its bed of straw or hay, and the corral became quiet for sleep.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a corral?",
            answer="A corral is a fenced area where animals can stay safely in one place.",
        ),
        QAItem(
            question="What does a counselor do?",
            answer="A counselor helps people feel calm, listens carefully, and offers kind advice.",
        ),
        QAItem(
            question="Why can a silly sound be funny at bedtime?",
            answer="A silly sound can be funny because it breaks the quiet in a small, harmless way, and that surprise can make people smile.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.type:9}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="pony", child_name="Mia", child_type="girl", counselor_name="counselor"),
    StoryParams(animal="goat", child_name="Leo", child_type="boy", counselor_name="counselor"),
    StoryParams(animal="donkey", child_name="Nora", child_type="girl", counselor_name="counselor"),
]


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, animal in combos:
            print(f"  {place:8} {animal}")
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
            i += 1
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
            header = f"### {p.child_name}: {p.animal} at corral"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
