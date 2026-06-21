#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/doll_dim_curiosity_foreshadowing_humor_fairy_tale.py
=====================================================================================

A tiny fairy-tale storyworld about a curious child, a doll-sized secret place, a
humorous warning, and a foreshadowed discovery.

The seed words are rebuilt as a world model:
- doll-dim: a hidden chamber or passage sized for a doll
- curiosity: the hero cannot resist peeking
- foreshadowing: an earlier hint predicts what the curious choice will reveal
- humor: the world gives a gentle, playful turn
- fairy tale: the prose is simple, old-storybook, and complete

The world is intentionally small, classical, and state-driven. It produces a
beginning, a middle turn, and an ending image that proves what changed.
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "queen", "father": "king"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    mood: str
    hidden_spot: str
    style: str = "fairy tale"
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


@dataclass
class SecretThing:
    id: str
    label: str
    size: str
    sound: str
    glow: str
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
class CuriosityHook:
    id: str
    hint: str
    clue: str
    promise: str
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
class HumorBeat:
    id: str
    line: str
    result: str
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
class Resolution:
    id: str
    action: str
    reveal: str
    ending: str
    sense: int
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
        clone.facts = dict(self.facts)
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


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("secret").meters["glow"] += 1
    child.memes["wonder"] += 1
    out.append("__hint__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pet").memes["silliness"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("pet").meters["jingles"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("bloom", _r_bloom), Rule("laugh", _r_laugh)]


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


def secret_visible(world: World) -> bool:
    return world.get("secret").meters["glow"] >= THRESHOLD


def curious_enough(world: World) -> bool:
    return world.get("child").memes["curiosity"] >= THRESHOLD


def response_ok(response: Resolution) -> bool:
    return response.sense >= SENSE_MIN


def could_reveal(response: Resolution, delay: int) -> bool:
    return response.power >= (1 + delay)


def play_opening(world: World, child: Entity, guide: Entity, setting: Setting, hook: CuriosityHook) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, there lived {child.id}, a child with bright eyes and a bouncy step."
    )
    world.say(
        f"Near {setting.hidden_spot}, {guide.id} said, \"Do not go wandering there; the old stones keep tiny secrets.\""
    )
    world.say(
        f"But {hook.hint}."
    )


def tease(world: World, child: Entity, hook: CuriosityHook, secret: SecretThing) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned closer and whispered, \"What is behind the little door?\" {hook.clue}"
    )
    world.say(f"The clue sounded almost like a joke, yet it promised {hook.promise}.")


def foreshadow(world: World, guide: Entity, secret: SecretThing, humor: HumorBeat) -> None:
    guide.memes["care"] += 1
    world.say(
        f"{guide.id} raised a finger. \"Mind the floor,\" {guide.pronoun()} said. \"It squeaks like a mouse in boots.\""
    )
    world.say(
        f"That was a funny warning, but it mattered: the loose plank near {secret.label} gave a tiny {secret.sound}."
    )
    world.facts["foreshadowed_sound"] = secret.sound
    world.facts["humor_line"] = humor.line


def peek(world: World, child: Entity, secret: SecretThing) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} tiptoed on, and at last the hidden place opened up: a {secret.size} chamber, doll-dim and neat as a sugar cube."
    )
    world.say(
        f"Inside, the air gave a little {secret.sound}, and the corners {secret.glow} like bedtime candles."
    )


def humor(world: World, pet: Entity, humor_beats: HumorBeat) -> None:
    pet.memes["silliness"] += 1
    propagate(world, narrate=False)
    world.say(humor_beats.line)
    world.say(humor_beats.result)


