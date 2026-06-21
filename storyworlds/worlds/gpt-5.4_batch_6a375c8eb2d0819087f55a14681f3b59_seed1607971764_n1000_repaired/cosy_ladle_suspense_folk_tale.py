#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cosy_ladle_suspense_folk_tale.py
===========================================================

A standalone story world for a cosy folk-tale suspense story about a child, a
grandmother, a simmering supper, and a mysterious sound in the night.

The little domain:
- A child and a grandmother are cooking with a ladle in a warm house.
- A strange sound comes from the door, window, or chimney.
- The child imagines something fearsome.
- The grandmother chooses a sensible way to answer the mystery.
- The true visitor is revealed, and the bubbling meal is either saved or lightly
  scorched depending on how quickly and wisely they respond.

The world model drives:
- physical meters: bubbling, scorched, smoke, cold, hunger
- emotional memes: fear, curiosity, calm, relief, welcome

It also includes:
- a Python reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in the simulated world
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather", "peddler", "ferryman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Home:
    id: str
    label: str
    warm_detail: str
    night_detail: str
    openings: set[str] = field(default_factory=set)
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
class Meal:
    id: str
    label: str
    phrase: str
    smell: str
    bubble_text: str
    saved_end: str
    scorched_end: str
    risk: int
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
class Visitor:
    id: str
    label: str
    article: str
    reveal: str
    need: str
    gift: str
    sound: str
    places: set[str] = field(default_factory=set)
    cold: int = 1
    hungry: int = 1
    tags: set[str] = field(default_factory=set)

    @property
    def phrase(self) -> str:
        return f"{self.article} {self.label}"
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
class SoundPlace:
    id: str
    label: str
    from_text: str
    open_text: str
    small_hint: str
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
    label: str
    sense: int
    power: int
    action_text: str
    reveal_text: str
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
    def __init__(self, home: Home) -> None:
        self.home = home
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
        clone = World(self.home)
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


