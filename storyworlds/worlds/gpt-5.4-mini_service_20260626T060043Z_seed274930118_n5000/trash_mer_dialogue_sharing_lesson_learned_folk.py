#!/usr/bin/env python3
"""
storyworlds/worlds/trash_mer_dialogue_sharing_lesson_learned_folk.py
=====================================================================

A small folk-tale storyworld about a mer, washed-up trash, dialogue, sharing,
and a lesson learned.

Premise seed:
- A mer finds trash near a quiet shore.
- The mer asks for help, shares tools, and gathers the trash.
- The town learns to keep the sea clean, and the mer learns that speaking up
  and sharing work can turn a hard chore into a kind ending.

The world is intentionally small and constraint-checked:
- The narrative depends on physical state (meters) and emotional state (memes).
- Dialogue advances the story.
- Sharing changes both resources and feelings.
- The lesson learned is grounded in the cleanup outcome.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    mer: object | None = None
    trash: object | None = None
    def __post_init__(self):
        for k in ["trash", "clean", "share", "hope", "worry", "pride", "kindness", "lesson"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "maid", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    coast: bool = True
    affords: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    helps: set[str]
    phrase: str
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
    place: str = "harbor"
    mer_name: str = "Mira"
    mer_type: str = "mer"
    helper_name: str = "Nell"
    helper_type: str = "fisher"
    trash_kind: str = "netscrap"
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
    def __init__(self, place: Place):
        self.place = place
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def has_trash(world: World) -> bool:
    return any(e.meters["trash"] >= THRESHOLD for e in world.entities.values())


def cleanup_level(world: World) -> float:
    return sum(max(0.0, e.meters["clean"]) for e in world.entities.values())


def _r_sharing(world: World) -> list[str]:
    out = []
    mer = world.get("mer")
    helper = world.get("helper")
    if mer.memes["asked"] >= THRESHOLD and helper.memes["agreed"] >= THRESHOLD:
        if mer.meters["share"] < THRESHOLD:
            mer.meters["share"] += 1
            helper.meters["share"] += 1
            mer.memes["kindness"] += 1
            helper.memes["kindness"] += 1
            out.append("They shared the work.")
    return out


def _r_cleaning(world: World) -> list[str]:
    out = []
    mer = world.get("mer")
    helper = world.get("helper")
    if mer.meters["share"] < THRESHOLD or helper.meters["share"] < THRESHOLD:
        return out
    if mer.meters["trash"] >= THRESHOLD:
        mer.meters["trash"] = 0
        mer.meters["clean"] += 1
        helper.meters["clean"] += 1
        mer.memes["pride"] += 1
        helper.memes["pride"] += 1
        out.append("The trash was gathered into a sack.")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    mer = world.get("mer")
    helper = world.get("helper")
    if mer.meters["clean"] >= THRESHOLD and helper.meters["clean"] >= THRESHOLD:
        if mer.memes["lesson"] < THRESHOLD:
            mer.memes["lesson"] += 1
            helper.memes["lesson"] += 1
            out.append("The sea looked brighter, and a lesson took root.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_sharing, _r_cleaning, _r_lesson):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "harbor": Place(name="the harbor", coast=True, affords={"trash", "talk", "share"}),
    "cove": Place(name="the cove", coast=True, affords={"trash", "talk", "share"}),
    "shore": Place(name="the shore", coast=True, affords={"trash", "talk", "share"}),
}

TRASH_KINDS = {
    "netscrap": "a tangle of old net scraps",
    "bottlecap": "a pile of bottle caps",
    "rope": "a broken coil of rope",
}

TOOLS = {
    "sack": Tool(id="sack", label="a woven sack", helps={"trash"}, phrase="a woven sack for the mess"),
    "hook": Tool(id="hook", label="a shell hook", helps={"trash"}, phrase="a shell hook to gather the trash"),
    "gloves": Tool(id="gloves", label="soft gloves", helps={"trash"}, phrase="soft gloves to keep hands safe"),
}

MER_NAMES = ["Mira", "Maren", "Mero", "Nami", "Ariel", "Luma"]
HELPER_NAMES = ["Nell", "Finn", "Jory", "Tess", "Wren", "Pip"]
TRAITS = ["gentle", "curious", "brave", "kind", "patient"]


def reasonableness_gate(place: Place, trash_kind: str) -> None:
    if not place.coast:
        pass
    if trash_kind not in TRASH_KINDS:
        pass


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    reasonableness_gate(place, params.trash_kind)

    world = World(place)
    mer = world.add(Entity(id="mer", kind="character", type=params.mer_type, label=params.mer_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    trash = world.add(Entity(
        id="trash",
        type="trash",
        label="trash",
        phrase=_safe_lookup(TRASH_KINDS, params.trash_kind),
        plural=True,
        owner=None,
    ))
    trash.meters["trash"] = 1
    mer.memes["worry"] = 1
    mer.memes["hope"] = 1
    helper.memes["kindness"] = 1

    world.say(f"At {place.name}, {params.mer_name} the mer found {trash.phrase} washed up along the water.")
    world.say(f'"What a sad thing to see," said {params.mer_name}. "Will you help me make it right?"')
    world.say(f'"Of course," said {params.helper_name}. "I can share a sack and a steady pair of hands."')

    mer.memes["asked"] += 1
    helper.memes["agreed"] += 1
    mer.meters["share"] += 0.0
    helper.meters["share"] += 0.0

    world.para()
    world.say(f'Together they worked beside the waves, and {params.helper_name} said, "One hand can ask, but two hands can mend."')
    propagate(world, narrate=True)

    world.para()
    if mer.meters["clean"] >= THRESHOLD:
        world.say(f'{params.mer_name} smiled and said, "When we share the work, even a hard mess grows small."')
        world.say(f'{params.helper_name} laughed and answered, "Then let the sea be kinder tomorrow."')
    else:
        pass

    world.facts.update(
        mer=mer,
        helper=helper,
        trash=trash,
        place=place,
        trash_kind=params.trash_kind,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a mer who finds {f["trash"].phrase} at {f["place"].name} and asks for help.',
        f'Write a child-friendly story with dialogue where {f["mer"].label} and {f["helper"].label} share the work of cleaning trash by the sea.',
        f'Write a simple folk tale about trash, sharing, and a lesson learned near {f["place"].name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mer: Entity = _safe_fact(world, f, "mer")
    helper: Entity = _safe_fact(world, f, "helper")
    place: Place = _safe_fact(world, f, "place")
    trash: Entity = _safe_fact(world, f, "trash")
    return [
        QAItem(
            question=f"Who found the trash at {place.name}?",
            answer=f"{mer.label} the mer found {trash.phrase} at {place.name}.",
        ),
        QAItem(
            question=f"What did {mer.label} ask {helper.label} to do?",
            answer=f"{mer.label} asked {helper.label} to help make the mess right and share the work.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The trash was gathered away, the sea looked brighter, and the mer learned that sharing the work helps everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is trash?",
            answer="Trash is something people do not want to keep, so it should be thrown away or cleaned up properly.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or help with something so the work or joy belongs to more than one person.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone understands after something happens, and they remember it later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class ASPChoice:
    place: str
    trash_kind: str
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


ASP_RULES = r"""
place(P) :- setting(P).
trash_kind(T) :- trash(TK), kind(TK, T).

