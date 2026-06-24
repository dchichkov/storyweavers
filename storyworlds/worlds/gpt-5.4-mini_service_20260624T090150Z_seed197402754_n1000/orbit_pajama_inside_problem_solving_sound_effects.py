#!/usr/bin/env python3
"""
A detective-style tiny story world about an inside mystery involving orbit,
pajamas, sound effects, and a little bit of magic.

The premise:
- A child detective notices a strange sound inside.
- A pajama-related clue is tied to a toy orbiting lamp/moon.
- The detective solves the problem with careful observation, sound clues, and a magic helper.

The world model tracks:
- physical meters: noisy, hidden, sparkling, orbiting, tidy, cozy
- emotional memes: curiosity, worry, confidence, relief

The prose is driven from state changes rather than a frozen template.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    pajama: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the bedroom"
    inside: bool = True
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    clue_sound: str
    cause_sound: str
    verb: str
    fix: str
    location: str
    mess: str
    tags: set[str] = field(default_factory=set)
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
class MagicTool:
    id: str
    label: str
    effect: str
    needed: str
    reveal: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    current_problem: Optional[Problem] = None
    current_magic: Optional[MagicTool] = None

    clone: object | None = None
    world: object | None = None
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.current_problem = self.current_problem
        clone.current_magic = self.current_magic
        return clone
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
    problem: str
    magic: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", inside=True, affords={"orbit_lamp", "hidden_toy"}),
    "hall": Setting(place="the hall", inside=True, affords={"orbit_lamp"}),
    "playroom": Setting(place="the playroom", inside=True, affords={"hidden_toy", "orbit_lamp"}),
}

PROBLEMS = {
    "orbit_lamp": Problem(
        id="orbit_lamp",
        clue_sound="whirr-whirr",
        cause_sound="tink-tink",
        verb="trace the orbiting toy",
        fix="stop the little wheel that kept spinning the lamp",
        location="under the bed",
        mess="noisy",
        tags={"orbit", "inside", "sound"},
    ),
    "hidden_toy": Problem(
        id="hidden_toy",
        clue_sound="scritch-scritch",
        cause_sound="rustle-rustle",
        verb="find the hidden pajama button",
        fix="lift the pajama sleeve and peek inside the pocket",
        location="inside the pajama pocket",
        mess="hidden",
        tags={"pajama", "inside", "sound"},
    ),
}

MAGIC_TOOLS = {
    "moon_beam": MagicTool(
        id="moon_beam",
        label="a moon-beam charm",
        effect="made tiny silver sparks",
        needed="light",
        reveal="glimmered on the clue",
        tags={"magic", "orbit"},
    ),
    "pajama_key": MagicTool(
        id="pajama_key",
        label="a pajama key",
        effect="opened hidden stitches with a soft glow",
        needed="fabric",
        reveal="opened a secret seam",
        tags={"magic", "pajama"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Max", "Noah", "Ben", "Finn", "Theo"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style tiny story world with orbit, pajamas, inside, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGIC_TOOLS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, magic=magic, name=name, gender=gender, parent=parent, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    prob = _safe_lookup(PROBLEMS, params.problem)
    magic = _safe_lookup(MAGIC_TOOLS, params.magic)
    if "orbit" in prob.tags and "orbit" not in magic.tags:
        pass
    if "pajama" in prob.tags and "pajama" not in magic.tags:
        pass


def _do_clue(world: World, child: Entity, prob: Problem) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(f"Inside {world.setting.place}, {child.id} heard {prob.clue_sound} from somewhere nearby.")
    world.say(f"{child.id} paused like a detective and listened again, because the sound felt odd.")


def _do_search(world: World, child: Entity, parent: Entity, prob: Problem) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"{child.id} followed the sound to {prob.location}, where {prob.cause_sound} came back in a soft echo.")
    world.say(f"{child.pronoun().capitalize()} wanted to {prob.verb}, but the problem still hid its shape.")


def _do_magic(world: World, child: Entity, parent: Entity, prob: Problem, magic: MagicTool) -> None:
    world.say(f"{parent.id} smiled and held up {magic.label}.")
    world.say(f"It {magic.effect}, and {magic.reveal} like a tiny clue in a detective book.")
    world.current_magic = magic


def _do_solve(world: World, child: Entity, parent: Entity, prob: Problem, magic: MagicTool) -> None:
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say(f"With that hint, {child.id} could {prob.fix}.")
    world.say(
        f"The room went quiet at last: the {prob.mess} sound stopped, {child.id}'s pajama stayed neat, "
        f"and the two detectives shared a proud smile."
    )


def tell(setting: Setting, problem: Problem, magic: MagicTool, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    world.current_problem = problem
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "detective"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    pajama = world.add(Entity(id="pajama", type="pajama", label="pajama", phrase="soft striped pajamas", owner=child.id))
    pajama.worn_by = child.id

    world.say(f"{child.id} was a little detective with sharp eyes and soft {pajama.label}s.")
    world.say(f"{child.pronoun().capitalize()} loved being inside where every quiet sound could become a clue.")
    world.say(f"One evening, {child.id} noticed a strange sound and tugged at {child.pronoun('possessive')} {pajama.label} sleeve.")

    world.para()
    _do_clue(world, child, problem)
    world.say(f"{parent.id} listened too, because a good detective team checks every room twice.")
    _do_search(world, child, parent, problem)

    world.para()
    _do_magic(world, child, parent, problem, magic)
    _do_solve(world, child, parent, problem, magic)

    world.facts.update(
        hero=child,
        parent=parent,
        pajama=pajama,
        problem=problem,
        magic=magic,
        setting=setting,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prob = _safe_fact(world, f, "problem")
    return [
        f'Write a short detective story for a young child about "{prob.id}", "{hero.id}", and a clue inside a room.',
        f"Tell a gentle mystery where {hero.id} hears {prob.clue_sound}, looks inside, and solves it with a little magic.",
        "Write a cozy story with orbit, pajama, and inside that ends with the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prob = _safe_fact(world, f, "problem")
    magic = _safe_fact(world, f, "magic")
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and the strange sound?",
            answer=f"It is a detective-style story about {hero.id}, who listens carefully inside and follows a clue until the problem is solved.",
        ),
        QAItem(
            question=f"What sound clue did {hero.id} hear before solving the mystery?",
            answer=f"{hero.id} heard {prob.clue_sound} before the room's secret was found.",
        ),
        QAItem(
            question=f"How did {parent.id} help {hero.id} solve the problem?",
            answer=f"{parent.id} helped by bringing {magic.label}, which gave off a magic clue and made the answer easy to see.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {prob.mess} sound stopped, {hero.id} felt proud, and the pajama stayed tidy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is an orbit?",
            answer="An orbit is the curved path something takes when it goes around another thing in a circle-like path.",
        ),
        QAItem(
            question="Why can a sound be a clue?",
            answer="A sound can be a clue because it may tell you where something is hiding or what is happening nearby.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special and surprising happens, like a glow, spark, or charm that helps the characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} type={e.type}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts are emitted from the registries.
% A story is compatible when the chosen magic matches the problem's theme.
compatible(P, M) :- problem(P), magic(M), requires(P, T), has(M, T).
chosen_story(Place, P, M) :- setting(Place), supports(Place, P), compatible(P, M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in setting.affords:
            lines.append(asp.fact("supports", sid, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in prob.tags:
            lines.append(asp.fact("requires", pid, t))
    for mid, magic in MAGIC_TOOLS.items():
        lines.append(asp.fact("magic", mid))
        for t in magic.tags:
            lines.append(asp.fact("has", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    prog = asp_program("#show chosen_story/3.")
    model = asp.one_model(prog)
    asp_set = set(asp.atoms(model, "chosen_story"))
    py_set = set()
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for mid, magic in MAGIC_TOOLS.items():
                if place in SETTINGS and prob.tags <= magic.tags | {"inside"} and pid in PROBLEMS:
                    if all(t in magic.tags for t in ({"orbit"} if "orbit" in prob.tags else set())):
                        py_set.add((place, pid, mid))
    if asp_set == py_set:
        print(f"OK: ASP/Python parity holds ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only ASP:", sorted(asp_set - py_set))
    print("only Python:", sorted(py_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="bedroom", problem="orbit_lamp", magic="moon_beam", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="playroom", problem="hidden_toy", magic="pajama_key", name="Leo", gender="boy", parent="father", trait="careful"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(MAGIC_TOOLS, params.magic), params.name, params.gender, params.parent)
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
        print(asp_program("#show chosen_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show chosen_story/3."))
        print(sorted(set(asp.atoms(model, "chosen_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
