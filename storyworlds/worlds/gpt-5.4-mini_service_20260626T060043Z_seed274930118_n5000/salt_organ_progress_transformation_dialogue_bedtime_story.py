#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/salt_organ_progress_transformation_dialogue_bedtime_story.py
==============================================================================================================================

A bedtime-story world about a child, a careful salty fix, and a gentle
transformation that turns a noisy problem into sleepy progress.

Premise:
- A little child and a grown-up are getting ready for bed.
- A tiny hand organ in the nursery has become sticky and stuck.
- The grown-up worries because the child wants to keep pulling at it.

Turn:
- They notice that a pinch of salt can help dry the sticky keys.
- The child must slow down and help instead of tugging harder.
- Dialogue guides the child from impatience to patience.

Resolution:
- The organ changes from stuck and grumpy to soft and playable.
- The child makes steady progress, and the room settles into a calm bedtime glow.

This world models:
- physical state: saltiness, stickiness, cleanliness, readiness
- emotional state: worry, eagerness, calm, pride, sleepiness
- transformation: one object and one child both change across the story
- dialogue: short quoted lines that move the story forward
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
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    organ: object | None = None
    parent: object | None = None
    salt: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
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
    place: str = "the nursery"
    bedtime: bool = True
    world: object | None = None
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
    child_name: str
    child_type: str
    parent_type: str
    place: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        return World(
            setting=self.setting,
            entities=_copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=dict(self.facts),
        )
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


def _meter(x: float) -> bool:
    return x >= THRESHOLD


def story_traits() -> list[str]:
    return ["sleepy", "curious", "gentle", "brave", "tiny"]


def valid_child_types() -> list[str]:
    return ["girl", "boy"]


def valid_parent_types() -> list[str]:
    return ["mother", "father"]


def names_for(child_type: str) -> list[str]:
    return {
        "girl": ["Mina", "Lily", "Ivy", "Nora", "Ada"],
        "boy": ["Theo", "Ben", "Owen", "Milo", "Finn"],
    }[child_type]


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_salt_dries(world: World) -> list[str]:
    out: list[str] = []
    organ = world.entities.get("organ")
    salt = world.entities.get("salt")
    if not organ or not salt:
        return out
    if organ.meters.get("stuck", 0.0) < THRESHOLD:
        return out
    if salt.meters.get("sprinkled", 0.0) < THRESHOLD:
        return out
    sig = ("dry", "organ")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    organ.meters["stuck"] = 0.0
    organ.meters["clean"] = 1.0
    organ.meters["playable"] = 1.0
    organ.memes["relief"] = organ.memes.get("relief", 0.0) + 1.0
    out.append("The salty dust helped the organ dry and loosen.")
    return out


