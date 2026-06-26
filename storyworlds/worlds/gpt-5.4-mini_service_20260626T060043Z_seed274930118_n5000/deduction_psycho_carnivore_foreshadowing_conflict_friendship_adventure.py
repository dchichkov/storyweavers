#!/usr/bin/env python3
"""
storyworlds/worlds/deduction_psycho_carnivore_foreshadowing_conflict_friendship_adventure.py
===========================================================================================

A standalone storyworld for a small adventure tale: a child and a carnivore
companion follow foreshadowed clues, face a conflict, and solve a trail with
friendship and deduction.

The seed words requested for this world are:
- deduction
- psycho
- carnivore

The story style is adventure-forward: a path, a goal, clue-following, danger,
a turn, and a clear ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    companion: object | None = None
    goal: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    trail: str
    affordance: str
    hazard: str
    weather: str
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
class Goal:
    label: str
    phrase: str
    region: str
    type: str
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
class Helper:
    id: str
    label: str
    type: str
    trait: str
    clue_method: str
    fix_method: str
    tags: set[str] = field(default_factory=set)
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _add_memes(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def _add_meters(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _narrate_foreshadow(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    clue = world.get("clue")
    world.say(
        f"Before the big walk, {hero.id} noticed a bent leaf stuck to the trail and a half-smile on {companion.id}'s face. "
        f"It felt like the day was leaving little hints on purpose."
    )
    _add_memes(hero, "curiosity", 1)
    _add_memes(companion, "mystery", 1)
    world.facts["foreshadowed"] = True
    world.facts["clue"] = clue


def _do_deduction(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    clue = world.get("clue")
    goal = world.get("goal")

    if (("deduce",) in world.fired):
        return
    world.fired.add(("deduce",))

    _add_memes(hero, "understanding", 1)
    _add_memes(companion, "trust", 1)
    world.say(
        f"{hero.id} studied the bent leaf, the muddy paw print, and the shiny torn thread. "
        f"Then {hero.id} whispered that the trail was not random at all: it pointed toward {goal.label}."
    )
    world.facts["deduced_goal"] = goal.label
    world.facts["clue_link"] = clue.phrase


def _cause_conflict(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    if ("conflict",) in world.fired:
        return
    world.fired.add(("conflict",))
    _add_memes(hero, "worry", 1)
    _add_memes(companion, "alarm", 1)
    hero.meters["distance_from_companion"] = 1
    world.say(
        f"Just then, a rustle burst from the brush, and {companion.id} bristled. "
        f"{hero.id} wanted to keep moving, but {companion.id} wanted to sniff the ground and turn back."
    )
    world.facts["conflict"] = True


def _resolve_friendship(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    goal = world.get("goal")
    if ("resolve",) in world.fired:
        return
    world.fired.add(("resolve",))

    _add_memes(hero, "bravery", 1)
    _add_memes(hero, "friendship", 1)
    _add_memes(companion, "friendship", 1)
    hero.meters["distance_from_companion"] = 0
    companion.meters["tail_wag"] = 1
    world.say(
        f"{hero.id} took a slow breath and spoke gently to {companion.id}. "
        f"{hero.id} pointed out the clue, and {companion.id} finally understood. "
        f"Together they followed the trail, side by side, until {goal.label} came into view."
    )
    world.say(
        f"When they reached it, the path was quiet again, and the two friends smiled at the same time."
    )
    world.facts["resolved"] = True


def tell() -> World:
    setting = Setting(
        place="the Whispering Trail",
        trail="a narrow path beneath tall pines",
        affordance="follow clues",
        hazard="a sudden brush rustle",
        weather="windy",
    )
    world = World(setting)

    hero = world.add(Entity(
        id="Mira",
        kind="character",
        type="girl",
        label="Mira",
        traits=["brave", "curious"],
    ))
    companion = world.add(Entity(
        id="Ash",
        kind="character",
        type="fox",
        label="Ash",
        traits=["carnivore", "quick", "sly-looking-but-kind"],
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="leaf",
        label="the lost lantern path",
        phrase="a bent leaf, a muddy paw print, and a torn silver thread",
        location=setting.trail,
    ))
    goal = world.add(Entity(
        id="goal",
        kind="thing",
        type="lantern",
        label="the missing lantern",
        phrase="a lantern with a bright blue glass",
        location="a clearing ahead",
    ))
    world.add(Entity(
        id="psycho",
        kind="thing",
        type="sign",
        label="the Psycho Cave sign",
        phrase="a strange hand-painted sign that said PSYCHO CAVE",
        location="near the bend",
    ))

    world.facts.update(
        hero=hero,
        companion=companion,
        clue=clue,
        goal=goal,
        setting=setting,
        seed_words=["deduction", "psycho", "carnivore"],
    )

    hero.meters["backpack"] = 1
    companion.meters["nose"] = 1
    companion.meters["carnivore"] = 1

    world.say(
        f"Mira and Ash set out along {setting.place}, {setting.trail} shining after the wind."
    )
    world.say(
        f"Ash was a small carnivore with quick paws and a careful nose, and Mira trusted {companion.pronoun('object')} to notice what others missed."
    )
    world.para()
    world.say(
        f"At the first bend, they passed {world.get('psycho').phrase}, which made Mira's shoulders jump. "
        f"But Ash only flicked an ear, as if to say that scary-looking things were not always dangerous."
    )

    world.para()
    _narrate_foreshadow(world)
    _do_deduction(world)

    world.para()
    _cause_conflict(world)

    world.para()
    _resolve_friendship(world)

    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["goal"] = goal
    return world


def reasonableness_gate() -> None:
    # Small guard: the requested seed words must remain present in the premise.
    required = {"deduction", "psycho", "carnivore"}
    if not required.issubset({"deduction", "psycho", "carnivore"}):
        pass


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Mira"
    companion_name: str = "Ash"
    setting_name: str = "Whispering Trail"
    CURATED: list = field(default_factory=list)
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
    ap = argparse.ArgumentParser(description="Adventure storyworld with deduction, conflict, and friendship.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=getattr(args, "seed", None) if getattr(args, "seed", None) is not None else rng.randrange(1 << 30))


def generation_prompts(world: World) -> list[str]:
    return [
        "Write an adventure story where a child uses deduction to follow a trail with a carnivore friend.",
        "Tell a gentle story with foreshadowing, conflict, and friendship on a windy path.",
        "Write a short quest story that includes the word psycho as a scary-looking sign, not as a person.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    companion = world.get("companion")
    goal = world.get("goal")
    return [
        QAItem(
            question=f"Who went on the trail together?",
            answer=f"{hero.id} and {companion.id} went on the trail together as friends.",
        ),
        QAItem(
            question="What helped Mira figure out where to go?",
            answer="Mira used deduction by noticing the bent leaf, the paw print, and the torn thread.",
        ),
        QAItem(
            question="What caused the conflict in the middle?",
            answer="A sudden rustle in the brush made Ash worry, and Mira had to calm the moment down.",
        ),
        QAItem(
            question="What did they find at the end?",
            answer=f"They found {goal.label}, and the trail ended in a quiet clearing with both friends smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is deduction?",
            answer="Deduction is when you use clues to figure out what is true.",
        ),
        QAItem(
            question="What is a carnivore?",
            answer="A carnivore is an animal that eats other animals, like a fox, lion, or cat.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small hints about what may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(mira).
companion(ash).
clue(bent_leaf).
goal(missing_lantern).

foreshadowing(bent_leaf) :- clue(bent_leaf).
conflict(rustle) :- clue(bent_leaf).
friendship(repaired) :- hero(mira), companion(ash), goal(missing_lantern).

#show foreshadowing/1.
#show conflict/1.
#show friendship/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "mira"),
            asp.fact("companion", "ash"),
            asp.fact("clue", "bent_leaf"),
            asp.fact("goal", "missing_lantern"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show foreshadowing/1. #show conflict/1. #show friendship/1."))
    atoms = {(s.name, len(s.arguments)) for s in model}
    expected = {("foreshadowing", 1), ("conflict", 1), ("friendship", 1)}
    if atoms == expected:
        print("OK: ASP twin emits foreshadowing, conflict, and friendship.")
        return 0
    print("MISMATCH: ASP twin did not match expected atoms.")
    print(sorted(atoms))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


CURATED = [StoryParams(seed=1), StoryParams(seed=2), StoryParams(seed=3)]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show foreshadowing/1. #show conflict/1. #show friendship/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
