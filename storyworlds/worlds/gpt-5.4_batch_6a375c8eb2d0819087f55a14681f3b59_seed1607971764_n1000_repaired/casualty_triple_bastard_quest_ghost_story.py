#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py
=======================================================================

A small ghost-story storyworld about a child who goes on a nighttime quest to
return an old stray key and comfort a gentle ghost.

This world always includes the seed words:
- casualty
- triple
- bastard

The words are used as story facts, not random garnish:
- the ghost was the only casualty of an old accident,
- the child follows a triple sign through the haunted place,
- an old diary calls the lost key "the bastard key," meaning a stray key with no ring.

Run it
------
    python storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py
    python storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py --place chapel
    python storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py --hesitate 2 --qa
    python storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/casualty_triple_bastard_quest_ghost_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
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
    ghost_name: str
    ghost_role: str
    casualty_event: str
    clue_sound: str
    clue_line: str
    hidden_spot: str
    spot_type: str
    rest_spot: str
    warm_image: str
    tags: set[str] = field(default_factory=set)
    spook: int = 4
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
    action: str
    reaches: set[str] = field(default_factory=set)
    steadiness: int = 1
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
class ElderType:
    id: str
    type: str
    calm: int
    intro: str
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
class ChildTrait:
    id: str
    courage: int
    line: str
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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    ghost = world.get("ghost")
    hero = world.get("hero")
    if ghost.meters["unsettled"] >= THRESHOLD and ("haunt",) not in world.fired:
        world.fired.add(("haunt",))
        room.meters["cold"] += 1
        hero.memes["fear"] += 1
        out.append("__cold__")
    return out


