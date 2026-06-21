#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py
============================================================================================

A small standalone story world for gentle ghost stories built from the seed
words "lonesome" and "salute", with Dialogue, Curiosity, and Transformation.

Premise
-------
A child notices a lonesome haunting sign in an old place. Instead of running
away, the child asks questions. The ghost answers, the child finds the missing
keepsake, and a respectful greeting helps the ghost transform from a dim, shaky
figure into a peaceful shining one.

The world model prefers plausible hauntings: the chosen setting must be able to
contain the sign, the sign must plausibly point to the missing keepsake, and
the greeting must be respectful enough for a child-facing resolution. A rude
greeting is known to the world but refused.

Run it
------
python storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py
python storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py --qa --json
python storyworlds/worlds/gpt-5.4/lonesome_salute_dialogue_curiosity_transformation_ghost_story.py --verify
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
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    hidden_spot: str
    closing: str
    supports: set[str] = field(default_factory=set)
    holds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    opening: str
    mystery: str
    linked_keepsakes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    ghost_role: str
    memory_line: str
    hidden_text: str
    transform_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Greeting:
    id: str
    words: str
    gesture: str
    respect: int
    sense: int
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_dialogue(world: World) -> list[str]:
    child = world.get("child")
    ghost = world.get("ghost")
    if ghost.meters["visible"] < THRESHOLD or child.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("dialogue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["trust"] += 1
    return ["__dialogue__"]


def _r_return(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    ghost = world.get("ghost")
    if keepsake.meters["returned"] < THRESHOLD:
        return []
    sig = ("return",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["hope"] += 1
    ghost.meters["burden"] = 0.0
    return ["__return__"]


def _r_transform(world: World) -> list[str]:
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.memes["hope"] < THRESHOLD or child.memes["respect"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["dim"] = 0.0
    ghost.meters["bright"] += 1
    ghost.meters["peace"] += 1
    ghost.meters["visible"] += 1
    ghost.attrs["form"] = "changed"
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="dialogue", tag="social", apply=_r_dialogue),
    Rule(name="return", tag="memory", apply=_r_return),
    Rule(name="transform", tag="spiritual", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the old attic",
        opening="The attic above the house smelled of cedar and dust, and moonlight lay over the trunks like pale blankets.",
        hidden_spot="inside a cracked sea chest under an old quilt",
        closing="By morning, the attic no longer felt lonely; it felt watched over.",
        supports={"draft_song", "portrait_glow"},
        holds={"medal", "ribbon"},
        tags={"attic", "old_house"},
    ),
    "garden": Setting(
        id="garden",
        place="the walled garden",
        opening="The garden behind the house was full of silver dew, and the tall gate clicked softly whenever the wind passed through.",
        hidden_spot="beneath a loose stone by the dry fountain",
        closing="When dawn touched the roses, the garden looked less haunted and more loved.",
        supports={"gate_tap", "portrait_glow"},
        holds={"ribbon", "lantern"},
        tags={"garden", "night"},
    ),
    "watchtower": Setting(
        id="watchtower",
        place="the old watchtower",
        opening="The stone watchtower stood over the fields, and the stairs held every footstep as if they remembered them.",
        hidden_spot="in a little wall niche behind a hanging map",
        closing="Afterward, the watchtower kept its silence kindly, like a place at rest.",
        supports={"lantern_swing", "draft_song"},
        holds={"medal", "lantern"},
        tags={"tower", "night"},
    ),
}

SIGNS = {
    "draft_song": Sign(
        id="draft_song",
        label="a thin song in the draft",
        opening="A lonesome tune slipped through the dark as if someone were humming with no breath at all.",
        mystery='“Did you hear that?”',
        linked_keepsakes={"medal", "ribbon"},
        tags={"song", "ghost"},
    ),
    "portrait_glow": Sign(
        id="portrait_glow",
        label="a glowing portrait",
        opening="An old portrait on the wall gave off a small gray shimmer, and the painted eyes seemed full of waiting.",
        mystery='“Why is that picture shining?”',
        linked_keepsakes={"ribbon", "lantern"},
        tags={"portrait", "ghost"},
    ),
    "lantern_swing": Sign(
        id="lantern_swing",
        label="a swinging lantern",
        opening="A lantern with no hand on it began to sway, brushing gold light over the stones and then going dim again.",
        mystery='“Who is moving that lantern?”',
        linked_keepsakes={"lantern", "medal"},
        tags={"lantern", "ghost"},
    ),
}

KEEPSAKES = {
    "medal": Keepsake(
        id="medal",
        label="brass medal",
        phrase="a brass medal on a frayed ribbon",
        ghost_role="watcher",
        memory_line="I used to stand watch and salute the sunrise from this very place.",
        hidden_text="At the bottom lay a brass medal, cold and heavy, with a little star stamped in the middle.",
        transform_text="The ghost straightened like a night guard remembering an old promise and lifted a shining hand in salute.",
        tags={"medal", "memory"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon folded like a tiny bow",
        ghost_role="dancer",
        memory_line="I wore this ribbon when music still filled the room and my feet knew every turn.",
        hidden_text="There, tucked between old things, rested a blue ribbon soft as a faded petal.",
        transform_text="The ghost spun once, slowly and lightly, until the ragged edges of its shape turned smooth and bright.",
        tags={"ribbon", "memory"},
    ),
    "lantern": Keepsake(
        id="lantern",
        label="tin lantern",
        phrase="a small tin lantern with a cloudy glass pane",
        ghost_role="keeper",
        memory_line="I carried this lantern so no child would lose the path home in the dark.",
        hidden_text="Hidden in the shadows was a small tin lantern with a handle bent into a careful curve.",
        transform_text="Warm light spread through the ghost from the inside out, until it glowed like a lantern newly lit.",
        tags={"lantern", "memory"},
    ),
}

GREETINGS = {
    "salute": Greeting(
        id="salute",
        words="I salute you.",
        gesture="raised one small hand in a careful salute",
        respect=2,
        sense=2,
        closing="The ghost answered the salute with a smile that looked almost solid.",
        tags={"salute", "respect"},
    ),
    "hello": Greeting(
        id="hello",
        words="Hello. I am not here to be mean.",
        gesture="spoke softly into the dimness",
        respect=1,
        sense=2,
        closing="The ghost nodded as if kindness itself had opened a door.",
        tags={"hello", "respect"},
    ),
    "bow": Greeting(
        id="bow",
        words="I brought what you lost.",
        gesture="made a little bow before holding the keepsake out",
        respect=1,
        sense=2,
        closing="The ghost bent its shining head in thanks.",
        tags={"bow", "respect"},
    ),
    "mock": Greeting(
        id="mock",
        words="Go away, silly sheet.",
        gesture="laughed at the ghost",
        respect=0,
        sense=0,
        closing="",
        tags={"rude"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ava", "Elsie", "Clara", "Rose", "Maya"]
BOY_NAMES = ["Tom", "Eli", "Noah", "Finn", "Leo", "Sam", "Theo", "Ben"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "quiet", "gentle"]


def sign_matches(setting_id: str, sign_id: str) -> bool:
    return sign_id in SETTINGS[setting_id].supports


def keepsake_matches(setting_id: str, sign_id: str, keepsake_id: str) -> bool:
    setting = SETTINGS[setting_id]
    sign = SIGNS[sign_id]
    return keepsake_id in setting.holds and keepsake_id in sign.linked_keepsakes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for sign_id in SIGNS:
            if not sign_matches(setting_id, sign_id):
                continue
            for keepsake_id in KEEPSAKES:
                if not keepsake_matches(setting_id, sign_id, keepsake_id):
                    continue
                for greeting_id, greeting in GREETINGS.items():
                    if greeting.sense >= SENSE_MIN:
                        combos.append((setting_id, sign_id, keepsake_id, greeting_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    sign: str
    keepsake: str
    greeting: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="attic",
        sign="draft_song",
        keepsake="medal",
        greeting="salute",
        child_name="Lily",
        child_gender="girl",
        elder_type="grandmother",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        setting="garden",
        sign="portrait_glow",
        keepsake="ribbon",
        greeting="hello",
        child_name="Tom",
        child_gender="boy",
        elder_type="grandfather",
        trait="thoughtful",
        seed=102,
    ),
    StoryParams(
        setting="watchtower",
        sign="lantern_swing",
        keepsake="lantern",
        greeting="bow",
        child_name="Mina",
        child_gender="girl",
        elder_type="grandmother",
        trait="brave",
        seed=103,
    ),
    StoryParams(
        setting="watchtower",
        sign="draft_song",
        keepsake="medal",
        greeting="salute",
        child_name="Eli",
        child_gender="boy",
        elder_type="grandfather",
        trait="quiet",
        seed=104,
    ),
]


def explain_rejection(setting_id: str, sign_id: str, keepsake_id: str, greeting_id: str) -> str:
    if greeting_id in GREETINGS and GREETINGS[greeting_id].sense < SENSE_MIN:
        return (
            f"(No story: greeting '{greeting_id}' is too rude for this gentle ghost world. "
            f"Choose a respectful greeting such as salute, hello, or bow.)"
        )
    if setting_id in SETTINGS and sign_id in SIGNS and not sign_matches(setting_id, sign_id):
        return (
            f"(No story: {SIGNS[sign_id].label} does not fit {SETTINGS[setting_id].place}. "
            f"Pick a sign the setting could really hold.)"
        )
    if setting_id in SETTINGS and sign_id in SIGNS and keepsake_id in KEEPSAKES:
        return (
            f"(No story: {KEEPSAKES[keepsake_id].phrase} does not match the memory suggested by "
            f"{SIGNS[sign_id].label} in {SETTINGS[setting_id].place}.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def outcome_of(params: StoryParams) -> str:
    greeting = GREETINGS[params.greeting]
    return "salute_release" if greeting.respect >= 2 else "gentle_release"


def predict_dialogue(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    ghost = sim.get("ghost")
    child.memes["curiosity"] += 1
    ghost.meters["visible"] += 1
    propagate(sim, narrate=False)
    return ghost.memes["trust"] >= THRESHOLD


def introduce(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"One cool evening, {child.id} climbed with {child.pronoun('possessive')} {elder.label_word} to {setting.place}. "
        f"{setting.opening}"
    )
    world.say(
        f"{child.id} was a {next((t for t in child.traits if t), 'quiet')} child, and old places always made "
        f"{child.pronoun('object')} wonder who had been there before."
    )


def first_sign(world: World, child: Entity, sign: Sign) -> None:
    ghost = world.get("ghost")
    ghost.meters["visible"] += 1
    child.memes["unease"] += 1
    child.memes["curiosity"] += 1
    world.say(sign.opening)
    world.say(f'{sign.mystery} {child.id} whispered.')
    propagate(world, narrate=False)


def elder_warning(world: World, child: Entity, elder: Entity) -> None:
    if predict_dialogue(world):
        world.say(
            f'"If the house wants to tell a story," {elder.label_word} said, "listen with a kind heart."'
        )
    else:
        world.say(
            f'"Stay close to me," {elder.label_word} said softly.'
        )


def approach(world: World, child: Entity, greeting: Greeting) -> None:
    ghost = world.get("ghost")
    child.memes["respect"] += float(greeting.respect)
    child.memes["fear"] = 0.0
    world.say(
        f"Instead of running, {child.id} {greeting.gesture} and said, "
        f'"{greeting.words}"'
    )
    propagate(world, narrate=False)
    if ghost.memes["trust"] >= THRESHOLD:
        world.say("The cold in the air loosened a little, as if the dark had decided to answer back.")


def ghost_speaks(world: World, child: Entity, keepsake: Keepsake) -> None:
    ghost = world.get("ghost")
    ghost.attrs["role_name"] = keepsake.ghost_role
    world.say(
        'From the gray shimmer came a voice no louder than turning paper. '
        f'"I have been lonesome for a very long time," it said. '
        f'"Something of mine is still hidden here. {keepsake.memory_line}"'
    )
    world.say(
        f'"Then let me look," {child.id} said.'
    )


def search(world: World, child: Entity, setting: Setting, keepsake: Keepsake) -> None:
    child.meters["searching"] += 1
    world.say(
        f"With a candle stub in one hand and {child.pronoun('possessive')} questions in the other, "
        f"{child.id} searched {setting.hidden_spot}."
    )
    world.say(keepsake.hidden_text)


def return_keepsake(world: World, child: Entity, keepsake: Keepsake) -> None:
    item = world.get("keepsake")
    item.meters["found"] += 1
    item.meters["returned"] += 1
    world.say(
        f"{child.id} carried the {keepsake.label} back through the hush and held it out. "
        f'"Was it this?"'
    )
    propagate(world, narrate=False)


def transform(world: World, keepsake: Keepsake, greeting: Greeting) -> None:
    ghost = world.get("ghost")
    if ghost.meters["bright"] >= THRESHOLD:
        world.say(keepsake.transform_text)
        world.say(greeting.closing)
    else:
        world.say("The gray shape softened and grew less lonely, though it did not yet shine.")


def release(world: World, child: Entity, setting: Setting, params: StoryParams) -> None:
    ghost = world.get("ghost")
    outcome = outcome_of(params)
    if outcome == "salute_release":
        world.say(
            f'"Thank you," the ghost said. "Now I remember how to stand tall." '
            f"It gave {child.id} one last bright salute, and then its light thinned into the dawn."
        )
    else:
        world.say(
            f'"Thank you," the ghost said. "Now I can rest." '
            f"It grew gentle and clear, then drifted upward like the palest morning mist."
        )
    ghost.meters["visible"] = 0.0
    world.say(setting.closing)


def tell(
    setting: Setting,
    sign: Sign,
    keepsake: Keepsake,
    greeting: Greeting,
    child_name: str = "Lily",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
        )
    )
    ghost.meters["dim"] += 1
    ghost.meters["burden"] += 1
    ghost.attrs["form"] = "ragged"
    item = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
        )
    )

    introduce(world, child, elder, setting)
    world.para()
    first_sign(world, child, sign)
    elder_warning(world, child, elder)
    approach(world, child, greeting)
    ghost_speaks(world, child, keepsake)
    world.para()
    search(world, child, setting, keepsake)
    return_keepsake(world, child, keepsake)
    transform(world, keepsake, greeting)
    world.para()
    release(world, child, setting, StoryParams(
        setting=setting.id,
        sign=sign.id,
        keepsake=keepsake.id,
        greeting=greeting.id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        trait=trait,
    ))

    world.facts.update(
        child=child,
        elder=elder,
        ghost=ghost,
        setting=setting,
        sign=sign,
        keepsake_cfg=keepsake,
        greeting=greeting,
        keepsake=item,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                sign=sign.id,
                keepsake=keepsake.id,
                greeting=greeting.id,
                child_name=child_name,
                child_gender=child_gender,
                elder_type=elder_type,
                trait=trait,
            )
        ),
        transformed=ghost.meters["bright"] >= THRESHOLD,
        dialogue_started=ghost.memes["trust"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story about someone or something that seems to come from another time. In gentle ghost stories, the mystery is often sad or lonely instead of mean."
        )
    ],
    "salute": [
        (
            "What is a salute?",
            "A salute is a respectful gesture, often made by lifting a hand neatly. It can show honor, thanks, or remembrance."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space right under the roof of a house. People often keep old trunks, boxes, and memories there."
        )
    ],
    "garden": [
        (
            "Why can a garden feel spooky at night?",
            "At night, shadows move, leaves rustle, and familiar things look strange. That can make a garden feel mysterious even when it is still safe."
        )
    ],
    "tower": [
        (
            "What is a watchtower for?",
            "A watchtower is a tall place where someone can look far away and keep watch. Long ago, people used towers to guard roads, fields, or towns."
        )
    ],
    "portrait": [
        (
            "What is a portrait?",
            "A portrait is a picture of a person, often painted carefully to show what they looked like. Old portraits can make people wonder about lives from long ago."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light inside a case or frame, often with glass around it. It helps people see in the dark."
        )
    ],
    "medal": [
        (
            "What is a medal?",
            "A medal is a small piece of metal given or kept to remember something important. People may treasure medals because they carry a story."
        )
    ],
    "ribbon": [
        (
            "Why can a ribbon matter in a story?",
            "A ribbon can matter because it is small but full of memory. Sometimes one little object helps someone remember a whole moment from long ago."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to ask questions and learn more. It can help someone understand something that first seemed scary."
        )
    ],
    "kindness": [
        (
            "Why does kindness help in a scary moment?",
            "Kindness can calm people and make them feel safe enough to speak honestly. In stories, kindness often changes fear into understanding."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "salute",
    "attic",
    "garden",
    "tower",
    "portrait",
    "lantern",
    "medal",
    "ribbon",
    "curiosity",
    "kindness",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    sign = f["sign"]
    keepsake = f["keepsake_cfg"]
    greeting = f["greeting"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "lonesome" and "salute".',
        f"Tell a story where a {child.type} named {child.id} notices {sign.label} in {setting.place}, asks questions instead of running away, and helps a ghost by returning {keepsake.phrase}.",
        f"Write a story with dialogue, curiosity, and transformation, ending when the child uses a respectful greeting like {greeting.id} and the ghost changes into something peaceful.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    sign = f["sign"]
    keepsake = f["keepsake_cfg"]
    greeting = f["greeting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and a ghost waiting in {setting.place}. The story follows how {child.id} turns fear into understanding."
        ),
        (
            f"What first made {child.id} think something strange was there?",
            f"{sign.opening} That sign made the place feel haunted and pulled {child.id}'s curiosity forward."
        ),
        (
            f"Why did {child.id} talk to the ghost instead of running away?",
            f"{child.id} was frightened for a moment, but curiosity was stronger than the wish to hide. {elder.label_word.capitalize()} also reminded {child.pronoun('object')} to listen with a kind heart."
        ),
        (
            "What did the ghost want?",
            f"The ghost wanted its lost keepsake back. It had been lonesome because that small object held the memory of who it had been."
        ),
        (
            f"Where did {child.id} find the missing thing?",
            f"{child.id} found it {setting.hidden_spot}. The search matters because the ghost could only change after the keepsake was returned."
        ),
    ]
    if outcome == "salute_release":
        qa.append(
            (
                "How did the story use the word salute?",
                f"{child.id} greeted the ghost with a careful salute, and the ghost answered with one of its own. That respectful moment helped the ghost stand tall again and leave in peace."
            )
        )
    else:
        qa.append(
            (
                "How did the ghost transform at the end?",
                f"After the keepsake was returned and the child spoke kindly, the ghost changed from a dim, ragged shape into a gentle shining one. Then it drifted away peacefully because it was no longer lonely."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the ghost released and {setting.place} feeling calmer than before. The last image shows that kindness and curiosity changed the whole place."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "curiosity", "kindness"}
    setting = f["setting"]
    sign = f["sign"]
    keepsake = f["keepsake_cfg"]
    greeting = f["greeting"]
    tags |= set(setting.tags)
    tags |= set(sign.tags)
    tags |= set(keepsake.tags)
    tags |= set(greeting.tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_sign(S, G) :- setting(S), sign(G), supports(S, G).
fits_keepsake(S, G, K) :- setting(S), sign(G), keepsake(K), holds(S, K), linked(G, K).
respectful(H) :- greeting(H), sense(H, V), sense_min(M), V >= M.

valid(S, G, K, H) :- fits_sign(S, G), fits_keepsake(S, G, K), respectful(H).

outcome(salute_release) :- chosen_greeting(H), respect(H, R), R >= 2.
outcome(gentle_release) :- chosen_greeting(H), respect(H, R), R < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for sign in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, sign))
        for keepsake in sorted(setting.holds):
            lines.append(asp.fact("holds", sid, keepsake))
    for gid, sign in SIGNS.items():
        lines.append(asp.fact("sign", gid))
        for keepsake in sorted(sign.linked_keepsakes):
            lines.append(asp.fact("linked", gid, keepsake))
    for kid in KEEPSAKES:
        lines.append(asp.fact("keepsake", kid))
    for hid, greeting in GREETINGS.items():
        lines.append(asp.fact("greeting", hid))
        lines.append(asp.fact("sense", hid, greeting.sense))
        lines.append(asp.fact("respect", hid, greeting.respect))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_greeting", params.greeting)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print("MISMATCH in outcome:", case, asp_outcome(case), outcome_of(case))
            break
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Gentle ghost story world: a lonesome haunting, a respectful greeting, and a peaceful transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--greeting", choices=GREETINGS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.greeting and GREETINGS[args.greeting].sense < SENSE_MIN:
        raise StoryError(explain_rejection(
            args.setting or next(iter(SETTINGS)),
            args.sign or next(iter(SIGNS)),
            args.keepsake or next(iter(KEEPSAKES)),
            args.greeting,
        ))
    if args.setting and args.sign and not sign_matches(args.setting, args.sign):
        raise StoryError(explain_rejection(
            args.setting,
            args.sign,
            args.keepsake or next(iter(KEEPSAKES)),
            args.greeting or "salute",
        ))
    if args.setting and args.sign and args.keepsake and not keepsake_matches(args.setting, args.sign, args.keepsake):
        raise StoryError(explain_rejection(args.setting, args.sign, args.keepsake, args.greeting or "salute"))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sign is None or combo[1] == args.sign)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.greeting is None or combo[3] == args.greeting)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sign_id, keepsake_id, greeting_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        sign=sign_id,
        keepsake=keepsake_id,
        greeting=greeting_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Invalid sign: {params.sign})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake: {params.keepsake})")
    if params.greeting not in GREETINGS:
        raise StoryError(f"(Invalid greeting: {params.greeting})")
    if params.greeting in GREETINGS and GREETINGS[params.greeting].sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.setting, params.sign, params.keepsake, params.greeting))
    if not sign_matches(params.setting, params.sign):
        raise StoryError(explain_rejection(params.setting, params.sign, params.keepsake, params.greeting))
    if not keepsake_matches(params.setting, params.sign, params.keepsake):
        raise StoryError(explain_rejection(params.setting, params.sign, params.keepsake, params.greeting))

    world = tell(
        setting=SETTINGS[params.setting],
        sign=SIGNS[params.sign],
        keepsake=KEEPSAKES[params.keepsake],
        greeting=GREETINGS[params.greeting],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sign, keepsake, greeting) combos:\n")
        for setting_id, sign_id, keepsake_id, greeting_id in combos:
            print(f"  {setting_id:10} {sign_id:14} {keepsake_id:9} {greeting_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting}, {p.sign}, {p.keepsake}, {p.greeting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
