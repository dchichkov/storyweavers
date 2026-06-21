#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py
============================================================================

A tiny story world for a humorous breakfast-table whodunit with a harmless
transformation at its center.

Premise
-------
A child detective comes to the table and finds that an ordinary breakfast has
been transformed into a ridiculous creature-face. Someone clearly scrounged up
extra toppings to do it. The detective studies clues, questions a few suspects,
and discovers that the culprit had a gentle reason: usually to prolong breakfast
until someone late can join the fun, or to cheer up a gloomy family member.
The ending image proves what changed: the mystery becomes a shared joke instead
of a worry.

Run it
------
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py --target pancakes --makeover berry_face
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py --target porridge --makeover pretzel_antlers
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py --all
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py --qa --json
python storyworlds/worlds/gpt-5.4/prolong_scrounge_humor_transformation_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "sister", "cousin_girl"}
        male = {"boy", "father", "man", "uncle", "brother", "cousin_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    nook: str
    pantry: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TargetCfg:
    id: str
    label: str
    phrase: str
    surface: str
    room_note: str
    eat_verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Makeover:
    id: str
    label: str
    source: str
    source_phrase: str
    pantry_spot: str
    clue: str
    clue_phrase: str
    look: str
    verb: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    label: str
    reason: str
    confession: str
    ending: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


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

    def suspects(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "suspect"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mystery(world: World) -> list[str]:
    target = world.get("target")
    detective = world.get("detective")
    if target.meters["transformed"] < THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curious"] += 1
    for suspect in world.suspects():
        suspect.memes["attention"] += 1
    world.get("room").meters["mystery"] += 1
    return ["__mystery__"]


def _r_clue_link(world: World) -> list[str]:
    culprit = world.get("culprit")
    detective = world.get("detective")
    target = world.get("target")
    if target.meters["clued"] < THRESHOLD:
        return []
    sig = ("clue_link", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.meters["linked"] += 1
    detective.memes["certainty"] += 1
    culprit.memes["sheepish"] += 1
    return ["__linked__"]


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="clue_link", tag="social", apply=_r_clue_link),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        nook="the breakfast nook by the sunny window",
        pantry="the fruit bowl and the little bread shelf",
        tags={"kitchen"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        nook="the little wicker table near the steps",
        pantry="a picnic basket and a cool tray by the door",
        tags={"porch"},
    ),
    "cabin": Place(
        id="cabin",
        label="the cabin kitchen",
        nook="the pine table under a tiny lamp",
        pantry="a camp crate full of breakfast bits",
        tags={"cabin"},
    ),
}

TARGETS = {
    "pancakes": TargetCfg(
        id="pancakes",
        label="pancakes",
        phrase="a warm stack of pancakes",
        surface="a soft, flat stack",
        room_note="The syrup bottle stood nearby, and the room smelled sweet.",
        eat_verb="cut into",
        tags={"pancakes", "breakfast"},
    ),
    "porridge": TargetCfg(
        id="porridge",
        label="porridge",
        phrase="a round bowl of porridge",
        surface="a smooth bowl top",
        room_note="A spoon rested on the napkin, waiting beside the bowl.",
        eat_verb="stir",
        tags={"porridge", "breakfast"},
    ),
    "rolls": TargetCfg(
        id="rolls",
        label="breakfast rolls",
        phrase="three warm breakfast rolls",
        surface="three puffy little tops",
        room_note="Steam still curled from the basket.",
        eat_verb="pull apart",
        tags={"rolls", "breakfast"},
    ),
}

MAKEOVERS = {
    "berry_face": Makeover(
        id="berry_face",
        label="a berry face",
        source="berries",
        source_phrase="a little cup of berries",
        pantry_spot="the fruit bowl",
        clue="purple smudges and one tiny seed",
        clue_phrase="a purple smudge and a tiny berry seed",
        look="two round berry eyes and a crooked grin",
        verb="dabbed on berry bits",
        fits={"pancakes", "porridge"},
        tags={"berries", "fruit", "face"},
    ),
    "banana_mustache": Makeover(
        id="banana_mustache",
        label="a banana mustache",
        source="banana slices",
        source_phrase="a banana and the small fruit knife",
        pantry_spot="the fruit bowl",
        clue="a yellow peel curl",
        clue_phrase="a yellow curl of peel",
        look="a grand yellow mustache under raisin eyes",
        verb="laid down banana slices",
        fits={"pancakes", "rolls"},
        tags={"banana", "fruit", "mustache"},
    ),
    "pretzel_antlers": Makeover(
        id="pretzel_antlers",
        label="pretzel antlers",
        source="pretzels",
        source_phrase="a handful of pretzels",
        pantry_spot="the snack tin",
        clue="a sprinkle of salt crystals",
        clue_phrase="a sparkle of salt",
        look="two crunchy antlers and a proud little face",
        verb="stuck on pretzels",
        fits={"rolls"},
        tags={"pretzel", "salt", "antlers"},
    ),
    "cocoa_hair": Makeover(
        id="cocoa_hair",
        label="cocoa hair",
        source="cocoa powder",
        source_phrase="the cocoa shaker",
        pantry_spot="the shelf by the mugs",
        clue="a brown dusting on the table edge",
        clue_phrase="a brown dusting on the table edge",
        look="wild fuzzy hair with marshmallow teeth",
        verb="shook on cocoa powder",
        fits={"porridge", "pancakes"},
        tags={"cocoa", "marshmallow", "hair"},
    ),
}

MOTIVES = {
    "prolong_wait": Motive(
        id="prolong_wait",
        label="to prolong breakfast",
        reason="the culprit wanted to prolong breakfast until a sleepy family member could reach the table",
        confession='\"I only wanted to prolong breakfast,\" the culprit admitted. \"I thought a silly face would keep everyone guessing for one more minute.\"',
        ending="No one hurried after that. They waited together, grinning at the ridiculous breakfast creature.",
        gentle=True,
        tags={"waiting", "family"},
    ),
    "cheer_up": Motive(
        id="cheer_up",
        label="to cheer someone up",
        reason="the culprit had noticed a gloomy face and wanted to turn breakfast into a joke",
        confession='\"I was trying to make someone laugh,\" the culprit admitted. \"A banana mustache felt funnier than a sad morning.\"',
        ending="The gloomy feeling melted away, and even the spoons seemed to ring more brightly against the bowls.",
        gentle=True,
        tags={"feelings", "kindness"},
    ),
    "celebrate": Motive(
        id="celebrate",
        label="to make breakfast feel special",
        reason="the culprit wanted an ordinary meal to look like a tiny party",
        confession='\"It looked too plain,\" the culprit admitted. \"I wanted breakfast to come in wearing its party face.\"',
        ending="Soon the table looked like a parade of silly little foods, and nobody minded the delay.",
        gentle=True,
        tags={"celebration", "party"},
    ),
}

SUSPECT_ROLES = {
    "sibling": {"label": "older sibling", "types": ["girl", "boy"]},
    "cousin": {"label": "cousin", "types": ["cousin_girl", "cousin_boy"]},
    "parent": {"label": "grown-up helper", "types": ["mother", "father"]},
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def makeover_fits(target_id: str, makeover_id: str) -> bool:
    return target_id in MAKEOVERS[makeover_id].fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for target_id in TARGETS:
            for makeover_id in MAKEOVERS:
                if makeover_fits(target_id, makeover_id):
                    combos.append((place_id, target_id, makeover_id))
    return combos


@dataclass
class StoryParams:
    place: str
    target: str
    makeover: str
    motive: str
    detective: str
    detective_gender: str
    culprit: str
    culprit_gender: str
    culprit_role: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="kitchen",
        target="pancakes",
        makeover="berry_face",
        motive="prolong_wait",
        detective="Lily",
        detective_gender="girl",
        culprit="Tom",
        culprit_gender="boy",
        culprit_role="sibling",
        helper="Mom",
        helper_gender="mother",
        seed=1,
    ),
    StoryParams(
        place="porch",
        target="rolls",
        makeover="banana_mustache",
        motive="cheer_up",
        detective="Ben",
        detective_gender="boy",
        culprit="Maya",
        culprit_gender="girl",
        culprit_role="cousin",
        helper="Dad",
        helper_gender="father",
        seed=2,
    ),
    StoryParams(
        place="cabin",
        target="porridge",
        makeover="cocoa_hair",
        motive="celebrate",
        detective="Zoe",
        detective_gender="girl",
        culprit="Aunt June",
        culprit_gender="aunt",
        culprit_role="parent",
        helper="Max",
        helper_gender="boy",
        seed=3,
    ),
    StoryParams(
        place="kitchen",
        target="rolls",
        makeover="pretzel_antlers",
        motive="prolong_wait",
        detective="Theo",
        detective_gender="boy",
        culprit="Lucy",
        culprit_gender="girl",
        culprit_role="sibling",
        helper="Dad",
        helper_gender="father",
        seed=4,
    ),
]


