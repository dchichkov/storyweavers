#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py
==================================================================================

A standalone story world for a tiny myth-shaped tale about a child on a forest
path who shares food with a strange traveler and discovers, to everyone's
surprise, that the traveler can transform. The child's generosity changes the
ending of the journey.

Seed request
------------
Words: path, subsequent
Features: Sharing, Surprise, Transformation
Style: Myth

World idea
----------
A child walks a mountain path carrying an offering to a hill shrine. Along the
way, a hungry traveler asks for help. The traveler is secretly a spirit in
disguise. If the child shares enough of the offering, the spirit reveals its
true form and transforms either the path or the final gift into a blessing.
If the child refuses or shares too little, the spirit stays hidden and the trip
ends as an ordinary, smaller story.

This world prefers a few strong variants over many weak ones:
- the carried gift must be shareable;
- the disguised spirit must be able to eat that gift;
- the surprise/transformation only happens when generosity clears a threshold;
- some explicit combinations are refused with a clear StoryError.

Run it
------
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py --traveler crane --gift rice_cakes --share all
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py --gift lantern
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py --all
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/path_subsequent_sharing_surprise_transformation_myth.py --verify
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
REVEAL_SHARE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    shareable: bool = False
    transformable: bool = False
    blessed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    path_desc: str
    shrine_desc: str
    weather_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    vessel: str
    portion_word: str
    portions: int
    edible: bool
    shareable: bool
    shrine_use: str
    transformed_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TravelerKind:
    id: str
    disguise: str
    true_form: str
    title: str
    appetite: set[str]
    hunger_line: str
    reveal_line: str
    blessing: str
    transformed_path: str
    gift_transformation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharePlan:
    id: str
    count: int
    phrase: str
    enough_for_reveal: bool
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


