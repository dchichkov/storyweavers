#!/usr/bin/env python3
"""
storyworlds/worlds/eyed_wrong_foreshadowing_slice_of_life.py
=============================================================

A small slice-of-life storyworld about a child, a tiny wrong choice, and a
quiet foreshadowed fix.

Premise:
- A child is getting ready for a simple outing.
- They eye the wrong item or take the wrong path.
- Small physical cues foreshadow a later snag.
- A parent or helper notices the hint, makes a gentle correction, and the day
  ends calmly with a better choice.

This world is intentionally modest: one small domestic domain, a few entities,
and a short causal chain that supports complete stories rather than event logs.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    par: object | None = None
    right: object | None = None
    wrong: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Scenario:
    place: str
    outing: str
    wrong_item: str
    right_item: str
    weather: str
    hint: str
    consequence: str
    fix: str
    tags: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    scenario: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
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
        import copy as _copy

        clone = World(self.scenario)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def maybe(article: str, phrase: str) -> str:
    return f"{article} {phrase}"


def begins_with_vowel(text: str) -> bool:
    return text[:1].lower() in "aeiou"


def art(phrase: str) -> str:
    return ("an " if begins_with_vowel(phrase) else "a ") + phrase


def article_label(label: str) -> str:
    return art(label)


def item_phrase(item: Entity) -> str:
    return item.phrase or item.label


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    wrong = world.get("wrong_item")
    right = world.get("right_item")
    scen = world.scenario

    if child.memes.get("wrong_choice", 0.0) >= THRESHOLD and ("wrong_choice",) not in world.fired:
        world.fired.add(("wrong_choice",))
        child.memes["awkward"] = child.memes.get("awkward", 0.0) + 1
        out.append(f"{child.pronoun('subject').capitalize()} hesitated, because that choice felt wrong.")

    if child.memes.get("foreshadow", 0.0) >= THRESHOLD and ("foreshadow",) not in world.fired:
        world.fired.add(("foreshadow",))
        out.append(f"At the window, the little sign had already hinted that the day might turn tricky.")

    if child.meters.get("carry_wrong", 0.0) >= THRESHOLD and ("carry_wrong",) not in world.fired:
        world.fired.add(("carry_wrong",))
        out.append(f"Sure enough, {item_phrase(wrong)} made the walk clumsy.")

    if child.meters.get("helped", 0.0) >= THRESHOLD and ("helped",) not in world.fired:
        world.fired.add(("helped",))
        out.append(f"With the better choice, {item_phrase(right)} was ready for the outing.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def foreshadow(world: World) -> None:
    child = world.get("child")
    scen = world.scenario
    child.memes["foreshadow"] = child.memes.get("foreshadow", 0.0) + 1
    world.say(
        f"Before they left {scen.place}, {child.id} noticed {scen.hint}; "
        f"it was a tiny clue that something was off."
    )
    propagate(world)


def choose_wrong(world: World) -> None:
    child = world.get("child")
    wrong = world.get("wrong_item")
    child.memes["wrong_choice"] = child.memes.get("wrong_choice", 0.0) + 1
    wrong.worn_by = child.id
    child.meters["carry_wrong"] = child.meters.get("carry_wrong", 0.0) + 1
    world.say(
        f"{child.id} eyed {article_label(wrong.label)} and picked it up first."
    )
    world.say(
        f"It looked fine for a second, but the choice was the wrong one for {world.scenario.outing}."
    )
    propagate(world)


def gentle_fix(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    wrong = world.get("wrong_item")
    right = world.get("right_item")
    wrong.worn_by = None
    right.worn_by = child.id
    child.meters["carry_wrong"] = 0.0
    child.meters["helped"] = 1.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    world.say(
        f"{parent.id} smiled and pointed to {article_label(right.label)} instead."
    )
    world.say(
        f"Together they switched things around before the small problem could grow."
    )
    propagate(world)


def ending(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    right = world.get("right_item")
    scen = world.scenario
    world.say(
        f"In the end, {child.id} left with {article_label(right.label)}, "
        f"and the day felt easy again."
    )
    world.say(
        f"{child.id} went on to {scen.outing} with {parent.id}, "
        f"feeling lighter and glad they had noticed the clue in time."
    )


def tell(scenario: Scenario, name: str = "Mina", gender: str = "girl",
         parent: str = "mother", trait: str = "curious") -> World:
    world = World(scenario)
    child = world.add(Entity(id=name, kind="character", type=gender))
    par = world.add(Entity(id="parent", kind="character", type=parent, label=parent))
    wrong = world.add(Entity(
        id="wrong_item",
        type=scenario.wrong_item,
        label=scenario.wrong_item,
        phrase=scenario.wrong_item,
        owner=child.id,
    ))
    right = world.add(Entity(
        id="right_item",
        type=scenario.right_item,
        label=scenario.right_item,
        phrase=scenario.right_item,
        owner=child.id,
    ))
    world.add(Entity(id="place", type="place", label=scenario.place, phrase=scenario.place))

    world.say(
        f"{child.id} was a little {trait} {gender} who liked calm morning routines."
    )
    world.say(
        f"{child.id}'s {parent} had already set out {article_label(right.label)} for {scenaria(scenario)}."
    )
    world.para()
    foreshadow(world)
    choose_wrong(world)
    world.para()
    world.say(
        f"For a moment, the room felt ordinary, but the earlier clue still hung in the air."
    )
    gentle_fix(world)
    world.para()
    ending(world)

    world.facts.update(
        child=child,
        parent=par,
        wrong=wrong,
        right=right,
        scenario=scenario,
    )
    return world


def scenaria(scenario: Scenario) -> str:
    return f"{scenario.outing}"


SCENARIOS = {
    "library_walk": Scenario(
        place="the front hall",
        outing="the walk to the library",
        wrong_item="stiff coat",
        right_item="soft blue sweater",
        weather="cool",
        hint="the hallway draft fluttering the coat sleeve",
        consequence="it would have felt too stiff to carry in the stroller",
        fix="the sweater",
        tags={"coat", "sweater", "library", "hint"},
    ),
    "bakery_stop": Scenario(
        place="the kitchen",
        outing="the stop at the bakery",
        wrong_item="empty lunch box",
        right_item="snack bag",
        weather="warm",
        hint="the nearly empty shelf where the lunch box usually sat",
        consequence="there would be nothing to share at snack time",
        fix="the snack bag",
        tags={"lunch", "snack", "bakery", "hint"},
    ),
    "rainy_errand": Scenario(
        place="the mudroom",
        outing="the errand to the corner shop",
        wrong_item="thin cap",
        right_item="red rain hat",
        weather="drizzly",
        hint="the gray sky pressing close to the window",
        consequence="the cap would soak through by the second block",
        fix="the rain hat",
        tags={"rain", "hat", "shop", "hint"},
    ),
    "playdate": Scenario(
        place="the porch",
        outing="the playdate across the street",
        wrong_item="heavy boots",
        right_item="light sneakers",
        weather="bright",
        hint="the neat row of sneakers by the door",
        consequence="the boots would make every step feel slow and clunky",
        fix="the sneakers",
        tags={"boots", "sneakers", "playdate", "hint"},
    ),
}

NAMES = ["Mina", "Luca", "Ivy", "Noah", "Tia", "Eli", "Zuri", "Ari"]
TRAITS = ["curious", "quiet", "cheerful", "thoughtful", "playful", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, scen in SCENARIOS.items():
        for w in [scen.wrong_item, scen.right_item]:
            if w != scen.right_item:
                out.append((sid, w))
    return out


@dataclass
class _Placeholder:
    pass
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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with foreshadowing.")
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scen = getattr(args, "scenario", None) or rng.choice(sorted(SCENARIOS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(scenario=scen, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    s = _safe_fact(world, world.facts, "scenario")
    child = _safe_fact(world, world.facts, "child")
    return [
        f"Write a short slice-of-life story where {child.id} eyes the wrong thing before a calm outing.",
        f"Tell a gentle story with foreshadowing about a child getting ready for {s.outing}.",
        f"Write a child-friendly story where a tiny clue helps avoid a wrong choice at {s.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    s = _safe_fact(world, world.facts, "scenario")
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    wrong = _safe_fact(world, world.facts, "wrong")
    right = _safe_fact(world, world.facts, "right")
    return [
        QAItem(
            question=f"What did {child.id} eye first before the outing?",
            answer=f"{child.id} eyed {article_label(wrong.label)} first, but it was the wrong choice for {s.outing}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the problem in {s.place}?",
            answer=f"The clue was {s.hint}, which gently hinted that something was off before they left.",
        ),
        QAItem(
            question=f"What did {parent.id} suggest instead of {wrong.label}?",
            answer=f"{parent.id} suggested {article_label(right.label)} instead, and that made the outing feel right again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    s = _safe_fact(world, world.facts, "scenario")
    out = [
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is a small clue early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="What does it mean when a choice is wrong?",
            answer="A wrong choice is one that does not fit the moment well, so it can cause a small problem or delay.",
        ),
    ]
    if "rain" in s.tags:
        out.append(QAItem(
            question="Why can a thin cap be a bad choice on a rainy day?",
            answer="A thin cap can get wet quickly, so it does not protect very well when rain is coming down.",
        ))
    return out


ASP_RULES = r"""
wrong_choice(S) :- scenario(S), picks_wrong(S).
foreshadowing(S) :- scenario(S), hint(S).
resolved(S) :- wrong_choice(S), better_choice(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, scen in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("hint", sid))
        lines.append(asp.fact("picks_wrong", sid))
        lines.append(asp.fact("better_choice", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show wrong_choice/1. #show foreshadowing/1. #show resolved/1."))
    atoms = asp.atoms(model, "wrong_choice")
    if atoms:
        print("OK: ASP program parses and yields a model.")
        return 0
    print("MISMATCH: ASP program did not produce expected atoms.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SCENARIOS, params.scenario), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show wrong_choice/1. #show foreshadowing/1. #show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import asp
        except Exception as e:
            print(f"ASP unavailable: {e}")
            sys.exit(1)
        model = asp.one_model(asp_program("#show wrong_choice/1. #show foreshadowing/1. #show resolved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for sid in SCENARIOS:
            p = StoryParams(
                scenario=sid,
                name=random.Random(base_seed + len(samples)).choice(NAMES),
                gender=random.Random(base_seed + len(samples) + 1).choice(["girl", "boy"]),
                parent=random.Random(base_seed + len(samples) + 2).choice(["mother", "father"]),
                trait=random.Random(base_seed + len(samples) + 3).choice(TRAITS),
                seed=base_seed + len(samples),
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            sample = generate(p)
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
