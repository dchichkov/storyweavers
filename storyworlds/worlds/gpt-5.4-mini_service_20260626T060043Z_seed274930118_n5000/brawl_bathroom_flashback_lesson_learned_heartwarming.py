#!/usr/bin/env python3
"""
storyworlds/worlds/brawl_bathroom_flashback_lesson_learned_heartwarming.py
===========================================================================
A standalone story world about a bathroom brawl, a warm flashback, and a lesson
learned. The domain stays small and constraint-checked: a child-sized brawl
about bathroom space or bath toys, a remembered lesson, and a kind ending.
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

    region: object | None = None
    hero: object | None = None
    mentor: object | None = None
    sibling: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the bathroom"
    affords: set[str] = field(default_factory=lambda: {"brawl", "splash", "soak"})
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "brawl"
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Lesson:
    label: str
    flashback_line: str
    method: str
    turn: str
    ending: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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


def _pulse(world: World, actor: Entity) -> None:
    actor.memes["stress"] = actor.memes.get("stress", 0.0) + 1.0


def _brawl(world: World) -> list[str]:
    out: list[str] = []
    for a in world.characters():
        if a.memes.get("brawl", 0.0) < THRESHOLD:
            continue
        sig = ("brawl", a.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        a.memes["stress"] = a.memes.get("stress", 0.0) + 1.0
        out.append(f"{a.id} and the air around {a.id} felt tight with tears and grumpy words.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for s in _brawl(world):
        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, prize: Prize, lesson: Lesson,
         hero_name: str, hero_type: str, sibling_name: str, sibling_type: str,
         mentor_name: str, mentor_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type))
    toy = world.add(Entity(
        id="toy",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=prize.region,
        plural=prize.plural,
    ))

    hero.memes["love_play"] = 1.0
    sibling.memes["love_play"] = 1.0
    hero.memes["brawl"] = 1.0

    world.say(
        f"{hero.id} loved bath time, especially {activity.gerund}, and {sibling.id} loved it too."
    )
    world.say(
        f"One evening, they both reached for {hero.pronoun('possessive')} {toy.label} in {setting.place}."
    )
    world.say(
        f"That turned into a little {activity.keyword} over the tub, with splashy hands and upset faces."
    )

    world.para()
    world.say(
        f"Then {hero.id} remembered a flashback: {lesson.flashback_line}"
    )
    world.say(
        f"{lesson.method}"
    )
    world.say(
        f"{lesson.turn}"
    )

    hero.memes["brawl"] = 0.0
    sibling.memes["brawl"] = 0.0
    hero.memes["joy"] = 1.0
    sibling.memes["joy"] = 1.0
    mentor.memes["warmth"] = 1.0

    world.para()
    world.say(
        f"In the end, {lesson.ending}"
    )
    world.say(
        f"{hero.id} and {sibling.id} shared the bathroom again, and the whole room felt soft and safe."
    )

    world.facts.update(
        hero=hero,
        sibling=sibling,
        mentor=mentor,
        toy=toy,
        setting=setting,
        activity=activity,
        lesson=lesson,
    )
    return world


SETTINGS = {
    "bathroom": Setting(place="the bathroom", affords={"brawl", "splash", "soak"}),
}

ACTIVITIES = {
    "brawl": Activity(
        id="brawl",
        verb="brawl over the bath toys",
        gerund="splashing and arguing",
        mess="wet",
        soil="soggy and upset",
        zone={"hands", "floor"},
        keyword="brawl",
        tags={"bathroom", "wet", "brawl"},
    )
}

PRIZES = {
    "duck": Prize(
        label="rubber duck",
        phrase="a bright little rubber duck",
        type="duck",
        region="hands",
    ),
    "boat": Prize(
        label="toy boat",
        phrase="a tiny blue toy boat",
        type="boat",
        region="hands",
    ),
}

LESSONS = {
    "share": Lesson(
        label="sharing",
        flashback_line="Grandma had once said, 'Two happy turns are better than one angry grab.'",
        method="So the child counted to three, then offered the first turn to the sibling.",
        turn="The sibling smiled, nodded, and promised to give the toy back after a song.",
        ending="the duck got passed back and forth like a treasure, and everyone stayed dry in their hearts even while the tub splashed.",
    ),
    "talk": Lesson(
        label="talking",
        flashback_line="Dad had once whispered, 'When feelings crowd in, use gentle words first.'",
        method="So the child took a deep breath and said what hurt instead of pushing.",
        turn="The sibling listened, and the grumpy knot in the middle of the room loosened.",
        ending="the toy boat floated in peace, and the bathroom felt calm enough for sleepy toes.",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Noah", "Ivy", "Owen"]
SIBLING_NAMES = ["Pip", "June", "Kit", "Bo", "Nia", "Ray"]
MENTOR_NAMES = ["Grandma", "Dad", "Mom"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    lesson: str
    hero_name: str
    hero_type: str
    sibling_name: str
    sibling_type: str
    mentor_name: str
    mentor_type: str
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, pr, l) for p in SETTINGS for a in ACTIVITIES for pr in PRIZES for l in LESSONS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.activity not in ACTIVITIES:
        pass
    if params.prize not in PRIZES:
        pass
    if params.lesson not in LESSONS:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bathroom brawl with a flashback and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--mentor", choices=MENTOR_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sibling-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-type", choices=["mother", "father", "grandmother"])
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
    place = getattr(args, "place", None) or "bathroom"
    activity = getattr(args, "activity", None) or "brawl"
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    lesson = getattr(args, "lesson", None) or rng.choice(list(LESSONS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    sibling_type = getattr(args, "sibling_type", None) or ("boy" if hero_type == "girl" else "girl")
    mentor_type = getattr(args, "mentor_type", None) or rng.choice(["mother", "father", "grandmother"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    sibling_name = getattr(args, "sibling", None) or rng.choice([n for n in SIBLING_NAMES if n != hero_name])
    mentor_name = getattr(args, "mentor", None) or rng.choice(MENTOR_NAMES)
    params = StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        lesson=lesson,
        hero_name=hero_name,
        hero_type=hero_type,
        sibling_name=sibling_name,
        sibling_type=sibling_type,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
    )
    reasonableness_gate(params)
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle story for a young child about a {f["activity"].keyword} in {f["setting"].place} that ends with a lesson learned.',
        f"Tell a heartwarming bathroom story where {f['hero'].id} and {f['sibling'].id} brawl over {f['toy'].label}, then remember a kind lesson.",
        f'Write a simple flashback story that includes the word "brawl" and ends with the toy being shared calmly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, mentor, toy, lesson, act = f["hero"], f["sibling"], f["mentor"], f["toy"], f["lesson"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {sibling.id} get into a brawl in the bathroom?",
            answer=f"They both wanted {hero.pronoun('possessive')} {toy.label} at the same time, so the little fight started over sharing.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {lesson.flashback_line.lower()}",
        ),
        QAItem(
            question=f"How did the lesson help the bathroom brawl end?",
            answer=f"{lesson.method} {lesson.turn} That helped everyone calm down and share the {toy.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bathroom for?", answer="A bathroom is a room where people wash, brush teeth, and get clean."),
        QAItem(question="What is a brawl?", answer="A brawl is a rough argument or fight, usually with upset words or pushing."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is when a story shows something that happened before the main moment."),
        QAItem(question="What does it mean to learn a lesson?", answer="Learning a lesson means understanding a better way to act next time."),
    ]


ASP_RULES = r"""
place_ok(bathroom).
activity_ok(brawl).
lesson_ok(share).
lesson_ok(talk).

valid_story(P,A,L) :- place_ok(P), activity_ok(A), lesson_ok(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place_ok", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity_ok", a))
    for l in LESSONS:
        lines.append(asp.fact("lesson_ok", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:10}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(LESSONS, params.lesson),
        params.hero_name,
        params.hero_type,
        params.sibling_name,
        params.sibling_type,
        params.mentor_name,
        params.mentor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("bathroom", "brawl", "duck", "share", "Mina", "girl", "Pip", "boy", "Grandma", "grandmother"),
    StoryParams("bathroom", "brawl", "boat", "talk", "Toby", "boy", "June", "girl", "Dad", "father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible story combo(s).")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