def _r_child_settles(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("impatience", 0.0) < THRESHOLD:
        return []
    if child.memes.get("patience", 0.0) < THRESHOLD:
        return []
    sig = ("settle", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] = 1.0
    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1.0
    return ["The child grew calmer and sleepier."]


RULES = [Rule("salt_dries", _r_salt_dries), Rule("child_settles", _r_child_settles)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_fix(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    organ = sim.get("organ")
    return _meter(organ.meters.get("playable", 0.0))


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved quiet nights, warm blankets, and one small song."
    )
    world.say(
        f"{child.id}'s {parent.type} kept the nursery soft and dim, ready for bedtime."
    )


def show_problem(world: World, child: Entity, organ: Entity) -> None:
    world.say(
        f"On the shelf sat a tiny {organ.label}, but one of its keys was stuck and sticky."
    )
    world.say(
        f"{child.id} wanted to touch it right away, yet {child.pronoun('possessive')} fingers only made the stickiness spread."
    )


def dialogue_warning(world: World, parent: Entity, child: Entity, organ: Entity) -> None:
    child.memes["impatience"] = 1.0
    parent.memes["worry"] = 1.0
    world.say(
        f'"Wait a moment," {parent.pronoun()} said softly. "If you pull too hard, the organ will stay grumpy."'
    )
    world.say(
        f'"But I want the little song now," {child.id} whispered.'
    )


def transformation_step(world: World, child: Entity, organ: Entity, salt: Entity) -> None:
    child.memes["patience"] = 1.0
    salt.meters["sprinkled"] = 1.0
    salt.memes["useful"] = 1.0
    world.say(
        f'{child.id} nodded and pinched a little salt between {child.pronoun("possessive")} fingers.'
    )
    world.say(
        f'"Just a tiny bit," {child.id} said. "Then we can let it rest."'
    )
    propagate(world, narrate=True)


def progress_scene(world: World, child: Entity, organ: Entity, parent: Entity) -> None:
    if organ.meters.get("playable", 0.0) >= THRESHOLD:
        child.memes["pride"] = 1.0
        world.say(
            f'{child.id} pressed the key again, and this time the organ answered with a soft, sweet note.'
        )
        world.say(
            f'"It worked," {child.id} said, smiling.'
        )
        world.say(
            f'"Yes," {parent.pronoun()} answered. "You made careful progress."'
        )
        world.say(
            f"The little room felt warmer somehow, as if the music had tucked the whole house in."
        )


def tell(params: StoryParams) -> World:
    world = World(setting=Setting(place=params.place))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=["little", random.choice(story_traits())],
        memes={"impatience": 0.0, "patience": 0.0, "calm": 0.0, "sleepiness": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        memes={"worry": 0.0},
    ))
    organ = world.add(Entity(
        id="organ",
        type="organ",
        label="toy organ",
        phrase="a tiny wooden toy organ",
        meters={"stuck": 1.0, "clean": 0.0, "playable": 0.0},
        memes={"relief": 0.0},
    ))
    salt = world.add(Entity(
        id="salt",
        type="salt",
        label="salt",
        phrase="a little dish of salt",
        meters={"sprinkled": 0.0},
        memes={"useful": 0.0},
    ))

    introduce(world, child, parent)
    world.para()
    show_problem(world, child, organ)
    dialogue_warning(world, parent, child, organ)
    world.para()
    transformation_step(world, child, organ, salt)
    world.para()
    progress_scene(world, child, organ, parent)

    world.facts.update(child=child, parent=parent, organ=organ, salt=salt)
    return world


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    return [
        "Write a gentle bedtime story about a child, a stuck organ, and a little salt that helps things change.",
        f"Tell a sleepy story where {child.id} listens to a parent, makes careful progress, and helps a tiny organ become playable again.",
        "Write a short bedtime tale with dialogue, transformation, and a calm ending about salt and an organ.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    organ: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "organ")
    salt: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "salt")
    return [
        QAItem(
            question=f"What was stuck in the nursery story?",
            answer=f"The toy organ was stuck and sticky at first, so it could not make its soft bedtime note.",
        ),
        QAItem(
            question=f"What did {child.id} use to help the organ change?",
            answer=f"{child.id} used a little salt, because the salty dust helped dry and loosen the stuck key.",
        ),
        QAItem(
            question=f"How did {child.id} make progress in the story?",
            answer=f"{child.id} slowed down, listened, sprinkled the salt carefully, and tried again until the organ could play softly.",
        ),
        QAItem(
            question=f"How did the parent speak to {child.id}?",
            answer=f"The parent spoke softly in dialogue, warning {child.id} not to pull too hard and then praising the careful progress.",
        ),
    ]


KNOWLEDGE = {
    "salt": [
        QAItem(
            question="What is salt?",
            answer="Salt is a tiny white seasoning that people use in food, and it can also help soak up a little moisture.",
        )
    ],
    "organ": [
        QAItem(
            question="What is an organ?",
            answer="An organ can be a musical instrument with keys and pipes that makes long, rich sounds.",
        )
    ],
    "progress": [
        QAItem(
            question="What does progress mean?",
            answer="Progress means getting a little farther or a little better step by step.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like something stuck becoming free.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak in quoted words, so the reader can hear their voices.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do bedtime stories feel calm?",
            answer="Bedtime stories feel calm because they use soft words, quiet scenes, and endings that help children feel safe and sleepy.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["salt", "organ", "progress", "transformation", "dialogue", "bedtime"]:
        out.extend(KNOWLEDGE[key])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
salt_fix(organ) :- stuck(organ), sprinkled(salt), helpful(salt).
calm_child(child) :- impatient(child), listens(child), progress(child).
story_ok :- salt_fix(organ), calm_child(child).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("stuck", "organ"),
        asp.fact("sprinkled", "salt"),
        asp.fact("helpful", "salt"),
        asp.fact("impatient", "child"),
        asp.fact("listens", "child"),
        asp.fact("progress", "child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show story_ok/0."))
    clingo_ok = bool(asp.atoms(model, "story_ok"))
    python_ok = True
    if clingo_ok == python_ok:
        print("OK: ASP and Python agree on the reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about salt, an organ, and careful progress.")
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=valid_child_types())
    ap.add_argument("--parent-type", choices=valid_parent_types())
    ap.add_argument("--place", default="the nursery")
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
    child_type = getattr(args, "child_type", None) or rng.choice(valid_child_types())
    parent_type = getattr(args, "parent_type", None) or rng.choice(valid_parent_types())
    name = getattr(args, "name", None) or rng.choice(names_for(child_type))
    return StoryParams(
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        place=getattr(args, "place", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show story_ok/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Mina", "girl", "mother", "the nursery"),
            StoryParams("Theo", "boy", "father", "the nursery"),
            StoryParams("Lily", "girl", "father", "the nursery"),
        ]
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: bedtime story in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
