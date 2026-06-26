#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coat_repetition_mystery_to_solve_bravery_mystery.py
================================================================================================

A small mystery storyworld about a missing coat, repeated clues, and a brave
child who solves the puzzle.

Premise:
- A child loves a special coat.
- The coat keeps disappearing from the expected place.
- The child notices repeated clues: a soft swish, a cold spot, a trail, a
  helpful echo from a friend, or a tiny shiny button.
- The child must be brave enough to look carefully and ask questions.
- The ending proves what changed: the coat is found and the mystery is solved.

This world keeps the setting small and concrete: a home, a hallway, a porch,
a closet, or a school cubby. The prose is generated from world state rather
than a fixed paragraph template.
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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "home": {
        "place": "at home",
        "rooms": ["the hallway", "the closet", "the porch"],
    },
    "school": {
        "place": "at school",
        "rooms": ["the classroom", "the cubby area", "the coat hook"],
    },
    "library": {
        "place": "at the library",
        "rooms": ["the front table", "the reading corner", "the coat rack"],
    },
}

COAT_STYLES = {
    "red": {
        "label": "red coat",
        "phrase": "a bright red coat",
        "detail": "bright as a berry",
    },
    "blue": {
        "label": "blue coat",
        "phrase": "a soft blue coat",
        "detail": "cool as rain",
    },
    "yellow": {
        "label": "yellow coat",
        "phrase": "a sunny yellow coat",
        "detail": "cheerful as a lamp",
    },
    "green": {
        "label": "green coat",
        "phrase": "a neat green coat",
        "detail": "fresh as leaves",
    },
}

CLUES = {
    "swish": {
        "meter": "heard",
        "meme": "curiosity",
        "text": "a soft swish in the next room",
    },
    "button": {
        "meter": "seen",
        "meme": "curiosity",
        "text": "a tiny button on the floor",
    },
    "trail": {
        "meter": "tracked",
        "meme": "focus",
        "text": "a little trail leading toward the porch",
    },
    "echo": {
        "meter": "heard",
        "meme": "hope",
        "text": "an echo from someone calling from the hallway",
    },
    "tag": {
        "meter": "noticed",
        "meme": "focus",
        "text": "the coat tag peeking out from under a chair",
    },
}

HIDING_PLACES = {
    "closet": "the closet",
    "hook": "the coat hook",
    "basket": "the basket",
    "chair": "the chair",
    "porch": "the porch bench",
}

