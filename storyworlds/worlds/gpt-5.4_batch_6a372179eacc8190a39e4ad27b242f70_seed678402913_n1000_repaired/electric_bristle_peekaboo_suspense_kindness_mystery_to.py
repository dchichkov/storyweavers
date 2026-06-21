#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py
====================================================================================

A small story world about a strange buzzing sound, a tucked-away electric brush,
and two children who solve the mystery kindly together.

The seed asked for:
- the words "electric", "bristle", and "peekaboo"
- suspense
- kindness
- a mystery to solve
- an adventurous tone

This world models a nighttime search in a cozy place. A hidden buzzing object
creates suspense; a brave child chooses whether to be gentle with a scared
companion; a safe light reveals the clue; and the children end by helping the
object's owner instead of laughing at the fear.

Run it
------
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py --setting cabin --spot washbag
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py --light candle_lantern
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py --qa --json
    python storyworlds/worlds/gpt-5.4/electric_bristle_peekaboo_suspense_kindness_mystery_to.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    hush: str
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class BuzzThing:
    id: str
    label: str
    phrase: str
    bristle_color: str
    buzz: str
    use: str
    owner_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    darkness: int
    muffle: int
    reveal: str
    settings: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    power: int
    beam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GuideStyle:
    id: str
    comfort: int
    line: str
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


