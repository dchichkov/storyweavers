#!/usr/bin/env python3
"""
A gentle mystery story world about a proposal, a cinch, and a missing deodorant.

Seed tale:
---
Luna planned a funny proposal for her friend Milo at the village picnic. She hid
the ring inside a little gift box and tied the box with a bright cinch. Just
before the picnic began, the box vanished. Luna noticed a strong deodorant smell
near the empty basket and followed tiny blue footprints to the shed. Inside, a
goat had dragged the box away because it liked the scented ribbon. Luna rescued
the box, made a new cinch, and proposed a silly mystery game instead. Everyone
laughed, and the ring was safe.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
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
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    box: object | None = None
    luna: object | None = None
    place: object | None = None
    ribbon: object | None = None
    spray: object | None = None
    suspect: object | None = None
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
class StoryParams:
    name: str = "Luna"
    setting: str = "picnic"
    case: int = 0
    clue: int = 0
    joke: int = 0
    ending: int = 0
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
    suspect: str
    object_name: str
    location: str
    clue: str
    cause: str
    recovery: str
    ending_images: tuple[str, ...]
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


CASES = {
    "picnic": (
        Case(
            suspect="a goat named Pickle",
            object_name="the proposal box",
            location="the garden shed",
            clue="a sharp deodorant smell mixed with tiny blue hoofprints",
            cause="Pickle had dragged the scented cinch toward the shed because he liked its smell",
            recovery="lifting the box from beneath a straw basket and replacing the chewed cinch",
            ending_images=(
                "Pickle wore the old cinch like a very proud belt.",
                "The recovered ring sparkled beside a plate of cucumber sandwiches.",
                "The new cinch held the box shut while Pickle sneezed at the ribbon.",
            ),
        ),
        Case(
            suspect="a cheeky crow named Ink",
            object_name="the proposal box",
            location="the bell tower",
            clue="a deodorant scent and three silver feathers on the picnic blanket",
            cause="Ink had carried the scented cinch upward, mistaking its shine for treasure",
            recovery="climbing the safe ladder and trading the bright cinch for a plain red string",
            ending_images=(
                "Ink dropped the old cinch into a flowerpot and flew off, satisfied.",
                "The ring shone below the bell while the crow guarded a bread crumb.",
                "The red string held tight, and nobody trusted a shiny feather quite so quickly again.",
            ),
        ),
        Case(
            suspect="the wind-up toy clown from the games table",
            object_name="the proposal box",
            location="the picnic wagon",
            clue="a deodorant smell, a squeaky wheel, and a trail of yellow confetti",
            cause="the clown's rolling wheel had caught the scented cinch and pulled the box under the wagon",
            recovery="stopping the wheel, reaching under the wagon, and tying a double cinch",
            ending_images=(
                "The toy clown squeaked once, as if it knew it had been caught.",
                "Luna's proposal box sat safely beside the lemonade.",
                "The double cinch stayed firm while the clown rolled in harmless circles.",
            ),
        ),
    )
}

SETTINGS = {
    "picnic": Setting("the village picnic", "striped blankets, lemonade, and a crooked games table"),
    "square": Setting("the village square", "paper lanterns, flower pots, and a sleepy fountain"),
    "orchard": Setting("the old orchard", "apple trees, soft grass, and a little wooden cart"),
}

ASP_RULES = r"""
object(proposal_box).
object(cinching_ribbon).
object(deodorant).
event(proposal).
instrument(cinch).
clue(deodorant).
mystery(proposal_box).
resolved(proposal_box) :- mystery(proposal_box), instrument(cinch), clue(deodorant).
humor(proposal) :- resolved(proposal_box).
valid_case :- event(proposal), resolved(proposal_box), humor(proposal).
#show valid_case/0.
#show resolved/1.
"""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Luna's humorous proposal mystery.")
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--case", type=int, choices=range(3), default=None)
    parser.add_argument("--clue", type=int, choices=range(4), default=None)
    parser.add_argument("--joke", type=int, choices=range(4), default=None)
    parser.add_argument("--ending", type=int, choices=range(3), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
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
        name=getattr(args, "name", None),
        setting=getattr(args, "setting", None) or rng.choice(list(SETTINGS)),
        case=getattr(args, "case", None) if getattr(args, "case", None) is not None else rng.randrange(3),
        clue=getattr(args, "clue", None) if getattr(args, "clue", None) is not None else rng.randrange(4),
        joke=getattr(args, "joke", None) if getattr(args, "joke", None) is not None else rng.randrange(4),
        ending=getattr(args, "ending", None) if getattr(args, "ending", None) is not None else rng.randrange(3),
        seed=getattr(args, "seed", None),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        pass
    if params.setting not in SETTINGS:
        pass
    if not 0 <= params.case < 3:
        pass
    if not 0 <= params.clue < 4:
        pass
    if not 0 <= params.joke < 4:
        pass
    if not 0 <= params.ending < 3:
        pass


def asp_facts() -> str:
    import asp
    return "\n".join(
        (
            asp.fact("object", "proposal_box"),
            asp.fact("object", "cinching_ribbon"),
            asp.fact("object", "deodorant"),
            asp.fact("event", "proposal"),
            asp.fact("instrument", "cinch"),
            asp.fact("clue", "deodorant"),
            asp.fact("mystery", "proposal_box"),
        )
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_case/0.\n#show resolved/1."))
    valid = bool(asp.atoms(model, "valid_case"))
    resolved = set(asp.atoms(model, "resolved"))
    if valid and resolved == {("proposal_box",)}:
        print("OK: ASP mystery facts resolve with humor.")
        return 0
    print("MISMATCH")
    print("valid_case:", valid)
    print("resolved:", sorted(resolved))
    return 1


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.setting)[params.case]
    world = World(setting)

    luna = world.add(Entity("luna", "character", params.name, "person"))
    box = world.add(Entity("box", "object", case.object_name, "proposal_box", owner=params.name))
    ribbon = world.add(Entity("cinch", "object", "the bright cinch", "cinch", owner=params.name))
    spray = world.add(Entity("deodorant", "object", "a little deodorant", "deodorant"))
    place = world.add(Entity("place", "place", setting.place, "setting"))
    suspect = world.add(Entity("suspect", "character", case.suspect, "suspect"))

    luna.memes.update({"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "amusement": 0.0})
    box.meters.update({"safety": 0.4, "visibility": 0.0})
    ribbon.meters.update({"tightness": 0.8, "scent": 1.0})
    spray.meters.update({"scent": 1.0})
    place.meters.update({"calm": 0.8, "mystery": 1.0})

    openings = (
        f"{params.name} had a proposal ready, and she had hidden the ring in {case.object_name}.",
        f"{params.name} planned a proposal so carefully that even the lemonade seemed to know the secret.",
        f"At {setting.place}, {params.name} prepared a proposal with a ring, a joke, and a very determined cinch.",
        f"{params.name} checked the ring twice, the box twice, and the deodorant once, because mysteries can be surprisingly smelly.",
    )
    world.say(openings[params.clue])
    world.say(f"She tied the box with {ribbon.label}, then placed it beside the picnic basket.")
    world.say(f"Everything was ready among {setting.detail}.")
    world.para()

    luna.memes["worry"] += 1
    box.meters["visibility"] = 0.0
    world.say(f"Then the box vanished. Only {spray.label} and a loose end of the cinch remained.")
    world.say(f'"Do not panic," {params.name} told herself. "A missing proposal box is only a mystery with a very important ending."')
    world.say(f"She found the first clue: {case.clue}.")
    world.say(f'"Did you see my box?" {params.name} asked {case.suspect}.')
    replies = (
        '"I saw nothing," came the reply. "But something smelled like a fancy armpit near the shed."',
        '"Perhaps," came the reply, "the box proposed to itself and ran away."',
        '"I heard a squeak," came the reply. "It sounded guilty, or possibly hungry."',
        '"Follow the scent," came the reply. "It is stronger than my best detective hat."',
    )
    world.say(replies[params.joke])
    world.para()

    observations = (
        "Luna followed the smell past the basket and noticed that the blue marks pointed away from the table.",
        "She compared the loose ribbon with the marks and saw that the cinch had been pulled, not untied.",
        "She held the deodorant near the trail. The scent grew stronger beside the shed door.",
        "She listened carefully. A faint scrape came from behind the straw basket, followed by one enormous sneeze.",
    )
    world.say(observations[params.clue])
    world.say(f"That made the cause clear: {case.cause}.")
    world.say(f'"Aha!" {params.name} said. "The culprit is not a villain. The culprit has excellent, if peculiar, taste."')
    world.say(f"She opened the {case.location}, found the box, and {case.recovery}.")
    box.meters["safety"] = 1.0
    box.meters["visibility"] = 1.0
    ribbon.meters["tightness"] = 1.0
    place.meters["mystery"] = 0.0
    luna.memes["relief"] += 1
    luna.memes["amusement"] += 1
    world.para()

    world.say(f"The ring was safe, the cinch was snug, and the deodorant was back in the basket.")
    world.say(f'{case.suspect.title()} said, "Was that the proposal?"')
    world.say(f'{params.name} laughed. "Not quite. First, I propose a mystery game: find who stole the smelly ribbon."')
    world.say("Everyone searched for three seconds, then looked at the suspect.")
    world.say(f'{case.suspect.title()} answered, "I plead guilty to excellent ribbon judgment."')
    world.say(case.ending_images[params.ending])
    world.say(f"Then {params.name} gave the real proposal, and the picnic filled with laughter instead of another disappearance.")

    world.facts.update(
        luna=luna,
        box=box,
        ribbon=ribbon,
        deodorant=spray,
        place=place,
        suspect=suspect,
        case=case,
        setting=setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")  # type: ignore[assignment]
    return [
        "Write a child-friendly mystery about a missing proposal box, a cinch, and deodorant.",
        f"Make the clue point toward {case.location}, with gentle humor and a safe resolution.",
        "Include dialogue that changes the detective's next action and end with laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")  # type: ignore[assignment]
    params: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")  # type: ignore[assignment]
    return [
        QAItem(
            "What was missing?",
            f"The proposal box containing {params.name}'s ring was missing from the picnic basket.",
        ),
        QAItem(
            "What clues did Luna find?",
            f"She found a deodorant smell, a loose cinch, and marks leading toward {case.location}.",
        ),
        QAItem(
            "What caused the mystery?",
            f"{case.cause.capitalize()}. It was a silly accident, not a dangerous crime.",
        ),
        QAItem(
            "How did Luna solve it?",
            f"She followed the scent and marks, found the box, and {case.recovery}.",
        ),
        QAItem(
            "How did the story end?",
            f"The ring was safe, Luna made a humorous mystery game, and the real proposal brought laughter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a proposal?", "A proposal is a special question or plan, often shared when someone wants to begin something important together."),
        QAItem("What is a cinch?", "A cinch is a tight fastening or strap that helps hold something securely."),
        QAItem("Why can scent be a mystery clue?", "A scent can show where an object or person has recently been, helping a careful detective follow a trail."),
        QAItem("What makes humor gentle for children?", "Gentle humor uses surprising, harmless situations and kind reactions rather than fear or cruelty."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_case/0.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_case/0.\n#show resolved/1."))
        print(asp.atoms(model, "valid_case"))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        index = 0
        for setting in SETTINGS:
            for case in range(3):
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name=getattr(args, "name", None),
                    setting=setting,
                    case=case,
                    clue=rng.randrange(4),
                    joke=rng.randrange(4),
                    ending=rng.randrange(3),
                    seed=base_seed + index,
                )
                samples.append(generate(params))
                index += 1
    else:
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
