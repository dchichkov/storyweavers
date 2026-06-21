#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py
================================================================================

A standalone story world for a small fairy-tale domain built from the seed words
"chamber" and "splendid" with a Surprise and Happy Ending shape.

Premise
-------
A child-facing fairy-tale hero notices that someone dear has gone quiet and sad
inside a castle chamber. The hero quietly prepares a surprise with the help of
a skilled castle friend. The surprise only makes sense when:

* the helper can truly make the chosen gift,
* the gift suits the recipient's heart,
* the chosen chamber decoration fits the castle's chamber.

When those constraints hold, the world state changes: a dim chamber becomes
splendid, the worried heart brightens, and the ending image proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/chamber_splendid_surprise_happy_ending_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "place" | "thing"
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
        female = {"girl", "princess", "queen", "fairy_godmother", "baker_woman", "gardener_woman"}
        male = {"boy", "prince", "king", "minstrel", "weaver", "dragon_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Castle:
    id: str
    name: str
    chamber: str
    chamber_size: str
    window: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RecipientCfg:
    id: str
    title: str
    type: str
    likes: set[str] = field(default_factory=set)
    worry: str = ""
    wish: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    craft: str
    made_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    title: str
    type: str
    skills: set[str] = field(default_factory=set)
    entrance: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Decor:
    id: str
    label: str
    phrase: str
    fit_sizes: set[str] = field(default_factory=set)
    action: str = ""
    sparkle: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    castle: str
    recipient: str
    gift: str
    helper: str
    decor: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rule engine
# ---------------------------------------------------------------------------
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


def _r_splendid(world: World) -> list[str]:
    chamber = world.entities.get("chamber")
    if chamber is None:
        return []
    if chamber.meters["lit"] < THRESHOLD:
        return []
    if chamber.meters["decorated"] < THRESHOLD:
        return []
    sig = ("splendid",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chamber.meters["splendid"] += 1
    return []


def _r_wonder(world: World) -> list[str]:
    chamber = world.entities.get("chamber")
    recipient = world.entities.get("recipient")
    gift = world.entities.get("gift")
    if chamber is None or recipient is None or gift is None:
        return []
    if chamber.meters["splendid"] < THRESHOLD:
        return []
    if gift.meters["revealed"] < THRESHOLD:
        return []
    if not (gift.tags & recipient.tags):
        return []
    sig = ("wonder", recipient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["wonder"] += 1
    recipient.memes["lonely"] = 0.0
    return []


def _r_joy(world: World) -> list[str]:
    recipient = world.entities.get("recipient")
    hero = world.entities.get("hero")
    if recipient is None or hero is None:
        return []
    if recipient.memes["wonder"] < THRESHOLD:
        return []
    sig = ("joy", recipient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="splendid", tag="place", apply=_r_splendid),
    Rule(name="wonder", tag="emotion", apply=_r_wonder),
    Rule(name="joy", tag="emotion", apply=_r_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                # Rule may have changed state silently; keep chaining once.
                pass
        old_count = len(world.fired)
        # A second pass is only needed when new fired signatures appeared.
        for rule in CAUSAL_RULES:
            pass
        if len(world.fired) != old_count:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def helper_can_make(helper: HelperCfg, gift: Gift) -> bool:
    return gift.made_by in helper.skills


def gift_suits(recipient: RecipientCfg, gift: Gift) -> bool:
    return bool(recipient.likes & gift.tags)


def decor_fits(castle: Castle, decor: Decor) -> bool:
    return castle.chamber_size in decor.fit_sizes


def valid_combo(castle: Castle, recipient: RecipientCfg, gift: Gift,
                helper: HelperCfg, decor: Decor) -> bool:
    return (
        helper_can_make(helper, gift)
        and gift_suits(recipient, gift)
        and decor_fits(castle, decor)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for castle_id, castle in CASTLES.items():
        for recipient_id, recipient in RECIPIENTS.items():
            for gift_id, gift in GIFTS.items():
                for helper_id, helper in HELPERS.items():
                    for decor_id, decor in DECORS.items():
                        if valid_combo(castle, recipient, gift, helper, decor):
                            combos.append((castle_id, recipient_id, gift_id, helper_id, decor_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_surprise(world: World, castle: Castle, recipient_cfg: RecipientCfg,
                     gift_cfg: Gift, decor_cfg: Decor) -> dict:
    sim = world.copy()
    chamber = sim.get("chamber")
    gift = sim.get("gift")
    recipient = sim.get("recipient")
    chamber.meters["lit"] += 1
    chamber.meters["decorated"] += 1
    gift.meters["ready"] += 1
    gift.meters["revealed"] += 1
    propagate(sim, narrate=False)
    return {
        "splendid": chamber.meters["splendid"] >= THRESHOLD,
        "wonder": recipient.memes["wonder"] >= THRESHOLD,
        "joy": recipient.memes["joy"] >= THRESHOLD,
        "decor": decor_cfg.label,
        "gift": gift_cfg.label,
        "recipient": recipient_cfg.title,
        "castle": castle.name,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, recipient: Entity, castle: Castle, recipient_cfg: RecipientCfg) -> None:
    hero.memes["care"] += 1
    recipient.memes["lonely"] += 1
    chamber = world.get("chamber")
    chamber.meters["dim"] += 1
    world.say(
        f"In {castle.name}, there was a quiet chamber with {castle.window}. "
        f"There, {recipient_cfg.title} sat very still, thinking about {recipient_cfg.wish}."
    )
    world.say(
        f"{hero.id}, a {hero.traits[0]} little {hero.type}, saw that the room felt hushed "
        f"and that {recipient.id}'s heart had gone lonely."
    )


def promise_surprise(world: World, hero: Entity, recipient: Entity, recipient_cfg: RecipientCfg) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} did not wish to leave {recipient.id} in such a mood. '
        f'"I will find a surprise to mend this day," {hero.pronoun()} whispered.'
    )
    world.say(
        f"{recipient.id} gave only a small sigh. {recipient.pronoun().capitalize()} was worried about {recipient_cfg.worry}."
    )


def seek_helper(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg, gift_cfg: Gift) -> None:
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"So {hero.id} hurried through the corridor stones and found {helper_cfg.title}. "
        f"{helper.pronoun().capitalize()} {helper_cfg.entrance}."
    )
    world.say(
        f'"Can you help me make {gift_cfg.phrase}?" asked {hero.id}. '
        f'{helper_cfg.title} smiled at once.'
    )


def craft_gift(world: World, helper: Entity, gift: Entity, gift_cfg: Gift) -> None:
    helper.memes["purpose"] += 1
    gift.meters["ready"] += 1
    world.say(
        f"Together they {gift_cfg.craft}, and before long {gift.phrase} was ready. "
        f"It was made for a true surprise, not for boasting."
    )


def prepare_chamber(world: World, hero: Entity, chamber: Entity, castle: Castle, decor_cfg: Decor) -> None:
    hero.memes["effort"] += 1
    chamber.meters["lit"] += 1
    chamber.meters["decorated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"While the gift waited under a silver cloth, {hero.id} slipped back to the chamber and {decor_cfg.action}. "
        f"Soon {castle.glow}."
    )
    if chamber.meters["splendid"] >= THRESHOLD:
        world.say(
            f"The once-quiet chamber did not look plain anymore. It looked splendid, as if a kind spell had brushed every corner."
        )


def invite_recipient(world: World, hero: Entity, recipient: Entity) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        f'At last {hero.id} knocked softly. "Will you come with me?" {hero.pronoun()} asked.'
    )
    world.say(
        f"{recipient.id} rose slowly and followed, not knowing what waited behind the door."
    )


def reveal(world: World, hero: Entity, recipient: Entity, chamber: Entity, gift: Entity,
           recipient_cfg: RecipientCfg, gift_cfg: Gift, decor_cfg: Decor) -> None:
    gift.meters["revealed"] += 1
    recipient.memes["surprised"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the door opened, {recipient.id} stopped in wonder. {decor_cfg.sparkle}, "
        f"and in the middle of the chamber stood {gift_cfg.phrase}."
    )
    if recipient.memes["wonder"] >= THRESHOLD:
        world.say(
            f'"For me?" {recipient.pronoun()} breathed. The surprise fit {recipient.pronoun("possessive")} heart exactly, "
            f"and the loneliness melted away."
        )
    if recipient.memes["joy"] >= THRESHOLD:
        world.say(
            f"{recipient.id} laughed for the first time that day and drew {hero.id} into a warm hug."
        )


def ending(world: World, hero: Entity, recipient: Entity, castle: Castle, gift_cfg: Gift) -> None:
    hero.memes["love"] += 1
    recipient.memes["gratitude"] += 1
    world.say(
        f'From then on, whenever anyone in {castle.name} said the day had turned dull, '
        f'{recipient.id} would smile and answer, "A gentle surprise can brighten even a stone room."'
    )
    world.say(
        f"And that night the chamber windows shone late, while {recipient.id} kept {gift_cfg.label} close "
        f"and {hero.id} watched the happy light dancing on the walls."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(castle: Castle, recipient_cfg: RecipientCfg, gift_cfg: Gift,
         helper_cfg: HelperCfg, decor_cfg: Decor, hero_name: str,
         hero_gender: str, hero_trait: str) -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
        tags={"hero"},
    ))
    recipient = world.add(Entity(
        id=recipient_cfg.title,
        kind="character",
        type=recipient_cfg.type,
        label=recipient_cfg.title,
        role="recipient",
        tags=set(recipient_cfg.likes),
    ))
    helper = world.add(Entity(
        id=helper_cfg.title,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.title,
        role="helper",
        tags=set(helper_cfg.skills),
    ))
    chamber = world.add(Entity(
        id="chamber",
        kind="place",
        type="chamber",
        label=castle.chamber,
        phrase=castle.chamber,
        role="chamber",
        tags=set(castle.tags),
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        role="gift",
        tags=set(gift_cfg.tags),
    ))

    introduce(world, hero, recipient, castle, recipient_cfg)
    world.para()
    promise_surprise(world, hero, recipient, recipient_cfg)
    seek_helper(world, hero, helper, helper_cfg, gift_cfg)
    craft_gift(world, helper, gift, gift_cfg)
    world.para()
    prepare_chamber(world, hero, chamber, castle, decor_cfg)
    invite_recipient(world, hero, recipient)
    reveal(world, hero, recipient, chamber, gift, recipient_cfg, gift_cfg, decor_cfg)
    world.para()
    ending(world, hero, recipient, castle, gift_cfg)

    world.facts.update(
        castle=castle,
        recipient_cfg=recipient_cfg,
        gift_cfg=gift_cfg,
        helper_cfg=helper_cfg,
        decor_cfg=decor_cfg,
        hero=hero,
        recipient=recipient,
        helper=helper,
        chamber=chamber,
        gift=gift,
        splendid=chamber.meters["splendid"] >= THRESHOLD,
        happy=recipient.memes["joy"] >= THRESHOLD,
        surprise=gift.meters["revealed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CASTLES = {
    "moonkeep": Castle(
        id="moonkeep",
        name="Moonkeep Castle",
        chamber="the moonlit chamber",
        chamber_size="small",
        window="one round window full of pale moonlight",
        glow="three little lamps glimmered beside the wall and soft light pooled over the floor",
        tags={"castle", "moon"},
    ),
    "rosehall": Castle(
        id="rosehall",
        name="Rosehall Palace",
        chamber="the rose chamber",
        chamber_size="small",
        window="a tall window framed with climbing roses",
        glow="golden lamp-light touched the petals and made the room gentle and warm",
        tags={"castle", "roses"},
    ),
    "sunspire": Castle(
        id="sunspire",
        name="Sunspire Castle",
        chamber="the high royal chamber",
        chamber_size="grand",
        window="four shining windows looking over the whole valley",
        glow="a bright chain of lamps woke the corners and sent merry gleams into the rafters",
        tags={"castle", "sun"},
    ),
}

RECIPIENTS = {
    "princess": RecipientCfg(
        id="princess",
        title="Princess Elara",
        type="princess",
        likes={"flowers", "music"},
        worry="whether the garden would bloom again after the long rain",
        wish="the sleeping roses in the court below",
        tags={"princess"},
    ),
    "prince": RecipientCfg(
        id="prince",
        title="Prince Rowan",
        type="prince",
        likes={"music", "stories"},
        worry="whether he would ever learn to welcome the grand guests with a brave smile",
        wish="the old tales his mother used to tell by candlelight",
        tags={"prince"},
    ),
    "dragon": RecipientCfg(
        id="dragon",
        title="the Young Dragon",
        type="dragon_boy",
        likes={"sweet", "shiny"},
        worry="whether everyone in the castle thought dragons could only frighten and never delight",
        wish="the bright fairs he had only heard about",
        tags={"dragon"},
    ),
}

GIFTS = {
    "flower_crown": Gift(
        id="flower_crown",
        label="a flower crown",
        phrase="a flower crown woven with dew-bright petals",
        craft="wove a crown from fresh blossoms and silver thread",
        made_by="flowers",
        tags={"flowers"},
    ),
    "silver_flute": Gift(
        id="silver_flute",
        label="a silver flute",
        phrase="a silver flute that could sing like a lark at dawn",
        craft="polished a flute until it shone and tested its sweetest notes",
        made_by="music",
        tags={"music", "shiny"},
    ),
    "honey_cake": Gift(
        id="honey_cake",
        label="a honey cake",
        phrase="a round honey cake glazed like amber",
        craft="baked a honey cake and painted its top with tiny sugar stars",
        made_by="sweet",
        tags={"sweet"},
    ),
    "story_tapestry": Gift(
        id="story_tapestry",
        label="a story tapestry",
        phrase="a little story tapestry stitched with brave silver beasts",
        craft="stitched a tapestry that showed a hero crossing a bright wood",
        made_by="stories",
        tags={"stories", "shiny"},
    ),
}

HELPERS = {
    "gardener": HelperCfg(
        id="gardener",
        title="Mira the Gardener",
        type="gardener_woman",
        skills={"flowers"},
        entrance="came in smelling of rain and rosemary",
        tags={"flowers"},
    ),
    "minstrel": HelperCfg(
        id="minstrel",
        title="Old Tavin the Minstrel",
        type="minstrel",
        skills={"music"},
        entrance="was tuning a stringed harp by the stair",
        tags={"music"},
    ),
    "baker": HelperCfg(
        id="baker",
        title="Bram the Castle Baker",
        type="weaver",
        skills={"sweet"},
        entrance="stood by the ovens with flour on his sleeves",
        tags={"sweet"},
    ),
    "weaver": HelperCfg(
        id="weaver",
        title="Sera the Weaver",
        type="fairy_godmother",
        skills={"stories"},
        entrance="sat at a loom where threads gleamed like morning frost",
        tags={"stories"},
    ),
}

DECORS = {
    "lanterns": Decor(
        id="lanterns",
        label="lantern garlands",
        phrase="strings of lanterns",
        fit_sizes={"small", "grand"},
        action="hung lantern garlands from hook to hook",
        sparkle="The lanterns trembled like tame stars",
        tags={"light"},
    ),
    "rose_ribbons": Decor(
        id="rose_ribbons",
        label="rose ribbons",
        phrase="rose-colored ribbons",
        fit_sizes={"small"},
        action="tied rose ribbons around the chairs and laid petals along the sill",
        sparkle="The ribbons stirred in the light like little sunset clouds",
        tags={"flowers", "light"},
    ),
    "gold_banners": Decor(
        id="gold_banners",
        label="gold banners",
        phrase="gold banners",
        fit_sizes={"grand"},
        action="raised gold banners between the tall pillars",
        sparkle="The banners shone high above like captured sunbeams",
        tags={"light", "grand"},
    ),
    "velvet_cushions": Decor(
        id="velvet_cushions",
        label="velvet cushions",
        phrase="deep velvet cushions",
        fit_sizes={"small", "grand"},
        action="set velvet cushions in a bright ring around the middle of the room and lit little lamps near them",
        sparkle="The cushions made the stone floor look soft and welcoming",
        tags={"comfort", "light"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nella", "Tessa", "Ivy", "Ada", "Poppy", "Wren"]
BOY_NAMES = ["Tobin", "Finn", "Eli", "Rowan", "Milo", "Ari", "Jory", "Leo"]
TRAITS = ["kind", "brave", "gentle", "quick-footed", "hopeful", "bright-eyed"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "castle": [(
        "What is a chamber in a castle?",
        "A chamber is a room inside a large house or castle. In fairy tales, it is often a quiet private room."
    )],
    "flowers": [(
        "Why do flowers make a room feel cheerful?",
        "Flowers add color and a sweet smell, so a room can feel brighter and more alive. They often help people feel calm and glad."
    )],
    "music": [(
        "Why can music cheer someone up?",
        "Music can change how a person feels by giving the heart something lovely to follow. A soft tune can make a sad room feel warm again."
    )],
    "sweet": [(
        "Why is a cake often part of a celebration?",
        "A cake is a special treat people share on joyful days. Sharing sweet food can make a celebration feel generous and festive."
    )],
    "stories": [(
        "Why do stories comfort people?",
        "Stories can remind people that brave and kind things are possible. They help hearts feel less alone."
    )],
    "shiny": [(
        "Why do shiny things seem magical in fairy tales?",
        "Shiny things catch the light and make ordinary rooms look special. In fairy tales, that sparkle often feels like a tiny kind of magic."
    )],
    "light": [(
        "Why does more light change the feeling of a room?",
        "Light helps people see clearly and makes shadows seem less heavy. A bright room often feels safer and happier than a dark one."
    )],
    "surprise": [(
        "What makes a surprise kind instead of mean?",
        "A kind surprise is chosen to delight or comfort someone. It fits what they love and does not scare or trick them."
    )],
}
KNOWLEDGE_ORDER = ["castle", "light", "flowers", "music", "sweet", "stories", "shiny", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    castle = f["castle"]
    recipient_cfg = f["recipient_cfg"]
    gift_cfg = f["gift_cfg"]
    decor_cfg = f["decor_cfg"]
    hero = f["hero"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "chamber" and "splendid".',
        f"Tell a gentle surprise story where {hero.id} prepares {gift_cfg.phrase} in {castle.name} to cheer {recipient_cfg.title}.",
        f"Write a happy fairy tale where a quiet chamber is changed with {decor_cfg.label} until it looks splendid and a lonely heart feels bright again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    castle = f["castle"]
    recipient_cfg = f["recipient_cfg"]
    gift_cfg = f["gift_cfg"]
    helper_cfg = f["helper_cfg"]
    decor_cfg = f["decor_cfg"]
    chamber = f["chamber"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to cheer {recipient.id} in {castle.name}. It is also about the quiet chamber that changed along with {recipient.id}'s feelings."
        ),
        (
            f"Why was {recipient.id} sad at the beginning?",
            f"{recipient.id} was worried about {recipient_cfg.worry}. That worry made the chamber feel hushed and lonely too."
        ),
        (
            f"What surprise did {hero.id} prepare?",
            f"{hero.id} asked {helper_cfg.title} for help and prepared {gift_cfg.phrase}. The gift was chosen because it suited what {recipient.id} loves."
        ),
        (
            "How did the chamber become splendid?",
            f"{hero.id} {decor_cfg.action}, and warm light filled the room. Because the chamber was both bright and decorated, it no longer felt plain and looked splendid."
        ),
    ]
    if f["surprise"] and f["happy"]:
        qa.append((
            f"How did {recipient.id} feel when the surprise was revealed?",
            f"{recipient.id} stopped in wonder and then felt joyful. The gift fit {recipient.pronoun('possessive')} heart, and the bright chamber helped the lonely feeling melt away."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily, with the chamber windows shining late into the night. {recipient.id} stayed close to {gift_cfg.label}, and {hero.id} watched the happy light on the walls."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"castle", "surprise"}
    tags |= set(f["gift_cfg"].tags)
    tags |= set(f["decor_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"kind={ent.kind}", f"type={ent.type}"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:18} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        castle="moonkeep",
        recipient="princess",
        gift="flower_crown",
        helper="gardener",
        decor="rose_ribbons",
        hero_name="Lina",
        hero_gender="girl",
        hero_trait="kind",
    ),
    StoryParams(
        castle="sunspire",
        recipient="prince",
        gift="silver_flute",
        helper="minstrel",
        decor="gold_banners",
        hero_name="Tobin",
        hero_gender="boy",
        hero_trait="brave",
    ),
    StoryParams(
        castle="moonkeep",
        recipient="dragon",
        gift="honey_cake",
        helper="baker",
        decor="lanterns",
        hero_name="Ivy",
        hero_gender="girl",
        hero_trait="gentle",
    ),
    StoryParams(
        castle="sunspire",
        recipient="dragon",
        gift="story_tapestry",
        helper="weaver",
        decor="velvet_cushions",
        hero_name="Finn",
        hero_gender="boy",
        hero_trait="hopeful",
    ),
]


# ---------------------------------------------------------------------------
# Rejection explanations
# ---------------------------------------------------------------------------
def explain_rejection(castle: Castle, recipient: RecipientCfg, gift: Gift,
                      helper: HelperCfg, decor: Decor) -> str:
    reasons: list[str] = []
    if not helper_can_make(helper, gift):
        reasons.append(
            f"{helper.title} cannot truly make {gift.phrase}"
        )
    if not gift_suits(recipient, gift):
        reasons.append(
            f"{gift.label} does not fit what {recipient.title} loves"
        )
    if not decor_fits(castle, decor):
        reasons.append(
            f"{decor.label} does not fit a {castle.chamber_size} chamber in {castle.name}"
        )
    if not reasons:
        return "(No story: this combination is not reasonable.)"
    return "(No story: " + "; ".join(reasons) + ".)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_make(H, G) :- helper_skill(H, S), gift_made_by(G, S).
suits(R, G)    :- recipient_likes(R, T), gift_tag(G, T).
fits(C, D)     :- chamber_size(C, Z), decor_fits(D, Z).

valid(C, R, G, H, D) :- castle(C), recipient(R), gift(G), helper(H), decor(D),
                        can_make(H, G), suits(R, G), fits(C, D).

outcome(C, R, G, H, D, happy) :- valid(C, R, G, H, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for castle_id, castle in CASTLES.items():
        lines.append(asp.fact("castle", castle_id))
        lines.append(asp.fact("chamber_size", castle_id, castle.chamber_size))
    for recipient_id, recipient in RECIPIENTS.items():
        lines.append(asp.fact("recipient", recipient_id))
        for like in sorted(recipient.likes):
            lines.append(asp.fact("recipient_likes", recipient_id, like))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("gift_made_by", gift_id, gift.made_by))
        for tag in sorted(gift.tags):
            lines.append(asp.fact("gift_tag", gift_id, tag))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for skill in sorted(helper.skills):
            lines.append(asp.fact("helper_skill", helper_id, skill))
    for decor_id, decor in DECORS.items():
        lines.append(asp.fact("decor", decor_id))
        for size in sorted(decor.fit_sizes):
            lines.append(asp.fact("decor_fits", decor_id, size))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_castle", params.castle),
        asp.fact("chosen_recipient", params.recipient),
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_decor", params.decor),
        "picked_happy :- outcome(C,R,G,H,D,happy), chosen_castle(C), chosen_recipient(R), chosen_gift(G), chosen_helper(H), chosen_decor(D).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_happy/0."))
    atoms = getattr(model, "symbols", lambda **_: [])(shown=True) if model is not None else []
    return "happy" if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for params in CURATED:
        expected = "happy" if (params.castle, params.recipient, params.gift, params.helper, params.decor) in py else "invalid"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(f"MISMATCH outcome for curated params: expected {expected}, got {got}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        if "chamber" not in sample.story.lower():
            raise StoryError("Smoke test story did not mention the chamber.")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a quiet chamber, a kind surprise, and a splendid happy ending."
    )
    ap.add_argument("--castle", choices=CASTLES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--decor", choices=DECORS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.castle and args.recipient and args.gift and args.helper and args.decor:
        castle = CASTLES[args.castle]
        recipient = RECIPIENTS[args.recipient]
        gift = GIFTS[args.gift]
        helper = HELPERS[args.helper]
        decor = DECORS[args.decor]
        if not valid_combo(castle, recipient, gift, helper, decor):
            raise StoryError(explain_rejection(castle, recipient, gift, helper, decor))

    combos = [
        combo for combo in valid_combos()
        if (args.castle is None or combo[0] == args.castle)
        and (args.recipient is None or combo[1] == args.recipient)
        and (args.gift is None or combo[2] == args.gift)
        and (args.helper is None or combo[3] == args.helper)
        and (args.decor is None or combo[4] == args.decor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    castle_id, recipient_id, gift_id, helper_id, decor_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        castle=castle_id,
        recipient=recipient_id,
        gift=gift_id,
        helper=helper_id,
        decor=decor_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.castle not in CASTLES:
        raise StoryError(f"(Invalid castle: {params.castle})")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Invalid recipient: {params.recipient})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Invalid gift: {params.gift})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.decor not in DECORS:
        raise StoryError(f"(Invalid decor: {params.decor})")

    castle = CASTLES[params.castle]
    recipient = RECIPIENTS[params.recipient]
    gift = GIFTS[params.gift]
    helper = HELPERS[params.helper]
    decor = DECORS[params.decor]
    if not valid_combo(castle, recipient, gift, helper, decor):
        raise StoryError(explain_rejection(castle, recipient, gift, helper, decor))

    world = tell(
        castle=castle,
        recipient_cfg=recipient,
        gift_cfg=gift,
        helper_cfg=helper,
        decor_cfg=decor,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
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
        print(asp_program("", "#show valid/5.\n#show outcome/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (castle, recipient, gift, helper, decor) combos:\n")
        for castle_id, recipient_id, gift_id, helper_id, decor_id in combos:
            print(f"  {castle_id:9} {recipient_id:9} {gift_id:15} {helper_id:9} {decor_id}")
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
            header = f"### {p.hero_name}: {p.gift} for {p.recipient} in {p.castle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
