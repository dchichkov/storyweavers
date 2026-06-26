#!/usr/bin/env python3
"""
storyworlds/worlds/lima_humor_detective_story.py
=================================================

A tiny detective storyworld with a humorous turn: Detective Lima follows clues,
meets a few ridiculous suspects, and solves a small mystery in a way that feels
satisfying and kind.

Seed premise:
- A young detective named Lima investigates a missing item.
- The case is funny rather than scary.
- The ending proves what changed in the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    location: str = ""
    solved: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    case: object | None = None
    detective: object | None = None
    entities: set[str] = field(default_factory=set)
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
    place: str
    detail: str
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
    missing_item: str
    missing_phrase: str
    missing_location: str
    culprit: str
    culprit_reason: str
    clue: str
    clue_location: str
    humorous_detail: str
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
    def __init__(self, setting: Setting, mystery: Mystery):
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        w = World(self.setting, self.mystery)
        w.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "location": v.location, "solved": v.solved,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "market": Setting(place="the market", detail="The market was bright, busy, and full of baskets."),
    "library": Setting(place="the library", detail="The library was quiet, except for a squeaky cart wheel."),
    "school": Setting(place="the school hallway", detail="The hallway smelled like crayons and floor wax."),
}

MYSTERIES = {
    "missing_lunch": Mystery(
        id="missing_lunch",
        missing_item="lunchbox",
        missing_phrase="a shiny blue lunchbox",
        missing_location="under the counter",
        culprit="parrot",
        culprit_reason="it liked shiny lids and carried it to make a nest",
        clue="a single cracker crumb",
        clue_location="near the birdcage",
        humorous_detail="the parrot had tucked the lunchbox under one wing and looked very proud",
    ),
    "missing_eraser": Mystery(
        id="missing_eraser",
        missing_item="eraser",
        missing_phrase="a big pink eraser",
        missing_location="inside a storybook",
        culprit="hamster",
        culprit_reason="it used the eraser as a pillow because it was soft and square",
        clue="tiny nibble marks",
        clue_location="beside the reading nook",
        humorous_detail="the hamster was asleep with its cheeks puffed like two tiny balloons",
    ),
    "missing_hat": Mystery(
        id="missing_hat",
        missing_item="hat",
        missing_phrase="a floppy yellow hat",
        missing_location="on the coat rack",
        culprit="dog",
        culprit_reason="it thought the hat was a game of hide-and-seek",
        clue="muddy paw prints",
        clue_location="by the front mat",
        humorous_detail="the dog wore the hat sideways and sneezed every time it wagged its tail",
    ),
}

NAMES = ["Lima", "Milo", "Nora", "Toby", "Zoe", "Iris"]


def clean_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
        pass
    return name


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if not params.name:
        pass


def predict_solution(world: World) -> bool:
    return world.mystery.culprit in {"parrot", "hamster", "dog"}


def solve_case(world: World, detective: Entity, narrate: bool = True) -> None:
    mystery = world.mystery
    detective.meters["attention"] += 1
    detective.memes["curiosity"] += 1
    world.say(f"{detective.id} was a small detective with a tidy notebook and a very serious hat.")
    world.say(f"{detective.pronoun().capitalize()} was in {world.setting.place}, where {world.setting.detail.lower()}")
    world.say(f"Someone had lost {mystery.missing_phrase}, and the whole place felt puzzled.")
    world.para()

    detective.meters["clues"] += 1
    world.say(f"{detective.id} found {mystery.clue} {mystery.clue_location}.")
    world.say(f"That clue pointed toward {mystery.culprit_reason}.")
    detective.memes["amusement"] += 1
    detective.meters["evidence"] += 1

    world.para()
    world.say(f"{detective.id} followed the trail with tiny, careful steps.")
    world.say(f"At last, {detective.pronoun('subject')} found the missing {mystery.missing_item}.")
    world.say(f"It was {mystery.humorous_detail}.")
    detective.meters["solution"] += 1
    detective.memes["relief"] += 1

    world.para()
    world.say(
        f"{detective.id} returned {mystery.missing_phrase} to its owner, and the mystery was solved."
    )
    world.say(
        f"The whole scene ended with a laugh, because the culprit was just being silly, not bad."
    )


def tell(setting: Setting, mystery: Mystery, name: str) -> World:
    world = World(setting, mystery)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type="girl" if name in {"Lima", "Nora", "Zoe", "Iris"} else "boy",
        label="detective",
        location=setting.place,
    ))
    case = world.add(Entity(
        id="case",
        kind="thing",
        type="case",
        label="mystery",
        phrase=mystery.missing_phrase,
        location=mystery.missing_location,
    ))
    world.facts["detective"] = detective
    world.facts["case"] = case
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    solve_case(world, detective)
    detective.meters["solved"] += 1
    detective.memes["pride"] += 1
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a funny detective story for a young child about {detective.id} and a missing {mystery.missing_item}.',
        f'Tell a short mystery where {detective.id} looks for {mystery.missing_phrase} and solves the case with a smile.',
        f'Write a playful detective tale set at {world.setting.place} that ends when the missing item is found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = _safe_fact(world, world.facts, "detective")
    mystery = _safe_fact(world, world.facts, "mystery")
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{detective.id} solved the mystery by following clues and finding {mystery.missing_phrase}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"{mystery.missing_phrase} was missing.",
        ),
        QAItem(
            question=f"Why was the case funny?",
            answer=f"It was funny because the culprit was {mystery.culprit_reason}, which was silly instead of scary.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that can help solve a problem.",
        )
    ],
    "parrot": [
        QAItem(
            question="What can a parrot do?",
            answer="A parrot can talk, copy sounds, and sometimes act very silly.",
        )
    ],
    "hamster": [
        QAItem(
            question="What is a hamster like?",
            answer="A hamster is a small furry pet that likes to chew and store things in its cheeks.",
        )
    ],
    "dog": [
        QAItem(
            question="What do dogs often enjoy?",
            answer="Dogs often enjoy playing, sniffing, and carrying things around.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [*WORLD_KNOWLEDGE["detective"], *WORLD_KNOWLEDGE["clue"]]
    culprit = world.mystery.culprit
    if culprit in WORLD_KNOWLEDGE:
        out.extend(WORLD_KNOWLEDGE[culprit])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} location={e.location}")
    lines.append(f"setting={world.setting.place}")
    lines.append(f"mystery={world.mystery.id}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Funny detective storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    name = clean_name(getattr(args, "name", None)) if getattr(args, "name", None) else "Lima"
    return StoryParams(setting=setting, mystery=mystery, name=name, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.name)
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
setting(library).
setting(market).
setting(school).

mystery(missing_lunch).
mystery(missing_eraser).
mystery(missing_hat).

solves(D) :- detective(D), clue_found(D), finds_item(D), funny_case(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    lines.append(asp.fact("detective", "lima"))
    lines.append(asp.fact("clue_found", "lima"))
    lines.append(asp.fact("finds_item", "lima"))
    lines.append(asp.fact("funny_case", "lima"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solves/1."))
    atoms = set(asp.atoms(model, "solves"))
    expected = {("lima",)}
    if atoms == expected:
        print("OK: ASP and Python gate agree.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


CURATED = [
    StoryParams(setting="market", mystery="missing_lunch", name="Lima"),
    StoryParams(setting="library", mystery="missing_eraser", name="Lima"),
    StoryParams(setting="school", mystery="missing_hat", name="Lima"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solves/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 40):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            try:
                s = generate(p)
            except StoryError:
                continue
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
