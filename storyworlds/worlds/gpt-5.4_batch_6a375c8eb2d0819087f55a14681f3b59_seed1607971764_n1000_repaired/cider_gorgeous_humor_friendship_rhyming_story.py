#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py
============================================================================

A standalone storyworld about two friends, a pot of cider, and a gorgeous banner
that may or may not survive a gusty day.

This domain is built to stay close to a playful rhyming-story feel while still
being a genuine simulation: the world tracks physical state (loosening banner,
danger on the stand, sloshing cider, sticky mess) and emotional state
(friendship, worry, relief, laughter). The prose comes from those states, not
from a frozen paragraph.

The core constraint is simple common sense:
- there must be a real flutter hazard (an outdoor breezy place + a hangable banner)
- the rescue method must be sensible
- the ending depends on whether the chosen rescue is strong enough for the
  place, banner, and delay before the friends act

Run it
------
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py --place orchard_gate --banner satin_sign --response twine
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py --place kitchen_nook
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py --response sticker
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/cider_gorgeous_humor_friendship_rhyming_story.py --qa --json
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
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
    breeze: int
    outdoor: bool = True
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
class Banner:
    id: str
    label: str
    phrase: str
    material: str
    sail: int
    hangable: bool = True
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
class Response:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
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


@dataclass
class StoryParams:
    place: str
    banner: str
    response: str
    dreamer: str
    dreamer_gender: str
    helper: str
    helper_gender: str
    trait: str
    delay: int = 0
    relation: str = "friends"
    thermos: bool = True
    pet: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"dreamer", "helper"}]

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


