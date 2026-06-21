#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py
==========================================================================================

A standalone storyworld for a silly rehearsal tale: two children prepare a comic
costume act with an artificial creature, a sloshy cup of koolaid, and one clear
bit of foreshadowing. A careful helper may steer the act into a tiny planned
makeover, or an eager performer may ignore the warning and let the cup hurl
koolaid everywhere. Either way, the plain costume transforms into a bright,
funny stage creature, and the ending image proves the children learned how to
turn a mistake into a joke.

Run it
------
    python storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py
    python storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py --creature robot --move twirl --costume sheet
    python storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py --costume raincoat
    python storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/artificial_hurl_koolaid_foreshadowing_transformation_comedy.py --verify
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
SPILL_THRESHOLD = 3
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    absorbent: bool = False
    wearable: bool = False
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
    plain_name: str
    built_from: str
    pretend_line: str
    transformed_name: str
    crowd_line: str
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
class Container:
    id: str
    label: str
    phrase: str
    spilliness: int
    intro: str
    wobble_text: str
    plural: bool = False
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
class Move:
    id: str
    verb: str
    gerund: str
    force: int
    warning: str
    stunt_line: str
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
class Costume:
    id: str
    label: str
    phrase: str
    absorbent: bool
    splash_text: str
    transformed_text: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_stain(world: World) -> list[str]:
    performer = world.get("performer")
    costume = world.get("costume")
    cup = world.get("drink")
    if cup.meters["spilled"] < THRESHOLD:
        return []
    sig = ("stain", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if costume.absorbent:
        costume.meters["stained"] += 1
        performer.memes["shock"] += 1
        return ["__stain__"]
    return []


def _r_transform(world: World) -> list[str]:
    costume = world.get("costume")
    performer = world.get("performer")
    if costume.meters["stained"] < THRESHOLD:
        return []
    sig = ("transform", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    costume.meters["transformed"] += 1
    performer.memes["embarrassment"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="stain", tag="physical", apply=_r_stain),
    Rule(name="transform", tag="physical", apply=_r_transform),
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


def spill_risk(container: Container, move: Move) -> bool:
    return container.spilliness + move.force >= SPILL_THRESHOLD


def can_transform(costume: Costume) -> bool:
    return costume.absorbent


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for creature_id in CREATURES:
        for container_id, container in CONTAINERS.items():
            for move_id, move in MOVES.items():
                for costume_id, costume in COSTUMES.items():
                    if spill_risk(container, move) and can_transform(costume):
                        combos.append((creature_id, container_id, move_id, costume_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, performer_age: int, helper_age: int, trait: str) -> bool:
    older_helper = relation == "siblings" and helper_age > performer_age
    authority = initial_caution(trait) + (3.0 if older_helper else 0.0)
    return older_helper and authority >= 8.0


def predict_spill(world: World, container_id: str, move_id: str) -> dict:
    sim = world.copy()
    cup = sim.get(container_id)
    costume = sim.get("costume")
    container = CONTAINERS[sim.facts["container_cfg"].id]
    move = MOVES[move_id]
    if spill_risk(container, move):
        cup.meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "will_spill": cup.meters["spilled"] >= THRESHOLD,
        "will_transform": costume.meters["transformed"] >= THRESHOLD,
    }


def setup_stage(world: World, performer: Entity, helper: Entity,
                creature: Creature, costume: Costume, adult: Entity) -> None:
    performer.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On talent-show afternoon, {performer.id} and {helper.id} spread cardboard, tape, "
        f"and a box of markers across the classroom stage."
    )
    world.say(
        f"They were building an artificial {creature.plain_name} {creature.built_from}. "
        f'{creature.pretend_line}'
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled at the busy mess and promised to come back "
        f"when the act was ready."
    )
    world.say(
        f"{performer.id} slipped into {costume.phrase}, which was plain and pale enough to look "
        f"perfectly serious for one funny minute."
    )


def introduce_prop(world: World, performer: Entity, helper: Entity, container: Container,
                   move: Move) -> None:
    world.say(
        f"To make the creature look extra wild, {helper.id} mixed a cup of koolaid and set it in "
        f"{container.phrase}. {container.intro}"
    )
    world.say(
        f'"When I {move.verb}, it will look like the creature is roaring berry fire!" '
        f"{performer.id} said."
    )


def foreshadow(world: World, helper: Entity, performer: Entity, move: Move, container: Container,
               relation: str) -> None:
    pred = predict_spill(world, "drink", move.id)
    helper.memes["caution"] += 1
    world.facts["predicted_spill"] = pred["will_spill"]
    world.facts["predicted_transform"] = pred["will_transform"]
    relation_note = ""
    if relation == "siblings" and helper.age > performer.age:
        relation_note = f" As the older sibling, {helper.id} sounded very sure."
    world.say(
        f"{helper.id} looked at the cup and frowned. "
        f'"That {container.label} is wobbling. If you {move.warning}, it might hurl koolaid."'
        f"{relation_note}"
    )


def defy(world: World, performer: Entity, helper: Entity, move: Move) -> None:
    performer.memes["defiance"] += 1
    world.say(
        f'{performer.id} grinned at {helper.id}. "That will make it funnier," '
        f"{performer.pronoun()} said."
    )
    world.say(move.stunt_line)


def back_down(world: World, performer: Entity, helper: Entity, creature: Creature,
              costume: Costume, container: Container) -> None:
    performer.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{performer.id} stopped in the middle of the pose and looked again at the wobbling cup."
    )
    world.say(
        f'"Okay," {performer.pronoun()} admitted. "Maybe I do not need the whole {container.label} '
        f'flying through the air."'
    )
    world.say(
        f"Instead, {helper.id} dipped one finger into the koolaid and dotted a few careful swirls "
        f"across the {costume.label}. Even that tiny touch began to transform the artificial "
        f"{creature.plain_name} into {creature.transformed_name}."
    )
    costume_ent = world.get("costume")
    costume_ent.meters["stained"] += 1
    propagate(world, narrate=False)


