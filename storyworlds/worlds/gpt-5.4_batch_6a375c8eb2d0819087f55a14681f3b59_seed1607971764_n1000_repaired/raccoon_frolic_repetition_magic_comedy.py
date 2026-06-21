#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py
====================================================================

A standalone story world about a child preparing a silly little magic frolic,
a raccoon who cannot resist repeated tricks, and a helper who either redirects
the chaos or fails to get ahead of it.

Reference seed, rebuilt as a stateful tiny domain:
--------------------------------------------------
The seed asked for a story with the words "raccoon" and "frolic", featuring
Repetition and Magic in a comedic style. This world turns that into a small
simulation:

* A child plans a twilight frolic with a funny magic finale.
* The child enchants one light prop with an echo spell that makes it act
  "again, again, again."
* A nearby raccoon is drawn to certain kinds of props: shiny things, jangly
  things, or snacks.
* A calm grown-up predicts the trouble and tries a fitting redirect.
* If the response matches the raccoon's temptation and is strong enough for the
  prop's mischief level, the show lands smoothly. Otherwise the ending becomes a
  comic romp.

Run it
------
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --prop tart
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --prop wash_tub
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --response clap_pause
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --all
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/raccoon_frolic_repetition_magic_comedy.py --verify
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
REPEAT_COUNT = 3


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        raccoonish = {"raccoon"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in raccoonish:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
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
    opening: str
    hiding_spot: str
    ending: str
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
class Prop:
    id: str
    label: str
    phrase: str
    action: str
    repeat_line: str
    attraction: str
    mischief: int
    enchantable: bool = True
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
    sense: int
    power: int
    handles: set[str]
    text: str
    fail: str
    qa_text: str
    aftermath: str
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


def _r_magic_notice(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    child = world.entities.get("child")
    if not prop or not child:
        return out
    if prop.meters["enchanted"] < THRESHOLD:
        return out
    sig = ("magic_notice", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["delight"] += 1
    world.get("stage").meters["sparkle"] += 1
    out.append("__magic__")
    return out


def _r_raccoon_drawn(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    raccoon = world.entities.get("raccoon")
    child = world.entities.get("child")
    if not prop or not raccoon or not child:
        return out
    if prop.meters["active"] < THRESHOLD:
        return out
    if prop.attrs.get("attraction") != raccoon.attrs.get("temptation"):
        return out
    sig = ("raccoon_drawn", prop.id, raccoon.attrs.get("temptation"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    raccoon.meters["approach"] += 1
    raccoon.memes["glee"] += 1
    child.memes["surprise"] += 1
    world.get("stage").meters["clutter"] += 1
    out.append("__raccoon__")
    return out


def _r_stage_fluster(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    stage = world.entities.get("stage")
    raccoon = world.entities.get("raccoon")
    if not child or not helper or not stage or not raccoon:
        return out
    if raccoon.meters["approach"] < THRESHOLD:
        return out
    sig = ("stage_fluster", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    helper.memes["alert"] += 1
    stage.meters["noise"] += 1
    out.append("__fluster__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="magic_notice", tag="wonder", apply=_r_magic_notice),
    Rule(name="raccoon_drawn", tag="comic", apply=_r_raccoon_drawn),
    Rule(name="stage_fluster", tag="social", apply=_r_stage_fluster),
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


def hazard_at_risk(prop: Prop) -> bool:
    return prop.enchantable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def chaos_severity(prop: Prop, delay: int) -> int:
    return prop.mischief + delay


def response_matches(response: Response, prop: Prop) -> bool:
    return prop.attraction in response.handles


def is_redirected(response: Response, prop: Prop, delay: int) -> bool:
    return response_matches(response, prop) and response.power >= chaos_severity(prop, delay)


def predict_chaos(world: World) -> dict:
    sim = world.copy()
    cast_repeat_spell(sim, narrate=False)
    prop = sim.get("prop")
    raccoon = sim.get("raccoon")
    stage = sim.get("stage")
    return {
        "draws_raccoon": raccoon.meters["approach"] >= THRESHOLD,
        "clutter": stage.meters["clutter"],
        "attraction": prop.attrs.get("attraction", ""),
    }


def introduce(world: World, child: Entity, helper: Entity, prop: Prop) -> None:
    place = world.place
    helper_word = helper.label_word
    world.say(
        f"One soft evening, {child.id} asked {helper_word} if they could have a moonlight frolic in {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"{child.id} had practiced one ridiculous trick all day: {prop.phrase} would {prop.action} "
        f"whenever {child.pronoun('subject')} whispered a tiny echo spell."
    )


def invite_raccoon_hint(world: World, raccoon: Entity) -> None:
    place = world.place
    world.say(
        f"Nobody invited the raccoon, but everyone in the house knew he liked to peek from {place.hiding_spot} "
        f"whenever anything sparkled, jingled, or smelled interesting."
    )


def boast(world: World, child: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"Watch this," {child.id} said, standing as straight as a tiny magician with very serious eyebrows. '
        f'"It works again, again, again."'
    )


def warn(world: World, helper: Entity, child: Entity, prop: Prop) -> None:
    pred = predict_chaos(world)
    world.facts["predicted_draws_raccoon"] = pred["draws_raccoon"]
    world.facts["predicted_clutter"] = pred["clutter"]
    helper.memes["caution"] += 1
    if pred["draws_raccoon"]:
        world.say(
            f'{helper.label_word.capitalize()} looked at {prop.label} and gave a sideways smile. '
            f'"If it does {prop.repeat_line} in a row, that raccoon may think the whole show is meant for him."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} watched the prop closely. '
            f'"Let us make sure the trick stays funny and does not run away with itself."'
        )


def insist(world: World, child: Entity) -> None:
    child.memes["stubbornness"] += 1
    world.say(
        f'{child.id} bounced on {child.pronoun("possessive")} toes. '
        f'"Just one spell," {child.pronoun()} promised, which was exactly the kind of promise that sounded like three spells.'
    )


def cast_repeat_spell(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    prop = world.get("prop")
    prop.meters["enchanted"] += 1
    prop.meters["active"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f'{child.id} swirled one finger and whispered, "Again, again, again." '
            f'At once {prop.phrase} {prop.repeat_line}: once, twice, three times.'
        )


def raccoon_arrives(world: World, child: Entity, raccoon: Entity, prop: Prop) -> None:
    raccoon.memes["mischief"] += 1
    raccoon.meters["pawing"] += 1
    world.say(
        f"Out popped the raccoon from {world.place.hiding_spot}. He blinked at {prop.label}, "
        f"then did his own little frolic toward it as if the spell had rung a dinner bell just for him."
    )
    if prop.attraction == "snack":
        world.say(
            f"He reached for it once, reached for it twice, reached for it three times, "
            f"looking more delighted each time."
        )
    elif prop.attraction == "jingly":
        world.say(
            f"He patted at the noise once, patted at it twice, patted at it three times, "
            f"with both paws working like fuzzy little drumsticks."
        )
    else:
        world.say(
            f"He grabbed at the glitter once, grabbed at it twice, grabbed at it three times, "
            f"turning the trick into a very rude duet."
        )
    child.memes["laughter"] += 1


def redirect_success(world: World, helper: Entity, raccoon: Entity, response: Response, prop: Prop) -> None:
    stage = world.get("stage")
    raccoon.meters["approach"] = 0.0
    raccoon.meters["pawing"] = 0.0
    stage.meters["clutter"] = 0.0
    stage.meters["noise"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} did not shout. {helper.pronoun().capitalize()} {response.text}."
    )
    world.say(response.aftermath.format(prop=prop.label))
    world.say(
        f"The raccoon sat back on his haunches, busy and pleased, while {helper.label_word} nodded to {child.id} "
        f"to finish the show with a quieter flourish."
    )
    child.memes["confidence"] += 1
    child.memes["embarrassment"] = 0.0


def redirect_fail(world: World, helper: Entity, raccoon: Entity, response: Response, prop: Prop) -> None:
    stage = world.get("stage")
    stage.meters["clutter"] += 1
    stage.meters["noise"] += 1
    raccoon.meters["pawing"] += 1
    helper.memes["fluster"] += 1
    child.memes["embarrassment"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {response.fail}."
    )
    world.say(
        f"But the raccoon was already too interested in the {prop.label}. He scampered through the middle of the act, "
        f"and now the whole yard was laughing too hard to pretend this had ever been a proper performance."
    )


def quiet_finale(world: World, child: Entity, prop: Prop) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} took a breath, bowed to the moon, and changed the ending. "
        f"Instead of making {prop.label} repeat itself, {child.pronoun()} let the last spark drift up softly and vanish."
    )
    world.say(world.place.ending)


def comic_romp_ending(world: World, child: Entity, helper: Entity, raccoon: Entity, prop: Prop) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    raccoon.memes["glee"] += 1
    world.say(
        f"In the end, {child.id}, {helper.label_word}, and the raccoon all crossed the yard in one crooked parade, "
        f"following the {prop.label} in circles until even the fireflies seemed to be giggling."
    )
    world.say(
        f"When the spinning finally stopped, the raccoon sat in the grass looking terribly proud of himself, "
        f"as if he had been the head magician all along."
    )


def tell(
    place: Place,
    prop_cfg: Prop,
    response: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
        traits=["eager", "dramatic"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        traits=["calm", "wry"],
    ))
    raccoon = world.add(Entity(
        id="Pip",
        kind="character",
        type="raccoon",
        role="raccoon",
        label="the raccoon",
        traits=["curious", "nimble"],
        attrs={"temptation": prop_cfg.attraction},
    ))
    stage = world.add(Entity(
        id="stage",
        kind="thing",
        type="yard",
        label="the yard",
        attrs={"place": place.id},
    ))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type="prop",
        label=prop_cfg.label,
        attrs={"attraction": prop_cfg.attraction, "mischief": prop_cfg.mischief},
        tags=set(prop_cfg.tags),
    ))

    world.facts.update(
        place=place,
        prop_cfg=prop_cfg,
        response=response,
        repeat_count=REPEAT_COUNT,
        delay=delay,
    )

    introduce(world, child, helper, prop_cfg)
    invite_raccoon_hint(world, raccoon)

    world.para()
    boast(world, child)
    warn(world, helper, child, prop_cfg)
    insist(world, child)

    world.para()
    cast_repeat_spell(world, narrate=True)
    raccoon_arrives(world, child, raccoon, prop_cfg)

    redirected = is_redirected(response, prop_cfg, delay)

    world.para()
    if redirected:
        redirect_success(world, helper, raccoon, response, prop_cfg)
        quiet_finale(world, child, prop_cfg)
        outcome = "redirected"
    else:
        redirect_fail(world, helper, raccoon, response, prop_cfg)
        comic_romp_ending(world, child, helper, raccoon, prop_cfg)
        outcome = "romp"

    world.facts.update(
        child=child,
        helper=helper,
        raccoon=raccoon,
        stage=stage,
        prop=prop,
        attracted=prop_cfg.attraction,
        redirected=redirected,
        outcome=outcome,
        clutter=stage.meters["clutter"],
        repeated=True,
    )
    return world


PLACES = {
    "backyard": Place(
        id="backyard",
        label="the backyard",
        opening="The clothesline shivered in the breeze, and the old plum tree looked ready to clap.",
        hiding_spot="the plum tree",
        ending="The frolic ended with moonlit grass, one pleased child, and one politely disappointed raccoon.",
        tags={"yard"},
    ),
    "porch": Place(
        id="porch",
        label="the porch garden",
        opening="Flowerpots lined the steps like an audience that had already bought tickets.",
        hiding_spot="under the porch bench",
        ending="The frolic ended with flowerpots still upright and the porch glowing like a tiny stage.",
        tags={"garden"},
    ),
    "orchard": Place(
        id="orchard",
        label="the little orchard",
        opening="The pears hung above the path like sleepy lanterns waiting for a joke.",
        hiding_spot="the crate by the fence",
        ending="The frolic ended beneath the pear trees, where even the leaves seemed to be smiling.",
        tags={"orchard"},
    ),
}

PROPS = {
    "ribbon": Prop(
        id="ribbon",
        label="silver ribbon",
        phrase="a silver ribbon on a stick",
        action="whip bright loops through the air",
        repeat_line="whipped bright loops through the air again and again and again",
        attraction="shiny",
        mischief=1,
        enchantable=True,
        tags={"shiny", "magic_ribbon"},
    ),
    "bell_hat": Prop(
        id="bell_hat",
        label="bell hat",
        phrase="a tall paper hat with three tiny bells",
        action="bob like it knew a secret tune",
        repeat_line="bobbed and chimed again and again and again",
        attraction="jingly",
        mischief=2,
        enchantable=True,
        tags={"bells", "hat"},
    ),
    "tart": Prop(
        id="tart",
        label="jam tart",
        phrase="a jam tart balanced on a saucer",
        action="spin in a perfect smug little circle",
        repeat_line="spun in perfect smug little circles again and again and again",
        attraction="snack",
        mischief=3,
        enchantable=True,
        tags={"snack", "tart"},
    ),
    "wash_tub": Prop(
        id="wash_tub",
        label="wash tub",
        phrase="a dented wash tub",
        action="thump around the yard",
        repeat_line="thumped around the yard again and again and again",
        attraction="jingly",
        mischief=4,
        enchantable=False,
        tags={"heavy"},
    ),
}

RESPONSES = {
    "berry_bowl": Response(
        id="berry_bowl",
        sense=3,
        power=4,
        handles={"snack"},
        text="set down a bowl of blackberries at the far end of the grass and slid it away with a magician's flourish",
        fail="hurried out a bowl of blackberries, but set it down too near to distract anyone",
        qa_text="set out a bowl of blackberries to lead the raccoon away from the trick",
        aftermath="The sweet smell pulled the trouble right off the stage, and the raccoon trotted after it as if that had been the plan all along.",
        tags={"berries", "raccoon"},
    ),
    "shiny_button": Response(
        id="shiny_button",
        sense=3,
        power=3,
        handles={"shiny", "jingly"},
        text="flicked a bright tin button across the flagstones, where it winked and rattled in a more interesting direction",
        fail="flicked a bright tin button, but it only made the raccoon come faster",
        qa_text="used a bright rattling button to pull the raccoon toward a safer spot",
        aftermath="The button skittered away in tiny flashes, and the raccoon chased that sparkle instead of snatching the {prop}.",
        tags={"shiny", "button", "raccoon"},
    ),
    "lantern_swap": Response(
        id="lantern_swap",
        sense=2,
        power=2,
        handles={"shiny"},
        text="lifted a paper moon lantern and raised it high so the soft glow became the new star of the show",
        fail="lifted the moon lantern, but the new glow was not enough to beat the old excitement",
        qa_text="raised a moon lantern to give the raccoon a calmer glow to follow",
        aftermath="The raccoon paused, dazzled by the lantern, and for one useful moment forgot all about the {prop}.",
        tags={"lantern", "light"},
    ),
    "clap_pause": Response(
        id="clap_pause",
        sense=1,
        power=1,
        handles=set(),
        text="clapped twice and said, \"Shoo, please,\" in the hopeful voice of someone who had no real plan",
        fail="clapped twice and said, \"Shoo, please,\" but the sound only turned into part of the game",
        qa_text="clapped and tried to shoo the raccoon",
        aftermath="For one second everybody looked hopeful, which was not the same thing as helpful.",
        tags={"clap"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Poppy", "Ivy", "June", "Ada"]
BOY_NAMES = ["Otis", "Ben", "Milo", "Finn", "Theo", "Jules", "Sam", "Leo"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in PLACES:
        for prop_id, prop in PROPS.items():
            if hazard_at_risk(prop):
                combos.append((place_id, prop_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prop: str
    response: str
    child_name: str
    child_type: str
    helper_type: str
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
    "raccoon": [
        (
            "What is a raccoon?",
            "A raccoon is a small masked animal with clever paws. It likes to explore, sniff, and grab interesting things."
        )
    ],
    "magic": [
        (
            "What is a magic trick?",
            "A magic trick is a pretend piece of wonder that makes something seem surprising or impossible. In stories it can be playful and funny instead of scary."
        )
    ],
    "repetition": [
        (
            "What does repetition mean in a story?",
            "Repetition means something happens again and again on purpose. It can make a story funnier because children can feel the pattern building."
        )
    ],
    "berries": [
        (
            "Why might berries distract a raccoon?",
            "Raccoons follow smells and snacks very quickly. A bowl of berries can pull their attention away from something else."
        )
    ],
    "shiny": [
        (
            "Why do shiny things catch the eye?",
            "Shiny things flash the light back at you. That quick glint makes them easy to notice."
        )
    ],
    "bells": [
        (
            "Why do bells attract attention?",
            "Bells make quick bright sounds that are hard to ignore. A jingle can call people or animals to look."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a covered light that glows steadily. It can make a place feel warm and magical."
        )
    ],
}
KNOWLEDGE_ORDER = ["raccoon", "magic", "repetition", "berries", "shiny", "bells", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    prop_cfg = f["prop_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    if outcome == "redirected":
        return [
            f'Write a funny bedtime story for a 3-to-5-year-old that includes the words "raccoon" and "frolic". A child uses magic in {place.label}, and a repeated trick almost lures a raccoon into the show.',
            f"Tell a comedy where {child.id} enchants {prop_cfg.phrase}, it happens again and again, and a calm grown-up redirects the raccoon with {response.id.replace('_', ' ')}.",
            f'Write a gentle magic story with repetition, a backyard frolic, and a silly raccoon interruption that ends neatly and softly.',
        ]
    return [
        f'Write a funny story for a 3-to-5-year-old using the words "raccoon" and "frolic". A child performs a magic trick in {place.label}, and repetition makes the trouble bigger.',
        f"Tell a comedy where {child.id} enchants {prop_cfg.phrase}, the trick repeats three times, and a raccoon turns the whole show into a romp.",
        f'Write a playful magical story with repetition where a raccoon barges into a moonlight frolic and steals the scene.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    raccoon = f["raccoon"]
    place = f["place"]
    prop_cfg = f["prop_cfg"]
    response = f["response"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper_word}, and a raccoon named {raccoon.id}. They are all pulled into one silly moonlight frolic."
        ),
        (
            f"What trick did {child.id} want to do?",
            f"{child.id} wanted to enchant {prop_cfg.phrase} so it would {prop_cfg.action}. The joke of the trick was that it would keep going again, again, again."
        ),
        (
            f"Why did {helper_word} worry before the spell?",
            f"{helper_word.capitalize()} guessed that repeating the trick would draw the raccoon closer. The prop was exactly the kind of thing that matched what the raccoon wanted."
        ),
        (
            "How did repetition change the problem?",
            f"The trick did not happen only once; it repeated three times, so the raccoon had three chances to notice it and rush in. That pattern made the comedy grow bigger with each beat."
        ),
    ]
    if f["outcome"] == "redirected":
        qa.append((
            f"How did {helper_word} fix the problem?",
            f"{helper_word.capitalize()} {response.qa_text}. That worked because the response matched what the raccoon cared about more than the trick itself."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the raccoon settled somewhere else and {child.id} finishing the show quietly. The ending proves the frolic changed from noisy confusion into a calm little bit of magic."
        ))
    else:
        qa.append((
            f"Did {helper_word}'s plan stop the raccoon?",
            f"No. {helper_word.capitalize()}'s idea was too weak or not suited to the kind of prop, so the raccoon stayed in the middle of the act. That is why the show turned into a comic chase instead of a tidy performance."
        ))
        qa.append((
            "How did the story end?",
            f"It ended in a laughing romp, with everyone circling the yard and the raccoon acting like the star. The change is clear because the planned magic show becomes a shared frolic instead."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    prop_cfg = f["prop_cfg"]
    response = f["response"]
    tags: set[str] = {"raccoon", "magic", "repetition"}
    if prop_cfg.attraction == "snack":
        tags.add("berries")
    if prop_cfg.attraction == "shiny":
        tags.add("shiny")
    if prop_cfg.attraction == "jingly":
        tags.add("bells")
    if "lantern" in response.tags:
        tags.add("lantern")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        prop="ribbon",
        response="shiny_button",
        child_name="Mina",
        child_type="girl",
        helper_type="grandmother",
        delay=0,
    ),
    StoryParams(
        place="porch",
        prop="bell_hat",
        response="shiny_button",
        child_name="Otis",
        child_type="boy",
        helper_type="grandfather",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        prop="tart",
        response="berry_bowl",
        child_name="Lila",
        child_type="girl",
        helper_type="grandmother",
        delay=1,
    ),
    StoryParams(
        place="backyard",
        prop="tart",
        response="lantern_swap",
        child_name="Milo",
        child_type="boy",
        helper_type="grandfather",
        delay=1,
    ),
    StoryParams(
        place="porch",
        prop="bell_hat",
        response="lantern_swap",
        child_name="June",
        child_type="girl",
        helper_type="grandmother",
        delay=1,
    ),
]


def explain_rejection(prop: Prop) -> str:
    if not prop.enchantable:
        return (
            f"(No story: {prop.phrase} is too clunky for this little echo spell. "
            f"The trick needs a light prop that can act funny three times in a row.)"
        )
    return "(No story: this prop does not fit the world.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a more purposeful redirect: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    prop = PROPS[params.prop]
    response = RESPONSES[params.response]
    return "redirected" if is_redirected(response, prop, params.delay) else "romp"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, Pr) :- place(P), prop(Pr), enchantable(Pr).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
severity(V)      :- chosen_prop(Pr), mischief(Pr, M), delay(D), V = M + D.
matches_response :- chosen_prop(Pr), attraction(Pr, A),
                    chosen_response(R), handles(R, A).
redirected       :- matches_response, chosen_response(R), power(R, P),
                    severity(V), P >= V.

outcome(redirected) :- redirected.
outcome(romp)       :- not redirected.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        if prop.enchantable:
            lines.append(asp.fact("enchantable", prop_id))
        lines.append(asp.fact("mischief", prop_id, prop.mischief))
        lines.append(asp.fact("attraction", prop_id, prop.attraction))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for handled in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, handled))
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
        asp.fact("chosen_prop", params.prop),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(7))
        sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magic frolic, a raccoon, and a repeated trick that may turn into comedy."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much of a head start the chaos gets")
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
    if args.prop:
        prop = PROPS[args.prop]
        if not hazard_at_risk(prop):
            raise StoryError(explain_rejection(prop))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.prop is None or c[1] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prop_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        prop=prop_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = PLACES[params.place]
    prop = PROPS[params.prop]
    response = RESPONSES[params.response]

    if not hazard_at_risk(prop):
        raise StoryError(explain_rejection(prop))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        prop_cfg=prop,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prop) combos:\n")
        for place_id, prop_id in combos:
            print(f"  {place_id:10} {prop_id}")
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
            header = f"### {p.child_name}: {p.prop} at {p.place} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
