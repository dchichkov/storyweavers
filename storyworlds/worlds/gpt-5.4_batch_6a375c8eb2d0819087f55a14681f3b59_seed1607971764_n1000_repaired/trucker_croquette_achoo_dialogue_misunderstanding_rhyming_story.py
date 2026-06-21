#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py
================================================================================================

A small standalone storyworld about a hungry trucker, a sneeze, a croquette,
and a silly misunderstanding in a roadside café. The story is told in a gentle
rhyming style and driven by simulated state: hunger, confusion, relief, and the
physical cues that help the characters understand one another.

Run it
------
    python storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py --place diner --sneeze flour_achoo --method point_menu
    python storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py --method shout_again
    python storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/trucker_croquette_achoo_dialogue_misunderstanding_rhyming_story.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "woman", "mother", "server_f", "cook_f"}
        male = {"boy", "man", "father", "trucker", "server_m", "cook_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    menu_surface: str
    serves_croquette: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Sneeze:
    id: str
    cue: str
    heard_as: str
    confusion: int
    flourish: str
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
    sense: int
    clarity: int
    needs: set[str]
    line: str
    success: str
    fallback: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_request_obscured(world: World) -> list[str]:
    out: list[str] = []
    trucker = world.get("trucker")
    listener = world.get("listener")
    sneeze = world.facts["sneeze"]
    if trucker.meters["asked"] < THRESHOLD:
        return out
    sig = ("obscured", sneeze.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.meters["confused"] += float(sneeze.confusion)
    trucker.memes["embarrassed"] += 1
    out.append("__misheard__")
    return out


def _r_confused_listener(world: World) -> list[str]:
    out: list[str] = []
    listener = world.get("listener")
    if listener.meters["confused"] < THRESHOLD:
        return out
    sig = ("wrong_guess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.meters["wrong_guess"] += 1
    out.append("__wrong_guess__")
    return out


def _r_clear_understanding(world: World) -> list[str]:
    out: list[str] = []
    listener = world.get("listener")
    trucker = world.get("trucker")
    if world.facts.get("clarity_used", 0) <= listener.meters["confused"]:
        return out
    sig = ("understood",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.meters["understood"] += 1
    listener.meters["confused"] = 0.0
    trucker.meters["order_taken"] += 1
    trucker.memes["relief"] += 1
    listener.memes["relief"] += 1
    out.append("__understood__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="request_obscured", tag="social", apply=_r_request_obscured),
    Rule(name="confused_listener", tag="social", apply=_r_confused_listener),
    Rule(name="clear_understanding", tag="social", apply=_r_clear_understanding),
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


def valid_combo(place: Place, method: Method) -> bool:
    return place.serves_croquette and method.sense >= SENSE_MIN and method.needs.issubset(place.affordances)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for method_id, method in METHODS.items():
            if valid_combo(place, method):
                combos.append((place_id, method_id))
    return combos


def predict_understanding(world: World, method: Method) -> dict:
    sim = world.copy()
    sim.facts["clarity_used"] = method.clarity
    propagate(sim, narrate=False)
    listener = sim.get("listener")
    return {
        "understood": listener.meters["understood"] >= THRESHOLD,
        "remaining_confusion": listener.meters["confused"],
    }


def is_quick_fix(sneeze: Sneeze, method: Method) -> bool:
    return method.clarity > sneeze.confusion


def introduce(world: World, trucker: Entity, listener: Entity, place: Place) -> None:
    trucker.meters["hunger"] = 2.0
    trucker.memes["hope"] += 1
    world.say(
        f"Past puddles and pines rolled a trucker named {trucker.id}, humming a road-song low. "
        f"At {place.label}, where lamps made a buttery glow, {trucker.pronoun('subject')} parked by the window with nowhere else to go."
    )
    world.say(
        f"Inside stood {listener.id}, kind-eyed and quick, keeping cups in a neat little row. "
        f"The room smelled warm and peppery-sweet, like supper saying, \"Come in from the snow,\" though no snow fell there below."
    )


def spot_food(world: World, trucker: Entity) -> None:
    trucker.memes["appetite"] += 1
    world.say(
        f"Then {trucker.pronoun('subject')} saw a golden croquette on the board and whispered, "
        f"\"That crunchy round treat is just right for my trip.\" "
        f"{trucker.pronoun('possessive').capitalize()} hungry tummy gave a hopeful flip."
    )


def ask_and_sneeze(world: World, trucker: Entity, listener: Entity, sneeze: Sneeze) -> None:
    trucker.meters["asked"] += 1
    world.facts["asked_food"] = "croquette"
    world.say(
        f'"May I have a croquette?" asked {trucker.id}. But just then came {sneeze.cue} -- "{sneeze.cue}!" -- '
        f"and the word skipped sideways with a comic slip."
    )
    world.say(sneeze.flourish)
    propagate(world, narrate=False)
    if listener.meters["wrong_guess"] >= THRESHOLD:
        world.say(
            f'"A {sneeze.heard_as}?" said {listener.id}. "{sneeze.heard_as.capitalize()} it is, I think!" '
            f"{listener.pronoun('subject').capitalize()} reached the wrong way with a puzzled blink."
        )


def react_to_mixup(world: World, trucker: Entity, listener: Entity, sneeze: Sneeze) -> None:
    trucker.memes["confusion"] += 1
    listener.memes["worry"] += 1
    world.say(
        f'"No, no," said {trucker.id}, then stopped with a sheepish smile. '
        f'"I said croquette, but my achoo made the sound run wild."'
    )
    world.say(
        f"{listener.id} tilted {listener.pronoun('possessive')} head for a little while. "
        f"The misunderstanding made the air feel knotted, though nobody meant to be beguiled."
    )


def try_method(world: World, trucker: Entity, listener: Entity, method: Method) -> None:
    world.facts["clarity_used"] = method.clarity
    trucker.memes["patience"] += 1
    world.say(method.line.format(trucker=trucker.id, listener=listener.id, surface=world.place.menu_surface))
    propagate(world, narrate=False)


def quick_resolution(world: World, trucker: Entity, listener: Entity, method: Method) -> None:
    trucker.meters["served"] += 1
    trucker.meters["hunger"] = 0.0
    trucker.memes["joy"] += 1
    listener.memes["joy"] += 1
    world.say(
        method.success.format(trucker=trucker.id, listener=listener.id)
    )
    world.say(
        f'Soon a crisp croquette arrived on a plate with a curl of steam and a savory scent. '
        f'"Now I understand," said {listener.id}. "{trucker.id}, that is what you meant."'
    )
    world.say(
        f"{trucker.id} laughed, and the rhyme of the room turned bright instead of bent. "
        f"Crunch by crunch, the meal went down, and the muddled moment was kindly spent."
    )


def helper_resolution(world: World, trucker: Entity, listener: Entity, cook: Entity, method: Method) -> None:
    cook.memes["helpfulness"] += 1
    world.say(
        method.fallback.format(cook=cook.id, surface=world.place.menu_surface)
    )
    world.say(
        f'"Croquette!" said {cook.id} with a grin, tapping the word so plain and neat. '
        f'"Ah!" said {listener.id}. "Now I hear it right -- not coat, not crate, but croquette to eat."'
    )
    world.facts["clarity_used"] = method.clarity + 2
    propagate(world, narrate=False)
    trucker.meters["served"] += 1
    trucker.meters["hunger"] = 0.0
    trucker.memes["relief"] += 1
    trucker.memes["joy"] += 1
    listener.memes["relief"] += 1
    listener.memes["joy"] += 1
    cook.memes["joy"] += 1
    world.say(
        f"Then out came the croquette at last, warm and round and crackly-sweet. "
        f"The three of them smiled at the silly achoo that had tangled a simple treat."
    )
    world.say(
        f"Before {trucker.id} left, {listener.id} wrote CROQUETTE in a bold little seat on the chalkboard edge, "
        f"so the next soft sneeze and the next quick breeze would still let the right words meet."
    )


def tell(
    place: Place,
    sneeze: Sneeze,
    method: Method,
    trucker_name: str = "Milo",
    listener_name: str = "Nell",
    listener_type: str = "server_f",
    cook_name: str = "Bo",
    cook_type: str = "cook_m",
) -> World:
    world = World(place)
    trucker = world.add(Entity(id=trucker_name, kind="character", type="trucker", role="trucker", label="the trucker"))
    listener = world.add(Entity(id=listener_name, kind="character", type=listener_type, role="listener", label="the server"))
    cook = world.add(Entity(id=cook_name, kind="character", type=cook_type, role="cook", label="the cook"))
    counter = world.add(Entity(id="counter", type="counter", label="the counter"))

    world.facts.update(
        place=place,
        sneeze=sneeze,
        method=method,
        trucker=trucker,
        listener=listener,
        cook=cook,
        food="croquette",
        asked_food="croquette",
        clarity_used=0,
    )

    introduce(world, trucker, listener, place)
    spot_food(world, trucker)

    world.para()
    ask_and_sneeze(world, trucker, listener, sneeze)
    react_to_mixup(world, trucker, listener, sneeze)

    world.para()
    try_method(world, trucker, listener, method)
    quick = is_quick_fix(sneeze, method)
    if quick and listener.meters["understood"] >= THRESHOLD:
        quick_resolution(world, trucker, listener, method)
        outcome = "quick_fix"
    else:
        helper_resolution(world, trucker, listener, cook, method)
        outcome = "helper_fix"

    world.facts["outcome"] = outcome
    return world


PLACES = {
    "diner": Place(
        id="diner",
        label="the Blue Mile Diner",
        scene="a shiny roadside diner",
        menu_surface="the tall menu board",
        serves_croquette=True,
        affordances={"menu_board", "napkin", "glass_case"},
        tags={"diner", "menu"},
    ),
    "truck_stop": Place(
        id="truck_stop",
        label="the Red Pump Truck Stop Café",
        scene="a busy truck-stop café",
        menu_surface="the chalkboard by the pie case",
        serves_croquette=True,
        affordances={"menu_board", "glass_case"},
        tags={"truck_stop", "menu"},
    ),
    "harbor_cafe": Place(
        id="harbor_cafe",
        label="the Harbor Lantern Café",
        scene="a snug café near the docks",
        menu_surface="the little card on the counter",
        serves_croquette=True,
        affordances={"napkin", "menu_card"},
        tags={"cafe", "menu"},
    ),
}

SNEEZES = {
    "soft_achoo": Sneeze(
        id="soft_achoo",
        cue="achoo",
        heard_as="coat",
        confusion=1,
        flourish="The tiny sneeze did not sound mean or rough, but it clipped the middle just enough.",
        tags={"sneeze", "achoo"},
    ),
    "flour_achoo": Sneeze(
        id="flour_achoo",
        cue="achoo",
        heard_as="coat, quick",
        confusion=2,
        flourish="It puffed like flour from a baker's sack, and \"croquette\" came out with its corners cracked.",
        tags={"sneeze", "achoo"},
    ),
    "double_achoo": Sneeze(
        id="double_achoo",
        cue="achoo-achoo",
        heard_as="cold crate",
        confusion=3,
        flourish="The double achoo bounced off spoon and plate, and the order came out sounding like \"cold crate.\"",
        tags={"sneeze", "achoo"},
    ),
}

METHODS = {
    "point_menu": Method(
        id="point_menu",
        sense=3,
        clarity=3,
        needs={"menu_board"},
        line='So {trucker} pointed to {surface} and spoke one careful beat at a time. '
             '"This one here -- croquette," {trucker} said. "Round, warm, and fine."',
        success='{listener} followed the finger, then the word, and the muddle untied like twine.',
        fallback='Still the sound wobbled in the room, so {cook} leaned out from the kitchen and patted {surface}.',
        qa_text="pointed to the menu and said the word slowly",
        tags={"menu", "clarify"},
    ),
    "write_napkin": Method(
        id="write_napkin",
        sense=3,
        clarity=2,
        needs={"napkin"},
        line='Then {trucker} borrowed a napkin and wrote CROQUETTE in neat block letters. '
             '"My mouth said achoo," {trucker} chuckled, "but my hand says supper better."',
        success='{listener} read the napkin, blinked once, and understood the letter by letter.',
        fallback='The napkin helped, but not enough, so {cook} came over and checked {surface} with a knowing nod.',
        qa_text="wrote CROQUETTE on a napkin so the order could be read clearly",
        tags={"writing", "clarify"},
    ),
    "tap_case": Method(
        id="tap_case",
        sense=2,
        clarity=2,
        needs={"glass_case"},
        line='Next {trucker} tapped the glass case softly. "Not a coat," {trucker} said. '
             '"That crunchy one there -- the croquette instead."',
        success='{listener} looked where {trucker} tapped, and the right idea popped into {listener}\'s head.',
        fallback='But the case held many snacks, so {cook} stepped in and matched the spoken word to {surface}.',
        qa_text="tapped the display case to show which food was wanted",
        tags={"display_case", "clarify"},
    ),
    "shout_again": Method(
        id="shout_again",
        sense=1,
        clarity=1,
        needs=set(),
        line='At first {trucker} simply tried saying it louder, but louder did not make it clearer.',
        success='{listener} somehow guessed it anyway, though that method was not the wiser way.',
        fallback='Loud words only made the rhyme bumpier, so {cook} came to help with a calmer clue at {surface}.',
        qa_text="shouted again",
        tags={"bad_fix"},
    ),
}

TRUCKER_NAMES = ["Milo", "Jeb", "Otis", "Rory", "Toby", "Wade"]
LISTENER_NAMES = ["Nell", "Mara", "June", "Pia", "Tess", "Lark"]
COOK_NAMES = ["Bo", "Gus", "Mae", "Ivy", "Pip", "Lou"]


@dataclass
class StoryParams:
    place: str
    sneeze: str
    method: str
    trucker_name: str
    listener_name: str
    listener_type: str
    cook_name: str
    cook_type: str
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
    "croquette": [
        (
            "What is a croquette?",
            "A croquette is a small food roll with a crispy outside and a soft filling inside. It is usually cooked until the outside turns golden and crunchy.",
        )
    ],
    "sneeze": [
        (
            "Why can a sneeze make words hard to hear?",
            "A sneeze bursts out suddenly and covers the sounds a mouth was trying to make. That can chop a word in the middle and make a listener hear the wrong thing.",
        )
    ],
    "menu": [
        (
            "Why does pointing to a menu help?",
            "Pointing gives the listener a clear visual clue. When ears get mixed up, eyes can help the words land in the right place.",
        )
    ],
    "writing": [
        (
            "Why can writing a word help people understand?",
            "Writing slows the message down and makes it visible. Even if a sound was fuzzy, the letters can still show exactly what was meant.",
        )
    ],
    "display_case": [
        (
            "Why does showing the food help in a café?",
            "Showing the real food gives a concrete clue, not just a sound. That makes misunderstandings smaller because everyone can look at the same thing.",
        )
    ],
    "clarify": [
        (
            "What should you do if someone misunderstands you?",
            "Stay calm and try another helpful way to explain. You can point, repeat slowly, or show the thing you mean.",
        )
    ],
}
KNOWLEDGE_ORDER = ["croquette", "sneeze", "menu", "writing", "display_case", "clarify"]


CURATED = [
    StoryParams(
        place="diner",
        sneeze="flour_achoo",
        method="point_menu",
        trucker_name="Milo",
        listener_name="Nell",
        listener_type="server_f",
        cook_name="Bo",
        cook_type="cook_m",
    ),
    StoryParams(
        place="harbor_cafe",
        sneeze="soft_achoo",
        method="write_napkin",
        trucker_name="Rory",
        listener_name="June",
        listener_type="server_f",
        cook_name="Mae",
        cook_type="cook_f",
    ),
    StoryParams(
        place="truck_stop",
        sneeze="double_achoo",
        method="tap_case",
        trucker_name="Otis",
        listener_name="Tess",
        listener_type="server_f",
        cook_name="Gus",
        cook_type="cook_m",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trucker = f["trucker"]
    listener = f["listener"]
    sneeze = f["sneeze"]
    place = f["place"]
    outcome = f["outcome"]
    if outcome == "helper_fix":
        return [
            'Write a gentle rhyming story for a 3-to-5-year-old that includes the words "trucker", "croquette", and "achoo".',
            f"Tell a dialogue-heavy story set in {place.scene} where a trucker asks for a croquette, a sneeze causes a misunderstanding, and a helper gently clears it up.",
            f"Write a rhyming misunderstanding story where {trucker.id} says \"croquette,\" {listener.id} hears \"{sneeze.heard_as},\" and the mix-up is solved with patience instead of anger.",
        ]
    return [
        'Write a gentle rhyming story for a 3-to-5-year-old that includes the words "trucker", "croquette", and "achoo".',
        f"Tell a short story with dialogue where a trucker in {place.scene} sneezes while ordering a croquette and then finds a calm way to be understood.",
        f"Write a rhyming café story where an achoo turns one food order into a misunderstanding, and the ending proves everyone understands at last.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trucker = f["trucker"]
    listener = f["listener"]
    cook = f["cook"]
    place = f["place"]
    sneeze = f["sneeze"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a trucker named {trucker.id} who stopped at {place.label}, plus {listener.id} at the counter. They were both trying to talk about lunch, but the sneeze made the words go crooked.",
        ),
        (
            "What did the trucker want?",
            f"{trucker.id} wanted a croquette. {trucker.pronoun('possessive').capitalize()} hunger and the sight of the golden snack are what started the whole scene.",
        ),
        (
            f"Why did {listener.id} misunderstand {trucker.id}?",
            f"{trucker.id} sneezed -- {sneeze.cue} -- right in the middle of saying \"croquette,\" so the word came out sounding like \"{sneeze.heard_as}.\" The misunderstanding happened because the sneeze covered part of the order, not because anyone was being rude.",
        ),
    ]
    if outcome == "quick_fix":
        qa.append(
            (
                f"How did {trucker.id} fix the misunderstanding?",
                f"{trucker.id} {method.qa_text}. That gave {listener.id} a clear clue beyond the fuzzy sound, so the right order was understood quickly.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the croquette arriving hot and crispy. The room felt bright again because the mix-up was solved with patience and a laugh.",
            )
        )
    else:
        qa.append(
            (
                f"Who helped solve the problem after {method.id.replace('_', ' ')} was not enough?",
                f"{cook.id} helped from the kitchen and showed the word clearly. That extra clue untangled the misunderstanding, so {listener.id} could finally hear that {trucker.id} wanted a croquette.",
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first the café held a muddled order and a worried pause, but by the end everyone understood one another. {listener.id} even made the word easier to see for next time, so a future achoo would not twist it again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"croquette"} | set(world.facts["sneeze"].tags) | set(world.facts["method"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} clarity_used={world.facts.get('clarity_used')}")
    return "\n".join(lines)


def explain_rejection(place: Place, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). In this world, shouting again is known but not preferred; "
            f"the story should choose a calmer clarifying move.)"
        )
    if not place.serves_croquette:
        return f"(No story: {place.label} does not serve croquette, so the order premise does not fit.)"
    missing = sorted(method.needs - place.affordances)
    if missing:
        return (
            f"(No story: {place.label} lacks what '{method.id}' needs: {missing}. "
            f"The fix must use a real clue available in that place.)"
        )
    return "(No story: that combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    sneeze = SNEEZES[params.sneeze]
    method = METHODS[params.method]
    return "quick_fix" if is_quick_fix(sneeze, method) else "helper_fix"


ASP_RULES = r"""
valid(P,M) :- place(P), method(M), serves_croquette(P), sensible(M), need_ok(P,M).
need_ok(P,M) :- place(P), method(M), not missing_need(P,M).

missing_need(P,M) :- needs(M,N), not affords(P,N).

quick_fix :- chosen_sneeze(S), chosen_method(M), confusion(S,C), clarity(M,K), K > C.
helper_fix :- chosen_sneeze(S), chosen_method(M), confusion(S,C), clarity(M,K), K <= C.

outcome(quick_fix) :- quick_fix.
outcome(helper_fix) :- helper_fix.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.serves_croquette:
            lines.append(asp.fact("serves_croquette", pid))
        for need in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, need))
    for sid, sneeze in SNEEZES.items():
        lines.append(asp.fact("sneeze", sid))
        lines.append(asp.fact("confusion", sid, sneeze.confusion))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("clarity", mid, method.clarity))
        if method.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", mid))
        for need in sorted(method.needs):
            lines.append(asp.fact("needs", mid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_sneeze", params.sneeze),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        sink = io.StringIO()
        old = sys.stdout
        sys.stdout = sink
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a trucker, a croquette, an achoo, and a rhyming misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sneeze", choices=SNEEZES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_people(rng: random.Random) -> tuple[str, str, str, str]:
    listener_type = rng.choice(["server_f", "server_m"])
    cook_type = rng.choice(["cook_f", "cook_m"])
    trucker_name = rng.choice(TRUCKER_NAMES)
    listener_name = rng.choice([n for n in LISTENER_NAMES if n != trucker_name])
    cook_name = rng.choice([n for n in COOK_NAMES if n not in {trucker_name, listener_name}])
    return trucker_name, listener_name, listener_type, cook_name, cook_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.method:
        if not valid_combo(PLACES[args.place], METHODS[args.method]):
            raise StoryError(explain_rejection(PLACES[args.place], METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.method is None or c[1] == args.method)
    ]
    if not combos:
        if args.place and args.method:
            raise StoryError(explain_rejection(PLACES[args.place], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, method_id = rng.choice(sorted(combos))
    sneeze_id = args.sneeze or rng.choice(sorted(SNEEZES))
    trucker_name, listener_name, listener_type, cook_name, cook_type = _pick_people(rng)
    return StoryParams(
        place=place_id,
        sneeze=sneeze_id,
        method=method_id,
        trucker_name=trucker_name,
        listener_name=listener_name,
        listener_type=listener_type,
        cook_name=cook_name,
        cook_type=cook_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.sneeze not in SNEEZES:
        raise StoryError(f"(Unknown sneeze: {params.sneeze})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    sneeze = SNEEZES[params.sneeze]
    method = METHODS[params.method]
    if not valid_combo(place, method):
        raise StoryError(explain_rejection(place, method))

    world = tell(
        place=place,
        sneeze=sneeze,
        method=method,
        trucker_name=params.trucker_name,
        listener_name=params.listener_name,
        listener_type=params.listener_type,
        cook_name=params.cook_name,
        cook_type=params.cook_type,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, method) combos:\n")
        for place, method in combos:
            print(f"  {place:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.trucker_name}: {p.place}, {p.sneeze}, {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
