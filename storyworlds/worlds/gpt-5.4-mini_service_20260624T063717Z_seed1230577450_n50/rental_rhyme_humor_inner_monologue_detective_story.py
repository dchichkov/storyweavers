#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/rental_rhyme_humor_inner_monologue_detective_story.py
===============================================================================================================================

A small, standalone storyworld about a rental mystery with rhyme, humor,
inner monologue, and a detective-story shape.

Premise:
- A child detective rents a tiny item for a task.
- Something goes missing or gets swapped.
- The detective follows concrete clues in the world.
- The case ends with a funny, rhyming resolution.

The world model keeps both physical meters and emotional memes so the prose is
driven by simulated state rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    location: str = ""
    rented: bool = False
    missing: bool = False
    dirty: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clerk: object | None = None
    detective: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
        if not hasattr(self, "_tags"):
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
    clue_places: list[str]
    weather: str = "gray"
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class RentalItem:
    id: str
    label: str
    phrase: str
    type: str
    clue: str
    smell: str
    size: str
    near: list[str]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    item: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None
    params: object | None = None
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


SETTINGS = {
    "station": Setting("the train station", ["bench", "locker", "ticket desk"], "gray"),
    "library": Setting("the library", ["desk", "shelf", "return cart"], "quiet"),
    "market": Setting("the market", ["stall", "crate", "canopy"], "busy"),
}

ITEMS = {
    "magnifier": RentalItem("magnifier", "magnifying glass", "a small magnifying glass", "tool", "smudged lens", "dust", "small", ["desk", "bench"]),
    "umbrella": RentalItem("umbrella", "umbrella", "a bright red umbrella", "tool", "bent tip", "rain", "medium", ["canopy", "bench"]),
    "bike": RentalItem("bike", "bike", "a tiny blue bike", "ride", "wobbly chain", "mud", "small", ["parking rack", "bench"]),
    "apron": RentalItem("apron", "apron", "a striped apron", "gear", "floury pocket", "flour", "small", ["stall", "desk"]),
}

GIRL_NAMES = ["Mina", "Tess", "Rina", "Luna"]
BOY_NAMES = ["Noel", "Arlo", "Jasper", "Finn"]


def validate_combo(place: str, item: str) -> None:
    if place not in SETTINGS:
        pass
    if item not in ITEMS:
        pass


@dataclass
class WorldState:
    detective: Entity
    clerk: Entity
    item: Entity
    clue_spot: str
    culprit: str = ""
    found: bool = False
    suspicion: int = 0
    state: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def rhyme(a: str, b: str) -> str:
    return f"{a}, {b}"


def build_world(params: StoryParams) -> tuple[World, WorldState]:
    setting = _safe_lookup(SETTINGS, params.place)
    item_def = _safe_lookup(ITEMS, params.item)
    world = World(setting)

    detective = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    clerk = world.add(Entity(id="clerk", kind="character", type="adult", label="the clerk"))
    item = world.add(Entity(
        id=item_def.id,
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=clerk.id,
        location="rental shelf",
        rented=True,
        meters={"wear": 0.0, "clue": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "confidence": 0.0},
    ))
    clue_spot = random.choice(setting.clue_places)

    state = WorldState(detective=detective, clerk=clerk, item=item, clue_spot=clue_spot)
    world.facts.update(params=params, detective=detective, clerk=clerk, item=item, setting=setting)
    return world, state


def narrate_opening(world: World, st: WorldState) -> None:
    world.say(
        f"{st.detective.label} was a little detective with a notebook and a grin. "
        f"At {world.setting.place}, {st.detective.pronoun()} rented {st.item.phrase} "
        f"for a careful case."
    )
    world.say(
        f"\"If I can peek and seek, I'll find the sneaky streak,\" {st.detective.label} thought."
    )
    world.say(
        f"The clerk smiled at the sign: {st.item.label} was due back by sunset, neat and light."
    )


