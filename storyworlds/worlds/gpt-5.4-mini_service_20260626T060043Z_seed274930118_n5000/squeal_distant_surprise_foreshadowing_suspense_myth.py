#!/usr/bin/env python3
"""
storyworlds/worlds/squeal_distant_surprise_foreshadowing_suspense_myth.py
=========================================================================

A small mythic storyworld about a foretold sound, a hidden cause, and a gentle
surprise. The tale grows from a distant squeal in a sacred place, lingers in
suspense, and ends with a revelation that changes how the characters see the
world.

Core premise:
- A young keeper hears a distant squeal from a shrine, bridge, or grove.
- An elder has already noticed foreshadowing signs: dust, hush, and a strange
  echo.
- The hero enters suspense while deciding whether to open the sealed place.
- The surprise is that the sound comes from a living, harmless, wondrous creature
  or mechanism that needed help, not punishment.
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
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
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
class Place:
    id: str
    label: str
    hush: str
    echo: str
    affords: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    sound: str
    source: str
    hidden: str
    risk: str
    foreshadow: str
    reveal: str
    answer: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    riskless: bool = False
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


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
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
        import copy
        clone = World(self.place, self.mystery)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _pron_name(ent: Entity) -> str:
    return ent.id


def _article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def _do_suspense(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{_pron_name(hero)} paused at the shrine gate, listening to a distant squeal "
        f"that seemed to drift from under the stones."
    )
    world.say(
        f"{elder.label_word} had already seen the foreshadowing: a thin line of dust on "
        f"the threshold, and a candle that would not stay lit."
    )


def _do_warning(world: World, elder: Entity, hero: Entity) -> None:
    world.say(
        f'"Do not strike the seal," {elder.pronoun("subject")} whispered. '
        f'"The old sound is not always a cruel sound."'
    )
    hero.memes["wonder"] += 1
    hero.memes["fear"] += 1


def _do_open(world: World, hero: Entity, tool: Tool) -> None:
    hero.meters["bravery"] = hero.meters.get("bravery", 0) + 1
    hero.meters["care"] = hero.meters.get("care", 0) + 1
    world.say(
        f"{_pron_name(hero)} lifted {tool.phrase} and worked the stone seal with care, "
        f"while the squeal rose again from below."
    )


def _do_reveal(world: World, hero: Entity, companion: Entity) -> None:
    m = world.mystery
    world.say(
        f"Then came the surprise: beneath the shrine sat {m.answer}, not a beast at all, "
        f"but a living thing that had been calling for help."
    )
    world.say(
        f"{_pron_name(hero)} saw that the {m.hidden} had been trapped by the old stone, "
        f"and {companion.pronoun('subject')} knelt beside it at once."
    )


def _do_resolve(world: World, hero: Entity, companion: Entity) -> None:
    m = world.mystery
    hero.memes["joy"] += 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["suspense"] = 0.0
    world.say(
        f"Together they freed the little hidden one, and the distant squeal turned to a "
        f"bright chirp of relief."
    )
    world.say(
        f"The elder smiled, for the foreshadowing had been true: the sign was a warning, "
        f"but also a promise that mercy would be needed."
    )
    world.say(
        f"By nightfall, the {m.source} was quiet again, and {hero.id} walked home knowing "
        f"that a strange sound can lead to a kinder ending."
    )


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    companion: str
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


PLACES = {
    "shrine": Place(
        id="shrine",
        label="the old shrine",
        hush="quiet as a held breath",
        echo="soft and long",
        affords={"open", "listen", "pray"},
    ),
    "bridge": Place(
        id="bridge",
        label="the stone bridge",
        hush="still as river glass",
        echo="deep and round",
        affords={"open", "listen", "cross"},
    ),
    "grove": Place(
        id="grove",
        label="the moonlit grove",
        hush="gentle with leaves",
        echo="thin and silver",
        affords={"open", "listen", "wait"},
    ),
}

MYSTERIES = {
    "lantern-bird": Mystery(
        id="lantern-bird",
        sound="distant squeal",
        source="the shrine",
        hidden="lantern-bird",
        risk="break the stone seal",
        foreshadow="a candle that would not stay lit",
        reveal="golden feathers",
        answer="a tiny lantern-bird",
        tags={"bird", "light", "squeal"},
    ),
    "river-foal": Mystery(
        id="river-foal",
        sound="distant squeal",
        source="the bridge",
        hidden="river-foal",
        risk="crack the bridge stone",
        foreshadow="water trembling under moonlight",
        reveal="wet hoofprints",
        answer="a small river-foal",
        tags={"water", "horse", "squeal"},
    ),
    "moon-goat": Mystery(
        id="moon-goat",
        sound="distant squeal",
        source="the grove",
        hidden="moon-goat",
        risk="startle the sleeping roots",
        foreshadow="silver leaves shaking without wind",
        reveal="a ribbon of moon-white fur",
        answer="a shy moon-goat kid",
        tags={"goat", "moon", "squeal"},
    ),
}

TOOLS = {
    "chisel": Tool(id="chisel", label="bronze chisel", phrase="a bronze chisel", helps="open the seal"),
    "key": Tool(id="key", label="old key", phrase="an old key", helps="turn the latch"),
    "twig": Tool(id="twig", label="ash twig", phrase="an ash twig", helps="lift the latch gently", riskless=True),
}

CURATED = [
    StoryParams(place="shrine", mystery="lantern-bird", name="Mira", companion="elder", seed=None),
    StoryParams(place="bridge", mystery="river-foal", name="Taro", companion="aunt", seed=None),
    StoryParams(place="grove", mystery="moon-goat", name="Nia", companion="priestess", seed=None),
]


class Elder(Entity):
    @property
    def label_word(self) -> str:
        return self.label or self.type


def tell(place: Place, mystery: Mystery, hero_name: str, companion_type: str) -> World:
    world = World(place, mystery)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    if companion_type == "elder":
        companion = world.add(Elder(id="elder", kind="character", type="woman", label="the elder"))
    elif companion_type == "aunt":
        companion = world.add(Elder(id="aunt", kind="character", type="woman", label="the aunt"))
    else:
        companion = world.add(Elder(id="priestess", kind="character", type="priestess", label="the priestess"))

    tool = world.add(Entity(id="tool", type="thing", label="tool", phrase=TOOLS["twig"].phrase))
    world.facts.update(hero=hero, companion=companion, tool=tool, mystery=mystery, place=place)

    world.say(f"Long ago, {hero_name} walked to {place.label}, where the air was {place.hush}.")
    world.say(
        f"That evening, {hero_name} heard a {mystery.sound} from the stones below, and the echo "
        f"came back {place.echo}."
    )
    world.say(f"It was not the first sign. Earlier, there had been {mystery.foreshadow}.")
    world.para()
    _do_suspense(world, hero, companion)
    _do_warning(world, companion, hero)
    _do_open(world, hero, tool)
    world.para()
    _do_reveal(world, hero, companion)
    _do_resolve(world, hero, companion)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for a child where a distant squeal leads {f["hero"].id} to a hidden surprise.',
        f"Tell a suspenseful, gentle myth about {f['hero'].id} at {f['place'].label} with foreshadowing and a kind ending.",
        f"Write a story where an elder warns a child not to force a stone seal, but the strange sound turns out to be harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    comp: Entity = _safe_fact(world, f, "companion")
    place: Place = _safe_fact(world, f, "place")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"Who heard the distant squeal at {place.label}?",
            answer=f"{hero.id} heard it first, while {comp.label_word} listened beside {hero.id}.",
        ),
        QAItem(
            question="What foreshadowing sign hinted that the strange sound was important?",
            answer=f"The foreshadowing sign was {mystery.foreshadow}.",
        ),
        QAItem(
            question="What was the surprise at the end of the story?",
            answer=f"The surprise was that {mystery.answer} was trapped below the stones and needed help.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"{hero.id} and {comp.label_word} freed the little hidden one, and the sound changed "
                f"from a worrying squeal into a happy sign of relief."
            ),
        ),
    ]


WORLD_QA = [
    QAItem(question="What is a shrine?", answer="A shrine is a sacred place where people may leave offerings, pray, or remember old stories."),
    QAItem(question="What is suspense in a story?", answer="Suspense is the feeling of waiting and not yet knowing what will happen next."),
    QAItem(question="What is foreshadowing?", answer="Foreshadowing is when a story gives a small clue that something important may happen later."),
    QAItem(question="What is a surprise in a story?", answer="A surprise is an unexpected turn that changes what the characters thought was true."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("sound", mid, "squeal"))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
place_story(P,M) :- place(P), mystery(M), affords(P,open), sound(M,squeal).
good_story(P,M) :- place_story(P,M).
#show place_story/2.
#show good_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(p, m) for p in PLACES for m in MYSTERIES}
    if asp_set == py_set:
        print(f"OK: ASP matches Python gate ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of distant squeals, foreshadowing, suspense, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["elder", "aunt", "priestess"])
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(sorted(MYSTERIES))
    name = getattr(args, "name", None) or rng.choice(["Mira", "Nia", "Taro", "Sora", "Luna", "Arin"])
    companion = getattr(args, "companion", None) or rng.choice(["elder", "aunt", "priestess"])
    return StoryParams(place=place, mystery=mystery, name=name, companion=companion, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name, params.companion)
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
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(combos)} compatible mythic story pairs:")
        for p, m in combos:
            print(f"  {p:8} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
