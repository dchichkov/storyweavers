#!/usr/bin/env python3
"""
storyworlds/worlds/atrocious_problem_solving_mystery.py
=======================================================

A small storyworld for a child-sized mystery: an atrocious little problem,
careful clue-watching, and a satisfying solve.

Premise:
- A child notices something important has gone missing or gone wrong.
- The clues feel atrocious: muddled, messy, or misleading at first.
- The child and a helper look closely, test a guess, and discover the truth.
- The ending proves the problem was solved by attention, not magic.

The world keeps the mystery grounded in physical clues and emotional states:
curiosity, worry, suspicion, relief, and pride.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    clue_spots: list[str]
    outdoors: bool = False
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
class Mystery:
    id: str
    missing: str
    reason: str
    culprit: str
    clue: str
    search_word: str
    test_word: str
    reveal_word: str
    result: str
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
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting("the kitchen", ["table", "sink", "cupboard", "floor"], outdoors=False),
    "library": Setting("the little library", ["shelf", "reading nook", "return basket", "window"], outdoors=False),
    "garden": Setting("the garden shed", ["bench", "hook", "box", "doorstep"], outdoors=False),
    "porch": Setting("the porch", ["step", "doormat", "chair", "railing"], outdoors=True),
}

MYSTERIES = {
    "missing_spoon": Mystery(
        id="missing_spoon",
        missing="silver spoon",
        reason="the spoon was needed for pudding",
        culprit="the puppy",
        clue="a shiny trail to the dog bed",
        search_word="search",
        test_word="tap",
        reveal_word="fetch",
        result="the spoon was under a blanket by the puppy",
    ),
    "missing_bookmark": Mystery(
        id="missing_bookmark",
        missing="paper bookmark",
        reason="the bookmark held the place in a storybook",
        culprit="the cat",
        clue="tiny claw marks on the rug",
        search_word="look",
        test_word="follow",
        reveal_word="peek",
        result="the bookmark was tucked behind the chair by the cat",
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="brass key",
        reason="the key opened a small tin box",
        culprit="the wind",
        clue="a flutter of paper near the window",
        search_word="investigate",
        test_word="check",
        reveal_word="open",
        result="the key had blown into the flower pot",
    ),
    "missing_marble": Mystery(
        id="missing_marble",
        missing="glass marble",
        reason="the marble was part of a counted set",
        culprit="the little brother",
        clue="a soft rattle in a toy truck",
        search_word="inspect",
        test_word="shake",
        reveal_word="count",
        result="the marble was rolling inside the toy truck",
    ),
}

TRAITS = ["curious", "careful", "brave", "quiet", "bright", "patient"]
GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ivy", "June", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Eli", "Noah", "Ben", "Sam"]
HELPERS = ["mother", "father", "grandma", "grandpa"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery story is reasonable if the missing thing can plausibly be found
% in one of the setting's clue spots.
reasonable(S, M) :- setting(S), mystery(M), has_spot(S, _), clue_fit(S, M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in s.clue_spots:
            lines.append(asp.fact("has_spot", sid, spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("clue_fit", "kitchen", mid))
        lines.append(asp.fact("clue_fit", "library", mid))
        lines.append(asp.fact("clue_fit", "garden", mid))
        lines.append(asp.fact("clue_fit", "porch", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {mystery} does not fit the mystery style for {setting}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _hero_label(hero: Entity) -> str:
    return hero.id


def introduce(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait']} {hero.type} who noticed tiny things "
        f"that other people skipped over."
    )
    world.say(
        f"One day, {hero.pronoun('possessive')} {mystery.missing} went missing, "
        f"and that made the whole room feel atrocious and wrong."
    )


def worry(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} frowned and began to {mystery.search_word}. "
        f"{hero.pronoun().capitalize()} and {helper.id} both wanted the clue to make sense."
    )


def inspect_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"They found {mystery.clue}, which looked atrocious at first because it "
        f"seemed to point everywhere at once."
    )
    world.say(
        f"Still, {hero.id} decided to {mystery.test_word} the clue instead of guessing."
    )


def test_theory(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["suspicion"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} suggested they {mystery.test_word} the place where the clue "
        f"made the most sense. {hero.id} tried that idea carefully."
    )


def reveal(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"That was the right move. {mystery.result}, and {mystery.culprit} had been the reason "
        f"the problem looked so strange."
    )
    world.say(
        f"{hero.id} laughed, because the answer was simple once the clues were lined up."
    )
    world.say(
        f"By the end, the missing {mystery.missing} was back, and the atrocious mystery was solved."
    )


def build_world(setting: Setting, mystery: Mystery, name: str, gender: str, helper_role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"trait": trait}))
    helper_name = helper_role.capitalize()
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_role, memes={"care": 0.0}))
    item = world.add(Entity(id="missing", kind="thing", type=mystery.missing, label=mystery.missing, owner=hero.id))
    world.facts.update(hero=hero, helper=helper, item=item, mystery=mystery, setting=setting)
    return world


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, helper_role: str, trait: str) -> World:
    world = build_world(setting, mystery, name, gender, helper_role, trait)
    hero = world.get(name)
    helper = world.get(helper_role.capitalize())

    introduce(world, hero, mystery)
    world.para()
    worry(world, hero, helper, mystery)
    inspect_clue(world, hero, mystery)
    test_theory(world, hero, helper, mystery)
    reveal(world, hero, helper, mystery)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, mystery, setting = f["hero"], f["helper"], f["mystery"], f["setting"]
    return [
        f'Write a child-friendly mystery story set in {setting.place} about a missing {mystery.missing}.',
        f"Tell a story where {hero.id} and {helper.id} solve an atrocious little problem by following clues.",
        f"Write a short mystery for a young child that ends with the lost {mystery.missing} found at {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mystery, setting = f["hero"], f["helper"], f["mystery"], f["setting"]
    return [
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"The missing thing was a {mystery.missing}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.id} helped by suggesting a careful clue check.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the atrocious mystery?",
            answer=f"{hero.id} solved it by following the clue and testing a guess instead of rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out an answer.",
        ),
        QAItem(
            question="Why do detectives look carefully?",
            answer="Detectives look carefully because tiny details can show what really happened.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find the answer or fix what went wrong.",
        ),
        QAItem(
            question=f"Why did the story feel atrocious at first?",
            answer=f"It felt atrocious because the missing {mystery.missing} made everything confusing until the clues were sorted out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="kitchen", mystery="missing_spoon", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(setting="library", mystery="missing_bookmark", name="Leo", gender="boy", helper="father", trait="careful"),
    StoryParams(setting="garden", mystery="missing_key", name="Nora", gender="girl", helper="grandma", trait="bright"),
    StoryParams(setting="porch", mystery="missing_marble", name="Theo", gender="boy", helper="grandpa", trait="patient"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "mystery", None) and (getattr(args, "setting", None), getattr(args, "mystery", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = valid_combos()
    if getattr(args, "setting", None):
        choices = [c for c in choices if c[0] == getattr(args, "setting", None)]
    if getattr(args, "mystery", None):
        choices = [c for c in choices if c[1] == getattr(args, "mystery", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.helper, params.trait)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    model = asp.one_model(asp_program("#show reasonable/2."))
    cl = set(asp.atoms(model, "reasonable"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-sized atrocious mystery with careful problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def asp_facts_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_facts_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_facts_program() + "#show reasonable/2.\n")
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} reasonable combos:\n")
        for s, m in combos:
            print(f"  {s:10} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
