#!/usr/bin/env python3
"""
storyworlds/worlds/match_chew_learn_bike_lane_surprise_mystery.py
=================================================================

A small mystery storyworld set in a bike lane.

Premise:
- A child notices a surprising clue in the bike lane.
- The child wants to learn what it means.
- Something chews on the clue and makes the mystery harder.
- The child and a helper match the clue to the right source and discover the truth.

This world is intentionally compact and state-driven: curiosity grows, confusion
rises when the clue is damaged, and the ending proves what was learned.
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

    child: object | None = None
    clue: object | None = None
    helper: object | None = None
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
    place: str = "the bike lane"
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
class Clue:
    id: str
    label: str
    phrase: str
    source: str
    match_to: str
    surprise: str
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
    clue: str
    name: str
    gender: str
    parent: str
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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


CLUE_REGISTRY = {
    "sticker": Clue(
        id="sticker",
        label="bright sticker",
        phrase="a bright sticker with a star on it",
        source="a repair helper's toolbox",
        match_to="a toolbox sticker sheet",
        surprise="the repair helper was the one who lost it",
    ),
    "bell": Clue(
        id="bell",
        label="tiny bike bell",
        phrase="a tiny bike bell shaped like a moon",
        source="a child's fallen basket",
        match_to="a missing basket charm",
        surprise="the bell had rolled out of a basket during the ride",
    ),
    "leaf": Clue(
        id="leaf",
        label="crisp leaf",
        phrase="a crisp leaf with one bitten edge",
        source="a squirrel's nest",
        match_to="a nest of leaves",
        surprise="a squirrel had tucked it there as a secret snack",
    ),
}

NAMES_GIRL = ["Mia", "Lila", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Sam", "Owen"]
TRAITS = ["curious", "quiet", "careful", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a bike-lane mystery with surprise, matching, and learning."
    )
    ap.add_argument("--clue", choices=sorted(CLUE_REGISTRY))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def clue_for(params: StoryParams) -> Clue:
    return CLUE_REGISTRY[params.clue]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUE_REGISTRY))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(clue=clue, name=name, gender=gender, parent=parent)


def _do_chew(world: World, child: Entity, clue: Entity) -> None:
    child.memes["confusion"] += 1
    clue.meters["damaged"] = clue.meters.get("damaged", 0) + 1
    clue.meters["clear"] = max(0.0, clue.meters.get("clear", 1.0) - 1.0)
    world.say(f"Before they could study it, a small dog chewed the edge of the clue.")


def generate(params: StoryParams) -> StorySample:
    clue_cfg = clue_for(params)
    world = World(Setting())
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"curiosity": 0.0, "confusion": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "surprise": 0.0, "learned": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={},
        memes={"helpfulness": 1.0},
    ))
    clue = world.add(Entity(
        id=clue_cfg.id,
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        owner="bike_lane",
        caretaker="Parent",
        meters={"clear": 1.0, "damaged": 0.0},
        memes={"mystery": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label="the repair helper",
        meters={},
        memes={"helpfulness": 1.0},
    ))

    world.say(
        f"{child.id} was a little {params.gender} who liked quiet walks beside {world.setting.place}."
    )
    world.say(
        f"One day, {child.id} spotted {clue.phrase} lying near the painted line."
    )
    world.say(
        f"It looked like a surprise, and {child.pronoun('subject')} wanted to learn what it meant."
    )

    world.para()
    child.meters["curiosity"] += 1.0
    child.memes["surprise"] += 1.0
    world.say(
        f"{child.id} leaned closer, but the clue still felt like a mystery."
    )

    _do_chew(world, child, clue)

    world.say(
        f"{child.id} frowned, because the clue was harder to read after the chewing."
    )
    world.say(
        f"{params.parent.capitalize()} knelt beside {child.pronoun('object')} and said they could match the torn clue to something nearby."
    )

    world.para()
    child.meters["curiosity"] += 1.0
    child.memes["surprise"] += 1.0
    world.say(
        f"They matched the shape and color to {clue_cfg.match_to} at the little repair stand."
    )
    world.say(
        f"That was when they learned {clue_cfg.surprise}."
    )

    child.memes["learned"] += 1.0
    child.memes["confusion"] = 0.0
    clue.meters["clear"] = 0.5
    world.say(
        f"{child.id} smiled, because the mystery was solved, and the bike lane felt friendly again."
    )

    world.facts.update(
        child=child,
        parent=parent,
        clue=clue,
        helper=helper,
        clue_cfg=clue_cfg,
        params=params,
    )

    story = world.render()
    prompts = generation_prompts(world)
    story_qa = build_story_qa(world)
    world_qa = build_world_qa(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = _safe_fact(world, f, "clue_cfg")
    child = _safe_fact(world, f, "child")
    return [
        "Write a short mystery story for a young child set in a bike lane, with a surprising clue and a gentle ending.",
        f"Tell a story where {child.id} notices {clue.phrase}, something chews it, and the adults help {child.pronoun('object')} learn the answer.",
        f"Create a child-friendly mystery about a {child.type} who wants to learn why {clue.label} appeared in the bike lane.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    clue: Entity = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {clue.phrase} near the painted line in {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the mystery harder to solve?",
            answer=f"A small dog chewed the edge of the clue, so it was harder to read.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label} solve it?",
            answer=f"They matched the torn clue to {clue_cfg.match_to} and learned that {clue_cfg.surprise}.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the mystery was solved?",
            answer=f"{child.id} felt happy and less confused after learning the answer.",
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand right away, so you look for clues to learn the answer.",
        ),
        QAItem(
            question="What does it mean to match something?",
            answer="To match something means to find another thing that goes with it, like two pieces that fit together.",
        ),
        QAItem(
            question="Why can chewing damage paper?",
            answer="Chewing can tear paper into little pieces, which makes writing harder to read.",
        ),
        QAItem(
            question="Why do people learn from clues?",
            answer="People learn from clues because clues can point to what happened and help explain a surprise.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bike_lane")]
    for cid, clue in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("phrase", cid, clue.label))
        lines.append(asp.fact("matches", cid, clue.match_to))
        lines.append(asp.fact("surprise", cid, clue.surprise))
    lines.append(asp.fact("theme", "match"))
    lines.append(asp.fact("theme", "chew"))
    lines.append(asp.fact("theme", "learn"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_clue(C) :- clue(C).
mystery(C) :- clue(C), matches(C,_), surprise(C,_).
#show valid_clue/1.
#show mystery/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_clue/1.\n#show mystery/1."))
    return sorted(set(asp.atoms(model, "valid_clue"))), sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    valid, mystery = asp_valid()
    python_valid = sorted((cid,) for cid in CLUE_REGISTRY)
    python_mystery = sorted((cid,) for cid in CLUE_REGISTRY)
    if valid == python_valid and mystery == python_mystery:
        print(f"OK: ASP parity matches Python registry ({len(valid)} clues).")
        return 0
    print("MISMATCH between ASP and Python.")
    if valid != python_valid:
        print("  valid only in ASP:", sorted(set(valid) - set(python_valid)))
        print("  valid only in Python:", sorted(set(python_valid) - set(valid)))
    if mystery != python_mystery:
        print("  mystery only in ASP:", sorted(set(mystery) - set(python_mystery)))
        print("  mystery only in Python:", sorted(set(python_mystery) - set(mystery)))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(clue="sticker", name="Mia", gender="girl", parent="mother"),
        StoryParams(clue="bell", name="Leo", gender="boy", parent="father"),
        StoryParams(clue="leaf", name="Nora", gender="girl", parent="mother"),
    ]


CURATED = build_curated()


def resolve_gender_check(args: argparse.Namespace) -> None:
    if getattr(args, "name", None) and getattr(args, "gender", None):
        return


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
        print(asp_program("#show valid_clue/1.\n#show mystery/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        valid, mystery = asp_valid()
        print(f"{len(valid)} clues; {len(mystery)} mystery facts")
        for item in valid:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.clue} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