def resolve(world: World, guide: Entity, child: Entity, secret: SecretThing, response: Resolution, delay: int) -> None:
    if could_reveal(response, delay):
        child.memes["joy"] += 1
        child.memes["relief"] += 1
        world.get("secret").meters["opened"] = 1
        world.say(
            f"{guide.id} smiled and {response.action}, and out came {response.reveal}."
        )
        world.say(
            f"{response.ending}"
        )
    else:
        world.get("secret").meters["closed"] = 1
        world.say(
            f"{guide.id} tried to {response.action}, but the old latch would not budge in time."
        )
        world.say(
            "So the secret stayed shut for the night, and the children could only wonder."
        )


def ending_image(world: World, child: Entity, secret: SecretThing, guide: Entity) -> None:
    if world.get("secret").meters["opened"] >= THRESHOLD:
        world.say(
            f"In the end, {child.id} held the little thing in both hands, and the doll-dim chamber was no longer a mystery but a treasure."
        )
    else:
        world.say(
            f"In the end, {child.id} left the little door alone, while the dim room kept its secret and its quiet."
        )


def tell(setting: Setting, hook: CuriosityHook, secret: SecretThing, humor_beats: HumorBeat,
         response: Resolution, child_name: str = "Mina", child_type: str = "girl",
         guide_name: str = "Grandmother", guide_type: str = "woman",
         pet_name: str = "Pip", pet_type: str = "cat", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide"))
    pet = world.add(Entity(id=pet_name, kind="character", type=pet_type, role="pet"))
    world.add(Entity(id="secret", label=secret.label, type="thing"))
    world.add(Entity(id="setting", label=setting.place, type="room"))
    child.memes["curiosity"] = 1.0

    play_opening(world, child, guide, setting, hook)
    world.para()
    tease(world, child, hook, secret)
    foreshadow(world, guide, secret, humor_beats)
    world.para()
    peek(world, child, secret)
    humor(world, pet, humor_beats)
    world.para()
    resolve(world, guide, child, secret, response, delay)
    ending_image(world, child, secret, guide)

    world.facts.update(
        child=child,
        guide=guide,
        pet=pet,
        setting=setting,
        hook=hook,
        secret=secret,
        humor=humor_beats,
        response=response,
        delay=delay,
        outcome="opened" if world.get("secret").meters["opened"] >= THRESHOLD else "closed",
        foreshadowed=secret.sound,
    )
    return world


SETTINGS = {
    "tower": Setting(id="tower", place="a little tower at the edge of the wood", mood="moonlit", hidden_spot="the crooked stair"),
    "cottage": Setting(id="cottage", place="a warm cottage with blue shutters", mood="cozy", hidden_spot="the pantry wall"),
    "garden": Setting(id="garden", place="a rose garden behind the palace", mood="sunlit", hidden_spot="the hedgerow"),
}

SECRETS = {
    "box": SecretThing(id="box", label="a velvet box", size="doll-sized", sound="plink", glow="twinkled", tags={"doll-dim"}),
    "door": SecretThing(id="door", label="a little brass door", size="doll-dim", sound="tink", glow="sparkled", tags={"doll-dim"}),
    "cupboard": SecretThing(id="cupboard", label="a tiny cupboard", size="small as a dollhouse cup", sound="tick", glow="shone", tags={"doll-dim"}),
}

HOOKS = {
    "key": CuriosityHook(id="key", hint="a silver key kept peeking from beneath the mat", clue="The key seemed to wink every time the child looked away.", promise="a secret that fit in a palm", tags={"curiosity", "foreshadowing"}),
    "whisper": CuriosityHook(id="whisper", hint="a whisper kept slipping out from under the floorboard", clue="It sounded like the house was telling a story to itself.", promise="a surprise with a ribbon on top", tags={"curiosity", "foreshadowing"}),
    "crumb": CuriosityHook(id="crumb", hint="a trail of sugar crumbs led the way", clue="Even the crumbs marched in a straight line, as if they knew the ending first.", promise="a sweet secret", tags={"curiosity", "foreshadowing"}),
}

HUMOR = {
    "cat": HumorBeat(id="cat", line="Pip the cat sat down beside the stair and gave the most serious look in the whole kingdom.", result="Then Pip sneezed, and the dust puffed up like a tiny cloud with a moustache.", tags={"humor"}),
    "mouse": HumorBeat(id="mouse", line="A mouse poked its nose out and squeaked, \"I live here too, but I charge no rent.\" ", result="Everyone laughed, even the door, which answered with a soft click.", tags={"humor"}),
    "frog": HumorBeat(id="frog", line="A fat green frog blinked from the pail and looked as if it had come to supervise the castle.", result="It made the chamber feel less scary and much more odd.", tags={"humor"}),
}

RESPONSES = {
    "lift": Resolution(id="lift", action="lifted the latch", reveal="a pocket of moonlight and a thimble-sized crown", ending="The crown fit on the sill like a star that had taken a nap.", sense=3, power=2, tags={"resolution"}),
    "turn": Resolution(id="turn", action="turned the key", reveal="a tiny song-box that played one bright note", ending="The note rang out, and the doll-dim room felt suddenly grand.", sense=3, power=2, tags={"resolution"}),
    "push": Resolution(id="push", action="pushed the panel", reveal="a hidden shelf with a biscuit tin and a laughing ribbon", ending="The ribbon fluttered like a flag, proud to be found.", sense=2, power=1, tags={"resolution"}),
}

@dataclass
class StoryParams:
    setting: str
    hook: str
    secret: str
    humor: str
    response: str
    child_name: str = "Mina"
    child_type: str = "girl"
    guide_name: str = "Grandmother"
    guide_type: str = "woman"
    pet_name: str = "Pip"
    pet_type: str = "cat"
    delay: int = 0
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


CURATED = [
    StoryParams(
        setting="tower",
        hook="key",
        secret="door",
        humor="cat",
        response="turn",
        child_name="Mina",
        child_type="girl",
        guide_name="Grandmother",
        guide_type="woman",
        pet_name="Pip",
        pet_type="cat",
        delay=0,
    ),
    StoryParams(
        setting="cottage",
        hook="whisper",
        secret="box",
        humor="mouse",
        response="lift",
        child_name="Nico",
        child_type="boy",
        guide_name="Auntie",
        guide_type="woman",
        pet_name="Muffin",
        pet_type="cat",
        delay=0,
    ),
    StoryParams(
        setting="garden",
        hook="crumb",
        secret="cupboard",
        humor="frog",
        response="push",
        child_name="Lena",
        child_type="girl",
        guide_name="King Rowan",
        guide_type="man",
        pet_name="Bram",
        pet_type="cat",
        delay=1,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HOOKS:
            for sec in SECRETS:
                if "doll-dim" in SECRETS[sec].tags:
                    combos.append((sid, hid, sec))
    return combos


KNOWLEDGE = {
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to know what is hidden or new. It can help you learn, but you still need to be careful.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is a small hint that tells you something important may happen later. It helps a story feel like it has a plan.")],
    "humor": [("What makes a story funny?", "A story can be funny when something silly or surprising happens, like a cat acting important or a door making a tiny sound.")],
    "doll-dim": [("What does doll-dim mean?", "Doll-dim means very small, like a space made for a doll. A doll-dim thing is tiny enough to feel secret and magical.")],
    "secret": [("Why are little hidden spaces interesting?", "Hidden spaces feel exciting because they make you wonder what is inside. That wondering is part of the fun of a fairy tale.")],
}

KNOWLEDGE_ORDER = ["doll-dim", "curiosity", "foreshadowing", "humor", "secret"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child about {f["child"].id}, who is curious about a doll-dim secret.',
        f"Tell a gentle story with foreshadowing and humor where {f['child'].id} follows a clue to a tiny hidden place.",
        f'Write a short fairy tale that includes the word "doll-dim" and ends with a small secret revealed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    setting = f["setting"]
    secret = f["secret"]
    hook = f["hook"]
    response = f["response"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, who lives near {setting.place}. The child is curious and keeps noticing little hints."),
        ("What was the hidden place like?", f"It was {secret.size} and felt doll-dim, like a secret built for a tiny visitor. That small size made the discovery feel magical."),
        ("What clue warned that something was waiting?", f"{hook.clue} The clue came before the surprise, so the later reveal felt foretold rather than random."),
        ("How did the story become funny?", f"{f['humor'].line} Then {f['humor'].result} The joke softened the mystery and made the scene feel friendly."),
    ]
    if f["outcome"] == "opened":
        qa.append(("How was the secret opened?", f"{guide.id} {response.action}, and {response.reveal}. {response.ending}"))
        qa.append(("How did the story end?", f"It ended with {child.id} holding the found treasure and the doll-dim room no longer feeling empty. The ending image proves the secret was truly revealed."))
    else:
        qa.append(("How did the story end?", f"The secret stayed closed, and {child.id} had to wonder a little longer. Even so, the foreshadowing showed that the child was close to a discovery."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["hook"].tags) | set(world.facts["secret"].tags) | set(world.facts["humor"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(child) :- curiosity(C), C >= 1.
hinted :- hook(_).
opened :- response_ok(R), delay(D), power(R,P), P >= 1 + D.
secret_visible :- opened.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HOOKS.items():
        lines.append(asp.fact("hook", hid))
    for secid, s in SECRETS.items():
        lines.append(asp.fact("secret", secid))
        if "doll-dim" in s.tags:
            lines.append(asp.fact("doll_dim", secid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response_ok", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show hook/1.\n#show secret/1.\n"))
    return sorted(set((a[0], b[0], c[0]) for a, b, c in []))  # placeholder replaced below


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hook=None, secret=None, humor=None, response=None,
                                                            child_name=None, child_type=None, guide_name=None, guide_type=None,
                                                            pet_name=None, pet_type=None, delay=None, seed=None),
                                         random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"FAILED: normal generation smoke test crashed: {exc}")
        return 1
    try:
        # parity check for Python gate vs ASP gate
        import asp
        prog = asp_program("#show valid/3.")
        model = asp.one_model(prog)
        asp_set = set(asp.atoms(model, "valid"))
        py_set = set(valid_combos())
        if asp_set == py_set:
            print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in gate:")
            if asp_set - py_set:
                print(" only in ASP:", sorted(asp_set - py_set))
            if py_set - asp_set:
                print(" only in Python:", sorted(py_set - asp_set))
    except Exception as exc:
        print(f"FAILED: ASP verify crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a doll-dim secret, curiosity, foreshadowing, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hook", choices=HOOKS)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--humor", choices=HUMOR)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["woman", "man"])
    ap.add_argument("--pet-name")
    ap.add_argument("--pet-type", choices=["cat", "dog", "mouse", "frog"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hook = args.hook or rng.choice(sorted(HOOKS))
    secret = args.secret or rng.choice(sorted(SECRETS))
    humor = args.humor or rng.choice(sorted(HUMOR))
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(
        setting=setting,
        hook=hook,
        secret=secret,
        humor=humor,
        response=response,
        child_name=args.child_name or rng.choice(["Mina", "Nico", "Lena", "Oren"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        guide_name=args.guide_name or rng.choice(["Grandmother", "Auntie", "King Rowan", "Old Willow"]),
        guide_type=args.guide_type or rng.choice(["woman", "man"]),
        pet_name=args.pet_name or rng.choice(["Pip", "Muffin", "Brim", "Tansy"]),
        pet_type=args.pet_type or rng.choice(["cat", "mouse", "frog", "dog"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 1),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.hook not in HOOKS or params.secret not in SECRETS or params.humor not in HUMOR or params.response not in RESPONSES:
        raise StoryError("Unknown registry choice.")
    world = tell(
        SETTINGS[params.setting],
        HOOKS[params.hook],
        SECRETS[params.secret],
        HUMOR[params.humor],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        pet_name=params.pet_name,
        pet_type=params.pet_type,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
