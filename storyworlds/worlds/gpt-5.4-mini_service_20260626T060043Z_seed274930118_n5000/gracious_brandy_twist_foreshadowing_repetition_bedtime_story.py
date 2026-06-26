#!/usr/bin/env python3
"""
storyworlds/worlds/gracious_brandy_twist_foreshadowing_repetition_bedtime_story.py
===================================================================================

A small bedtime-story world with gentle repetition, soft foreshadowing, and a
kind twist.

Seed tale:
---
At bedtime, a little child worried about a creaky shadow near the window. The
parent kept the room calm with a repeated lullaby and a gracious reminder to
look closely. The shadow turned out to be Brandy, the family dog, carrying the
child's blanket. The child laughed, thanked the dog, and fell asleep feeling
safe.

World model:
---
- bedtime ritual -> sleepiness rises, worry falls
- repeated lullaby -> comfort rises for everyone in the room
- foreshadowing clue (jingle / thump / tail tap) -> can explain the twist
- twist reveal -> the "scary" shadow is a friendly helper
- closing image -> child sleeps, blanket returned, room peaceful

The story is intentionally small and constraint-checked: only a few plausible
variations, each with a clear beginning, middle turn, and ending.
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
    kind: str = "thing"  # character | thing | pet
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    child: object | None = None
    parent: object | None = None
    pet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman", "parent"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    place: str
    indoors: bool
    quiet: bool = True
    gentle_light: bool = True
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
    place: str
    child_name: str
    child_gender: str
    parent_type: str
    pet_kind: str
    blanket: str
    clue: str
    twist: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

    def pets(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "pet"]

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _raise_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = _meter(e, key) + amt


def _raise_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _set_meme(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True),
    "hallway": Setting(place="the hallway", indoors=True),
    "nursery": Setting(place="the nursery", indoors=True),
}

CLUES = {
    "jingle": "a tiny jingle from a collar",
    "thump": "a soft thump from the floor",
    "tap": "little tapping paws on the rug",
}

TWISTS = {
    "dog": "Brandy the family dog",
    "cat": "Brandy the family cat",
    "toy": "a stuffed toy named Brandy",
}


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


def _r_lullaby(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if _meter(parent, "singing") < THRESHOLD:
        return out
    sig = ("lullaby",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _raise_meme(child, "comfort", 1)
    _raise_meme(child, "sleepiness", 1)
    _raise_meme(parent, "comfort", 1)
    out.append("The lullaby made the room feel softer.")
    return out


def _r_bedtime(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if _meter(child, "tucked") < THRESHOLD:
        return out
    sig = ("tucked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _raise_meme(child, "sleepiness", 1)
    _raise_meme(child, "comfort", 1)
    out.append("The blanket tucked under the chin felt warm and safe.")
    return out


RULES = [Rule("lullaby", _r_lullaby), Rule("bedtime", _r_bedtime)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked quiet nights and soft pillows."
    )


def foreshadow(world: World, clue: str) -> None:
    world.say(
        f"Near bedtime, there was {clue}, and {clue.split(' from ')[-1]} seemed to come from the dark corner."
    )


def repeat_lullaby(world: World, parent: Entity) -> None:
    parent.meters["singing"] = 1
    world.say(
        f"{parent.pronoun().capitalize()} sang, \"Hush now, hush now, little one,\" and then sang it again: "
        f"\"Hush now, hush now, little one.\""
    )
    propagate(world)


def worry(world: World, child: Entity) -> None:
    _raise_meme(child, "worry", 1)
    world.say(
        f"{child.id} peeked at the shadow and felt a tiny shiver in {child.pronoun('possessive')} chest."
    )


def investigate(world: World, child: Entity, pet: Entity, blanket: Entity) -> None:
    _raise_meme(child, "curiosity", 1)
    world.say(
        f"{child.id} listened again and heard the same little sound, over and over, like a bedtime riddle."
    )
    world.say(
        f"Then the shadow wobbled, and {pet.id} stepped into the light with {blanket.it()} in {pet.pronoun('possessive')} mouth."
    )


def twist_reveal(world: World, child: Entity, parent: Entity, pet: Entity, blanket: Entity, twist: str) -> None:
    _set_meme(child, "worry", 0)
    _raise_meme(child, "joy", 1)
    _raise_meme(parent, "joy", 1)
    if twist == "dog":
        word = "dog"
    elif twist == "cat":
        word = "cat"
    else:
        word = "toy"
    world.say(
        f"The scary shape was not a monster at all. It was {pet.id}, a friendly {word}, helping carry back {blanket.label}."
    )
    world.say(
        f"{child.id} smiled and said, \"How gracious of you, Brandy.\""
    )


def ending(world: World, child: Entity, parent: Entity, blanket: Entity) -> None:
    child.meters["tucked"] = 1
    _raise_meme(child, "sleepiness", 1)
    world.say(
        f"After that, {child.id} snuggled under {blanket.it()} while {parent.id} turned the lamp low."
    )
    world.say(
        f"Brandy curled at the foot of the bed, the room grew still, and {child.id} drifted into sleep."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"tucked": 0.0},
        memes={"worry": 0.0, "sleepiness": 0.0, "comfort": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        meters={"singing": 0.0},
        memes={"comfort": 0.0, "joy": 0.0},
    ))
    pet = world.add(Entity(
        id="Brandy",
        kind="pet",
        type=params.pet_kind,
        label="Brandy",
        memes={"helpful": 1.0},
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label=params.blanket,
        owner=child.id,
        caretaker=parent.id,
    ))

    world.facts.update(
        child=child,
        parent=parent,
        pet=pet,
        blanket=blanket,
        clue=params.clue,
        twist=params.twist,
        setting=params.place,
    )

    introduce(world, child)
    world.say(
        f"At {setting.place}, everything was quiet and gentle, just right for bedtime."
    )
    world.para()
    foreshadow(world, _safe_lookup(CLUES, params.clue))
    worry(world, child)
    repeat_lullaby(world, parent)
    world.say(
        f"{child.id} listened to the same hush-hush song, and each repeat made the shadow seem a little less scary."
    )
    investigate(world, child, pet, blanket)
    twist_reveal(world, child, parent, pet, blanket, params.twist)
    world.para()
    ending(world, child, parent, blanket)
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in SETTINGS:
        for clue in CLUES:
            for twist in TWISTS:
                combos.append((place, clue, twist, "blanket"))
    return combos


def explain_rejection(msg: str) -> str:
    return f"(No story: {msg})"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny bedtime story world with foreshadowing, repetition, and a twist."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    parent_type = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    child_name = getattr(args, "child_name", None) or rng.choice(
        ["Mia", "Noah", "Luna", "Leo", "Ava", "Finn", "Nora", "Ezra"]
    )
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        parent_type=parent_type,
        pet_kind=twist if twist in {"dog", "cat"} else "dog",
        blanket="the blue blanket",
        clue=clue,
        twist=twist,
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child with the words "gracious" and "Brandy".',
        f"Tell a gentle story where {f['child'].id} hears a tiny clue at bedtime, worries for a moment, and then learns the shadow is friendly.",
        f"Write a short bedtime tale with repetition in the lullaby and a twist that explains the shadow near the window.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    pet: Entity = _safe_fact(world, f, "pet")
    blanket: Entity = _safe_fact(world, f, "blanket")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id}, a little {child.type} who was getting ready for bed.",
        ),
        QAItem(
            question=f"What was the repeated lullaby for?",
            answer=f"The repeated lullaby was there to calm {child.id} and make the room feel safe and sleepy.",
        ),
        QAItem(
            question=f"What turned out to be the shadow?",
            answer=f"The shadow turned out to be {pet.id}, a friendly {pet.type}, carrying {blanket.label} back.",
        ),
        QAItem(
            question=f"Why did {child.id} stop worrying?",
            answer=(
                f"{child.id} stopped worrying when the shadow was explained and the blanket came back, "
                f"so the scary feeling could fade away."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {child.id} tucked under {blanket.label}, {parent.id} turning the lamp low, "
                f"and Brandy curled at the foot of the bed."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lullaby?",
            answer="A lullaby is a soft song that grown-ups sing to help children feel calm and sleepy.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer=(
                "Foreshadowing gives a small clue early in a story so readers can guess what might matter later."
            ),
        ),
        QAItem(
            question="Why do stories repeat a line sometimes?",
            answer=(
                "Repetition can make a song or story feel cozy, easy to remember, and soothing, especially at bedtime."
            ),
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
    lines.append("== (3) World-knowledge questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
has_combo(P, C, T) :- place(P), clue(C), twist(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show has_combo/3."))
    return sorted(set(asp.atoms(model, "has_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python combos")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show has_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for clue in CLUES:
                for twist in TWISTS:
                    params = StoryParams(
                        place=place,
                        child_name="Mia",
                        child_gender="girl",
                        parent_type="mother",
                        pet_kind=twist if twist in {"dog", "cat"} else "dog",
                        blanket="the blue blanket",
                        clue=clue,
                        twist=twist,
                        seed=base_seed,
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
