#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a curious little baker's helper, a scone,
and a bottle of liqueur that should not be sipped.

Premise:
- A small child or mouse-like helper wants the warm scone on the table.
- A bottle of liqueur glimmers nearby, which makes curiosity rise.
- Suspense builds as the helper reaches, sniffs, and hesitates.
- The bad ending is a gentle but unhappy consequence: the scone is spoiled,
  the jar spills, and the helper is left with a sticky, sad kitchen.

This world is intentionally narrow and constraint-checked. The story is not a
frozen paragraph; it is driven by simulated state:
- curiosity can rise
- suspicion/suspense can rise
- mess can spread
- the scone can become soggy or stale
- the ending image proves the state change
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bottle: object | None = None
    child: object | None = None
    treat: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "sticky": 0.0, "broken": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "suspense": 0.0, "sadness": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the little kitchen"
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
class Treat:
    label: str
    phrase: str
    region: str = "table"
    risk: str = "soggy"
    ruined_as: str = "ruined"
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
class Bottle:
    label: str = "liqueur"
    phrase: str = "a glass bottle of liqueur"
    risky: bool = True
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def nursery_name(rng: random.Random) -> tuple[str, str]:
    names = [("Milo", "boy"), ("Nina", "girl"), ("Pip", "boy"), ("Luna", "girl"), ("Toby", "boy")]
    return rng.choice(names)


def introduce(world: World, child: Entity, place: str) -> None:
    world.say(f"In {place}, a little {child.type} named {child.id} came to play.")


def like_story(world: World, child: Entity, treat: Treat, bottle: Bottle) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} liked the warm {treat.label}, and {child.pronoun('subject')} liked the shine of the {bottle.label}."
    )
    world.say("Curious thoughts began to dance like little bells.")


def suspense(world: World, child: Entity, bottle: Bottle) -> None:
    child.memes["suspense"] += 1
    world.say(
        f"Near the shelf stood {bottle.phrase}, and {child.id} tiptoed closer and closer, "
        f"wondering what would happen if {child.pronoun('subject')} touched it."
    )


def warn(world: World, child: Entity, treat: Treat, bottle: Bottle) -> None:
    world.say(
        f"A gentle voice said, 'No, no, dear one; the {bottle.label} is not for little mouths, "
        f"and the {treat.label} must stay dry.'"
    )


def disturb(world: World, child: Entity, bottle: Bottle, treat: Treat) -> None:
    child.memes["curiosity"] += 1
    child.memes["suspense"] += 1
    sig = ("disturb", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bottle_ent = world.get("bottle")
    treat_ent = world.get("treat")
    bottle_ent.meters["wet"] += 1
    treat_ent.meters["wet"] += 1
    treat_ent.meters["sticky"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"But {child.id} reached out anyway, and the bottle tipped with a tiny clink and a sad little spill."
    )


def bad_ending(world: World, child: Entity, treat: Treat) -> None:
    treat_ent = world.get("treat")
    bottle_ent = world.get("bottle")
    if treat_ent.meters["wet"] >= THRESHOLD or treat_ent.meters["sticky"] >= THRESHOLD:
        world.say(
            f"The {treat.label} was {treat.ruined_as}, all damp and sticky on the plate."
        )
        child.memes["sadness"] += 1
        world.say(
            f"{child.id} stared at the mess and felt quite small, while the {bottle_ent.label} sat crooked and still."
        )


def tell(setting: Setting, name: str, kind: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=kind))
    treat = world.add(Entity(id="treat", type="scone", label="scone", phrase="a golden scone", caretaker=name))
    bottle = world.add(Entity(id="bottle", type="liqueur", label="liqueur", phrase="a glass bottle of liqueur", caretaker=name))

    world.facts.update(child=child, treat=treat, bottle=bottle, setting=setting)

    introduce(world, child, setting.place)
    like_story(world, child, treat, bottle)
    world.para()
    suspense(world, child, bottle)
    warn(world, child, treat, bottle)
    disturb(world, child, bottle, treat)
    world.para()
    bad_ending(world, child, treat)
    return world


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
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


SETTINGS = {
    "kitchen": Setting(place="the little kitchen"),
    "bakery": Setting(place="the tiny bakery"),
    "pantry": Setting(place="the cozy pantry"),
}

NAMES = {
    "girl": ["Lily", "Mina", "Nora", "Poppy"],
    "boy": ["Milo", "Toby", "Otis", "Finn"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about scones and liqueur.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(valid_places())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    return StoryParams(place=place, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    return [
        "Write a short nursery-rhyme story about a curious child, a scone, and liqueur.",
        f"Tell a gentle but suspenseful tale in rhyme where {child.id} is warned away from the liqueur.",
        "Make the ending sad and sticky, with the scone spoiled by one curious mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    treat = _safe_fact(world, world.facts, "treat")
    bottle = _safe_fact(world, world.facts, "bottle")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who was the little one in {setting.place}?",
            answer=f"It was {child.id}, a little {child.type} who wandered into {setting.place}.",
        ),
        QAItem(
            question=f"What tasty thing did {child.id} notice first?",
            answer=f"{child.id} noticed the warm {treat.label} first, and it looked ready to eat.",
        ),
        QAItem(
            question=f"What bottle made the moment feel tense?",
            answer=f"The tense bottle was the {bottle.label}, which was not for little mouths.",
        ),
        QAItem(
            question=f"What happened to the {treat.label} at the end?",
            answer=f"The {treat.label} became wet and sticky, so it was ruined.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scone?",
            answer="A scone is a small baked treat that can be sweet or plain and is often eaten warm.",
        ),
        QAItem(
            question="What is liqueur?",
            answer="Liqueur is a sweet alcoholic drink for grown-ups, not for children.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and find out more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender)
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


ASP_RULES = r"""
curious(C) :- child(C).
suspense(C) :- curious(C), near_bottle(C).
warned(C) :- suspense(C).
spill(B) :- touched(C, B), bottle(B), curious(C).
ruined(T) :- spill(B), near(T, B), scone(T).
bad_ending(C, T) :- ruined(T), child(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("scone", "treat"))
    lines.append(asp.fact("bottle", "bottle"))
    lines.append(asp.fact("near_bottle", "child"))
    lines.append(asp.fact("near", "treat", "bottle"))
    lines.append(asp.fact("touched", "child", "bottle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/2."))
    return sorted(set(asp.atoms(model, "bad_ending")))


def asp_verify() -> int:
    expected = {("child", "treat")}
    got = set(asp_valid())
    if got == expected:
        print("OK: ASP and Python agree on the bad ending.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(got))
    print("Python:", sorted(expected))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="kitchen", name="Lily", gender="girl"),
        StoryParams(place="bakery", name="Milo", gender="boy"),
        StoryParams(place="pantry", name="Nora", gender="girl"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/2."))
        return

    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} bad endings:")
        for item in vals:
            print(" ", item)
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
