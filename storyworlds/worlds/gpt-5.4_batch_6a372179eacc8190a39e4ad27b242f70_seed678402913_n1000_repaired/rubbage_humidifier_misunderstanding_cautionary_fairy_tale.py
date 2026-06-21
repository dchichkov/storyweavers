#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py
========================================================================================

A standalone storyworld for a cautionary fairy-tale misunderstanding:
a child sees a humming humidifier making mist, mistakes it for a magical little
creature, and tries to feed it "rubbage." A wiser helper or calm grown-up turns
the misunderstanding into a lesson: machines are helped the right way, not with
scraps and guesses.

The world model tracks:
- typed entities with physical meters and emotional memes
- a small causal engine: debris in the humidifier -> sputter -> spill/work
- a reasonableness gate over compatible misreadings and hazardous offerings
- an inline ASP twin for valid combinations and ending parity

Run it
------
python storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py
python storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/rubbage_humidifier_misunderstanding_cautionary_fairy_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
WISE_TRAITS = {"careful", "wise", "patient", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    opening: str
    shelf: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HumidifierCfg:
    id: str
    label: str
    phrase: str
    shape: str
    glow: str
    song: str
    where: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misread:
    id: str
    sees_as: str
    name_for_it: str
    hunger_line: str
    fix_line: str
    compatible_shapes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    material: str
    source: str
    debris: bool = True
    clog: int = 1
    soggy: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    failure: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    realm: str
    humidifier: str
    misread: str
    offering: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    helper_trait: str
    relation: str = "siblings"
    child_age: int = 5
    helper_age: int = 7
    trust: int = 6
    delay: int = 0
    seed: Optional[int] = None


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


def _r_sputter(world: World) -> list[str]:
    humid = world.get("humidifier")
    if humid.meters["clog"] < THRESHOLD:
        return []
    sig = ("sputter",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    humid.meters["mist"] = 0.0
    humid.meters["noise"] += 1
    world.get("room").meters["worry"] += 1
    world.get("child").memes["fear"] += 1
    return ["__sputter__"]


def _r_spill(world: World) -> list[str]:
    humid = world.get("humidifier")
    if humid.meters["clog"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("floor").meters["wet"] += 1
    world.get("parent").meters["work"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="sputter", tag="physical", apply=_r_sputter),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            if sent == "__sputter__":
                world.say(
                    "At once the little machine gave a worried cough. Its silver mist broke apart, and the humming song turned into a sputter."
                )
            elif sent == "__spill__":
                world.say(
                    "A bead of water slipped from its mouth, then another, until a dark little puddle spread over the floorboards."
                )
    return produced


REALMS = {
    "moon_cottage": Realm(
        id="moon_cottage",
        place="a moonlit cottage room",
        opening="Once, in a moonlit cottage at the edge of a sleepy wood,",
        shelf="on the high painted shelf beside the bed",
        ending="the room looked peaceful again, as if the moon itself had tucked it in",
        tags={"cottage", "night"},
    ),
    "moss_house": Realm(
        id="moss_house",
        place="a moss-roofed house",
        opening="Long ago, in a moss-roofed house where dew pearled on every window,",
        shelf="on a round stool near the window",
        ending="the small house breathed softly and safely through the night",
        tags={"house", "night"},
    ),
    "thorn_tower": Realm(
        id="thorn_tower",
        place="a little nursery in a thorn-vine tower",
        opening="In a little nursery high in a thorn-vine tower,",
        shelf="on a carved chest under the stars",
        ending="the nursery glimmered calmly, gentle as a bedtime spell",
        tags={"tower", "night"},
    ),
}

HUMIDIFIERS = {
    "cloud": HumidifierCfg(
        id="cloud",
        label="humidifier",
        phrase="a cloud-shaped humidifier",
        shape="cloud",
        glow="its pearl lamp glowed like a moon-drop",
        song="it hummed as softly as a bee in clover",
        where="by the bed",
        tags={"humidifier", "mist", "cloud"},
    ),
    "dragon": HumidifierCfg(
        id="dragon",
        label="humidifier",
        phrase="a dragon-shaped humidifier",
        shape="dragon",
        glow="its tiny amber eye glowed in the dark",
        song="it purred with a warm little whirr",
        where="near the curtain",
        tags={"humidifier", "mist", "dragon"},
    ),
    "teapot": HumidifierCfg(
        id="teapot",
        label="humidifier",
        phrase="a teapot-shaped humidifier",
        shape="teapot",
        glow="its blue light shone on the wall",
        song="it sang with a low sleepy hum",
        where="beside the storybooks",
        tags={"humidifier", "mist", "teapot"},
    ),
}

MISREADS = {
    "cloud_pony": Misread(
        id="cloud_pony",
        sees_as="a tiny cloud pony",
        name_for_it="cloud pony",
        hunger_line="The child thought the silver mist looked like a hungry pony breathing in little puffs.",
        fix_line="Cloud ponies in stories may nibble clover, but a humidifier needs only clean water.",
        compatible_shapes={"cloud"},
        tags={"misunderstanding", "cloud"},
    ),
    "baby_dragon": Misread(
        id="baby_dragon",
        sees_as="a baby dragon",
        name_for_it="baby dragon",
        hunger_line="The child thought the mist was dragon breath, thin and brave and waiting for supper.",
        fix_line="A baby dragon in a fairy tale might eat shiny berries, but a humidifier must never be fed scraps.",
        compatible_shapes={"dragon", "teapot"},
        tags={"misunderstanding", "dragon"},
    ),
    "thirsty_kettle_sprite": Misread(
        id="thirsty_kettle_sprite",
        sees_as="a thirsty kettle sprite",
        name_for_it="kettle sprite",
        hunger_line="The child thought a tiny sprite lived inside, puffing sighs because it wanted help.",
        fix_line="Sprites in tales may whisper for gifts, but a humidifier is a machine and only clean water belongs inside.",
        compatible_shapes={"teapot", "cloud"},
        tags={"misunderstanding", "sprite"},
    ),
}

OFFERINGS = {
    "rubbage": Offering(
        id="rubbage",
        label="rubbage",
        phrase="a little fist of rubbage",
        material="dry scraps",
        source="from the basket where torn paper stars and lint had gathered",
        debris=True,
        clog=2,
        soggy="The rubbage drank up the water, turned to a mushy lump, and blocked the little mouth of the machine.",
        tags={"rubbage", "debris"},
    ),
    "crumbs": Offering(
        id="crumbs",
        label="crumbs",
        phrase="a pinch of cake crumbs",
        material="crumbs",
        source="from a napkin forgotten after supper",
        debris=True,
        clog=1,
        soggy="The crumbs swelled into pale paste inside the water tray.",
        tags={"crumbs", "debris"},
    ),
    "paper_petals": Offering(
        id="paper_petals",
        label="paper petals",
        phrase="a handful of paper petals",
        material="paper bits",
        source="from an old craft box",
        debris=True,
        clog=1,
        soggy="The paper petals sagged, stuck together, and plugged the mist hole.",
        tags={"paper", "debris"},
    ),
    "water": Offering(
        id="water",
        label="water",
        phrase="a spoon of clean water",
        material="water",
        source="from a bedside cup",
        debris=False,
        clog=0,
        soggy="",
        tags={"water"},
    ),
}

RESPONSES = {
    "unplug_rinse": Response(
        id="unplug_rinse",
        sense=3,
        power=3,
        success="unplugged the humidifier at once, tipped out the dirty water, and rinsed every hidden corner before drying the floor",
        failure="unplugged the humidifier and tried to rinse it, but the scraps had already swollen too tightly inside",
        qa_text="unplugged the humidifier, emptied the dirty water, and rinsed it clean",
        tags={"unplug", "clean"},
    ),
    "wipe_outside": Response(
        id="wipe_outside",
        sense=1,
        power=1,
        success="wiped the outside with a cloth and hoped that would be enough",
        failure="wiped the outside with a cloth, but the clog hidden inside kept the machine from working",
        qa_text="only wiped the outside with a cloth",
        tags={"wipe"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Ivy", "Wren"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Rowan", "Owen", "Jules"]
HELPER_TRAITS = ["careful", "wise", "patient", "gentle", "curious"]


def valid_combo(hid: str, mid: str, oid: str) -> bool:
    humid = HUMIDIFIERS[hid]
    misread = MISREADS[mid]
    offer = OFFERINGS[oid]
    return humid.shape in misread.compatible_shapes and offer.debris and offer.clog > 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hid in HUMIDIFIERS:
        for mid in MISREADS:
            for oid in OFFERINGS:
                if valid_combo(hid, mid, oid):
                    combos.append((hid, mid, oid))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def explain_rejection(hid: str, mid: str, oid: str) -> str:
    humid = HUMIDIFIERS[hid]
    misread = MISREADS[mid]
    offer = OFFERINGS[oid]
    if humid.shape not in misread.compatible_shapes:
        return (
            f"(No story: {humid.phrase} does not plausibly look like {misread.sees_as}. "
            f"This misunderstanding needs a shape that could honestly invite that mistake.)"
        )
    if not offer.debris or offer.clog <= 0:
        return (
            f"(No story: giving {offer.label} to a humidifier would not create the cautionary mess this world models. "
            f"Pick debris such as rubbage or crumbs, not clean water.)"
        )
    return "(No story: this combination has no reasonable misunderstanding hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def initial_caution(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_avert(relation: str, child_age: int, helper_age: int, helper_trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > child_age
    authority = initial_caution(helper_trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > BRAVERY_INIT


def severity_of(offering: Offering, delay: int) -> int:
    return offering.clog + delay


def is_contained(response: Response, offering: Offering, delay: int) -> bool:
    return response.power >= severity_of(offering, delay)


def predict_trouble(world: World, offering: Offering) -> dict:
    sim = world.copy()
    _do_feed(sim, offering, narrate=False)
    return {
        "mist_lost": sim.get("humidifier").meters["mist"] < THRESHOLD,
        "floor_wet": sim.get("floor").meters["wet"] >= THRESHOLD,
        "work": sim.get("parent").meters["work"],
    }


def _do_feed(world: World, offering: Offering, narrate: bool = True) -> None:
    humid = world.get("humidifier")
    humid.meters["clog"] += offering.clog
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, realm: Realm, humid: HumidifierCfg) -> None:
    child.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"{realm.opening} {child.id} could not sleep. Across {realm.place}, {humid.phrase} sat {realm.shelf}, and {humid.glow} while {humid.song}."
    )
    world.say(
        f"From its little mouth drifted a silver thread of mist, thin as silk and bright in the moon."
    )


def misunderstanding(world: World, child: Entity, misread: Misread, offering: Offering) -> None:
    child.memes["imagination"] += 1
    world.say(misread.hunger_line)
    world.say(
        f'"Oh," whispered {child.id}, "it is not a machine at all. It is a {misread.name_for_it}, and it must be hungry."'
    )
    world.say(
        f"On the rug nearby lay {offering.phrase} {offering.source}. To {child.id}, it looked like the very sort of supper a tiny enchanted thing might want."
    )


def warning(world: World, helper: Entity, child: Entity, parent: Entity, misread: Misread, offering: Offering) -> None:
    pred = predict_trouble(world, offering)
    world.facts["predicted_floor_wet"] = pred["floor_wet"]
    world.facts["predicted_work"] = pred["work"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} sat up and caught {child.id} reaching. "{child.id}, no," {helper.pronoun()} said softly. '
        f'"That is a humidifier. If rubbage or scraps go inside, the mist stops and the water can spill."'
    )
    if pred["floor_wet"]:
        world.say(
            f"{helper.id} imagined the puddle before it happened and shivered. {misread.fix_line}"
        )


def defy(world: World, child: Entity, helper: Entity) -> None:
    child.memes["defiance"] += 1
    if child.attrs.get("relation") == "siblings" and child.age > helper.age:
        world.say(
            f'"It is only a little supper," {child.id} said, because {child.pronoun()} felt older and bolder just then. Before {helper.id} could stop {child.pronoun("object")}, {child.pronoun()} stretched up on tiptoe.'
        )
    else:
        world.say(
            f'"It is only a little supper," {child.id} said. Still sure of the mistake, {child.pronoun()} stretched up on tiptoe.'
        )


def back_down(world: World, child: Entity, helper: Entity, parent: Entity, humid: HumidifierCfg) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} looked from the silver mist to {helper.id}'s steady face. At last {child.pronoun()} lowered {child.pronoun('possessive')} hand and let the rubbage fall back into the basket."
    )
    world.say(
        f'Together they padded to {parent.label_word}\'s door and whispered what had happened. Soon {parent.label_word} came in smiling, checked the {humid.label}, and praised them for asking before touching.'
    )


def feed_machine(world: World, child: Entity, offering: Offering) -> None:
    _do_feed(world, offering, narrate=True)
    child.memes["fear"] += 1
    world.say(
        f"{child.id} dropped the {offering.label} into the water opening. {offering.soggy}"
    )


def alarm(world: World, helper: Entity, child: Entity, parent: Entity) -> None:
    world.say(
        f'"{helper.id} gasped. "{child.id}, listen!" The sweet hum was gone. "{parent.label_word.capitalize()}!"'
    )


def rescue(world: World, parent: Entity, response: Response) -> None:
    humid = world.get("humidifier")
    humid.meters["clog"] = 0.0
    humid.meters["mist"] = 1.0
    humid.meters["noise"] = 0.0
    world.get("floor").meters["wet"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried in barefoot and {response.success}."
    )
    world.say(
        "In a little while the silver mist returned, quiet and even, as though the room itself had taken a calm breath."
    )


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    humid = world.get("humidifier")
    humid.meters["ruined"] += 1
    humid.meters["mist"] = 0.0
    world.get("floor").meters["wet"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in barefoot and {response.failure}."
    )
    world.say(
        "The poor machine gave one last cough and fell silent. Water had already soaked the mat beneath it."
    )


def lesson(world: World, parent: Entity, child: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f'Then {parent.label_word} knelt and held both children close. "A humidifier is helpful," {parent.pronoun()} said, "but only when we care for it the right way. Only clean water goes inside, and if something seems wrong, you call a grown-up."'
    )
    world.say(
        f'{child.id} nodded hard. "I thought the mist meant it was asking for supper," {child.pronoun()} whispered.'
    )
    world.say(
        f'"I know," said {parent.label_word}. "But not every puff and hum is magic. Sometimes the kindest thing is to understand what a thing really is."'
    )


def grim_lesson(world: World, parent: Entity, child: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["sad"] += 1
    helper.memes["sad"] += 1
    world.say(
        f'{parent.label_word.capitalize()} wrapped the wet cord away from little hands and held the children close. "You are safe, and that matters most," {parent.pronoun()} said, "but a machine can be spoiled when we guess instead of asking."'
    )
    world.say(
        f"{child.id} cried a little, not because of a scolding, but because the quiet room no longer had its silver mist."
    )
    world.say(
        "From that night on, neither child ever fed scraps to a humming thing again."
    )


def safe_ending(world: World, parent: Entity, child: Entity, helper: Entity, realm: Realm) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The next evening, {parent.label_word} set a bowl of water on the table and floated paper moons upon it so the children could pretend at clouds without touching any machine."
    )
    world.say(
        f"{child.id} and {helper.id} watched the moons drift and laughed softly. {realm.ending}."
    )


def sober_ending(world: World, parent: Entity, child: Entity, helper: Entity, realm: Realm) -> None:
    world.say(
        f"The next evening, {parent.label_word} brought a lantern and a storybook instead. {child.id} and {helper.id} sat close together and listened more carefully than before."
    )
    world.say(
        f"Outside, the moon shone on the window, but inside the room felt changed: a little sadder, and a good deal wiser."
    )


def tell(
    realm: Realm,
    humidifier: HumidifierCfg,
    misread: Misread,
    offering: Offering,
    response: Response,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    helper_trait: str,
    relation: str,
    child_age: int,
    helper_age: int,
    trust: int,
    delay: int,
) -> World:
    world = World(realm)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            age=child_age,
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            phrase=helper_name,
            role="helper",
            age=helper_age,
            attrs={"relation": relation, "trust": trust, "trait": helper_trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    humid = world.add(
        Entity(
            id="humidifier",
            type="humidifier",
            label="humidifier",
            phrase=humidifier.phrase,
            tags=set(humidifier.tags),
        )
    )
    room = world.add(Entity(id="room", type="room", label=realm.place))
    floor = world.add(Entity(id="floor", type="floor", label="floorboards"))

    child.memes["bravery"] = BRAVERY_INIT
    helper.memes["caution"] = initial_caution(helper_trait)
    helper.memes["trust"] = float(trust)
    humid.meters["mist"] = 1.0
    humid.meters["water"] = 1.0

    opening(world, child, helper, realm, humidifier)
    misunderstanding(world, child, misread, offering)

    world.para()
    warning(world, helper, child, parent, misread, offering)
    averted = would_avert(relation, child_age, helper_age, helper_trait)

    if averted:
        back_down(world, child, helper, parent, humidifier)
        world.para()
        lesson(world, parent, child, helper)
        safe_ending(world, parent, child, helper, realm)
        outcome = "averted"
    else:
        defy(world, child, helper)
        world.para()
        feed_machine(world, child, offering)
        alarm(world, helper, child, parent)
        world.para()
        contained = is_contained(response, offering, delay)
        if contained:
            rescue(world, parent, response)
            lesson(world, parent, child, helper)
            world.para()
            safe_ending(world, parent, child, helper, realm)
            outcome = "cleaned"
        else:
            rescue_fail(world, parent, response)
            grim_lesson(world, parent, child, helper)
            world.para()
            sober_ending(world, parent, child, helper, realm)
            outcome = "ruined"

    world.facts.update(
        realm=realm,
        humidifier_cfg=humidifier,
        misread=misread,
        offering=offering,
        response=response,
        child=child,
        helper=helper,
        parent=parent,
        outcome=outcome,
        delay=delay,
        relation=relation,
        child_name=child_name,
        helper_name=helper_name,
        trust=trust,
        helper_trait=helper_trait,
        floor_wet=floor.meters["wet"] >= THRESHOLD,
        ruined=humid.meters["ruined"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "humidifier": [
        (
            "What does a humidifier do?",
            "A humidifier puts a gentle mist of water into the air. That can help a room feel less dry.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud of tiny water drops floating in the air. It can look smoky, but it is really just water.",
        )
    ],
    "rubbage": [
        (
            "What is rubbage?",
            "Rubbage is a word in this tale for little scraps and bits of mess, like lint, torn paper, and other tiny rubbish. Those scraps do not belong inside a machine.",
        )
    ],
    "water_only": [
        (
            "Why should only clean water go in a humidifier?",
            "A humidifier is made to use clean water, not crumbs or scraps. Other things can clog it, make it spill, or stop it from working.",
        )
    ],
    "plug": [
        (
            "Why should a grown-up unplug a machine before cleaning it?",
            "Unplugging makes the machine safer to handle while it is being cleaned. It is a careful first step before touching water and parts.",
        )
    ],
    "ask": [
        (
            "What should a child do if a machine makes a strange sound?",
            "The child should leave it alone and tell a grown-up. Asking for help is safer than guessing.",
        )
    ],
    "mistake": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. In stories, that mistake can lead to trouble until someone explains the truth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["humidifier", "mist", "rubbage", "water_only", "plug", "ask", "mistake"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    misread = f["misread"]
    outcome = f["outcome"]
    base = (
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "rubbage" and "humidifier" and centers on a misunderstanding.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle cautionary tale where {child.label} mistakes a humidifier for {misread.sees_as}, but {helper.label} stops the mistake before anything is dropped inside.",
            "Write a bedtime fairy tale in which a child almost feeds rubbage to a humming machine, then learns to ask a grown-up before touching it.",
        ]
    if outcome == "ruined":
        return [
            base,
            f"Tell a cautionary fairy tale where {child.label} feeds rubbage to a humidifier after mistaking it for {misread.sees_as}, and the room ends sadder and wiser.",
            "Write a soft but serious tale about guessing wrong about a machine, causing a soggy mess, and learning that not every puff of mist is magic.",
        ]
    return [
        base,
        f"Tell a fairy-tale cautionary story where {child.label} mistakes a humidifier for {misread.sees_as}, drops rubbage inside, and a calm grown-up fixes the problem.",
        "Write a child-facing bedtime tale where a misunderstanding causes a little indoor mess, and the ending shows a safer way to imagine clouds.",
    ]


def pair_noun(child: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and helper.type == "boy":
            return "two brothers"
        if child.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    humid = f["humidifier_cfg"]
    misread = f["misread"]
    offering = f["offering"]
    response = f["response"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(child, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.label} and {helper.label}, and their {parent.label_word}. The trouble began when they watched a humming {humid.label} in the night.",
        ),
        (
            f"What misunderstanding did {child.label} have?",
            f"{child.label} thought the humidifier was {misread.sees_as}, not a machine. The drifting mist made the mistake feel real.",
        ),
        (
            f"Why did {child.label} pick up the {offering.label}?",
            f"{child.label} believed the little puffs of mist meant the thing was hungry and needed supper. Because of that misunderstanding, the {offering.label} seemed like help instead of harm.",
        ),
        (
            f"What warning did {helper.label} give?",
            f"{helper.label} said the humidifier was not a magical creature and that scraps could stop the mist and make water spill. The warning came from understanding what the machine really was.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What happened after {helper.label} warned {child.label}?",
                f"{child.label} listened and put the rubbage back instead of feeding it to the humidifier. Then the children fetched their {parent.label_word} and learned that asking first is the safer kind of kindness.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with a lesson but no mess. The children played a safe cloud game the next evening, which showed they had changed what they did.",
            )
        )
    elif outcome == "cleaned":
        qa.append(
            (
                f"What happened when the {offering.label} went into the humidifier?",
                f"The humidifier sputtered, the silver mist stopped, and water began to spread on the floor. The scraps clogged the machine and turned a kind mistake into real trouble.",
            )
        )
        qa.append(
            (
                f"How did the {parent.label_word} fix the problem?",
                f"The {parent.label_word} {response.qa_text}. That worked because the real trouble was inside the machine, not just on the outside.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that a humidifier is cared for with clean water and grown-up help, not with rubbage or guesses. They also learned that something can look magical without needing magical treatment.",
            )
        )
    else:
        qa.append(
            (
                "Could the humidifier be saved right away?",
                f"No. By the time the {parent.label_word} tried to help, the soggy scraps had already done too much harm inside. The room stayed safe, but the machine was spoiled and the children felt sad.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in a sober way: nobody was hurt, but the humidifier lost its silver mist and the room felt changed. That sad ending proves why the warning mattered.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"humidifier", "mist", "rubbage", "water_only", "ask", "mistake"}
    if world.facts["outcome"] != "averted":
        tags.add("plug")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        label = e.label or e.id
        lines.append(f"  {e.id:10} ({e.type:10}) {label:18} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="moon_cottage",
        humidifier="dragon",
        misread="baby_dragon",
        offering="rubbage",
        response="unplug_rinse",
        child_name="Finn",
        child_gender="boy",
        helper_name="Elsie",
        helper_gender="girl",
        parent="mother",
        helper_trait="wise",
        relation="siblings",
        child_age=5,
        helper_age=7,
        trust=5,
        delay=0,
    ),
    StoryParams(
        realm="moss_house",
        humidifier="cloud",
        misread="cloud_pony",
        offering="paper_petals",
        response="unplug_rinse",
        child_name="Lina",
        child_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        parent="father",
        helper_trait="careful",
        relation="friends",
        child_age=5,
        helper_age=5,
        trust=4,
        delay=0,
    ),
    StoryParams(
        realm="thorn_tower",
        humidifier="teapot",
        misread="baby_dragon",
        offering="rubbage",
        response="unplug_rinse",
        child_name="Mira",
        child_gender="girl",
        helper_name="Nora",
        helper_gender="girl",
        parent="mother",
        helper_trait="patient",
        relation="siblings",
        child_age=4,
        helper_age=8,
        trust=7,
        delay=0,
    ),
    StoryParams(
        realm="moon_cottage",
        humidifier="teapot",
        misread="thirsty_kettle_sprite",
        offering="crumbs",
        response="unplug_rinse",
        child_name="Theo",
        child_gender="boy",
        helper_name="Rowan",
        helper_gender="boy",
        parent="father",
        helper_trait="gentle",
        relation="friends",
        child_age=6,
        helper_age=6,
        trust=3,
        delay=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.helper_age, params.helper_trait):
        return "averted"
    return "cleaned" if is_contained(RESPONSES[params.response], OFFERINGS[params.offering], params.delay) else "ruined"


ASP_RULES = r"""
valid(H, M, O) :- humidifier(H), misread(M), offering(O), shape(H, S), compatible(M, S), debris(O), clog(O, C), C > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

caution_value(5) :- helper_trait(T), wise_trait(T).
caution_value(3) :- helper_trait(T), not wise_trait(T).
older_helper :- relation(siblings), helper_age(HA), child_age(CA), HA > CA.
bonus(3) :- older_helper.
bonus(0) :- not older_helper.
authority(C + 1 + B) :- caution_value(C), bonus(B).
averted :- older_helper, authority(A), bravery_init(BR), A > BR.

severity(V) :- chosen_offering(O), clog(O, C), delay(D), V = C + D.
resp_power(P) :- chosen_response(R), power(R, P).
cleaned :- not averted, resp_power(P), severity(V), P >= V.
ruined :- not averted, not cleaned.

outcome(averted) :- averted.
outcome(cleaned) :- cleaned.
outcome(ruined) :- ruined.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, humid in HUMIDIFIERS.items():
        lines.append(asp.fact("humidifier", hid))
        lines.append(asp.fact("shape", hid, humid.shape))
    for mid, misread in MISREADS.items():
        lines.append(asp.fact("misread", mid))
        for shape in sorted(misread.compatible_shapes):
            lines.append(asp.fact("compatible", mid, shape))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        if offering.debris:
            lines.append(asp.fact("debris", oid))
        lines.append(asp.fact("clog", oid, offering.clog))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_offering", params.offering),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("helper_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "humidifier" not in sample.story or "rubbage" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing required content.")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="### smoke")
    finally:
        sys.stdout = old
    if not buf.getvalue().strip():
        raise StoryError("Smoke test failed: emit produced no output.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
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
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale storyworld: a child misunderstands a humidifier and learns not to feed it rubbage."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--humidifier", choices=HUMIDIFIERS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the grown-up takes to respond")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.humidifier and args.misread and args.offering:
        if not valid_combo(args.humidifier, args.misread, args.offering):
            raise StoryError(explain_rejection(args.humidifier, args.misread, args.offering))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.humidifier is None or c[0] == args.humidifier)
        and (args.misread is None or c[1] == args.misread)
        and (args.offering is None or c[2] == args.offering)
    ]
    if not combos:
        if args.humidifier and args.misread and args.offering:
            raise StoryError(explain_rejection(args.humidifier, args.misread, args.offering))
        raise StoryError("(No valid combination matches the given options.)")

    humidifier, misread, offering = rng.choice(sorted(combos))
    realm = args.realm or rng.choice(sorted(REALMS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_trait = rng.choice(HELPER_TRAITS)
    relation = rng.choice(["siblings", "friends"])
    child_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(2, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        realm=realm,
        humidifier=humidifier,
        misread=misread,
        offering=offering,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        helper_trait=helper_trait,
        relation=relation,
        child_age=child_age,
        helper_age=helper_age,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"Unknown realm: {params.realm}")
    if params.humidifier not in HUMIDIFIERS:
        raise StoryError(f"Unknown humidifier: {params.humidifier}")
    if params.misread not in MISREADS:
        raise StoryError(f"Unknown misread: {params.misread}")
    if params.offering not in OFFERINGS:
        raise StoryError(f"Unknown offering: {params.offering}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if not valid_combo(params.humidifier, params.misread, params.offering):
        raise StoryError(explain_rejection(params.humidifier, params.misread, params.offering))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        realm=REALMS[params.realm],
        humidifier=HUMIDIFIERS[params.humidifier],
        misread=MISREADS[params.misread],
        offering=OFFERINGS[params.offering],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        helper_trait=params.helper_trait,
        relation=params.relation,
        child_age=params.child_age,
        helper_age=params.helper_age,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (humidifier, misread, offering) combos:\n")
        for humidifier, misread, offering in combos:
            print(f"  {humidifier:10} {misread:20} {offering}")
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
            header = (
                f"### {p.child_name} and {p.helper_name}: {p.misread} / {p.offering} "
                f"({p.humidifier}, {outcome_of(p)})"
            )
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