def explain_rejection(target_id: str, makeover_id: str) -> str:
    target = TARGETS[target_id]
    makeover = MAKEOVERS[makeover_id]
    return (
        f"(No story: {makeover.label} does not fit {target.phrase}. "
        f"The transformed breakfast has to make visual sense, and {target.label} "
        f"does not give enough shape for {makeover.look}.)"
    )


def build_character(name: str, kind_type: str, role: str) -> Entity:
    return Entity(id=name, kind="character", type=kind_type, role=role, label=name)


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    if gender in {"girl", "mother", "aunt", "cousin_girl"}:
        pool = [n for n in GIRL_NAMES if n not in avoid]
        if gender == "mother":
            pool = [n for n in ["Mom", "Mama", "Mother"] if n not in avoid] or pool
        if gender == "aunt":
            pool = [n for n in ["Aunt June", "Aunt May"] if n not in avoid] or pool
    else:
        pool = [n for n in BOY_NAMES if n not in avoid]
        if gender == "father":
            pool = [n for n in ["Dad", "Papa", "Father"] if n not in avoid] or pool
    return rng.choice(pool)


def introduce(world: World, detective: Entity, helper: Entity, place: Place, target: TargetCfg) -> None:
    detective.memes["calm"] += 1
    world.say(
        f"On a bright morning in {place.label}, {detective.id} padded into {place.nook} "
        f"expecting {target.phrase}. {target.room_note}"
    )
    world.say(
        f"{helper.id} was humming nearby, and the whole breakfast looked ordinary for exactly one blink."
    )


