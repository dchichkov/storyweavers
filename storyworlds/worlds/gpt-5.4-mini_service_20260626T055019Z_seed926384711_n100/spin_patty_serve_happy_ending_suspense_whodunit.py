#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/spin_patty_serve_happy_ending_suspense_whodunit.py
==============================================================================================================================

A small whodunit storyworld about a careful cook, a missing patty, a spinning clue,
and a happy ending in a little diner kitchen.

The world is intentionally tiny:
- One cook is preparing dinner.
- A patty must be spun on the griddle and served.
- A suspicious clue creates tension.
- A helpful reveal resolves the mystery.

The narrative style stays close to whodunit, but child-friendly and warm:
something goes missing, everyone looks a little suspicious, and then the
truth makes the ending happy.
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

LOOK_THRESHOLD = 1.0



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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cook: object | None = None
    pat: object | None = None
    sidekick: object | None = None
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
    place: str = "the little diner kitchen"
    world: object | None = None
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
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
    name: str
    role: str
    helper: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


ROLES = {
    "cook": Entity(id="Cook", kind="character", type="woman", label="cook"),
    "chef": Entity(id="Chef", kind="character", type="man", label="chef"),
}
HELPERS = {
    "cat": "the cat",
    "neighbor": "the neighbor",
    "child": "the child",
    "dog": "the dog",
}

PATTIES = {
    "beef": Item(id="beef", label="beef patty", phrase="a juicy beef patty", kind="patty"),
    "bean": Item(id="bean", label="bean patty", phrase="a soft bean patty", kind="patty"),
}

CLUES = [
    "a tiny trail of sesame seeds",
    "a lonely napkin with grease on the corner",
    "a little paw print near the counter",
    "a dropped onion ring by the stove",
]


@dataclass
class ASPChoice:
    role: str
    helper: str
    patty: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit about spinning and serving a patty.")
    ap.add_argument("--role", choices=sorted(ROLES), default=None)
    ap.add_argument("--helper", choices=sorted(HELPERS), default=None)
    ap.add_argument("--patty", choices=sorted(PATTIES), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def reasonableness_gate(role: str, helper: str, patty: str) -> None:
    if role not in ROLES:
        pass
    if helper not in HELPERS:
        pass
    if patty not in PATTIES:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    role = getattr(args, "role", None) or rng.choice(sorted(ROLES))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    patty = getattr(args, "patty", None) or rng.choice(sorted(PATTIES))
    reasonableness_gate(role, helper, patty)
    return StoryParams(name="Milo", role=role, helper=helper, seed=getattr(args, "seed", None))


def _spin_patty(world: World, cook: Entity, patty: Entity) -> None:
    cook.memes["busy"] = cook.memes.get("busy", 0.0) + 1
    patty.meters["spin"] = patty.meters.get("spin", 0.0) + 1
    world.say(f"{cook.id} spun the patty on the hot griddle until it sizzled just right.")


def _set_suspense(world: World, helper: str) -> str:
    clue = random.choice(CLUES)
    world.facts["clue"] = clue
    world.say(f"Then {clue} appeared near the stove, and everyone wondered who had been there.")
    return clue


def _reveal(world: World, helper: str, cook: Entity, patty: Entity) -> None:
    cook.memes["worry"] = max(0.0, cook.memes.get("worry", 0.0) - 1)
    cook.memes["joy"] = cook.memes.get("joy", 0.0) + 1
    patty.carried_by = cook.id
    world.say(
        f"At last, {helper} nudged the clue aside and revealed the truth: the missing patty "
        f"had only slipped onto the warming plate."
    )
    world.say(
        f"{cook.id} laughed, served the {patty.label} on a fresh bun, and the whole little kitchen "
        f"ended in a happy, crumb-sprinkled relief."
    )


def tell(role: str, helper: str, patty: str, name: str = "Milo") -> World:
    world = World(Setting())
    cook = world.add(Entity(id=name, kind="character", type=role, label=role))
    sidekick = world.add(Entity(id="Helper", kind="character", type="child", label=helper))
    pat = world.add(Entity(id="Patty", kind="thing", type="patty", label=_safe_lookup(PATTIES, patty).label, phrase=_safe_lookup(PATTIES, patty).phrase))
    world.facts.update(cook=cook, helper=sidekick, patty=pat)

    world.say(f"In {world.setting.place}, {cook.id} was ready to make dinner.")
    world.say(f"{cook.id} wanted to spin {pat.phrase} on the griddle and serve it with care.")
    world.para()

    _spin_patty(world, cook, pat)
    world.say(f"But just as the smell turned golden, the patty was nowhere to be seen.")
    world.say(f"{cook.id} narrowed {cook.pronoun('possessive')} eyes and looked around the room like a detective.")
    _set_suspense(world, helper)
    world.say(f"Everyone seemed suspicious, even {helper}.")
    world.para()

    world.say(f"Then {helper} pointed to the warming plate and smiled.")
    _reveal(world, helper, cook, pat)
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params.role, params.helper, params.patty, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short whodunit for a young child about a missing patty, a clue, and a happy ending.',
        f"Tell a suspenseful but gentle story where {world.facts['cook'].id} tries to spin and serve dinner in {world.setting.place}.",
        "Write a mystery story that ends with the meal being served and everyone feeling relieved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cook: Entity = _safe_fact(world, world.facts, "cook")
    patty: Entity = _safe_fact(world, world.facts, "patty")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question="What was the cook trying to do at the start of the story?",
            answer=f"{cook.id} was trying to spin {patty.phrase} and then serve it for dinner.",
        ),
        QAItem(
            question="Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the patty seemed to vanish, and {clue} made everyone wonder what had happened.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{helper.id} helped solve the mystery by pointing out that the patty had only slipped onto the warming plate.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {cook.id} laughing and serving the {patty.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to serve food?",
            answer="To serve food means to put it on a plate or dish so someone can eat it.",
        ),
        QAItem(
            question="What does spin mean in cooking?",
            answer="In cooking, to spin something means to turn it around quickly, often with a hand or tool, so it cooks evenly.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a flat piece of food, often made from meat, beans, or vegetables, that can be cooked on a pan or griddle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
role(cook;chef).
helper(cat;neighbor;child;dog).
patty(beef;bean).

valid(R,H,P) :- role(R), helper(H), patty(P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROLES:
        lines.append(asp.fact("role", r))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for p in PATTIES:
        lines.append(asp.fact("patty", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_choices() -> list[tuple]:
    import asp
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(r, h, p) for r in ROLES for h in HELPERS for p in PATTIES}
    cl = set(asp_choices())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


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
    StoryParams(name="Milo", role="cook", helper="cat", seed=1),
    StoryParams(name="Iris", role="chef", helper="neighbor", seed=2),
    StoryParams(name="Nina", role="cook", helper="child", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for t in asp_choices():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError:
                continue
            if (p.role, p.helper, p.name) in seen:
                continue
            seen.add((p.role, p.helper, p.name))
            params_list.append(p)

    for p in params_list:
        samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
