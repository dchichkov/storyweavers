#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py
===================================================================================

A standalone story world for a gentle ghost-story domain: a curious child sees a
strange night sign near a tray of sushi, begins a small quest, and learns that
curiosity is most beneficial when shared with a trusted helper.

The world models:
- a child, helper, and gentle ghost
- a moonlit place with one practical hidden need
- physical meters (light, danger, solved, found)
- emotional memes (curiosity, fear, trust, relief, lesson)

The prose is driven from simulated state and a short screenplay:
setup -> omen -> warning -> decision -> quest -> reveal -> fix -> ending image

Run it
------
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py --all
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py --trace
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py --json
    python storyworlds/worlds/gpt-5.4/beneficial_sushi_curiosity_quest_lesson_learned_ghost.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CALM_TRAITS = {"careful", "patient", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "grandmother"}
        male = {"boy", "father", "uncle", "man", "grandfather"}
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
        }.get(self.type, self.type)
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
    opening: str
    path: str
    ending: str
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
class Omen:
    id: str
    text: str
    motion: str
    whisper: str
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
class Tool:
    id: str
    label: str
    phrase: str
    beam: str
    safe: bool
    makes_flame: bool = False
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
class Need:
    id: str
    label: str
    hint: str
    reveal: str
    consequence: str
    benefit: str
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
class Response:
    id: str
    sense: int
    solves: str
    text: str
    qa_text: str
    fail_text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {
            "problem_found": False,
            "solved": False,
            "outcome": "",
            "startled": False,
            "waited": False,
            "pet": "",
        }

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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    place = world.get("place")
    ghost = world.get("ghost")
    need = world.get("need")

    if child.meters["walking_alone"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            place.meters["unease"] += 1
            world.facts["startled"] = True
            out.append("The shadows suddenly looked longer, and the night felt much bigger than before.")

    if child.meters["light"] >= THRESHOLD and ghost.meters["guiding"] >= THRESHOLD:
        sig = ("found", need.id)
        if sig not in world.fired:
            world.fired.add(sig)
            need.meters["found"] += 1
            world.facts["problem_found"] = True

    if need.meters["found"] >= THRESHOLD and need.meters["help_given"] >= THRESHOLD:
        sig = ("solved", need.id)
        if sig not in world.fired:
            world.fired.add(sig)
            need.meters["solved"] += 1
            place.meters["calm"] += 1
            ghost.meters["peace"] += 1
            child.memes["relief"] += 1
            child.memes["lesson"] += 1
            helper.memes["pride"] += 1
            world.facts["solved"] = True

    if narrate:
        for line in out:
            world.say(line)
    return out


PLACES = {
    "inn": Place(
        id="inn",
        label="the old seaside inn",
        mood="salty and silver in the moonlight",
        opening="The floorboards remembered every footstep, and the kitchen windows glimmered like sleepy eyes.",
        path="a narrow hall that led past the pantry and out to the back steps",
        ending="From then on, the inn felt less haunted and more kindly watched.",
        affords={"cat", "medicine"},
        tags={"inn", "night"},
    ),
    "temple": Place(
        id="temple",
        label="the little hill temple",
        mood="quiet under the cedar trees",
        opening="Paper charms stirred on their strings, and the stone path held pale pools of moonlight.",
        path="the lantern path between the kitchen door and the herb shed",
        ending="After that, the temple bells sounded gentle instead of eerie.",
        affords={"cat", "shutter"},
        tags={"temple", "night"},
    ),
    "teahouse": Place(
        id="teahouse",
        label="the garden teahouse",
        mood="still beside the pond",
        opening="The pond reflected the moon like a round white coin, and the shoji screens shivered softly.",
        path="the stepping-stones between the tea room and the little storehouse",
        ending="Since that night, the teahouse seemed full of old kindness instead of old chills.",
        affords={"medicine", "shutter"},
        tags={"teahouse", "night"},
    ),
}

OMENS = {
    "lantern": Omen(
        id="lantern",
        text="a pale blue lantern-light floating where no hand held it",
        motion="drifted ahead as if it wanted to be followed",
        whisper='"This way," seemed to sigh the boards underfoot.',
        tags={"ghost", "lantern"},
    ),
    "whisper": Omen(
        id="whisper",
        text="a whisper that moved from one dark corner to another",
        motion="slipped onward each time someone listened closely",
        whisper='"Not here. There," the sound seemed to breathe.',
        tags={"ghost", "whisper"},
    ),
    "tapping": Omen(
        id="tapping",
        text="a small tapping, like a fingernail on a bowl",
        motion="came once, then twice, then farther down the hall",
        whisper='It was almost like a polite ghost knocking for help.',
        tags={"ghost", "sound"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with a warm battery light",
        beam="made a round golden puddle on the floor",
        safe=True,
        makes_flame=False,
        tags={"lantern", "safe_light"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        beam="drew a bright path over the boards",
        safe=True,
        makes_flame=False,
        tags={"flashlight", "safe_light"},
    ),
    "glow_stick": Tool(
        id="glow_stick",
        label="glow stick",
        phrase="a green glow stick",
        beam="painted the dark with a soft green shine",
        safe=True,
        makes_flame=False,
        tags={"glow", "safe_light"},
    ),
    "candle": Tool(
        id="candle",
        label="candle",
        phrase="a real candle",
        beam="shook with a tiny living flame",
        safe=False,
        makes_flame=True,
        tags={"flame"},
    ),
}

NEEDS = {
    "cat": Need(
        id="cat",
        label="a hungry white cat",
        hint="a pale tail flicking behind a rice barrel",
        reveal="curled behind the rice barrel was a hungry white cat with one paw caught in a loop of string",
        consequence="The poor thing had been crying so softly that the house had turned its small sounds into a ghost story.",
        benefit="Feeding and freeing the cat was beneficial because the frightened animal could finally eat and rest.",
        tags={"cat", "animal"},
    ),
    "medicine": Need(
        id="medicine",
        label="grandpa's herb tin",
        hint="a silver tin shining under a low shelf",
        reveal="under the low shelf lay grandpa's herb tin, the one he needed for his sore throat tea",
        consequence="Without it, grandpa would have coughed all night and slept badly.",
        benefit="Finding the herb tin was beneficial because it helped grandpa get the tea that soothed his throat.",
        tags={"medicine", "helper"},
    ),
    "shutter": Need(
        id="shutter",
        label="a loose shoji shutter",
        hint="a screen edge lifting and tapping in the draft",
        reveal="one shoji shutter had come loose, and the wind was making it tap and bow like ghostly fingers",
        consequence="If nobody fixed it, the night air would keep blowing in and the paper would tear by morning.",
        benefit="Tying the shutter closed was beneficial because it kept the room warm and protected the paper screen.",
        tags={"house", "wind"},
    ),
}

RESPONSES = {
    "share_sushi": Response(
        id="share_sushi",
        sense=3,
        solves="cat",
        text="set one little piece of sushi on a dish, cut away the string, and waited while the cat ate in tiny grateful bites",
        qa_text="shared a little piece of sushi and freed the cat from the string",
        fail_text="offered sushi to the dark, but that would not fix the real problem",
        tags={"sushi", "animal"},
    ),
    "fetch_tin": Response(
        id="fetch_tin",
        sense=3,
        solves="medicine",
        text="picked up the silver herb tin and hurried it back to grandpa so warm tea could be made at once",
        qa_text="found the herb tin and brought it back to grandpa",
        fail_text="kept guessing about the ghost, but that would not help anyone who needed the herb tin",
        tags={"medicine", "help"},
    ),
    "tie_shutter": Response(
        id="tie_shutter",
        sense=3,
        solves="shutter",
        text="held the loose shutter steady while the helper tied it shut with a soft cord",
        qa_text="helped tie the loose shutter closed",
        fail_text="stared at the tapping screen, but that would not stop the draft",
        tags={"house", "repair"},
    ),
    "shout_at_ghost": Response(
        id="shout_at_ghost",
        sense=1,
        solves="none",
        text="shouted into the darkness",
        qa_text="shouted into the darkness",
        fail_text="shouted at the ghost, but noise was not a real fix",
        tags={"fear"},
    ),
}


def matching_responses(need_id: str) -> list[Response]:
    return [r for r in RESPONSES.values() if r.solves == need_id and r.sense >= SENSE_MIN]


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for need_id in sorted(place.affords):
            if not matching_responses(need_id):
                continue
            for tool in sensible_tools():
                combos.append((place_id, need_id, tool.id))
    return combos


@dataclass
class StoryParams:
    place: str
    need: str
    tool: str
    response: str
    omen: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    sushi_kind: str
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


GIRL_NAMES = ["Mina", "Aki", "Yuna", "Hana", "Sora", "Mei", "Nori", "Aya"]
BOY_NAMES = ["Ren", "Taro", "Kaito", "Haru", "Ken", "Daichi", "Riku", "Jun"]
TRAITS = ["curious", "careful", "patient", "bold", "thoughtful", "steady"]
SUSHI_KINDS = ["cucumber sushi", "egg sushi", "avocado sushi", "little seaweed sushi rolls"]


def helper_role(helper_type: str) -> str:
    return "adult" if helper_type in {"grandmother", "grandfather"} else "sibling"


def should_wait(helper_type: str, trait: str) -> bool:
    return helper_role(helper_type) == "adult" or trait in CALM_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "guided" if should_wait(params.helper_type, params.trait) else "startled"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return (
        f"(Refusing tool '{tool_id}': {tool.label} uses a real flame. "
        f"A gentle night quest here should use safe light like "
        f"{', '.join(sorted(t.id for t in sensible_tools()))}.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Pick a response that actually solves the hidden need.)"
    )


def explain_rejection(place_id: str, need_id: str) -> str:
    place = PLACES[place_id]
    need = NEEDS[need_id]
    return (
        f"(No story: {need.label} does not fit {place.label}. "
        f"Choose a need the place could honestly hide.)"
    )


def introduce(world: World, child: Entity, helper: Entity, place: Place, sushi_kind: str) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One moonlit evening, {child.id} was helping {helper.label_word} in {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"On the kitchen tray sat neat pieces of {sushi_kind}, shining softly with brushed soy and cucumber. "
        f"{child.id} thought they looked almost too pretty to eat."
    )


def rumor(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f'"Some houses keep their own stories," {helper.label_word.capitalize()} said as they worked. '
        f'"This one sometimes sounds like it remembers old footsteps."'
    )
    world.say(
        f"{child.id} glanced down {place.path} and felt a pleasant little shiver. "
        f"It was the sort of night that made curiosity sit up very straight."
    )


def omen_appears(world: World, child: Entity, omen: Omen) -> None:
    ghost = world.get("ghost")
    ghost.meters["guiding"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} saw {omen.text}. It {omen.motion}. {omen.whisper}"
    )


def warning(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"If we look, we look kindly and carefully," {helper.label_word} said, reaching for {tool.phrase}. '
        f'"A little light is beneficial. Running into the dark alone is not."'
    )


def sneak_ahead(world: World, child: Entity, tool: Tool) -> None:
    child.meters["walking_alone"] += 1
    child.meters["light"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"But curiosity tugged harder than patience. {child.id} took {tool.phrase} and padded ahead first. "
        f"The {tool.label} {tool.beam}."
    )
    propagate(world, narrate=True)


def wait_together(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.meters["light"] += 1
    child.memes["trust"] += 1
    world.facts["waited"] = True
    world.say(
        f"{child.id} slipped a small hand into {helper.label_word}'s hand instead. Together they took {tool.phrase}, "
        f"and the {tool.label} {tool.beam}."
    )
    propagate(world, narrate=False)


def call_back(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}?" {child.id} called in a smaller voice. '
        f'"Please come with me." {helper.label_word.capitalize()} came at once, calm and close.'
    )


def discover(world: World, need: Need) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At the end of the path, the light found {need.hint}. Then the dark opened its secret: {need.reveal}. "
        f"{need.consequence}"
    )


def solve(world: World, child: Entity, helper: Entity, response: Response, need: Need, sushi_kind: str) -> None:
    need_ent = world.get("need")
    need_ent.meters["help_given"] += 1
    propagate(world, narrate=False)
    if need.id == "cat":
        world.say(
            f"{helper.label_word.capitalize()} knelt quietly. {child.id} remembered the tray of {sushi_kind} and fetched one tiny piece. "
            f"Together they {response.text}."
        )
    elif need.id == "medicine":
        world.say(
            f'"So that is what our visitor wanted us to see," {helper.label_word} whispered. '
            f"Together they {response.text}."
        )
    else:
        world.say(
            f"{helper.label_word.capitalize()} smiled at the tapping screen, no longer fooled by it. "
            f"Together they {response.text}."
        )
    world.say(need.benefit)


def ghost_bows(world: World) -> None:
    ghost = world.get("ghost")
    if ghost.meters["peace"] >= THRESHOLD:
        world.say(
            "For one moment the pale sign returned, softer now, like a nod in the air. Then it thinned into moonlight and was gone."
        )


def lesson(world: World, child: Entity, helper: Entity) -> None:
    if world.facts["startled"]:
        first = (
            f"{child.id} leaned against {helper.label_word} and let out the breath "
            f"{child.pronoun()} had been holding."
        )
    else:
        first = (
            f"{child.id} looked down the now-quiet hall and felt brave in a steadier way than before."
        )
    world.say(first)
    world.say(
        f'"Curiosity can be a good lantern," {helper.label_word} said softly, '
        f'"but only when it walks with care. That is the lesson old houses like to teach."'
    )


def ending(world: World, place: Place, child: Entity, helper: Entity, sushi_kind: str, need: Need) -> None:
    if need.id == "cat":
        world.say(
            f"Later, they set the rest of the {sushi_kind} on the table for supper, and the white cat slept in a folded towel by the warm stove."
        )
    elif need.id == "medicine":
        world.say(
            f"Later, steam rose from grandpa's cup, and the room smelled sweet and green while the untouched {sushi_kind} waited for supper."
        )
    else:
        world.say(
            f"Later, the tied screen stayed still, the night air stayed outside, and the tray of {sushi_kind} sat safely on the table."
        )
    world.say(place.ending)


def tell(
    *,
    place: Place,
    omen: Omen,
    tool: Tool,
    need: Need,
    response: Response,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
    sushi_kind: str,
) -> World:
    world = World(place=place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type, role="helper"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the old ghost", role="ghost"))
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    need_ent = world.add(Entity(id="need", type="need", label=need.label, tags=set(need.tags)))

    child.attrs["name"] = child_name
    child.attrs["trait"] = trait
    helper.attrs["role"] = helper_role(helper_type)
    world.facts["sushi_kind"] = sushi_kind
    world.facts["child_name"] = child_name

    introduce(world, child, helper, place, sushi_kind)
    rumor(world, child, helper, place)

    world.para()
    omen_appears(world, child, omen)
    warning(world, child, helper, tool)

    if should_wait(helper_type, trait):
        world.facts["outcome"] = "guided"
        wait_together(world, child, helper, tool)
    else:
        world.facts["outcome"] = "startled"
        sneak_ahead(world, child, tool)
        call_back(world, child, helper)

    world.para()
    discover(world, need)
    solve(world, child, helper, response, need, sushi_kind)
    ghost_bows(world)

    world.para()
    lesson(world, child, helper)
    ending(world, place, child, helper, sushi_kind, need)

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        place_cfg=place,
        place=place_ent,
        omen=omen,
        tool=tool,
        need_cfg=need,
        need=need_ent,
        response=response,
        solved=need_ent.meters["solved"] >= THRESHOLD,
        problem_found=need_ent.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with spooky sounds, shadows, or spirits. It can feel chilly and mysterious even when nothing truly mean is there."
        )
    ],
    "sushi": [
        (
            "What is sushi?",
            "Sushi is a food often made with rice and other ingredients rolled or shaped together. Some kinds have vegetables or egg, and some use seaweed around the rice."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light in the dark so you can see where you are going. A battery lantern is especially useful because it shines without a flame."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small electric light you can carry in your hand. It helps people look carefully in dark places."
        )
    ],
    "glow": [
        (
            "What is a glow stick?",
            "A glow stick is a small plastic stick that gives off soft light after you bend it. It is cool to the touch and useful in the dark."
        )
    ],
    "animal": [
        (
            "Why should you move gently around a scared animal?",
            "A scared animal may hide, scratch, or run if people rush at it. Quiet voices and gentle hands help it feel safer."
        )
    ],
    "medicine": [
        (
            "Why is medicine or an herb remedy important when someone is sick?",
            "Medicine or a soothing remedy can help a sore body feel better. Finding it quickly can make rest easier."
        )
    ],
    "house": [
        (
            "Why should a loose window or screen be fixed?",
            "A loose screen can flap, tear, and let cold air inside. Fixing it keeps the room calmer and protects the house."
        )
    ],
    "safe_light": [
        (
            "Why is safe light better than a candle for a night search?",
            "Safe light lets you see without carrying a real flame. That is better indoors because it lowers the chance of burning something by accident."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "sushi", "lantern", "flashlight", "glow", "animal", "medicine", "house", "safe_light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    need = f["need_cfg"]
    omen = f["omen"]
    tool = f["tool"]
    if f["outcome"] == "guided":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "beneficial" and "sushi".',
            f"Tell a moonlit quest where {child.attrs['name']} sees {omen.text}, stays with {helper.label_word}, and discovers {need.label}.",
            f"Write a story about curiosity that becomes beneficial because a child uses {tool.label} and asks a trusted helper to come along.",
        ]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "beneficial" and "sushi".',
        f"Tell a spooky-but-kind quest where {child.attrs['name']} starts after {omen.text} alone, gets frightened, and then calls {helper.label_word} for help.",
        f"Write a story with a lesson learned: curiosity can begin a quest, but care and company are what make the ending beneficial.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    need = f["need_cfg"]
    tool = f["tool"]
    omen = f["omen"]
    response = f["response"]
    sushi_kind = f["sushi_kind"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']}, {helper.label_word}, and a gentle ghostly sign in {f['place_cfg'].label}. The story follows their night quest from mystery to understanding."
        ),
        (
            "What started the quest?",
            f"The quest began when {child.attrs['name']} saw {omen.text} near a tray of {sushi_kind}. That strange sign made curiosity feel stronger than the ordinary quiet of the house."
        ),
    ]

    if f["outcome"] == "guided":
        qa.append(
            (
                f"Why did {child.attrs['name']} stay with {helper.label_word}?",
                f"{child.attrs['name']} listened when {helper.label_word} said light and care were beneficial. Because they walked together with {tool.phrase}, the dark felt less frightening and they could notice the real clue."
            )
        )
    else:
        qa.append(
            (
                f"Why did {child.attrs['name']} call {helper.label_word} back?",
                f"{child.attrs['name']} went ahead because curiosity pulled hard, but the dark suddenly felt much bigger. Calling {helper.label_word} back helped turn a frightened moment into a safer quest."
            )
        )

    qa.append(
        (
            "What was the ghost trying to show them?",
            f"The ghost was trying to show them {need.label}. It was not leading them to trouble at all; it was pointing toward something that needed help."
        )
    )
    qa.append(
        (
            "How did they solve the problem?",
            f"They {response.qa_text}. That solved the hidden need and proved the ghost's guidance was beneficial instead of harmful."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.attrs['name']} learned that curiosity can begin a quest, but it should walk beside care. The story ends happily because the child shared the mystery with {helper.label_word} instead of treating the night like a game to rush through alone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "sushi", "safe_light"}
    tags |= set(world.facts["tool"].tags)
    tags |= set(world.facts["need_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} solved={world.facts.get('solved')} found={world.facts.get('problem_found')}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="inn",
        need="cat",
        tool="lantern",
        response="share_sushi",
        omen="lantern",
        child_name="Mina",
        child_gender="girl",
        helper_type="grandmother",
        trait="careful",
        sushi_kind="cucumber sushi",
    ),
    StoryParams(
        place="temple",
        need="shutter",
        tool="flashlight",
        response="tie_shutter",
        omen="tapping",
        child_name="Ren",
        child_gender="boy",
        helper_type="grandfather",
        trait="patient",
        sushi_kind="egg sushi",
    ),
    StoryParams(
        place="teahouse",
        need="medicine",
        tool="glow_stick",
        response="fetch_tin",
        omen="whisper",
        child_name="Hana",
        child_gender="girl",
        helper_type="sister",
        trait="bold",
        sushi_kind="little seaweed sushi rolls",
    ),
    StoryParams(
        place="inn",
        need="medicine",
        tool="flashlight",
        response="fetch_tin",
        omen="lantern",
        child_name="Kaito",
        child_gender="boy",
        helper_type="sister",
        trait="thoughtful",
        sushi_kind="avocado sushi",
    ),
]