def _r_hidden_buzz(world: World) -> list[str]:
    source = world.get("source")
    spot = world.get("spot")
    if source.meters["on"] < THRESHOLD or source.meters["hidden"] < THRESHOLD:
        return []
    sig = ("hidden_buzz",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["mystery"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "worrier":
            ent.memes["fear"] += float(spot.attrs.get("darkness", 1))
    return ["__mystery__"]


def _r_kindness(world: World) -> list[str]:
    guide = world.get("guide")
    friend = world.get("friend")
    if guide.memes["comforting"] < THRESHOLD:
        return []
    sig = ("kindness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["fear"] = max(0.0, friend.memes["fear"] - guide.attrs.get("comfort", 1))
    friend.memes["courage"] += guide.attrs.get("comfort", 1)
    friend.memes["trust"] += 1
    return ["__comfort__"]


def _r_reveal(world: World) -> list[str]:
    source = world.get("source")
    light = world.get("light")
    friend = world.get("friend")
    spot = world.get("spot")
    if light.meters["shining"] < THRESHOLD or source.meters["hidden"] < THRESHOLD:
        return []
    need = int(spot.attrs.get("darkness", 1))
    power = int(light.attrs.get("power", 1))
    if power < need:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["found"] += 1
    source.meters["hidden"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    friend.memes["fear"] = max(0.0, friend.memes["fear"] - 1)
    friend.memes["relief"] += 1
    world.get("guide").memes["relief"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="hidden_buzz", tag="mystery", apply=_r_hidden_buzz),
    Rule(name="kindness", tag="social", apply=_r_kindness),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "cabin": Setting(
        id="cabin",
        place="the little forest cabin",
        opening="Rain tapped the pine roof, and the cabin felt like a fort at the edge of the woods.",
        hush="The hallway was dim and wooden, with shadows tucked between the pegs and towels.",
        spots={"washbag", "towel_stack", "bunk_shelf"},
        tags={"night", "cabin"},
    ),
    "lighthouse": Setting(
        id="lighthouse",
        place="the lighthouse keeper's cottage",
        opening="Wind curled around the lighthouse hill, and the cottage windows shone like tiny stars.",
        hush="The washroom below the tall stair felt full of echoes and secret corners.",
        spots={"washbag", "sink_drawer", "towel_stack"},
        tags={"night", "lighthouse"},
    ),
    "houseboat": Setting(
        id="houseboat",
        place="the small houseboat",
        opening="Water bumped softly against the boat, and every creak sounded like a clue from an adventure map.",
        hush="The narrow wash corner was snug and shadowy, with shelves built into the wall.",
        spots={"washbag", "sink_drawer", "bunk_shelf"},
        tags={"night", "boat"},
    ),
}

SOURCES = {
    "toothbrush": BuzzThing(
        id="toothbrush",
        label="electric toothbrush",
        phrase="an electric toothbrush",
        bristle_color="blue",
        buzz="zzzz-brrr",
        use="to brush teeth with tiny fast bristles",
        owner_hint="bedtime",
        tags={"electric", "toothbrush", "bristle"},
    ),
    "scrubbrush": BuzzThing(
        id="scrubbrush",
        label="electric scrub brush",
        phrase="an electric scrub brush",
        bristle_color="green",
        buzz="buzzy-whirr",
        use="to scrub muddy spots with a stiff bristle head",
        owner_hint="cleaning",
        tags={"electric", "brush", "bristle"},
    ),
}

SPOTS = {
    "washbag": Spot(
        id="washbag",
        label="washbag",
        phrase="a striped washbag under the sink",
        darkness=2,
        muffle=2,
        reveal="The zipper bulged, and something inside wriggled against the cloth.",
        settings={"cabin", "lighthouse", "houseboat"},
        tags={"bag", "hidden"},
    ),
    "towel_stack": Spot(
        id="towel_stack",
        label="towel stack",
        phrase="a tall stack of folded towels",
        darkness=1,
        muffle=1,
        reveal="One towel gave a funny little shake, as if it had swallowed a bee.",
        settings={"cabin", "lighthouse"},
        tags={"towels", "hidden"},
    ),
    "sink_drawer": Spot(
        id="sink_drawer",
        label="sink drawer",
        phrase="the sink drawer",
        darkness=2,
        muffle=1,
        reveal="The drawer hummed back when the light touched its crack.",
        settings={"lighthouse", "houseboat"},
        tags={"drawer", "hidden"},
    ),
    "bunk_shelf": Spot(
        id="bunk_shelf",
        label="bunk shelf",
        phrase="the little shelf by the bunks",
        darkness=1,
        muffle=1,
        reveal="Behind a rolled sock, a small handle trembled like a trapped bug.",
        settings={"cabin", "houseboat"},
        tags={"bunk", "hidden"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        power=2,
        beam="drew a clean yellow path through the dark",
        tags={"flashlight", "safe_light"},
    ),
    "headlamp": Light(
        id="headlamp",
        label="head-lamp",
        phrase="a snug head-lamp",
        power=2,
        beam="made a steady circle of light wherever they looked",
        tags={"headlamp", "safe_light"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a starry night-light",
        power=1,
        beam="spilled a small puddle of moon-soft light",
        tags={"nightlight", "safe_light"},
    ),
    "candle_lantern": Light(
        id="candle_lantern",
        label="paper lantern",
        phrase="a paper lantern with an electric candle inside",
        power=1,
        beam="glowed gently, brave but small",
        tags={"electric", "lantern", "safe_light"},
    ),
}

GUIDE_STYLES = {
    "gentle": GuideStyle(
        id="gentle",
        comfort=2,
        line="I will not let the mystery chase you. We can go together, slow as explorers.",
        tags={"kindness"},
    ),
    "playful": GuideStyle(
        id="playful",
        comfort=1,
        line="If something silly is hiding, we can catch it with a peekaboo beam.",
        tags={"peekaboo"},
    ),
    "steady": GuideStyle(
        id="steady",
        comfort=2,
        line="Hold my hand. We will look first and make up our minds after that.",
        tags={"kindness"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def spot_allowed(setting_id: str, spot_id: str) -> bool:
    return spot_id in SETTINGS[setting_id].spots and setting_id in SPOTS[spot_id].settings


def light_can_reveal(light_id: str, spot_id: str) -> bool:
    return LIGHTS[light_id].power >= SPOTS[spot_id].darkness


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in sorted(SETTINGS):
        for spot_id in sorted(SPOTS):
            if not spot_allowed(setting_id, spot_id):
                continue
            for light_id in sorted(LIGHTS):
                if not light_can_reveal(light_id, spot_id):
                    continue
                for source_id in sorted(SOURCES):
                    combos.append((setting_id, spot_id, light_id, source_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    spot: str
    light: str
    source: str
    guide_name: str
    guide_gender: str
    friend_name: str
    friend_gender: str
    relation: str
    style: str
    owner_type: str
    seed: Optional[int] = None


def explain_spot(setting_id: str, spot_id: str) -> str:
    return (
        f"(No story: {SPOTS[spot_id].phrase} does not belong in {SETTINGS[setting_id].place}. "
        f"Pick a hiding place that fits the setting.)"
    )


def explain_light(light_id: str, spot_id: str) -> str:
    return (
        f"(No story: {LIGHTS[light_id].phrase} is too dim to search {SPOTS[spot_id].phrase}. "
        f"The mystery needs a light strong enough to reveal the clue.)"
    )


def explain_source(source_id: str, spot_id: str) -> str:
    source = SOURCES[source_id]
    spot = SPOTS[spot_id]
    if source.id == "scrubbrush" and spot.id == "bunk_shelf":
        return (
            f"(No story: {source.phrase} is a cleaning tool, so leaving it on {spot.phrase} "
            f"is not a sensible bedtime mystery. Choose a sink area or a different source.)"
        )
    return "(No story: that source does not fit this hiding place.)"


def source_fits_spot(source_id: str, spot_id: str) -> bool:
    if source_id == "scrubbrush" and spot_id == "bunk_shelf":
        return False
    return True


def suspense_level(spot: Spot) -> int:
    return spot.darkness + spot.muffle


def outcome_of(params: StoryParams) -> str:
    guide = GUIDE_STYLES[params.style]
    spot = SPOTS[params.spot]
    light = LIGHTS[params.light]
    score = guide.comfort + light.power
    target = suspense_level(spot)
    return "calm" if score >= target else "jumpy"


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("guide").memes["comforting"] += 1
    propagate(sim, narrate=False)
    sim.get("light").meters["shining"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("source").meters["found"] >= THRESHOLD,
        "fear_after": sim.get("friend").memes["fear"],
    }


def introduce(world: World, guide: Entity, friend: Entity, setting: Setting) -> None:
    world.say(f"{setting.opening} {guide.id} and {friend.id} were supposed to be getting ready for bed in {setting.place}.")
    relation = guide.attrs.get("relation", "friends")
    if relation == "siblings":
        world.say(f"They whispered like treasure hunters sharing a secret map instead of two sleepy siblings in their pajamas.")
    else:
        world.say(f"They whispered like treasure hunters sharing a secret map instead of two sleepy friends in their pajamas.")


def start_mystery(world: World, setting: Setting, source_cfg: BuzzThing, spot_cfg: Spot, owner: Entity) -> None:
    source = world.get("source")
    source.meters["on"] += 1
    source.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(setting.hush)
    world.say(
        f"Then a strange sound slipped out of the shadows: {source_cfg.buzz}. It was small, but it was so steady that it made the room feel suddenly full of questions."
    )
    world.say(
        f'"Did you hear that?" whispered {world.get("friend").id}. The sound seemed to come from {spot_cfg.phrase}, where {owner.label_word} had left the bedtime things.'
    )


def fear_beat(world: World, friend: Entity, spot_cfg: Spot) -> None:
    if friend.memes["fear"] >= 2:
        world.say(
            f"{friend.id} moved close enough to bump shoulders. In the dark, {spot_cfg.label} looked almost like a little cave where anything might be waiting."
        )
    else:
        world.say(f"{friend.id} listened hard, curious but careful.")


def comfort(world: World, guide: Entity, friend: Entity, style: GuideStyle) -> None:
    guide.memes["comforting"] += 1
    propagate(world, narrate=False)
    world.say(f'{guide.id} reached for {friend.id}\'s hand. "{style.line}"')
    if friend.memes["fear"] < THRESHOLD:
        world.say(f"The words did not make the buzzing stop, but they made it feel smaller.")
    else:
        world.say(f"The buzzing still trembled in the room, yet now {friend.id} was trembling less.")


def search(world: World, guide: Entity, friend: Entity, light_cfg: Light, spot_cfg: Spot) -> None:
    light = world.get("light")
    light.meters["shining"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They took {light_cfg.phrase}. Its beam {light_cfg.beam}, and the two of them crept closer as if they were crossing a rope bridge over a deep ravine."
    )
    if "peekaboo" in GUIDE_STYLES[guide.attrs.get("style", "")].tags or guide.attrs.get("style") == "playful":
        world.say(
            f'{guide.id} tipped the light toward the hiding place and whispered, "Peekaboo, mystery. We see you now."'
        )
    else:
        world.say(f"{guide.id} lifted the light slowly, giving the shadows time to give up their secret.")
    world.say(spot_cfg.reveal)


def reveal(world: World, guide: Entity, friend: Entity, source_cfg: BuzzThing, owner: Entity) -> None:
    source = world.get("source")
    if source.meters["found"] < THRESHOLD:
        raise StoryError("(Story failure: the clue was not actually revealed.)")
    world.say(
        f"It was not a bug or a tiny cave monster at all. It was {source_cfg.phrase}, switched on by mistake, with its {source_cfg.bristle_color} bristle head shaking and buzzing against the cloth."
    )
    world.say(
        f'{friend.id} let out one surprised puff of air and then laughed. "It was only {owner.label_word}\'s {source_cfg.label}!"'
    )


def kind_resolution(world: World, guide: Entity, friend: Entity, source_cfg: BuzzThing, owner: Entity, outcome: str) -> None:
    guide.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    guide.memes["joy"] += 1
    friend.memes["joy"] += 1
    if outcome == "calm":
        world.say(
            f"{guide.id} clicked the brush off and set it gently in {owner.label_word}'s cup, so it would be ready in the morning."
        )
        world.say(
            f"They did not tease each other for being scared. Instead, they grinned the way explorers do after solving the hardest part of the map."
        )
    else:
        world.say(
            f"For one jumpy second they both nearly dropped the light, and then {guide.id} clicked the brush off and steadied it with both hands."
        )
        world.say(
            f'{guide.pronoun().capitalize()} smiled at {friend.id}. "Mysteries can sound bigger than they are." {friend.id} nodded, brave again now that the answer was real.'
        )
    if source_cfg.id == "toothbrush":
        world.say(
            f"When {owner.label_word} came by, the children showed {owner.pronoun('object')} the electric toothbrush and the wagging bristle head. {owner.label_word.capitalize()} thanked them for helping instead of hiding the clue away again."
        )
    else:
        world.say(
            f"When {owner.label_word} came by, the children showed {owner.pronoun('object')} the electric scrub brush. {owner.label_word.capitalize()} thanked them for rescuing it before it rattled all night."
        )
    world.say(
        f"After that, the dim little room no longer felt spooky. It felt like the place where {guide.id} and {friend.id} had solved a mystery together, hand in hand."
    )


def tell(
    setting: Setting,
    spot_cfg: Spot,
    light_cfg: Light,
    source_cfg: BuzzThing,
    guide_name: str,
    guide_gender: str,
    friend_name: str,
    friend_gender: str,
    relation: str,
    style_id: str,
    owner_type: str,
) -> World:
    world = World(setting)
    guide = world.add(
        Entity(
            id=guide_name,
            kind="character",
            type=guide_gender,
            role="guide",
            attrs={"relation": relation, "style": style_id, "comfort": GUIDE_STYLES[style_id].comfort},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="worrier",
            attrs={"relation": relation},
        )
    )
    owner = world.add(
        Entity(
            id="Owner",
            kind="character",
            type=owner_type,
            role="owner",
            label="the owner",
        )
    )
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot_cfg.label,
            phrase=spot_cfg.phrase,
            attrs={"darkness": spot_cfg.darkness, "muffle": spot_cfg.muffle},
        )
    )
    world.add(
        Entity(
            id="light",
            type="light",
            label=light_cfg.label,
            phrase=light_cfg.phrase,
            attrs={"power": light_cfg.power},
        )
    )
    world.add(
        Entity(
            id="source",
            type="tool",
            label=source_cfg.label,
            phrase=source_cfg.phrase,
            tags=set(source_cfg.tags),
        )
    )

    introduce(world, guide, friend, setting)
    world.para()
    start_mystery(world, setting, source_cfg, spot_cfg, owner)
    fear_beat(world, friend, spot_cfg)

    world.para()
    comfort(world, guide, friend, GUIDE_STYLES[style_id])
    pred = predict_reveal(world)
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_fear_after"] = pred["fear_after"]
    search(world, guide, friend, light_cfg, spot_cfg)
    reveal(world, guide, friend, source_cfg, owner)

    world.para()
    outcome = outcome_of(
        StoryParams(
            setting=setting.id,
            spot=spot_cfg.id,
            light=light_cfg.id,
            source=source_cfg.id,
            guide_name=guide_name,
            guide_gender=guide_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            relation=relation,
            style=style_id,
            owner_type=owner_type,
        )
    )
    kind_resolution(world, guide, friend, source_cfg, owner, outcome)

    world.facts.update(
        setting=setting,
        spot_cfg=spot_cfg,
        light_cfg=light_cfg,
        source_cfg=source_cfg,
        guide=guide,
        friend=friend,
        owner=owner,
        relation=relation,
        style=GUIDE_STYLES[style_id],
        outcome=outcome,
        found=world.get("source").meters["found"] >= THRESHOLD,
        suspense=suspense_level(spot_cfg),
    )
    return world


KNOWLEDGE = {
    "electric": [
        (
            "What does electric mean?",
            "Electric means something uses electricity to work. An electric toothbrush buzzes because a tiny motor inside it is moving."
        )
    ],
    "bristle": [
        (
            "What is a bristle?",
            "A bristle is one of the stiff little hairs on a brush. Lots of bristles together help a brush scrub or sweep."
        )
    ],
    "toothbrush": [
        (
            "What does an electric toothbrush do?",
            "An electric toothbrush helps clean teeth with a small moving brush head. The fast brushing can make a soft buzzing sound."
        )
    ],
    "brush": [
        (
            "What is a scrub brush for?",
            "A scrub brush is used to clean dirt or muddy spots. Its stiff bristles help rub the mess away."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight good for looking in dark places?",
            "A flashlight makes a bright beam you can point where you need it. That helps you see what is really there instead of only guessing."
        )
    ],
    "headlamp": [
        (
            "What is a head-lamp?",
            "A head-lamp is a light you wear on your head. It keeps your hands free while you look around."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small gentle glow in a dark room. It can help a room feel less scary at bedtime."
        )
    ],
    "kindness": [
        (
            "How can kindness help when someone feels scared?",
            "Kindness can make fear feel smaller because the scared person does not feel alone. A calm hand, a gentle voice, and staying together all help."
        )
    ],
    "peekaboo": [
        (
            "What is peekaboo?",
            "Peekaboo is a game where something hides and then suddenly appears. It can turn a tense moment into a playful one."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "electric",
    "bristle",
    "toothbrush",
    "brush",
    "flashlight",
    "headlamp",
    "nightlight",
    "kindness",
    "peekaboo",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    guide = f["guide"]
    friend = f["friend"]
    setting = f["setting"]
    source_cfg = f["source_cfg"]
    light_cfg = f["light_cfg"]
    return [
        'Write an adventure-style bedtime mystery for a 3-to-5-year-old that includes the words "electric", "bristle", and "peekaboo".',
        f"Tell a suspenseful but gentle story where {guide.id} and {friend.id} hear a strange buzz in {setting.place} and use {light_cfg.phrase} to discover that it is {source_cfg.phrase}.",
        f"Write a child-facing mystery-to-solve story where kindness matters as much as bravery, and the children help each other before they solve the sound."
    ]


def pair_noun(guide: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if guide.type == "boy" and friend.type == "boy":
            return "two brothers"
        if guide.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    guide = f["guide"]
    friend = f["friend"]
    owner = f["owner"]
    setting = f["setting"]
    source_cfg = f["source_cfg"]
    spot_cfg = f["spot_cfg"]
    light_cfg = f["light_cfg"]
    style = f["style"]
    pair = pair_noun(guide, friend, f["relation"])
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {guide.id} and {friend.id}, in {setting.place}. They become mystery-solvers when a strange buzzing sound appears at bedtime."
        ),
        (
            "What was the mystery?",
            f"The children heard a strange buzzing sound coming from {spot_cfg.phrase}, and they did not know what was making it. The hidden sound made the room feel spooky until they found the real cause."
        ),
        (
            f"Why did {friend.id} feel scared?",
            f"{friend.id} was scared because the sound came from a dark tucked-away place, and hidden noises can seem bigger than they really are. Before the light showed the answer, the mystery let imagination fill the shadows."
        ),
        (
            f"How was {guide.id} kind?",
            f"{guide.id} did not laugh at {friend.id}. {guide.pronoun().capitalize()} offered a hand and said, \"{style.line}\""
        ),
        (
            "How did they solve the mystery?",
            f"They used {light_cfg.phrase} and searched carefully near {spot_cfg.phrase}. The light revealed that the buzzing thing was {source_cfg.phrase} with its {source_cfg.bristle_color} bristle head shaking."
        ),
    ]
    if outcome == "calm":
        qa.append(
            (
                "How did the story end?",
                f"It ended calmly: the children switched the buzzing brush off and put it back for {owner.label_word}. The scary place no longer felt spooky once they knew the truth."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with one last startled jump and then relief. After they saw the real answer, the mystery shrank into an ordinary object they could gently put away."
            )
        )
    qa.append(
        (
            f"Why does the story use the word peekaboo?",
            f"The word peekaboo turns the search into a playful reveal instead of a mean scare. It shows how the children used courage and kindness to face the hidden sound together."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"electric", "bristle", "kindness"}
    source_cfg = world.facts["source_cfg"]
    light_cfg = world.facts["light_cfg"]
    style = world.facts["style"]
    tags |= set(source_cfg.tags)
    tags |= set(light_cfg.tags)
    if "peekaboo" in style.tags or style.id == "playful":
        tags.add("peekaboo")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cabin",
        spot="washbag",
        light="flashlight",
        source="toothbrush",
        guide_name="Lily",
        guide_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        relation="siblings",
        style="gentle",
        owner_type="grandfather",
    ),
    StoryParams(
        setting="lighthouse",
        spot="towel_stack",
        light="headlamp",
        source="scrubbrush",
        guide_name="Max",
        guide_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        relation="friends",
        style="steady",
        owner_type="grandmother",
    ),
    StoryParams(
        setting="houseboat",
        spot="bunk_shelf",
        light="nightlight",
        source="toothbrush",
        guide_name="Nora",
        guide_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        relation="siblings",
        style="playful",
        owner_type="father",
    ),
    StoryParams(
        setting="lighthouse",
        spot="sink_drawer",
        light="flashlight",
        source="toothbrush",
        guide_name="Sam",
        guide_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        relation="friends",
        style="gentle",
        owner_type="mother",
    ),
]


ASP_RULES = r"""
spot_allowed(S, P) :- setting(S), spot(P), affords(S, P), in_setting(P, S).
light_ok(L, P) :- light(L), spot(P), power(L, LP), darkness(P, DP), LP >= DP.
source_ok(Src, P) :- source(Src), spot(P), not bad_source_spot(Src, P).

valid(S, P, L, Src) :- spot_allowed(S, P), light_ok(L, P), source_ok(Src, P).

suspense(P, D + M) :- darkness(P, D), muffle(P, M).
calm_score(St, L, C + P) :- style(St), light(L), comfort(St, C), power(L, P).
outcome(calm) :- chosen_spot(P), chosen_light(L), chosen_style(St),
                 suspense(P, S), calm_score(St, L, C), C >= S.
outcome(jumpy) :- chosen_spot(P), chosen_light(L), chosen_style(St),
                  suspense(P, S), calm_score(St, L, C), C < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for spot_id in sorted(setting.spots):
            lines.append(asp.fact("affords", setting_id, spot_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("darkness", spot_id, spot.darkness))
        lines.append(asp.fact("muffle", spot_id, spot.muffle))
        for setting_id in sorted(spot.settings):
            lines.append(asp.fact("in_setting", spot_id, setting_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("power", light_id, light.power))
    for style_id, style in GUIDE_STYLES.items():
        lines.append(asp.fact("style", style_id))
        lines.append(asp.fact("comfort", style_id, style.comfort))
    lines.append(asp.fact("bad_source_spot", "scrubbrush", "bunk_shelf"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_style", params.style),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hidden electric buzz, a kind search, and a bedtime mystery solved."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--style", choices=GUIDE_STYLES)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--owner", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--guide-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spot and not spot_allowed(args.setting, args.spot):
        raise StoryError(explain_spot(args.setting, args.spot))
    if args.light and args.spot and not light_can_reveal(args.light, args.spot):
        raise StoryError(explain_light(args.light, args.spot))
    if args.source and args.spot and not source_fits_spot(args.source, args.spot):
        raise StoryError(explain_source(args.source, args.spot))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spot is None or combo[1] == args.spot)
        and (args.light is None or combo[2] == args.light)
        and (args.source is None or combo[3] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spot_id, light_id, source_id = rng.choice(sorted(combos))
    guide_name, guide_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=guide_name)
    return StoryParams(
        setting=setting_id,
        spot=spot_id,
        light=light_id,
        source=source_id,
        guide_name=args.guide_name or guide_name,
        guide_gender=guide_gender,
        friend_name=args.friend_name or friend_name,
        friend_gender=friend_gender,
        relation=args.relation or rng.choice(["siblings", "friends"]),
        style=args.style or rng.choice(sorted(GUIDE_STYLES)),
        owner_type=args.owner or rng.choice(["mother", "father", "grandmother", "grandfather"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Invalid light: {params.light})")
    if params.source not in SOURCES:
        raise StoryError(f"(Invalid source: {params.source})")
    if params.style not in GUIDE_STYLES:
        raise StoryError(f"(Invalid style: {params.style})")
    if params.owner_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Invalid owner: {params.owner_type})")
    if not spot_allowed(params.setting, params.spot):
        raise StoryError(explain_spot(params.setting, params.spot))
    if not light_can_reveal(params.light, params.spot):
        raise StoryError(explain_light(params.light, params.spot))
    if not source_fits_spot(params.source, params.spot):
        raise StoryError(explain_source(params.source, params.spot))

    world = tell(
        setting=SETTINGS[params.setting],
        spot_cfg=SPOTS[params.spot],
        light_cfg=LIGHTS[params.light],
        source_cfg=SOURCES[params.source],
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        relation=params.relation,
        style_id=params.style,
        owner_type=params.owner_type,
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


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke, trace=False, qa=False)
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verification guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, spot, light, source) combos:\n")
        for setting_id, spot_id, light_id, source_id in combos:
            print(f"  {setting_id:10} {spot_id:12} {light_id:14} {source_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.guide_name} & {p.friend_name}: {p.setting}, {p.spot}, {p.light}, {p.source} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