def _r_flap(world: World) -> list[str]:
    out: list[str] = []
    banner = world.entities.get("banner")
    stand = world.entities.get("stand")
    if banner is None or stand is None:
        return out
    if banner.meters["loose"] < THRESHOLD:
        return out
    sig = ("flap", banner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    banner.meters["flapping"] += 1
    stand.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__flap__")
    return out


def _r_slosh(world: World) -> list[str]:
    out: list[str] = []
    stand = world.entities.get("stand")
    cider = world.entities.get("cider")
    if stand is None or cider is None:
        return out
    if stand.meters["danger"] < THRESHOLD:
        return out
    if cider.attrs.get("sealed"):
        return out
    sig = ("slosh", cider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cider.meters["sloshing"] += 1
    out.append("__slosh__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="flap", tag="physical", apply=_r_flap),
    Rule(name="slosh", tag="physical", apply=_r_slosh),
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
    "orchard_gate": Place(
        id="orchard_gate",
        label="the orchard gate",
        scene="where red apples blinked in the sun",
        breeze=2,
        outdoor=True,
        tags={"breeze", "orchard"},
    ),
    "park_table": Place(
        id="park_table",
        label="the park table",
        scene="near a duck pond bright as a plate",
        breeze=1,
        outdoor=True,
        tags={"breeze", "park"},
    ),
    "porch_step": Place(
        id="porch_step",
        label="the front porch step",
        scene="where leaves skittered by in a skipping stripe",
        breeze=1,
        outdoor=True,
        tags={"breeze", "porch"},
    ),
    "windy_hill": Place(
        id="windy_hill",
        label="the windy little hill",
        scene="where every gust liked to show off its skill",
        breeze=3,
        outdoor=True,
        tags={"breeze", "hill"},
    ),
    "kitchen_nook": Place(
        id="kitchen_nook",
        label="the kitchen nook",
        scene="with quiet tiles and hardly a puff",
        breeze=0,
        outdoor=False,
        tags={"kitchen"},
    ),
}

BANNERS = {
    "leaf_garland": Banner(
        id="leaf_garland",
        label="leaf garland",
        phrase="a gorgeous leaf garland",
        material="paper leaves",
        sail=1,
        hangable=True,
        tags={"banner", "leaves"},
    ),
    "satin_sign": Banner(
        id="satin_sign",
        label="satin sign",
        phrase="a gorgeous satin sign",
        material="shiny satin",
        sail=2,
        hangable=True,
        tags={"banner", "gorgeous"},
    ),
    "ribbon_arc": Banner(
        id="ribbon_arc",
        label="ribbon arc",
        phrase="a gorgeous ribbon arc",
        material="long ribbons",
        sail=2,
        hangable=True,
        tags={"banner", "ribbons"},
    ),
    "painted_board": Banner(
        id="painted_board",
        label="painted board",
        phrase="a painted wooden board",
        material="wood",
        sail=0,
        hangable=False,
        tags={"board"},
    ),
}

RESPONSES = {
    "clothespins": Response(
        id="clothespins",
        label="clothespins",
        sense=3,
        power=2,
        text="snapped bright clothespins onto the banner and tucked the loose middle flat",
        fail="snapped on a few clothespins, but the gust tugged harder than the little pins could hold",
        qa_text="used clothespins to pin the banner down",
        tags={"clothespins", "teamwork"},
    ),
    "twine": Response(
        id="twine",
        label="twine",
        sense=3,
        power=3,
        text="looped garden twine through the corners and tied the banner snug against the stand",
        fail="looped twine through the corners, but the knot came too late and the banner still whipped forward",
        qa_text="used twine to tie the banner tight",
        tags={"twine", "teamwork"},
    ),
    "hold_and_tie": Response(
        id="hold_and_tie",
        label="hold and tie",
        sense=4,
        power=4,
        text="worked as a pair: one held the banner still while the other tied it tight with twine",
        fail="worked fast with hands and twine, but the gust had already taken one giant swipe",
        qa_text="worked together, with one holding and one tying",
        tags={"twine", "teamwork"},
    ),
    "sticker": Response(
        id="sticker",
        label="sticker",
        sense=1,
        power=0,
        text="pressed on a shiny apple sticker as if a sticker could boss around the wind",
        fail="pressed on a shiny apple sticker, which pleased nobody except the sticker",
        qa_text="tried to use a sticker",
        tags={"sticker"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nora", "Zoe", "Ava", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Leo", "Jack", "Eli", "Noah"]
TRAITS = ["careful", "cheerful", "clever", "steady", "funny", "thoughtful"]
PETS = ["the dachshund", "the orange cat", "the duck", "the puppy"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for banner_id, banner in BANNERS.items():
            if flutter_hazard(place, banner):
                combos.append((place_id, banner_id))
    return combos


def flutter_hazard(place: Place, banner: Banner) -> bool:
    return place.outdoor and place.breeze > 0 and banner.hangable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(place: Place, banner: Banner, delay: int) -> int:
    return max(1, place.breeze + banner.sail + delay - 1)


def is_contained(place: Place, banner: Banner, response: Response, delay: int) -> bool:
    return response.power >= severity(place, banner, delay)


def explain_rejection(place: Place, banner: Banner) -> str:
    if not place.outdoor or place.breeze <= 0:
        return (
            f"(No story: {place.label} is too calm for a banner-flapping problem. "
            f"With no real breeze, there is no honest danger to the cider stand.)"
        )
    if not banner.hangable:
        return (
            f"(No story: {banner.phrase} is not really a banner you can hang and watch flutter. "
            f"Pick a garland or sign made to sway in the wind.)"
        )
    return "(No story: this place and banner do not make a plausible flutter hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_gust(world: World) -> dict:
    sim = world.copy()
    banner = sim.get("banner")
    banner.meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("stand").meters["danger"],
        "sloshing": sim.get("cider").meters["sloshing"],
    }


def _do_gust(world: World) -> None:
    banner = world.get("banner")
    banner.meters["loose"] += 1
    propagate(world, narrate=False)


def setup_scene(world: World, dreamer: Entity, helper: Entity, banner_cfg: Banner, pet: str) -> None:
    for kid in (dreamer, helper):
        kid.memes["friendship"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"{dreamer.id} and {helper.id} were the kind of friends who could turn a crate into a treat. "
        f"They set a tiny cider stand at {world.place.label}, {world.place.scene}."
    )
    world.say(
        f"There were apples in a basket, cups in a row, and {banner_cfg.phrase} waiting to steal the show."
    )
    if pet:
        world.say(f"Nearby, {pet} watched with a nose that twitched at the smell of warm cider.")


def dream_big(world: World, dreamer: Entity, helper: Entity, banner_cfg: Banner) -> None:
    dreamer.memes["pride"] += 1
    world.say(
        f'"If our sign looks gorgeous, everyone will grin!" said {dreamer.id}. '
        f'{helper.id} laughed. "Then let the little leaf fair begin."'
    )


def warn(world: World, helper: Entity, dreamer: Entity, banner_cfg: Banner, response: Response) -> None:
    pred = predict_gust(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_sloshing"] = pred["sloshing"]
    extra = ""
    if helper.traits and helper.traits[0] in {"careful", "steady", "thoughtful"}:
        extra = f" {helper.pronoun().capitalize()} pressed one palm to the stand and squinted at the breeze."
    world.say(
        f'{helper.id} looked up at the {banner_cfg.material} and said, '
        f'"Pretty is fine, but the wind may disagree. If that banner starts dancing, the cider may flee."'
        f"{extra}"
    )
    world.say(
        f'"If it wobbles," {helper.id} added, "we should grab {response.label} right away."'
    )


def hang_and_flap(world: World, dreamer: Entity, banner_cfg: Banner) -> None:
    _do_gust(world)
    world.say(
        f"{dreamer.id} lifted {banner_cfg.phrase}, high with a hopeful cheer. "
        f"Then whooo went a gust, as if the wind wanted a turn at being engineer."
    )
    world.say(
        "The banner gave one silly flap, then two, and the stand began to wobble in view."
    )


def alarm(world: World, helper: Entity) -> None:
    helper.memes["alarm"] += 1
    world.say(
        f'"Catch it!" cried {helper.id}. "The cups are starting to skate!"'
    )


def rescue(world: World, dreamer: Entity, helper: Entity, response: Response) -> None:
    banner = world.get("banner")
    stand = world.get("stand")
    cider = world.get("cider")
    banner.meters["loose"] = 0.0
    banner.meters["secure"] += 1
    stand.meters["danger"] = 0.0
    cider.meters["sloshing"] = 0.0
    for kid in (dreamer, helper):
        kid.memes["relief"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"They moved in a flash. {helper.id} and {dreamer.id} {response.text}."
    )
    world.say(
        "The breeze puffed once more, but now the banner only fluttered with manners, like a bowing parade."
    )


def happy_ending(world: World, dreamer: Entity, helper: Entity, pet: str) -> None:
    cider = world.get("cider")
    cider.meters["served"] += 1
    for kid in (dreamer, helper):
        kid.memes["laughter"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"Soon they poured the cider. Foam kissed {dreamer.id}'s lip, then hopped to {helper.id}'s too, "
        f"so both of them wore apple mustaches before the first proper sip was through."
    )
    if pet:
        world.say(f"{pet.capitalize()} tilted its head as if to ask who had invited the two fuzzy apples to tea.")
    world.say(
        f"They laughed so hard the cups went clink, clink, clink, and the stand looked grander for all their teamwork and think."
    )
    world.say(
        "By sunset the sign still swayed, the cider still glowed, and the best thing on display was the friendship they showed."
    )


def rescue_fail(world: World, dreamer: Entity, helper: Entity, response: Response, banner_cfg: Banner) -> None:
    banner = world.get("banner")
    stand = world.get("stand")
    cider = world.get("cider")
    cider.meters["spilled"] += 1
    cider.meters["sticky"] += 1
    stand.meters["mess"] += 1
    banner.meters["dipped"] += 1
    for kid in (dreamer, helper):
        kid.memes["worry"] += 1
        kid.memes["surprise"] += 1
    world.say(
        f"They tried to save it. They {response.fail}."
    )
    world.say(
        f"With one floppy swoop, the {banner_cfg.label} dipped into the cider, and splash went the table in a cinnamon shower."
    )


def sticky_repair(world: World, dreamer: Entity, helper: Entity, pet: str) -> None:
    cider = world.get("cider")
    banner = world.get("banner")
    cider.meters["shared_last_cup"] += 1
    banner.meters["retired"] += 1
    for kid in (dreamer, helper):
        kid.memes["friendship"] += 1
        kid.memes["relief"] += 1
        kid.memes["laughter"] += 1
    world.say(
        f"For one blink, {dreamer.id} looked crushed. Then {helper.id} wiped a sticky drop from {dreamer.pronoun('possessive')} nose and said, "
        f'"Well, now you really are the most gorgeous cider statue in town."'
    )
    world.say(
        f"{dreamer.id} snorted, then giggled, then laughed. Together they mopped the crate, folded away the soggy sign, and saved one warm cup from the thermos."
    )
    if pet:
        world.say(f"{pet.capitalize()} tried to sniff the sticky puddle, but both friends shooed it back with laughing toes.")
    world.say(
        "They sat side by side on the step and shared the last cup in turns. The stand was simpler now, but their smiles were brighter than the fancy sign had been."
    )


def tell(
    place: Place,
    banner_cfg: Banner,
    response: Response,
    dreamer_name: str = "Lila",
    dreamer_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    trait: str = "careful",
    delay: int = 0,
    relation: str = "friends",
    thermos: bool = True,
    pet: str = "",
) -> World:
    world = World(place)
    dreamer = world.add(Entity(
        id=dreamer_name,
        kind="character",
        type=dreamer_gender,
        label=dreamer_name,
        role="dreamer",
        traits=["bold", "funny"],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=[trait],
        attrs={"relation": relation},
    ))
    world.add(Entity(
        id="stand",
        type="stand",
        label="the stand",
        attrs={"cups": 4},
    ))
    world.add(Entity(
        id="banner",
        type="banner",
        label=banner_cfg.label,
        attrs={"material": banner_cfg.material},
    ))
    world.add(Entity(
        id="cider",
        type="drink",
        label="the cider",
        attrs={"sealed": False, "thermos": thermos},
    ))

    world.facts["pet"] = pet
    world.facts["thermos"] = thermos

    setup_scene(world, dreamer, helper, banner_cfg, pet)
    dream_big(world, dreamer, helper, banner_cfg)

    world.para()
    warn(world, helper, dreamer, banner_cfg, response)
    hang_and_flap(world, dreamer, banner_cfg)
    alarm(world, helper)

    world.para()
    needed = severity(place, banner_cfg, delay)
    world.get("banner").meters["severity"] = float(needed)
    contained = is_contained(place, banner_cfg, response, delay)
    if contained:
        rescue(world, dreamer, helper, response)
        world.para()
        happy_ending(world, dreamer, helper, pet)
        outcome = "contained"
    else:
        rescue_fail(world, dreamer, helper, response, banner_cfg)
        world.para()
        sticky_repair(world, dreamer, helper, pet)
        outcome = "spilled"

    world.facts.update(
        dreamer=dreamer,
        helper=helper,
        place=place,
        banner_cfg=banner_cfg,
        response=response,
        outcome=outcome,
        delay=delay,
        severity=needed,
        stand=world.get("stand"),
        banner=world.get("banner"),
        cider=world.get("cider"),
        relation=relation,
        rescued=contained,
        sloshed=world.get("cider").meters["sloshing"] >= THRESHOLD or not contained,
    )
    return world


def pair_noun(dreamer: Entity, helper: Entity) -> str:
    if dreamer.type == "girl" and helper.type == "girl":
        return "two friends"
    if dreamer.type == "boy" and helper.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dreamer = f["dreamer"]
    helper = f["helper"]
    place = f["place"]
    banner_cfg = f["banner_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    if outcome == "contained":
        return [
            f'Write a rhyming story for a 3-to-5-year-old about friendship, a tiny cider stand, and a gorgeous banner at {place.label}.',
            f"Tell a humorous story where {dreamer.id} and {helper.id} nearly lose their sign to the wind, but save it by using {response.label} together.",
            f'Write a playful autumn story that includes the words "cider" and "gorgeous" and ends with two friends laughing over a silly apple mustache.',
        ]
    return [
        f'Write a rhyming friendship story about a tiny cider stand at {place.label}, where a gorgeous banner causes a sticky problem.',
        f"Tell a funny story where {dreamer.id} and {helper.id} try to rescue a windy sign with {response.label}, but end up sharing one last cup together.",
        f'Write a gentle humorous story that includes the words "cider" and "gorgeous" and teaches that friends matter more than fancy decorations.',
    ]


KNOWLEDGE = {
    "cider": [
        (
            "What is cider?",
            "Cider is a drink made from apples. It can be cool or warm, and warm cider often smells sweet and spicy.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a sign or decoration that hangs up where people can see it. Light banners can flap when the wind blows.",
        )
    ],
    "breeze": [
        (
            "What is a breeze?",
            "A breeze is a soft wind. Even a soft wind can push light things like paper, ribbons, or leaves.",
        )
    ],
    "clothespins": [
        (
            "What are clothespins for?",
            "Clothespins are little clips that hold fabric or paper in place. They can help stop something light from flapping away.",
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a thin, strong string. People use it to tie things together or fasten them so they stay put.",
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help?",
            "Teamwork helps because one person can do a job that is hard alone while another person helps in a different way. Working together can make a wobbly problem easier to solve.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cider", "banner", "breeze", "clothespins", "twine", "teamwork"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dreamer = f["dreamer"]
    helper = f["helper"]
    place = f["place"]
    banner_cfg = f["banner_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(dreamer, helper)}, {dreamer.id} and {helper.id}, who made a tiny cider stand together. Their friendship matters as much as the stand itself.",
        ),
        (
            "What did they make together?",
            f"They made a little cider stand with apples, cups, and {banner_cfg.phrase}. They wanted it to look special and welcoming.",
        ),
        (
            f"Why did {helper.id} worry about the banner?",
            f"{helper.id} saw that the place was breezy and the banner was light enough to flap. {helper.pronoun().capitalize()} warned that if it danced too hard, it could bump the stand and slosh the cider.",
        ),
        (
            "What was the problem in the middle of the story?",
            f"A gust made the banner flap and the stand wobble. That put the cider in danger and turned the pretty setup into a funny, urgent mess.",
        ),
    ]
    if outcome == "contained":
        qa.extend([
            (
                f"How did they save the stand?",
                f"They moved quickly and {response.qa_text}. Because they worked together right away, the banner stopped pulling at the stand before the cider spilled.",
            ),
            (
                "Why is the ending funny?",
                f"The cider foam made little apple mustaches on both friends. They laughed at how silly they looked, which turned the scare into a joke.",
            ),
            (
                "How did the story end?",
                "It ended happily with the stand still up, the cider still warm, and the friends laughing together. The final picture shows that teamwork made the beautiful plan work.",
            ),
        ])
    else:
        qa.extend([
            (
                f"Did {response.label} work well enough?",
                f"No. They tried, but the gust beat them, and the banner dipped into the cider. That made the table sticky and spoiled the fancy setup.",
            ),
            (
                "Why is the ending still about friendship?",
                f"After the splash, one friend made the other laugh instead of blaming them. Then they cleaned up together and shared the last cup, showing that being kind mattered more than keeping the stand perfect.",
            ),
            (
                "How did the story end?",
                "It ended with the fancy sign put away and the two friends sitting side by side, sharing one warm cup. The ending proves that they cared more about each other than about looking grand.",
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cider", "banner", "breeze"}
    tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park_table",
        banner="leaf_garland",
        response="clothespins",
        dreamer="Lila",
        dreamer_gender="girl",
        helper="Ben",
        helper_gender="boy",
        trait="careful",
        delay=0,
        relation="friends",
        thermos=True,
        pet="the duck",
    ),
    StoryParams(
        place="orchard_gate",
        banner="satin_sign",
        response="twine",
        dreamer="Mina",
        dreamer_gender="girl",
        helper="Theo",
        helper_gender="boy",
        trait="steady",
        delay=0,
        relation="friends",
        thermos=True,
        pet="the orange cat",
    ),
    StoryParams(
        place="windy_hill",
        banner="ribbon_arc",
        response="clothespins",
        dreamer="Poppy",
        dreamer_gender="girl",
        helper="Max",
        helper_gender="boy",
        trait="thoughtful",
        delay=1,
        relation="friends",
        thermos=True,
        pet="the puppy",
    ),
    StoryParams(
        place="windy_hill",
        banner="satin_sign",
        response="hold_and_tie",
        dreamer="Nora",
        dreamer_gender="girl",
        helper="Finn",
        helper_gender="boy",
        trait="clever",
        delay=0,
        relation="friends",
        thermos=True,
        pet="the dachshund",
    ),
]


ASP_RULES = r"""
hazard(P, B) :- place(P), banner(B), outdoor(P), breeze(P, Br), Br > 0, hangable(B).
valid(P, B) :- hazard(P, B).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

severity(V) :- chosen_place(P), chosen_banner(B), delay(D),
               breeze(P, Br), sail(B, Sa), V = Br + Sa + D - 1, V > 0.
resp_power(Pw) :- chosen_response(R), power(R, Pw).

contained :- resp_power(Pw), severity(V), Pw >= V.
outcome(contained) :- contained.
outcome(spilled) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("breeze", place_id, place.breeze))
        if place.outdoor:
            lines.append(asp.fact("outdoor", place_id))
    for banner_id, banner in BANNERS.items():
        lines.append(asp.fact("banner", banner_id))
        lines.append(asp.fact("sail", banner_id, banner.sail))
        if banner.hangable:
            lines.append(asp.fact("hangable", banner_id))
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

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_banner", params.banner),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.banner not in BANNERS or params.response not in RESPONSES:
        raise StoryError("(Outcome requested for unknown parameter value.)")
    return "contained" if is_contained(PLACES[params.place], BANNERS[params.banner], RESPONSES[params.response], params.delay) else "spilled"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny cider stand, a gorgeous banner, and friendship in the wind."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long they hesitate before grabbing the rescue method")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.banner:
        place = PLACES[args.place]
        banner = BANNERS[args.banner]
        if not flutter_hazard(place, banner):
            raise StoryError(explain_rejection(place, banner))
    if args.place and not args.banner:
        place = PLACES[args.place]
        if not place.outdoor or place.breeze <= 0:
            banner = next(iter(BANNERS.values()))
            raise StoryError(explain_rejection(place, banner))
    if args.banner and not args.place and not BANNERS[args.banner].hangable:
        place = next(v for v in PLACES.values() if v.outdoor and v.breeze > 0)
        raise StoryError(explain_rejection(place, BANNERS[args.banner]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.banner is None or combo[1] == args.banner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, banner_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    dreamer, dg = _pick_child(rng)
    helper, hg = _pick_child(rng, avoid=dreamer)
    trait = rng.choice(TRAITS)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        place=place_id,
        banner=banner_id,
        response=response_id,
        dreamer=dreamer,
        dreamer_gender=dg,
        helper=helper,
        helper_gender=hg,
        trait=trait,
        delay=delay,
        relation="friends",
        thermos=True,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.banner not in BANNERS:
        raise StoryError(f"(Unknown banner: {params.banner})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    banner_cfg = BANNERS[params.banner]
    response = RESPONSES[params.response]

    if not flutter_hazard(place, banner_cfg):
        raise StoryError(explain_rejection(place, banner_cfg))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        banner_cfg=banner_cfg,
        response=response,
        dreamer_name=params.dreamer,
        dreamer_gender=params.dreamer_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        delay=params.delay,
        relation=params.relation,
        thermos=params.thermos,
        pet=params.pet,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, banner) combos:\n")
        for place, banner in combos:
            print(f"  {place:12} {banner}")
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
            header = f"### {p.dreamer} & {p.helper}: {p.banner} at {p.place} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
