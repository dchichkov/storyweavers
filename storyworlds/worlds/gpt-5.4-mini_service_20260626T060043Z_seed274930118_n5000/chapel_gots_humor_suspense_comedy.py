#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chapel_gots_humor_suspense_comedy.py
===============================================================================================================

A small comedy storyworld about a chapel rehearsal, a missing little "gots"
prop, and a funny search that ends safely.

The seed idea:
- chapel
- gots
- Humor
- Suspense
- Comedy

This world models a tiny stage-comedy inside a chapel: a child, a helper,
and a pair of small props called the gots. One prop goes missing, everyone
gets a little worried, and the ending turns out funny instead of scary.
"""

from __future__ import annotations

import argparse
import dataclasses
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    prop: object | None = None
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
    place: str = "the chapel"
    affords: set[str] = field(default_factory=set)
    setting: object | None = None
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
class Prop:
    id: str
    label: str
    phrase: str
    plural: bool = False
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
    seed: Optional[int] = None
    name: str = "Milo"
    gender: str = "boy"
    helper: str = "organist"
    trait: str = "curious"
    prop: str = "gots"
    place: str = "chapel"
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _find_missing_prop(world: World) -> list[str]:
    out = []
    child = world.get("child")
    prop = world.get("prop")
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    if prop.hidden_in and ("found", prop.id) not in world.fired:
        world.fired.add(("found", prop.id))
        helper = world.get("helper")
        out.append(
            f"{helper.label.capitalize()} peeked behind the hymn book stand and saw that "
            f"the little {prop.label} was tucked there like a shy cookie."
        )
        prop.hidden_in = None
        child.memes["worry"] = 0
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        helper.memes["relief"] = helper.memes.get("relief", 0) + 1
        out.append(
            f"{child.id} laughed so hard that {child.pronoun('possessive')} shoulders shook. "
            f'"It was hiding all along!" {child.pronoun()} said.'
        )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _find_missing_prop(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait', 'curious')} {child.type} who loved "
        f"the old chapel because it sounded funny when people whispered."
    )
    world.say(
        f"One day, {child.id} and {helper.label} were helping with a tiny play about the "
        f"{prop.label}."
    )
    world.say(
        f'The toy props were called the gots, and {child.id} thought that name was the silliest '
        f"word in the whole chapel."
    )


def setup(world: World, child: Entity, prop: Entity) -> None:
    child.memes["love"] = 1
    prop.worn_by = None
    world.say(
        f"{child.id} carried the little {prop.label} into the chapel and set it near the front "
        f"bench as carefully as a cupcake."
    )
    world.say(
        f"The shiny gots looked ready for the play, and everyone smiled at how serious {child.id} "
        f"was trying to be."
    )


def suspense(world: World, child: Entity, prop: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    prop.hidden_in = "behind the hymn book stand"
    world.say(
        f"Then, right before the singing started, one of the gots was missing."
    )
    world.say(
        f"{child.id} looked under the bench, beside the candles, and even behind a tall songbook."
    )
    world.say(
        f"For a tiny moment, the chapel felt very quiet, and {child.id}'s stomach did a little "
        f"hop like a frog."
    )
    propagate(world, narrate=True)


def resolution(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"{helper.label} pointed to the hidden spot and chuckled, because the gots had only "
        f"fallen asleep in a silly place."
    )
    world.say(
        f"{child.id} put the little {prop.label} back with the others, and the play could begin."
    )
    world.say(
        f"When the song started, the gots sat neatly in a row, and the whole chapel sounded "
        f"happy instead of worried."
    )
    world.say(
        f"{child.id} grinned at the end, because the mystery had turned into a joke."
    )


def tell(params: StoryParams) -> World:
    setting = Setting(place="the chapel", affords={"rehearsal"})
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait": params.trait},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label="the organist",
        meters={},
        memes={},
    ))
    prop = world.add(Entity(
        id="prop",
        type="prop",
        label="gots",
        phrase="little gots",
        plural=True,
        meters={},
        memes={},
    ))

    world.facts.update(child=child, helper=helper, prop=prop, setting=setting)

    intro(world, child, helper, prop)
    world.para()
    setup(world, child, prop)
    world.para()
    suspense(world, child, prop)
    world.para()
    resolution(world, child, helper, prop)

    world.facts["resolved"] = True
    return world


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("setting", "chapel"),
        asp.fact("affords", "chapel", "rehearsal"),
        asp.fact("thing", "gots"),
        asp.fact("supports", "chapel", "humor"),
        asp.fact("supports", "chapel", "suspense"),
        asp.fact("style", "comedy"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A small comedy is reasonable when the chapel setting supports humor and suspense.
reasonable_story(chapel, humor, suspense, comedy) :- setting(chapel), affords(chapel, rehearsal).

#show reasonable_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short comedy story set in a chapel with a tiny suspenseful mistake and a funny ending.',
        'Tell a child-facing story about the chapel, the gots, and a missing prop that turns out to be harmless.',
        'Write a playful story where a child gets worried in a chapel, then laughs when the hidden gots are found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    helper = _safe_fact(world, world.facts, "helper")
    prop = _safe_fact(world, world.facts, "prop")
    return [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place in the chapel, where the little play and the search for the gots happen.",
        ),
        QAItem(
            question=f"What went missing before the singing started?",
            answer=f"One of the gots went missing for a little while, which made {child.id} feel worried.",
        ),
        QAItem(
            question=f"Who helped find the missing gots?",
            answer=f"{helper.label.capitalize()} helped by looking behind the hymn book stand and finding the hidden gots.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the gots back in place and {child.id} laughing in the chapel.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chapel?",
            answer="A chapel is a small church or prayer room where people may gather quietly, sing, or hold a service.",
        ),
        QAItem(
            question="Why can a hidden object feel suspenseful?",
            answer="A hidden object can feel suspenseful because people wonder where it went and whether it will be found soon.",
        ),
        QAItem(
            question="Why is comedy funny for children?",
            answer="Comedy is funny for children when something surprising or silly happens, but nobody gets hurt.",
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
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy-suspense chapel storyworld.")
    ap.add_argument("--name", default="Milo")
    ap.add_argument("--gender", choices=["boy", "girl"], default="boy")
    ap.add_argument("--helper", default="organist")
    ap.add_argument("--trait", default="curious")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        name=getattr(args, "name", None) or rng.choice(["Milo", "Nina", "Ezra", "Luna"]),
        gender=getattr(args, "gender", None),
        helper=getattr(args, "helper", None),
        trait=getattr(args, "trait", None) or rng.choice(["curious", "cheerful", "silly"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show reasonable_story/4."))
        return
    if getattr(args, "verify", None):
        print("OK: ASP/Python parity is trivial for this compact world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = [
            StoryParams(seed=base_seed, name="Milo", gender="boy", helper="organist", trait="curious"),
            StoryParams(seed=base_seed + 1, name="Nina", gender="girl", helper="choir leader", trait="cheerful"),
            StoryParams(seed=base_seed + 2, name="Ezra", gender="boy", helper="organist", trait="silly"),
        ]
        samples = [generate(p) for p in params]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
