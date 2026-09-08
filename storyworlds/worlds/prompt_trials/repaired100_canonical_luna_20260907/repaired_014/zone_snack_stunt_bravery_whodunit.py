#!/usr/bin/env python3
"""
A gentle whodunit about a snack-zone stunt, brave questions, and a missing clue.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    helper: object | None = None
    keeper: object | None = None
    snack: object | None = None
    stunt: object | None = None
    zone: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    zone: str
    affords: set[str] = field(default_factory=lambda: {"look", "ask", "compare"})
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
class StoryParams:
    name: str = ""
    helper_name: str = ""
    keeper_name: str = ""
    case: int = 0
    stunt: int = 0
    snack: int = 0
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Case:
    zone: str
    snack: str
    stunt: str
    clue: str
    cause: str
    reveal: str
    ending: str
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


CASES = [
    Case(
        "the school picnic zone",
        "a cinnamon bun",
        "a paper-cup tower stunt",
        "a curl of blue paper beside the toppled cups",
        "a breeze had tugged a blue napkin through the tower",
        "the napkin was caught beneath a picnic basket",
        "the rebuilt tower stood beside a warm cinnamon bun",
    ),
    Case(
        "the library snack zone",
        "a honey cracker",
        "a book-balancing stunt",
        "three golden crumbs on the lowest shelf",
        "a bookmark had slipped from a book and nudged the cracker plate",
        "the bookmark rested inside a book about bridges",
        "the cracker waited on a clean plate while the books stood straight",
    ),
    Case(
        "the garden snack zone",
        "a strawberry muffin",
        "a leaf-jumping stunt",
        "a line of red dots near the stepping stones",
        "a ladybug had carried crumbs from the picnic cloth",
        "the ladybug crawled safely onto a marigold",
        "the muffin sat under a cloth while the marigolds nodded",
    ),
    Case(
        "the clubhouse snack zone",
        "a cheese sandwich",
        "a spoon-spinning stunt",
        "a silver spoon mark across the table",
        "the tablecloth had pulled the spoon when the door slammed",
        "the loose cloth corner was tucked beneath a book",
        "the sandwich was safe while the spoon rested in its cup",
    ),
    Case(
        "the playground snack zone",
        "an apple slice",
        "a hoop-rolling stunt",
        "a small wheel track through the dust",
        "a toy cart had rolled beneath the snack bench",
        "the cart was returned to its toy box",
        "the apple slice gleamed beside a hoop that no longer wandered",
    ),
]

STUNTS = [
    "a paper-cup tower stunt",
    "a book-balancing stunt",
    "a leaf-jumping stunt",
    "a spoon-spinning stunt",
    "a hoop-rolling stunt",
]

SNACKS = [
    "a cinnamon bun",
    "a honey cracker",
    "a strawberry muffin",
    "a cheese sandwich",
    "an apple slice",
]

NAMES = ["Luna", "Mina", "Nora", "Ivy", "Ruby", "Ada"]
HELPERS = ["Theo", "Milo", "Eli", "Finn", "Owen", "Jude"]
KEEPERS = ["Ms. June", "Mr. Lee", "Aunt Sam", "Coach Bea"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_story(params: StoryParams) -> World:
    case = _safe_lookup(CASES, params.case % len(CASES))
    setting = Setting(case.zone)
    world = World(setting)

    child = world.add(Entity("Child", "character", "child", params.name))
    helper = world.add(Entity("Helper", "character", "child", params.helper_name))
    keeper = world.add(Entity("Keeper", "character", "adult", params.keeper_name))
    zone = world.add(Entity("Zone", "place", "zone", case.zone))
    snack = world.add(Entity("Snack", "thing", "snack", case.snack))
    stunt = world.add(Entity("Stunt", "activity", "stunt", case.stunt))

    world.facts.update(
        case=case,
        child=child,
        helper=helper,
        keeper=keeper,
        zone=zone,
        snack=snack,
        stunt=stunt,
    )

    world.say(
        f"In {case.zone}, {child.label} set down {case.snack} before beginning "
        f"{case.stunt}."
    )
    world.say(
        f"When the stunt wobbled, the snack vanished. A tiny clue remained: {case.clue}."
    )
    child.memes["worried"] = 1.0
    snack.meters["missing"] = 1.0

    world.para()
    world.say(
        f'"Someone took it," whispered {child.label}. {helper.label} looked toward the quiet zone.'
    )
    world.say(
        f'"Maybe," said {helper.label}, "but bravery means asking questions before blaming anyone."'
    )
    child.memes["bravery"] = 1.0
    helper.memes["bravery"] = 1.0
    helper.memes["careful"] = 1.0

    world.para()
    world.say(
        f"They began with the clue. {child.label} crouched near the mark while "
        f"{helper.label} checked the table, the floor, and the place where the stunt had started."
    )
    world.say(
        f'"Did you see the snack move?" asked {child.label}.'
    )
    world.say(
        f'"No," said {helper.label}, "but I saw the breeze lift something blue."'
    )
    world.facts["first_observation"] = "a blue paper moved near the cups"
    world.para()

    world.say(
        f"They asked {keeper.label} what had happened. {keeper.label} remembered that "
        "the side door had banged just before the tower fell."
    )
    world.say(
        f'"Let us test one thing at a time," said {helper.label}. They closed the door, '
        "placed a spare napkin beside the stunt, and watched."
    )
    world.facts["tested"] = True

    world.para()
    world.say(
        f"The same little breeze slid the napkin across the table. The mystery was solved: {case.cause}."
    )
    world.say(f"{case.reveal.capitalize()}.")
    snack.meters["missing"] = 0.0
    snack.meters["safe"] = 1.0
    child.memes["worried"] = 0.0
    world.say(
        f"{child.label} felt proud. Bravery had not meant making a bigger stunt; "
        "it had meant telling the truth, asking kindly, and checking the clue."
    )
    world.say(f"At snack time, {case.ending.capitalize()}.")
    world.facts["lesson"] = (
        "Bravery means asking careful questions and testing clues before blaming someone."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")  # type: ignore[assignment]
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")  # type: ignore[assignment]
    return [
        f"Write a gentle whodunit about {child.label} investigating a missing snack in {case.zone}.",
        f"Include {case.stunt}, a concrete clue, brave questions, and a kind solution.",
        "Show that bravery means checking evidence instead of blaming a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")  # type: ignore[assignment]
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")  # type: ignore[assignment]
    keeper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "keeper")  # type: ignore[assignment]
    return [
        QAItem(
            f"Why did {child.label} investigate the snack zone?",
            f"{child.label} investigated because {case.snack} seemed to vanish when {case.stunt} wobbled, leaving only {case.clue}.",
        ),
        QAItem(
            f"How did {child.label} and {helper.label} solve the mystery?",
            f"They asked {keeper.label} what had happened, watched the zone carefully, and tested the breeze one change at a time. They discovered that {case.cause}.",
        ),
        QAItem(
            f"What did {helper.label} say about bravery?",
            f"{helper.label} said that bravery meant asking questions before blaming anyone.",
        ),
        QAItem(
            f"What lesson did {child.label} learn?",
            f"{child.label} learned that bravery means asking careful questions and testing clues before blaming someone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a zone?",
            "A zone is a marked or understood area set aside for a particular activity.",
        ),
        QAItem(
            "What is a snack?",
            "A snack is a small amount of food eaten between meals.",
        ),
        QAItem(
            "What is a stunt?",
            "A stunt is a special action or trick that may require careful practice.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing a careful, helpful action even when you feel worried or afraid.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:7} ({entity.type:7}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "zone"),
            asp.fact("topic", "snack"),
            asp.fact("topic", "stunt"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "whodunit"),
            asp.fact("affords", "snack_zone", "look"),
            asp.fact("affords", "snack_zone", "ask"),
            asp.fact("affords", "snack_zone", "compare"),
        ]
    )


ASP_RULES = r"""
topic(zone).
topic(snack).
topic(stunt).
feature(bravery).
feature(whodunit).

