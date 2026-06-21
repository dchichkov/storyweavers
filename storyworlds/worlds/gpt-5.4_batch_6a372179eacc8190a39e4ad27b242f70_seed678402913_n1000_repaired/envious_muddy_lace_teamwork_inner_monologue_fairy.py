#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/envious_muddy_lace_teamwork_inner_monologue_fairy.py
===============================================================================

A small fairy-tale storyworld about envy, muddy trouble, lace, and teamwork.

Two young fairies are preparing for a moon festival. One child becomes envious
of the other's lovely lace, and that feeling pushes the choice that drives the
story. A muddy crossing and a practical rescue tool give the domain a concrete
reasonableness gate: only tools strong enough for the crossing make a valid
story. The emotional turn is also modeled: sometimes the hero admits the envious
feeling early, and sometimes the hero hides it, blunders into the mud, and must
accept help.

Run it
------
    python storyworlds/worlds/gpt-5.4/envious_muddy_lace_teamwork_inner_monologue_fairy.py
    python storyworlds/worlds/gpt-5.4/envious_muddy_lace_teamwork_inner_monologue_fairy.py --all
    python storyworlds/worlds/gpt-5.4/envious_muddy_lace_teamwork_inner_monologue_fairy.py --qa
    python storyworlds/worlds/gpt-5.4/envious_muddy_lace_teamwork_inner_monologue_fairy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
        female = {"girl", "fairy_girl", "mother", "queen", "seamstress", "woman"}
        male = {"boy", "fairy_boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"seamstress": "seamstress", "queen": "queen"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Adornment:
    id: str
    label: str
    phrase: str
    lace_phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    place_phrase: str
    depth: int
    cling: int
    mud_text: str
    danger_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    power: int
    grace: int
    sense: int
    method: str
    rescue_text: str
    cross_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    adornment: str
    obstacle: str
    aid: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    guide_type: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


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
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

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


def _r_muddy_shame(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero and hero.meters["muddy"] >= THRESHOLD:
        sig = ("muddy_shame", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["shame"] += 1
            out.append("__muddy__")
    return out


def _r_teamwork_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["helped_by_friend"] >= THRESHOLD:
        sig = ("teamwork_relief", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["relief"] += 1
        friend.memes["care"] += 1
        return ["__teamwork__"]
    return []


CAUSAL_RULES = [
    Rule(name="muddy_shame", tag="emotional", apply=_r_muddy_shame),
    Rule(name="teamwork_relief", tag="social", apply=_r_teamwork_relief),
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


SETTINGS = {
    "willow_glen": Setting(
        id="willow_glen",
        place="Willow Glen",
        path="a silver path between foxgloves and fern",
        glow="The fireflies were already rehearsing their tiny lamps.",
        tags={"fairy", "forest"},
    ),
    "moon_meadow": Setting(
        id="moon_meadow",
        place="Moon Meadow",
        path="a pale path through clover and white bells",
        glow="The grass held little drops of evening light.",
        tags={"fairy", "meadow"},
    ),
    "thistle_hollow": Setting(
        id="thistle_hollow",
        place="Thistle Hollow",
        path="a winding path under thistle plumes and hanging moss",
        glow="Even the breeze seemed to whisper festival songs.",
        tags={"fairy", "hollow"},
    ),
}

ADORNMENTS = {
    "sash": Adornment(
        id="sash",
        label="sash",
        phrase="a sky-blue sash trimmed with lace",
        lace_phrase="the soft lace on the sash",
        tags={"lace"},
    ),
    "collar": Adornment(
        id="collar",
        label="collar",
        phrase="a pearl-white collar edged with lace",
        lace_phrase="the neat lace around the collar",
        tags={"lace"},
    ),
    "slippers": Adornment(
        id="slippers",
        label="slippers",
        phrase="a pair of petal slippers tied with lace",
        lace_phrase="the pale lace on the slippers",
        plural=True,
        tags={"lace"},
    ),
}

OBSTACLES = {
    "muddy_bank": Obstacle(
        id="muddy_bank",
        label="muddy bank",
        place_phrase="beside a moonflower pool",
        depth=2,
        cling=2,
        mud_text="The bank was muddy and glossy, as if the earth were trying to hold little feet.",
        danger_text="one wrong step could sink an ankle and spoil the flowers",
        tags={"mud", "muddy"},
    ),
    "muddy_rill": Obstacle(
        id="muddy_rill",
        label="muddy rill",
        place_phrase="where a thin stream crossed the path",
        depth=1,
        cling=1,
        mud_text="The rill had spread a ribbon of muddy earth across the path.",
        danger_text="a quick dash could still end in a messy slip",
        tags={"mud", "muddy"},
    ),
    "reed_patch": Obstacle(
        id="reed_patch",
        label="muddy reed patch",
        place_phrase="at the edge of the lily water",
        depth=3,
        cling=2,
        mud_text="Between the reeds lay a muddy patch, dark and sticky under the moon.",
        danger_text="it was deep enough to trap a small fairy until help came",
        tags={"mud", "muddy"},
    ),
}

AIDS = {
    "moss_board": Aid(
        id="moss_board",
        label="moss board",
        phrase="a smooth moss board",
        power=2,
        grace=1,
        sense=2,
        method="laid the board down to make a little bridge",
        rescue_text="slid the moss board over the muck so the trapped feet could be lifted free",
        cross_text="they crossed one after the other on the moss board",
        tags={"bridge", "teamwork"},
    ),
    "vine_line": Aid(
        id="vine_line",
        label="vine line",
        phrase="a braided vine line",
        power=3,
        grace=2,
        sense=3,
        method="tied the vine line to a willow root and held it tight",
        rescue_text="braced the vine line and pulled together until the mud let go with a wet sigh",
        cross_text="they leaned on the vine line together and stepped across carefully",
        tags={"rope", "teamwork"},
    ),
    "lily_sled": Aid(
        id="lily_sled",
        label="lily sled",
        phrase="a wide lily-leaf sled",
        power=3,
        grace=3,
        sense=3,
        method="pushed the lily-leaf sled over the wet ground like a floating tray",
        rescue_text="glided the lily sled over the mud and drew the stuck fairy onto it",
        cross_text="they glided across on the lily sled without splashing a drop",
        tags={"sled", "teamwork"},
    ),
    "twig_hop": Aid(
        id="twig_hop",
        label="twig hop",
        phrase="a bundle of springy twigs",
        power=1,
        grace=0,
        sense=1,
        method="dropped the twigs in a hurry and hoped they would hold",
        rescue_text="poked the twigs toward the mud, but they bent and vanished",
        cross_text="they tried to hop across on the twigs",
        tags={"twig"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nella", "Poppy", "Wren", "Ivy", "Faye", "Elsa"]
BOY_NAMES = ["Rowan", "Tobin", "Finn", "Ash", "Leo", "Milo", "Bram", "Nico"]
HERO_TRAITS = ["honest", "proud", "quick", "tender"]
FRIEND_TRAITS = ["patient", "gentle", "brisk", "merry"]


def valid_combo(obstacle: Obstacle, aid: Aid) -> bool:
    return aid.sense >= SENSE_MIN and aid.power >= obstacle.depth


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for adornment_id in ADORNMENTS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for aid_id, aid in AIDS.items():
                    if valid_combo(obstacle, aid):
                        combos.append((setting_id, adornment_id, obstacle_id, aid_id))
    return combos


def explain_combo(obstacle: Obstacle, aid: Aid) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} is a weak, hasty idea for a muddy crossing. "
            f"Pick a steadier rescue tool.)"
        )
    return (
        f"(No story: {aid.label} is too weak for the {obstacle.label}. "
        f"The tool must truly carry or pull a small fairy through the mud.)"
    )


def would_confess(hero_trait: str, friend_trait: str) -> bool:
    return hero_trait == "honest" or friend_trait in {"patient", "gentle"}


def rescue_stays_clean(obstacle: Obstacle, aid: Aid) -> bool:
    return aid.grace >= obstacle.cling


def inner_monologue(hero: Entity, adornment: Adornment) -> str:
    if hero.memes["envy"] >= THRESHOLD:
        return (
            f'Inside, {hero.id} thought, "I should be glad for my friend, '
            f'but I feel envious of {adornment.lace_phrase}. I wish I had something '
            f'so pretty too."'
        )
    return (
        f'Inside, {hero.id} thought, "The festival will be lovelier if we both shine."'
    )


def introduce(world: World, setting: Setting, hero: Entity, friend: Entity, guide: Entity,
              adornment: Adornment) -> None:
    world.say(
        f"In {setting.place}, where fern tips gleamed like tiny green candles, "
        f"{hero.id} and {friend.id} were young fairies on their way to the Moonlace Festival."
    )
    world.say(setting.glow)
    world.say(
        f"The old {guide.label_word} had asked them to gather moonflowers for the queen's crown, "
        f"and {friend.id} came wearing {adornment.phrase}."
    )
    world.say(
        f"{hero.id} noticed {adornment.lace_phrase}, and a small hard feeling stirred."
    )


def feel_envy(world: World, hero: Entity, friend: Entity, adornment: Adornment) -> None:
    hero.memes["envy"] += 1
    friend.memes["joy"] += 1
    world.say(inner_monologue(hero, adornment))
    world.say(
        f"{friend.id} only smiled and said, \"Come along. The moonflowers close if we are late.\""
    )


def reach_crossing(world: World, setting: Setting, obstacle: Obstacle) -> None:
    world.say(
        f"They followed {setting.path} until they came to {obstacle.place_phrase}."
    )
    world.say(obstacle.mud_text)
    world.say(
        f"Beyond it, the moonflowers glowed like little bowls of milk, but {obstacle.danger_text}."
    )


def confess(world: World, hero: Entity, friend: Entity, adornment: Adornment) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f"{hero.id} stopped before the mud and lowered {hero.pronoun('possessive')} eyes. "
        f"\"I must tell the truth,\" {hero.pronoun()} said. "
        f"\"I was so envious of {adornment.lace_phrase} that I almost forgot the flowers.\""
    )
    world.say(
        f"{friend.id} touched {hero.pronoun('possessive')} hand. "
        f"\"Then let us do the task together,\" {friend.pronoun()} said. "
        f"\"Pretty lace is nicer when hearts stay kind.\""
    )


def blunder(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["hurry"] += 1
    hero.meters["muddy"] += 1
    hero.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But envy made {hero.id} hasty. Before another word could be spoken, "
        f"{hero.pronoun()} skipped onto the {obstacle.label} alone."
    )
    world.say(
        f"At once the ground gave a wet gulp. Mud splashed to {hero.pronoun('possessive')} knees, "
        f"and one foot sank so deep that {hero.pronoun()} could not pull it free."
    )
    world.say(
        f'Inside, {hero.id} thought, "Oh dear. Being first is not the same as being wise."'
    )


def prepare_aid(world: World, friend: Entity, aid: Aid) -> None:
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} did not laugh. {friend.pronoun().capitalize()} ran to fetch {aid.phrase} and "
        f"{aid.method}."
    )


def rescue(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, aid: Aid) -> None:
    hero.memes["helped_by_friend"] += 1
    hero.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} called, \"Pull when I pull!\" Together they {aid.rescue_text}."
    )
    world.say(
        f"The mud clung for a breath, then let go. {hero.id} tumbled out, spattered and trembling."
    )


def cross_together(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"After that, neither fairy tried to be grand alone. {aid.cross_text}, "
        f"and each held a side of the moonflower basket."
    )
    world.say(
        "Soon the basket was full, and the flowers' pale light shone over both smiling faces."
    )


def muddy_lace(world: World, friend: Entity, adornment_ent: Entity, adornment: Adornment) -> None:
    adornment_ent.meters["muddy"] += 1
    friend.meters["muddy"] += 1
    world.say(
        f"In the pulling and splashing, mud spotted {adornment.lace_phrase}. "
        f"For one sad blink, the lovely trim looked brown instead of bright."
    )


def wash_lace(world: World, hero: Entity, friend: Entity, adornment: Adornment) -> None:
    hero.memes["care"] += 1
    hero.memes["shame"] = 0.0
    hero.memes["gratitude"] += 1
    world.say(
        f"{hero.id} knelt by the clear stream and rinsed the lace with cupped hands until it shone again."
    )
    world.say(
        f"\"I made the trouble,\" {hero.pronoun()} said, \"so I will help mend it.\" "
        f"{friend.id} smiled, because the words were as clean as the water."
    )


def ending(world: World, hero: Entity, friend: Entity, guide: Entity, adornment: Adornment,
           lace_muddied: bool) -> None:
    hero.memes["envy"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    lace_line = (
        f"The lace gleamed softly again, with not a muddy spot left on it."
        if lace_muddied
        else f"The lace stayed neat and pale all the while."
    )
    world.say(
        f"When they returned, the old {guide.label_word} wove the moonflowers into the queen's crown."
    )
    world.say(
        f"{lace_line} {hero.id} no longer wished the lace were {hero.pronoun('possessive')} alone."
    )
    world.say(
        f"Standing shoulder to shoulder with {friend.id}, {hero.pronoun()} felt richer than ribbons, "
        f"for the best finery in all the fairy wood was teamwork with a true friend."
    )


def tell(setting: Setting, adornment: Adornment, obstacle: Obstacle, aid: Aid,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str,
         guide_type: str, hero_trait: str, friend_trait: str) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_type,
        label="seamstress",
        role="guide",
    ))
    adornment_ent = world.add(Entity(
        id="adornment",
        type="adornment",
        label=adornment.label,
        phrase=adornment.phrase,
        tags=set(adornment.tags),
    ))

    introduce(world, setting, hero, friend, guide, adornment)
    feel_envy(world, hero, friend, adornment)

    world.para()
    reach_crossing(world, setting, obstacle)

    confessed = would_confess(hero_trait, friend_trait)
    if confessed:
        confess(world, hero, friend, adornment)
        world.para()
        prepare_aid(world, friend, aid)
        cross_together(world, hero, friend, aid)
        lace_muddied = False
        outcome = "confessed"
    else:
        blunder(world, hero, obstacle)
        world.para()
        prepare_aid(world, friend, aid)
        rescue(world, hero, friend, obstacle, aid)
        lace_muddied = not rescue_stays_clean(obstacle, aid)
        if lace_muddied:
            muddy_lace(world, friend, adornment_ent, adornment)
            wash_lace(world, hero, friend, adornment)
            outcome = "muddy_lace"
        else:
            world.say(
                f"By good luck and careful hands, not even {adornment.lace_phrase} was spoiled."
            )
            hero.memes["gratitude"] += 1
            outcome = "rescued_clean"

        world.para()
        cross_together(world, hero, friend, aid)

    world.para()
    ending(world, hero, friend, guide, adornment, lace_muddied)

    world.facts.update(
        setting=setting,
        adornment_cfg=adornment,
        obstacle=obstacle,
        aid=aid,
        hero=hero,
        friend=friend,
        guide=guide,
        adornment=adornment_ent,
        confessed=confessed,
        lace_muddied=lace_muddied,
        outcome=outcome,
    )
    return world


