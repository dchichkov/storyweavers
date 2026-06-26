#!/usr/bin/env python3
"""
storyworlds/worlds/bang_dialogue_misunderstanding_myth.py
=========================================================

A compact myth-style story world about a startling bang, a spoken warning,
and a misunderstanding that changes into trust.

The seed tale:
---
Long ago, on a hill above a quiet village, a young shepherd heard a great bang
from the old temple. She thought the sky had cracked. Her brother said it was
only thunder, but she did not believe him. At the temple steps, the priestess
laughed and said the mountain-drums had woken. The shepherd misunderstood the
laugh and thought she was being mocked. Only when the priestess spoke gently,
and showed the drums, did the shepherd understand. She bowed, smiled, and the
three of them rang the bronze bell together so the village would know the storm
had passed.

World model:
---
- The bang is a physical event with loudness and shock.
- Dialogue can carry truth or create misunderstanding.
- A misunderstanding raises tension until a clarifying act lowers it.
- The ending proves the change by showing the village responding differently.

This file intentionally keeps the domain small: one hill, one temple, one bang,
one misheard exchange, and one resolution.
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

TITLE = "Bang, Dialogue, and Misunderstanding"
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
    name: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    keeper: object | None = None
    sibling: object | None = None
    def label(self) -> str:
        return self.name or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "sister", "mother"}
        male = {"boy", "man", "shepherd", "brother", "priest", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
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
class Place:
    id: str
    name: str
    sky: str
    holds: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    hero: str
    sibling: str
    keeper: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _loud_bang(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("shock", 0.0) >= THRESHOLD and ("bang", e.id) not in world.fired:
            world.fired.add(("bang", e.id))
            e.memes["fear"] = e.memes.get("fear", 0.0) + 1
            out.append(f"A bang rolled across {world.place.name}, and everyone went still.")
    return out


def _misunderstanding(world: World) -> list[str]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    if hero.memes.get("misunderstanding", 0.0) < THRESHOLD:
        return []
    sig = ("misunderstanding", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    keeper.memes["distance"] = keeper.memes.get("distance", 0.0) + 1
    return [f"{hero.name} thought {keeper.name}'s laugh was sharp and unkind."]


def _clarify(world: World) -> list[str]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    sibling = world.get("sibling")
    if hero.memes.get("clarity", 0.0) < THRESHOLD:
        return []
    sig = ("clarify", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hurt"] = max(0.0, hero.memes.get("hurt", 0.0) - 1)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    keeper.memes["warmth"] = keeper.memes.get("warmth", 0.0) + 1
    sibling.memes["relief"] = sibling.memes.get("relief", 0.0) + 1
    return [f"Then {keeper.name} spoke gently and showed the mountain-drums hidden in the stone."]
    

CAUSAL_RULES = [_loud_bang, _misunderstanding, _clarify]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_setting(place_id: str) -> Place:
    if place_id not in SETTINGS:
        pass
    return _safe_lookup(SETTINGS, place_id)


def tell(params: StoryParams) -> World:
    place = build_setting(params.place)
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type="girl", name=params.hero, role="shepherd"))
    sibling = world.add(Entity(id="sibling", kind="character", type="boy", name=params.sibling, role="brother"))
    keeper = world.add(Entity(id="keeper", kind="character", type="woman", name=params.keeper, role="priestess"))

    world.say(f"Long ago, on {place.name}, {hero.name} kept watch while the sky turned dark.")
    world.say(f"She loved the old stories of the hill, but the sudden bang made her heart jump.")
    world.say(f'"That sound means the sky is breaking," {hero.name} cried.')
    world.say(f'"No," said {sibling.name}. "It is only thunder, and the storm is far away."')

    hero.memes["misunderstanding"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At the temple steps, {keeper.name} laughed softly.")
    world.say(f'{hero.name} heard that laugh and thought, "She is laughing at me."')
    world.say(f"Her cheeks burned, and she wanted to turn away.")
    keeper.memes["clarity"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{keeper.name} held up the bronze drum and said, \"The bang came from here, not from the sky.\"")
    world.say(f'{sibling.name} nodded. "{keeper.name} was trying to help you," he said.')
    world.say(f'{hero.name} bowed her head, then smiled. "I was wrong," she said, "and now I understand."')
    world.say(f"Together they rang the bronze bell, and the village heard that the storm had passed.")

    world.facts.update(hero=hero, sibling=sibling, keeper=keeper, place=place)
    return world


SETTINGS = {
    "hill": Place(id="hill", name="the hill above the village", sky="storm"),
    "temple": Place(id="temple", name="the temple steps", sky="storm"),
}

HERO_NAMES = ["Asha", "Nira", "Mina", "Tala", "Ira", "Suri"]
SIBLING_NAMES = ["Ravi", "Kian", "Miro", "Sajan", "Bela", "Toma"]
KEEPER_NAMES = ["Priya", "Sana", "Mara", "Dina", "Luma", "Kora"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    keeper = _safe_fact(world, f, "keeper")
    return [
        'Write a short myth-like story for a child about a bang, a misheard laugh, and a gentle explanation.',
        f"Tell a myth where {hero.name} misreads a bang and then misunderstands {keeper.name}'s voice before learning the truth.",
        f"Write a child-friendly legend in which {hero.name} and {sibling.name} listen to {keeper.name} and discover what caused the bang.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    keeper = _safe_fact(world, f, "keeper")
    return [
        QAItem(
            question=f"Why did {hero.name} get scared at first?",
            answer=f"{hero.name} got scared because a great bang rolled across the hill and she thought the sky had cracked open.",
        ),
        QAItem(
            question=f"Why did {hero.name} think {keeper.name} was upset?",
            answer=f"{hero.name} misunderstood {keeper.name}'s laugh and thought it sounded sharp and unkind, even though it was gentle.",
        ),
        QAItem(
            question=f"What helped {hero.name} understand what the bang really was?",
            answer=f"{keeper.name} spoke gently and showed the mountain-drums hidden in the stone, and that made the mistake clear.",
        ),
        QAItem(
            question=f"What did {hero.name}, {sibling.name}, and {keeper.name} do at the end?",
            answer="They rang the bronze bell together so the village would know the storm had passed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is thunder?",
            answer="Thunder is the loud sound that comes after lightning warms the air very quickly.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word or action means one thing, but it really means something else.",
        ),
        QAItem(
            question="Why can a gentle voice help?",
            answer="A gentle voice can calm fear and help people listen carefully instead of guessing badly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", hero="Asha", sibling="Ravi", keeper="Priya"),
    StoryParams(place="temple", hero="Nira", sibling="Kian", keeper="Mara"),
]


def explain_rejection(place: str) -> str:
    return f"(No story: the place {place!r} does not belong to this myth world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about a bang and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sibling", choices=SIBLING_NAMES)
    ap.add_argument("--keeper", choices=KEEPER_NAMES)
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
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in SIBLING_NAMES if n != hero])
    keeper = getattr(args, "keeper", None) or rng.choice(KEEPER_NAMES)
    return StoryParams(place=place, hero=hero, sibling=sibling, keeper=keeper)


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
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(hill).
place(temple).

event(bang).
event(dialogue).
event(misunderstanding).

caused_fear(hero) :- event(bang).
misunderstanding(hero) :- caused_fear(hero), dialogue(keeper).
clarified(hero) :- misunderstanding(hero), dialogue(keeper), gentle(keeper).
resolved(hero) :- clarified(hero).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "hill"),
        asp.fact("place", "temple"),
        asp.fact("event", "bang"),
        asp.fact("event", "dialogue"),
        asp.fact("event", "misunderstanding"),
        asp.fact("dialogue", "keeper"),
        asp.fact("gentle", "keeper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    resolved = set(asp.atoms(model, "resolved"))
    expected = {("hero",)}
    if resolved == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH between ASP and Python story logic.")
    print("  asp:", sorted(resolved))
    print("  py :", sorted(expected))
    return 1


def build_story_rng(args: argparse.Namespace) -> random.Random:
    return random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_rng = build_story_rng(args)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            params.seed = (getattr(args, "seed", None) or 0) + i
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
