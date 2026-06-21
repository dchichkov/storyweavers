#!/usr/bin/env python3
"""
storyworlds/worlds/place_wooded_pester_driveway_sound_effects_transformation.py
===============================================================================

A small standalone storyworld about an animal in a driveway, a pesky neighbor,
funny sound effects, and a transformation that changes the ending.

The domain is intentionally narrow:
- setting: driveway
- seed words: place, wooded, pester
- features: sound effects, transformation
- style: animal story

A child-facing story grows from world state, not from swapping nouns in a fixed
paragraph. The story tracks physical meters and emotional memes, and it emits
three QA sets grounded in the simulated world.

Run it:
    python storyworlds/worlds/place_wooded_pester_driveway_sound_effects_transformation.py
    python storyworlds/worlds/place_wooded_pester_driveway_sound_effects_transformation.py --qa --json
    python storyworlds/worlds/place_wooded_pester_driveway_sound_effects_transformation.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"cat", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    driveway: bool = True
    wooded: bool = False
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
class Animal:
    id: str
    type: str
    label: str
    voice: str
    tail: str
    sound: str
    transform_to: str
    kind: str = "character"
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"cat", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SoundEffect:
    id: str
    text: str
    kind: str = "sound"
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
class Transformation:
    id: str
    before: str
    after: str
    method: str
    result_label: str
    kind: str = "transformation"
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
class StoryParams:
    animal: str
    pester: str
    place: str
    sound: str
    transformation: str
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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_trance(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["startled"] < THRESHOLD:
            continue
        sig = ("trance", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wonder"] += 1
        out.append("__trance__")
    return out


def _r_change(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["changed"] < THRESHOLD:
            continue
        sig = ("change", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["changed"] += 1
        out.append("__change__")
    return out


CAUSAL_RULES = [Rule("trance", _r_trance), Rule("change", _r_change)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, animal_id: str, effect_id: str, transform_id: str) -> dict:
    sim = world.copy()
    _pester(sim, sim.get(animal_id), sim.get("pester"), narrate=False)
    _sound(sim, sim.get(effect_id), narrate=False)
    _transform(sim, sim.get(transform_id), narrate=False)
    pet = sim.get(animal_id)
    return {"startled": pet.meters["startled"] >= THRESHOLD, "changed": pet.meters["changed"] >= THRESHOLD}


def _pester(world: World, animal: Entity, pester: Entity, narrate: bool = True) -> None:
    animal.meters["startled"] += 1
    animal.memes["annoyed"] += 1
    if narrate:
        world.say(f"{pester.label} kept trying to pester {animal.id} into moving.")


def _sound(world: World, sound: Entity, narrate: bool = True) -> None:
    if narrate:
        world.say(sound.label)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.meters["startled"] += 1


def _transform(world: World, animal: Entity, trans: Entity, narrate: bool = True) -> None:
    animal.meters["changed"] += 1
    animal.memes["brave"] += 1
    if narrate:
        world.say(f"{animal.id} tried the strange change and became {trans.label}.")


def start(world: World, animal: Entity, place: Place) -> None:
    world.say(
        f"In the driveway, {animal.id} liked to sit in {place.id} and watch the day go by."
    )
    if place.wooded:
        world.say("Beyond the driveway, the wooded side yard whispered with leaves and twigs.")


def pester_beat(world: World, animal: Entity, pester: Entity) -> None:
    pester.memes["pushy"] += 1
    world.say(
        f"{pester.label} would not stop pestering {animal.id}. "
        f'"Come on, come on, come on," {pester.pronoun()} said.'
    )


def warn(world: World, animal: Entity, pester: Entity, sound: SoundEffect) -> None:
    world.say(
        f"{animal.id} flattened {animal.pronoun('possessive')} ears. "
        f'"That sound feels too big," {animal.pronoun()} said, as if {sound.text} might fill the whole driveway.'
    )


def do_sound(world: World, animal: Entity, sound: SoundEffect) -> None:
    animal.meters["startled"] += 1
    animal.memes["fear"] += 1
    world.say(f"Then {sound.text} echoed off the garage and the fence.")


def transform_beat(world: World, animal: Entity, trans: Transformation) -> None:
    animal.meters["changed"] += 1
    animal.memes["curious"] += 1
    world.say(
        f"{animal.id} took a breath, touched {animal.pronoun('possessive')} nose, and felt the transformation begin."
    )
    world.say(
        f"{animal.id} became {trans.result_label}, just as {trans.method} promised."
    )


def ending(world: World, animal: Entity, place: Place, trans: Transformation) -> None:
    world.say(
        f"After that, {animal.id} stayed in the driveway only for the quiet, ordinary part of the afternoon."
    )
    if place.wooded:
        world.say(
            f"The wooded trees still swayed nearby, but now {animal.id} looked calm and different, {trans.after}."
        )
    else:
        world.say(
            f"Even the garage door looked smaller now that {animal.id} had changed into {trans.after}."
        )


SOUNDS = {
    "bark": SoundEffect(id="bark", text="Bark! Bark-bark!", tags={"sound"}),
    "rattle": SoundEffect(id="rattle", text="Rattle-rattle-rattle!", tags={"sound"}),
    "squeak": SoundEffect(id="squeak", text="Squeeeak!", tags={"sound"}),
}

TRANSFORMATIONS = {
    "fox": Transformation(
        id="fox",
        before="a little dog",
        after="quick and clever",
        method="the moonlit magic of one good spin",
        result_label="a quick little fox",
        tags={"transformation"},
    ),
    "owl": Transformation(
        id="owl",
        before="a curious cat",
        after="quiet and wise",
        method="the hush of a deep breath",
        result_label="a wise little owl",
        tags={"transformation"},
    ),
    "deer": Transformation(
        id="deer",
        before="a shy rabbit",
        after="light-footed and brave",
        method="the tickle of the windy leaves",
        result_label="a small deer with steady steps",
        tags={"transformation"},
    ),
}

PLACES = {
    "driveway": Place(id="the driveway", driveway=True, wooded=False, tags={"driveway", "place"}),
    "wooded_driveway": Place(id="the driveway beside the wooded trees", driveway=True, wooded=True, tags={"driveway", "wooded", "place"}),
}

ANIMALS = {
    "dog": Animal(id="Milo", type="dog", label="Milo the dog", voice="bark", tail="wagged", sound="bark", transform_to="fox", traits=["friendly"]),
    "cat": Animal(id="Mina", type="cat", label="Mina the cat", voice="meow", tail="twitch", sound="squeak", transform_to="owl", traits=["curious"]),
    "rabbit": Animal(id="Pip", type="rabbit", label="Pip the rabbit", voice="sniff", tail="binky", sound="rattle", transform_to="deer", traits=["timid"]),
}


@dataclass
class StoryParams:
    animal: str
    pester: str
    place: str
    sound: str
    transformation: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id, animal in ANIMALS.items():
            for sound_id in SOUNDS:
                for trans_id in TRANSFORMATIONS:
                    if place.driveway and (place.wooded or animal_id != "rabbit"):
                        combos.append((animal_id, sound_id, trans_id))
    return sorted(set(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about a driveway, pestering, sound effects, and transformation.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--pester", choices=["squirrel", "raccoon", "neighbor"])
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    combos = valid_combos()
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    chosen_place = args.place or rng.choice(list(PLACES))
    if args.animal and args.animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    chosen_animal = args.animal or rng.choice(list(ANIMALS))
    chosen_pester = args.pester or rng.choice(["squirrel", "raccoon", "neighbor"])
    chosen_sound = args.sound or rng.choice(list(SOUNDS))
    chosen_trans = args.transformation or rng.choice(list(TRANSFORMATIONS))
    if chosen_place == "driveway" and chosen_animal == "rabbit" and not PLACES["wooded_driveway"].wooded:
        raise StoryError("The rabbit story needs the wooded driveway setting.")
    return StoryParams(
        animal=chosen_animal,
        pester=chosen_pester,
        place=chosen_place,
        sound=chosen_sound,
        transformation=chosen_trans,
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES["wooded_driveway"] if params.place == "wooded_driveway" else PLACES["driveway"]
    animal = world.add(Entity(id=ANIMALS[params.animal].id, kind="character", type=ANIMALS[params.animal].type, label=ANIMALS[params.animal].label, traits=list(ANIMALS[params.animal].traits)))
    pest = world.add(Entity(id=params.pester, kind="character", type="thing", label=f"the {params.pester}", role="pester"))
    sound = SOUNDS[params.sound]
    trans = TRANSFORMATIONS[params.transformation]
    world.add(Entity(id="sound", kind="thing", type="thing", label=sound.text))
    world.add(Entity(id="trans", kind="thing", type="thing", label=trans.result_label))
    world.facts.update(animal=animal, pester=pest, place=place, sound=sound, trans=trans)
    start(world, animal, place)
    world.para()
    pester_beat(world, animal, pest)
    warn(world, animal, pest, sound)
    world.para()
    do_sound(world, animal, sound)
    transform_beat(world, animal, trans)
    ending(world, animal, place, trans)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story set in the driveway that includes the words place and wooded.",
        f"Tell a story where {f['animal'].id} gets pestered, hears a funny sound effect, and changes into something surprising.",
        f"Write a child-friendly driveway story with sound effects and a transformation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal: Animal = f["animal"]
    place: Place = f["place"]
    sound: SoundEffect = f["sound"]
    trans: Transformation = f["trans"]
    return [
        ("Who is the story about?", f"It is about {animal.id}, an animal in the driveway. The story follows what happens when {f['pester'].label} keeps pestering {animal.id}."),
        ("What did the pester do?", f"{f['pester'].label} kept pestering {animal.id}. That made the little scene feel pushy and awkward until the sound and transformation changed it."),
        ("What sound did the story use?", f"It used {sound.text} as the sound effect. The sound echoed in the driveway and made {animal.id} feel startled."),
        ("What changed at the end?", f"{animal.id} changed into {trans.result_label}. The transformation made the ending calmer and braver than the beginning."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What is a driveway?", "A driveway is the path where cars go up to a house. People and animals can pause there, but it is usually a place for going, not staying forever."),
        ("What does pester mean?", "To pester someone is to bother them again and again. It can make a creature feel annoyed or pressured."),
        ("What is a sound effect?", "A sound effect is a made-up or repeated sound, like Bark! or Squeak!, used to make a story feel lively."),
        ("What is a transformation?", "A transformation is a big change from one form into another. In stories, it can make a character look and feel different by the end."),
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="dog", pester="squirrel", place="driveway", sound="bark", transformation="fox"),
    StoryParams(animal="cat", pester="neighbor", place="wooded_driveway", sound="squeak", transformation="owl"),
    StoryParams(animal="rabbit", pester="raccoon", place="wooded_driveway", sound="rattle", transformation="deer"),
]


ASP_RULES = r"""
valid(A,S,T) :- animal(A), sound(S), transformation(T).
wooded_ok(rabbit, wooded_driveway).
wooded_ok(dog, driveway).
wooded_ok(cat, driveway).
allowed(A, P) :- valid(A, S, T), wooded_ok(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3.\n"))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = sample.to_json()
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p != a:
        rc = 1
        print("MISMATCH in ASP parity.")
        print(" python only:", sorted(p - a))
        print(" asp only:", sorted(a - p))
    else:
        print(f"OK: ASP parity matches valid_combos() ({len(p)} combos).")
    print("OK: generate() smoke test succeeded.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id in ANIMALS:
            for sound_id in SOUNDS:
                for trans_id in TRANSFORMATIONS:
                    if place_id == "wooded_driveway" or animal_id != "rabbit":
                        combos.append((animal_id, sound_id, trans_id))
    return sorted(set(combos))


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
    if args.show_asp:
        print(asp_program("#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, sound, transformation) combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
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
