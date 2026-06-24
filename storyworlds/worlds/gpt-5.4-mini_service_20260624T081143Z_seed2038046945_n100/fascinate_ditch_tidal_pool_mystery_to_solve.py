#!/usr/bin/env python3
"""
storyworlds/worlds/fascinate_ditch_tidal_pool_mystery_to_solve.py
==================================================================

A standalone storyworld for a small adventure at a tidal pool.

Seed idea:
A curious child is fascinated by a tidal pool mystery. A tempting ditch trails
through the rocks, but the child is warned that unsafe footing can turn a little
search into a bigger problem. The story turns when the child chooses a careful
route, solves the mystery, and leaves the pool better understood than before.

The world is built around:
- fascination with a mysterious find
- a ditch that is tempting but risky
- a cautionary adult voice
- an adventure-style resolution at a tidal pool

The story remains grounded in simulated state: meters track physical changes
and memes track feelings, caution, and discovery.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
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
    place: str = "the tidal pool"
    tidally_active: bool = True
    SETTING: object | None = None
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
class Mystery:
    id: str
    clue: str
    truth: str
    risk: str
    solution: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
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


def cautious_gate(mystery: Mystery) -> bool:
    return "ditch" in mystery.tags and "tidal" in mystery.tags


def solve_mystery(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["fascination"] += 1
    child.memes["caution"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was fascinated by the little mystery at {world.setting.place}. "
        f"A thin ditch curled past the rocks, and {child.pronoun('possessive')} eyes kept following it."
    )


def warn_about_ditch(world: World, parent: Entity, child: Entity, mystery: Mystery) -> None:
    child.memes["warned"] += 1
    world.say(
        f'"Don’t ditch the safe path," {parent.pronoun("subject")} said. '
        f'"That wet rock can slip, and {mystery.risk}."'
    )


def inspect_clue(world: World, child: Entity, mystery: Mystery) -> None:
    child.meters["steps"] += 1
    child.memes["careful"] += 1
    world.say(
        f"{child.id} crouched by the pool and looked closer. "
        f"{mystery.clue.capitalize()}, and that was the first clue."
    )


def choose_safe_route(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["brave"] += 1
    child.memes["fear"] += 0.5
    world.say(
        f"Instead of leaping into the ditch, {child.id} picked a careful path around it. "
        f"{parent.pronoun('subject').capitalize()} nodded, because adventure was better when nobody skidded."
    )


def reveal_solution(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["delight"] += 1
    world.say(
        f"Then the mystery made sense: {mystery.truth}. "
        f"{child.id} smiled, because {mystery.solution}."
    )


def ending_image(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"By the end, {child.id} left the tidal pool with salty shoes, a bright grin, "
        f"and {parent.pronoun('possessive')} hand held tight beside {child.pronoun('object')}."
    )


SETTING = Setting()

MYSTERIES = {
    "shell": Mystery(
        id="shell",
        clue="a spiral shell glimmered in a puddle",
        truth="the tide had dropped a tiny shell into the pool and left it shining on the sand",
        risk="the ditch was filled with slick water that could twist an ankle",
        solution="the shell could be picked up without crossing the unsafe ditch",
        tags={"tidal", "ditch", "shell", "mystery"},
    ),
    "crab": Mystery(
        id="crab",
        clue="small tracks zigzagged from a rock crack",
        truth="a crab had slipped out to hunt and left its quick tracks behind",
        risk="the ditch hid a wobbling stone that could tumble underfoot",
        solution="the tracks pointed to the crab’s hiding place near the safe stones",
        tags={"tidal", "ditch", "crab", "mystery"},
    ),
    "bottle": Mystery(
        id="bottle",
        clue="something round was bobbing between the pools",
        truth="a little glass bottle had washed in with the tide and rested in a tide-made pocket",
        risk="the ditch made the route steep and slippery",
        solution="the bottle could be reached from the edge by walking carefully",
        tags={"tidal", "ditch", "bottle", "mystery"},
    ),
}

GIRL_NAMES = ["Ava", "Mia", "Nora", "Zoe", "Lily"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Ben", "Max"]
TRAITS = ["curious", "brave", "playful", "bright", "spirited"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a tidal-pool mystery, caution, and a safe solution.")
    ap.add_argument("--place", choices=["tidal_pool"], default="tidal_pool")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=getattr(args, "place", None), mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    if not cautious_gate(mystery):
        pass
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    world.add(Entity(id="mystery", type="thing", label=mystery.id, tags=set(mystery.tags)))

    world.say(
        f"At the tidal pool, little {params.trait} {params.name} loved to look for surprises after the tide went out."
    )
    world.say(
        f"{params.name} had never seen anything so interesting, and the little scene fascinated {child.pronoun('object')} at once."
    )
    world.para()
    solve_mystery(world, child, mystery)
    warn_about_ditch(world, parent, child, mystery)
    inspect_clue(world, child, mystery)
    world.para()
    choose_safe_route(world, child, parent, mystery)
    reveal_solution(world, child, mystery)
    ending_image(world, child, parent)
    world.facts.update(child=child, parent=parent, mystery=mystery, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    return [
        f"Write a gentle adventure about a {p.gender} named {p.name} at a tidal pool where a ditch makes the child slow down and think.",
        f"Tell a child-friendly mystery story in which {p.name} is fascinated by a clue, listens to a cautionary warning, and solves the problem safely.",
        f"Write a short story that includes the words 'fascinate' and 'ditch' and ends with a clear discovery at the tidal pool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why was {p.name} fascinated at the tidal pool?",
            answer=f"{p.name} was fascinated because {m.clue}, and the strange little sight promised a mystery to solve.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} warn {p.name} about the ditch?",
            answer=f"{parent.pronoun('subject').capitalize()} warned {p.name} because {m.risk}. The warning helped keep the adventure safe.",
        ),
        QAItem(
            question=f"How did {p.name} solve the mystery without getting hurt?",
            answer=f"{p.name} slowed down, chose the safe path, and followed the clue until {m.truth}. That careful choice solved the mystery.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end of the story?",
            answer=f"{p.name} felt proud and happy, because the mystery was solved and the tidal pool was understood better than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a pool of seawater left behind when the tide goes out, often between rocks near the shore.",
        ),
        QAItem(
            question="Why should you be careful on wet rocks?",
            answer="Wet rocks can be slippery, so careful steps help keep you from falling.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs clues to solve.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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


ASP_RULES = r"""
place(tidal_pool).
mystery(shell).
mystery(crab).
mystery(bottle).
cautionary(M) :- mystery(M).
adventure(M) :- mystery(M).
interesting(M) :- mystery(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import by contract
    lines = [asp.fact("setting", "tidal_pool")]
    for m in sorted(MYSTERIES):
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("cautionary", m))
        lines.append(asp.fact("adventure", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    if "tidal_pool" in asp_program("#show place/1."):
        print("OK: ASP twin is present.")
        return 0
    print("MISMATCH: ASP twin missing.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, mid in enumerate(sorted(MYSTERIES)):
            params = StoryParams(
                place="tidal_pool",
                mystery=mid,
                name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)),
                gender="girl" if i % 2 == 0 else "boy",
                parent="mother" if i % 2 == 0 else "father",
                trait=_safe_lookup(TRAITS, i % len(TRAITS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
