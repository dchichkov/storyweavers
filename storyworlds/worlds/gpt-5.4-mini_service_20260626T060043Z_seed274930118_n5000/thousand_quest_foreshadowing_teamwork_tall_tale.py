#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thousand_quest_foreshadowing_teamwork_tall_tale.py
==============================================================================================================================

A tall-tale storyworld about a quest that grows as long as a thousand wagon
tracks, with foreshadowing that hints at the fix and teamwork that carries it
home.

The seed image:
---
A tiny settlement needs the Silver Bell at the top of Thousand Hill before dusk.
Old signs warn that the hill listens, the wind answers, and no one brings back
the bell alone. Three friends set out with a map, a rope, and a mule named Bean.
The journey is hard, the hints are strange, and each friend learns that the job
is too big for one pair of hands.
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
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bell: object | None = None
    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    name: str
    mile_marker: int
    affords: set[str] = field(default_factory=set)
    omen: str = ""
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
class Quest:
    name: str
    goal: str
    path: str
    obstacle: str
    clue: str
    ending: str
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
    helps: set[str]
    carries: set[str]
    plural: bool = False
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    helper: str
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


PLACES = {
    "town": Place(name="Mossy Town", mile_marker=0, affords={"quest"}, omen="The bell rope could be heard in the wind."),
    "hill": Place(name="Thousand Hill", mile_marker=1000, affords={"quest"}, omen="A stone sign pointed upward and said, 'One road, many feet.'"),
    "harbor": Place(name="Blue Harbor", mile_marker=12, affords={"quest"}, omen="The gulls kept circling like they knew a secret."),
}

QUESTS = {
    "bell": Quest(
        name="bell",
        goal="bring back the Silver Bell",
        path="climb the long road to the top of Thousand Hill",
        obstacle="the hill kept changing its steps",
        clue="the old sign promised that three small efforts could do a giant job",
        ending="the bell rang softly as if it had been waiting for friends",
        tags={"thousand", "quest", "foreshadowing", "teamwork"},
    ),
    "lantern": Quest(
        name="lantern",
        goal="recover the lantern from the echo cave",
        path="follow the lantern-road into the dark",
        obstacle="every shadow looked like the wrong door",
        clue="a crack in the wall glowed before anyone touched it",
        ending="the lantern glimmered like a small sun in a child’s hands",
        tags={"quest", "foreshadowing", "teamwork"},
    ),
}

TOOLS = [
    Tool(id="rope", label="a rope", helps={"climb", "carry"}, carries={"bell"}, plural=False),
    Tool(id="map", label="a map", helps={"find"}, carries=set(), plural=False),
    Tool(id="mule", label="Bean the mule", helps={"carry", "climb"}, carries={"bell", "lantern"}, plural=False),
    Tool(id="lantern", label="a lantern", helps={"see"}, carries=set(), plural=False),
]

HERO_NAMES = ["Mara", "Bix", "Jory", "Lena", "Tess", "Pip", "Oren", "Nia"]
HELPER_NAMES = ["Bean", "Milo", "Sage", "Dot", "Rook", "Lark"]
TRAITS = ["bold", "spry", "clever", "stubborn", "bright-eyed", "quick-handed"]


class ScriptError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest world with foreshadowing and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, quest=quest, hero=hero, helper=helper)


def _tool_for(quest: Quest) -> Tool:
    if quest.name == "bell":
        return next(t for t in TOOLS if t.id == "rope")
    return next(t for t in TOOLS if t.id == "lantern")