def _r_share_softens(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    traveler = world.get("traveler")
    if child.meters["shared"] >= THRESHOLD:
        sig = ("share_softens", int(child.meters["shared"]))
        if sig not in world.fired:
            world.fired.add(sig)
            traveler.memes["trust"] += 1
            child.memes["kindness"] += 1
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    traveler = world.get("traveler")
    if child.meters["shared"] >= REVEAL_SHARE_MIN and traveler.meters["fed"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            traveler.meters["revealed"] += 1
            traveler.meters["transformed"] += 1
            child.memes["wonder"] += 1
            out.append("__reveal__")
    return out


def _r_bless(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.get("traveler")
    path = world.get("path")
    gift = world.get("gift")
    if traveler.meters["transformed"] >= THRESHOLD:
        if ("bless_path",) not in world.fired:
            world.fired.add(("bless_path",))
            path.blessed = True
            path.meters["safe"] += 1
        if gift.meters["remaining"] >= THRESHOLD and ("bless_gift",) not in world.fired:
            world.fired.add(("bless_gift",))
            gift.transformable = True
            gift.meters["glow"] += 1
    return out


CAUSAL_RULES = [
    Rule("share_softens", "social", _r_share_softens),
    Rule("reveal", "myth", _r_reveal),
    Rule("bless", "myth", _r_bless),
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
        for s in produced:
            world.say(s)
    return produced


def compatible(gift: Gift, traveler: TravelerKind) -> bool:
    return gift.shareable and gift.edible and gift.id in traveler.appetite


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for gift_id, gift in GIFTS.items():
            for traveler_id, traveler in TRAVELERS.items():
                if compatible(gift, traveler):
                    combos.append((setting_id, gift_id, traveler_id))
    return combos


def explain_rejection(gift: Gift, traveler: TravelerKind) -> str:
    if not gift.shareable:
        return (
            f"(No story: {gift.phrase} cannot honestly be shared in this world, "
            f"so the tale would lose its Sharing turn. Pick a food gift instead.)"
        )
    if not gift.edible:
        return (
            f"(No story: {traveler.disguise} is hungry, but {gift.label} is not food, "
            f"so the traveler cannot eat it and the mythic test does not work.)"
        )
    return (
        f"(No story: {traveler.disguise} would not eat {gift.label} here, so the "
        f"surprise and transformation would have no grounded cause.)"
    )


def predict_reveal(gift: Gift, traveler: TravelerKind, share: SharePlan) -> bool:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl", role="child"))
    t = world.add(Entity(id="traveler", kind="character", type="spirit", role="traveler"))
    world.add(Entity(id="path", type="path", label="path"))
    g = world.add(Entity(id="gift", type="gift", label=gift.label))
    g.meters["remaining"] = max(0, gift.portions - share.count)
    if compatible(gift, traveler):
        child.meters["shared"] += share.count
        t.meters["fed"] += 1 if share.count > 0 else 0
    propagate(world, narrate=False)
    return t.meters["revealed"] >= THRESHOLD


def begin_journey(world: World, child: Entity, setting: Setting, gift: Gift, elder: Entity) -> None:
    child.memes["duty"] += 1
    gift.meters["remaining"] = gift.attrs["portions"]
    world.say(
        f"In the old days, when hills still listened and streams remembered names, "
        f"{child.id} set out for {setting.shrine_desc}."
    )
    world.say(
        f"{elder.label.capitalize()} had placed {gift.phrase} in {gift.vessel} and asked "
        f"{child.pronoun('object')} to carry it along {setting.path_desc}."
    )
    world.say(setting.weather_line)


def stranger_appears(world: World, child: Entity, traveler: Entity, traveler_cfg: TravelerKind) -> None:
    child.memes["caution"] += 1
    world.say(
        f"Halfway up the path, {child.id} saw {traveler_cfg.disguise} sitting on a stone, "
        f"small and still as if it had been waiting since dawn."
    )
    world.say(
        f'"{traveler_cfg.hunger_line}" said the stranger, and its voice sounded older '
        f"than the cedar trees."
    )


def choice_to_share(world: World, child: Entity, gift: Entity, gift_cfg: Gift,
                    share: SharePlan, traveler: Entity, traveler_cfg: TravelerKind) -> None:
    child.memes["hesitation"] += 1
    if share.count <= 0:
        world.say(
            f"{child.id} tightened {child.pronoun('possessive')} hands around {gift_cfg.vessel} "
            f"and remembered the shrine at the top of the hill."
        )
        world.say(
            f'"I must keep every {gift_cfg.portion_word} for the offering," '
            f"{child.pronoun()} whispered."
        )
        traveler.memes["sadness"] += 1
        return
    child.meters["shared"] += share.count
    traveler.meters["fed"] += 1
    gift.meters["remaining"] = max(0, gift_cfg.portions - share.count)
    world.say(
        f"{child.id} knelt beside the stone and gave the stranger {share.phrase}."
    )
    world.say(
        f"The hungry traveler ate slowly, as if each bite were being measured against "
        f"something deep and unseen."
    )
    propagate(world, narrate=False)


def surprise_reveal(world: World, child: Entity, traveler_cfg: TravelerKind, share: SharePlan) -> None:
    traveler = world.get("traveler")
    if traveler.meters["revealed"] < THRESHOLD:
        return
    world.say(
        f"Then came the surprise. The bent back straightened, the patched cloak shivered, "
        f"and the stranger rose shining in the shape of {traveler_cfg.true_form}."
    )
    world.say(
        f'"{traveler_cfg.reveal_line}" said the {traveler_cfg.title}. "Few share on a steep path, '
        f'and fewer still do so before the subsequent turn of fortune can be seen."'
    )


def bless_path_or_gift(world: World, child: Entity, setting: Setting, gift_cfg: Gift,
                       traveler_cfg: TravelerKind) -> None:
    traveler = world.get("traveler")
    gift = world.get("gift")
    if traveler.meters["transformed"] < THRESHOLD:
        return
    world.say(
        f"At once the world answered the transformation: {traveler_cfg.transformed_path}."
    )
    if gift.meters["remaining"] >= THRESHOLD:
        world.say(
            f"The food still in {gift_cfg.vessel} changed as well. {traveler_cfg.gift_transformation}"
        )
    else:
        world.say(
            f"Though nothing remained in the basket, the blessing ran ahead to the shrine "
            f"like golden water."
        )


def ordinary_arrival(world: World, child: Entity, setting: Setting, gift_cfg: Gift) -> None:
    gift = world.get("gift")
    if gift.meters["remaining"] >= THRESHOLD:
        world.say(
            f"The path stayed only a path. {child.id} climbed in silence and reached "
            f"{setting.shrine_desc} with the offering still plain and small."
        )
    else:
        world.say(
            f"The path stayed only a path. {child.id} climbed in silence, carrying an empty "
            f"{gift_cfg.vessel} and a puzzled heart."
        )


def shrine_ending(world: World, child: Entity, setting: Setting, gift_cfg: Gift,
                  traveler_cfg: TravelerKind) -> None:
    traveler = world.get("traveler")
    gift = world.get("gift")
    if traveler.meters["transformed"] >= THRESHOLD:
        child.memes["gratitude"] += 1
        world.say(
            f"At the shrine, the keepers lifted their lamps and gasped, for {gift_cfg.transformed_use}. "
            f"The blessing was enough for everyone who had climbed the hill that day."
        )
        world.say(
            f"From then on, people said that {setting.ending_image}, and that the surest way to call "
            f"a hidden spirit by its true name was simple sharing."
        )
    else:
        child.memes["reflection"] += 1
        if gift.meters["remaining"] >= THRESHOLD:
            world.say(
                f"At the shrine, {child.id} laid down the gift as asked. Yet all through the evening, "
                f"{child.pronoun()} remembered the hungry face beside the path."
            )
        else:
            world.say(
                f"At the shrine, {child.id} bowed with empty hands and told the whole story. The keepers "
                f"did not scold {child.pronoun('object')}, but they wondered who the stranger had been."
            )
        world.say(
            f"After that, travelers on that hill learned to carry a little extra, because an ordinary meeting "
            f"may hide a test no one sees at first."
        )


def tell(setting: Setting, gift_cfg: Gift, traveler_cfg: TravelerKind, share: SharePlan,
         child_name: str = "Nara", child_gender: str = "girl", elder_type: str = "mother",
         trait: str = "gentle") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=[trait, "young"]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type,
                             role="elder", label=elder_type))
    traveler = world.add(Entity(id="traveler", kind="character", type="spirit",
                                role="traveler", label=traveler_cfg.disguise))
    path = world.add(Entity(id="path", type="path", label="the path", transformable=True))
    gift = world.add(Entity(id="gift", type="gift", label=gift_cfg.label,
                            edible=gift_cfg.edible, shareable=gift_cfg.shareable,
                            attrs={"portions": gift_cfg.portions}))

    begin_journey(world, child, setting, gift_cfg, elder)
    world.para()
    stranger_appears(world, child, traveler, traveler_cfg)
    choice_to_share(world, child, gift, gift_cfg, share, traveler, traveler_cfg)
    world.para()

    if compatible(gift_cfg, traveler_cfg) and share.count > 0:
        propagate(world, narrate=False)

    if traveler.meters["revealed"] >= THRESHOLD:
        surprise_reveal(world, child, traveler_cfg, share)
        bless_path_or_gift(world, child, setting, gift_cfg, traveler_cfg)
    else:
        ordinary_arrival(world, child, setting, gift_cfg)

    world.para()
    shrine_ending(world, child, setting, gift_cfg, traveler_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        traveler=traveler,
        path=path,
        gift=gift,
        setting=setting,
        gift_cfg=gift_cfg,
        traveler_cfg=traveler_cfg,
        share=share,
        revealed=traveler.meters["revealed"] >= THRESHOLD,
        transformed=traveler.meters["transformed"] >= THRESHOLD,
        path_blessed=path.blessed,
        shared=share.count,
        remaining=max(0, gift_cfg.portions - share.count),
        predicted_reveal=predict_reveal(gift_cfg, traveler_cfg, share) if compatible(gift_cfg, traveler_cfg) else False,
    )
    return world


SETTINGS = {
    "cedar_hill": Setting(
        "cedar_hill",
        "the cedar hill",
        "a narrow path under cedar boughs",
        "the little hill shrine above the clouds",
        "Mist moved between the trunks, and every drop of dew looked like a tiny pearl.",
        "the cedar path never seemed lonely again",
        tags={"hill", "shrine"},
    ),
    "moon_steps": Setting(
        "moon_steps",
        "the moonlit steps",
        "an old stone path cut into the mountain",
        "the moon shrine at the high gate",
        "The morning moon still hung pale above the ridge, and the stones held the night's cool breath.",
        "the mountain steps shone softly after dusk",
        tags={"mountain", "moon"},
    ),
    "spring_vale": Setting(
        "spring_vale",
        "the spring vale",
        "a winding path beside clear water",
        "the spring shrine where bells rang in the wind",
        "Swallows circled above the stream, and the path smelled of wet grass and sun-warmed rock.",
        "the valley path was spoken of as a kindly road",
        tags={"stream", "bells"},
    ),
}

GIFTS = {
    "rice_cakes": Gift(
        "rice_cakes",
        "rice cakes",
        "a basket of round rice cakes wrapped in leaves",
        "the basket",
        "cake",
        3,
        edible=True,
        shareable=True,
        shrine_use="for the noon offering",
        transformed_use="the few rice cakes had become a shining feast without losing their gentle shape",
        tags={"food", "cakes"},
    ),
    "pears": Gift(
        "pears",
        "pears",
        "a willow tray with three sweet pears",
        "the willow tray",
        "pear",
        3,
        edible=True,
        shareable=True,
        shrine_use="for the evening altar",
        transformed_use="the remaining pears gleamed like lantern moons and filled the hall with summer scent",
        tags={"food", "fruit"},
    ),
    "sesame_buns": Gift(
        "sesame_buns",
        "sesame buns",
        "a cloth bundle of warm sesame buns",
        "the cloth bundle",
        "bun",
        4,
        edible=True,
        shareable=True,
        shrine_use="for the travelers' bowl",
        transformed_use="the buns broke open into sweet steam and there was enough for every waiting hand",
        tags={"food", "bread"},
    ),
    "lantern": Gift(
        "lantern",
        "lantern",
        "a brass lantern for the shrine",
        "both hands",
        "piece",
        1,
        edible=False,
        shareable=False,
        shrine_use="to hang before the altar",
        transformed_use="the lantern's old brass flashed like sunrise",
        tags={"object", "light"},
    ),
}

TRAVELERS = {
    "crane": TravelerKind(
        "crane",
        "an old gray beggar with bright eyes",
        "a silver crane taller than a door",
        "Crane of the High Wind",
        appetite={"rice_cakes", "pears"},
        hunger_line="Child, I have walked since moonset. Will you share a little food?",
        reveal_line="I wore small feathers beneath that old cloak",
        blessing="wind",
        transformed_path="The stones lost their sharpness, and white feathers drifted over the path without falling",
        gift_transformation="Each simple bite now carried the freshness of mountain air.",
        tags={"crane", "wind"},
    ),
    "fox": TravelerKind(
        "fox",
        "a thin traveler in a patched saffron robe",
        "a fox-spirit with nine bright tails",
        "Fox of the Hidden Hearth",
        appetite={"rice_cakes", "sesame_buns"},
        hunger_line="Little one, the road is long. Might your basket spare one mouthful?",
        reveal_line="I wore whiskers beneath my smile",
        blessing="hearth",
        transformed_path="The cold shade warmed, and little lights flickered along the roots like banked coals",
        gift_transformation="A sweet, honeyed warmth filled the food, and it seemed to multiply as kindly fire multiplies light.",
        tags={"fox", "hearth"},
    ),
    "carp": TravelerKind(
        "carp",
        "a soaked old ferryman wrapped in reeds",
        "a river carp bright as beaten gold",
        "Carp of the Returning Spring",
        appetite={"pears", "sesame_buns"},
        hunger_line="I have come far from the water and have no strength left. Will you spare a bite?",
        reveal_line="I wore scales beneath those dripping reeds",
        blessing="spring",
        transformed_path="Water sang under the stones, and the dust of the path turned clear and cool",
        gift_transformation="The gift tasted of clear spring water and freshness after rain.",
        tags={"carp", "water"},
    ),
}

SHARES = {
    "none": SharePlan("none", 0, "nothing at all", False, tags={"refusal"}),
    "one": SharePlan("one", 1, "one small portion", False, tags={"small_share"}),
    "half": SharePlan("half", 2, "half of the gift", True, tags={"large_share"}),
    "all": SharePlan("all", 3, "nearly all of the gift", True, tags={"great_share"}),
}

GIRL_NAMES = ["Nara", "Aki", "Mina", "Sora", "Yuna", "Hana", "Kiri", "Emi"]
BOY_NAMES = ["Ren", "Taro", "Kaito", "Haru", "Jun", "Soma", "Daichi", "Yori"]
TRAITS = ["gentle", "thoughtful", "brave", "patient", "kind", "quiet"]


@dataclass
class StoryParams:
    setting: str
    gift: str
    traveler: str
    share: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "shrine": [
        ("What is a shrine?",
         "A shrine is a special place where people go to pray, leave offerings, or show respect. In stories, shrines often feel close to the spirit world.")
    ],
    "offering": [
        ("Why do people bring offerings in stories?",
         "An offering is a gift given with respect or thanks. In myths, it shows care, humility, or hope for blessing.")
    ],
    "sharing": [
        ("Why is sharing important?",
         "Sharing means giving some of what you have to help someone else. It can turn a hard moment into a kinder one for everyone.")
    ],
    "surprise": [
        ("What is a surprise in a story?",
         "A surprise is something unexpected that changes how characters understand what is happening. Good surprises still fit the story once you look back at the clues.")
    ],
    "transformation": [
        ("What does transformation mean in a myth?",
         "Transformation means something changes into a new form. In myths, that change often reveals a hidden truth or reward.")
    ],
    "crane": [
        ("Why do cranes matter in myths?",
         "Cranes often stand for grace, height, and messages between earth and sky. A crane spirit can feel wise and otherworldly.")
    ],
    "fox": [
        ("Why do fox spirits appear in tales?",
         "Fox spirits are clever magical beings in many old stories. They often hide their true nature until someone shows kindness or foolishness.")
    ],
    "carp": [
        ("Why is a carp special in stories?",
         "A carp is a strong river fish, and in stories it can stand for endurance and change. Water creatures often bring blessings about renewal.")
    ],
    "path": [
        ("Why does a path matter in myths?",
         "A path is more than a road in a myth. It often stands for a choice, a test, or the way a person grows.")
    ],
}

KNOWLEDGE_ORDER = ["path", "sharing", "surprise", "transformation", "shrine",
                   "offering", "crane", "fox", "carp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    gift = f["gift_cfg"]
    traveler = f["traveler_cfg"]
    share = f["share"]
    if f["revealed"]:
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "path" and the word "subsequent".',
            f"Tell a gentle myth where {child.id} carries {gift.label} to a shrine, shares {share.phrase} with {traveler.disguise}, and discovers a magical transformation.",
            f"Write a child-facing story about sharing on a mountain path, with a surprise reveal and a shining ending."
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "path" and the word "subsequent".',
        f"Tell a myth where {child.id} carries {gift.label} to a shrine and meets {traveler.disguise} on the path, but the hidden wonder is not fully revealed.",
        f"Write a story about a child learning that sharing matters, even when the surprise comes later or stays hidden."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    gift = f["gift_cfg"]
    traveler = f["traveler_cfg"]
    share = f["share"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a young child walking {setting.path_desc} with {gift.phrase}. "
            f"{elder.label.capitalize()} had sent {child.pronoun('object')} to the shrine."
        ),
        (
            f"What was {child.id} carrying, and where was {child.pronoun()} going?",
            f"{child.id} was carrying {gift.phrase} as an offering. {child.pronoun().capitalize()} was taking it to {setting.shrine_desc}."
        ),
        (
            "Who did the child meet on the path?",
            f"{child.id} met {traveler.disguise} sitting beside the path. The stranger asked for food in a voice that sounded very old."
        ),
    ]
    if share.count <= 0:
        qa.append((
            f"Did {child.id} share the gift?",
            f"No. {child.id} kept the whole offering because {child.pronoun()} was thinking about the shrine and the task from {elder.label}. "
            f"That choice left the mystery hidden."
        ))
    else:
        qa.append((
            f"How did {child.id} help the stranger?",
            f"{child.id} shared {share.phrase} from the offering. That kindness fed the traveler and became the cause of everything that changed afterward."
        ))
    if f["revealed"]:
        qa.append((
            "What was the surprise?",
            f"The stranger was not ordinary at all. After being fed, {traveler.disguise} transformed into {traveler.true_form}, showing that the meeting had been a hidden test."
        ))
        qa.append((
            "How did the transformation change the ending?",
            f"The transformation blessed the path and the offering, so the gift became more than it had been before. "
            f"Because {child.id} shared first, there was enough blessing for many people at the shrine."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The child reached the shrine without seeing any shining spirit reveal. Even so, the meeting stayed in {child.pronoun('possessive')} mind and taught a quiet lesson about carrying a little extra kindness."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"path", "sharing", "shrine", "offering"}
    if f["revealed"]:
        tags |= {"surprise", "transformation"}
    tags |= set(f["traveler_cfg"].tags)
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
        flags = [n for n, on in (
            ("edible", e.edible),
            ("shareable", e.shareable),
            ("transformable", e.transformable),
            ("blessed", e.blessed),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cedar_hill", "rice_cakes", "crane", "half", "Nara", "girl", "mother", "gentle"),
    StoryParams("moon_steps", "sesame_buns", "fox", "all", "Ren", "boy", "father", "brave"),
    StoryParams("spring_vale", "pears", "carp", "one", "Mina", "girl", "mother", "thoughtful"),
    StoryParams("cedar_hill", "pears", "crane", "none", "Jun", "boy", "father", "quiet"),
]


ASP_RULES = r"""
share_reveal(S) :- share(S), share_count(S, C), reveal_min(M), C >= M.
compatible(G, T) :- gift(G), traveler(T), shareable(G), edible(G), appetite(T, G).
valid(St, G, T) :- setting(St), compatible(G, T).

revealed :- chosen_gift(G), chosen_traveler(T), chosen_share(S),
            compatible(G, T), share_reveal(S), share_count(S, C), C > 0.
outcome(revealed) :- revealed.
outcome(ordinary) :- not revealed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if gift.shareable:
            lines.append(asp.fact("shareable", gid))
        if gift.edible:
            lines.append(asp.fact("edible", gid))
    for tid, traveler in TRAVELERS.items():
        lines.append(asp.fact("traveler", tid))
        for g in sorted(traveler.appetite):
            lines.append(asp.fact("appetite", tid, g))
    for sid, share in SHARES.items():
        lines.append(asp.fact("share", sid))
        lines.append(asp.fact("share_count", sid, share.count))
    lines.append(asp.fact("reveal_min", REVEAL_SHARE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_traveler", params.traveler),
        asp.fact("chosen_share", params.share),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if compatible(GIFTS[params.gift], TRAVELERS[params.traveler]) and SHARES[params.share].count >= REVEAL_SHARE_MIN and SHARES[params.share].count > 0:
        return "revealed"
    return "ordinary"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a child on a path, a hidden spirit, and the power of sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gift and args.traveler:
        gift = GIFTS[args.gift]
        traveler = TRAVELERS[args.traveler]
        if not compatible(gift, traveler):
            raise StoryError(explain_rejection(gift, traveler))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.gift is None or c[1] == args.gift)
        and (args.traveler is None or c[2] == args.traveler)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, gift, traveler = rng.choice(sorted(combos))
    share = args.share or rng.choice(sorted(SHARES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, gift, traveler, share, name, gender, elder, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GIFTS[params.gift],
        TRAVELERS[params.traveler],
        SHARES[params.share],
        params.child_name,
        params.child_gender,
        params.elder,
        params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, gift, traveler) combos:\n")
        for setting, gift, traveler in combos:
            print(f"  {setting:12} {gift:12} {traveler}")
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
            header = f"### {p.child_name}: {p.gift} with {p.traveler} on {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