def _r_found_key(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    key = world.get("key")
    if key.meters["found"] >= THRESHOLD and ("found",) not in world.fired:
        world.fired.add(("found",))
        hero.memes["hope"] += 1
        out.append("__found__")
    return out


def _r_returned_key(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    ghost = world.get("ghost")
    hero = world.get("hero")
    key = world.get("key")
    if key.meters["returned"] >= THRESHOLD and ("returned",) not in world.fired:
        world.fired.add(("returned",))
        ghost.meters["hope"] += 1
        room.meters["cold"] = 0.0
        hero.memes["relief"] += 1
        out.append("__returned__")
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    hero = world.get("hero")
    if ghost.meters["named"] >= THRESHOLD and ghost.meters["hope"] >= THRESHOLD and ("release",) not in world.fired:
        world.fired.add(("release",))
        ghost.meters["peace"] += 1
        ghost.meters["unsettled"] = 0.0
        hero.memes["wonder"] += 1
        out.append("__release__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="physical", apply=_r_haunt),
    Rule(name="found_key", tag="quest", apply=_r_found_key),
    Rule(name="returned_key", tag="quest", apply=_r_returned_key),
    Rule(name="release", tag="social", apply=_r_release),
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


PLACES = {
    "lighthouse": Place(
        id="lighthouse",
        label="Bramble Lighthouse",
        ghost_name="Mara",
        ghost_role="keeper's daughter",
        casualty_event="the storm",
        clue_sound="a triple bell high above them",
        clue_line="three little bell-notes rang where no wind could reach",
        hidden_spot="under a loose stair board on the spiral steps",
        spot_type="floorboard",
        rest_spot="the little brass box beside the lamp ledger",
        warm_image="the lamp glass turned honey-gold, and the sea below stopped sounding lonely",
        tags={"lighthouse", "storm", "ghost"},
        spook=5,
    ),
    "manor": Place(
        id="manor",
        label="Hollowfen Manor",
        ghost_name="Edwin",
        ghost_role="page boy",
        casualty_event="the fire",
        clue_sound="a triple knock from behind the pantry wall",
        clue_line="three soft knocks tapped from the cold bricks",
        hidden_spot="behind the iron grate of the old pantry hearth",
        spot_type="grate",
        rest_spot="the music box on the nursery shelf",
        warm_image="the music box gave one sweet note, and the dark hall seemed to breathe out",
        tags={"manor", "fire", "ghost"},
        spook=4,
    ),
    "chapel": Place(
        id="chapel",
        label="Mothglass Chapel",
        ghost_name="Clara",
        ghost_role="choir child",
        casualty_event="the flood",
        clue_sound="a triple tap along the hanging bell rope",
        clue_line="three tiny taps shivered down the rope like raindrops",
        hidden_spot="inside a swallow's nest above the rafters",
        spot_type="rafters",
        rest_spot="the hymn box under the last pew",
        warm_image="the candles stood straight and calm, and pale moonlight spread over the pews like a blanket",
        tags={"chapel", "flood", "ghost"},
        spook=3,
    ),
}

TOOLS = {
    "ruler": Tool(
        id="ruler",
        label="a flat wooden ruler",
        action="slid the ruler under the board and lifted it just enough to reach inside",
        reaches={"floorboard"},
        steadiness=1,
        tags={"ruler", "tool"},
    ),
    "magnet": Tool(
        id="magnet",
        label="a string with a little magnet tied at the end",
        action="lowered the magnet through the bars and drew something metal out of the ash-dark gap",
        reaches={"grate"},
        steadiness=2,
        tags={"magnet", "tool"},
    ),
    "crook": Tool(
        id="crook",
        label="a walking stick with a bent handle",
        action="hooked the nest very gently and tipped something bright into a folded handkerchief",
        reaches={"rafters"},
        steadiness=1,
        tags={"walking_stick", "tool"},
    ),
    "spoon": Tool(
        id="spoon",
        label="a long wooden spoon",
        action="worked the spoon's handle into the crack and nudged the board open with both hands",
        reaches={"floorboard"},
        steadiness=0,
        tags={"spoon", "tool"},
    ),
}

ELDERS = {
    "grandmother": ElderType(
        id="grandmother",
        type="grandmother",
        calm=2,
        intro="believed old houses remembered things",
        tags={"grandma"},
    ),
    "grandfather": ElderType(
        id="grandfather",
        type="grandfather",
        calm=2,
        intro="never laughed at a frightened whisper",
        tags={"grandpa"},
    ),
    "aunt": ElderType(
        id="aunt",
        type="aunt",
        calm=1,
        intro="carried stories the way other people carried umbrellas",
        tags={"aunt"},
    ),
}

TRAITS = {
    "timid": ChildTrait(
        id="timid",
        courage=2,
        line="had a soft voice and a brave heart that needed a moment to wake up",
        tags={"timid"},
    ),
    "careful": ChildTrait(
        id="careful",
        courage=3,
        line="liked to look twice before stepping into the dark",
        tags={"careful"},
    ),
    "gentle": ChildTrait(
        id="gentle",
        courage=3,
        line="was the sort of child who listened even to quiet things",
        tags={"gentle"},
    ),
    "steady": ChildTrait(
        id="steady",
        courage=4,
        line="could keep both hands still even when a room felt strange",
        tags={"steady"},
    ),
    "bold": ChildTrait(
        id="bold",
        courage=4,
        line="walked forward first and shivered later",
        tags={"bold"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Elsie", "Ada", "June", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Miles", "Theo", "Jude", "Eli", "Noah", "Finn", "Hugo"]

KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale about a spirit or a strange haunting. It can feel spooky, but in gentle stories the ghost often wants help, not harm.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special trip with a clear goal, like finding something lost or helping someone in trouble. A quest feels important because each step leads toward the answer.",
        )
    ],
    "lighthouse": [
        (
            "What does a lighthouse do?",
            "A lighthouse shines a strong light near the sea so boats can find their way. It helps sailors stay safe in fog and darkness.",
        )
    ],
    "chapel": [
        (
            "What is a chapel?",
            "A chapel is a small building used for quiet prayer or singing. Chapels often feel still because people go there to whisper and listen.",
        )
    ],
    "manor": [
        (
            "What is a manor?",
            "A manor is a large old house. In stories, old houses can feel mysterious because they hold many rooms and many memories.",
        )
    ],
    "storm": [
        (
            "What is a storm casualty?",
            "A casualty is someone harmed or lost in an accident or disaster. In this story world, the word means a sad loss from long ago, not something happening now.",
        )
    ],
    "fire": [
        (
            "Why does an old fire leave strong memories?",
            "A fire changes a place very quickly, so people remember the sounds and smells for a long time. That is why old fire stories can feel haunting.",
        )
    ],
    "flood": [
        (
            "What does a flood do?",
            "A flood is water rising where it should not be, covering land or buildings. Fast water can carry things away and make a place feel changed afterward.",
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key is used to open a lock. In stories, a lost key can also stand for a memory or a secret waiting to be found.",
        )
    ],
    "echo": [
        (
            "Why do old rooms echo?",
            "Sound bounces off hard walls, floors, and ceilings, then comes back to your ears. In an empty old room, that can make even tiny noises sound bigger and stranger.",
        )
    ],
}


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for tool_id, tool in TOOLS.items():
            if place.spot_type in tool.reaches:
                combos.append((place_id, tool_id))
    return combos


def outcome_score(place: Place, tool: Tool, elder: ElderType, trait: ChildTrait, hesitate: int) -> int:
    return trait.courage + elder.calm + tool.steadiness - hesitate - place.spook


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    elder = ELDERS[params.elder]
    trait = TRAITS[params.trait]
    return "released" if outcome_score(place, tool, elder, trait, params.hesitate) >= 0 else "visited"


def explain_rejection(place: Place, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot reach {place.hidden_spot}. "
        f"The quest only works when the tool can honestly retrieve the key.)"
    )


@dataclass
class StoryParams:
    place: str
    tool: str
    elder: str
    trait: str
    name: str
    gender: str
    hesitate: int = 0
    seed: Optional[int] = None
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


def enter_haunting(world: World, place: Place, hero: Entity, elder: Entity) -> None:
    world.say(
        f"They crossed the threshold of {place.label}, and at once the air turned colder. "
        f"{hero.id} heard {place.clue_sound}, though the place around them looked still."
    )
    world.say(
        f"{elder.label_word.capitalize()} squeezed {hero.pronoun('possessive')} hand and did not pull away."
    )
    propagate(world, narrate=False)


def introduce(world: World, hero: Entity, elder: Entity, trait: ChildTrait, place: Place) -> None:
    world.say(
        f"On a misty evening, {hero.id} went with {hero.pronoun('possessive')} {elder.label_word} to the hill above the village. "
        f"{hero.id} {trait.line}."
    )
    world.say(
        f"{elder.label_word.capitalize()} {ELDERS[elder.type].intro}, and that was why the two of them stopped when {place.label} gave a lonely sigh in the dark."
    )


def diary_clue(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    ghost = world.get("ghost")
    world.say(
        f"In a drawer by the door, they found a thin old diary. One page said that {ghost.attrs['name']} the {place.ghost_role} had been the only casualty of {place.casualty_event}."
    )
    world.say(
        f"Another page, written in hurried ink, said, 'Follow the triple sound. Find the bastard key.' "
        f"{elder.label_word.capitalize()} traced the line with one finger and explained that here bastard meant a stray key with no ring and no home."
    )
    world.say(
        f'"Then that is our quest," {hero.id} whispered. "We have to take it home."'
    )


def follow_clue(world: World, hero: Entity, place: Place) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"They listened again, and {place.clue_line}. {hero.id} followed the sound through dust and shadows until it pointed straight at {place.hidden_spot}."
    )


def show_fear(world: World, hero: Entity, hesitate: int) -> None:
    if hesitate <= 0:
        return
    if hesitate == 1:
        world.say(
            f"{hero.id} stopped for one small breath. The dark felt deep enough to hide a whole winter."
        )
    else:
        world.say(
            f"{hero.id} almost turned back. The cold pressed close, and even the floorboards seemed to listen."
        )
    hero.memes["fear"] += float(hesitate)


def retrieve_key(world: World, hero: Entity, tool: Tool, place: Place) -> None:
    key = world.get("key")
    world.say(
        f"Using {tool.label}, {hero.id} {tool.action}. Out came a brass key with no ribbon and no ring, green at the teeth and bright at the tip."
    )
    key.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"The bastard key," {hero.id} said softly, but now the words did not sound rude. They sounded lonely.'
    )


def return_key(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    key = world.get("key")
    world.say(
        f"Together they carried the key to {place.rest_spot}. When {hero.id} laid it there, the cold in the room loosened like a knot coming undone."
    )
    key.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A pale child-shape gathered by the far wall, not sharp and dreadful, but thin as breath on glass."
    )


def speak_name(world: World, hero: Entity, place: Place) -> None:
    ghost = world.get("ghost")
    world.say(
        f'{hero.id} lifted {hero.pronoun("possessive")} chin and said, "{place.ghost_name}, your key is home."'
    )
    ghost.meters["named"] += 1
    propagate(world, narrate=False)


def hush_name(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f'{hero.id} tried to say the name waiting in the diary, but the last part of it faded into a whisper.'
    )
    world.say(
        f"Still, {hero.pronoun().capitalize()} kept the key in its place and did not run."
    )


def released_ending(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    ghost = world.get("ghost")
    hero.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"The ghost-child smiled at them. For one blink, {ghost.attrs['name']} looked solid enough to be only a child again, glad and surprised to be remembered."
    )
    world.say(
        f"Then {place.warm_image}. Where the ghost had been, there was only calm space and the gentle sense that the house could sleep at last."
    )
    world.say(
        f"As they walked home, {hero.id} did not keep looking over {hero.pronoun('possessive')} shoulder. The quest was over, and the night no longer felt hungry."
    )


def visited_ending(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"The ghost-child did not vanish, but the sorrow went out of {world.get('ghost').pronoun('possessive')} face. Instead of crying, the spirit gave {hero.id} a small thankful nod."
    )
    world.say(
        f"{place.warm_image}. The haunting was gentler now, as if the house had stopped asking for help and had begun only to wait."
    )
    world.say(
        f'"Next time I will say it louder," {hero.id} promised on the walk home. {elder.label_word.capitalize()} nodded, and the promise itself felt like a little lantern between them.'
    )


def tell(
    place: Place,
    tool: Tool,
    elder_cfg: ElderType,
    trait_cfg: ChildTrait,
    name: str = "Lila",
    gender: str = "girl",
    hesitate: int = 0,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            label=name,
            attrs={"trait": trait_cfg.id},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_cfg.type,
            role="elder",
            label="the elder",
            attrs={"calm": elder_cfg.calm},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
            attrs={"name": place.ghost_name, "role_name": place.ghost_role},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=place.label,
        )
    )
    key = world.add(
        Entity(
            id="key",
            kind="thing",
            type="key",
            label="the key",
            tags={"key"},
        )
    )

    hero.memes["fear"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["wonder"] = 0.0
    elder.memes["relief"] = 0.0
    room.meters["cold"] = 0.0
    ghost.meters["unsettled"] = 1.0
    ghost.meters["hope"] = 0.0
    ghost.meters["named"] = 0.0
    ghost.meters["peace"] = 0.0
    key.meters["found"] = 0.0
    key.meters["returned"] = 0.0

    world.facts.update(
        place=place,
        tool=tool,
        elder_cfg=elder_cfg,
        trait_cfg=trait_cfg,
        hesitate=hesitate,
        predicted_release=(outcome_score(place, tool, elder_cfg, trait_cfg, hesitate) >= 0),
    )

    introduce(world, hero, elder, trait_cfg, place)
    diary_clue(world, hero, elder, place)

    world.para()
    enter_haunting(world, place, hero, elder)
    show_fear(world, hero, hesitate)
    follow_clue(world, hero, place)

    world.para()
    retrieve_key(world, hero, tool, place)
    return_key(world, hero, elder, place)

    released = outcome_score(place, tool, elder_cfg, trait_cfg, hesitate) >= 0
    world.para()
    if released:
        speak_name(world, hero, place)
        released_ending(world, hero, elder, place)
        outcome = "released"
    else:
        hush_name(world, hero, place)
        visited_ending(world, hero, elder, place)
        outcome = "visited"

    world.facts.update(
        hero=hero,
        elder=elder,
        ghost=ghost,
        room=room,
        key=key,
        released=released,
        outcome=outcome,
        clue=place.clue_sound,
        quest_item="the bastard key",
        casualty=f"{place.ghost_name} was the only casualty of {place.casualty_event}",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    if outcome == "released":
        ending = "the ghost is finally laid to rest"
    else:
        ending = "the haunting softens, though the ghost still lingers kindly"
    return [
        (
            f'Write a gentle ghost story for a 3-to-5-year-old about a child named {hero.id} who goes on a quest in {place.label}. '
            f'Include the exact words "casualty," "triple," and "bastard."'
        ),
        (
            f"Tell a spooky-but-tender story where an old diary mentions a casualty, a triple sound leads the way, "
            f"and a lost bastard key must be returned home so {ending}."
        ),
        (
            f"Write a child-facing quest story in a ghost-story style: a brave child follows a triple clue through an old place, "
            f"learns why a ghost is sad, and ends by changing the feeling of the house."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    place = world.facts["place"]
    tool = world.facts["tool"]
    outcome = world.facts["outcome"]
    ghost = world.facts["ghost"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} {elder.label_word}, and the ghost of {place.ghost_name} in {place.label}. "
            f"The story follows them through a nighttime quest to help the ghost.",
        ),
        (
            "What did the diary say?",
            f"The diary said that {place.ghost_name} was the only casualty of {place.casualty_event}, and it told them to follow the triple sound and find the bastard key. "
            f"Those clues gave the child a clear reason to begin the quest.",
        ),
        (
            "How did they find the key?",
            f"They listened for {place.clue_sound} and followed it to {place.hidden_spot}. "
            f"Then {hero.id} used {tool.label} to reach the hiding place and pull the lost key out.",
        ),
        (
            "Why was the key called the bastard key?",
            f"In the old diary, bastard meant the key was stray and had no ring or home. "
            f"That made the word sad instead of mean, because the key had been left alone just like the ghost's memory had been left alone.",
        ),
        (
            "What changed when the key was returned?",
            f"When {hero.id} placed the key in {place.rest_spot}, the cold feeling in the room eased at once. "
            f"Returning the key showed the ghost that someone had finally finished the unfinished task.",
        ),
    ]
    if outcome == "released":
        qa.append(
            (
                f"Why was the ghost able to rest at the end?",
                f"The ghost could rest because {hero.id} returned the key and spoke {place.ghost_name}'s name aloud. "
                f"That gave the ghost both the lost object and the feeling of being remembered, so the haunting ended.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the ghost stay, even after the key was returned?",
                f"The key went home, so the ghost stopped looking sorrowful, but {hero.id} was still too frightened to say the full name aloud. "
                f"Because of that, the haunting softened instead of ending all the way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    tags = {"ghost", "quest", "key", "echo"}
    if "lighthouse" in place.tags:
        tags.add("lighthouse")
        tags.add("storm")
    if "manor" in place.tags:
        tags.add("manor")
        tags.add("fire")
    if "chapel" in place.tags:
        tags.add("chapel")
        tags.add("flood")
    out: list[tuple[str, str]] = []
    order = ["ghost", "quest", "key", "echo", "lighthouse", "manor", "chapel", "storm", "fire", "flood"]
    for tag in order:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T) :- place(P), tool(T), hidden_type(P,S), reaches(T,S).

score(C + K + St - H - Sp) :-
    chosen_place(P), chosen_tool(T), chosen_elder(E), chosen_trait(R), hesitate(H),
    calm(E, K), courage(R, C), steadiness(T, St), spook(P, Sp).

released :- score(S), S >= 0.
outcome(released) :- released.
outcome(visited) :- not released.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("hidden_type", place_id, place.spot_type))
        lines.append(asp.fact("spook", place_id, place.spook))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("steadiness", tool_id, tool.steadiness))
        for spot in sorted(tool.reaches):
            lines.append(asp.fact("reaches", tool_id, spot))
    for elder_id, elder in ELDERS.items():
        lines.append(asp.fact("elder", elder_id))
        lines.append(asp.fact("calm", elder_id, elder.calm))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("courage", trait_id, trait.courage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_elder", params.elder),
            asp.fact("chosen_trait", params.trait),
            asp.fact("hesitate", params.hesitate),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        place="lighthouse",
        tool="ruler",
        elder="grandmother",
        trait="bold",
        name="Lila",
        gender="girl",
        hesitate=0,
    ),
    StoryParams(
        place="manor",
        tool="magnet",
        elder="aunt",
        trait="careful",
        name="Owen",
        gender="boy",
        hesitate=1,
    ),
    StoryParams(
        place="chapel",
        tool="crook",
        elder="grandfather",
        trait="timid",
        name="Mina",
        gender="girl",
        hesitate=2,
    ),
    StoryParams(
        place="lighthouse",
        tool="spoon",
        elder="aunt",
        trait="gentle",
        name="Theo",
        gender="boy",
        hesitate=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child goes on a ghostly quest to return a lost key."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--hesitate", type=int, choices=[0, 1, 2], help="how much the child falters before speaking the ghost's name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, tool) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.tool:
        place = PLACES[args.place]
        tool = TOOLS[args.tool]
        if (args.place, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(place, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_id = args.elder or rng.choice(sorted(ELDERS))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    hesitate = args.hesitate if args.hesitate is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        tool=tool_id,
        elder=elder_id,
        trait=trait_id,
        name=name,
        gender=gender,
        hesitate=hesitate,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if (params.place, params.tool) not in valid_combos():
        raise StoryError(explain_rejection(PLACES[params.place], TOOLS[params.tool]))
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.hesitate not in {0, 1, 2}:
        raise StoryError(f"(Invalid hesitate value: {params.hesitate})")

    world = tell(
        place=PLACES[params.place],
        tool=TOOLS[params.tool],
        elder_cfg=ELDERS[params.elder],
        trait_cfg=TRAITS[params.trait],
        name=params.name,
        gender=params.gender,
        hesitate=params.hesitate,
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

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {s}")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("smoke test produced incomplete output")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tool) pairs:\n")
        for place_id, tool_id in combos:
            print(f"  {place_id:10} {tool_id}")
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
            header = f"### {p.name}: {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