def spill(world: World, performer: Entity, creature: Creature, costume: Costume,
          container: Container, move: Move) -> None:
    cup = world.get("drink")
    cup.meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{performer.id} {move.gerund} once, then twice. On the third beat, the {container.label} "
        f"tipped and hurl seemed like exactly the right word for what happened next."
    )
    world.say(
        f"Koolaid flew in a bright arc and {costume.splash_text}. In one sticky blink, the "
        f"artificial {creature.plain_name} stopped looking stern and started looking like "
        f"{creature.transformed_name}."
    )


def embarrassment(world: World, performer: Entity, helper: Entity) -> None:
    performer.memes["embarrassment"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"{performer.id} froze with a pink drip on {performer.pronoun('possessive')} nose, and "
        f"{helper.id} made a tiny squeak that sounded almost like a laugh trying to be polite."
    )


def recovery(world: World, adult: Entity, performer: Entity, helper: Entity,
             creature: Creature, costume: Costume, outcome: str) -> None:
    performer.memes["joy"] += 1
    helper.memes["joy"] += 1
    performer.memes["embarrassment"] = 0.0
    helper.memes["caution"] = 0.0
    costume_ent = world.get("costume")
    costume_ent.meters["decorated"] += 1
    if outcome == "averted":
        world.say(
            f"{adult.label_word.capitalize()} came back just then, studied the berry swirls, and "
            f"laughed. \"Now that looks deliberate,\" {adult.pronoun()} said."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} came back just then, saw the splash, and put one hand "
            f"over {adult.pronoun('possessive')} smile. \"Well,\" {adult.pronoun()} said, "
            f"\"that certainly woke the costume up.\""
        )
    world.say(
        f"{adult.pronoun().capitalize()} added paper stars, two giant eyebrows, and a cardboard sign "
        f"that read {creature.crowd_line}. Soon {costume.transformed_text}."
    )
    world.say(
        f"When the curtain opened, the audience giggled first and then clapped harder than anyone "
        f"expected."
    )
    world.say(
        f"{performer.id} bowed beside {helper.id}, and the new creature looked so cheerfully strange "
        f"that even the sticky koolaid smell felt like part of the joke."
    )