def discover(world: World, detective: Entity, target_ent: Entity, target: TargetCfg, makeover: Makeover) -> None:
    target_ent.meters["transformed"] += 1
    target_ent.meters["funny"] += 1
    target_ent.meters["clued"] += 1
    propagate(world, narrate=False)
    detective.memes["surprise"] += 1
    world.say(
        f"Then {detective.id} gasped. The {target.label} had been transformed into {makeover.label}: "
        f"{makeover.look} where a plain breakfast should have been."
    )
    world.say(
        f"\"A breakfast mystery!\" {detective.id} whispered. \"Someone must have scrounged up "
        f"{makeover.source} from {makeover.pantry_spot}.\""
    )


def inspect_scene(world: World, detective: Entity, makeover: Makeover, place: Place) -> None:
    detective.memes["curious"] += 1
    world.say(
        f"{detective.id} leaned close and found {makeover.clue_phrase} by the plate. "
        f"That was clue number one."
    )
    world.say(
        f"Clue number two waited near {place.pantry}: the place where someone could have quietly found "
        f"{makeover.source_phrase}."
    )


def question_suspects(world: World, detective: Entity, suspects: list[Entity], culprit: Entity, motive: Motive) -> None:
    lines: list[str] = []
    for suspect in suspects:
        if suspect.id == culprit.id:
            suspect.memes["nervous"] += 1
            line = (
                f"{suspect.id} tried to look very busy and said, "
                f"\"Me? I was only helping.\""
            )
        else:
            suspect.memes["calm"] += 1
            line = (
                f"{suspect.id} blinked and said, "
                f"\"I didn't touch the breakfast. I only came to see what smelled so good.\""
            )
        lines.append(line)
    world.say(
        f"{detective.id} put on a serious detective face and questioned everyone at the table. "
        + " ".join(lines)
    )
    if motive.id == "prolong_wait":
        world.say(
            "One chair was still empty, which made the mystery feel even bigger. "
            "Why would anyone want to prolong breakfast instead of start eating?"
        )


