#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py
=============================================================================

A standalone storyworld for a small folk-tale domain: in a dry village, a child
must coax a magic cloud to water a hungry garden. The child remembers a
grandmother's lesson in a flashback, chooses a gift for the cloud, and earns a
bonus blessing when the gift truly fits. The world model tracks physical change
(wilt, moisture, bloom) and emotional change (hope, worry, courage), then
renders complete child-facing stories from that state.

Seed words carried into the generated stories:
    granulate, cloud, bonus

Features:
    Flashback, Magic

Style:
    Folk Tale

Run it
------
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py --gift song --need seedlings
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py --gift pebble   # rejected: weak gift
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/granulate_cloud_bonus_flashback_magic_folk_tale.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.label or self.type)


@dataclass
class Need:
    id: str
    crop: str
    patch: str
    trouble: str
    dry_image: str
    saved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    sense: int
    kindness: int
    songlike: bool = False
    bright: bool = False
    living: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class CloudKind:
    id: str
    name: str
    color: str
    arrival: str
    voice: str
    bonus: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    title: str
    line: str
    granulate_line: str
    memory: str
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


def _r_water_helps(world: World) -> list[str]:
    out: list[str] = []
    garden = world.get("garden")
    child = world.get("child")
    cloud = world.get("cloud")
    if cloud.meters["rain"] < THRESHOLD:
        return out
    sig = ("water_helps",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    garden.meters["moisture"] += 1
    garden.meters["wilt"] = 0.0
    child.memes["hope"] += 1
    out.append("__rain__")
    return out


def _r_bonus_bloom(world: World) -> list[str]:
    out: list[str] = []
    garden = world.get("garden")
    cloud = world.get("cloud")
    if cloud.meters["bonus"] < THRESHOLD or garden.meters["moisture"] < THRESHOLD:
        return out
    sig = ("bonus_bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    garden.meters["bloom"] += 1
    out.append("__bonus__")
    return out


CAUSAL_RULES = [
    Rule(name="water_helps", tag="physical", apply=_r_water_helps),
    Rule(name="bonus_bloom", tag="physical", apply=_r_bonus_bloom),
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


def gift_fits(gift: Gift, cloud: CloudKind) -> bool:
    if gift.sense < SENSE_MIN:
        return False
    if cloud.id == "song_cloud":
        return gift.songlike or gift.kindness >= 3
    if cloud.id == "silver_cloud":
        return gift.bright or gift.kindness >= 3
    if cloud.id == "moss_cloud":
        return gift.living or gift.kindness >= 3
    return gift.kindness >= 2


def earns_bonus(gift: Gift, spell: Spell, cloud: CloudKind) -> bool:
    if not gift_fits(gift, cloud):
        return False
    if gift.kindness >= 3:
        return True
    if cloud.id == "song_cloud" and spell.id == "lullaby":
        return True
    if cloud.id == "silver_cloud" and spell.id == "bell":
        return True
    if cloud.id == "moss_cloud" and spell.id == "dew":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for need_id in NEEDS:
        for gift_id, gift in GIFTS.items():
            for cloud_id, cloud in CLOUDS.items():
                if gift_fits(gift, cloud):
                    combos.append((need_id, gift_id, cloud_id))
    return combos


def predict_help(need: Need, gift: Gift, cloud: CloudKind, spell: Spell) -> dict:
    return {
        "fits": gift_fits(gift, cloud),
        "bonus": earns_bonus(gift, spell, cloud),
        "bloom": 1 if earns_bonus(gift, spell, cloud) else 0,
        "rain": 1 if gift_fits(gift, cloud) else 0,
    }


def opening(world: World, child: Entity, elder: Entity, need: Need) -> None:
    child.memes["love"] += 1
    child.memes["worry"] += 1
    world.say(
        f"In a small valley where hills held the wind like folded hands, {child.id} "
        f"lived with {child.pronoun('possessive')} {elder.label_word} beside {need.patch}."
    )
    world.say(
        f"There they tended {need.crop}, but the summer had turned hard and bright, "
        f"and {need.dry_image}."
    )
    world.say(
        f"{child.id} touched the dry ground and whispered that the little field looked thirsty."
    )


def elder_charge(world: World, child: Entity, elder: Entity, need: Need) -> None:
    world.say(
        f'{elder.label_word.capitalize()} said, "If no rain comes soon, {need.trouble}. '
        f'Go to the hill of winds, little one, and ask the sky for mercy."'
    )


def journey(world: World, child: Entity, cloud: CloudKind) -> None:
    child.memes["courage"] += 1
    world.say(
        f"So {child.id} climbed the path of thyme and stone until the air grew cool. "
        f"Above the hill, {cloud.arrival}"
    )


def flashback(world: World, child: Entity, elder: Entity, spell: Spell) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Then a memory came back like a lamp lit in daylight. Once, in winter, "
        f"{elder.label_word} had taught {child.id} {spell.title}."
    )
    world.say(
        f"{spell.memory} In that flashback, the old lesson felt warm in {child.id}'s chest."
    )


def offer(world: World, child: Entity, gift: Gift, cloud: CloudKind, spell: Spell) -> None:
    pred = predict_help(world.facts["need_cfg"], gift, cloud, spell)
    world.facts["predicted_bonus"] = pred["bonus"]
    world.facts["predicted_rain"] = pred["rain"]
    child.memes["hope"] += 1
    world.say(
        f'{child.id} lifted {gift.phrase} and called, "{cloud.voice} '
        f'{spell.line} {spell.granulate_line}"'
    )
    world.say(
        f"The child offered {gift.label} not as a trade, but as a true gift."
    )


def reject(world: World, cloud_ent: Entity, cloud: CloudKind, gift: Gift) -> None:
    cloud_ent.memes["distance"] += 1
    world.say(
        f"The {cloud.name} drifted in a slow circle and did not come lower. "
        f'"A sky-heart is not moved by {gift.label} alone," it murmured.'
    )


def accept(world: World, child: Entity, cloud_ent: Entity, gift: Gift, cloud: CloudKind) -> None:
    cloud_ent.memes["kindness"] += 1
    child.memes["relief"] += 1
    world.say(
        f"The {cloud.name} stooped until its silver edge brushed the hill grass. "
        f'"You have brought {gift.label} with an open hand," it said.'
    )


def rain_scene(world: World, need: Need, cloud_ent: Entity, cloud: CloudKind) -> None:
    cloud_ent.meters["rain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once the {cloud.name} loosened itself over the valley. "
        f"A gentle cloud-shadow rolled across the field, and rain began to fall."
    )
    world.say(
        f"The dust darkened, the roots drank deep, and {need.saved_image}."
    )


def bonus_scene(world: World, need: Need, cloud_ent: Entity, cloud: CloudKind) -> None:
    cloud_ent.meters["bonus"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before the last drops were gone, the cloud gave a bonus blessing: {cloud.bonus}."
    )
    world.say(
        "The whole valley seemed to hold its breath, and then smile."
    )


def homecoming(world: World, child: Entity, elder: Entity, need: Need) -> None:
    garden = world.get("garden")
    if garden.meters["bloom"] >= THRESHOLD:
        ending = "tiny blossoms opened where only worry had been"
    else:
        ending = "the leaves stood up green and straight again"
    world.say(
        f"When {child.id} came home, {elder.label_word} stepped to the door and saw that {ending}."
    )
    world.say(
        f'Together they knelt beside {need.patch}, and {elder.label_word} said, '
        f'"A kind gift and a remembered lesson can travel farther than fear."'
    )


def tell(
    need: Need,
    gift: Gift,
    cloud: CloudKind,
    spell: Spell,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["gentle", "brave"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    garden = world.add(Entity(
        id="garden",
        type="garden",
        label=need.patch,
        phrase=need.patch,
        tags=set(need.tags),
    ))
    cloud_ent = world.add(Entity(
        id="cloud",
        type="cloud",
        label=cloud.name,
        phrase=cloud.name,
        tags=set(cloud.tags),
    ))
    garden.meters["wilt"] = 1.0

    opening(world, child, elder, need)
    elder_charge(world, child, elder, need)

    world.para()
    journey(world, child, cloud)
    flashback(world, child, elder, spell)

    world.para()
    offer(world, child, gift, cloud, spell)
    fits = gift_fits(gift, cloud)

    if fits:
        accept(world, child, cloud_ent, gift, cloud)
        world.para()
        rain_scene(world, need, cloud_ent, cloud)
        if earns_bonus(gift, spell, cloud):
            bonus_scene(world, need, cloud_ent, cloud)
        world.para()
        homecoming(world, child, elder, need)
        outcome = "bonus" if world.get("garden").meters["bloom"] >= THRESHOLD else "rain"
    else:
        reject(world, cloud_ent, cloud, gift)
        world.say(
            f"{child.id} bowed, ashamed for a moment, and understood that magic listens best to care."
        )
        outcome = "refused"

    world.facts.update(
        child=child,
        elder=elder,
        cloud=cloud,
        cloud_ent=cloud_ent,
        need_cfg=need,
        gift=gift,
        spell=spell,
        outcome=outcome,
        helped=fits,
        bonus=world.get("garden").meters["bloom"] >= THRESHOLD,
        garden=world.get("garden"),
    )
    return world


@dataclass
class StoryParams:
    need: str
    gift: str
    cloud: str
    spell: str
    child_name: str
    child_gender: str
    elder_type: str
    seed: Optional[int] = None


NEEDS = {
    "beans": Need(
        id="beans",
        crop="climbing beans",
        patch="a narrow bean patch",
        trouble="the bean vines will curl into brown strings",
        dry_image="the bean leaves had folded like tired little hands",
        saved_image="the bean leaves uncurling one by one looked like many green fingers waving",
        tags={"garden", "beans"},
    ),
    "seedlings": Need(
        id="seedlings",
        crop="pumpkin seedlings",
        patch="a round pumpkin bed",
        trouble="the seedlings will sink back into the dust",
        dry_image="the small seedling stems bent as if they were listening to the empty soil",
        saved_image="the seedling cups lifted and held bright drops on their rims",
        tags={"garden", "seedling"},
    ),
    "herbs": Need(
        id="herbs",
        crop="mint and sage",
        patch="a little herb square",
        trouble="the herbs will lose their smell and crumble dry",
        dry_image="the herb leaves had gone dull, and even the mint had forgotten its cool scent",
        saved_image="the herb square breathed out fresh scent so strong that the air itself felt awake",
        tags={"garden", "herb"},
    ),
}

GIFTS = {
    "song": Gift(
        id="song",
        label="a song",
        phrase="a small song carried in both hands of the heart",
        sense=3,
        kindness=3,
        songlike=True,
        tags={"song", "kindness"},
    ),
    "bread": Gift(
        id="bread",
        label="warm bread",
        phrase="a heel of warm bread wrapped in cloth",
        sense=3,
        kindness=3,
        tags={"bread", "kindness"},
    ),
    "flower": Gift(
        id="flower",
        label="a moonflower",
        phrase="a moonflower still shining with dawn",
        sense=2,
        kindness=2,
        bright=True,
        living=True,
        tags={"flower"},
    ),
    "bell": Gift(
        id="bell",
        label="a brass bell",
        phrase="a little brass bell on a red thread",
        sense=2,
        kindness=2,
        bright=True,
        tags={"bell"},
    ),
    "moss": Gift(
        id="moss",
        label="soft moss",
        phrase="a cushion of soft moss cupped like a nest",
        sense=2,
        kindness=2,
        living=True,
        tags={"moss"},
    ),
    "pebble": Gift(
        id="pebble",
        label="a pebble",
        phrase="a plain gray pebble from the path",
        sense=1,
        kindness=0,
        tags={"pebble"},
    ),
}

CLOUDS = {
    "song_cloud": CloudKind(
        id="song_cloud",
        name="Song Cloud",
        color="blue",
        arrival="a blue cloud shaped like a folded harp drifted out from the west",
        voice="Sky of listening, hear me.",
        bonus="each bean tip wore a shining bead of rain, neat as pearls on a string",
        tags={"cloud", "song_cloud"},
    ),
    "silver_cloud": CloudKind(
        id="silver_cloud",
        name="Silver Cloud",
        color="silver",
        arrival="a silver cloud with bright edges came gliding as quietly as a swan",
        voice="Sky of brightness, hear me.",
        bonus="a silver sheen stayed on the leaves until sunset, so the whole bed glimmered like treasure",
        tags={"cloud", "silver_cloud"},
    ),
    "moss_cloud": CloudKind(
        id="moss_cloud",
        name="Moss Cloud",
        color="green-gray",
        arrival="a green-gray cloud, soft as a hillside sheep, drifted low over the stones",
        voice="Sky of growing things, hear me.",
        bonus="a ring of tiny white mushrooms rose by the field wall as if the rain had told the earth a secret",
        tags={"cloud", "moss_cloud"},
    ),
}

SPELLS = {
    "lullaby": Spell(
        id="lullaby",
        title="the Lullaby of Soft Rain",
        line="Come lightly, come kindly, cloud over stone and plain.",
        granulate_line="Granulate the hard dust into dark, drinkable earth.",
        memory="The old voice had said that true words must sound like kindness before they sound like power.",
        tags={"flashback", "magic", "lullaby"},
    ),
    "bell": Spell(
        id="bell",
        title="the Bell-Call of High Air",
        line="Ring once for mercy, ring twice for rain.",
        granulate_line="Granulate the sun-baked crust and loosen the sleeping roots below.",
        memory="The elder had tapped a cup with a spoon and said that some spells wake the sky by shining.",
        tags={"flashback", "magic", "bell"},
    ),
    "dew": Spell(
        id="dew",
        title="the Dew-Mother's Saying",
        line="Soft step, sky sheep; soft fleece, sky rain.",
        granulate_line="Granulate the dry clods into crumbs gentle enough for roots to drink through.",
        memory="The elder had laughed and crumbled old soil in one hand, teaching that even magic must know the feel of earth.",
        tags={"flashback", "magic", "dew"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tala", "Nora", "Esme", "Pia", "Runa"]
BOY_NAMES = ["Toma", "Ivo", "Nico", "Luka", "Milo", "Sami", "Ren", "Teo"]


KNOWLEDGE = {
    "cloud": [
        (
            "What is a cloud?",
            "A cloud is a big group of tiny water drops or ice crystals floating in the sky. When some clouds grow heavy, they can bring rain.",
        )
    ],
    "garden": [
        (
            "Why do plants need water?",
            "Plants need water to stay firm and keep growing. When the soil gets too dry, leaves droop and the plant can weaken.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a moment when the story remembers something that happened earlier. It helps explain why a character knows or feels something now.",
        )
    ],
    "magic": [
        (
            "What is magic in a folk tale?",
            "In a folk tale, magic is a special power that can change the world in surprising ways. It often listens to courage, kindness, or wise words.",
        )
    ],
    "bonus": [
        (
            "What is a bonus?",
            "A bonus is something extra that comes on top of what you already hoped for. It is like an unexpected extra gift.",
        )
    ],
    "beans": [
        (
            "Why do bean plants climb?",
            "Bean plants send out long stems that like to climb upward toward light. Gardeners often give them poles or strings to hold.",
        )
    ],
    "seedling": [
        (
            "What is a seedling?",
            "A seedling is a very young plant that has only just begun to grow from a seed. It is small and needs gentle care.",
        )
    ],
    "herb": [
        (
            "What is an herb garden?",
            "An herb garden is a little place where plants like mint or sage are grown for their leaves and smell. Many herbs are used in cooking or tea.",
        )
    ],
    "song": [
        (
            "Why might a song matter in a folk tale?",
            "Songs in folk tales can help characters remember brave words or call on magic. A song also shows feeling, not just cleverness.",
        )
    ],
}


def pair_child(hero: Entity) -> str:
    return f"a little {hero.type} named {hero.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    need = f["need_cfg"]
    gift = f["gift"]
    cloud = f["cloud"]
    spell = f["spell"]
    if f["outcome"] == "bonus":
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the words "granulate", "cloud", and "bonus".',
            f"Tell a magical folk tale where {child.id} climbs a hill to save {need.crop}, remembers an elder's lesson in a flashback, and wins rain plus a bonus blessing from the {cloud.name}.",
            f"Write a gentle tale where a child offers {gift.label} to a magic cloud, speaks {spell.title}, and comes home to a changed garden.",
        ]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "granulate", "cloud", and "bonus".',
        f"Tell a magical story where {child.id} uses a flashback to remember an old sky-spell and asks the {cloud.name} for rain to help {need.crop}.",
        f"Write a simple folk tale where kindness matters more than force when a child speaks to a magic cloud.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    need = f["need_cfg"]
    gift = f["gift"]
    cloud = f["cloud"]
    spell = f["spell"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_child(child)} who wanted to save {need.crop}, and {child.pronoun('possessive')} {elder.label_word} who sent {child.pronoun('object')} to ask the sky for help.",
        ),
        (
            "Why did the child go up the hill?",
            f"{child.id} went because the garden was drying out and {need.trouble}. The hill was the place where the child could speak to the magic cloud.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {child.id} remembered {elder.label_word} teaching {spell.title}. The memory gave {child.pronoun('object')} the right words and the courage to use them.",
        ),
        (
            f"What did {child.id} offer the {cloud.name}?",
            f"{child.id} offered {gift.label}. The gift mattered because the cloud listened for kindness, not just for noise.",
        ),
    ]
    if outcome in {"rain", "bonus"}:
        qa.append(
            (
                f"How did the cloud help the garden?",
                f"The {cloud.name} sent rain over the field, so the dry soil darkened and the plants could drink. That changed the garden from thirsty and drooping to alive and hopeful again.",
            )
        )
    if outcome == "bonus":
        qa.append(
            (
                "What was the bonus blessing?",
                f"The bonus blessing was that {cloud.bonus}. It was something extra beyond plain rain, which proved the cloud had been deeply pleased.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the garden not only saved but shining with new beauty. When {child.id} came home, the changed field showed that remembered wisdom and kindness had worked together.",
            )
        )
    elif outcome == "rain":
        qa.append(
            (
                "Did the child get a bonus too?",
                f"No extra wonder appeared after the rain, but the garden was still saved. The good ending came from the water itself and from the child using the old lesson well.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"cloud", "garden", "flashback", "magic", "bonus"}
    tags |= set(f["need_cfg"].tags)
    tags |= set(f["gift"].tags)
    out: list[tuple[str, str]] = []
    order = ["cloud", "garden", "flashback", "magic", "bonus", "beans", "seedling", "herb", "song"]
    for tag in order:
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        need="beans",
        gift="song",
        cloud="song_cloud",
        spell="lullaby",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        need="seedlings",
        gift="bell",
        cloud="silver_cloud",
        spell="bell",
        child_name="Luka",
        child_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        need="herbs",
        gift="moss",
        cloud="moss_cloud",
        spell="dew",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        need="beans",
        gift="bread",
        cloud="silver_cloud",
        spell="lullaby",
        child_name="Milo",
        child_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        need="seedlings",
        gift="flower",
        cloud="moss_cloud",
        spell="dew",
        child_name="Runa",
        child_gender="girl",
        elder_type="grandfather",
    ),
]


def explain_rejection(gift: Gift, cloud: CloudKind) -> str:
    if gift.sense < SENSE_MIN:
        return (
            f"(No story: {gift.label} is too weak or thoughtless for this tale. "
            f"The gift must be offered with some real care so the cloud has a sensible reason to answer.)"
        )
    return (
        f"(No story: {gift.label} does not fit the nature of the {cloud.name}. "
        f"Choose a gift that sings, shines, grows, or shows deeper kindness.)"
    )


def outcome_of(params: StoryParams) -> str:
    bonus = earns_bonus(GIFTS[params.gift], SPELLS[params.spell], CLOUDS[params.cloud])
    return "bonus" if bonus else "rain"


ASP_RULES = r"""
% reasonableness gate
valid_need(N) :- need(N).
sensible_gift(G) :- gift(G), sense(G, S), sense_min(M), S >= M.

fits(G, song_cloud)   :- sensible_gift(G), songlike(G).
fits(G, silver_cloud) :- sensible_gift(G), bright(G).
fits(G, moss_cloud)   :- sensible_gift(G), living(G).
fits(G, C)            :- sensible_gift(G), kindness(G, K), K >= 3, cloud(C).

valid(N, G, C) :- need(N), gift(G), cloud(C), fits(G, C).

% bonus logic
bonus_gift(G, C, S) :- fits(G, C), kindness(G, K), K >= 3, spell(S).
bonus_gift(G, song_cloud, lullaby) :- fits(G, song_cloud), gift(G).
bonus_gift(G, silver_cloud, bell)  :- fits(G, silver_cloud), gift(G).
bonus_gift(G, moss_cloud, dew)     :- fits(G, moss_cloud), gift(G).

outcome(bonus) :- chosen_gift(G), chosen_cloud(C), chosen_spell(S), bonus_gift(G, C, S).
outcome(rain)  :- chosen_gift(G), chosen_cloud(C), chosen_spell(S), fits(G, C),
                  not bonus_gift(G, C, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("sense", gid, gift.sense))
        lines.append(asp.fact("kindness", gid, gift.kindness))
        if gift.songlike:
            lines.append(asp.fact("songlike", gid))
        if gift.bright:
            lines.append(asp.fact("bright", gid))
        if gift.living:
            lines.append(asp.fact("living", gid))
    for cid in CLOUDS:
        lines.append(asp.fact("cloud", cid))
    for sid in SPELLS:
        lines.append(asp.fact("spell", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_gift", params.gift),
            asp.fact("chosen_cloud", params.cloud),
            asp.fact("chosen_spell", params.spell),
        ]
    )
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
        smoke = generate(CURATED[0])
        if not smoke.story or "cloud" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: story did not render expected prose.)")
        print("OK: smoke generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a folk-tale child asks a magic cloud for rain. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--cloud", choices=CLOUDS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gift and args.cloud:
        gift = GIFTS[args.gift]
        cloud = CLOUDS[args.cloud]
        if not gift_fits(gift, cloud):
            raise StoryError(explain_rejection(gift, cloud))
    if args.gift and GIFTS[args.gift].sense < SENSE_MIN:
        cloud = CLOUDS[args.cloud] if args.cloud else next(iter(CLOUDS.values()))
        raise StoryError(explain_rejection(GIFTS[args.gift], cloud))

    combos = [
        c
        for c in valid_combos()
        if (args.need is None or c[0] == args.need)
        and (args.gift is None or c[1] == args.gift)
        and (args.cloud is None or c[2] == args.cloud)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    need_id, gift_id, cloud_id = rng.choice(sorted(combos))
    spell_choices = sorted(SPELLS.keys())
    spell_id = args.spell or rng.choice(spell_choices)
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        need=need_id,
        gift=gift_id,
        cloud=cloud_id,
        spell=spell_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        need = NEEDS[params.need]
        gift = GIFTS[params.gift]
        cloud = CLOUDS[params.cloud]
        spell = SPELLS[params.spell]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not gift_fits(gift, cloud):
        raise StoryError(explain_rejection(gift, cloud))

    world = tell(
        need=need,
        gift=gift,
        cloud=cloud,
        spell=spell,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (need, gift, cloud) combos:\n")
        for need, gift, cloud in combos:
            print(f"  {need:10} {gift:8} {cloud}")
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
            header = f"### {p.child_name}: {p.gift} to {p.cloud} for {p.need} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