def tell(creature: Creature, container: Container, move: Move, costume: Costume,
         performer_name: str = "Milo", performer_gender: str = "boy",
         helper_name: str = "Nia", helper_gender: str = "girl",
         adult_type: str = "teacher", helper_trait: str = "careful",
         relation: str = "siblings", performer_age: int = 5, helper_age: int = 7) -> World:
    world = World()
    performer = world.add(Entity(
        id=performer_name,
        kind="character",
        type=performer_gender,
        label=performer_name,
        role="performer",
        age=performer_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=[helper_trait],
        age=helper_age,
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))
    world.add(Entity(
        id="costume",
        kind="thing",
        type="costume",
        label=costume.label,
        absorbent=costume.absorbent,
        wearable=True,
        worn_by=performer.id,
    ))
    world.add(Entity(
        id="drink",
        kind="thing",
        type="drink",
        label=container.label,
        carried_by=helper.id,
    ))

    performer.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    helper.memes["caution"] = initial_caution(helper_trait)
    performer.memes["defiance"] = 0.0
    performer.memes["embarrassment"] = 0.0
    world.facts["creature_cfg"] = creature
    world.facts["container_cfg"] = container
    world.facts["move_cfg"] = move
    world.facts["costume_cfg"] = costume
    world.facts["relation"] = relation

    setup_stage(world, performer, helper, creature, costume, adult)
    world.para()
    introduce_prop(world, performer, helper, container, move)
    foreshadow(world, helper, performer, move, container, relation)

    averted = would_avert(relation, performer_age, helper_age, helper_trait)

    world.para()
    if averted:
        back_down(world, performer, helper, creature, costume, container)
        outcome = "averted"
    else:
        defy(world, performer, helper, move)
        spill(world, performer, creature, costume, container, move)
        embarrassment(world, performer, helper)
        outcome = "spilled"

    world.para()
    recovery(world, adult, performer, helper, creature, costume, outcome)

    world.facts.update(
        performer=performer,
        helper=helper,
        adult=adult,
        creature=creature,
        container=container,
        move=move,
        costume=costume,
        outcome=outcome,
        transformed=world.get("costume").meters["transformed"] >= THRESHOLD,
        spilled=world.get("drink").meters["spilled"] >= THRESHOLD,
    )
    return world


CREATURES = {
    "robot": Creature(
        id="robot",
        plain_name="robot",
        built_from="out of silver cereal boxes and spoon-shaped ears",
        pretend_line='"Behold," said the children, "the most artificial robot in the whole school."',
        transformed_name="a raspberry robot with opera eyebrows",
        crowd_line='"BEEP-BLOOP BERRY MODE"',
        tags={"artificial", "robot", "transformation"},
    ),
    "dragon": Creature(
        id="dragon",
        plain_name="dragon",
        built_from="from cardboard scales and a floppy tail made from paper loops",
        pretend_line='"If it stomps, the curtains will tremble," they whispered, even though the tail kept folding over.',
        transformed_name="a fruit-punch dragon with grand stage manners",
        crowd_line='"ROYAL JUICE DRAGON"',
        tags={"artificial", "dragon", "transformation"},
    ),
    "monster": Creature(
        id="monster",
        plain_name="monster",
        built_from="with two tennis-ball eyes and knees that squeaked when it walked",
        pretend_line='"It is fearsome," they declared, though one eye was looking at the ceiling.',
        transformed_name="a cherry monster in party colors",
        crowd_line='"TICKLE MONSTER DELUXE"',
        tags={"artificial", "monster", "transformation"},
    ),
}

CONTAINERS = {
    "paper_cup": Container(
        id="paper_cup",
        label="paper cup",
        phrase="a tall paper cup",
        spilliness=2,
        intro="It looked dramatic, but it also leaned to one side like it was thinking dangerous thoughts.",
        wobble_text="leaned to one side",
        tags={"koolaid", "cup", "spill"},
    ),
    "loose_lid": Container(
        id="loose_lid",
        label="loose-lidded shaker",
        phrase="a loose-lidded shaker bottle",
        spilliness=2,
        intro="The lid clicked down with a sound that was not nearly as confident as anyone wanted.",
        wobble_text="clicked in a doubtful way",
        tags={"koolaid", "shaker", "spill"},
    ),
    "wobbly_pitcher": Container(
        id="wobbly_pitcher",
        label="wobbly pitcher",
        phrase="a little plastic pitcher with no handle",
        spilliness=3,
        intro="It was bright and cheerful and almost impossible to swing without a slosh.",
        wobble_text="sloshes at every step",
        tags={"koolaid", "pitcher", "spill"},
    ),
}

