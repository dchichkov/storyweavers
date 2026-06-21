#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py
=============================================================================

A standalone story world for a tiny, child-facing nursery-rhyme domain about a
hurtful scary word, a remembered fright, and a repaired friendship.

Seed constraints
----------------
- must include the word "cannibal"
- must include Reconciliation and Flashback
- style close to a Nursery Rhyme

World premise
-------------
Two children bring a handmade parade puppet into a rhyme game. The puppet is a
friendly make-believe eater of garden treats, but during the game one child,
startled by a memory, blurts out the scary word "cannibal." The owner feels
hurt. A calm explanation, a flashback to the remembered mix-up, and a small act
of repair lead to reconciliation. The children end by singing a kinder rhyme
together.

The reasonableness gate refuses choices where the scary word would be aimed at a
human child. In this world, "cannibal" can only be spoken about a pretend
creature puppet, never about a person.

Run it
------
    python storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py --creature goat --memory goose --repair patch
    python storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py --target child
    python storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/cannibal_reconciliation_flashback_nursery_rhyme.py --qa --json
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
KINDNESS_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher"}.get(self.type, self.type)
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
class Creature:
    id: str
    label: str
    phrase: str
    rhyme_name: str
    snack: str
    sound: str
    color: str
    nibbles_props: bool = True
    human: bool = False
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
class Memory:
    id: str
    title: str
    place: str
    thief: str
    lost_item: str
    feeling: str
    flash: str
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
class Repair:
    id: str
    kindness: int
    verb: str
    line: str
    proof: str
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