NAMES = {
    "girl": ["Mia", "Nora", "Lina", "Ruby", "June", "Ivy"],
    "boy": ["Eli", "Noah", "Finn", "Leo", "Owen", "Sam"],
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
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


class World:
    def __init__(self, setting_key: str):
        self.setting_key = setting_key
        self.setting = _safe_lookup(SETTINGS, setting_key)
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    coat: str
    clue: str
    child_name: str
    gender: str
    sibling_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story mechanics
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


THRESHOLD = 1.0


def _append_repeat(world: World, child: Entity, clue: str) -> None:
    child.memes["repetition"] = child.memes.get("repetition", 0.0) + 1
    world.say(f"Again and again, {clue} seemed to show up.")


def _mystery_pressure(world: World, child: Entity) -> None:
    child.memes["mystery"] = child.memes.get("mystery", 0.0) + 1
    world.say(f"{child.pronoun().capitalize()} knew something was odd, but not yet what it was.")


def _brave_step(world: World, child: Entity) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
    world.say(f"{child.pronoun().capitalize()} took a brave breath and looked closer.")


def _solve(world: World, child: Entity, coat: Entity, hiding_place: str) -> None:
    coat.hidden = False
    coat.location = world.setting["place"]
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["mystery"] = 0.0
    world.say(
        f"At last, {child.pronoun('subject')} found {child.pronoun('possessive')} {coat.label} in {hiding_place}."
    )
    world.say(
        f"The mystery was solved, and the missing coat was right where the repeated clues had led {child.pronoun('object')}."
    )


def tell(world: World) -> World:
    child = world.get("child")
    sibling = world.get("sibling")
    coat = world.get("coat")
    clue_key = (world.facts.get("clue") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "clue"))
    clue_text = _safe_lookup(CLUES, clue_key)["text"]
    hiding_place = _safe_fact(world, world.facts, "hiding_place")

    # Beginning
    world.say(
        f"{child.id} had {child.pronoun('possessive')} {coat.phrase}, and {coat.label} was {coat.style_detail}."
    )
    world.say(
        f"One day, {child.id} could not find the coat where it should have been."
    )
    world.para()

    # Middle: repeated clues and a growing mystery
    world.say(
        f"{child.id} looked in {world.setting['rooms'][0]}, then in {world.setting['rooms'][1]}, then in {world.setting['rooms'][2]}."
    )
    _append_repeat(world, child, clue_text)
    _mystery_pressure(world, child)
    world.say(f"Each time, the same clue returned: {clue_text}.")
    world.say(f"{sibling.id} noticed it too and pointed toward the hiding place.")
    world.para()

    # Turn: bravery to search carefully
    _brave_step(world, child)
    world.say(
        f"{child.id} crouched down, listened, and asked the right questions instead of guessing."
    )
    world.say(
        f"That brave choice helped {child.pronoun('object')} follow the clue without getting scared."
    )
    world.para()

    # Resolution
    _solve(world, child, coat, hiding_place)
    world.say(
        f"In the end, {child.id} wore {coat.label} again, and the whole day felt warm and safe."
    )

    world.facts.update(
        child=child,
        sibling=sibling,
        coat=coat,
        clue=clue_key,
        hiding_place=hiding_place,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(params.setting)
    style = _safe_lookup(COAT_STYLES, params.coat)
    clue = params.clue

    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.gender,
            label=params.child_name,
            meters={},
            memes={},
        )
    )
    sibling = world.add(
        Entity(
            id=params.sibling_name,
            kind="character",
            type="character",
            label=params.sibling_name,
            meters={},
            memes={},
        )
    )
    coat = world.add(
        Entity(
            id="coat",
            kind="thing",
            type="coat",
            label=style["label"],
            phrase=style["phrase"],
            owner=child.id,
            location=_safe_lookup(HIDING_PLACES, world.facts.get("hiding_place", "closet")),
            hidden=True,
            meters={"clean": 1.0},
            memes={},
        )
    )
    coat.style_detail = style["detail"]  # type: ignore[attr-defined]

    world.facts["clue"] = clue
    world.facts["hiding_place"] = random.choice(list(HIDING_PLACES.values()))
    return world


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    coat = getattr(args, "coat", None) or rng.choice(list(COAT_STYLES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    sibling_name = getattr(args, "sibling", None) or rng.choice(NAMES["girl" if gender == "boy" else "boy"])
    if child_name == sibling_name:
        sibling_name = rng.choice([n for n in NAMES["girl"] + NAMES["boy"] if n != child_name])
    return StoryParams(
        setting=setting,
        coat=coat,
        clue=clue,
        child_name=child_name,
        gender=gender,
        sibling_name=sibling_name,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return choose_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    coat = _safe_fact(world, f, "coat")
    clue = _safe_fact(world, f, "clue")
    return [
        f"Write a short mystery story for young children about {child.id}, a missing {coat.label}, and the clue '{clue}'.",
        f"Tell a gentle story where repeated clues lead {child.id} to find {coat.label} again.",
        f"Write a brave little mystery about a child, a coat, and a puzzle that gets solved by careful looking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    coat = _safe_fact(world, f, "coat")
    sibling = _safe_fact(world, f, "sibling")
    clue = _safe_fact(world, f, "clue")
    hiding_place = _safe_fact(world, f, "hiding_place")
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {coat.phrase}, which {child.id} cared about and wanted to wear again.",
        ),
        QAItem(
            question=f"What clue kept coming back?",
            answer=f"The repeated clue was {_safe_lookup(CLUES, clue)['text']}. That clue helped guide the search.",
        ),
        QAItem(
            question=f"Who helped notice the clue?",
            answer=f"{sibling.id} helped notice the clue and point toward the right place.",
        ),
        QAItem(
            question=f"Where was the coat found?",
            answer=f"It was found in {hiding_place}, which was the place the clues were leading toward.",
        ),
        QAItem(
            question=f"How did {child.id} solve the mystery?",
            answer=f"{child.id} stayed brave, looked carefully, and followed the repeated clue until the coat was found.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coat for?",
            answer="A coat helps keep a person warm when the air is chilly or windy.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or uncertain even while you feel nervous.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you have to think about and solve.",
        ),
        QAItem(
            question="Why can repetition help in a mystery?",
            answer="When a clue repeats, it can help someone notice a pattern and understand where to look next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} hidden={e.hidden} location={e.location} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting, coat, and clue exist.
valid_story(S, C, L) :- setting(S), coat_style(C), clue(L).

% The mystery is meaningful when the coat can be hidden somewhere and a clue exists.
meaningful(C, L) :- coat_style(C), clue(L).

#show valid_story/3.
#show meaningful/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in COAT_STYLES:
        lines.append(asp.fact("coat_style", c))
    for l in CLUES:
        lines.append(asp.fact("clue", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, c, l) for s in SETTINGS for c in COAT_STYLES for l in CLUES}
    clingo_set = set(asp_valid())
    if python_set != clingo_set:
        print("MISMATCH between Python and ASP.")
        print("only python:", sorted(python_set - clingo_set))
        print("only asp:", sorted(clingo_set - python_set))
        return 1
    print(f"OK: ASP and Python agree on {len(python_set)} story combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a missing coat.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--coat", choices=list(COAT_STYLES))
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
    StoryParams(setting="home", coat="red", clue="swish", child_name="Mia", gender="girl", sibling_name="Eli"),
    StoryParams(setting="school", coat="blue", clue="button", child_name="Noah", gender="boy", sibling_name="Ivy"),
    StoryParams(setting="library", coat="yellow", clue="trail", child_name="Lina", gender="girl", sibling_name="Sam"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{x}" for x in asp_valid()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