def deduce(world: World, detective: Entity, culprit: Entity, makeover: Makeover) -> None:
    propagate(world, narrate=False)
    culprit.meters["linked"] += 1
    detective.memes["certainty"] += 1
    culprit.memes["sheepish"] += 1
    world.say(
        f"Then {detective.id} noticed the same clue again: {makeover.clue}. "
        f"It matched a tiny mark on {culprit.id}'s hand."
    )
    world.say(
        f"\"Aha!\" cried {detective.id}. \"The clues point to {culprit.id}. "
        f"You were the one who {makeover.verb}!\""
    )


def reveal(world: World, culprit: Entity, motive: Motive) -> None:
    culprit.memes["relief"] += 1
    world.say(motive.confession)
    world.say(
        f"{culprit.id} gave a small shrug that was half apology and half laugh."
    )


def repair(world: World, helper: Entity, target_ent: Entity, target: TargetCfg, makeover: Makeover) -> None:
    helper.memes["calm"] += 1
    target_ent.meters["shared"] += 1
    world.say(
        f"{helper.id} looked at the silly {target.label} and laughed so hard that a chair squeaked. "
        f"\"This is the gentlest mystery I have ever seen,\" {helper.pronoun()} said."
    )
    if makeover.id == "pretzel_antlers":
        world.say(
            f"Instead of scolding, {helper.id} set the pretzel antlers neatly back in place and "
            f"helped everyone {target.eat_verb} the rest."
        )
    else:
        world.say(
            f"Instead of scolding, {helper.id} straightened the funny face and helped everyone "
            f"{target.eat_verb} breakfast before it grew cold."
        )


def close_case(world: World, detective: Entity, culprit: Entity, motive: Motive, target: TargetCfg) -> None:
    detective.memes["joy"] += 1
    culprit.memes["joy"] += 1
    target_ent = world.get("target")
    target_ent.meters["mystery_solved"] += 1
    world.say(
        f"{detective.id} bowed to the table and declared, "
        f"\"Case solved. The culprit was kind, the clues were delicious, and the breakfast may now be eaten.\""
    )
    world.say(motive.ending)
    world.say(
        f"Soon the whole table was giggling, and even the once-suspicious {target.label} looked less like evidence "
        f"and more like breakfast again."
    )


def tell(
    place: Place,
    target: TargetCfg,
    makeover: Makeover,
    motive: Motive,
    detective_name: str,
    detective_gender: str,
    culprit_name: str,
    culprit_gender: str,
    culprit_role: str,
    helper_name: str,
    helper_gender: str,
) -> World:
    world = World(place)
    detective = world.add(build_character(detective_name, detective_gender, "detective"))
    culprit = world.add(build_character(culprit_name, culprit_gender, "suspect"))
    helper = world.add(build_character(helper_name, helper_gender, "helper"))
    target_ent = world.add(
        Entity(
            id="target",
            type="food",
            label=target.label,
            phrase=target.phrase,
            role="target",
            tags=set(target.tags),
        )
    )
    room = world.add(Entity(id="room", type="room", label=place.label))

    spare_names = []
    for name in GIRL_NAMES + BOY_NAMES + ["Aunt May", "Uncle Joe", "Mom", "Dad"]:
        if name not in {detective_name, culprit_name, helper_name}:
            spare_names.append(name)

    suspect_two_name = spare_names[0]
    suspect_three_name = spare_names[1]
    suspect_two_gender = "girl" if suspect_two_name in GIRL_NAMES else "boy"
    suspect_three_gender = "girl" if suspect_three_name in GIRL_NAMES else "boy"
    suspect_two = world.add(build_character(suspect_two_name, suspect_two_gender, "suspect"))
    suspect_three = world.add(build_character(suspect_three_name, suspect_three_gender, "suspect"))

    culprit.attrs["role_label"] = SUSPECT_ROLES[culprit_role]["label"]
    culprit.attrs["motive"] = motive.id
    detective.attrs["style"] = "whodunit"

    introduce(world, detective, helper, place, target)
    world.para()
    discover(world, detective, target_ent, target, makeover)
    inspect_scene(world, detective, makeover, place)
    question_suspects(world, detective, [culprit, suspect_two, suspect_three], culprit, motive)
    world.para()
    deduce(world, detective, culprit, makeover)
    reveal(world, culprit, motive)
    repair(world, helper, target_ent, target, makeover)
    world.para()
    close_case(world, detective, culprit, motive, target)

    world.facts.update(
        place=place,
        target_cfg=target,
        makeover=makeover,
        motive=motive,
        detective=detective,
        culprit=culprit,
        helper=helper,
        suspects=[culprit, suspect_two, suspect_three],
        target=target_ent,
        solved=target_ent.meters["mystery_solved"] >= THRESHOLD,
        transformed=target_ent.meters["transformed"] >= THRESHOLD,
        culprit_role=culprit_role,
    )
    return world


