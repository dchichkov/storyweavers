#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py

A standalone storyworld about two children playing pirates near a thorny thicket.
One child is tempted to use a forbidden magic bullet to blast a shortcut. If the
bullet strikes a dry thicket, sparks can start a fire. A calm grown-up helps, and
the children learn that a good pirate uses intellect before noise.

Run it
------
python storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py
python storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py --thicket ivy
python storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py --response bucket
python storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py --all
python storyworlds/worlds/gpt-5.4/bullet_thicket_intellect_sound_effects_magic_lesson.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    flammable: bool = False
    magical: bool = False
    loud: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str = "pirates"
    scene: str = "a windy pirate island"
    props: str = (
        "The sandbox was their harbor, a rake became a mast, a blue blanket was the sea, "
        "and an old crate held their treasure map."
    )
    title_a: str = "Captain"
    title_b: str = "Lookout"
    goal: str = "the buried treasure"
    obstacle: str = "a thorny thicket"
    role_solo: str = "a pirate"
    role_plural: str = "pirates"
    closing: str = "followed the safe path to the treasure"


@dataclass
class MagicBullet:
    id: str = ""
    label: str = ""
    phrase: str = ""
    boom: str = ""
    flare: str = ""
    lesson_name: str = ""
    plural: bool = False
    magical: bool = True
    sparks: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Thicket:
    id: str = ""
    label: str = ""
    phrase: str = ""
    touch: str = ""
    clue: str = ""
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"


