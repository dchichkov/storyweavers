#!/usr/bin/env python3
"""
storyworlds/worlds/square_downward_kindness_dialogue_heartwarming.py
=====================================================================

A small heartwarming story world about a child in a square, a downward
problem, and a kind dialogue that helps everyone feel better.

Seed image:
---
In a town square, a child sees something drifting downward and worries it will
be lost. A kind helper notices, talks gently, and offers a simple way to help.
The child listens, acts kindly in return, and the little problem becomes a warm
moment of shared care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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

    child: object | None = None
    helper: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str = "the town square"
    affordance: str = "a place to meet and help"
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
class StoryEvent:
    name: str
    text: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    place: str = ""
    child: str = ""
    child_type: str = ""
    helper: str = ""
    helper_type: str = ""
    object: str = ""
    object_kind: str = ""
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


PLACES = {
    "square": Setting(place="the town square", affordance="meeting, music, and helpful talk"),
    "market_square": Setting(place="the market square", affordance="busy walks and friendly help"),
}

CHILDREN = [
    ("Mia", "girl"),
    ("Noah", "boy"),
    ("Luna", "girl"),
    ("Eli", "boy"),
    ("Ava", "girl"),
]

HELPERS = [
    ("Mrs. Reed", "woman"),
    ("Mr. Park", "man"),
    ("Nana Jo", "woman"),
    ("Uncle Ben", "man"),
]

OBJECTS = {
    "balloon": ("a red balloon", "balloon"),
    "paper_plane": ("a paper plane", "paper plane"),
    "kite": ("a small kite", "kite"),
    "apple": ("a shiny apple from a basket", "apple"),
}


TRAITS = ["gentle", "curious", "patient", "kind", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(square).
place(market_square).

child(mia). child(noah). child(luna). child(eli). child(ava).
helper(mrs_reed). helper(mr_park). helper(nana_jo). helper(uncle_ben).

object(balloon). object(paper_plane). object(kite). object(apple).

kind_child(mia). kind_child(luna). kind_child(ava).
kind_helper(mrs_reed). kind_helper(nana_jo).
kind_helper(mr_park). kind_helper(uncle_ben).

usable(square, balloon).
usable(square, paper_plane).
usable(square, kite).
usable(square, apple).
usable(market_square, balloon).
usable(market_square, paper_plane).
usable(market_square, kite).
usable(market_square, apple).

valid_story(P, C, H, O) :- place(P), child(C), helper(H), object(O), usable(P, O).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in PLACES:
        lines.append(asp.fact("place", k))
    for name, typ in CHILDREN:
        lines.append(asp.fact("child", name.lower()))
        if typ in {"girl", "boy"}:
            lines.append(asp.fact("gender", name.lower(), typ))
    for name, typ in HELPERS:
        lines.append(asp.fact("helper", name.lower().replace(" ", "_")))
        lines.append(asp.fact("gender", name.lower().replace(" ", "_"), typ))
    for k in OBJECTS:
        lines.append(asp.fact("object", k))
    for p in PLACES:
        for o in OBJECTS:
            lines.append(asp.fact("usable", p, o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_stories())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo matches python ({len(python_set)} stories).")
        return 0
    print("MISMATCH:")
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for child, _ in CHILDREN:
            for helper, _ in HELPERS:
                for obj in OBJECTS:
                    out.append((place, child, helper, obj))
    return out


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: the {obj} does not fit this gentle square scene.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(PLACES, params.place)
    w = World(setting)

    child = w.add(Entity(id=params.child, kind="character", type=params.child_type))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    obj_label, obj_kind = _safe_lookup(OBJECTS, params.object)
    obj = w.add(Entity(
        id=params.object,
        kind="thing",
        type=obj_kind,
        label=obj_kind,
        phrase=obj_label,
        owner=child.id,
        caretaker=helper.id,
    ))

    child.memes["worry"] = 1.0
    helper.memes["kindness"] = 1.0
    w.facts.update(child=child, helper=helper, obj=obj, params=params)
    return w


def tell_story(w: World) -> None:
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    helper: Entity = w.facts["helper"]  # type: ignore[assignment]
    obj: Entity = w.facts["obj"]  # type: ignore[assignment]
    params: StoryParams = w.facts["params"]  # type: ignore[assignment]

    place = w.setting.place
    w.say(
        f"One afternoon, {child.id} walked into {place} with {obj.phrase} tucked close."
    )
    w.say(
        f"The square felt busy and bright, full of footsteps, pigeons, and soft music."
    )

    w.para()
    w.say(
        f"Then {child.id} noticed something drifting downward near the fountain, and {child.pronoun()} felt a small worry in {child.pronoun('possessive')} chest."
    )
    w.say(
        f"{child.id} looked up and said, 'Oh no, it's going downward! I don't want it to be lost.'"
    )

    w.para()
    w.say(
        f"{helper.id} heard the little voice, came over slowly, and said, 'We can help together.'"
    )
    w.say(
        f"{child.id} answered, 'Will you show me what to do?' and {helper.id} smiled."
    )
    w.say(
        f"'Yes,' {helper.id} said. 'Let's stand by the bench and watch carefully.'"
    )

    w.para()
    w.say(
        f"So {child.id} and {helper.id} spoke kindly, one gentle sentence at a time, until the drifting thing settled safely."
    )
    w.say(
        f"{child.id} reached out, and instead of grabbing in a rush, {child.pronoun()} helped with a careful hand."
    )
    w.say(
        f"The square felt warmer after that, as if the whole place had taken a happy breath."
    )

    w.para()
    w.say(
        f"{child.id} laughed, because the downward problem had turned into a shared moment of kindness."
    )
    w.say(
        f"Together they watched {obj.phrase} stay safe, and {helper.id} waved as {child.id} went home smiling."
    )
    w.facts["resolved"] = True


def generation_prompts(w: World) -> list[str]:
    p: StoryParams = w.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story in a square where {p.child} notices something going downward and gets help.",
        f"Tell a gentle dialogue story about {p.child} and {p.helper} in the {w.setting.place} with kindness at the center.",
        f"Write a small child-friendly story about a downward worry that becomes a kind shared moment.",
    ]


def story_qa(w: World) -> list[QAItem]:
    p: StoryParams = w.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {p.child} meet {p.helper}?",
            answer=f"{p.child} met {p.helper} in {w.setting.place}, where people could stop, talk, and help each other.",
        ),
        QAItem(
            question=f"What worried {p.child} in the story?",
            answer=f"{p.child} worried because something was going downward and might get lost, so {p.child} wanted help.",
        ),
        QAItem(
            question=f"How did {p.helper} help?",
            answer=f"{p.helper} spoke kindly, stayed calm, and showed {p.child} a safe way to help.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the problem felt smaller, {p.child} felt safer, and the square felt warm and happy again.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a square?",
            answer="A square can be an open place in a town where people walk, meet, and do things together.",
        ),
        QAItem(
            question="What does downward mean?",
            answer="Downward means moving toward a lower place, like falling or going down.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to be gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="Why is dialogue useful?",
            answer="Dialogue is useful because talking can help people understand each other and solve a problem calmly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(w: World) -> str:
    lines = ["--- world trace ---"]
    for e in w.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming square/downward kindness story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--object", choices=OBJECTS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    child, child_type = rng.choice(CHILDREN)
    helper, helper_type = rng.choice(HELPERS)
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    if getattr(args, "child", None):
        child = getattr(args, "child", None)
    if getattr(args, "helper", None):
        helper = getattr(args, "helper", None)
    return StoryParams(
        place=place,
        child=child,
        child_type=child_type,
        helper=helper,
        helper_type=helper_type,
        object=obj,
        object_kind=_safe_lookup(OBJECTS, obj)[1],
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(place="square", child="Mia", child_type="girl", helper="Mrs. Reed", helper_type="woman", object="balloon"),
    StoryParams(place="square", child="Noah", child_type="boy", helper="Mr. Park", helper_type="man", object="paper_plane"),
    StoryParams(place="market_square", child="Luna", child_type="girl", helper="Nana Jo", helper_type="woman", object="kite"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories[:50]:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