KNOWLEDGE = {
    "breakfast": [
        (
            "What is breakfast?",
            "Breakfast is the first meal of the day. It gives your body energy after sleeping.",
        )
    ],
    "berries": [
        (
            "Why do berries leave purple marks?",
            "Many berries have strong juice inside them. When the juice is pressed out, it can leave bright purple or red stains.",
        )
    ],
    "banana": [
        (
            "Why do bananas bend like a smile?",
            "A banana curves as it grows. That shape can make it look funny, almost like a smile or a mustache.",
        )
    ],
    "pretzel": [
        (
            "Why are pretzels salty?",
            "Pretzels often have a little salt on top. The salt gives them a crunchy, savory taste.",
        )
    ],
    "cocoa": [
        (
            "What is cocoa powder?",
            "Cocoa powder is a fine brown powder used to make chocolate drinks and treats. A little puff of it can dust a whole surface.",
        )
    ],
    "mystery": [
        (
            "What does a detective do?",
            "A detective notices clues and asks careful questions. Then the detective uses those clues to figure out what happened.",
        )
    ],
    "kindness": [
        (
            "Can a prank be kind?",
            "Sometimes a silly surprise is meant to help someone laugh, but it should stay gentle and safe. A kind joke does not hurt people or ruin important things.",
        )
    ],
}

