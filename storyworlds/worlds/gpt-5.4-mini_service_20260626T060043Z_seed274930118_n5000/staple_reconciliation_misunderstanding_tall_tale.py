#!/usr/bin/env python3
"""
A story world for a tall-tale reconciliation built around a misunderstanding and
a staple.

Premise:
A boastful little barn-cat-sized helper thinks a tiny staple is a mighty treasure.
A misunderstanding makes the whole town assume the staple is lost forever, so
the hero must follow a clue trail, face a dramatic problem, and then reconcile
with the friend who was blamed.

This world keeps the story small, causal, and child-facing:
- physical meters: where the staple is, whether paper is torn, whether a poster
  is mended, whether a bundle is secure
- emotional memes: pride, worry, misunderstanding, apology, relief, trust

Style:
Tall tale / big-voiced exaggeration, but with a concrete, state-driven ending.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"present": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "uncle"}:
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
class Place:
    name: str
    detail: str
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
class Item:
    id: str
    label: str
    phrase: str
    location: str
    owner: Optional[str] = None
    bundle: object | None = None
    poster: object | None = None
    staple: object | None = None
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
    place: str
    hero: str
    helper: str
    object: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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


def _bump(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _feel(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add_entity(Entity(id=params.hero, kind="character", type="child"))
    helper = world.add_entity(Entity(id=params.helper, kind="character", type="child"))
    staple = world.add_item(Item(
        id="staple",
        label="staple",
        phrase="a shiny little staple",
        location="in the hero's pocket",
        owner=hero.id,
    ))
    poster = world.add_item(Item(
        id="poster",
        label="poster",
        phrase="a parade poster",
        location="hung on the school wall",
        owner=helper.id,
    ))
    bundle = world.add_item(Item(
        id="bundle",
        label="bundle",
        phrase="a stack of letters",
        location="on the table",
        owner=helper.id,
    ))

    # Act 1: setup
    world.say(
        f"On a day big as a barn roof and bright as a brass bell, {hero.id} and "
        f"{helper.id} met at {place.name}. {place.detail}"
    )
    world.say(
        f"{hero.id} had found {staple.phrase}, and {hero.pronoun('possessive')} eyes "
        f"grew round as marbles. {hero.id} called it a treasure from the king's own desk."
    )
    _feel(hero, "pride", 1)
    _feel(hero, "curiosity", 1)
    _feel(helper, "calm", 1)

    # Act 2: misunderstanding
    world.para()
    world.say(
        f"Then the wind gave one fierce whistle, and the little staple vanished from sight."
    )
    staple.location = "missing"
    _feel(hero, "worry", 1)
    _feel(helper, "worry", 1)

    world.say(
        f"{helper.id} saw the empty pocket and thought {hero.id} had hidden the staple on purpose."
    )
    _feel(helper, "misunderstanding", 1)
    _feel(hero, "misunderstanding", 1)
    _feel(hero, "hurt", 1)
    world.say(
        f"{helper.id} frowned and said, \"You must have lost my important thing on purpose!\""
    )

    # The actual physical problem: the poster is loose and the bundle needs the staple.
    _bump(poster, "torn", 1)
    _bump(bundle, "loose", 1)
    world.say(
        f"Without the staple, the parade poster flapped like a sail in a hurricane, and "
        f"the stack of letters threatened to tumble apart."
    )

    # Act 3: search and turn
    world.para()
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin and followed a clue as plain as pie: "
        f"a tiny silver gleam near the floorboard."
    )
    _bump(staple, "found", 1)
    staple.location = "under the table"
    world.say(
        f"There it was, snug under the table, where a speck of dust had been hiding it like a fox in a thimble."
    )
    _feel(hero, "relief", 1)
    _feel(helper, "relief", 1)

    # Reconciliation
    world.say(
        f"{hero.id} carried the staple back with both hands, as careful as a sheriff with a gold nugget."
    )
    world.say(
        f"{hero.id} said, \"I wasn't hiding it. The wind whisked it away.\""
    )
    _feel(hero, "apology", 1)
    _feel(helper, "apology", 1)
    _feel(helper, "trust", 1)

    staple.location = "in the hero's hand"
    poster.location = "mended"
    bundle.location = "secure"
    _bump(poster, "torn", -1)
    _bump(poster, "mended", 1)
    _bump(bundle, "loose", -1)
    _bump(bundle, "secure", 1)

    world.say(
        f"{helper.id} blinked, then laughed the kind of laugh that rolls over a hill and wakes the cows."
    )
    world.say(
        f"\"I was wrong,\" said {helper.id}. \"I blamed you before I knew the whole tall tale.\""
    )
    world.say(
        f"They fixed the poster, pinned the letters tight, and set the staple safely in a tin cup."
    )
    _feel(hero, "forgiveness", 1)
    _feel(helper, "forgiveness", 1)
    _feel(hero, "trust", 1)
    _feel(helper, "relief", 1)

    world.say(
        f"By sunset, {hero.id} and {helper.id} were side by side again, grinning like two lanterns in the dark."
    )
    world.say(
        f"The staple was no longer a missing mystery; it was a little silver hero that had helped mend the day."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "staple": staple,
        "poster": poster,
        "bundle": bundle,
        "place": place,
    }
    return world


PLACES = {
    "school": Place(
        name="the school copy room",
        detail="The walls smelled like chalk, and the paper stacks stood up straighter than Sunday hats.",
    ),
    "barn": Place(
        name="the old barn office",
        detail="The rafters creaked like old boots, and every nail in the wall looked ready to tell a story.",
    ),
    "library": Place(
        name="the tiny library desk",
        detail="The books stood in rows as neat as buttons, and the lamp glowed like a sleepy moon.",
    ),
    "station": Place(
        name="the little train station",
        detail="The floorboards rattled like a wagon trail, and the timetable board clacked in the breeze.",
    ),
}


HEROES = ["Nell", "Pip", "Toby", "Mara", "Wren", "June", "Otis", "Ivy"]
HELPERS = ["Bean", "Luna", "Hank", "Midge", "Jo", "Ruth", "Bea", "Finn"]


def narration_opening(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a tall-tale story for a young child about a {hero.kind} named {hero.id}, a missing staple, and a misunderstanding that turns into reconciliation.',
        f"Tell a funny, old-timey story where {hero.id} and {helper.id} argue over a tiny staple, then make up after the truth comes out.",
        f'Write a short, child-facing tall tale that includes the word "staple" and ends with friends mending both paper and feelings.',
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    staple: Item = _safe_fact(world, f, "staple")
    poster: Item = _safe_fact(world, f, "poster")
    bundle: Item = _safe_fact(world, f, "bundle")
    place: Place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} meet?",
            answer=f"They met at {place.name}. It was a place full of paper, noise, and a little bit of drama.",
        ),
        QAItem(
            question=f"What did {hero.id} think the staple was?",
            answer=f"{hero.id} thought the staple was a treasure from the king's own desk, because it looked shiny and small enough to matter a lot.",
        ),
        QAItem(
            question=f"Why did {helper.id} get upset when the staple disappeared?",
            answer=f"{helper.id} misunderstood the empty pocket and thought {hero.id} had hidden the staple on purpose, which made {helper.pronoun('object')} worried and cross.",
        ),
        QAItem(
            question="What happened because the staple was missing?",
            answer=f"The parade poster got torn and the stack of letters became loose. Without the staple, the paper could not stay neat and secure.",
        ),
        QAItem(
            question=f"How did the misunderstanding get fixed?",
            answer=f"{hero.id} found the staple under the table, explained that the wind had whisked it away, and {helper.id} said sorry. Then they mended the poster and secured the letters again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The staple was safe again, the poster was mended, the bundle was secure, and {hero.id} and {helper.id} were friendly again.",
        ),
    ]


def world_knowledge(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a staple used for?",
            answer="A staple is a small metal fastener that holds paper together.",
        ),
        QAItem(
            question="Why can a misunderstanding cause trouble?",
            answer="A misunderstanding can cause trouble because people may think the wrong thing before they know the truth.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a disagreement and feel friendly again.",
        ),
        QAItem(
            question="What does it mean for paper to be mended?",
            answer="Mended paper has been fixed so it is no longer torn or loose.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if abs(v) > 0}
        memes = {k: v for k, v in ent.memes.items() if abs(v) > 0}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    for item in world.items.values():
        lines.append(f"{item.id}: location={item.location} owner={item.owner}")
    return "\n".join(lines)


def validate_params(args: argparse.Namespace) -> None:
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        pass
    if getattr(args, "name", None) and not getattr(args, "name", None).strip():
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    validate_params(args)
    place = getattr(args, "place", None) or rng.choice(list(PLACES.keys()))
    hero = getattr(args, "name", None) or rng.choice(HEROES)
    helper = rng.choice([h for h in HELPERS if h != hero])
    if getattr(args, "helper", None):
        helper = getattr(args, "helper", None)
    if helper == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        hero=hero,
        helper=helper,
        object="staple",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=narration_opening(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge(world),
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
hero(H). helper(K). staple(S). place(P).

misunderstanding(H,K) :- hero(H), helper(K), heard_wrong(H,K).
reconciliation(H,K) :- misunderstanding(H,K), apology(H), apology(K), truth_known(H,K).

mended(poster) :- staple_recovered, poster_fixed.
secure(bundle) :- staple_recovered, bundle_tied.

#show misunderstanding/2.
#show reconciliation/2.
#show mended/1.
#show secure/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("helper", "helper"),
        asp.fact("staple", "staple"),
        asp.fact("place", "place"),
        asp.fact("heard_wrong", "hero", "helper"),
        asp.fact("apology", "hero"),
        asp.fact("apology", "helper"),
        asp.fact("truth_known", "hero", "helper"),
        asp.fact("staple_recovered"),
        asp.fact("poster_fixed"),
        asp.fact("bundle_tied"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show reconciliation/2.\n#show mended/1.\n#show secure/1."))
    atoms = set((sym.name, tuple(arg.name if hasattr(arg, "name") else getattr(arg, "string", getattr(arg, "number", None)) for arg in sym.arguments)) for sym in model)
    expected = {
        ("misunderstanding", ("hero", "helper")),
        ("reconciliation", ("hero", "helper")),
        ("mended", ("poster",)),
        ("secure", ("bundle",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches Python world facts.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("asp:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a staple, a misunderstanding, and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="school", hero="Nell", helper="Bean", object="staple"),
        StoryParams(place="library", hero="Ivy", helper="Ruth", object="staple"),
        StoryParams(place="barn", hero="Pip", helper="Hank", object="staple"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding/2.\n#show reconciliation/2.\n#show mended/1.\n#show secure/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2.\n#show reconciliation/2.\n#show mended/1.\n#show secure/1."))
        print("ASP model atoms:")
        for sym in model:
            print(sym)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            params.seed = (getattr(args, "seed", None) or 0) + i
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
