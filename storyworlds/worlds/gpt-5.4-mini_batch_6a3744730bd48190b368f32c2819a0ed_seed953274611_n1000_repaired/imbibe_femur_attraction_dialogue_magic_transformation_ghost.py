#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/imbibe_femur_attraction_dialogue_magic_transformation_ghost.py
=============================================================================================

A small ghost-story storyworld about a moonlit house, a whispering portrait, a
forbidden sip, a long-buried femur, and a magical transformation that reveals
what the house was trying to say.

The world is built to support:
- the seed words: imbibe, femur, attraction
- the requested features: Dialogue, Magic, Transformation
- a child-facing ghost-story feel with a clear beginning, turn, and ending

The story model is state-driven:
- a ghostly attraction draws the child toward the attic
- dialogue can warn, tempt, or explain
- a magical sip from a bottle changes the child's state
- a hidden femur can be revealed, returned, or respectfully buried
- the ending proves what changed in the world

This script is standalone, stdlib-only, and follows the shared StorySample API.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    mood: str
    haunted: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Spirit:
    id: str
    label: str
    whisper: str
    attraction: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Bottle:
    id: str
    label: str
    phrase: str
    drink_word: str
    magic: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    comfort: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    rules = [r_apply_attraction, r_apply_transformation, r_apply_reveal]
    while changed:
        changed = False
        for rule in rules:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def r_apply_attraction(world: World) -> list[str]:
    out = []
    child = world.get("child")
    spirit = world.get("spirit")
    if child.memes["curiosity"] >= THRESHOLD and spirit.meters["draw"] >= THRESHOLD:
        sig = ("attraction",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["drawn"] += 1
        world.get("house").meters["sway"] += 1
        out.append(f"The house seemed to lean closer, as if it wanted to hear {child.id} breathe.")
    return out


def r_apply_transformation(world: World) -> list[str]:
    out = []
    child = world.get("child")
    bottle = world.get("bottle")
    if child.meters["sipped"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["changed"] += 1
    child.memes["brave"] += 1
    child.memes["fear"] = 0.0
    out.append(f"A warm shimmer passed over {child.id}, and {child.pronoun()} felt different in the bones.")
    return out


def r_apply_reveal(world: World) -> list[str]:
    out = []
    child = world.get("child")
    femur = world.get("femur")
    if child.meters["changed"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    femur.meters["revealed"] += 1
    out.append("The hidden femur showed itself at last, pale as a candle bone under the stairs.")
    return out


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    spirit: str
    bottle: str
    remedy: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "attic_house": Place(id="attic_house", label="the old house", mood="moonlit and quiet", haunted=True, tags={"ghost", "house"}),
    "nursery": Place(id="nursery", label="the nursery", mood="soft and sleepy", haunted=False, tags={"room"}),
}

SPIRITS = {
    "lantern": Spirit(id="lantern", label="the lantern ghost", whisper="Come upstairs. There is something waiting.", attraction=3, tags={"ghost", "attraction"}),
    "mirror": Spirit(id="mirror", label="the mirror ghost", whisper="Look once more. You will want to know.", attraction=2, tags={"ghost", "attraction"}),
}

BOTTLES = {
    "moonwater": Bottle(id="moonwater", label="moonwater", phrase="a silver bottle of moonwater", drink_word="imbibe", magic="glimmered", effect="made the child glow like starlight", tags={"imbibe", "magic"}),
    "violet_tonic": Bottle(id="violet_tonic", label="violet tonic", phrase="a violet tonic in a cracked glass bottle", drink_word="imbibe", magic="sparkled", effect="opened the eyes to hidden things", tags={"imbibe", "magic"}),
}

REMEDIES = {
    "speak_softly": Remedy(id="speak_softly", label="speak softly", action="spoke softly to the ghost", comfort="kept the fear from growing", power=2, tags={"dialogue"}),
    "bury_bone": Remedy(id="bury_bone", label="bury the bone", action="buried the femur in the garden", comfort="gave the house a proper goodbye", power=3, tags={"femur"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lila", "Elsie"]
BOY_NAMES = ["Theo", "Miles", "Otis", "Evan", "Jude"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for spirit in SPIRITS:
            for bottle in BOTTLES:
                for remedy in REMEDIES:
                    combos.append((place, spirit, bottle, remedy))
    return combos


def reasonableness_gate(place: Place, spirit: Spirit) -> bool:
    return place.haunted and spirit.attraction >= 2


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story storyworld with dialogue, magic, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    spirit = args.spirit or rng.choice(list(SPIRITS))
    bottle = args.bottle or rng.choice(list(BOTTLES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if not reasonableness_gate(PLACES[place], SPIRITS[spirit]):
        raise StoryError("No story: the chosen place is not haunted enough for a ghost story.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, child_name=name, child_gender=gender, spirit=spirit, bottle=bottle, remedy=remedy)


def tell(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(id="place", kind="place", type="place", label=PLACES[params.place].label, attrs={"mood": PLACES[params.place].mood}))
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    spirit = world.add(Entity(id="spirit", kind="spirit", type="spirit", label=SPIRITS[params.spirit].label, role="ghost"))
    bottle = world.add(Entity(id="bottle", kind="thing", type="thing", label=BOTTLES[params.bottle].label, role="magic"))
    femur = world.add(Entity(id="femur", kind="thing", type="thing", label="the femur", role="bone"))
    remedy = world.add(Entity(id="remedy", kind="thing", type="thing", label=REMEDIES[params.remedy].label, role="help"))

    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 1.0
    spirit.meters["draw"] = float(SPIRITS[params.spirit].attraction)

    world.say(f"On a moonlit night, {child.label} wandered into {PLACES[params.place].label}.")
    world.say(f'The air was still, but the spirit whispered, "{SPIRITS[params.spirit].whisper}"')
    world.say(f'The words gave the house an odd attraction, and {child.label} could not help listening.')

    world.para()
    world.say(f'{child.label} stared at {BOTTLES[params.bottle].phrase} and asked, "Should I {BOTTLES[params.bottle].drink_word} it?"')
    world.say(f'The ghost sighed. "{BOTTLES[params.bottle].magic}," it said, "and the dark will tell you its secret."')
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f'{child.label} lifted the bottle and chose to {BOTTLES[params.bottle].drink_word} the strange, sweet liquid.')
    child.meters["sipped"] += 1
    child.meters["magic"] += 1
    world.say(f"It tasted like winter rain, and {BOTTLES[params.bottle].effect}.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then the hidden femur appeared near the stair rail, and the room went very quiet.")
    world.say(f'{child.label} whispered, "What do I do with a bone in a haunted house?"')
    world.say(f'"If you want the house to rest," said the ghost, "you must be gentle."')
    world.say(f'{REMEDIES[params.remedy].action.capitalize()}.')
    world.get("femur").meters["buried"] += 1
    world.get("place").meters["peace"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    world.say(f"{REMEDIES[params.remedy].comfort.capitalize()}, and the whispering finally sounded thankful.")

    world.para()
    world.say(f"At dawn, {child.label} looked back at {PLACES[params.place].label}, and the windows no longer felt hungry.")
    world.say(f"The child had changed, the bone had been put away, and the house felt less like a trap and more like a story.")
    world.facts.update(
        place=place,
        child=child,
        spirit=spirit,
        bottle=bottle,
        femur=femur,
        remedy=remedy,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    spirit = SPIRITS[p.spirit]
    bottle = BOTTLES[p.bottle]
    return [
        f'Write a ghost story for a child that uses the words "imbibe", "femur", and "attraction".',
        f"Tell a spooky but gentle story where {p.child_name} hears a ghostly invitation, drinks a magical bottle, and transforms before finding a femur.",
        f'Write a dialogue-rich ghost story with magic and transformation, ending when the haunted place becomes peaceful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    qas = [
        QAItem(
            question="Why did the child go toward the attic?",
            answer=f"{p.child_name} was drawn by the ghost's strange attraction and wanted to learn what was hidden there. The whisper made the old house feel important, so curiosity pulled the child forward."
        ),
        QAItem(
            question="What did the child drink?",
            answer=f"{p.child_name} chose to imbibe {BOTTLES[p.bottle].phrase}. The drink was magical, and it changed how the child looked at the dark house."
        ),
        QAItem(
            question="What changed after the magic?",
            answer=f"The child transformed and became braver, while the hidden femur was revealed and then respectfully put away. That change made the house feel calm instead of hungry."
        ),
    ]
    qas.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended peacefully, with {p.child_name} leaving the haunted place quieter than before. The bone was no longer hidden, and the house seemed to rest."
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does imbibe mean?",
            answer="Imbibe means to drink something. In a magical story, it can mean taking in a special potion or tonic."
        ),
        QAItem(
            question="What is a femur?",
            answer="A femur is the long bone in the upper part of the leg. It is one of the biggest bones in the body."
        ),
        QAItem(
            question="What is attraction?",
            answer="Attraction means a pull or draw toward something. In a ghost story, it can be the feeling that makes someone want to follow a whisper or light."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic_house", child_name="Mina", child_gender="girl", spirit="lantern", bottle="moonwater", remedy="bury_bone", seed=None),
    StoryParams(place="attic_house", child_name="Theo", child_gender="boy", spirit="mirror", bottle="violet_tonic", remedy="speak_softly", seed=None),
]


def explain_rejection(place: Place, spirit: Spirit) -> str:
    return f"(No story: {place.label} is not haunted enough for this ghost story.)"


def valid_story_combo(params: StoryParams) -> bool:
    return reasonableness_gate(PLACES[params.place], SPIRITS[params.spirit])


ASP_RULES = r"""
haunted_place(P) :- place(P), haunted(P).
ghost_story(P,S,B,R) :- haunted_place(P), spirit(S), bottle(B), remedy(R).
attracted(C) :- curiosity(C), draw(S), draw(S) >= 2.
transformed(C) :- sipped(C), magic(B), bottle(B).
revealed_femur(F) :- transformed(C), femur(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.haunted:
            lines.append(asp.fact("haunted", pid))
    for sid in SPIRITS:
        lines.append(asp.fact("spirit", sid))
    for bid in BOTTLES:
        lines.append(asp.fact("bottle", bid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show ghost_story/4."))
    if not model:
        print("MISMATCH: ASP produced no ghost story model.")
        return 1
    print("OK: ASP program grounds and solves.")
    return 0


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.spirit not in SPIRITS or params.bottle not in BOTTLES or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
    if not valid_story_combo(params):
        raise StoryError(explain_rejection(PLACES[params.place], SPIRITS[params.spirit]))
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    spirit = args.spirit or rng.choice(list(SPIRITS))
    bottle = args.bottle or rng.choice(list(BOTTLES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if not reasonableness_gate(PLACES[place], SPIRITS[spirit]):
        raise StoryError(explain_rejection(PLACES[place], SPIRITS[spirit]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, child_name=name, child_gender=gender, spirit=spirit, bottle=bottle, remedy=remedy)


def asp_list() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("", "#show ghost_story/4.")), "ghost_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show ghost_story/4."))
        return
    if args.verify:
        rc = asp_verify()
        if rc == 0:
            try:
                sample = build_story(CURATED[0])
                _ = sample.story
            except Exception as e:
                print(f"SMOKE TEST FAILED: {e}")
                sys.exit(1)
            print("OK: story generation smoke test passed.")
        sys.exit(rc)
    if args.asp:
        print(f"{len(asp_list())} ASP ghost-story combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            sample = build_story(p)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
