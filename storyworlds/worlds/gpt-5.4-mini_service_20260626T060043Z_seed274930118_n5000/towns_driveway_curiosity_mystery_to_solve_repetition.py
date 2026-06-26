#!/usr/bin/env python3
"""
A small slice-of-life storyworld about driveway towns, curiosity, and a tiny
mystery that repeats until someone notices the pattern.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    town_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the driveway"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Town:
    id: str
    name: str
    material: str
    tiny: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    repeats: int
    reveals: str
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
    town: str
    clue: str
    hero_name: str
    hero_gender: str
    parent_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.turns: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.turns = self.turns
        return clone


def _r_repeat_notice(world: World) -> list[str]:
    out = []
    clue = _safe_fact(world, world.facts, "clue")
    for town in world.facts["towns"]:
        sig = ("repeat", town.id, clue.id, world.turns)
        if sig in world.fired:
            continue
        if world.turns >= clue.repeats:
            continue
        world.fired.add(sig)
        out.append(f"Again, something small was missing from {town.name}.")
    return out


def _r_discover_pattern(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    clue = _safe_fact(world, world.facts, "clue")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return []
    if world.turns < clue.repeats:
        return []
    sig = ("discover", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["clarity"] = hero.memes.get("clarity", 0) + 1
    return [f"{hero.id} noticed the same little problem kept returning after each quiet morning."]


CAUSAL_RULES = [
    _r_repeat_notice,
    _r_discover_pattern,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the driveway", affords={"arrange_towns", "search", "repeat"})
TOWNS = {
    "chalk": Town(id="chalk", name="chalk town", material="chalk"),
    "blocks": Town(id="blocks", name="block town", material="toy blocks"),
    "stones": Town(id="stones", name="stone town", material="smooth stones"),
}
CLUES = {
    "missing_sign": Clue(
        id="missing_sign",
        label="tiny sign",
        phrase="a tiny paper sign",
        repeats=2,
        reveals="the mail cart kept nudging it aside",
    ),
    "shifted_road": Clue(
        id="shifted_road",
        label="road line",
        phrase="a blue tape road line",
        repeats=3,
        reveals="the bicycle wheel rolled over the corner each time",
    ),
    "lost_flag": Clue(
        id="lost_flag",
        label="flag",
        phrase="a little flag made from cardboard",
        repeats=2,
        reveals="the breeze kept flicking it off the mailbox stone",
    ),
}

HERO_NAMES = ["Maya", "Noah", "Lena", "Owen", "Iris", "Eli", "Nina", "Theo"]
TRAITS = ["curious", "careful", "quiet", "patient", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [(t, c) for t in TOWNS for c in CLUES]


@dataclass
class _DummyGear:
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


def build_town(world: World, town: Town, hero: Entity, clue: Clue) -> None:
    town_ent = world.add(Entity(id=town.id, kind="thing", type="town", label=town.name, phrase=town.name))
    town_ent.meters["neatness"] = 1.0
    world.facts.setdefault("towns", []).append(town_ent)
    world.facts["hero"] = hero
    world.facts["clue"] = clue
    world.say(f"{hero.id} liked making little towns on the driveway with {town.material}.")
    world.say(f"{hero.pronoun().capitalize()} gave each town a name and arranged the roads just so.")
    world.say(f"One town had {clue.phrase}, and {hero.id} wondered why it never stayed put.")


def start_mystery(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"That made {hero.id} look twice, then three times, because {clue.label} was gone again.")
    world.say(f"{hero.pronoun().capitalize()} wanted to know what was happening on the driveway.")


def loop_day(world: World, hero: Entity, clue: Clue) -> None:
    for turn in range(clue.repeats):
        world.turns = turn
        world.para()
        world.say(f"The next time {hero.id} came outside, the little {clue.label} was missing once more.")
        propagate(world, narrate=True)
        if turn == clue.repeats - 1:
            break
        world.say(f"{hero.id} put it back and waited, wondering if the driveway itself was hiding a trick.")


def solve(world: World, hero: Entity, parent: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.para()
    world.say(f"At last, {hero.id} watched carefully and saw the answer.")
    world.say(f"{clue.reveals.capitalize()}, so the little mystery was really a repeated bump from everyday life.")
    world.say(f"{parent.pronoun().capitalize()} smiled and helped make a better spot for the tiny {clue.label}.")
    world.say(f"After that, the driveway towns stayed neat, and {hero.id} could play without the surprise returning.")


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        memes={"curiosity": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="parent"))
    town = _safe_lookup(TOWNS, params.town)
    clue = _safe_lookup(CLUES, params.clue)
    build_town(world, town, hero, clue)
    start_mystery(world, hero, clue)
    loop_day(world, hero, clue)
    solve(world, hero, parent, clue)
    world.facts.update(hero=hero, parent=parent, town=town, clue=clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story set on a driveway where a child makes little towns and notices a repeat mystery involving {f["clue"].label}.',
        f"Tell a short story about {f['hero'].id} being curious about a tiny problem in the driveway towns and finding the pattern after looking again and again.",
        f'Write a simple story that includes the word "towns" and ends with a small driveway mystery being solved through patient noticing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    clue = _safe_fact(world, f, "clue")
    town = _safe_fact(world, f, "town")
    return [
        QAItem(
            question=f"What did {hero.id} like making on the driveway?",
            answer=f"{hero.id} liked making little {town.name} towns on the driveway and giving them names.",
        ),
        QAItem(
            question=f"What kept disappearing from the little town?",
            answer=f"The {clue.label} kept disappearing, which made {hero.id} curious.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.id} watched carefully, noticed the repeated pattern, and learned that {clue.reveals}.",
        ),
        QAItem(
            question=f"Who helped once the answer was found?",
            answer=f"{parent.id} helped make a better spot so the tiny {clue.label} would stay in place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a driveway?",
            answer="A driveway is a hard path next to a house where people can walk, play, or park a car.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and paying close attention to find out why something happens.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that makes people look, think, and ask questions.",
        ),
        QAItem(
            question="Why can repetition help solve a problem?",
            answer="Repetition can help because when something happens again and again, the pattern becomes easier to notice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
town(T) :- town_fact(T).
clue(C) :- clue_fact(C).
curious(H) :- hero(H).
repeats(C,N) :- clue_repeats(C,N).
mystery(T,C) :- town(T), clue(C).
solved(H,C) :- curious(H), repeats(C,N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TOWNS:
        lines.append(asp.fact("town_fact", tid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("clue_repeats", cid, clue.repeats))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery/2.")
    model = asp.one_model(program)
    asp_pairs = set(asp.atoms(model, "mystery"))
    py_pairs = set((t, c) for t, c in valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: ASP matches Python valid_combos() ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_pairs - py_pairs))
    print("only in Python:", sorted(py_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Driveway towns, curiosity, and a small repeated mystery.")
    ap.add_argument("--town", choices=TOWNS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    town = getattr(args, "town", None) or rng.choice(sorted(TOWNS))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(town=town, clue=clue, hero_name=name, hero_gender=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(town="chalk", clue="missing_sign", hero_name="Maya", hero_gender="girl", parent_type="mother"),
    StoryParams(town="blocks", clue="shifted_road", hero_name="Noah", hero_gender="boy", parent_type="father"),
    StoryParams(town="stones", clue="lost_flag", hero_name="Iris", hero_gender="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery/2."))
        pairs = sorted(set(asp.atoms(model, "mystery")))
        print(f"{len(pairs)} compatible town/clue pairs:")
        for t, c in pairs:
            print(f"  {t} {c}")
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
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero_name}: {p.town} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