MOVES = {
    "twirl": Move(
        id="twirl",
        verb="twirl in a circle",
        gerund="twirled",
        force=2,
        warning="twirl that hard",
        stunt_line="Then the rehearsal music started, and the twirl seemed too tempting to resist.",
        tags={"comedy", "movement"},
    ),
    "hop": Move(
        id="hop",
        verb="hop across the stage",
        gerund="hopped",
        force=1,
        warning="hop that fast",
        stunt_line="The beat bounced in the speaker, and soon the whole costume was hopping with it.",
        tags={"comedy", "movement"},
    ),
    "moonwalk": Move(
        id="moonwalk backward",
        verb="moonwalk backward",
        gerund="moonwalked",
        force=2,
        warning="moonwalk backward with your knees that loose",
        stunt_line="The silver shoes slid, the cardboard tail wiggled, and backward suddenly felt like the funniest direction.",
        tags={"comedy", "movement"},
    ),
    "bow": Move(
        id="bow",
        verb="take a huge bow",
        gerund="bowed",
        force=1,
        warning="bow that low",
        stunt_line="The rehearsal needed a grand ending, and the bow grew bigger and bigger until it became a stunt.",
        tags={"comedy", "movement"},
    ),
}

COSTUMES = {
    "sheet": Costume(
        id="sheet",
        label="sheet costume",
        phrase="a white sheet costume with eye holes cut a little crooked",
        absorbent=True,
        splash_text="splashed all over the white cloth",
        transformed_text="the sheet had become a bright, blotchy masterpiece instead of a plain costume",
        tags={"costume", "cloth", "stain"},
    ),
    "apron": Costume(
        id="apron",
        label="apron cape",
        phrase="a long white apron worn backward like a cape",
        absorbent=True,
        splash_text="ran down the apron in zigzags and dots",
        transformed_text="the apron cape looked like a parade banner for a very silly king",
        tags={"costume", "cloth", "stain"},
    ),
    "towel": Costume(
        id="towel",
        label="towel robe",
        phrase="a fluffy white towel robe clipped at the shoulders",
        absorbent=True,
        splash_text="soaked into the towel and puffed up the pink patches",
        transformed_text="the towel robe looked like a fancy berry cloud with legs",
        tags={"costume", "cloth", "stain"},
    ),
    "raincoat": Costume(
        id="raincoat",
        label="raincoat costume",
        phrase="a shiny white raincoat with paper spikes taped on",
        absorbent=False,
        splash_text="beaded up and rolled right off the plastic",
        transformed_text="the raincoat still looked nearly the same",
        tags={"costume", "plastic"},
    ),
}

HELPER_TRAITS = ["careful", "cautious", "sensible", "steady", "curious", "playful"]
GIRL_NAMES = ["Nia", "Lila", "Maya", "Zoe", "Ella", "Ruby", "Ivy", "Tess"]
BOY_NAMES = ["Milo", "Owen", "Ben", "Theo", "Finn", "Leo", "Max", "Jude"]