def _r_hurt(world: World) -> list[str]:
    speaker = world.get("speaker")
    owner = world.get("owner")
    puppet = world.get("puppet")
    if speaker.memes["scary_word"] < THRESHOLD:
        return []
    sig = ("hurt", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["hurt"] += 1
    owner.memes["trust_loss"] += 1
    puppet.memes["misnamed"] += 1
    return ["__hurt__"]


def _r_memory_fear(world: World) -> list[str]:
    speaker = world.get("speaker")
    if speaker.memes["remembered"] < THRESHOLD:
        return []
    sig = ("memory_fear", speaker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    speaker.memes["fear"] += 1
    return ["__memory__"]


def _r_apology_softens(world: World) -> list[str]:
    speaker = world.get("speaker")
    owner = world.get("owner")
    if speaker.memes["apologized"] < THRESHOLD:
        return []
    sig = ("soften", owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["hurt"] = max(0.0, owner.memes["hurt"] - 1.0)
    owner.memes["warmth"] += 1
    speaker.memes["relief"] += 1
    return ["__soften__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="memory_fear", tag="emotion", apply=_r_memory_fear),
    Rule(name="apology_softens", tag="emotion", apply=_r_apology_softens),
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


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.kindness >= KINDNESS_MIN]


def valid_combo(creature: Creature, target: str, repair: Repair) -> bool:
    return creature.nibbles_props and not creature.human and target == "puppet" and repair.kindness >= KINDNESS_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for creature_id, creature in CREATURES.items():
        for target in TARGETS:
            for repair_id, repair in REPAIRS.items():
                if valid_combo(creature, target, repair):
                    combos.append((creature_id, target, repair_id))
    return combos


def explain_rejection(creature: Creature, target: str, repair: Repair) -> str:
    if target != "puppet":
        return "(No story: in this world, the scary word must be about a pretend puppet, never about a child. Choose --target puppet.)"
    if creature.human:
        return f"(No story: {creature.label} is treated as human here, and the world refuses to aim the word at a person.)"
    if not creature.nibbles_props:
        return f"(No story: {creature.label} does not nibble or chomp in play, so the misunderstanding would not arise.)"
    if repair.kindness < KINDNESS_MIN:
        return f"(No story: repair '{repair.id}' is too weak for a true reconciliation. Try one of: {', '.join(sorted(r.id for r in sensible_repairs()))}.)"
    return "(No story: this combination does not fit the world.)"


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    speaker = sim.get("speaker")
    speaker.memes["scary_word"] += 1
    propagate(sim, narrate=False)
    return {
        "hurt": sim.get("owner").memes["hurt"],
        "misnamed": sim.get("puppet").memes["misnamed"],
    }


def introduce(world: World, owner: Entity, speaker: Entity, teacher: Entity, creature: Creature) -> None:
    owner.memes["joy"] += 1
    speaker.memes["joy"] += 1
    world.say(
        f"In the sunny nursery room, {owner.id} and {speaker.id} sat by {teacher.label} with a basket of ribbons, bells, and cloth."
    )
    world.say(
        f"{owner.id} lifted {creature.phrase}, a {creature.color} parade puppet called {creature.rhyme_name}, and everyone tapped a small beat on the floor."
    )
    world.say(
        f'"Clip-clap, tip-tap, round the chair we scoot; {creature.rhyme_name} loves {creature.snack}, not little boots," sang {teacher.label}.'
    )


def play(world: World, owner: Entity, speaker: Entity, creature: Creature) -> None:
    puppet = world.get("puppet")
    puppet.meters["wobbling"] += 1
    puppet.meters["nibbling"] += 1
    world.say(
        f"{owner.id} made {creature.rhyme_name} bob and bow. {creature.sound.capitalize()}! went the puppet as it pretended to nibble a paper radish from the rhyme basket."
    )
    world.say(
        f"{speaker.id} laughed at first, but then the little cloth mouth came close to a berry bun on the tea tray, and {speaker.pronoun()} went still."
    )


def blurts(world: World, owner: Entity, speaker: Entity, creature: Creature) -> None:
    pred = predict_hurt(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_misnamed"] = pred["misnamed"]
    speaker.memes["scary_word"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh! Don\'t let {creature.rhyme_name} near my bun," cried {speaker.id}. "It looks like a cannibal puppet!"'
    )
    world.say(
        f"The room went quiet as a button box. {owner.id}'s smile folded small."
    )


def hurt_reaction(world: World, owner: Entity, creature: Creature) -> None:
    owner.memes["sadness"] += 1
    world.say(
        f'"{creature.rhyme_name} is not mean," {owner.id} whispered. "{owner.pronoun().capitalize()} only munches pretend garden treats because I stitched those felt leaves for {owner.pronoun("object")}."'
    )


def flashback(world: World, speaker: Entity, memory: Memory) -> None:
    speaker.memes["remembered"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"Then a memory fluttered up inside {speaker.id} like a page turning backward."
    )
    world.say(
        f"{memory.flash} At {memory.place}, a {memory.thief} had snatched {speaker.pronoun('possessive')} {memory.lost_item}, and {speaker.pronoun()} had felt {memory.feeling}."
    )
    world.say(
        f"Ever since then, a quick chomping mouth had made {speaker.pronoun('object')} jump before {speaker.pronoun()} could think."
    )


def explain(world: World, owner: Entity, speaker: Entity, teacher: Entity, creature: Creature, memory: Memory) -> None:
    speaker.memes["understanding"] += 1
    owner.memes["understanding"] += 1
    world.para()
    world.say(
        f'{teacher.label} knelt between them. "That was a frightened memory talking," {teacher.pronoun()} said softly. "But scary names can still sting."'
    )
    world.say(
        f'{speaker.id} looked at the puppet again. "I remembered the {memory.thief} from {memory.place}," {speaker.pronoun()} said. "I was startled. I should not have called {creature.rhyme_name} a cannibal."'
    )
    world.say(
        f'{owner.id} nodded slowly. "You can say you were scared," {owner.pronoun()} answered. "But please use a kinder word for my puppet."'
    )


def repair_step(world: World, owner: Entity, speaker: Entity, repair: Repair) -> None:
    puppet = world.get("puppet")
    speaker.memes["apologized"] += 1
    puppet.meters["mended"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{speaker.id} {repair.verb}. {repair.line}"
    )
    world.say(
        f"{repair.proof} The hurt place in the game began to mend."
    )
    owner.memes["trust"] += 1
    speaker.memes["trust"] += 1


def reconcile(world: World, owner: Entity, speaker: Entity, creature: Creature) -> None:
    owner.memes["friendship"] += 1
    speaker.memes["friendship"] += 1
    world.say(
        f'Soon {owner.id} smiled again. "{creature.rhyme_name} can be a crunchy gobbler instead," {owner.pronoun()} said.'
    )
    world.say(
        f'"A crunchy gobbler!" {speaker.id} laughed. Side by side, they marched the puppet past the tea tray and sang, '
        f'"Nibble the radish, nibble the pea, kind little chomper, dance with me."'
    )
    world.say(
        f"The berry bun stayed safe on the plate, and the last picture was bright and plain: two friends, one puppet, and one mended rhyme."
    )


def tell(
    creature: Creature,
    memory: Memory,
    repair: Repair,
    *,
    target: str = "puppet",
    owner_name: str = "Mira",
    owner_gender: str = "girl",
    speaker_name: str = "Toby",
    speaker_gender: str = "boy",
    teacher_name: str = "Miss Wren",
) -> World:
    world = World()
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner", label=owner_name))
    speaker = world.add(Entity(id=speaker_name, kind="character", type=speaker_gender, role="speaker", label=speaker_name))
    teacher = world.add(Entity(id=teacher_name, kind="character", type="teacher", role="teacher", label=teacher_name))
    puppet = world.add(Entity(id="puppet", kind="thing", type="puppet", role="puppet", label=creature.label, owner=owner.id))

    owner.memes["joy"] = 1.0
    owner.memes["hurt"] = 0.0
    owner.memes["trust"] = 1.0
    owner.memes["warmth"] = 0.0
    speaker.memes["joy"] = 1.0
    speaker.memes["fear"] = 0.0
    speaker.memes["scary_word"] = 0.0
    speaker.memes["remembered"] = 0.0
    speaker.memes["apologized"] = 0.0
    speaker.memes["relief"] = 0.0
    speaker.memes["trust"] = 1.0
    puppet.meters["wobbling"] = 0.0
    puppet.meters["nibbling"] = 0.0
    puppet.meters["mended"] = 0.0
    puppet.memes["misnamed"] = 0.0

    world.facts["target"] = target
    world.facts["creature"] = creature
    world.facts["memory"] = memory
    world.facts["repair"] = repair

    introduce(world, owner, speaker, teacher, creature)
    world.para()
    play(world, owner, speaker, creature)
    blurts(world, owner, speaker, creature)
    hurt_reaction(world, owner, creature)
    flashback(world, speaker, memory)
    explain(world, owner, speaker, teacher, creature, memory)
    repair_step(world, owner, speaker, repair)
    reconcile(world, owner, speaker, creature)

    world.facts.update(
        owner=owner,
        speaker=speaker,
        teacher=teacher,
        puppet=puppet,
        outcome="reconciled" if speaker.memes["apologized"] >= THRESHOLD and owner.memes["friendship"] >= THRESHOLD else "strained",
        scary_word_used=speaker.memes["scary_word"] >= THRESHOLD,
        flashback_happened=speaker.memes["remembered"] >= THRESHOLD,
        repaired=puppet.meters["mended"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "puppet": [
        (
            "What is a puppet?",
            "A puppet is a toy figure you can move with your hand or fingers so it seems to talk, dance, or nibble in a pretend game."
        )
    ],
    "memory": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly looks back at something that happened before. It helps you understand why a character feels the way they do now."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people who were upset make peace again. They listen, tell the truth, and do something kind to repair the hurt."
        )
    ],
    "apology": [
        (
            "Why can an apology help?",
            "An apology can help because it shows you know your words or actions hurt someone. A true apology is often followed by a kind action that proves you want to do better."
        )
    ],
    "goose": [
        (
            "Why do geese sometimes grab food?",
            "Geese are animals that peck and snatch food quickly when they think they can get a bite. That fast movement can surprise people."
        )
    ],
    "goat": [
        (
            "Why do goats nibble things?",
            "Goats like to explore with their mouths and may nibble leaves, paper, or cloth. In stories, that habit can be turned into a silly rhyme."
        )
    ],
    "crow": [
        (
            "Why do crows steal shiny or tasty things sometimes?",
            "Crows are clever birds, and they often investigate objects that look interesting. A quick grab from a crow can feel startling."
        )
    ],
    "duck": [
        (
            "Why can a duck make a picnic messy?",
            "A duck may waddle over and peck at crumbs or buns if food is left close by. It is not being rude on purpose; it is simply looking for a snack."
        )
    ],
    "patch": [
        (
            "What is a patch on cloth?",
            "A patch is a small piece of cloth sewn onto another piece to cover a hole or decorate it. It can make something look cared for and special."
        )
    ],
    "bell": [
        (
            "Why do little bells sound cheerful in rhymes?",
            "Little bells make a light ringing sound that fits marching and singing. Their bright sound can make a game feel festive."
        )
    ],
    "bow": [
        (
            "Why can a ribbon bow feel like a peace offering?",
            "A ribbon bow is small and gentle, and it shows someone took time to make something pretty. In a story, that careful effort can help show goodwill."
        )
    ],
}
KNOWLEDGE_ORDER = ["puppet", "memory", "reconciliation", "apology", "goose", "goat", "crow", "duck", "patch", "bell", "bow"]


CREATURES = {
    "goat": Creature(
        id="goat",
        label="goat puppet",
        phrase="a patchwork goat puppet",
        rhyme_name="Gilly Goat",
        snack="cabbage leaves",
        sound="clop-clop",
        color="silver-gray",
        nibbles_props=True,
        human=False,
        tags={"puppet", "goat"},
    ),
    "crocodile": Creature(
        id="crocodile",
        label="crocodile puppet",
        phrase="a long green crocodile puppet",
        rhyme_name="Crocus Croc",
        snack="peppery peas",
        sound="snap-swish",
        color="leafy green",
        nibbles_props=True,
        human=False,
        tags={"puppet"},
    ),
    "crow": Creature(
        id="crow",
        label="crow puppet",
        phrase="a glossy black crow puppet",
        rhyme_name="Cricket Crow",
        snack="crumbly buns",
        sound="caw-caw",
        color="inky black",
        nibbles_props=True,
        human=False,
        tags={"puppet", "crow"},
    ),
}

MEMORIES = {
    "goose": Memory(
        id="goose",
        title="goose by the pond",
        place="the pond path",
        thief="goose",
        lost_item="seed bun",
        feeling="small and shaky",
        flash="Last week came back in a blink.",
        tags={"memory", "goose"},
    ),
    "duck": Memory(
        id="duck",
        title="duck at the picnic rug",
        place="the park picnic rug",
        thief="duck",
        lost_item="jam tart",
        feeling="jumpy and cross",
        flash="Yesterday's picnic skittered through the mind.",
        tags={"memory", "duck"},
    ),
    "crow": Memory(
        id="crow",
        title="crow on the fence",
        place="the garden fence",
        thief="crow",
        lost_item="apple slice",
        feeling="startled and puzzled",
        flash="A sharp black flutter returned to mind.",
        tags={"memory", "crow"},
    ),
}

REPAIRS = {
    "patch": Repair(
        id="patch",
        kindness=3,
        verb="sewed a tiny heart patch onto the puppet's pocket with teacher's help",
        line='"I want my words to leave a kinder mark than that," said the apologizing child.',
        proof="The little stitched heart gave the puppet a new bright spot",
        qa_text="sewed a tiny heart patch onto the puppet",
        tags={"apology", "patch"},
    ),
    "bell": Repair(
        id="bell",
        kindness=3,
        verb="tied a bright bell on the puppet's ribbon collar",
        line='"Now everyone can hear the happy puppet coming," said the apologizing child.',
        proof="The bell chimed a gentle tring-tring instead of a harsh surprise",
        qa_text="tied a bright bell on the puppet's ribbon collar",
        tags={"apology", "bell"},
    ),
    "bow": Repair(
        id="bow",
        kindness=2,
        verb="made a soft ribbon bow for the puppet's ear",
        line='"I was wrong to use a scary name," said the apologizing child.',
        proof="The careful bow showed time, thought, and a wish to begin again",
        qa_text="made a soft ribbon bow for the puppet",
        tags={"apology", "bow"},
    ),
    "shrug": Repair(
        id="shrug",
        kindness=1,
        verb="gave a tiny shrug and looked at the floor",
        line='"Well, I did not mean it much," said the child, which was not enough.',
        proof="No new kindness appeared for the game to hold onto",
        qa_text="only shrugged and did not really repair the hurt",
        tags={"apology"},
    ),
}

TARGETS = {
    "puppet": "puppet",
    "child": "child",
}


@dataclass
class StoryParams:
    creature: str
    memory: str
    repair: str
    target: str
    owner_name: str
    owner_gender: str
    speaker_name: str
    speaker_gender: str
    teacher_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    speaker = f["speaker"]
    creature = f["creature"]
    memory = f["memory"]
    repair = f["repair"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "cannibal" but uses it only in a misunderstanding about a puppet, not about a person.',
        f"Tell a gentle story where {speaker.id} blurts out a scary word about {owner.id}'s {creature.label}, then a flashback to {memory.place} explains the mistake and the friends reconcile.",
        f"Write a musical little story with a hurt feeling, a remembered fright, and a true apology ending in {repair.qa_text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    speaker = f["speaker"]
    teacher = f["teacher"]
    creature = f["creature"]
    memory = f["memory"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} and {speaker.id} in the nursery room, with {teacher.label} helping them. They are playing with {owner.id}'s {creature.label} in a singing game."
        ),
        (
            f"Why did {speaker.id} say the word cannibal?",
            f"{speaker.id} said it because the puppet's quick nibbling made {speaker.pronoun('object')} remember {memory.title}. The flashback brought back a frightened feeling before {speaker.pronoun()} stopped to choose kinder words."
        ),
        (
            f"How did {owner.id} feel when the puppet was called that?",
            f"{owner.id} felt hurt and small right away. The puppet was something {owner.pronoun()} had lovingly brought into the game, so the scary name stung both the play and the friendship."
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, at {memory.place}, a {memory.thief} snatched {speaker.pronoun('possessive')} {memory.lost_item}. That old surprise is why a chomping mouth made {speaker.pronoun('object')} jump."
        ),
        (
            "How did they make peace again?",
            f"They made peace by telling the true reason for the mistake and then repairing the hurt. {speaker.id} {repair.qa_text}, which showed kindness in action and helped the friendship warm again."
        ),
        (
            "How did the story end?",
            f"It ended with the children singing a kinder rhyme together beside the safe berry bun. The ending image shows that the game, the puppet, and the friendship were all mended."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["creature"].tags) | set(f["memory"].tags) | set(f["repair"].tags) | {"reconciliation"}
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        creature="goat",
        memory="goose",
        repair="patch",
        target="puppet",
        owner_name="Mira",
        owner_gender="girl",
        speaker_name="Toby",
        speaker_gender="boy",
        teacher_name="Miss Wren",
    ),
    StoryParams(
        creature="crow",
        memory="duck",
        repair="bell",
        target="puppet",
        owner_name="Nell",
        owner_gender="girl",
        speaker_name="Finn",
        speaker_gender="boy",
        teacher_name="Miss Wren",
    ),
    StoryParams(
        creature="crocodile",
        memory="crow",
        repair="bow",
        target="puppet",
        owner_name="Pip",
        owner_gender="boy",
        speaker_name="Ada",
        speaker_gender="girl",
        teacher_name="Miss Wren",
    ),
]


ASP_RULES = r"""
target_ok(puppet).
kind_repair(R) :- repair(R), kindness(R, K), kindness_min(M), K >= M.
valid(C, T, R) :- creature(C), target(T), repair(R),
                  nibbles_props(C), not human(C), target_ok(T), kind_repair(R).

outcome(reconciled) :- chosen_repair(R), kind_repair(R), chosen_target(puppet).
outcome(rejected)   :- chosen_repair(R), repair(R), not kind_repair(R).
outcome(rejected)   :- chosen_target(T), target(T), not target_ok(T).

#show valid/3.
#show kind_repair/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.nibbles_props:
            lines.append(asp.fact("nibbles_props", cid))
        if c.human:
            lines.append(asp.fact("human", cid))
    for tid in TARGETS:
        lines.append(asp.fact("target", tid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("kindness", rid, r.kindness))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "kind_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_target", params.target),
        ]
    )
    model = asp.one_model(asp_program(scenario))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    if params.repair not in REPAIRS or params.target not in TARGETS:
        return "rejected"
    if REPAIRS[params.repair].kindness < KINDNESS_MIN:
        return "rejected"
    if params.target != "puppet":
        return "rejected"
    return "reconciled"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_repairs = {r.id for r in sensible_repairs()}
    asp_repairs = set(asp_kind_repairs())
    if py_repairs == asp_repairs:
        print(f"OK: kind repairs match ({sorted(py_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in repair gate: clingo={sorted(asp_repairs)} python={sorted(py_repairs)}")

    cases = list(CURATED)
    cases.append(
        StoryParams(
            creature="goat",
            memory="goose",
            repair="shrug",
            target="puppet",
            owner_name="Mira",
            owner_gender="girl",
            speaker_name="Toby",
            speaker_gender="boy",
            teacher_name="Miss Wren",
        )
    )
    cases.append(
        StoryParams(
            creature="goat",
            memory="goose",
            repair="patch",
            target="child",
            owner_name="Mira",
            owner_gender="girl",
            speaker_name="Toby",
            speaker_gender="boy",
            teacher_name="Miss Wren",
        )
    )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(17))
        smoke_params.seed = 17
        smoke_sample = generate(smoke_params)
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a scary word, a remembered fright, and a mended nursery rhyme."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--owner-name")
    ap.add_argument("--speaker-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--speaker-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


GIRL_NAMES = ["Mira", "Ada", "Nell", "Ruby", "June", "Ivy", "Tess", "Lila"]
BOY_NAMES = ["Toby", "Finn", "Pip", "Owen", "Milo", "Jem", "Kit", "Ned"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature is not None and args.repair is not None and args.target is not None:
        creature = CREATURES[args.creature]
        repair = REPAIRS[args.repair]
        if not valid_combo(creature, args.target, repair):
            raise StoryError(explain_rejection(creature, args.target, repair))

    if args.repair is not None and REPAIRS[args.repair].kindness < KINDNESS_MIN:
        creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        target = args.target if args.target else "puppet"
        raise StoryError(explain_rejection(creature, target, REPAIRS[args.repair]))

    if args.target is not None and args.target != "puppet":
        creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        repair = REPAIRS[args.repair] if args.repair else next(iter(sensible_repairs()))
        raise StoryError(explain_rejection(creature, args.target, repair))

    combos = [
        c for c in valid_combos()
        if (args.creature is None or c[0] == args.creature)
        and (args.target is None or c[1] == args.target)
        and (args.repair is None or c[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, target, repair_id = rng.choice(sorted(combos))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    speaker_gender = args.speaker_gender or rng.choice(["girl", "boy"])
    owner_name = args.owner_name or _pick_name(rng, owner_gender)
    speaker_name = args.speaker_name or _pick_name(rng, speaker_gender, avoid=owner_name)
    return StoryParams(
        creature=creature_id,
        memory=memory_id,
        repair=repair_id,
        target=target,
        owner_name=owner_name,
        owner_gender=owner_gender,
        speaker_name=speaker_name,
        speaker_gender=speaker_gender,
        teacher_name="Miss Wren",
    )


def generate(params: StoryParams) -> StorySample:
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")

    creature = CREATURES[params.creature]
    memory = MEMORIES[params.memory]
    repair = REPAIRS[params.repair]

    if not valid_combo(creature, params.target, repair):
        raise StoryError(explain_rejection(creature, params.target, repair))

    world = tell(
        creature=creature,
        memory=memory,
        repair=repair,
        target=params.target,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        speaker_name=params.speaker_name,
        speaker_gender=params.speaker_gender,
        teacher_name=params.teacher_name,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        repairs = asp_kind_repairs()
        print(f"kind repairs: {', '.join(repairs)}\n")
        print(f"{len(combos)} compatible (creature, target, repair) combos:\n")
        for creature, target, repair in combos:
            print(f"  {creature:10} {target:7} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.owner_name} & {p.speaker_name}: {p.creature}, {p.memory}, {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