@dataclass
class SafeTool:
    id: str = ""
    label: str = ""
    phrase: str = ""
    use_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str = ""
    sense: int = 0
    power: int = 0
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "yard" in world.entities:
            world.get("yard").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [
    Rule(name="spread", tag="physical", apply=_r_spread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def hazard_at_risk(bullet: MagicBullet, thicket: Thicket) -> bool:
    return bullet.sparks and thicket.flammable


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def fire_severity(thicket: Thicket, delay: int) -> int:
    return thicket.spread + delay


def is_contained(response: Response, thicket: Thicket, delay: int) -> bool:
    return response.power >= fire_severity(thicket, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_strike(world: World, thicket_id: str) -> dict:
    sim = world.copy()
    _do_bullet(sim, sim.get(thicket_id), narrate=False)
    return {
        "ignites": sim.get(thicket_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def _do_bullet(world: World, thicket_ent: Entity, narrate: bool = True) -> None:
    thicket_ent.meters["burning"] += 1
    thicket_ent.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, theme: Theme, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the backyard into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} cried. '
        f'"Today we sail for {theme.goal}!"'
    )


def spot_obstacle(world: World, b: Entity, theme: Theme, thicket: Thicket) -> None:
    world.say(
        f"At the far end of the yard, {thicket.phrase} curled around the garden gate like "
        f"a green wall. It looked just like {theme.obstacle} guarding the way."
    )
    world.say(
        f'{b.id} squinted at it. "That path looks poky and dark," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, bullet: MagicBullet) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes grew bright. "I know! We can use {bullet.phrase}. '
        f'It makes magic go {bullet.boom}!"'
    )


def warn(world: World, b: Entity, a: Entity, bullet: MagicBullet, thicket: Thicket, parent: Entity) -> None:
    pred = predict_strike(world, "thicket")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} knew a loud shortcut was not the clever way."
    world.say(
        f'{b.id} grabbed {a.id}\'s sleeve. "{a.id}, no. {parent.label_word.capitalize()} said '
        f'we must never touch {bullet.label}. If its sparks kiss {thicket.the}, '
        f'it can catch at once."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, bullet: MagicBullet) -> None:
    a.memes["defiance"] += 1
    older_instigator = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_instigator:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"A real pirate needs noise," {a.id} said, and because {a.id} was '
            f"{b.pronoun('possessive')} {rel}, {b.id} could not stop "
            f"{a.pronoun('object')} in time."
        )
    else:
        world.say(f'"A real pirate needs noise," {a.id} said, and dashed for the shelf.')


def back_down(world: World, a: Entity, b: Entity, bullet: MagicBullet, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"A real pirate needs noise," {a.id} began, but {b.id} stood firm like a steady '
        f"{rel}. {a.id} looked at {bullet.label}, then at {b.id}, and sighed."
    )
    world.say(
        f'"No thunder today," {a.id} said at last. Together they went to tell '
        f"{parent.label_word.capitalize()} that the gate path still needed a clever plan."
    )


def ignite(world: World, bullet: MagicBullet, thicket_ent: Entity, thicket: Thicket) -> None:
    _do_bullet(world, thicket_ent)
    world.say(
        f"{bullet.boom}! {bullet.flare}! The magic bullet burst from {a_or_an(bullet.label)} "
        f"glow into a bright streak. For one exciting blink it looked wonderful. Then the spark "
        f"struck {thicket.touch}, and a hungry orange line began to nibble through the leaves."
    )


def alarm(world: World, b: Entity, a: Entity, thicket: Thicket, parent: Entity) -> None:
    world.say(f'"{a.id}! Fire! {thicket.The}!" {b.id} shouted.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, thicket_ent: Entity, thicket: Thicket) -> None:
    thicket_ent.meters["burning"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    body = response.text.replace("{thicket}", thicket.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say("Ssssh! The flames shrank to smoke, and the children stood very still with thumping hearts.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, bullet: MagicBullet) -> None:
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say("For a tiny moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them and hugged them close. "
        f'"I am glad you called me," {parent.pronoun()} said softly. "But remember this: '
        f'{bullet.lesson_name.capitalize()} is not a toy. A loud trick is not the same as '
        f'intellect. The best pirate mind chooses the safe plan before the noisy one."'
    )
    world.say(f'"We understand," whispered {b.id} and {a.id} together.')


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
        kid.memes["intellect"] += 1
    if world.facts.get("outcome") == "averted":
        lead = "The next day, after their careful choice"
    else:
        lead = "The next day, after the scary smoke smell had gone"
    world.say(
        f"{lead}, {parent.label_word.capitalize()} brought out {tool1.phrase} and {tool2.phrase}."
    )
    world.say(
        f'"If pirates need help," {parent.pronoun()} said, "they can use intellect, light, and a safe path."'
    )
    world.say(f"{a.id} took the {tool1.label}, and {b.id} lifted the {tool2.label}.")
    world.say(f"{tool1.use_line} {tool2.use_line}")
    world.say(
        f"This time, the {theme.role_plural} {theme.closing}, laughing as the thicket rustled safely beside them."
    )


def rescue_fail(world: World, parent: Entity, response: Response, thicket_ent: Entity, thicket: Thicket) -> None:
    if "yard" in world.entities:
        world.get("yard").meters["burning"] += 1
    thicket_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{thicket}", thicket.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say(
        f"Crackle-crackle! The fire leapt through the {thicket.label} and licked at the old fence."
    )


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"There was no time for treasure games. {parent.label_word.capitalize()} swept {a.id} and {b.id} "
        "back across the yard and out through the front gate."
    )
    world.say(
        "From the sidewalk they heard the whoosh of hoses and saw gray smoke curling above the garden."
    )
    world.say(
        "The pirate harbor was ruined, and the children learned how quickly one foolish shortcut could grow."
    )


def grim_lesson(world: World, parent: Entity, bullet: MagicBullet) -> None:
    world.say(
        f'{parent.label_word.capitalize()} held them close and said, "You are safe, and that is what matters. '
        f'But never forget: {bullet.lesson_name} is not a toy, and intellect must lead the way."'
    )
    world.say(
        "After that day, they never chased a loud trick when a calm plan would do."
    )


def a_or_an(text: str) -> str:
    return "an" if text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def tell(
    theme: Theme,
    bullet: MagicBullet,
    thicket: Thicket,
    tools: tuple[SafeTool, SafeTool],
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation, "trust": trust},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="yard", type="yard", label="the yard"))
    world.add(
        Entity(
            id="bullet",
            type="magic",
            label=bullet.label,
            phrase=bullet.phrase,
            magical=True,
            loud=True,
            tags=set(bullet.tags),
        )
    )
    thicket_ent = world.add(
        Entity(
            id="thicket",
            type="thicket",
            label=thicket.label,
            phrase=thicket.phrase,
            flammable=thicket.flammable,
            tags=set(thicket.tags),
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    play_setup(world, theme, a, b)
    spot_obstacle(world, b, theme, thicket)

    world.para()
    tempt(world, a, bullet)
    warn(world, b, a, bullet, thicket, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, bullet, parent)
        world.para()
        safe_gift(world, parent, a, b, theme, tools[0], tools[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, bullet)
        world.para()
        ignite(world, bullet, thicket_ent, thicket)
        alarm(world, b, a, thicket, parent)

        severity = fire_severity(thicket, delay)
        thicket_ent.meters["severity"] = float(severity)
        contained = is_contained(response, thicket, delay)

        world.para()
        if contained:
            rescue(world, parent, response, thicket_ent, thicket)
            lesson(world, parent, a, b, bullet)
            world.para()
            safe_gift(world, parent, a, b, theme, tools[0], tools[1])
        else:
            rescue_fail(world, parent, response, thicket_ent, thicket)
            escape_and_loss(world, parent, a, b)
            grim_lesson(world, parent, bullet)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        theme=theme,
        bullet_cfg=bullet,
        thicket_cfg=thicket,
        response=response,
        tools=tools,
        instigator=a,
        cautioner=b,
        parent=parent,
        ignited=thicket_ent.meters["scorched"] >= THRESHOLD,
        outcome=outcome,
        delay=delay,
        severity=severity,
        relation=relation,
        thicket=thicket_ent,
        promised=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(),
}

BULLETS = {
    "thunder": MagicBullet(
        id="thunder",
        label="the thunder bullet",
        phrase="the thunder bullet from the high shelf",
        boom="BANG",
        flare="Fizz!",
        lesson_name="the thunder bullet",
        tags={"bullet", "magic", "noise"},
    ),
    "star": MagicBullet(
        id="star",
        label="the star bullet",
        phrase="the star bullet wrapped in blue velvet",
        boom="POW",
        flare="Spark!",
        lesson_name="the star bullet",
        tags={"bullet", "magic", "noise"},
    ),
    "comet": MagicBullet(
        id="comet",
        label="the comet bullet",
        phrase="the comet bullet with silver swirls",
        boom="WHIZZ-BOOM",
        flare="Flash!",
        lesson_name="the comet bullet",
        tags={"bullet", "magic", "noise"},
    ),
}

THICKETS = {
    "bramble": Thicket(
        id="bramble",
        label="bramble thicket",
        phrase="a dry bramble thicket",
        touch="the driest twigs of the bramble thicket",
        clue="dry",
        spread=3,
        flammable=True,
        tags={"thicket", "dry_brush"},
    ),
    "reed": Thicket(
        id="reed",
        label="reed thicket",
        phrase="a tall reed thicket",
        touch="the papery tops of the reed thicket",
        clue="papery",
        spread=2,
        flammable=True,
        tags={"thicket", "reeds"},
    ),
    "ivy": Thicket(
        id="ivy",
        label="ivy wall",
        phrase="a thick ivy wall",
        touch="the shiny ivy leaves",
        clue="green",
        spread=1,
        flammable=False,
        tags={"thicket", "ivy"},
    ),
}

SAFE_TOOLS = {
    "compass": SafeTool(
        id="compass",
        label="compass",
        phrase="a brass compass",
        use_line="The needle wiggled, then pointed to the open gate path.",
        tags={"compass"},
    ),
    "lantern": SafeTool(
        id="lantern",
        label="lantern",
        phrase="a safe pirate lantern",
        use_line="Its warm light showed every root without a single spark.",
        tags={"lantern"},
    ),
    "map": SafeTool(
        id="map",
        label="map",
        phrase="a fresh treasure map",
        use_line="The map showed a bend around the thicket where little feet could pass.",
        tags={"map"},
    ),
    "bell": SafeTool(
        id="bell",
        label="bell",
        phrase="a silver ship bell",
        use_line='Ding-ding! It made a cheerful sound without any danger at all.',
        tags={"bell", "noise"},
    ),
}

RESPONSES = {
    "hose": Response(
        id="hose",
        sense=3,
        power=4,
        text="snatched up the garden hose and sprayed the flames until every glowing edge turned black and wet",
        fail="sprayed the garden hose hard, but the flames had already raced too far through the {thicket}",
        qa_text="used the garden hose to soak the burning thicket until the flames went out",
        tags={"hose", "water"},
    ),
    "sand": Response(
        id="sand",
        sense=3,
        power=3,
        text="grabbed a bucket of sand from the play box and buried the little flames under it",
        fail="threw sand over the {thicket}, but the sparks had spread wider than the bucket could cover",
        qa_text="buried the little flames under sand",
        tags={"sand", "fire"},
    ),
    "blanket": Response(
        id="blanket",
        sense=2,
        power=2,
        text="beat the small fire down with a thick wet blanket until it could not breathe",
        fail="swung a wet blanket at the {thicket}, but the fire kept racing through the dry stems",
        qa_text="smothered the fire with a thick wet blanket",
        tags={"blanket", "smother"},
    ),
    "bucket": Response(
        id="bucket",
        sense=1,
        power=1,
        text="splashed a little bucket of water over the flames",
        fail="splashed a little bucket of water over the {thicket}, but it was nowhere near enough",
        qa_text="splashed a bucket of water over the flames",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "curious", "clever", "sensible"]


@dataclass
class StoryParams:
    theme: str
    bullet: str
    thicket: str
    tool1: str
    tool2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for bullet_id, bullet in BULLETS.items():
            for thicket_id, thicket in THICKETS.items():
                if hazard_at_risk(bullet, thicket):
                    combos.append((theme, bullet_id, thicket_id))
    return combos


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


KNOWLEDGE = {
    "bullet": [
        (
            "What is a bullet in this story?",
            "In this story, the bullet is a little magic object that makes a loud burst and sparks. It is not safe for children to touch."
        )
    ],
    "magic": [
        (
            "Why can magic still be dangerous?",
            "Something magical can still hurt people if it makes fire, loud blasts, or other risky surprises. Being magical does not make it safe."
        )
    ],
    "thicket": [
        (
            "What is a thicket?",
            "A thicket is a place where bushes, vines, or reeds grow close together. It can feel scratchy, dark, and hard to walk through."
        )
    ],
    "dry_brush": [
        (
            "Why can a dry thicket catch fire quickly?",
            "Dry twigs and leaves burn fast because they do not hold much water. A tiny spark can spread through them very quickly."
        )
    ],
    "hose": [
        (
            "What does a garden hose do?",
            "A garden hose sprays lots of water. A grown-up can use it to soak a small outdoor fire."
        )
    ],
    "sand": [
        (
            "How can sand help with a small fire?",
            "Sand can cover the flames and block some of the air they need. That is why grown-ups sometimes use sand on a small fire."
        )
    ],
    "smother": [
        (
            "What does it mean to smother a fire?",
            "To smother a fire means to cover it so it cannot get the air it needs. Without enough air, the flames go out."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps you find direction. It points the way so you can choose a path with your head instead of guessing."
        )
    ],
    "lantern": [
        (
            "Why is a safe lantern better than a sparkly blast?",
            "A safe lantern gives light without shooting sparks into dry plants. It solves the problem without creating a new one."
        )
    ],
    "map": [
        (
            "Why is a map useful?",
            "A map helps you notice the safe way around something. It is a tool for planning, which is part of using intellect."
        )
    ],
    "bell": [
        (
            "Can a sound effect be fun without being dangerous?",
            "Yes. A cheerful bell or a silly pirate shout can make a game exciting without making fire or causing harm."
        )
    ],
    "intellect": [
        (
            "What does intellect mean?",
            "Intellect means using your mind to think carefully and make a wise choice. It means stopping to plan instead of rushing into danger."
        )
    ],
    "call_adult": [
        (
            "What should a child do if something starts to burn?",
            "Move away and call for a grown-up right away. Getting help fast is the smart and brave thing to do."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bullet",
    "magic",
    "thicket",
    "dry_brush",
    "hose",
    "sand",
    "smother",
    "compass",
    "lantern",
    "map",
    "bell",
    "intellect",
    "call_adult",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    bullet = f["bullet_cfg"]
    thicket = f["thicket_cfg"]
    tool1, tool2 = f["tools"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style safety story for a 3-to-5-year-old that includes the words '
        f'"bullet", "thicket", and "intellect", plus sound effects and magic.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a story where {a.id} wants to use {bullet.label} to blast through {thicket.the}, "
            f"but {b.id} stops the plan before anything burns.",
            f"Write a gentle pirate tale where children choose intellect over noise and end up using a {tool1.label} and a {tool2.label} instead.",
        ]
    if outcome == "burned":
        return [
            base,
            f"Tell a cautionary pirate story where {a.id} uses {bullet.label} near {thicket.the}, "
            "the fire spreads too far, and everyone escapes safely while learning a hard lesson.",
            'Write a story that teaches "intellect before noise" with a sadder ending but safe children.',
        ]
    return [
        base,
        f"Tell a pirate adventure where {a.id} uses {bullet.label} near {thicket.the}, but a calm grown-up puts the fire out and teaches a lesson.",
        f"Write a child-facing story with loud sound effects, magic, a lesson learned, and a happy ending using a {tool1.label} and a {tool2.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    bullet = f["bullet_cfg"]
    thicket = f["thicket_cfg"]
    response = f["response"]
    tool1, tool2 = f["tools"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {a.id} and {b.id}, who were playing pirates in the backyard. "
            f"It also includes their {parent.label_word}, who came to help."
        ),
        (
            "What problem did the children face?",
            f"They wanted to reach their pretend treasure, but {thicket.phrase} blocked the path. "
            f"That made the noisy magic shortcut feel tempting."
        ),
        (
            f"Why did {b.id} tell {a.id} not to touch {bullet.label}?",
            f"{b.id} knew the magic bullet could throw sparks into {thicket.the}. "
            f"Because the plants were risky, one loud blast could turn the game into a real emergency."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} listened and gave up the idea of using {bullet.label}, so nothing caught fire. "
                f"That is the moment when intellect won over noise."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely with {a.id} and {b.id} using a {tool1.label} and a {tool2.label}. "
                f"They still had an adventure, but this time they used a smart plan."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when the magic bullet hit the thicket?",
                f"{thicket.The} caught fire, and the children got scared right away. "
                f"The exciting spark turned dangerous because it landed in dry plants."
            )
        )
        qa.append(
            (
                f"How did the {parent.label_word} stop the fire?",
                f"The {parent.label_word} {response.qa_text}. "
                f"The quick response worked before the flames could spread any farther."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that a noisy trick is not the same as intellect. "
                f"A good plan uses the mind first and asks for safe help when needed."
            )
        )
        qa.append(
            (
                "What proved the children had changed at the end?",
                f"They chose a {tool1.label} and a {tool2.label} instead of reaching for {bullet.label}. "
                f"The ending shows they still wanted adventure, but now they wanted it safely."
            )
        )
    else:
        qa.append(
            (
                f"Could the {parent.label_word} stop the fire in time?",
                f"No. The {parent.label_word} tried, but the fire spread through the thicket too fast. "
                f"Everyone got out safely, yet the game place was ruined."
            )
        )
        qa.append(
            (
                "What lesson did the children learn from the bad ending?",
                f"They learned that one foolish shortcut can grow bigger than a game. "
                f"They also learned that intellect means stopping before danger starts, not after."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"intellect", "call_adult"} | set(f["bullet_cfg"].tags) | set(f["thicket_cfg"].tags)
    outcome = f["outcome"]
    if outcome == "contained":
        tags |= set(f["response"].tags)
        for tool in f["tools"]:
            tags |= set(tool.tags)
    elif outcome == "averted":
        for tool in f["tools"]:
            tags |= set(tool.tags)
    else:
        tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        flags = [name for name, on in (("flammable", ent.flammable), ("magical", ent.magical), ("loud", ent.loud)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        bullet="thunder",
        thicket="bramble",
        tool1="compass",
        tool2="lantern",
        response="hose",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="pirates",
        bullet="star",
        thicket="reed",
        tool1="map",
        tool2="bell",
        response="sand",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="pirates",
        bullet="comet",
        thicket="bramble",
        tool1="compass",
        tool2="map",
        response="blanket",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=2,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        theme="pirates",
        bullet="star",
        thicket="reed",
        tool1="lantern",
        tool2="compass",
        response="hose",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(bullet: MagicBullet, thicket: Thicket) -> str:
    if not thicket.flammable:
        return (
            f"(No story: {bullet.label} throws sparks, but {thicket.the} is too green and wet to make the danger real. "
            "Pick a dry thicket so the warning, accident, and lesson all make sense.)"
        )
    return "(No story: this combination does not create a believable hazard.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is below the common-sense threshold "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], THICKETS[params.thicket], params.delay)
    return "contained" if contained else "burned"


ASP_RULES = r"""
hazard(B, T) :- sparks(B), flammable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Th, B, T) :- theme(Th), bullet(B), thicket(T), hazard(B, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(Sp + D) :- chosen_thicket(T), spread(T, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme in THEMES:
        lines.append(asp.fact("theme", theme))
    for bullet_id, bullet in BULLETS.items():
        lines.append(asp.fact("bullet", bullet_id))
        if bullet.sparks:
            lines.append(asp.fact("sparks", bullet_id))
    for thicket_id, thicket in THICKETS.items():
        lines.append(asp.fact("thicket", thicket_id))
        if thicket.flammable:
            lines.append(asp.fact("flammable", thicket_id))
        lines.append(asp.fact("spread", thicket_id, thicket.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
            asp.fact("chosen_thicket", params.thicket),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    py_sense = {resp.id for resp in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sense)} python={sorted(py_sense)}")

    cases = list(CURATED)
    for seed in range(120):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        _smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-style storyworld: a forbidden magic bullet, a thicket, and a lesson about intellect."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bullet", choices=BULLETS)
    ap.add_argument("--thicket", choices=THICKETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state after the story")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (theme, bullet, thicket) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thicket and not THICKETS[args.thicket].flammable:
        bullet = BULLETS[args.bullet] if args.bullet else next(iter(BULLETS.values()))
        raise StoryError(explain_rejection(bullet, THICKETS[args.thicket]))
    if args.bullet and args.thicket:
        bullet = BULLETS[args.bullet]
        thicket = THICKETS[args.thicket]
        if not hazard_at_risk(bullet, thicket):
            raise StoryError(explain_rejection(bullet, thicket))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.bullet is None or combo[1] == args.bullet)
        and (args.thicket is None or combo[2] == args.thicket)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, bullet_id, thicket_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(resp.id for resp in sensible_responses()))
    tool1, tool2 = rng.sample(sorted(SAFE_TOOLS), 2)
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme,
        bullet=bullet_id,
        thicket=thicket_id,
        tool1=tool1,
        tool2=tool2,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        bullet = BULLETS[params.bullet]
        thicket = THICKETS[params.thicket]
        response = RESPONSES[params.response]
        tool1 = SAFE_TOOLS[params.tool1]
        tool2 = SAFE_TOOLS[params.tool2]
    except KeyError as err:
        raise StoryError(f"(Unknown option in StoryParams: {err})") from err

    if not hazard_at_risk(bullet, thicket):
        raise StoryError(explain_rejection(bullet, thicket))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.tool1 == params.tool2:
        raise StoryError("(Safe ending needs two different tools.)")

    world = tell(
        theme=theme,
        bullet=bullet,
        thicket=thicket,
        tools=(tool1, tool2),
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, bullet, thicket) combos:\n")
        for theme, bullet, thicket in combos:
            print(f"  {theme:8} {bullet:8} {thicket}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.bullet} near {p.thicket} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
