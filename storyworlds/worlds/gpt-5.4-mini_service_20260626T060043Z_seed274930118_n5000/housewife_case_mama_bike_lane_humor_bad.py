#!/usr/bin/env python3
"""
storyworlds/worlds/housewife_case_mama_bike_lane_humor_bad.py
=============================================================

A tiny tall-tale storyworld about a housewife, a case, and a mama in a bike lane.
The story aims for humor, a bad ending, and a moral value at the end.
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


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

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
    name: str
    kind: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    housewife: object | None = None
    mama: object | None = None
    def pronoun(self) -> str:
        if self.kind in {"woman", "mother", "mama", "housewife"}:
            return "she"
        return "it"

    def possessive(self) -> str:
        if self.kind in {"woman", "mother", "mama", "housewife"}:
            return "her"
        return "its"
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
    name: str
    speed: str
    danger: str
    affords: set[str] = field(default_factory=set)
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
class Case:
    label: str
    contents: str
    weight: str
    kind: str = "case"
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
    case: str
    mama: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    "bike_lane": Place(
        name="the bike lane",
        speed="fast",
        danger="bells and wobble",
        affords={"rolling", "scooting", "carting"},
    )
}

CASES = {
    "suitcase": Case(label="suitcase", contents="a pile of hats", weight="heavy"),
    "lunch_case": Case(label="lunch case", contents="jam sandwiches", weight="small"),
    "music_case": Case(label="music case", contents="a fiddle and a bow", weight="long"),
}

MAMAS = {
    "mama": Entity(name="Mama", kind="mama", role="mama"),
    "housewife": Entity(name="Housewife", kind="housewife", role="housewife"),
}

NAMES = {
    "housewife": "housewife",
    "case": "case",
    "mama": "mama",
}


# ---------------------------------------------------------------------------
# World and narration
# ---------------------------------------------------------------------------
@dataclass
class World:
    place: Place
    housewife: Entity
    mama: Entity
    case: Case
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
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


def _speak_case(world: World) -> str:
    case = world.case.label
    if case == "suitcase":
        return "the suitcase bobbed like a stubborn pumpkin"
    if case == "lunch case":
        return "the lunch case clacked like a spoon in a biscuit tin"
    return "the music case hummed like a fence full of bees"


def _moral() -> str:
    return "A road works best when everyone keeps to the right little lane."


def _setup(world: World) -> None:
    h = world.housewife
    m = world.mama
    c = world.case
    world.say(
        f"There was once a housewife named {h.name}, and {m.name} was her mama, "
        f"bigger in heart than a windmill and twice as busy."
    )
    world.say(
        f"{h.name} had a {c.label} so dear to {h.possessive()} life that "
        f"{_speak_case(world)} wherever {h.pronoun()} went."
    )
    world.say(
        f"On market morning, the whole town could hear the hum of {world.place.name}; "
        f"bikes zipped by with their shiny little whistles."
    )


def _tension(world: World) -> None:
    h = world.housewife
    m = world.mama
    c = world.case
    world.para()
    world.say(
        f"{h.name} decided the bike lane was a fine place to haul the {c.label}, "
        f"because the road looked smooth as butter on a skillet."
    )
    world.say(
        f"Then {m.name} cried, \"Child, that lane is for bicycles, not for family errands!\""
    )
    world.say(
        f"But {h.name} only laughed, and the laugh was so loud it startled a pigeon "
        f"off a lamppost."
    )
    world.say(
        f"The {c.label} wobbled into the stripe, and a cyclist rang a bell like a tiny thunderclap."
    )
    world.facts["risk"] = True
    world.facts["humor"] = "pigeon and bell"
    world.facts["mama_warned"] = True


def _turn(world: World) -> None:
    h = world.housewife
    m = world.mama
    c = world.case
    world.para()
    world.say(
        f"{m.name} tried to mend the matter by reaching for the {c.label}, but the case was "
        f"heavier than three jam jars and a teapot together."
    )
    world.say(
        f"{h.name} tugged one way, the {c.label} tugged the other, and the whole family "
        f"began to wobble like chairs in a storm."
    )
    world.say(
        f"That is when a little boy on a bicycle shouted, \"Ma'am, your errand has become "
        f"a parade!\" and even {m.name} had to chuckle."
    )
    world.facts["humor"] = "parade"
    world.facts["tug_of_war"] = True


def _ending(world: World) -> None:
    h = world.housewife
    m = world.mama
    c = world.case
    world.para()
    world.say(
        f"But the wheel caught the case, the case tipped, and out spilled {c.contents} "
        f"all over the bike lane like confetti at a sad wedding."
    )
    world.say(
        f"The cyclists swerved, the jam sandwiches smushed, and the music case sang a last "
        f"lopsided note before landing in a puddle."
    )
    world.say(
        f"{m.name} sighed and picked up the mess while {h.name} stood by, red-faced and quiet."
    )
    world.say(
        f"So the day ended badly for the {c.label}, and {h.name} learned that a joke is not "
        f"worth a broken lane or a spoiled errand."
    )
    world.say(_moral())
    world.facts["bad_ending"] = True
    world.facts["moral"] = _moral()


def tell_story(place: Place, case: Case, mama_name: str, housewife_name: str) -> World:
    world = World(
        place=place,
        housewife=Entity(name=housewife_name, kind="housewife", role="housewife"),
        mama=Entity(name=mama_name, kind="mama", role="mama"),
        case=case,
    )
    _setup(world)
    _tension(world)
    _turn(world)
    _ending(world)
    world.facts.update(place=place.name, case=case.label, mama=mama_name, housewife=housewife_name)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a tall-tale style story about a housewife, a mama, and a {world.case.label} in the bike lane.",
        f"Tell a humorous story where {world.housewife.name} ignores {world.mama.name}'s warning and the {world.case.label} causes trouble.",
        f"Make a short moral story set in the bike lane with a bad ending and a lesson about keeping clear of traffic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {world.housewife.name}, a housewife, and {world.mama.name}, her mama.",
        ),
        QAItem(
            question=f"What was {world.housewife.name} carrying in the bike lane?",
            answer=f"{world.housewife.name} was carrying a {world.case.label}.",
        ),
        QAItem(
            question=f"Why did the bike lane become a problem?",
            answer=(
                f"It became a problem because {world.housewife.name} took the {world.case.label} "
                f"into the bike lane, where bicycles were supposed to go fast and clear."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly: the {world.case.label} tipped, the contents spilled, and "
                f"{world.mama.name} had to clean up the mess."
            ),
        ),
        QAItem(
            question="What lesson does the story give?",
            answer=_moral(),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bike lane for?",
            answer="A bike lane is a part of the road meant for bicycles to travel safely and smoothly.",
        ),
        QAItem(
            question="Why can a case be hard to carry?",
            answer="A case can be hard to carry because it may be heavy, awkward, or easy to drop.",
        ),
        QAItem(
            question="Why should people keep clear of a bike lane?",
            answer="People should keep clear of a bike lane so bicycles can move safely without bumps or spills.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(bike_lane).
case(suitcase). case(lunch_case). case(music_case).
mama(mama).
housewife(housewife).

bad_ending(C) :- case(C).
humor(C) :- case(C).
moral_value(keep_clear_of_bike_lane).

valid_story(P, C, M) :- place(P), case(C), mama(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for mid in MAMAS:
        lines.append(asp.fact("mama", mid))
    lines.append(asp.fact("housewife", "housewife"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, c, m) for p in PLACES for c in CASES for m in MAMAS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python combos ({len(py_set)}).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: housewife, case, mama, bike lane.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--mama", choices=MAMAS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "bike_lane"
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    mama = getattr(args, "mama", None) or "mama"
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if case not in CASES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, case=case, mama=mama, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(CASES, params.case), params.mama, params.name or "Hettie")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place.name}")
    lines.append(f"housewife: {world.housewife.name}")
    lines.append(f"mama: {world.mama.name}")
    lines.append(f"case: {world.case.label} -> {world.case.contents}")
    for k, v in sorted(world.facts.items()):
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


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
    StoryParams(place="bike_lane", case="suitcase", mama="mama"),
    StoryParams(place="bike_lane", case="lunch_case", mama="mama"),
    StoryParams(place="bike_lane", case="music_case", mama="mama"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories")
        for row in vals:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None), 1)):
            params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
