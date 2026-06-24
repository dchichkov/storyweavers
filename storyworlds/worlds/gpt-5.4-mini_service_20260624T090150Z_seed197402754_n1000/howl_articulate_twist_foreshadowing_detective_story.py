#!/usr/bin/env python3
"""
storyworlds/worlds/howl_articulate_twist_foreshadowing_detective_story.py
==========================================================================

A small detective-story world about a missing object, a careful sleuth, a
foreshadowed clue, and one clean twist.

Premise:
- A child detective notices something strange.
- A warning sound, a howl, hints that the answer is close.
- The detective must articulate the clues instead of guessing.
- The twist is that the "suspect" is not a thief at all, but the item hiding
  in an obvious place that was missed because everyone looked for the wrong kind
  of shadow.

This world keeps the prose concrete and state-driven: clues are collected, a
notebook is filled, and the final reveal depends on what was actually found.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    foreshadow: object | None = None
    hero: object | None = None
    item: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "detective"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    time: str
    ambient: str
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
class Case:
    missing_item: str
    suspect_noise: str
    clue_place: str
    twist_place: str
    reveal_phrase: str
    foreshadow_phrase: str
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
    setting: str
    case: str
    name: str
    sidekick: str
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
SETTINGS = {
    "library": Setting(place="the old library", time="evening", ambient="The lamps glowed softly between tall shelves."),
    "garden": Setting(place="the back garden", time="late afternoon", ambient="Leaves rustled over the stone path."),
    "attic": Setting(place="the attic", time="night", ambient="The ceiling beams creaked above dusty boxes."),
}

CASES = {
    "bell": Case(
        missing_item="silver bell",
        suspect_noise="a long howl outside the window",
        clue_place="under the reading rug",
        twist_place="inside a toy house",
        reveal_phrase="the bell was hiding where the smallest hands could not see it",
        foreshadow_phrase="the bell-shaped toy house on the shelf",
    ),
    "lantern": Case(
        missing_item="yellow lantern",
        suspect_noise="a lonely howl from the garden",
        clue_place="behind the watering can",
        twist_place="in the garden shed",
        reveal_phrase="the lantern had been tucked away for safety",
        foreshadow_phrase="the shed door that kept swinging open",
    ),
    "key": Case(
        missing_item="tiny brass key",
        suspect_noise="a sharp howl in the attic wind",
        clue_place="near the coat pocket",
        twist_place="under the patchwork quilt",
        reveal_phrase="the key was never stolen, only dropped in a sleepy place",
        foreshadow_phrase="the quilt with the stitched key pattern",
    ),
}

NAMES = ["Maya", "Noah", "Lena", "Theo", "Ivy", "Finn", "Nora", "Eli"]
SIDEKICKS = ["cat", "dog", "brother", "sister", "friend"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def intro_line(hero: Entity, setting: Setting) -> str:
    return f"{hero.id} was a little detective who liked quiet places and careful clues."


def articulate_line(hero: Entity, clue: str) -> str:
    return f'{hero.pronoun().capitalize()} could not guess the answer right away, so {hero.pronoun("subject")} chose to articulate the clue aloud: "{clue}."'  # noqa: E501


def howl_line(case: Case) -> str:
    return f"Then there was a howl nearby, and it made everyone look up at once."


def foreshadow_line(case: Case) -> str:
    return f"That strange noise seemed to point toward {case.foreshadow_phrase}."


def reveal_line(case: Case) -> str:
    return f"In the end, {case.reveal_phrase}."


def final_image(hero: Entity, item: Entity, setting: Setting) -> str:
    return f"{hero.id} tucked {item.label} back in place, and the room felt calm again under {setting.ambient.lower()}"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
missing(Case, Item) :- case(Case), item(Item), case_item(Case, Item).
noise_points_to(Case, Place) :- case(Case), clue_place(Case, Place).
foreshadowed(Case, Thing) :- case(Case), foreshadow(Case, Thing).
twist(Case) :- case(Case), twist_place(Case, Place), found_at(Case, Place).

valid_story(Setting, Case) :- setting(Setting), case(Case).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("case_item", cid, c.missing_item.replace(" ", "_")))
        lines.append(asp.fact("clue_place", cid, c.clue_place.replace(" ", "_")))
        lines.append(asp.fact("twist_place", cid, c.twist_place.replace(" ", "_")))
        lines.append(asp.fact("foreshadow", cid, c.foreshadow_phrase.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, c) for s in SETTINGS for c in CASES)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python registries:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="detective"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="friend"))
    item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type="object",
        label=case.missing_item,
        phrase=f"the {case.missing_item}",
        owner=hero.id,
        location="hidden",
        hidden=True,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label="clue card",
        phrase="a small clue card",
        location=case.clue_place,
        hidden=False,
    ))
    foreshadow = world.add(Entity(
        id="foreshadow",
        kind="thing",
        type="thing",
        label="toy house",
        phrase=case.foreshadow_phrase,
        location=case.twist_place,
        hidden=False,
    ))

    # Act 1: setup.
    world.say(intro_line(hero, setting))
    world.say(f"{setting.ambient}")
    world.say(f"{hero.id} and the {sidekick.type} were searching for the {item.label}.")
    world.say(f"Something small and strange felt important, because {case.foreshadow_phrase} was already there.")

    # Act 2: foreshadowing and investigation.
    world.para()
    world.say(howl_line(case))
    world.say(f"{hero.id} paused and listened.")
    world.say(articulate_line(hero, f"I hear a howl, but that does not mean someone is guilty"))
    world.say(foreshadow_line(case))
    world.say(f"{hero.id} checked {case.clue_place} and found the clue card.")
    clue.meters["found"] = 1
    hero.memes["certainty"] += 1
    world.say(f"The clue said the missing thing was near the place that had looked too ordinary to matter.")

    # Act 3: twist and reveal.
    world.para()
    world.say(f"{hero.id} went to {case.twist_place}.")
    item.location = case.twist_place
    item.hidden = False
    world.facts["found_at"] = case.twist_place
    world.say(f"{hero.id} found the {item.label} there.")
    world.say(f"That was the twist: the howl was only a warning sound, and the real answer was hiding in plain sight.")
    world.say(reveal_line(case))
    world.say(final_image(hero, item, setting))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        item=item,
        clue=clue,
        foreshadow=foreshadow,
        setting=setting,
        case=case,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    case = _safe_fact(world, f, "case")
    return [
        f'Write a short detective story for a young child that includes the word "howl" and a gentle mystery about a missing {case.missing_item}.',
        f"Tell a story where {hero.id} must articulate the clues carefully before the twist is revealed.",
        f"Write a simple detective tale with foreshadowing, a howl, and a happy ending where the missing {case.missing_item} is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    case = _safe_fact(world, f, "case")
    item = _safe_fact(world, f, "item")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What was {hero.id} trying to find in {setting.place}?",
            answer=f"{hero.id} was trying to find the {item.label}.",
        ),
        QAItem(
            question=f"What sound made the detective stop and listen?",
            answer=f"A howl made {hero.id} stop and listen carefully.",
        ),
        QAItem(
            question=f"What clue was already hinting at the answer?",
            answer=f"The {case.foreshadow_phrase} was a clue that hinted the answer was nearby.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the missing {item.label} was not stolen at all; it was hiding in the place everyone had overlooked.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} listened to the howl, articulated the clue out loud, checked the right place, and then found the missing {item.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure something out.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early on about what will matter later.",
        ),
        QAItem(
            question="What does articulate mean?",
            answer="To articulate something means to say it clearly and carefully so other people can understand it.",
        ),
        QAItem(
            question="What is a howl?",
            answer="A howl is a long, loud cry that can sound spooky or lonely, like a wolf calling out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} {e.kind:8} {e.type:10} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with a howl, foreshadowing, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    if setting not in SETTINGS or case not in CASES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, case=case, name=name, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(setting="library", case="bell", name="Maya", sidekick="cat"),
    StoryParams(setting="garden", case="lantern", name="Noah", sidekick="dog"),
    StoryParams(setting="attic", case="key", name="Lena", sidekick="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.case} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