KNOWLEDGE = {
    "lace": [
        (
            "What is lace?",
            "Lace is a light, patterned fabric with little holes and loops. People often use it to make clothes look delicate and fancy.",
        )
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is wet earth. It can be soft and sticky, so feet and shoes can sink into it.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another do one job together. It often works better than each person trying alone.",
        )
    ],
    "envy": [
        (
            "What does envious mean?",
            "Envious means wishing you had something that belongs to someone else. It is a feeling, and it helps to talk about it kindly instead of hiding it.",
        )
    ],
    "rope": [
        (
            "Why can a rope or vine help someone in mud?",
            "A rope or strong vine gives people something steady to hold. That makes it easier to pull carefully without slipping.",
        )
    ],
    "bridge": [
        (
            "Why does a little bridge help over mud?",
            "A bridge spreads your weight and gives your feet a firmer place to land. That keeps you from sinking into the soft ground.",
        )
    ],
    "sled": [
        (
            "Why can a wide sled or board glide over soft ground?",
            "A wide sled spreads weight across more ground. That makes it less likely to sink into mud than a small foot would.",
        )
    ],
    "fairy": [
        (
            "What is a fairy tale?",
            "A fairy tale is a make-believe story with magical or wondrous touches. It often teaches a gentle lesson through adventure.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fairy", "envy", "mud", "lace", "teamwork", "bridge", "rope", "sled"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adornment = f["adornment_cfg"]
    obstacle = f["obstacle"]
    return [
        'Write a short fairy-tale story for a 3-to-5-year-old that includes the words "envious", "muddy", and "lace".',
        f"Tell a gentle fairy story where {hero.label} feels envious of {friend.label}'s {adornment.label}, and a {obstacle.label} teaches the value of teamwork.",
        "Write a child-facing story with an inner monologue, a muddy problem, and a kind ending that shows sharing and teamwork matter more than pretty things.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guide = f["guide"]
    obstacle = f["obstacle"]
    adornment = f["adornment_cfg"]
    aid = f["aid"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young fairies, {hero.label} and {friend.label}. They are trying to gather moonflowers for the old {guide.label_word} and the festival.",
        ),
        (
            f"Why did {hero.label} feel envious?",
            f"{hero.label} felt envious because {friend.label} was wearing {adornment.phrase}. The pretty lace caught {hero.pronoun('possessive')} eye and stirred a hard little feeling inside.",
        ),
        (
            "What problem stood between the fairies and the moonflowers?",
            f"A {obstacle.label} stood in the way. It was slippery and sticky, so a careless step could leave a small fairy covered in mud.",
        ),
    ]
    if f["confessed"]:
        qa.append(
            (
                f"What did {hero.label} say before crossing the mud?",
                f"{hero.label} told the truth and admitted feeling envious of the lace. Saying it aloud changed the moment, because the two fairies could start helping each other instead of hiding feelings.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} tried to go first alone?",
                f"{hero.label} hurried onto the muddy ground and got stuck. That happened because envy made {hero.pronoun('object')} rush instead of waiting to work together.",
            )
        )
    qa.append(
        (
            f"How did the fairies solve the problem?",
            f"They used {aid.phrase} and worked together instead of one fairy trying alone. The teamwork gave them a steady way to rescue, cross, and carry the moonflowers safely.",
        )
    )
    if f["lace_muddied"]:
        qa.append(
            (
                "Did the lace stay clean?",
                f"No. The lace was splashed with mud during the rescue, but {hero.label} helped wash it clean in the stream. That showed {hero.pronoun()} had stopped thinking only about {hero.pronoun('possessive')} own feelings.",
            )
        )
    else:
        qa.append(
            (
                "What changed at the end of the story?",
                f"{hero.label} stopped wanting the lace for {hero.pronoun('object')}self and cared more about the friendship and the shared task. The ending proves it because the fairies stand together with the moonflowers instead of competing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"fairy", "envy", "mud", "lace", "teamwork"}
    aid = f["aid"]
    if "bridge" in aid.tags:
        tags.add("bridge")
    if "rope" in aid.tags:
        tags.add("rope")
    if "sled" in aid.tags:
        tags.add("sled")
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="willow_glen",
        adornment="sash",
        obstacle="muddy_bank",
        aid="vine_line",
        hero_name="Lina",
        hero_type="fairy_girl",
        friend_name="Mira",
        friend_type="fairy_girl",
        guide_type="seamstress",
        hero_trait="proud",
        friend_trait="patient",
    ),
    StoryParams(
        setting="moon_meadow",
        adornment="collar",
        obstacle="muddy_rill",
        aid="moss_board",
        hero_name="Rowan",
        hero_type="fairy_boy",
        friend_name="Poppy",
        friend_type="fairy_girl",
        guide_type="seamstress",
        hero_trait="quick",
        friend_trait="brisk",
    ),
    StoryParams(
        setting="thistle_hollow",
        adornment="slippers",
        obstacle="reed_patch",
        aid="lily_sled",
        hero_name="Ivy",
        hero_type="fairy_girl",
        friend_name="Finn",
        friend_type="fairy_boy",
        guide_type="seamstress",
        hero_trait="proud",
        friend_trait="gentle",
    ),
    StoryParams(
        setting="moon_meadow",
        adornment="sash",
        obstacle="muddy_bank",
        aid="moss_board",
        hero_name="Ash",
        hero_type="fairy_boy",
        friend_name="Wren",
        friend_type="fairy_girl",
        guide_type="seamstress",
        hero_trait="proud",
        friend_trait="merry",
    ),
]


ASP_RULES = r"""
valid(S, Ad, O, A) :- setting(S), adornment(Ad), obstacle(O), aid(A),
                      sense(A, Sns), sense_min(M), Sns >= M,
                      power(A, P), depth(O, D), P >= D.

confessed :- hero_trait(honest).
confessed :- friend_trait(patient).
confessed :- friend_trait(gentle).

rescue_clean :- chosen_aid(A), chosen_obstacle(O), grace(A, G), cling(O, C), G >= C.

outcome(confessed) :- confessed.
outcome(rescued_clean) :- not confessed, rescue_clean.
outcome(muddy_lace) :- not confessed, not rescue_clean.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for adid in ADORNMENTS:
        lines.append(asp.fact("adornment", adid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("depth", oid, obstacle.depth))
        lines.append(asp.fact("cling", oid, obstacle.cling))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        lines.append(asp.fact("grace", aid_id, aid.grace))
        lines.append(asp.fact("sense", aid_id, aid.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("hero_trait", params.hero_trait),
        asp.fact("friend_trait", params.friend_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_confess(params.hero_trait, params.friend_trait):
        return "confessed"
    if rescue_stays_clean(OBSTACLES[params.obstacle], AIDS[params.aid]):
        return "rescued_clean"
    return "muddy_lace"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        emit(sample, trace=False, qa=True, header="### smoke")
    if "moonflowers" not in sample.story:
        raise StoryError("Smoke test failed: expected story content missing.")


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
    for seed in range(50):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
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
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about envy, lace, muddy trouble, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--adornment", choices=ADORNMENTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-trait", choices=HERO_TRAITS)
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS)
    ap.add_argument("--guide", choices=["seamstress"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    hero_type = rng.choice(["fairy_girl", "fairy_boy"])
    pool = GIRL_NAMES if hero_type == "fairy_girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), hero_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid:
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not valid_combo(obstacle, aid):
            raise StoryError(explain_combo(obstacle, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.adornment is None or combo[1] == args.adornment)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, adornment_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    hero_name, hero_type = _pick_child(rng)
    friend_name, friend_type = _pick_child(rng, avoid=hero_name)
    hero_trait = args.hero_trait or rng.choice(HERO_TRAITS)
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)

    return StoryParams(
        setting=setting_id,
        adornment=adornment_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        guide_type=args.guide or "seamstress",
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        adornment = ADORNMENTS[params.adornment]
        obstacle = OBSTACLES[params.obstacle]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not valid_combo(obstacle, aid):
        raise StoryError(explain_combo(obstacle, aid))

    world = tell(
        setting=setting,
        adornment=adornment,
        obstacle=obstacle,
        aid=aid,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        guide_type=params.guide_type,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, adornment, obstacle, aid) combos:\n")
        for setting_id, adornment_id, obstacle_id, aid_id in combos:
            print(f"  {setting_id:14} {adornment_id:10} {obstacle_id:12} {aid_id}")
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
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.obstacle} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