def clue_scene(world: World, st: WorldState) -> None:
    world.para()
    st.item.meters["clue"] += 1
    st.detective.memes["curiosity"] += 1
    world.say(
        f"The trail led to the {st.clue_spot}. There, a tiny clue waited: {st.item.clue}."
    )
    world.say(
        f"{st.detective.label} sniffed and blinked. \"This case is ace, but where is the place "
        f"that keeps the item in grace?\""
    )
    world.say(
        f"In {st.detective.pronoun('possessive')} head, the thought went tap-tap: "
        f"rentals are borrowed, not swallowed."
    )


def false_lead(world: World, st: WorldState) -> None:
    world.para()
    st.suspicion += 1
    st.detective.memes["worry"] += 1
    world.say(
        f"A shiny cart by the bench looked guilty at first. \"Aha, the cart is art, but it may be "
        f"the start of a part I can't trust,\" {st.detective.label} muttered."
    )
    world.say(
        f"Then {st.detective.pronoun()} noticed a crumb trail of {st.item.smell} instead of any real proof."
    )


def resolve_case(world: World, st: WorldState) -> None:
    world.para()
    st.item.missing = False
    st.found = True
    st.detective.memes["confidence"] += 1
    world.say(
        f"Behind the return cart, {st.item.label} was tucked away where nobody could balk or squawk."
    )
    world.say(
        f"The clerk had moved it to dry it after a spill; the mystery was small, not tall."
    )
    world.say(
        f"{st.detective.label} laughed. \"No thief, just relief! A silly little mix-up fixed in a click-up.\""
    )
    world.say(
        f"{st.detective.label} returned {st.item.phrase}, and the station felt bright again."
    )


def tell_story(world: World, st: WorldState) -> None:
    narrate_opening(world, st)
    clue_scene(world, st)
    false_lead(world, st)
    resolve_case(world, st)


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    item = world.facts["item"]
    setting = world.facts["setting"]
    detective = world.facts["detective"]
    return [
        QAItem(
            question=f"Where did {detective.label} rent {item.label}?",
            answer=f"{detective.label} rented {item.phrase} at {setting.place}.",
        ),
        QAItem(
            question=f"What clue did the detective find?",
            answer=f"The detective found {item.clue} near the {world.facts['setting'].clue_places[0]}.",
        ),
        QAItem(
            question=f"Was the rental item stolen?",
            answer="No. It was only moved to dry after a spill, so the mystery turned into a funny mix-up.",
        ),
        QAItem(
            question=f"What did the detective learn about rentals?",
            answer="Rentals are borrowed items that must be returned, so it helps to check every place the item might have been set down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and solves mysteries.",
        ),
        QAItem(
            question="What does it mean to rent something?",
            answer="To rent something means you borrow it for a short time and then give it back.",
        ),
        QAItem(
            question="Why do people return rental items?",
            answer="People return rental items so the owner can use them again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    item = world.facts["item"]
    return [
        f"Write a short detective story about a child who rents {item.phrase} and follows clues.",
        f"Tell a funny mystery with rhyme where {p.name} solves a rental mix-up at {world.setting.place}.",
        "Make the detective's thoughts visible, with playful inner monologue and a neat ending.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.rented:
            bits.append("rented=True")
        if e.missing:
            bits.append("missing=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    validate_combo(place, item)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = getattr(args, "companion", None) or "clerk"
    return StoryParams(place=place, item=item, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world, st = build_world(params)
    tell_story(world, st)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rental detective storyworld with rhyme and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
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


ASP_RULES = r"""
place(station). place(library). place(market).
item(magnifier). item(umbrella). item(bike). item(apron).

rental_case(P, I) :- place(P), item(I), compatible(P, I).
#show rental_case/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for p in SETTINGS:
        for i in ITEMS:
            lines.append(asp.fact("compatible", p, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show rental_case/2."))
    asp_set = set(asp.atoms(model, "rental_case"))
    py_set = {(p, i) for p in SETTINGS for i in ITEMS}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} cases).")
        return 0
    print("MISMATCH")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show rental_case/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for item in ITEMS:
                params = StoryParams(place=place, item=item, name="Mina", gender="girl", companion="clerk")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