@dataclass
class StoryParams:
    creature: str
    container: str
    move: str
    costume: str
    performer: str
    performer_gender: str
    helper: str
    helper_gender: str
    adult: str
    helper_trait: str
    relation: str = "siblings"
    performer_age: int = 5
    helper_age: int = 7
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
    "artificial": [
        (
            "What does artificial mean?",
            "Artificial means made by people instead of growing or happening naturally. An artificial dragon costume is pretend, even if it looks exciting."
        )
    ],
    "koolaid": [
        (
            "What is koolaid?",
            "Koolaid is a sweet drink mix that turns water bright colors and flavors. Because it is colorful, it can leave stains if it spills."
        )
    ],
    "spill": [
        (
            "Why do drinks spill when you move too fast?",
            "A drink keeps sloshing after your hand moves. If the cup tips or wobbles too much, the liquid can fly out."
        )
    ],
    "stain": [
        (
            "Why does white cloth show stains so easily?",
            "White cloth has no dark color to hide splashes. Bright drinks stand out right away, so every drip is easy to see."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a story?",
            "A transformation is when something changes into a new form or seems completely different. It can be magical or just a big change in how it looks."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a clue that hints about something that will happen later. A warning about a wobbly cup can prepare you for a coming spill."
        )
    ],
}
KNOWLEDGE_ORDER = ["artificial", "koolaid", "spill", "stain", "transformation", "foreshadowing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    performer = f["performer"]
    helper = f["helper"]
    creature = f["creature"]
    move = f["move"]
    container = f["container"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny story for a 3-to-5-year-old that includes the words "artificial", "hurl", and "koolaid". Use foreshadowing when one child warns another about a wobbly cup.',
            f"Tell a comedy where {performer.id} almost makes an artificial {creature.plain_name} act go wrong, but {helper.id} spots the problem and the costume still transforms in a safe, silly way.",
            f"Write a gentle rehearsal story where a child listens to an older sibling's warning, avoids a big splash, and turns a plain costume into a joke everyone loves.",
        ]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "artificial", "hurl", and "koolaid". Use foreshadowing before the big comic accident.',
        f"Tell a comedy where {performer.id} is rehearsing as an artificial {creature.plain_name}, ignores a warning, and a wobbling {container.label} hurls koolaid during a {move.id}.",
        f"Write a simple transformation story where a costume accident becomes the best part of the show and the ending image is full of laughter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer = f["performer"]
    helper = f["helper"]
    adult = f["adult"]
    creature = f["creature"]
    move = f["move"]
    container = f["container"]
    costume = f["costume"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {performer.id} and {helper.id}, who were getting ready for a talent show with an artificial {creature.plain_name}. A grown-up came back later and helped them turn the surprise into part of the act."
        ),
        (
            f"What was the children’s plan at the beginning?",
            f"They wanted to perform as an artificial {creature.plain_name} and use koolaid as a silly stage effect. The plain {costume.label} was supposed to make the creature look serious before the joke landed."
        ),
        (
            f"How did the story use foreshadowing?",
            f"{helper.id} noticed that the {container.label} was wobbling and warned that it might hurl koolaid if {performer.id} moved too hard. That warning hinted at the big change that came later."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Did the cup really spill everywhere?",
                f"No. {performer.id} listened before the worst happened, so there was no wild hurl across the stage. Instead, they used a few careful drops to transform the costume on purpose."
            )
        )
        qa.append(
            (
                "How did the costume transform?",
                f"The plain costume changed because a little koolaid was dabbed onto the cloth in swirls and spots. That made the artificial {creature.plain_name} look funny and new without a giant mess."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {performer.id} did the big move?",
                f"The {container.label} tipped and hurl was the best word for the splash that followed. Koolaid flew onto the {costume.label}, and the stain transformed the artificial {creature.plain_name} into something much sillier."
            )
        )
        qa.append(
            (
                f"How did {performer.id} feel after the spill?",
                f"At first {performer.id} felt frozen and embarrassed because the koolaid was on the costume and even on {performer.pronoun('possessive')} nose. Then the grown-up helped turn the accident into a joke, so the feeling changed into relief and pride."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the audience laughing and clapping at the transformed creature. The children bowed together, and the new look proved that the accident had become part of the comedy."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"artificial", "koolaid", "spill", "transformation", "foreshadowing"}
    if world.facts["costume"].id in {"sheet", "apron", "towel"}:
        tags.add("stain")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.absorbent:
            bits.append("absorbent=True")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(container: Container, move: Move, costume: Costume) -> str:
    if not costume.absorbent:
        return (
            f"(No story: {costume.label} is shiny and non-absorbent, so koolaid would roll off instead of causing a visible transformation. "
            f"Pick a cloth costume like {COSTUMES['sheet'].label} or {COSTUMES['towel'].label}.)"
        )
    return (
        f"(No story: a {container.label} plus the move '{move.id}' would not honestly be sloshy enough to hurl koolaid. "
        f"Choose a riskier move or a wobblier container so the foreshadowed accident can really happen.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(
        params.relation,
        params.performer_age,
        params.helper_age,
        params.helper_trait,
    ) else "spilled"


ASP_RULES = r"""
hazard(Cn, Mv) :- container(Cn), move(Mv), spilliness(Cn, S), force(Mv, F), spill_threshold(T), S + F >= T.
transformable(Cs) :- costume(Cs), absorbent(Cs).
valid(Cr, Cn, Mv, Cs) :- creature(Cr), hazard(Cn, Mv), transformable(Cs).

cautious_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_helper :- relation(siblings), helper_age(H), performer_age(P), H > P.
authority(C + B) :- init_caution(C), older_helper, B = 3.
averted :- older_helper, authority(A), A >= 8.
outcome(averted) :- averted.
outcome(spilled) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("spilliness", cid, container.spilliness))
    for mid, move in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("force", mid, move.force))
    for cid, costume in COSTUMES.items():
        lines.append(asp.fact("costume", cid))
        if costume.absorbent:
            lines.append(asp.fact("absorbent", cid))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("spill_threshold", SPILL_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("performer_age", params.performer_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.helper_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        creature="robot",
        container="paper_cup",
        move="twirl",
        costume="sheet",
        performer="Milo",
        performer_gender="boy",
        helper="Nia",
        helper_gender="girl",
        adult="teacher",
        helper_trait="careful",
        relation="siblings",
        performer_age=5,
        helper_age=7,
    ),
    StoryParams(
        creature="dragon",
        container="loose_lid",
        move="moonwalk",
        costume="apron",
        performer="Ella",
        performer_gender="girl",
        helper="Ben",
        helper_gender="boy",
        adult="teacher",
        helper_trait="curious",
        relation="friends",
        performer_age=6,
        helper_age=6,
    ),
    StoryParams(
        creature="monster",
        container="wobbly_pitcher",
        move="bow",
        costume="towel",
        performer="Theo",
        performer_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        adult="teacher",
        helper_trait="steady",
        relation="siblings",
        performer_age=4,
        helper_age=8,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an artificial costume act, a foreshadowed koolaid spill, and a comic transformation."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--adult", choices=["teacher", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and args.move and args.costume:
        container = CONTAINERS[args.container]
        move = MOVES[args.move]
        costume = COSTUMES[args.costume]
        if not (spill_risk(container, move) and can_transform(costume)):
            raise StoryError(explain_rejection(container, move, costume))
    if args.costume and not COSTUMES[args.costume].absorbent:
        container = CONTAINERS[args.container] if args.container else next(iter(CONTAINERS.values()))
        move = MOVES[args.move] if args.move else next(iter(MOVES.values()))
        raise StoryError(explain_rejection(container, move, COSTUMES[args.costume]))

    combos = [
        combo for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.container is None or combo[1] == args.container)
        and (args.move is None or combo[2] == args.move)
        and (args.costume is None or combo[3] == args.costume)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, container_id, move_id, costume_id = rng.choice(sorted(combos))
    performer_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    performer = _pick_name(rng, performer_gender)
    helper = _pick_name(rng, helper_gender, avoid=performer)
    adult = args.adult or "teacher"
    helper_trait = rng.choice(HELPER_TRAITS)
    relation = rng.choice(["siblings", "friends"])
    performer_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        creature=creature_id,
        container=container_id,
        move=move_id,
        costume=costume_id,
        performer=performer,
        performer_gender=performer_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        helper_trait=helper_trait,
        relation=relation,
        performer_age=performer_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        creature = CREATURES[params.creature]
        container = CONTAINERS[params.container]
        move = MOVES[params.move]
        costume = COSTUMES[params.costume]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not spill_risk(container, move):
        raise StoryError(explain_rejection(container, move, costume))
    if not can_transform(costume):
        raise StoryError(explain_rejection(container, move, costume))

    world = tell(
        creature=creature,
        container=container,
        move=move,
        costume=costume,
        performer_name=params.performer,
        performer_gender=params.performer_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        helper_trait=params.helper_trait,
        relation=params.relation,
        performer_age=params.performer_age,
        helper_age=params.helper_age,
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome predictions differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: generation smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} compatible (creature, container, move, costume) combos:\n")
        for creature, container, move, costume in combos:
            print(f"  {creature:8} {container:14} {move:10} {costume}")
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
            header = (
                f"### {sample.params.performer} & {sample.params.helper}: "
                f"{sample.params.creature}, {sample.params.container}, {sample.params.move}, "
                f"{outcome_of(sample.params)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