def _r_scorch(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["bubbling"] < THRESHOLD:
        return out
    unattended = pot.attrs.get("unattended", 0)
    if unattended < world.facts.get("severity", 0):
        return out
    sig = ("scorch", unattended, world.facts.get("severity", 0))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["scorched"] = 1.0
    pot.meters["smoke"] = 1.0
    for eid in ("child", "elder"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__scorched__")
    return out


def _r_welcome(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("visitor_inside"):
        return out
    visitor = world.get("visitor")
    if visitor.meters["cold"] >= THRESHOLD or visitor.meters["hungry"] >= THRESHOLD:
        sig = ("welcome", visitor.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        visitor.meters["cold"] = 0.0
        visitor.meters["hungry"] = 0.0
        visitor.memes["relief"] += 1
        world.get("child").memes["kindness"] += 1
        world.get("elder").memes["kindness"] += 1
        out.append("__welcomed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scorch", tag="physical", apply=_r_scorch),
    Rule(name="welcome", tag="social", apply=_r_welcome),
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
        for sent in produced:
            world.say(sent)
    return produced


def plausible_visit(visitor: Visitor, place: SoundPlace, home: Home) -> bool:
    return place.id in visitor.places and place.id in home.openings


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(meal: Meal, delay: int) -> int:
    return meal.risk + delay


def meal_saved(response: Response, meal: Meal, delay: int) -> bool:
    return response.power >= severity_of(meal, delay)


def predict_wait(world: World, extra_unattended: int) -> dict:
    sim = world.copy()
    sim.facts["severity"] = world.facts.get("severity", 0)
    sim.get("pot").attrs["unattended"] += extra_unattended
    propagate(sim, narrate=False)
    return {
        "scorched": sim.get("pot").meters["scorched"] >= THRESHOLD,
        "smoke": sim.get("pot").meters["smoke"] >= THRESHOLD,
    }


def setup_scene(world: World, child: Entity, elder: Entity, meal: Meal) -> None:
    pot = world.get("pot")
    child.memes["cosy"] += 1
    elder.memes["calm"] += 1
    pot.meters["bubbling"] = 1.0
    world.say(
        f"In {world.home.label}, where {world.home.warm_detail}, {child.id} stood on a stool beside "
        f"{elder.label_word} and stirred {meal.phrase} with a wooden ladle."
    )
    world.say(
        f"The room felt cosy, and {meal.smell} while the fire hummed under the pot."
    )
    world.say(world.home.night_detail)


def strange_sound(world: World, child: Entity, visitor: Visitor, place: SoundPlace, meal: Meal) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Then came {visitor.sound} {place.from_text}. {meal.bubble_text}, but now even the soup-song "
        f"seemed to be listening."
    )
    world.say(
        f'"Who is there?" whispered {child.id}, for in folk tales a small sound in the dark often hides a great surprise.'
    )


def imagine(world: World, child: Entity, place: SoundPlace) -> None:
    world.say(
        f"{child.id} gripped the ladle and stared at {place.label}. In the dancing firelight, every shadow looked one breath larger than before."
    )


def grounded_guess(world: World, elder: Entity, visitor: Visitor, place: SoundPlace) -> None:
    pred = predict_wait(world, extra_unattended=1)
    world.facts["predicted_scorch"] = pred["scorched"]
    world.say(
        f'But {elder.label_word.capitalize()} tilted {elder.pronoun("possessive")} head and listened. '
        f'"That is not the thump of a giant," {elder.pronoun()} said. '
        f'"It sounds more like {place.small_hint}, and whatever waits there is likely {visitor.need}."'
    )
    if pred["scorched"]:
        world.say(
            f'"Still, we must be quick, or supper will catch on the bottom of the pot."'
        )


def respond(world: World, child: Entity, elder: Entity, response: Response, place: SoundPlace) -> None:
    child.memes["bravery"] += 1
    elder.memes["calm"] += 1
    pot = world.get("pot")
    pot.attrs["unattended"] += world.facts.get("delay", 0)
    pot.attrs["unattended"] += 1
    propagate(world, narrate=False)
    world.say(response.action_text.format(
        child=child.id,
        elder=elder.label_word,
        place=place.label,
    ))


def reveal_visitor(world: World, visitor_cfg: Visitor, place: SoundPlace, response: Response) -> None:
    visitor = world.get("visitor")
    world.facts["visitor_inside"] = True
    propagate(world, narrate=False)
    world.say(
        response.reveal_text.format(
            place=place.open_text,
            reveal=visitor_cfg.reveal,
        )
    )


def saved_meal_ending(world: World, child: Entity, elder: Entity, meal: Meal, visitor_cfg: Visitor) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"{child.id} laughed at {child.pronoun('possessive')} own shivers and reached for the ladle again."
    )
    world.say(
        f"Soon the pot was smooth and shining, and {meal.saved_end}. "
        f"They set out an extra bowl for {visitor_cfg.phrase}, who had brought {visitor_cfg.gift} in return for warmth."
    )
    world.say(
        f"By the time the moon climbed over the roof, the once-mysterious sound had become only a tale told beside the fire."
    )


def scorched_meal_ending(world: World, child: Entity, elder: Entity, meal: Meal, visitor_cfg: Visitor) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    elder.memes["patience"] += 1
    world.say(
        f"When {child.id} hurried back to the hearth, a thin dark smell curled from the pot."
    )
    world.say(
        f"{meal.scorched_end}. Yet {elder.label_word} only smiled, scraped away the bitter part, and shared bread and the unburned spoonfuls with {visitor_cfg.phrase}."
    )
    world.say(
        f"Thus {child.id} learned that a frightened moment can mark a supper, but kindness can still mend the evening."
    )


def tell(
    home: Home,
    meal: Meal,
    visitor_cfg: Visitor,
    place: SoundPlace,
    response: Response,
    *,
    child_name: str = "Mira",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World(home)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    pot = world.add(Entity(id="pot", type="pot", label=meal.label, attrs={"unattended": 0}))
    visitor = world.add(Entity(
        id="visitor",
        kind="character" if visitor_cfg.id in {"peddler", "ferryman"} else "thing",
        type=visitor_cfg.id if visitor_cfg.id in {"peddler", "ferryman"} else "animal",
        label=visitor_cfg.label,
        role="visitor",
        attrs={"place": place.id},
        tags=set(visitor_cfg.tags),
    ))
    visitor.meters["cold"] = float(visitor_cfg.cold)
    visitor.meters["hungry"] = float(visitor_cfg.hungry)

    world.facts.update(
        home=home,
        meal=meal,
        visitor_cfg=visitor_cfg,
        place=place,
        response=response,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        delay=delay,
        severity=severity_of(meal, delay),
        visitor_inside=False,
    )

    setup_scene(world, child, elder, meal)
    world.para()
    strange_sound(world, child, visitor_cfg, place, meal)
    imagine(world, child, place)
    grounded_guess(world, elder, visitor_cfg, place)

    world.para()
    respond(world, child, elder, response, place)
    reveal_visitor(world, visitor_cfg, place, response)

    world.para()
    saved = meal_saved(response, meal, delay)
    if saved:
        saved_meal_ending(world, child, elder, meal, visitor_cfg)
        outcome = "saved"
    else:
        scorched_meal_ending(world, child, elder, meal, visitor_cfg)
        outcome = "scorched"

    world.facts.update(
        child=child,
        elder=elder,
        pot=pot,
        visitor=visitor,
        outcome=outcome,
        meal_saved=saved,
        pot_scorched=pot.meters["scorched"] >= THRESHOLD,
    )
    return world


HOMES = {
    "cottage": Home(
        id="cottage",
        label="a low stone cottage",
        warm_detail="bundles of herbs hung from the beams and the kettle shelf shone like old honey",
        night_detail="Outside, the lane had gone dark, and the wind walked softly through the grass.",
        openings={"door", "window"},
        tags={"cottage", "home"},
    ),
    "cabin": Home(
        id="cabin",
        label="a pinewood cabin",
        warm_detail="the rafters smelled of cedar and the fire painted the walls gold",
        night_detail="Outside, the pines whispered to one another, and the dark stood close between the trunks.",
        openings={"door", "window", "chimney"},
        tags={"cabin", "home"},
    ),
    "millhouse": Home(
        id="millhouse",
        label="a little mill house",
        warm_detail="sacks of grain leaned by the wall and the warm oven stones held the day inside them",
        night_detail="Outside, the wheel creek muttered low, and the fields had turned the color of crows' wings.",
        openings={"door", "window"},
        tags={"mill", "home"},
    ),
}

MEALS = {
    "soup": Meal(
        id="soup",
        label="soup",
        phrase="a pot of carrot soup",
        smell="it smelled of onion and sweet roots",
        bubble_text="The broth made round, sleepy bubbles",
        saved_end="the carrot soup stayed bright and silky",
        scorched_end="The carrot soup had scorched at the edges of the pot",
        risk=1,
        tags={"soup", "food"},
    ),
    "porridge": Meal(
        id="porridge",
        label="porridge",
        phrase="a pot of oat porridge",
        smell="it smelled of oats and warm milk",
        bubble_text="The porridge plopped in thick little moons",
        saved_end="the porridge stayed creamy enough to shine on every spoon",
        scorched_end="The porridge had caught and thickened into a stubborn brown ring",
        risk=2,
        tags={"porridge", "food"},
    ),
    "stew": Meal(
        id="stew",
        label="stew",
        phrase="a pot of bean stew",
        smell="it smelled of beans, thyme, and the last sweet turnip of autumn",
        bubble_text="The stew gave slow hearty sighs under the lid",
        saved_end="the bean stew stayed rich and deep and ready for sharing",
        scorched_end="The bean stew had darkened where it had sat too long on the heat",
        risk=2,
        tags={"stew", "food"},
    ),
}

PLACES = {
    "door": SoundPlace(
        id="door",
        label="the door",
        from_text="at the door",
        open_text="the door latch lifted",
        small_hint="patient knocking from cold knuckles or a little paw",
        tags={"door"},
    ),
    "window": SoundPlace(
        id="window",
        label="the window",
        from_text="at the windowpane",
        open_text="the shutter swung wide",
        small_hint="something small brushing at the glass",
        tags={"window"},
    ),
    "chimney": SoundPlace(
        id="chimney",
        label="the chimney",
        from_text="in the chimney throat",
        open_text="the soot-shaded hearthstone was checked",
        small_hint="claws or wings near the warm chimney stones",
        tags={"chimney"},
    ),
}

VISITORS = {
    "hedgehog": Visitor(
        id="hedgehog",
        label="hedgehog",
        article="a",
        reveal="a hedgehog with rain pearls on its prickles and an apple leaf stuck over one ear",
        need="cold and hungry",
        gift="a red mushroom cap as neat as a saucer",
        sound="three small taps and a scratch",
        places={"door", "window"},
        tags={"hedgehog", "animal"},
    ),
    "cat": Visitor(
        id="cat",
        label="stray cat",
        article="a",
        reveal="a striped cat with moon-bright eyes and whiskers trembling from the cold",
        need="cold and hungry",
        gift="a contented purr and a curl by the fire",
        sound="a soft scratch, then a questioning mew",
        places={"door", "window"},
        tags={"cat", "animal"},
    ),
    "peddler": Visitor(
        id="peddler",
        label="traveling peddler",
        article="a",
        reveal="a traveling peddler with frost on his cap and a pack of ribbons on his back",
        need="cold and road-weary",
        gift="a blue ribbon and a story from the next valley",
        sound="two careful knocks and the creak of a tired boot",
        places={"door"},
        tags={"traveler", "peddler"},
    ),
    "owl": Visitor(
        id="owl",
        label="owl",
        article="an",
        reveal="an owl blinking from the chimney ledge, carrying a twig caught around one claw",
        need="startled and wind-tossed",
        gift="a pale feather left by the hearth",
        sound="a dry flutter and a small hollow thump",
        places={"chimney", "window"},
        tags={"owl", "bird"},
    ),
}

RESPONSES = {
    "call_and_stir": Response(
        id="call_and_stir",
        label="call out while stirring",
        sense=3,
        power=3,
        action_text='{child} kept the ladle moving while {elder} called toward {place}, "Friend or feather or paw, you may answer."',
        reveal_text="A voice or rustle answered at once, and when {place}, there stood {reveal}.",
        qa_text="They answered the sound right away while keeping the pot attended with the ladle",
        tags={"ladle", "voice", "safe"},
    ),
    "lantern_peek": Response(
        id="lantern_peek",
        label="take a lantern and peek",
        sense=3,
        power=2,
        action_text='{elder.capitalize_placeholder} lit the small lantern, and {child} followed with the ladle held close as they went to {place}.',
        reveal_text="The lantern glow found the truth, and when {place}, there stood {reveal}.",
        qa_text="They took a lantern to look carefully and then opened to the visitor",
        tags={"lantern", "safe"},
    ),
    "wait_and_listen": Response(
        id="wait_and_listen",
        label="wait too long in silence",
        sense=2,
        power=1,
        action_text='{child} and {elder} waited in perfect stillness, listening so long that the ladle rested against the pot and the fire worked on by itself.',
        reveal_text="At last they dared to look, and when {place}, there stood {reveal}.",
        qa_text="They waited in silence too long before checking the sound",
        tags={"delay", "listening"},
    ),
    "bar_the_door": Response(
        id="bar_the_door",
        label="bar the door at once",
        sense=1,
        power=0,
        action_text='{child} pushed a stool against {place} while {elder} said nothing, and the pot was forgotten.',
        reveal_text="Only later did they see that beyond {place} had been {reveal}.",
        qa_text="They barred the opening instead of checking kindly",
        tags={"fear"},
    ),
}


def _format_action_text(template: str, child_name: str, elder_word: str, place_label: str) -> str:
    text = template.format(child=child_name, elder=elder_word, place=place_label)
    return text.replace("{elder.capitalize_placeholder}", elder_word.capitalize())


GIRL_NAMES = ["Mira", "Anya", "Elsa", "Tessa", "Nora", "Lina"]
BOY_NAMES = ["Ivo", "Pavel", "Tomas", "Milo", "Nico", "Jorin"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for home_id, home in HOMES.items():
        for meal_id in MEALS:
            for visitor_id, visitor in VISITORS.items():
                for place_id, place in PLACES.items():
                    if plausible_visit(visitor, place, home):
                        combos.append((home_id, meal_id, visitor_id, place_id))
    return combos


@dataclass
class StoryParams:
    home: str
    meal: str
    visitor: str
    place: str
    response: str
    child_name: str
    child_type: str
    elder_type: str
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


KNOWLEDGE = {
    "ladle": [
        (
            "What is a ladle?",
            "A ladle is a big deep spoon with a long handle. People use it to stir or serve soup and stew.",
        )
    ],
    "hedgehog": [
        (
            "What is a hedgehog?",
            "A hedgehog is a small animal with prickles on its back. It can curl up into a ball when it feels afraid.",
        )
    ],
    "cat": [
        (
            "Why might a stray cat come to a house at night?",
            "A stray cat may come close to a house because it is cold, hungry, or looking for a safe place. Warm light and food can draw it near.",
        )
    ],
    "traveler": [
        (
            "Why would a traveler knock on a door after dark?",
            "A traveler may need warmth, directions, or a little food. In folk tales, a kind home often helps a tired traveler.",
        )
    ],
    "owl": [
        (
            "Why might an owl come near a chimney or window?",
            "An owl may be drawn by warmth, light, or shelter from the wind. It likes high places where it can perch and look around.",
        )
    ],
    "door": [
        (
            "Why do sounds at a door feel mysterious at night?",
            "At night you cannot see who is outside right away, so even a small knock can feel bigger than it is. Darkness lets imagination run ahead of the truth.",
        )
    ],
    "window": [
        (
            "Why can a window make outside sounds seem spooky?",
            "Glass can turn a tiny scratch or tap into a sharp little sound. When the room is quiet, that makes the noise seem strange and important.",
        )
    ],
    "chimney": [
        (
            "Why can a chimney make odd sounds?",
            "A chimney is hollow, so flutters and bumps can echo inside it. That can make a small creature sound much larger than it really is.",
        )
    ],
    "porridge": [
        (
            "Why must porridge be stirred?",
            "Porridge is thick, so it can stick to the bottom of the pot if nobody stirs it. Stirring spreads the heat and keeps it smooth.",
        )
    ],
    "soup": [
        (
            "Why should soup not be forgotten on the fire?",
            "Soup needs watching because the heat keeps working even when you look away. If it cooks too long, the bottom can scorch.",
        )
    ],
    "stew": [
        (
            "Why does stew need time and care?",
            "Stew grows rich slowly, but it can still catch on the bottom if it is left alone over the fire. Good cooking means warmth and attention together.",
        )
    ],
    "kindness": [
        (
            "Why is kindness important in folk tales?",
            "In many folk tales, the person who answers gently learns the truth and gains a friend. Kindness often turns fear into welcome.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ladle",
    "door",
    "window",
    "chimney",
    "hedgehog",
    "cat",
    "traveler",
    "owl",
    "soup",
    "porridge",
    "stew",
    "kindness",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["child_name"]
    meal = f["meal"]
    visitor = f["visitor_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    return [
        (
            f'Write a short folk tale for a 3-to-5-year-old that includes the words '
            f'"cosy" and "ladle", begins in a warm house, and builds suspense around a strange sound at {place.label}.'
        ),
        (
            f"Tell a cosy suspense story where {child_name} is stirring {meal.phrase} with a ladle, fears something mysterious, "
            f"and discovers {visitor.phrase} instead."
        ),
        (
            f"Write a child-facing folk tale where a night sound seems frightening at first, but kindness reveals the truth and the ending is "
            f"{'warm and shared' if outcome == 'saved' else 'warm but lightly chastened'}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    meal = f["meal"]
    visitor_cfg = f["visitor_cfg"]
    place = f["place"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {elder.label_word}, and {visitor_cfg.phrase} who made the mysterious sound. The story begins with the two cooks by the fire and ends with the visitor revealed.",
        ),
        (
            "Why did the sound feel scary at first?",
            f"The sound came from {place.label} after dark, when the room was quiet and the shadows were moving in the firelight. That made {child.label}'s imagination leap ahead of the truth.",
        ),
        (
            "What was the ladle for in the story?",
            f"The ladle was first used to stir the hot {meal.label}. It also mattered during the suspense, because keeping hold of the ladle helped them care for supper while they answered the mystery.",
        ),
        (
            "What was really making the sound?",
            f"It was {visitor_cfg.phrase}. The sound matched {visitor_cfg.need}, not a monster, so the fear changed once they looked carefully.",
        ),
        (
            f"How did {elder.label_word} answer the mystery?",
            f"{elder.label_word.capitalize()} chose to {response.label}. {response.qa_text}, which turned guessing into knowing.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "Why was supper still good at the end?",
                f"Supper was still good because they answered quickly enough and did not leave the pot alone for too long. The wise response let them learn the truth without letting the {meal.label} scorch.",
            )
        )
        qa.append(
            (
                "How did the ending show that things had changed?",
                f"At first the night sound made the house feel tense and uncertain. At the end there was an extra bowl by the fire, which showed that fear had turned into welcome.",
            )
        )
    else:
        qa.append(
            (
                "Why did the meal scorch?",
                f"The meal scorched because they spent too long listening and not enough time tending the pot. The suspense pulled their attention away, and the fire kept working underneath the {meal.label}.",
            )
        )
        qa.append(
            (
                "How did the ending still become gentle?",
                f"Even after the pot caught a little, {elder.label_word} stayed patient and shared what could still be eaten. That kindness changed the night from a frightened one into a mended one.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ladle", "kindness", f["place"].id, f["meal"].id}
    visitor = f["visitor_cfg"]
    if visitor.id == "hedgehog":
        tags.add("hedgehog")
    elif visitor.id == "cat":
        tags.add("cat")
    elif visitor.id == "peddler":
        tags.add("traveler")
    elif visitor.id == "owl":
        tags.add("owl")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or k == "place"}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} severity={world.facts.get('severity')} delay={world.facts.get('delay')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        home="cottage",
        meal="soup",
        visitor="hedgehog",
        place="door",
        response="call_and_stir",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        home="cabin",
        meal="porridge",
        visitor="owl",
        place="chimney",
        response="lantern_peek",
        child_name="Ivo",
        child_type="boy",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        home="millhouse",
        meal="stew",
        visitor="peddler",
        place="door",
        response="wait_and_listen",
        child_name="Anya",
        child_type="girl",
        elder_type="grandmother",
        delay=1,
    ),
    StoryParams(
        home="cabin",
        meal="porridge",
        visitor="cat",
        place="window",
        response="wait_and_listen",
        child_name="Milo",
        child_type="boy",
        elder_type="grandmother",
        delay=1,
    ),
]


def explain_combo(visitor: Visitor, place: SoundPlace, home: Home) -> str:
    if place.id not in home.openings:
        return (
            f"(No story: {home.label} does not have a usable {place.label} in this little world, "
            f"so the sound could not honestly come from there.)"
        )
    return (
        f"(No story: {visitor.phrase.capitalize()} does not plausibly come by {place.label} here. "
        f"Pick a place from {sorted(visitor.places)}.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a kinder, calmer choice such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "saved" if meal_saved(RESPONSES[params.response], MEALS[params.meal], params.delay) else "scorched"


ASP_RULES = r"""
% ----- compatibility gate ---------------------------------------------------
valid(H, M, V, P) :- home(H), meal(M), visitor(V), place(P), opening(H, P), visitor_place(V, P).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.

% ----- outcome model --------------------------------------------------------
severity(Risk + D) :- chosen_meal(M), risk(M, Risk), delay(D).
saved :- chosen_response(R), power(R, P), severity(S), P >= S.
outcome(saved) :- saved.
outcome(scorched) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        for place_id in sorted(home.openings):
            lines.append(asp.fact("opening", home_id, place_id))
    for meal_id, meal in MEALS.items():
        lines.append(asp.fact("meal", meal_id))
        lines.append(asp.fact("risk", meal_id, meal.risk))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        for place_id in sorted(visitor.places):
            lines.append(asp.fact("visitor_place", visitor_id, place_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_meal", params.meal),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            ns = parser.parse_args([])
            p = resolve_params(ns, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cosy folk-tale suspense storyworld about a mysterious night sound and a ladle by the fire."
    )
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra distracted time before the mystery is answered")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and sensible responses from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.home and args.place and args.place not in HOMES[args.home].openings:
        visitor = VISITORS[args.visitor] if args.visitor else next(iter(VISITORS.values()))
        raise StoryError(explain_combo(visitor, PLACES[args.place], HOMES[args.home]))
    if args.visitor and args.place and args.home:
        if not plausible_visit(VISITORS[args.visitor], PLACES[args.place], HOMES[args.home]):
            raise StoryError(explain_combo(VISITORS[args.visitor], PLACES[args.place], HOMES[args.home]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.home is None or c[0] == args.home)
        and (args.meal is None or c[1] == args.meal)
        and (args.visitor is None or c[2] == args.visitor)
        and (args.place is None or c[3] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    home_id, meal_id, visitor_id, place_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or "grandmother"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        home=home_id,
        meal=meal_id,
        visitor=visitor_id,
        place=place_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        (params.home, HOMES),
        (params.meal, MEALS),
        (params.visitor, VISITORS),
        (params.place, PLACES),
        (params.response, RESPONSES),
    ):
        if key not in table:
            raise StoryError("(No story: one of the chosen options is unknown.)")
    home = HOMES[params.home]
    meal = MEALS[params.meal]
    visitor = VISITORS[params.visitor]
    place = PLACES[params.place]
    response = RESPONSES[params.response]
    if not plausible_visit(visitor, place, home):
        raise StoryError(explain_combo(visitor, place, home))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    response_text = _format_action_text(response.action_text, params.child_name, params.elder_type, place.label)
    fixed_response = Response(
        id=response.id,
        label=response.label,
        sense=response.sense,
        power=response.power,
        action_text=response_text,
        reveal_text=response.reveal_text,
        qa_text=response.qa_text,
        tags=set(response.tags),
    )

    world = tell(
        home,
        meal,
        visitor,
        place,
        fixed_response,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        delay=params.delay,
    )
    world.get("child").label = params.child_name
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (home, meal, visitor, place) combos:\n")
        for home_id, meal_id, visitor_id, place_id in combos:
            print(f"  {home_id:10} {meal_id:8} {visitor_id:9} {place_id}")
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
            header = f"### {p.child_name}: {p.meal} in {p.home} ({p.visitor} at {p.place}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