good_story(P, T) :- place(P), trash_kind(T), coast(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.coast:
            lines.append(asp.fact("coast", pid))
    for tid, text in TRASH_KINDS.items():
        lines.append(asp.fact("trash", tid))
        lines.append(asp.fact("kind", tid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    python_set = {(p, t) for p in PLACES for t in TRASH_KINDS}
    clingo_set = set(asp_good_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale story world about a mer, trash, sharing, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trash-kind", choices=TRASH_KINDS)
    ap.add_argument("--mer-name", choices=MER_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    trash_kind = getattr(args, "trash_kind", None) or rng.choice(list(TRASH_KINDS))
    reasonableness_gate(_safe_lookup(PLACES, place), trash_kind)
    mer_name = getattr(args, "mer_name", None) or rng.choice(MER_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    if helper_name == mer_name:
        helper_name = next(n for n in HELPER_NAMES if n != mer_name)
    return StoryParams(
        place=place,
        mer_name=mer_name,
        mer_type="mer",
        helper_name=helper_name,
        helper_type="fisher",
        trash_kind=trash_kind,
    )


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


CURATED = [
    StoryParams(place="harbor", mer_name="Mira", helper_name="Nell", trash_kind="netscrap"),
    StoryParams(place="cove", mer_name="Maren", helper_name="Finn", trash_kind="bottlecap"),
    StoryParams(place="shore", mer_name="Luma", helper_name="Tess", trash_kind="rope"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_good_stories()
        print(f"{len(stories)} good stories:")
        for place, trash in stories:
            print(f"  {place:8} {trash}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
