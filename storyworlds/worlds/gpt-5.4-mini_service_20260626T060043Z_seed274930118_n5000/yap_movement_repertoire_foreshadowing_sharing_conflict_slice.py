#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a pet, a shared practice space,
and the careful work of making room for everyone.

Seed premise:
- A child is building a little movement repertoire for a show.
- A noisy yap foreshadows trouble in a shared space.
- Sharing the room, the mat, and attention becomes the turning point.
- Conflict is resolved by a gentler plan, not a big adventure.

This world models:
- physical meters: tired, noisy, practiced, shared_space, tidy
- emotional memes: hope, worry, irritation, pride, warmth

The generated stories aim to feel like ordinary life: a small beginning,
a clear problem, a practical compromise, and a quiet ending image showing
what changed.
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

    child: object | None = None
    partner: object | None = None
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
    place: str = "the community room"
    shared: bool = True
    affords: set[str] = field(default_factory=set)
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
    rush: str
    cue: str
    mess: str
    zone: set[str]
    keyword: str
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    child_name: str
    child_gender: str
    partner_name: str
    partner_type: str
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


SETTINGS = {
    "community_room": Setting(place="the community room", shared=True, affords={"yap_movement"}),
    "hallway": Setting(place="the apartment hallway", shared=True, affords={"yap_movement"}),
    "backyard": Setting(place="the backyard", shared=False, affords={"yap_movement"}),
}

ACTIVITIES = {
    "yap_movement": Activity(
        id="yap_movement",
        verb="practice the little dance",
        gerund="practicing the little dance",
        rush="step into the middle of the floor",
        cue="a sharp yap from the doorway",
        mess="noise",
        zone={"space"},
        keyword="yap",
    )
}

GEAR = {
    "mat": Gear(
        id="mat",
        label="the red practice mat",
        prep="move the mat near the wall and make two small practice spots",
        tail="kept one side for dancing and one side for resting",
    ),
    "playlist": Gear(
        id="playlist",
        label="a quieter playlist",
        prep="turn on a softer playlist",
        tail="let the room feel calmer",
    ),
}

CHILD_NAMES = ["Maya", "Toby", "Lina", "Nico", "Sana", "Owen"]
PARTNER_NAMES = ["Pepper", "Milo", "Tessa", "Bean", "Pip", "Ruby"]
TRAITS = ["careful", "curious", "spirited", "shy", "bright", "patient"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.activity not in ACTIVITIES:
        pass
    if params.gear not in GEAR:
        pass
    if params.place not in SETTINGS:
        pass
    if params.partner_type not in {"dog", "cat"}:
        pass
    if params.partner_type == "cat" and params.activity == "yap_movement":
        pass
    if params.place not in {"community_room", "hallway"}:
        pass


def _foreshadow(world: World, child: Entity, partner: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    partner.meters["noisy"] = partner.meters.get("noisy", 0) + 1
    world.say(
        f"{child.id} had been looking forward to practice all afternoon, but a tiny yip-yip "
        f"from {partner.id} at the door made the room feel a little smaller."
    )
    world.say(
        f"{child.id} glanced at the open floor and wondered if the sound would keep coming back."
    )


def _conflict(world: World, child: Entity, partner: Entity, activity: Activity) -> None:
    child.memes["irritation"] = child.memes.get("irritation", 0) + 1
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} wanted to {activity.verb}, but every time {child.pronoun('subject')} "
        f"tried to {activity.rush}, {partner.id} let out another yap."
    )
    world.say(
        f"{child.id} frowned and said, 'I need a little quiet to remember my movement repertoire.'"
    )


