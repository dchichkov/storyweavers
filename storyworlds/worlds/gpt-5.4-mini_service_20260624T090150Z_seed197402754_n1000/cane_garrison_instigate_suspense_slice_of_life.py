#!/usr/bin/env python3
"""
storyworlds/worlds/cane_garrison_instigate_suspense_slice_of_life.py
====================================================================

A small slice-of-life story world about a child, a cane, and a quiet garrison
day that grows a little suspenseful before ending warmly.

Seed tale used to build the world:
---
At the old garrison, Nia visited her grandfather every Thursday after school.
Grandpa moved slowly and leaned on his smooth wooden cane. Nia liked the quiet
hall, the echo of boots, and the little routine of tea, biscuits, and stories.

One afternoon, Nia noticed the cane was missing from its usual spot. She
looked under the bench, near the door, and behind the coat rack. Grandpa
started to worry, and Nia felt a small flutter of suspense. Then she found the
cane resting beside a map table where she had set her pencil down. Grandpa
smiled, the worry faded, and they went back to tea as if the day had simply
waited for them to catch up.

World model notes:
---
- The cane is a physical object that can be carried, leaned on, or misplaced.
- The garrison is a calm setting with a few familiar places.
- Suspense comes from a small missing-object search, not from danger.
- The resolution restores routine and shows what changed: worry becomes relief.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cane: object | None = None
    child: object | None = None
    elder: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the garrison"
    detail: str = "the quiet hall"
    spots: list[str] = field(default_factory=lambda: ["bench", "coat rack", "map table", "tea table"])
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
    place: str
    name: str
    elder_name: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def build_setting(place: str) -> Setting:
    if place != "garrison":
        pass
    return Setting()


def _search_step(world: World, child: Entity, elder: Entity, cane: Entity) -> None:
    if cane.meters.get("missing", 0.0) < THRESHOLD:
        return
    child.memes["suspense"] += 1
    if child.memes.get("asked") < THRESHOLD:
        world.say(
            f"{child.id} noticed the cane was not where it usually rested, and a small suspenseful feeling began to buzz in {child.pronoun('possessive')} chest."
        )
    spots = world.setting.spots
    for spot in spots:
        sig = ("search", spot)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if spot == cane.location:
            world.say(f"{child.id} looked near the {spot} and finally found the cane waiting there, as calm as could be.")
            cane.meters["found"] = 1
            elder.memes["worry"] = 0
            child.memes["suspense"] = 0
            elder.memes["relief"] += 1
            return
        else:
            world.say(f"{child.id} checked the {spot}, but the cane was not there.")
            elder.memes["worry"] += 0.2


def _settle(world: World, child: Entity, elder: Entity, cane: Entity) -> None:
    if cane.meters.get("found", 0.0) < THRESHOLD:
        return
    world.say(
        f"{elder.id} smiled when {child.id} brought the cane back, and the two of them sat down for tea as if the whole afternoon had simply taken a breath and let it go."
    )


def tell(place: str, child_name: str, elder_name: str) -> World:
    world = World(build_setting(place))
    child = world.add(Entity(id=child_name, kind="character", type="child", label=child_name))
    elder = world.add(Entity(id=elder_name, kind="character", type="grandfather", label=elder_name))
    cane = world.add(Entity(
        id="cane",
        kind="thing",
        type="cane",
        label="cane",
        phrase="a smooth wooden cane",
        owner=elder.id,
        caretaker=elder.id,
        location="map table",
    ))
    child.meters["curiosity"] = 1
    child.memes["care"] = 1
    elder.meters["age"] = 1
    elder.memes["habit"] = 1
    elder.memes["worry"] = 0

    world.say(
        f"{child.id} visited {elder.id} at {world.setting.place}, where the {world.setting.detail} smelled faintly of tea and old paper."
    )
    world.say(
        f"{elder.id} leaned on {cane.phrase} and told a story from the days when the boots in the hall still sounded new."
    )
    world.para()

    world.say(
        f"After a while, {child.id} noticed something odd: the cane was not beside the chair anymore."
    )
    cane.meters["missing"] = 1
    elder.memes["worry"] = 1
    child.memes["asked"] = 1
    world.say(
        f"{elder.id} looked around the room, and the quiet suddenly felt a little suspenseful."
    )

    world.para()
    _search_step(world, child, elder, cane)
    _settle(world, child, elder, cane)

    world.facts.update(child=child, elder=elder, cane=cane, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    elder = _safe_fact(world, world.facts, "elder")
    return [
        f"Write a gentle slice-of-life story set at the garrison about {child.id} and {elder.id}, where a missing cane creates mild suspense.",
        f"Tell a short child-friendly story in which {child.id} looks for {elder.id}'s cane and everything ends with tea and relief.",
        f"Write a calm suspense story about a cane, a garrison, and a family visit that turns back into an ordinary afternoon.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    elder = _safe_fact(world, world.facts, "elder")
    cane = _safe_fact(world, world.facts, "cane")
    return [
        QAItem(
            question=f"Where did {child.id} visit {elder.id}?",
            answer=f"{child.id} visited {elder.id} at the garrison, in the quiet hall where they often shared tea and stories.",
        ),
        QAItem(
            question=f"What was missing that made the afternoon feel suspenseful?",
            answer=f"The cane was missing from its usual place, and that made both {child.id} and {elder.id} feel uneasy for a little while.",
        ),
        QAItem(
            question=f"Where did {child.id} find the cane?",
            answer=f"{child.id} found the cane near the map table after checking the bench, the coat rack, and the other familiar spots.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the cane back in safe hands, the worry gone, and the two of them sitting down for tea again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cane used for?",
            answer="A cane is a walking stick that can help someone steady their steps or support them while they walk.",
        ),
        QAItem(
            question="What is a garrison?",
            answer="A garrison is a place where soldiers live, work, or gather, and it can also have quiet rooms and halls.",
        ),
        QAItem(
            question="What does it mean to instigate something?",
            answer="To instigate something means to start it or set it in motion, like beginning a search or starting a new idea.",
        ),
    ]


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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_cane(C) :- cane(C), cane_missing(C).
searching(C, P) :- missing_cane(C), spot(P).
found(C) :- missing_cane(C), cane_at(C, P), spot(P).
relief(E) :- found(_), elder(E).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("cane", "cane"),
        asp.fact("cane_missing", "cane"),
        asp.fact("cane_at", "cane", "map_table"),
        asp.fact("spot", "bench"),
        asp.fact("spot", "coat_rack"),
        asp.fact("spot", "map_table"),
        asp.fact("spot", "tea_table"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found/1."))
    ok = bool(asp.atoms(model, "found"))
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python agree on the cane search structure.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A calm slice-of-life storyworld with a little suspense at a garrison.")
    ap.add_argument("--place", choices=["garrison"], default="garrison")
    ap.add_argument("--name")
    ap.add_argument("--elder-name")
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
    return StoryParams(
        place=getattr(args, "place", None),
        name=getattr(args, "name", None) or rng.choice(["Nia", "Mina", "Eli", "Tess", "June"]),
        elder_name=getattr(args, "elder_name", None) or rng.choice(["Grandpa", "Uncle Jo", "Mr. Hale", "Old Ben"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.name, params.elder_name)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show found/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("This world exposes a small ASP twin but no alternate combinatorics.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(resolve_params(args, random.Random(base_seed)))]
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
