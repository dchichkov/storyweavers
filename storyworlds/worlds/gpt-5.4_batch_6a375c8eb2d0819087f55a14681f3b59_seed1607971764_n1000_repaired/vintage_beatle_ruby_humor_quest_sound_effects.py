#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py
============================================================================

A standalone story world for a tiny fairy-tale quest: a child meets a
waistcoated vintage beatle whose ruby has rolled away from a music box, and the
pair must recover it with the right silly tool.

The domain is intentionally small and constraint-checked:

- A REALM affords certain hiding places.
- Each HIDING PLACE requires a compatible retrieval method.
- Each TOOL supports one or more methods.
- Only compatible (realm, place, tool) stories are generated.

The live world model carries physical meters (lost, wet, sticky, retrieved,
ringing) and emotional memes (worry, hope, embarrassment, relief, joy).  A
small causal engine turns state into consequences: a lost ruby silences the
music box and worries the beatle; a bare-handed lunge can make the child soggy,
sticky, or sneezy; retrieving and resetting the ruby makes the music sing again.

Run it
------
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py --realm parlor --place gramophone_gap --tool ribbon_hook
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py --place lily_bowl --tool sugar_tongs
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vintage_beatle_ruby_humor_quest_sound_effects.py --verify
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

LISTENING_TRAITS = {"careful", "patient", "kind"}
FIRM_GUIDES = {"brisk", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Realm:
    id: str
    name: str
    intro: str
    light: str
    affords: set[str] = field(default_factory=set)
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    scene: str
    method: str
    hazard: str
    quick_fail: str
    hazard_effect: str
    sound: str
    recover_line: str
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
class Tool:
    id: str
    label: str
    phrase: str
    methods: set[str] = field(default_factory=set)
    move_sound: str = ""
    success_line: str = ""
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
class StoryParams:
    realm: str
    place: str
    tool: str
    child_name: str
    child_gender: str
    child_trait: str
    beatle_name: str
    guide_trait: str
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
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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
        clone = World(self.realm)
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


def _r_loss_silences(world: World) -> list[str]:
    ruby = world.get("ruby")
    box = world.get("music_box")
    beatle = world.get("beatle")
    if ruby.meters["lost"] < THRESHOLD:
        return []
    sig = ("loss_silences",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    box.meters["silent"] += 1
    beatle.memes["worry"] += 1
    beatle.memes["hope"] += 1
    return []


def _r_mishap_embarrasses(world: World) -> list[str]:
    child = world.get("child")
    beatle = world.get("beatle")
    if child.meters["mishap"] < THRESHOLD:
        return []
    sig = ("mishap_embarrasses",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    child.memes["determination"] += 1
    beatle.memes["concern"] += 1
    return []


def _r_retrieval_relief(world: World) -> list[str]:
    ruby = world.get("ruby")
    child = world.get("child")
    beatle = world.get("beatle")
    if ruby.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("retrieval_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ruby.meters["lost"] = 0.0
    child.memes["relief"] += 1
    beatle.memes["relief"] += 1
    beatle.memes["joy"] += 1
    return []


def _r_reset_restores_music(world: World) -> list[str]:
    ruby = world.get("ruby")
    box = world.get("music_box")
    child = world.get("child")
    beatle = world.get("beatle")
    if ruby.meters["set"] < THRESHOLD:
        return []
    sig = ("reset_restores_music",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    box.meters["ringing"] += 1
    box.meters["silent"] = 0.0
    child.memes["joy"] += 1
    beatle.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="loss_silences", tag="physical", apply=_r_loss_silences),
    Rule(name="mishap_embarrasses", tag="social", apply=_r_mishap_embarrasses),
    Rule(name="retrieval_relief", tag="social", apply=_r_retrieval_relief),
    Rule(name="reset_restores_music", tag="physical", apply=_r_reset_restores_music),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


REALMS = {
    "parlor": Realm(
        id="parlor",
        name="the Clockwork Parlor",
        intro="a room of winding clocks and lace curtains where every shelf seemed to remember a song",
        light="Amber afternoon light shone on a vintage gramophone and a neat row of teacups.",
        affords={"gramophone_gap", "jam_jar", "lily_bowl"},
    ),
    "garden": Realm(
        id="garden",
        name="the Rose-Cup Garden",
        intro="a garden behind the cottage where giant roses bowed over little pebble paths",
        light="Sunlight glittered on a lily bowl and on brass ornaments tucked among the leaves.",
        affords={"lily_bowl", "jam_jar"},
    ),
    "attic": Realm(
        id="attic",
        name="the Moonbeam Attic",
        intro="an attic of trunks, toy crowns, and old music where moonbeams made the dust look silver",
        light="A vintage sewing box sat beside a sleepy gramophone under the rafters.",
        affords={"gramophone_gap", "jam_jar"},
    ),
}

HIDING_PLACES = {
    "gramophone_gap": HidingPlace(
        id="gramophone_gap",
        label="gramophone gap",
        phrase="the narrow gap behind the gramophone cabinet",
        scene="The ruby had rolled behind a vintage gramophone, into a crack too slim for an easy reach.",
        method="hook",
        hazard="dusty",
        quick_fail="the crack would nip the knuckles and wake a sneeze",
        hazard_effect="dust puffed up around the child's nose",
        sound="skritch-skritch",
        recover_line="The jewel slid out at last like a red drop of sunset.",
        tags={"gramophone", "vintage", "dust"},
    ),
    "lily_bowl": HidingPlace(
        id="lily_bowl",
        label="lily bowl",
        phrase="the blue lily bowl by the window",
        scene="The ruby had plopped into a lily bowl where two paper swans bobbed in circles.",
        method="scoop",
        hazard="wet",
        quick_fail="the arm would only make a splash and send the jewel spinning deeper",
        hazard_effect="cool water splashed the child's sleeve",
        sound="glug-glug",
        recover_line="The ruby rocked into the spoon like a cherry in a silver moon.",
        tags={"water", "lily", "ruby"},
    ),
    "jam_jar": HidingPlace(
        id="jam_jar",
        label="jam jar",
        phrase="the tall raspberry jam jar on the side table",
        scene="The ruby had bounced into a jam jar and was blinking through the red stickiness like a trapped star.",
        method="pinch",
        hazard="sticky",
        quick_fail="fingers would only come back jammy while the jewel stayed put",
        hazard_effect="raspberry jam clung from fingertip to wrist",
        sound="splup-splup",
        recover_line="Up came the ruby, red and shining, with only one brave drop of jam following after it.",
        tags={"jam", "sticky", "ruby"},
    ),
}

TOOLS = {
    "ribbon_hook": Tool(
        id="ribbon_hook",
        label="ribbon hook",
        phrase="a ribbon hook made from a bonnet pin and blue ribbon",
        methods={"hook"},
        move_sound="zip-zip",
        success_line="It curled neatly behind the jewel and coaxed it forward.",
        tags={"hook", "ribbon"},
    ),
    "teaspoon_skimmer": Tool(
        id="teaspoon_skimmer",
        label="teaspoon skimmer",
        phrase="a long-handled teaspoon skimmer",
        methods={"scoop"},
        move_sound="plink-plink",
        success_line="It dipped under the little red gleam without splashing the bowl.",
        tags={"spoon", "water"},
    ),
    "sugar_tongs": Tool(
        id="sugar_tongs",
        label="sugar tongs",
        phrase="a pair of silver sugar tongs",
        methods={"pinch"},
        move_sound="click-click",
        success_line="The tiny jaws caught the ruby without asking the jam for permission.",
        tags={"tongs", "sticky"},
    ),
}

GIRL_NAMES = ["Ruby", "Lina", "Mira", "Elsie", "Nora", "Wren"]
BOY_NAMES = ["Theo", "Milo", "Pip", "Rowan", "Bram", "Ned"]
CHILD_TRAITS = ["careful", "patient", "kind", "curious", "hasty", "bouncy"]
GUIDE_TRAITS = ["wise", "brisk", "jolly", "fluttery"]

KNOWLEDGE = {
    "ruby": [(
        "What is a ruby?",
        "A ruby is a red gemstone. It can shine bright red when the light hits it."
    )],
    "vintage": [(
        "What does vintage mean?",
        "Vintage means something is from long ago and still special or beautiful. A vintage thing often feels old in a lovely way."
    )],
    "gramophone": [(
        "What is a gramophone?",
        "A gramophone is an old music machine. It plays sound from a spinning record."
    )],
    "water": [(
        "Why is it hard to pick a tiny thing up from water with your fingers?",
        "Little things can slip and wobble in water. A spoon or scoop can hold them more steadily."
    )],
    "sticky": [(
        "Why is jam sticky?",
        "Jam is full of fruit and sugar, so it clings to things. That is why fingers can get messy fast."
    )],
    "dust": [(
        "Why can dust make you sneeze?",
        "Dust can tickle your nose. When your nose wants it gone, it may make you sneeze."
    )],
    "hook": [(
        "What does a hook help you do?",
        "A hook can catch or pull something from a narrow place. It is useful when fingers cannot fit well."
    )],
    "spoon": [(
        "How can a spoon help in a rescue?",
        "A spoon can scoop up a small object. It helps lift something gently without dropping it."
    )],
    "tongs": [(
        "What are tongs for?",
        "Tongs are tools for pinching and lifting things. They help your fingers reach without getting messy."
    )],
}
KNOWLEDGE_ORDER = ["ruby", "vintage", "gramophone", "water", "sticky", "dust", "hook", "spoon", "tongs"]


def valid_combo(realm: Realm, place: HidingPlace, tool: Tool) -> bool:
    return place.id in realm.affords and place.method in tool.methods


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for place_id, place in HIDING_PLACES.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(realm, place, tool):
                    combos.append((realm_id, place_id, tool_id))
    return combos


def would_mishap(child_trait: str, guide_trait: str) -> bool:
    return child_trait not in LISTENING_TRAITS and guide_trait not in FIRM_GUIDES


def predict_quick_grab(world: World, place_id: str) -> dict:
    sim = world.copy()
    place = HIDING_PLACES[place_id]
    child = sim.get("child")
    if place.hazard == "wet":
        child.meters["wet"] += 1
    elif place.hazard == "sticky":
        child.meters["sticky"] += 1
    else:
        child.meters["dusty"] += 1
    child.meters["mishap"] += 1
    propagate(sim, narrate=False)
    return {
        "mishap": child.meters["mishap"] >= THRESHOLD,
        "effect": place.hazard,
    }


def explain_rejection(realm: Realm, place: HidingPlace, tool: Tool) -> str:
    if place.id not in realm.affords:
        return (
            f"(No story: {realm.name} does not contain {place.label}. "
            f"Choose a hiding place that belongs in this realm.)"
        )
    return (
        f"(No story: {tool.label} cannot retrieve a ruby from {place.label}. "
        f"That place needs a tool that can {place.method} it out.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "mishap" if would_mishap(params.child_trait, params.guide_trait) else "tidy"


def introduce(world: World, child: Entity, beatle: Entity, realm: Realm) -> None:
    world.say(
        f"Once upon a time, in {realm.name}, there lived {child.id}, a {child.traits[0]} "
        f"little {child.type}, and {beatle.id}, a tiny beatle in a waistcoat."
    )
    world.say(realm.intro)
    world.say(realm.light)


def setup_loss(world: World, child: Entity, beatle: Entity, place: HidingPlace) -> None:
    ruby = world.get("ruby")
    box = world.get("music_box")
    ruby.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{beatle.id} bowed so low that {beatle.pronoun('possessive')} hat nearly tipped off. "
        f'"Dear me," {beatle.pronoun()} squeaked. "The ruby from the music box has run away again!"'
    )
    world.say(place.scene)
    if box.meters["silent"] >= THRESHOLD:
        world.say(
            f"The little music box on the mantel gave only a sad '...tink?' and fell quiet. "
            f"Without its ruby, the room had forgotten how to sing."
        )


def promise_quest(world: World, child: Entity, beatle: Entity) -> None:
    child.memes["kindness"] += 1
    child.memes["bravery"] += 1
    world.say(
        f'"Then we shall go on a quest," said {child.id}. "{beatle.id}, point the way."'
    )
    world.say(
        f'"Tap-tap! Right this minute!" cried {beatle.id}, marching ahead on legs no thicker than threads.'
    )


def warn_about_grab(world: World, child: Entity, beatle: Entity, place: HidingPlace) -> None:
    pred = predict_quick_grab(world, place.id)
    world.facts["predicted_effect"] = pred["effect"]
    beatle.memes["concern"] += 1
    world.say(
        f"{child.id} knelt by {place.phrase} and reached forward at once."
    )
    world.say(
        f'"Boing, no!" cried {beatle.id}. "A quick grab there means {place.quick_fail}."'
    )


def quick_grab_mishap(world: World, child: Entity, place: HidingPlace) -> None:
    child.meters["mishap"] += 1
    if place.hazard == "wet":
        child.meters["wet"] += 1
    elif place.hazard == "sticky":
        child.meters["sticky"] += 1
    else:
        child.meters["dusty"] += 1
    propagate(world, narrate=False)
    if place.hazard == "wet":
        line = (
            f"But {child.id} gave one hopeful scoop with a bare hand anyway. "
            f"{place.sound}! {place.hazard_effect}, and the ruby bobbed away like it was giggling."
        )
    elif place.hazard == "sticky":
        line = (
            f"But {child.id} tried a fast pinch anyway. {place.sound}! {place.hazard_effect}, "
            f"while the ruby stayed exactly where it was, looking smug."
        )
    else:
        line = (
            f"But {child.id} tried a quick poke anyway. {place.sound}! {place.hazard_effect}, "
            f"and out burst a sneeze so grand it shook a tassel loose."
        )
    world.say(line)
    world.say(
        f'{child.id} blinked, then laughed a little. "That was not my cleverest move."'
    )


def choose_tool(world: World, beatle: Entity, tool: Tool) -> None:
    beatle.memes["hope"] += 1
    world.say(
        f'{beatle.id} straightened {beatle.pronoun("possessive")} waistcoat and held up {tool.phrase}. '
        f'"Quest rule number two," {beatle.pronoun()} said. "Use the right tiny thing for the tiny trouble."'
    )


def retrieve_ruby(world: World, child: Entity, beatle: Entity, place: HidingPlace, tool: Tool) -> None:
    ruby = world.get("ruby")
    ruby.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} guided the {tool.label} toward {place.phrase}. "
        f"{tool.move_sound}! {tool.success_line}"
    )
    world.say(place.recover_line)
    world.say(
        f'{beatle.id} clapped all six little hands. "Ha! A questing champion!"'
    )


def restore_music(world: World, child: Entity, beatle: Entity) -> None:
    ruby = world.get("ruby")
    ruby.meters["set"] += 1
    propagate(world, narrate=False)
    box = world.get("music_box")
    if box.meters["ringing"] >= THRESHOLD:
        world.say(
            f"{child.id} set the ruby back into the tiny music box crown. "
            f"'Click!' went the latch, and then 'ting-ting-tra-la!' sang the room."
        )
        world.say(
            f"The clocks nodded, the curtains fluttered, and even the sugar bowl seemed pleased."
        )
    child.memes["wonder"] += 1
    beatle.memes["wonder"] += 1


def ending_image(world: World, child: Entity, beatle: Entity, place: HidingPlace) -> None:
    if child.meters["wet"] >= THRESHOLD:
        extra = f"{child.id}'s sleeve was still damp, but now it looked like a badge of adventure."
    elif child.meters["sticky"] >= THRESHOLD:
        extra = f"{child.id}'s fingers were still a little jammy, and {beatle.id} declared that heroic hands were allowed one sticky day."
    elif child.meters["dusty"] >= THRESHOLD:
        extra = f"There was still a dust-speck on {child.id}'s nose, which made {beatle.id} laugh every time {child.pronoun()} sniffed."
    else:
        extra = f"Not a drop, smear, or sneeze had spoiled the brave little quest."
    world.say(
        f"From that day on, whenever the vintage music box began to hum, {child.id} and {beatle.id} smiled at one another."
    )
    world.say(
        f"{extra} And the ruby glowed red and merry, as if it too were trying not to giggle."
    )


def tell(
    realm: Realm,
    place: HidingPlace,
    tool: Tool,
    child_name: str = "Elsie",
    child_gender: str = "girl",
    child_trait: str = "careful",
    beatle_name: str = "Sir Click",
    guide_trait: str = "wise",
) -> World:
    world = World(realm)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        traits=[child_trait],
        role="child",
        attrs={},
        tags={"child"},
    ))
    beatle = world.add(Entity(
        id=beatle_name,
        kind="character",
        type="beatle",
        label=beatle_name,
        traits=[guide_trait],
        role="guide",
        attrs={},
        tags={"beatle", "vintage"},
    ))
    ruby = world.add(Entity(
        id="ruby",
        kind="thing",
        type="gem",
        label="ruby",
        attrs={},
        tags={"ruby"},
    ))
    box = world.add(Entity(
        id="music_box",
        kind="thing",
        type="music_box",
        label="music box",
        attrs={},
        tags={"vintage", "music"},
    ))

    world.facts.update(
        realm=realm,
        place_cfg=place,
        tool_cfg=tool,
        child=child,
        beatle=beatle,
        ruby=ruby,
        music_box=box,
        predicted_effect="",
        outcome="",
    )

    introduce(world, child, beatle, realm)
    setup_loss(world, child, beatle, place)

    world.para()
    promise_quest(world, child, beatle)
    warn_about_grab(world, child, beatle, place)

    if would_mishap(child_trait, guide_trait):
        quick_grab_mishap(world, child, place)
        outcome = "mishap"
    else:
        child.memes["self_control"] += 1
        world.say(
            f"{child.id} stopped just in time and folded {child.pronoun('possessive')} hands. "
            f'"I nearly made the trouble bigger," {child.pronoun()} admitted.'
        )
        outcome = "tidy"

    world.para()
    choose_tool(world, beatle, tool)
    retrieve_ruby(world, child, beatle, place, tool)
    restore_music(world, child, beatle)

    world.para()
    ending_image(world, child, beatle, place)

    world.facts.update(
        outcome=outcome,
        ruby_retrieved=world.get("ruby").meters["retrieved"] >= THRESHOLD,
        music_restored=world.get("music_box").meters["ringing"] >= THRESHOLD,
        mishap=child.meters["mishap"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    beatle = f["beatle"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    realm = f["realm"]
    outcome = f["outcome"]
    if outcome == "mishap":
        return [
            f'Write a fairy-tale quest story that includes the words "vintage", "beatle", and "ruby", and uses funny sound effects.',
            f"Tell a humorous quest where {child.id} helps a tiny beatle recover a lost ruby from {place.phrase}, makes one silly mistake first, and then uses {tool.phrase}.",
            f"Write a gentle story set in {realm.name} where a little hero and a waistcoated beatle save a silent music box and laugh along the way.",
        ]
    return [
        f'Write a fairy-tale quest story that includes the words "vintage", "beatle", and "ruby", and uses funny sound effects.',
        f"Tell a charming quest where {child.id} helps a tiny beatle recover a lost ruby from {place.phrase} by choosing the right tool.",
        f"Write a gentle story set in {realm.name} where a quiet warning prevents extra trouble and a music box sings again at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    beatle = f["beatle"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {beatle.id}, a tiny beatle in a waistcoat. Together they go on a quest to bring back a missing ruby."
        ),
        (
            "What problem started the quest?",
            f"The ruby from the music box had rolled away into {place.phrase}. Because the ruby was gone, the music box fell silent and the room lost its song."
        ),
        (
            f"Why did {beatle.id} tell {child.id} not to grab the ruby quickly?",
            f"{beatle.id} knew that a quick grab would cause trouble in that place. {beatle.pronoun().capitalize()} warned that {place.quick_fail}, so rushing would make the rescue harder instead of easier."
        ),
        (
            f"How did they get the ruby back?",
            f"{child.id} used {tool.phrase} to reach the jewel safely. The tool matched the hiding place, so the ruby could be lifted out without getting lost again."
        ),
        (
            "What changed at the end of the story?",
            f"The ruby was set back into the music box, and the room sang again with a happy 'ting-ting-tra-la!' That ending shows the quest was finished because the silence turned back into music."
        ),
    ]
    if outcome == "mishap":
        if child.meters["wet"] >= THRESHOLD:
            effect = "got splashed"
        elif child.meters["sticky"] >= THRESHOLD:
            effect = "got jam on those fingers"
        else:
            effect = "made dust fly and sneezed"
        qa.append((
            f"What happened when {child.id} tried too quickly at first?",
            f"{child.id} {effect}. The funny mishap proved that the beatle's warning was right, so {child.pronoun()} slowed down and used the proper tool."
        ))
    else:
        qa.append((
            f"Did {child.id} listen in time?",
            f"Yes. {child.id} stopped before making the trouble worse and admitted the warning was sensible. That careful pause helped the quest stay neat and successful."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place_cfg"]
    tool = world.facts["tool_cfg"]
    tags = {"ruby", "vintage"} | set(place.tags) | set(tool.tags)
    out: list[tuple[str, str]] = []
    mapping = {
        "ruby": "ruby",
        "vintage": "vintage",
        "gramophone": "gramophone",
        "water": "water",
        "sticky": "sticky",
        "dust": "dust",
        "hook": "hook",
        "spoon": "spoon",
        "tongs": "tongs",
    }
    for topic in KNOWLEDGE_ORDER:
        if topic in tags or topic in {mapping.get(t) for t in tags if t in mapping}:
            out.extend(KNOWLEDGE[topic])
    seen: set[tuple[str, str]] = set()
    cleaned: list[tuple[str, str]] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            cleaned.append(item)
    return cleaned


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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="parlor",
        place="gramophone_gap",
        tool="ribbon_hook",
        child_name="Elsie",
        child_gender="girl",
        child_trait="careful",
        beatle_name="Sir Click",
        guide_trait="wise",
    ),
    StoryParams(
        realm="parlor",
        place="lily_bowl",
        tool="teaspoon_skimmer",
        child_name="Theo",
        child_gender="boy",
        child_trait="bouncy",
        beatle_name="Lady Tikka",
        guide_trait="jolly",
    ),
    StoryParams(
        realm="garden",
        place="jam_jar",
        tool="sugar_tongs",
        child_name="Mira",
        child_gender="girl",
        child_trait="curious",
        beatle_name="Captain Crumb",
        guide_trait="fluttery",
    ),
    StoryParams(
        realm="attic",
        place="gramophone_gap",
        tool="ribbon_hook",
        child_name="Rowan",
        child_gender="boy",
        child_trait="patient",
        beatle_name="Duke Pip",
        guide_trait="brisk",
    ),
]


ASP_RULES = r"""
valid(R, P, T) :- realm(R), place(P), tool(T), affords(R, P), needs(P, M), supports(T, M).

listening_trait(careful; patient; kind).
firm_guide(brisk; wise).

mishap :- child_trait(C), not listening_trait(C), guide_trait(G), not firm_guide(G).
outcome(mishap) :- mishap.
outcome(tidy) :- not mishap.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for place_id in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, place_id))
    for place_id, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("needs", place_id, place.method))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for method in sorted(tool.methods):
            lines.append(asp.fact("supports", tool_id, method))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("child_trait", params.child_trait),
        asp.fact("guide_trait", params.guide_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
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
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome predictions differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test story was empty")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy-tale quest with a vintage beatle and a missing ruby."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--place", choices=HIDING_PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child", dest="child_name")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--child-trait", choices=CHILD_TRAITS)
    ap.add_argument("--beatle-name")
    ap.add_argument("--guide-trait", choices=GUIDE_TRAITS)
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
    if args.realm and args.place and args.tool:
        realm = REALMS[args.realm]
        place = HIDING_PLACES[args.place]
        tool = TOOLS[args.tool]
        if not valid_combo(realm, place, tool):
            raise StoryError(explain_rejection(realm, place, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.place is None or combo[1] == args.place)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, place_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    beatle_name = args.beatle_name or rng.choice(["Sir Click", "Lady Tikka", "Duke Pip", "Captain Crumb"])
    child_trait = args.child_trait or rng.choice(CHILD_TRAITS)
    guide_trait = args.guide_trait or rng.choice(GUIDE_TRAITS)

    return StoryParams(
        realm=realm_id,
        place=place_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=child_trait,
        beatle_name=beatle_name,
        guide_trait=guide_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.place not in HIDING_PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.child_trait not in CHILD_TRAITS:
        raise StoryError(f"(Unknown child trait: {params.child_trait})")
    if params.guide_trait not in GUIDE_TRAITS:
        raise StoryError(f"(Unknown guide trait: {params.guide_trait})")

    realm = REALMS[params.realm]
    place = HIDING_PLACES[params.place]
    tool = TOOLS[params.tool]
    if not valid_combo(realm, place, tool):
        raise StoryError(explain_rejection(realm, place, tool))

    world = tell(
        realm=realm,
        place=place,
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
        beatle_name=params.beatle_name,
        guide_trait=params.guide_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, place, tool) combos:\n")
        for realm, place, tool in combos:
            print(f"  {realm:8} {place:15} {tool}")
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
            header = f"### {p.child_name} and {p.beatle_name}: {p.place} in {p.realm} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