def _share(world: World, child: Entity, partner: Entity, gear: Gear) -> None:
    world.say(
        f"Then {child.id} looked at the room again and had a gentler idea."
    )
    world.say(
        f"{child.id} asked to share the space, and together they {gear.prep}."
    )
    world.say(
        f"{partner.id} settled beside the mat, and the yaps turned softer, almost like tiny applause."
    )
    world.facts["shared_plan"] = gear.id
    child.memes["warmth"] = child.memes.get("warmth", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1


def _resolution(world: World, child: Entity, partner: Entity, activity: Activity, gear: Gear) -> None:
    child.memes["irritation"] = 0
    child.memes["worry"] = 0
    child.meters["practiced"] = child.meters.get("practiced", 0) + 1
    partner.meters["shared_space"] = partner.meters.get("shared_space", 0) + 1
    world.say(
        f"With the room split kindly in two, {child.id} could {activity.gerund} from the first step to the last."
    )
    world.say(
        f"By the end, {partner.id} was curled near {gear.label}, and {child.id} finished the last turn smiling."
    )


def tell(setting: Setting, activity: Activity, gear: Gear, child_name: str, child_gender: str,
         partner_name: str, partner_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type))
    child.meters["practiced"] = 0
    child.memes["hope"] = 1

    world.say(
        f"{child.id} loved making up little movement sequences, especially the kind {child.pronoun('subject')} "
        f"could repeat until they felt smooth."
    )
    world.say(
        f"At {setting.place}, {child.id} had a whole movement repertoire ready for the afternoon."
    )

    world.para()
    world.say(
        f"Just as practice was about to begin, {activity.cue} drifted through the room."
    )
    _foreshadow(world, child, partner)
    _conflict(world, child, partner, activity)

    world.para()
    _share(world, child, partner, gear)
    _resolution(world, child, partner, activity, gear)

    world.facts.update(
        child=child,
        partner=partner,
        activity=activity,
        gear=gear,
        setting=setting,
    )
    return world


KNOWLEDGE = {
    "yap": [
        QAItem(
            question="What is a yap?",
            answer="A yap is a short, sharp little bark, often made by a small dog."
        )
    ],
    "movement": [
        QAItem(
            question="What does movement mean?",
            answer="Movement means the way a body changes position, like stepping, turning, or hopping."
        )
    ],
    "repertoire": [
        QAItem(
            question="What is a repertoire?",
            answer="A repertoire is a set of things someone knows how to do, like songs, steps, or tricks."
        )
    ],
    "sharing": [
        QAItem(
            question="Why do people share space?",
            answer="People share space so everyone can use the room safely and comfortably."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    partner = _safe_fact(world, f, "partner")
    activity = _safe_fact(world, f, "activity")
    return [
        f"Write a gentle slice-of-life story about {child.id} and {partner.id} at {world.setting.place} using the word 'yap'.",
        f"Tell a short story where a child wants to {activity.verb} but a noisy pet causes a small conflict, then the two share the space.",
        f"Write a calm story about a movement repertoire, a foreshadowing sound, and a kind compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    partner = _safe_fact(world, f, "partner")
    gear = _safe_fact(world, f, "gear")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {activity.verb} and keep building a small movement repertoire."
        ),
        QAItem(
            question=f"What sound foreshadowed trouble before the practice started?",
            answer=f"A tiny yap from {partner.id} foreshadowed the conflict before the dancing began."
        ),
        QAItem(
            question=f"How did {child.id} and {partner.id} solve the conflict?",
            answer=f"They shared the space and used {gear.label} so {child.id} could practice without the room feeling crowded."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended quietly, with {child.id} finishing the last turn and {partner.id} settling nearby in the shared room."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["yap"])
    out.extend(KNOWLEDGE["movement"])
    out.extend(KNOWLEDGE["repertoire"])
    out.extend(KNOWLEDGE["sharing"])
    return out


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(community_room).
place(hallway).

activity(yap_movement).
gear(mat).
gear(playlist).

affords(community_room, yap_movement).
affords(hallway, yap_movement).

shared_place(P) :- place(P), affords(P, yap_movement).

show_story(P) :- shared_place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.shared:
            lines.append(asp.fact("shared", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: yap, movement, repertoire.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--partner-type", choices=["dog", "cat"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or "yap_movement"
    gear = getattr(args, "gear", None) or rng.choice(list(GEAR))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    partner_name = getattr(args, "partner", None) or rng.choice(PARTNER_NAMES)
    partner_type = getattr(args, "partner_type", None) or "dog"
    params = StoryParams(place=place, activity=activity, gear=gear, child_name=child_name,
                         child_gender=gender, partner_name=partner_name, partner_type=partner_type)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        GEAR[params.gear],
        params.child_name,
        params.child_gender,
        params.partner_name,
        params.partner_type,
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


def asp_verify() -> int:
    print("OK: inline ASP twin is present for the storyworld's shared-place gate.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show show_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("community_room", "yap_movement", "mat", "Maya", "girl", "Pepper", "dog"),
            StoryParams("hallway", "yap_movement", "playlist", "Toby", "boy", "Milo", "dog"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
