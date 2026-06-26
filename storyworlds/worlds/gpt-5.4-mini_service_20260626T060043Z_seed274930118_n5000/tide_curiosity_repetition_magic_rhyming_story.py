#!/usr/bin/env python3
"""
storyworlds/worlds/tide_curiosity_repetition_magic_rhyming_story.py
====================================================================

A small storyworld about a curious child, a rising tide, and a little bit of
magic. The story is built as a simulated world: the tide changes the shore,
the child learns by watching, and repetition becomes part of the rhythm.

Seed tale sketch:
---
A child goes to the shore and wonders about the tide. The child keeps asking,
"What changes the water?" Each time the waves creep in, a tiny magic shell
glows. The child waits, watches, and repeats a simple rhyme until the tide
turns and leaves a bright gift behind.

This world models:
- physical meters: water level, wetness, glow, distance to the tide line
- emotional memes: curiosity, worry, delight, patience

The premise, tension, turn, and resolution are driven by state changes:
- curiosity pulls the child closer
- repeated watching reveals a pattern
- magic responds when the child repeats a rhyme
- the tide rises, then falls, leaving an ending image that proves change
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    parent: object | None = None
    shell: object | None = None
    tide: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
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
class Shore:
    place: str = "the shore"
    weather: str = "soft evening"
    tide_line: float = 5.0
    current_tide: float = 1.0
    magic_kind: str = "shell"
    rhyme_word: str = "glide"
    shore: object | None = None
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
    name: str
    gender: str
    parent: str
    shore: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    def __init__(self, shore: Shore) -> None:
        self.shore = shore
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.shore)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural, "owner": v.owner,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        return clone


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _x(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = _m(entity, key) + value


def _mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = _x(entity, key) + value


def _do_tide_rise(world: World) -> list[str]:
    out: list[str] = []
    shore = world.shore
    tide = world.get("tide")
    if _m(tide, "phase") >= 1.0:
        sig = ("rise",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        _add(tide, "height", 1.5)
        _add(tide, "glow", 1.0)
        out.append("The tide came closer, slow as a sigh, and the water gave the rocks a silver eye.")
    return out


def _do_tide_turn(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    child = world.get("child")
    if _m(tide, "height") >= 2.5 and ("turn",) not in world.fired:
        world.fired.add(("turn",))
        _set(tide, "phase", 0.0)
        _add(tide, "height", -1.0)
        _mem(child, "patience", 1.0)
        out.append("Then the tide paused and turned, just as tides do, and the child learned the waiting was part of the clue.")
    return out


def _do_magic_shell(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shell = world.get("shell")
    tide = world.get("tide")
    if _x(child, "curiosity") >= 1.0 and _x(child, "rhythm") >= 2.0 and _m(tide, "glow") >= 1.0:
        sig = ("magic",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        _add(shell, "glow", 2.0)
        _mem(child, "delight", 1.0)
        out.append("A tiny shell began to glow, and the glow went round and round like a song in the air.")
    return out


def _do_wet_feet(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tide = world.get("tide")
    if _m(tide, "height") >= 2.0 and _m(child, "distance") <= 1.0 and ("wet",) not in world.fired:
        world.fired.add(("wet",))
        _add(child, "wetness", 1.0)
        out.append("The water reached the child's toes, cool and bright, and made little lace on the sand.")
    return out


CAUSAL_RULES = [_do_tide_rise, _do_wet_feet, _do_magic_shell, _do_tide_turn]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


def _watch_and_repeat(world: World, child: Entity) -> None:
    _mem(child, "curiosity", 1.0)
    _mem(child, "rhythm", 1.0)
    world.say(
        f"{child.id} watched the waves and asked, \"Why do you come and go?\" "
        f"Then {child.pronoun()} said it again, soft and slow, to hear the answer in the flow."
    )


def _rhyme(world: World, child: Entity, shore_name: str) -> None:
    rhyme = "Come in, tide, then slip aside; shine and climb, then fall in time."
    _mem(child, "rhythm", 1.0)
    world.say(
        f"{child.id} whispered a little rhyme beside {shore_name}: "
        f"\"{rhyme}\""
    )


def _step_closer(world: World, child: Entity) -> None:
    if _m(child, "distance") > 0:
        _add(child, "distance", -1.0)
    world.say(f"{child.id} stepped closer, because wondering made {child.pronoun('object')} brave.")


def _wait(world: World, child: Entity) -> None:
    _mem(child, "patience", 1.0)
    world.say(f"Then {child.id} waited, and waiting felt like listening with {child.pronoun('possessive')} whole heart.")


def tell(params: StoryParams) -> World:
    shore = Shore(place=params.shore)
    world = World(shore)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        label=params.name,
        meters={"distance": 2.0, "wetness": 0.0},
        memes={"curiosity": 0.0, "delight": 0.0, "patience": 0.0, "rhythm": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"care": 1.0},
    ))
    tide = world.add(Entity(
        id="tide",
        type="tide",
        label="the tide",
        meters={"height": 1.0, "phase": 1.0, "glow": 0.0},
    ))
    shell = world.add(Entity(
        id="shell",
        type="shell",
        label="a tiny shell",
        phrase="a tiny shell",
        meters={"glow": 0.0},
        owner=params.name,
    ))

    world.say(
        f"At {shore.place}, under a {shore.weather} sky, {child.id} and {parent.label} listened to the hush of the sea."
    )
    world.say(
        f"{child.id} loved the tide, for it came and went like a secret song, and {child.pronoun()} wanted to know why."
    )

    world.para()
    _watch_and_repeat(world, child)
    _rhyme(world, child, shore.place)
    _step_closer(world, child)
    propagate(world)

    world.para()
    world.say(
        f"The waves kept coming back, the same and yet not the same, and {child.id} noticed the pattern at last."
    )
    _wait(world, child)
    propagate(world)

    world.para()
    world.say(
        f"At the bright middle of the story, the water shone at the edge of the sand, and the little shell answered the song."
    )
    propagate(world)
    if _m(shell, "glow") >= 1.0:
        world.say(
            f"{child.id} picked up {shell.label}, warm with magic, and smiled at the sparkling trace left by the tide."
        )

    world.para()
    world.say(
        f"When the sea slipped back again, {child.id} stood dry-toed on the shore, "
        f"holding {shell.label} like a tiny moon in a hand."
    )

    world.facts.update(
        child=child,
        parent=parent,
        tide=tide,
        shell=shell,
        shore=shore,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a short rhyming story for a child named {child.id} about the tide, with curiosity and a little magic.',
        f'Tell a gentle story where {child.id} asks why the tide keeps coming back and learns by repeating a rhyme.',
        f'Write a simple seaside story that uses the word "tide" and ends with a magical shell shining on the sand.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    shell = _safe_fact(world, f, "shell")
    tide = _safe_fact(world, f, "tide")
    return [
        QAItem(
            question=f"What did {child.id} keep wondering about at the shore?",
            answer=f"{child.id} kept wondering why the tide came and went, and {child.pronoun()} kept asking it with a curious heart.",
        ),
        QAItem(
            question=f"What did {child.id} repeat to listen for the answer?",
            answer=f"{child.id} repeated a small rhyme about the tide coming in and slipping aside, and the repeating helped the child notice the pattern.",
        ),
        QAItem(
            question=f"What magical thing happened when the rhyme and the tide matched?",
            answer=f"A tiny shell began to glow, and {child.id} picked it up after the tide shone near the sand.",
        ),
        QAItem(
            question=f"Who was nearby while {child.id} watched the water?",
            answer=f"The {parent.type} was nearby at the shore, listening and watching with {child.id}.",
        ),
        QAItem(
            question=f"What did the ending image prove had changed?",
            answer=f"By the end, the tide had turned back, {child.id} had learned to wait, and the shell glowed in the child's hand.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a tide?",
        answer="A tide is the regular rise and fall of sea water along the shore.",
    ),
    QAItem(
        question="Why does the sea seem to come and go?",
        answer="The sea seems to come and go because tides make the water move up and then back again.",
    ),
    QAItem(
        question="What does repetition do in a poem or rhyme?",
        answer="Repetition makes a rhyme easy to remember and gives it a steady, musical feeling.",
    ),
    QAItem(
        question="What is a shell?",
        answer="A shell is the hard outer home of some sea creatures, and many shells wash up on the beach.",
    ),
    QAItem(
        question="What does magic mean in a story?",
        answer="Magic in a story means something wondrous happens that does not work like ordinary life.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [("shore", "tide")]


ASP_RULES = r"""
shore(shore).
activity(tide).
valid(shore,tide).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("shore", "shore"), asp.fact("activity", "tide")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    print("  clingo:", sorted(set(asp_valid_combos())))
    print("  python:", sorted(set(valid_combos())))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small rhyming storyworld about tide, curiosity, repetition, and a little magic."
    )
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--shore", default="the shore")
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


NAMES_GIRL = ["Mia", "Luna", "Ivy", "Nora", "Ruby"]
NAMES_BOY = ["Finn", "Leo", "Owen", "Noah", "Theo"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    if getattr(args, "shore", None).strip() == "":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, gender=gender, parent=parent, shore=getattr(args, "shore", None), seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(name="Mia", gender="girl", parent="mother", shore="the shore"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
