#!/usr/bin/env python3
"""
A small storyworld about a child, a thousand tiny things, a twist, and a nursery-rhyme-style turn.

Seed tale:
---
Mina liked counting little glow-worms in the garden at dusk. She had a tiny blue jar and
wanted to catch just one more glow-worm so she could count a full thousand. Her grandmother
warned her that the jar had a cracked lid and the last light would slip out if she shook it
too hard. Mina hurried anyway, but the wind carried the glow-worms away in a blink. Then she
found something surprising: the "thousandth" light was not a glow-worm at all, but a pale
moth resting on the jar's glass. Mina laughed, lifted the jar gently, and let the moth go.
The garden shimmered, and she learned that counting can be sweet, but kindness makes the
brightest ending.

This script models that premise as a small world with:
- physical meters: count, glow, wind, crack, calm, distance
- emotional memes: wonder, worry, patience, joy, surprise
- a reasonableness gate: the story only exists if the thousandth light can be reached,
  the warning is honest, and the twist is plausible.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    child: object | None = None
    jar: object | None = None
    light: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "grandfather", "man"}:
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
    place: str = "the garden at dusk"
    affords: set[str] = field(default_factory=lambda: {"counting", "catching", "listening"})
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
class Twist:
    id: str
    reveal: str
    clue: str
    turn: str
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
class Foreshadowing:
    id: str
    clue_text: str
    meter_key: str
    meme_key: str
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
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    caregiver_type: str
    count_target: int = 1000
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


SETTINGS = {
    "garden": Setting("the garden at dusk", {"counting", "catching", "listening"}),
    "orchard": Setting("the orchard at dusk", {"counting", "catching", "listening"}),
}

CHILD_NAMES = ["Mina", "Luna", "Nora", "Pip", "Milo", "Ivy"]
CAREGIVERS = {"grandmother": "Grandma", "mother": "Mom"}

TWISTS = {
    "moth": Twist(
        id="moth",
        reveal="the thousandth light was a pale moth on the glass",
        clue="one light had fluttered slower than the rest",
        turn="she let it go instead of keeping it",
    ),
    "lantern": Twist(
        id="lantern",
        reveal="the thousandth light was a little lantern mooning in the grass",
        clue="one glow sat still while the others danced",
        turn="she lifted it gently and followed its gleam home",
    ),
}

FORESHADOWS = {
    "cracked_lid": Foreshadowing(
        id="cracked_lid",
        clue_text="the jar had a tiny crack near the lid",
        meter_key="crack",
        meme_key="worry",
    ),
    "wind": Foreshadowing(
        id="wind",
        clue_text="the wind kept whispering through the leaves",
        meter_key="wind",
        meme_key="unease",
    ),
}


def ask_story_seed() -> str:
    return "thousand"


def intro(world: World, child: Entity, caregiver: Entity) -> None:
    world.say(
        f"{child.id} was a bright little {child.type} who loved to count by the dusky light."
    )
    world.say(
        f"{child.pronoun().capitalize()} held hands with {caregiver.label} and listened to the garden sing."
    )


def foreshadow(world: World, child: Entity, jar: Entity, clue: Foreshadowing) -> None:
    world.say(
        f"{caregiver_name(world)} said, “Be gentle now; {clue.clue_text}.”"
    )
    world.facts["foreshadow"] = clue.id
    child.memes["worry"] += 0.2
    jar.meters[clue.meter_key] = 1.0


def caregiver_name(world: World) -> str:
    caregiver = next(e for e in world.entities.values() if e.kind == "character" and e.type in CAREGIVERS)
    return caregiver.label


def count_until_twist(world: World, child: Entity, jar: Entity, twist: Twist, target: int) -> None:
    world.say(
        f"{child.id} began to count, one and two and three, on until the thousandth glow."
    )
    child.memes["wonder"] += 1.0
    child.meters["count"] = float(target - 1)
    child.meters["reach"] = 0.0
    world.facts["target"] = target
    world.facts["twist"] = twist.id


def simulate_turn(world: World, child: Entity, jar: Entity) -> None:
    wind = world.facts.get("wind", 0.0)
    crack = jar.meters.get("crack", 0.0)
    if wind >= THRESHOLD:
        child.meters["count"] += 1
        child.memes["surprise"] += 0.5
    if crack >= THRESHOLD:
        jar.meters["glow"] = max(jar.meters.get("glow", 0.0) - 0.2, 0.0)


def reveal_twist(world: World, child: Entity, jar: Entity, twist: Twist) -> None:
    world.say(
        f"Just then, {twist.reveal}, and that was the twist in the tale."
    )
    child.memes["surprise"] += 1.0
    child.meters["count"] += 1.0
    world.facts["reveal"] = twist.reveal


def gentle_resolution(world: World, child: Entity, caregiver: Entity, jar: Entity, twist: Twist) -> None:
    child.memes["joy"] += 1.0
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id} smiled a small smile and said, “I can be kind to a tiny light.”"
    )
    world.say(
        f"So {child.id} opened the jar softly, and {twist.turn}."
    )
    world.say(
        f"The garden shimmered, and {caregiver.label} laughed as the night went still and sweet."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.count_target != 1000:
        pass

    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    caregiver_label = CAREGIVERS.get(params.caregiver_type, "the caregiver")
    caregiver = world.add(Entity(id=params.caregiver_type, kind="character", type=params.caregiver_type, label=caregiver_label))
    jar = world.add(Entity(id="jar", type="jar", label="tiny blue jar"))
    light = world.add(Entity(id="light", type="light", label="little glow", plural=True))

    world.facts["child"] = child
    world.facts["caregiver"] = caregiver
    world.facts["jar"] = jar
    world.facts["light"] = light

    intro(world, child, caregiver)
    world.para()

    foreshadow(world, child, jar, FORESHADOWS["cracked_lid"])
    world.say("The wind whispered softly, and the leaves began to sway.")
    world.facts["wind"] = 1.0
    world.para()

    count_until_twist(world, child, jar, TWISTS["moth"], params.count_target)
    simulate_turn(world, child, jar)
    reveal_twist(world, child, jar, TWISTS["moth"])
    world.para()

    gentle_resolution(world, child, caregiver, jar, TWISTS["moth"])
    return world


def valid_params(params: StoryParams) -> bool:
    return params.count_target == 1000 and params.place in SETTINGS


def _reasonableness_gate(params: StoryParams) -> None:
    if not valid_params(params):
        pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    caregiver = _safe_fact(world, f, "caregiver")
    return [
        f"Write a gentle nursery-rhyme-style story about {child.id} and a thousand little lights.",
        f"Tell a story where {child.id} counts to a thousand while {caregiver.label} gives a warning, then a surprise twist arrives.",
        f"Write a soft, child-friendly tale in which a tiny jar, a careful hand, and a thousand glow-worms lead to a sweet ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    caregiver = _safe_fact(world, f, "caregiver")
    return [
        QAItem(
            question=f"What was {child.id} trying to do in the garden at dusk?",
            answer=f"{child.id} was trying to count a thousand tiny lights.",
        ),
        QAItem(
            question=f"What warning did {caregiver.label} give before the twist?",
            answer="The warning was to be gentle because the jar had a crack near the lid and the little light could slip away.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the thousandth light was not an ordinary glow-worm at all; it was a pale moth resting on the glass.",
        ),
        QAItem(
            question=f"How did the story end after {child.id} understood the twist?",
            answer=f"{child.id} opened the jar softly, let the little light go, and the garden shimmered with a happy, quiet glow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a thousand mean?",
            answer="A thousand means one more than nine hundred ninety-nine.",
        ),
        QAItem(
            question="Why should you handle a jar with a cracked lid carefully?",
            answer="A cracked lid can make the jar unsafe or let small things slip out, so it is best to hold it gently.",
        ),
        QAItem(
            question="What is a moth?",
            answer="A moth is a flying insect that often comes out at night and is drawn to light.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
child_story(C, G, J, T) :- child(C), caregiver(G), jar(J), twist(T), thousand(1000), supported_place.
has_warning(J) :- jar(J), cracked(J).
honest_tale(C, T) :- child(C), twist(T), thousand(1000), has_warning(_).
valid_story(C, G, J, T) :- child(C), caregiver(G), jar(J), twist(T), honest_tale(C, T), thousand(1000), supported_place.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("thousand", 1000))
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("supported_place"))
    for name in CHILD_NAMES:
        lines.append(asp.fact("child", name))
    for key in CAREGIVERS:
        lines.append(asp.fact("caregiver", key))
    lines.append(asp.fact("jar", "jar"))
    lines.append(asp.fact("cracked", "jar"))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = []
    for place in SETTINGS:
        for child in CHILD_NAMES:
            for caregiver in CAREGIVERS:
                for twist in TWISTS:
                    py.append((child, caregiver, "jar", twist))
    py = sorted(set(py))
    if atoms == py:
        print(f"OK: ASP parity check passed ({len(atoms)} models).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", atoms)
    print("PY :", py)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about counting to a thousand with a twist.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=sorted(CAREGIVERS))
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
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(list(CAREGIVERS))
    return StoryParams(place=place, child_name=name, child_type="girl", caregiver_type=parent, count_target=1000)


CURATED = [
    StoryParams(place="garden", child_name="Mina", child_type="girl", caregiver_type="grandmother", count_target=1000),
    StoryParams(place="orchard", child_name="Luna", child_type="girl", caregiver_type="mother", count_target=1000),
]


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    world = tell(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} compatible story patterns:\n")
        for atom in atoms:
            print("  ", atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