KNOWLEDGE_ORDER = ["breakfast", "mystery", "berries", "banana", "pretzel", "cocoa", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    target = f["target_cfg"]
    makeover = f["makeover"]
    motive = f["motive"]
    return [
        (
            f'Write a short child-facing whodunit where a breakfast is transformed into something funny, '
            f'and include the words "prolong" and "scrounge".'
        ),
        (
            f"Tell a humorous mystery about {detective.id}, who finds {target.phrase} changed into {makeover.label}, "
            f"follows clues, and learns that the culprit acted {motive.label}."
        ),
        (
            f"Write a gentle transformation story with a detective-style voice, a silly reveal, and an ending where "
            f"everyone laughs and shares breakfast together."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    helper = f["helper"]
    target = f["target_cfg"]
    makeover = f["makeover"]
    motive = f["motive"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who acts like a little detective, and {culprit.id}, who changed the breakfast. "
            f"{helper.id} is there too and helps turn the mystery into a happy meal.",
        ),
        (
            f"What was strange about the {target.label}?",
            f"The {target.label} had been transformed into {makeover.label} with {makeover.look}. "
            f"That silly change is what started the mystery.",
        ),
        (
            f"What clue helped {detective.id} solve the case?",
            f"{detective.id} noticed {makeover.clue_phrase}. Later, the same kind of mark showed up on {culprit.id}, "
            f"so the clue connected the breakfast to the culprit.",
        ),
        (
            f"Why did {culprit.id} change the breakfast?",
            f"{culprit.id} did it because {motive.reason}. "
            f"The reason was gentle, so the mystery ended in laughter instead of trouble.",
        ),
        (
            "How did the story end?",
            f"The case was solved, everyone laughed, and they shared the transformed breakfast together. "
            f"The ending shows that the strange breakfast became a family joke instead of a worry.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"breakfast", "mystery", "kindness"}
    makeover = f["makeover"]
    if "berries" in makeover.tags:
        tags.add("berries")
    if "banana" in makeover.tags:
        tags.add("banana")
    if "pretzel" in makeover.tags:
        tags.add("pretzel")
    if "cocoa" in makeover.tags:
        tags.add("cocoa")
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
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(T, M) :- target(T), makeover(M), compatible(T, M).
valid(P, T, M) :- place(P), fits(T, M).

solved(T, Mv) :- fits(T, Mv), clue_strength(Mv, 1), gentle_motive.
gentle_motive :- motive(M), motive_gentle(M).

#show valid/3.
#show solved/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for target_id in TARGETS:
        lines.append(asp.fact("target", target_id))
    for makeover_id in MAKEOVERS:
        lines.append(asp.fact("makeover", makeover_id))
        lines.append(asp.fact("clue_strength", makeover_id, 1))
    for target_id, cfg in TARGETS.items():
        for makeover_id, makeover in MAKEOVERS.items():
            if target_id in makeover.fits:
                lines.append(asp.fact("compatible", target_id, makeover_id))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        if motive.gentle:
            lines.append(asp.fact("motive_gentle", motive_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved_pairs() -> list[tuple]:
    import asp

    extra = "gentle_motive :- motive_gentle(prolong_wait).\n#show solved/2."
    model = asp.one_model(asp_program(extra))
    return sorted(set(asp.atoms(model, "solved")))


def outcome_of(params: StoryParams) -> str:
    if not makeover_fits(params.target, params.makeover):
        return "invalid"
    return "solved"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    solved_pairs = set(asp_solved_pairs())
    expected_pairs = {(target_id, makeover_id) for _, target_id, makeover_id in valid_combos()}
    if solved_pairs == expected_pairs:
        print(f"OK: solved target/makeover pairs match ({len(solved_pairs)} pairs).")
    else:
        rc = 1
        print("MISMATCH in solved pairs:")
        if solved_pairs - expected_pairs:
            print("  only in ASP:", sorted(solved_pairs - expected_pairs))
        if expected_pairs - solved_pairs:
            print("  only in Python:", sorted(expected_pairs - solved_pairs))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny humorous whodunit about a transformed breakfast. Unspecified choices are picked at random."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--makeover", choices=MAKEOVERS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.makeover and not makeover_fits(args.target, args.makeover):
        raise StoryError(explain_rejection(args.target, args.makeover))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.target is None or combo[1] == args.target)
        and (args.makeover is None or combo[2] == args.makeover)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, target_id, makeover_id = rng.choice(sorted(combos))
    motive_id = args.motive or rng.choice(sorted(MOTIVES))

    detective_gender = rng.choice(["girl", "boy"])
    detective = rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)

    culprit_role = rng.choice(sorted(SUSPECT_ROLES))
    if culprit_role == "sibling":
        culprit_gender = "boy" if detective_gender == "girl" and rng.random() < 0.5 else rng.choice(["girl", "boy"])
        if culprit_gender == "girl":
            culprit = rng.choice([n for n in GIRL_NAMES if n != detective])
        else:
            culprit = rng.choice([n for n in BOY_NAMES if n != detective])
    elif culprit_role == "cousin":
        culprit_gender = rng.choice(["cousin_girl", "cousin_boy"])
        if culprit_gender == "cousin_girl":
            culprit = rng.choice([n for n in GIRL_NAMES if n != detective])
        else:
            culprit = rng.choice([n for n in BOY_NAMES if n != detective])
    else:
        culprit_gender = rng.choice(["mother", "father"])
        culprit = "Mom" if culprit_gender == "mother" else "Dad"

    helper_gender = rng.choice(["mother", "father", "girl", "boy"])
    helper = _pick_name(rng, helper_gender, avoid={detective, culprit})

    return StoryParams(
        place=place_id,
        target=target_id,
        makeover=makeover_id,
        motive=motive_id,
        detective=detective,
        detective_gender=detective_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        culprit_role=culprit_role,
        helper=helper,
        helper_gender=helper_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.target not in TARGETS:
        raise StoryError(f"(Invalid target: {params.target})")
    if params.makeover not in MAKEOVERS:
        raise StoryError(f"(Invalid makeover: {params.makeover})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Invalid motive: {params.motive})")
    if not makeover_fits(params.target, params.makeover):
        raise StoryError(explain_rejection(params.target, params.makeover))

    world = tell(
        place=PLACES[params.place],
        target=TARGETS[params.target],
        makeover=MAKEOVERS[params.makeover],
        motive=MOTIVES[params.motive],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        culprit_role=params.culprit_role,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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
        print(asp_program("#show valid/3.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, target, makeover) combos:\n")
        for place_id, target_id, makeover_id in combos:
            print(f"  {place_id:8} {target_id:10} {makeover_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.detective}: {p.target} -> {p.makeover} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