ASP_RULES = r"""
% --- gate ---------------------------------------------------------------
valid(P,N,T) :- place(P), affords(P,N), safe_tool(T), has_response(N).
sensible_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
matches(N,R) :- sensible_response(R), solves(R,N).
has_response(N) :- matches(N,_).

% --- outcome model ------------------------------------------------------
guided :- helper_kind(adult).
guided :- trait(T), calm_trait(T).
startled :- not guided.

outcome(guided) :- guided.
outcome(startled) :- startled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for need_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, need_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.safe:
            lines.append(asp.fact("safe_tool", tool_id))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("solves", rid, response.solves))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_responses() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("helper_kind", helper_role(params.helper_type)),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost story world: curiosity, a moonlit quest, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--helper", choices=["grandmother", "grandfather", "sister", "brother"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--sushi-kind", choices=SUSHI_KINDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not TOOLS[args.tool].safe:
        raise StoryError(explain_tool(args.tool))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.place and args.need and args.need not in PLACES[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.need))
    if args.need and args.response and RESPONSES[args.response].solves != args.need:
        raise StoryError("(No story: that response does not solve the chosen hidden need.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.need is None or combo[1] == args.need)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, need_id, tool_id = rng.choice(sorted(combos))
    responses = [r.id for r in matching_responses(need_id) if args.response is None or r.id == args.response]
    if not responses:
        raise StoryError("(No valid response matches the chosen need.)")

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    helper_type = args.helper or rng.choice(["grandmother", "grandfather", "sister", "brother"])
    trait = args.trait or rng.choice(TRAITS)
    omen = args.omen or rng.choice(sorted(OMENS))
    sushi_kind = args.sushi_kind or rng.choice(SUSHI_KINDS)

    return StoryParams(
        place=place_id,
        need=need_id,
        tool=tool_id,
        response=rng.choice(sorted(responses)),
        omen=omen,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
        sushi_kind=sushi_kind,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.need not in NEEDS:
        raise StoryError(f"Unknown need: {params.need}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.omen not in OMENS:
        raise StoryError(f"Unknown omen: {params.omen}")
    if params.tool not in {t.id for t in sensible_tools()}:
        raise StoryError(explain_tool(params.tool))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.need not in PLACES[params.place].affords:
        raise StoryError(explain_rejection(params.place, params.need))
    if RESPONSES[params.response].solves != params.need:
        raise StoryError("(No story: the response does not solve the chosen hidden need.)")

    world = tell(
        place=PLACES[params.place],
        omen=OMENS[params.omen],
        tool=TOOLS[params.tool],
        need=NEEDS[params.need],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
        sushi_kind=params.sushi_kind,
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

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))

    py_sens = {r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN}
    cl_sens = set(asp_sensible_responses())
    if py_sens == cl_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(py_sens))
        print("  clingo:", sorted(cl_sens))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome calculations differ.")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_response/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, need, tool) combos:\n")
        for place_id, need_id, tool_id in combos:
            print(f"  {place_id:8} {need_id:9} {tool_id}")
        print(f"\nsensible responses: {', '.join(asp_sensible_responses())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.need} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