def tell(place: Place, quest: Quest, hero_name: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="thing", label=helper_name))
    tool = _tool_for(quest)
    gear = world.add(Entity(id=tool.id, kind="thing", label=tool.label, plural=tool.plural, owner=hero.id))
    bell = world.add(Entity(id="prize", kind="thing", label="Silver Bell", phrase="the Silver Bell"))

    hero.memes["hope"] = 1
    helper.memes["helpful"] = 1
    hero.meters["road"] = 0
    hero.meters["resolve"] = 0

    world.say(f"{hero.id} lived where the road began, and {helper.id} was the sort of friend who could hear a trail before the first step hit it.")
    world.say(f"One morning, the town needed {quest.goal}, so {hero.id} and {helper.id} set out on {quest.path}.")
    world.say(f"Before they went, the old sign at the edge of the lane whispered, '{quest.clue}'. That was the first foreshadowing, plain as paint on a fence.")

    world.para()
    world.say(f"The way was long enough to tire a wagon, and the wind had a habit of tugging hats and telling lies.")
    world.say(f"At the third turn, they found another sign: '{place.omen}'")
    world.say(f"{hero.id} looked once at the sign and once at {helper.id}. They both knew the hill was warning them to travel together, not alone.")

    hero.meters["road"] += 500
    helper.meters["road"] += 500
    world.say(f"They shared the load. {hero.id} held the map, {helper.id} steadied the rope, and Bean the mule carried the hard part of the climb.")
    world.say(f"By the time they had climbed a thousand rocky steps, each one had done a small piece, and the giant road had become a dozen ordinary miles.")

    world.para()
    world.say(f"At the top, {quest.obstacle}, but teamwork made a ladder out of worry.")
    hero.memes["fear"] = 1
    helper.memes["courage"] = 1
    world.say(f"{hero.id} tied the rope. {helper.id} listened for the safest stone. Bean braced his hooves like a castle gate.")
    world.say(f"Then the bell was there at last, shining under a patch of sky the color of new tin.")
    world.say(f"They brought back {bell.label}, and {quest.ending}.")
    world.say(f"So the town learned what the hill had been hinting all along: a thousand-step quest is still shorter when friends walk it side by side.")

    world.facts.update(place=place, quest=quest, hero=hero, helper=helper, gear=gear, bell=bell)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    return [
        f"Write a tall-tale story about a quest for {q.goal} that includes the word 'thousand'.",
        f"Tell a child-friendly adventure where {f['hero'].id} and {f['helper'].id} solve {q.name} with teamwork and a hint before the danger.",
        f"Write a short tale with foreshadowing, a long road, and a happy ending at {f['place'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    place: Place = _safe_fact(world, f, "place")
    qa = [
        QAItem(
            question=f"What were {hero.id} and {helper.id} trying to do at {place.name}?",
            answer=f"They were on a quest to {q.goal}. They traveled to {place.name} because the town needed brave help, not just wishful thinking.",
        ),
        QAItem(
            question=f"What was the first hint that the trip would need patience and teamwork?",
            answer=f"The first hint was the sign that said, '{q.clue}'. It warned them before the hardest part of the road arrived.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} handle the long climb?",
            answer=f"They shared the work. {hero.id} carried the map and the rope, {helper.id} watched the stones, and Bean helped with the heavy parts so nobody had to do the whole giant job alone.",
        ),
        QAItem(
            question=f"Why is this quest a tall tale?",
            answer=f"Because the hill was said to have a thousand steps, the wind acted like a talkative old guide, and the whole story makes a small crew sound fit to outwalk a giant mountain.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint about something important that will happen later.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other and share the job so the work gets done together.",
        ),
        QAItem(
            question="Why do tall tales sound so big?",
            answer="Tall tales use extra-big, funny details to make ordinary adventures sound wild and legendary.",
        ),
        QAItem(
            question="Why is a thousand a big number in a story like this?",
            answer="A thousand makes the road sound long and hard, so the helpers have to keep going one step at a time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==",)
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_story(P,Q,H,He) :- place(P), quest(Q), hero(H), helper(He), valid(P,Q).
valid(P,Q) :- place(P), quest(Q).
#show quest_story/4.
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mile_marker", pid, p.mile_marker))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(p, q) for p in PLACES for q in QUESTS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), params.hero, params.helper)
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
    StoryParams(place="hill", quest="bell", hero="Mara", helper="Bean"),
    StoryParams(place="town", quest="lantern", hero="Lena", helper="Sage"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show quest_story/4.\n#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, quest) combos:")
        for p, q in vals:
            print(f"  {p:10} {q}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero} / {p.quest} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