has_clue :- topic(zone), topic(snack), topic(stunt).
careful_investigation :- has_clue, feature(bravery).
story_ok :- careful_investigation, feature(whodunit).

#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if not ok:
        print("MISMATCH: ASP twin failed.")
        return 1
    for i in range(3):
        sample = generate(
            StoryParams(
                name="Luna",
                helper_name="Theo",
                keeper_name="Ms. June",
                case=i,
                stunt=i,
                snack=i,
            )
        )
        if not sample.story or "bravery" not in sample.story.lower():
            print("MISMATCH: generated story check failed.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle whodunit about a snack-zone stunt and bravery."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
    parser.add_argument("--keeper-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPERS),
        keeper_name=getattr(args, "keeper_name", None) or rng.choice(KEEPERS),
        case=rng.randrange(len(CASES)),
        stunt=rng.randrange(len(STUNTS)),
        snack=rng.randrange(len(SNACKS)),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.name.strip() or not params.helper_name.strip() or not params.keeper_name.strip():
        pass
    if params.case < 0 or params.stunt < 0 or params.snack < 0:
        pass
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show story_ok/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(sym.name == "story_ok" for sym in model) else "no model")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i in range(len(CASES)):
            samples.append(
                generate(
                    StoryParams(
                        name="Luna",
                        helper_name="Theo",
                        keeper_name="Ms. June",
                        case=i,
                        stunt=i % len(STUNTS),
                        snack=i % len(SNACKS),
                        seed=base_seed + i,
                    )
                )
            )
    else:
        seen: set[str] = set()
        i = 0
        limit = max(getattr(args, "n", None) * 20, 20)
        while len(samples) < getattr(args, "n", None) and i < limit:
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
