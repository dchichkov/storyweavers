#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py
=================================================================

A standalone story world for a tiny "Superhero Story" domain: two children in
capes spot a small creature in trouble, one child dreams of a daring feat, a
wiser pause turns the moment, and a toy flute helps a grown-up carry out a safe
rescue. The ending includes a concrete surprise that proves the children learned
what real heroism looks like.

Run it
------
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py --scene town_square --trouble kitten_awning
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py --trouble kitten_awning --method helper_arms
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/feat_flute_surprise_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
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
SAFE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Scene:
    id: str
    label: str
    opening: str
    witness: str
    witness_type: str
    surprise: str
    affords: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    animal: str
    the_animal: str
    place_text: str
    level: int
    tune: str
    call: str
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
class Stunt:
    id: str
    label: str
    reach: int
    risk: int
    boast: str
    move_text: str
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
class Method:
    id: str
    label: str
    reach: int
    safe: int
    setup: str
    rescue_text: str
    qa_text: str
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.meters["attempted_stunt"] >= THRESHOLD and hero.attrs.get("stunt_risk", 0) >= 2:
        sig = ("wobble", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["wobble"] += 1
            sidekick.memes["fear"] += 1
            out.append("__wobble__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    flute = world.get("flute")
    animal = world.get("animal")
    if flute.meters["played"] >= THRESHOLD and animal.attrs.get("likes_music", False):
        sig = ("calm", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.memes["calm"] += 1
            animal.meters["within_reach"] += 1
            out.append("__calm__")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    animal = world.get("animal")
    needed = animal.attrs.get("needed_reach", 99)
    if (
        helper.meters["helping"] >= THRESHOLD
        and animal.memes["calm"] >= THRESHOLD
        and helper.attrs.get("reach", 0) >= needed
    ):
        sig = ("rescue", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.meters["rescued"] += 1
            out.append("__rescued__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    if animal.meters["rescued"] >= THRESHOLD:
        sig = ("relief", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["relief"] += 1
            world.get("hero").memes["wisdom"] += 1
            world.get("sidekick").memes["relief"] += 1
            world.get("helper").memes["pride"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="calm", tag="emotional", apply=_r_calm),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


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


def valid_combo(scene: Scene, trouble: Trouble, stunt: Stunt, method: Method) -> bool:
    return (
        trouble.id in scene.affords
        and stunt.reach >= trouble.level
        and method.reach >= trouble.level
        and method.safe >= SAFE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for trouble_id, trouble in TROUBLES.items():
            for stunt_id, stunt in STUNTS.items():
                for method_id, method in METHODS.items():
                    if valid_combo(scene, trouble, stunt, method):
                        out.append((scene_id, trouble_id, stunt_id, method_id))
    return out


def predict_stunt(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["attempted_stunt"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": hero.meters["wobble"] >= THRESHOLD,
        "fear": sim.get("sidekick").memes["fear"],
    }


def introduce(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    world.say(
        f"{hero.id} and {sidekick.id} hurried through {scene.label} in bright capes. "
        f"{scene.opening}"
    )
    world.say(
        f"{hero.id} kept a small silver flute tucked in {hero.pronoun('possessive')} belt "
        f"like a superhero signal."
    )


def trouble_appears(world: World, hero: Entity, sidekick: Entity, trouble: Trouble) -> None:
    animal = world.get("animal")
    world.say(
        f"Then they heard {trouble.call}. A {trouble.animal} was stuck {trouble.place_text}, "
        f"and even {hero.id} stopped short."
    )
    world.say(
        f'"A rescue mission!" {hero.id} said. "{sidekick.id}, this is our chance to do a real feat."'
    )
    animal.memes["fear"] += 1
    hero.memes["duty"] += 1
    sidekick.memes["care"] += 1


def boast(world: World, hero: Entity, stunt: Stunt) -> None:
    hero.memes["bravery"] += 1
    world.say(f'"I can {stunt.boast}," {hero.id} said. "{stunt.label.capitalize()} is what heroes do."')


def warn(world: World, hero: Entity, sidekick: Entity, trouble: Trouble) -> None:
    pred = predict_stunt(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    sidekick.memes["caution"] += 1
    if pred["wobble"]:
        world.say(
            f'{sidekick.id} caught {hero.id} by the sleeve. "Wait. If you try that, '
            f"you might wobble and fall before you even reach {trouble.the_animal}. "
            f"Real heroes stop and think first."
        )
    else:
        world.say(
            f'{sidekick.id} shook {sidekick.pronoun("possessive")} head. "Let\'s not guess. '
            f'Real heroes make a plan first."'
        )


def almost_try(world: World, hero: Entity, stunt: Stunt) -> None:
    hero.meters["attempted_stunt"] += 1
    propagate(world, narrate=False)
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{hero.id} set one foot to {stunt.move_text}, and the whole idea felt shaky at once. "
            f"{hero.pronoun().capitalize()} climbed back down before the risky part even began."
        )
    else:
        world.say(
            f"{hero.id} measured the jump with {hero.pronoun('possessive')} eyes, then lowered "
            f"{hero.pronoun('possessive')} hands. The plan still did not feel safe enough."
        )


def call_helper(world: World, helper: Entity, method: Method) -> None:
    world.say(
        f"{helper.label_word.capitalize()} came over fast and {method.setup}."
    )


def play_flute(world: World, hero: Entity, trouble: Trouble) -> None:
    flute = world.get("flute")
    flute.meters["played"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} lifted the flute and played a {trouble.tune} tune, soft and steady. '
        f'The little notes floated through the air like tiny superhero lanterns.'
    )
    if world.get("animal").memes["calm"] >= THRESHOLD:
        world.say(
            f"The sound made {trouble.the_animal} go still and listen instead of panicking."
        )


def safe_rescue(world: World, helper: Entity, method: Method, trouble: Trouble) -> None:
    helper.meters["helping"] += 1
    propagate(world, narrate=False)
    if world.get("animal").meters["rescued"] < THRESHOLD:
        raise StoryError("The rescue setup failed: helper and flute were not enough.")
    world.say(
        f"While the flute sang, {helper.label_word} {method.rescue_text}. "
        f"In one careful moment, {trouble.the_animal} was safe."
    )


def lesson(world: World, hero: Entity, sidekick: Entity, helper: Entity) -> None:
    world.say(
        f'"That was the bravest part," said {helper.label_word}. "Not the climbing. '
        f'The stopping, the planning, and the helping together."'
    )
    world.say(
        f"{hero.id} looked at {sidekick.id} and nodded. The best kind of feat, "
        f"{hero.pronoun()} decided, was the one that kept everyone safe."
    )


def surprise_ending(world: World, scene: Scene, hero: Entity, sidekick: Entity, trouble: Trouble) -> None:
    witness = world.get("witness")
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"Just then came the surprise. {witness.label} stepped forward and handed "
        f"{hero.id} and {sidekick.id} {scene.surprise}."
    )
    world.say(
        f'"For heroes who use their heads and hearts," {witness.pronoun()} said.'
    )
    world.say(
        f"{hero.id} tucked the flute back into {hero.pronoun('possessive')} belt, "
        f"and the two young superheroes marched on through {scene.label}, not looking taller, "
        f"but feeling wiser."
    )
    world.facts["surprise_seen"] = True
@dataclass
class StoryParams:
    scene: str
    trouble: str
    stunt: str
    method: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    helper: str
    trait: str
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


KNOWLEDGE = {
    "kitten": [
        (
            "Why do kittens get stuck in high places sometimes?",
            "Kittens are curious and climb quickly, but climbing down can feel much harder and scarier. That is why they sometimes freeze and cry for help.",
        )
    ],
    "puppy": [
        (
            "Why can a puppy get tangled easily?",
            "Puppies bounce and pull in every direction because everything feels exciting. That can make a leash or ribbon catch on things before the puppy understands what happened.",
        )
    ],
    "duckling": [
        (
            "Why should people help a duckling gently?",
            "Ducklings are small and can frighten easily, so sudden grabbing can scare them more. Calm hands and a quiet voice help them feel safer.",
        )
    ],
    "parrot": [
        (
            "Why can a parrot be noisy when it is scared?",
            "A parrot uses loud calls to show alarm and ask for attention. Noise is one way birds tell the world that something feels wrong.",
        )
    ],
    "ladder": [
        (
            "Why is a ladder better than climbing on wobbly things?",
            "A ladder is made for reaching up with steady steps and support. Wobbly piles can tip, so they are not a safe way to rescue someone.",
        )
    ],
    "rescue": [
        (
            "What does a real rescue hero do first?",
            "A real rescue hero stops to notice the danger and makes a safe plan. Being brave is important, but being careful keeps everyone from getting hurt.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a musical instrument you blow across to make clear notes. Soft music can help make a moment feel calmer.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you were not expecting. A happy surprise can make the ending of a day feel extra bright.",
        )
    ],
}
KNOWLEDGE_ORDER = ["flute", "rescue", "kitten", "puppy", "duckling", "parrot", "ladder", "surprise"]


CURATED = [
    StoryParams(
        scene="town_square",
        trouble="kitten_awning",
        stunt="crate_stack",
        method="ladder",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Ben",
        sidekick_gender="boy",
        helper="mother",
        trait="steady",
    ),
    StoryParams(
        scene="playground",
        trouble="puppy_tube",
        stunt="bench_leap",
        method="helper_arms",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Ava",
        sidekick_gender="girl",
        helper="father",
        trait="gentle",
    ),
    StoryParams(
        scene="garden",
        trouble="duckling_ledge",
        stunt="fence_climb",
        method="step_stool",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        helper="mother",
        trait="calm",
    ),
    StoryParams(
        scene="town_square",
        trouble="parrot_statue",
        stunt="crate_stack",
        method="ladder",
        hero_name="Finn",
        hero_gender="boy",
        sidekick_name="Nora",
        sidekick_gender="girl",
        helper="father",
        trait="bright",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    trouble = f["trouble"]
    scene = f["scene"]
    return [
        'Write a short Superhero Story for a 3-to-5-year-old that includes the words "feat" and "flute" and ends with a surprise.',
        f"Tell a child-friendly superhero rescue story in {scene.label} where {hero.label} wants a daring feat, but a safer plan with a flute helps save {trouble.the_animal}.",
        f"Write a gentle story where {hero.label} and {sidekick.label} learn that the smartest hero is the one who pauses, plans, and helps together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    helper = f["helper"]
    witness = f["witness"]
    trouble = f["trouble"]
    stunt = f["stunt"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {sidekick.label}, two children pretending to be superheroes, and {helper.label_word} who helps with the rescue.",
        ),
        (
            "What problem did they find?",
            f"They found {trouble.the_animal} stuck {trouble.place_text}. The little animal sounded scared, so the game suddenly turned into a real rescue.",
        ),
        (
            f"What feat did {hero.label} want to try?",
            f"{hero.label} wanted to try {stunt.label} to reach {trouble.the_animal}. It sounded brave at first, but it was too shaky to be safe.",
        ),
    ]
    if f.get("predicted_wobble"):
        qa.append(
            (
                f"Why did {sidekick.label} tell {hero.label} to stop?",
                f"{sidekick.label} could see the stunt might wobble and make {hero.label} fall. {sidekick.pronoun().capitalize()} wanted the rescue to help the animal, not create a second problem.",
            )
        )
    qa.append(
        (
            "How did the flute help?",
            f"{hero.label} played the flute in a {trouble.tune} way, and the music helped {trouble.the_animal} calm down. Once the animal stopped panicking, {helper.label_word} could help much more safely.",
        )
    )
    qa.append(
        (
            f"How did {helper.label_word} rescue {trouble.the_animal}?",
            f"{helper.label_word.capitalize()} {method.qa_text}. The rescue worked because the grown-up used the right tool and the children helped in a calm way.",
        )
    )
    if f.get("surprise_seen"):
        qa.append(
            (
                "What was the surprise at the end?",
                f"{witness.label.capitalize()} gave the children {world.scene.surprise}. That surprise showed other people had noticed their safe and kind rescue.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flute", "rescue", "surprise"}
    tags |= set(world.facts["trouble"].tags)
    tags |= set(world.facts["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_invalid(scene: Scene, trouble: Trouble, stunt: Stunt, method: Method) -> str:
    if trouble.id not in scene.affords:
        return (
            f"(No story: {scene.label} does not fit that problem. "
            f"{trouble.the_animal.capitalize()} being stuck there belongs in a different setting.)"
        )
    if stunt.reach < trouble.level:
        return (
            f"(No story: {stunt.label} would not even reach {trouble.the_animal}. "
            f"The tempting feat has to be plausible before the story can reject it as unsafe.)"
        )
    if method.safe < SAFE_MIN:
        return (
            f"(No story: the method '{method.id}' is known to the world but refused because it is not safe enough. "
            f"Pick a steadier rescue method.)"
        )
    if method.reach < trouble.level:
        return (
            f"(No story: {method.label} cannot reach {trouble.the_animal}. "
            f"The safe rescue has to be able to solve the actual problem.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid(Scene, Trouble, Stunt, Method) :-
    scene(Scene), trouble(Trouble), stunt(Stunt), method(Method),
    affords(Scene, Trouble),
    stunt_reach(Stunt, SR), trouble_level(Trouble, TL), SR >= TL,
    method_reach(Method, MR), MR >= TL,
    method_safe(Method, MS), safe_min(SM), MS >= SM.

sensible(Method) :-
    method(Method), method_safe(Method, MS), safe_min(SM), MS >= SM.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for tid in sorted(scene.affords):
            lines.append(asp.fact("affords", sid, tid))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_level", tid, trouble.level))
    for stid, stunt in STUNTS.items():
        lines.append(asp.fact("stunt", stid))
        lines.append(asp.fact("stunt_reach", stid, stunt.reach))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_reach", mid, method.reach))
        lines.append(asp.fact("method_safe", mid, method.safe))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_methods = sorted(mid for mid, m in METHODS.items() if m.safe >= SAFE_MIN)
    cl_methods = asp_sensible_methods()
    if py_methods == cl_methods:
        print(f"OK: sensible methods match ({', '.join(cl_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={cl_methods} python={py_methods}")

    smoke_cases = [CURATED[0]]
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print(f"FAILED to resolve default params during smoke test: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=True, header=f"### smoke {i}")
            print(f"OK: smoke test {i} generated and emitted a story.")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero rescue storyworld with a flute, a daring feat, and a surprise ending."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--stunt", choices=STUNTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.trouble and args.stunt and args.method:
        if not valid_combo(SCENES[args.scene], TROUBLES[args.trouble], STUNTS[args.stunt], METHODS[args.method]):
            raise StoryError(explain_invalid(SCENES[args.scene], TROUBLES[args.trouble], STUNTS[args.stunt], METHODS[args.method]))
    elif args.method and METHODS[args.method].safe < SAFE_MIN:
        scene = SCENES[args.scene] if args.scene else next(iter(SCENES.values()))
        trouble = TROUBLES[args.trouble] if args.trouble else next(iter(TROUBLES.values()))
        stunt = STUNTS[args.stunt] if args.stunt else next(iter(STUNTS.values()))
        raise StoryError(explain_invalid(scene, trouble, stunt, METHODS[args.method]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.stunt is None or combo[2] == args.stunt)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, trouble_id, stunt_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sidekick_name = args.sidekick_name or _pick_name(rng, sidekick_gender, avoid=hero_name)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        trouble=trouble_id,
        stunt=stunt_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        scene = SCENES[params.scene]
        trouble = TROUBLES[params.trouble]
        stunt = STUNTS[params.stunt]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid option: unknown key {err.args[0]!r}.)") from None

    if not valid_combo(scene, trouble, stunt, method):
        raise StoryError(explain_invalid(scene, trouble, stunt, method))

    world = tell(
        scene=scene,
        trouble=trouble,
        stunt=stunt,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (scene, trouble, stunt, method) combos:\n")
        for scene, trouble, stunt, method in combos:
            print(f"  {scene:12} {trouble:14} {stunt:11} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.sidekick_name}: {p.trouble} at {p.scene} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    scene: Scene,
    trouble: Trouble,
    stunt: Stunt,
    method: Method,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    sidekick_name: str = "Ben",
    sidekick_gender: str = "boy",
    helper_type: str = "mother",
    trait: str = "steady",
) -> World:
    world = World(scene)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=["brave", trait],
            attrs={"stunt_risk": stunt.risk},
        )
    )
    sidekick = world.add(
        Entity(
            id="sidekick",
            kind="character",
            type=sidekick_gender,
            label=sidekick_name,
            role="sidekick",
            traits=[trait, "careful"],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the grown-up",
            role="helper",
            attrs={"reach": method.reach},
        )
    )
    witness = world.add(
        Entity(
            id="witness",
            kind="character",
            type=scene.witness_type,
            label=scene.witness,
            role="witness",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="flute",
            kind="thing",
            type="flute",
            label="flute",
            role="tool",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="animal",
            kind="thing",
            type="animal",
            label=trouble.animal,
            role="animal",
            attrs={"needed_reach": trouble.level, "likes_music": True},
        )
    )

    world.facts.update(
        scene=scene,
        trouble=trouble,
        stunt=stunt,
        method=method,
        hero=hero,
        sidekick=sidekick,
        helper=helper,
        witness=witness,
        flute_word="flute",
        predicted_wobble=False,
        surprise_seen=False,
    )

    introduce(world, hero, sidekick, scene)
    trouble_appears(world, hero, sidekick, trouble)

    world.para()
    boast(world, hero, stunt)
    warn(world, hero, sidekick, trouble)
    almost_try(world, hero, stunt)

    world.para()
    call_helper(world, helper, method)
    play_flute(world, hero, trouble)
    safe_rescue(world, helper, method, trouble)
    lesson(world, hero, sidekick, helper)

    world.para()
    surprise_ending(world, scene, hero, sidekick, trouble)
    world.facts["rescued"] = world.get("animal").meters["rescued"] >= THRESHOLD
    return world


SCENES = {
    "town_square": Scene(
        id="town_square",
        label="the town square",
        opening="Red paper banners fluttered over the bakery awning, and every puddle of sun looked ready for adventure.",
        witness="the mayor",
        witness_type="woman",
        surprise="a paper badge shaped like a gold star",
        affords={"kitten_awning", "parrot_statue"},
        tags={"square", "surprise"},
    ),
    "playground": Scene(
        id="playground",
        label="the playground",
        opening="The slide flashed silver, the sandbox steamed in the sun, and the monkey bars looked like a city of steel.",
        witness="the crossing guard",
        witness_type="man",
        surprise="a bright cape pin with a lightning bolt on it",
        affords={"puppy_tube", "duckling_slide"},
        tags={"playground", "surprise"},
    ),
    "garden": Scene(
        id="garden",
        label="the community garden",
        opening="Tall sunflowers made green walls, and the paths smelled like mint and warm dirt.",
        witness="the gardener",
        witness_type="woman",
        surprise="a sunflower ribbon tied in a neat little bow",
        affords={"duckling_ledge", "kitten_wall"},
        tags={"garden", "surprise"},
    ),
}

TROUBLES = {
    "kitten_awning": Trouble(
        id="kitten_awning",
        animal="kitten",
        the_animal="the kitten",
        place_text="on the striped bakery awning above the bread window",
        level=2,
        tune="soft",
        call="a thin mew-mew from overhead",
        tags={"kitten", "height"},
    ),
    "parrot_statue": Trouble(
        id="parrot_statue",
        animal="parrot",
        the_animal="the parrot",
        place_text="on the elbow of the town statue, too nervous to fly down",
        level=2,
        tune="bright",
        call="a sharp squawk near the statue",
        tags={"parrot", "height"},
    ),
    "puppy_tube": Trouble(
        id="puppy_tube",
        animal="puppy",
        the_animal="the puppy",
        place_text="inside the round play tunnel with its leash caught",
        level=1,
        tune="cheerful",
        call="worried yips from the tunnel",
        tags={"puppy", "playground"},
    ),
    "duckling_slide": Trouble(
        id="duckling_slide",
        animal="duckling",
        the_animal="the duckling",
        place_text="on the warm ladder beside the slide, too frightened to step down",
        level=1,
        tune="soft",
        call="tiny peeps from the slide",
        tags={"duckling", "playground"},
    ),
    "duckling_ledge": Trouble(
        id="duckling_ledge",
        animal="duckling",
        the_animal="the duckling",
        place_text="on the stone pond ledge beside the water barrel",
        level=1,
        tune="soft",
        call="small peeping near the pond",
        tags={"duckling", "garden"},
    ),
    "kitten_wall": Trouble(
        id="kitten_wall",
        animal="kitten",
        the_animal="the kitten",
        place_text="on the warm brick wall between the tomato beds",
        level=1,
        tune="soft",
        call="a worried mew by the tomatoes",
        tags={"kitten", "garden"},
    ),
}

STUNTS = {
    "crate_stack": Stunt(
        id="crate_stack",
        label="standing on a stack of delivery crates",
        reach=2,
        risk=3,
        boast="hop onto the crates and reach up in one swoop",
        move_text="the crate stack",
        tags={"climb", "feat"},
    ),
    "fence_climb": Stunt(
        id="fence_climb",
        label="scrambling up the fence",
        reach=1,
        risk=2,
        boast="scramble up the fence and scoop it up",
        move_text="the fence rails",
        tags={"climb", "feat"},
    ),
    "bench_leap": Stunt(
        id="bench_leap",
        label="leaping from the bench with superhero balance",
        reach=1,
        risk=2,
        boast="spring from the bench and grab it",
        move_text="the bench edge",
        tags={"jump", "feat"},
    ),
}

METHODS = {
    "ladder": Method(
        id="ladder",
        label="ladder",
        reach=2,
        safe=3,
        setup="opened a folding ladder and held it steady",
        rescue_text="climbed only as high as needed and gently lifted the little animal down",
        qa_text="used a ladder and careful hands to bring the animal down",
        tags={"ladder", "rescue"},
    ),
    "helper_arms": Method(
        id="helper_arms",
        label="careful arms",
        reach=1,
        safe=2,
        setup="knelt close and reached with calm, steady arms",
        rescue_text="reached in slowly and untangled the little animal without any jerking",
        qa_text="reached in carefully and untangled the animal",
        tags={"gentle_help", "rescue"},
    ),
    "step_stool": Method(
        id="step_stool",
        label="step stool",
        reach=1,
        safe=2,
        setup="set a wide step stool on the flat ground and tested it first",
        rescue_text="stepped up once and gathered the trembling little animal into safe hands",
        qa_text="used a steady step stool to reach the animal safely",
        tags={"stool", "rescue"},
    ),
    "broom_hook": Method(
        id="broom_hook",
        label="broom hook",
        reach=2,
        safe=1,
        setup="dragged over a broom and tried to hook the problem from far away",
        rescue_text="poked from below and hoped for the best",
        qa_text="tried to poke at the animal from below",
        tags={"weak_method"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Jack", "Eli", "Theo"]
TRAITS = ["steady", "bright", "quick", "gentle", "thoughtful", "calm"]

if __name__ == "__main__":
    main()
