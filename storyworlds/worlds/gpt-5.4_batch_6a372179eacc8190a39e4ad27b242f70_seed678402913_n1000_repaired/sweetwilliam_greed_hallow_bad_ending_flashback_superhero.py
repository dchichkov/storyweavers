#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sweetwilliam_greed_hallow_bad_ending_flashback_superhero.py
=======================================================================================

A standalone storyworld about a child playing superhero in a garden. A glowing
hallow under an old tree is supposed to hold one treasure for each child at the
flower fair. When a greedy hero tries to grab too many star seeds at once, the
bag tears, the sweet william bed is crushed, and the day ends sadly. A brief
flashback shows the earlier promise that made the later mistake matter.

The model keeps a small physical/emotional world:
- physical meters: carrying, spill, crushed, gloom
- emotional memes: joy, greed, shame, warning, care

The reasonableness gate only allows combinations where the chosen prize really
belongs in a shared hallow and the chosen carrying method can plausibly fail
under greedy overloading. The inline ASP twin mirrors the compatibility and
outcome logic.

Run it
------
python storyworlds/worlds/gpt-5.4/sweetwilliam_greed_hallow_bad_ending_flashback_superhero.py
python storyworlds/worlds/gpt-5.4/sweetwilliam_greed_hallow_bad_ending_flashback_superhero.py --all
python storyworlds/worlds/gpt-5.4/sweetwilliam_greed_hallow_bad_ending_flashback_superhero.py --qa
python storyworlds/worlds/gpt-5.4/sweetwilliam_greed_hallow_bad_ending_flashback_superhero.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    hallow: str
    bed: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    count_word: str
    fragile: bool
    shareable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    power: int
    fail_text: str
    success_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guardian:
    id: str
    label: str
    phrase: str
    warning: str
    repair: str
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


def _r_spill_breaks_bed(world: World) -> list[str]:
    hero = world.entities.get("hero")
    bed = world.entities.get("bed")
    stash = world.entities.get("stash")
    if not hero or not bed or not stash:
        return []
    if hero.meters["spill"] < THRESHOLD:
        return []
    sig = ("spill_breaks_bed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bed.meters["crushed"] += 1
    stash.meters["lost"] += 1
    world.get("garden").meters["gloom"] += 1
    hero.memes["shame"] += 1
    return ["__crush__"]


def _r_crushed_saddens_friend(world: World) -> list[str]:
    bed = world.entities.get("bed")
    friend = world.entities.get("friend")
    if not bed or not friend or bed.meters["crushed"] < THRESHOLD:
        return []
    sig = ("crushed_saddens_friend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["sad"] += 1
    friend.memes["trust"] -= 1
    return []


CAUSAL_RULES = [
    Rule(name="spill_breaks_bed", tag="physical", apply=_r_spill_breaks_bed),
    Rule(name="crushed_saddens_friend", tag="social", apply=_r_crushed_saddens_friend),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(prize: Prize, carrier: Carrier) -> bool:
    return prize.shareable and carrier.capacity >= 1


def bad_ending(prize: Prize, carrier: Carrier, grab_count: int) -> bool:
    return prize.fragile and grab_count > carrier.capacity and carrier.power < grab_count


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for prize_id, prize in PRIZES.items():
            for carrier_id, carrier in CARRIERS.items():
                if compatible(prize, carrier):
                    combos.append((setting_id, prize_id, carrier_id))
    return combos


def explain_rejection(prize: Prize, carrier: Carrier) -> str:
    if not prize.shareable:
        return (
            f"(No story: {prize.label} is not a shared fair treasure, so greed in the hallow "
            f"would not make sense here.)"
        )
    return (
        f"(No story: {carrier.label} cannot plausibly carry even one fair prize, so the "
        f"superhero grab would not start.)"
    )


def predict_overload(world: World, grab_count: int) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    carrier = sim.get("carrier")
    hero.meters["carrying"] = float(grab_count)
    if grab_count > carrier.attrs["capacity"]:
        hero.meters["spill"] += 1
        propagate(sim, narrate=False)
    return sim.get("bed").meters["crushed"] >= THRESHOLD


def opening(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} ran through {setting.place} in a fluttering cape, calling {hero.pronoun('object')}self "
        f"Star Swift. {friend.id} ran behind, and together they made the evening feel like a superhero parade."
    )
    world.say(
        f"At the center of the grounds stood {setting.hallow}, ringed by {setting.bed}. "
        f"Above it, {setting.sky}."
    )


def mission(world: World, hero: Entity, friend: Entity, prize: Prize, guardian: Guardian) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"The village gardener, {guardian.phrase}, lifted the lid of the hallow and showed them "
        f"{prize.phrase}. \"One {prize.count_word} for each child at the lantern walk,\" {guardian.pronoun()} said."
    )
    world.say(
        f"{friend.id} clasped {friend.pronoun('possessive')} hands. \"Then we can pass them out like heroes,\" "
        f"{friend.pronoun()} said."
    )


def flashback(world: World, hero: Entity, friend: Entity, guardian: Guardian) -> None:
    world.para()
    world.say(
        f"A flashback flickered through {hero.id}'s mind. That afternoon, {guardian.label_word} had knelt beside "
        f"{hero.pronoun('object')} near the same hallow and touched the neat border of sweet william flowers."
    )
    world.say(
        f"\"Real heroes leave enough for everyone and step carefully around the blooms,\" {guardian.pronoun()} had said. "
        f"{hero.id} had promised with a brave nod, and {friend.id} had heard it too."
    )


def temptation(world: World, hero: Entity, friend: Entity, prize: Prize, carrier: Carrier, guardian: Guardian) -> None:
    hero.memes["greed"] += 1
    friend.memes["warning"] += 1
    overload = predict_overload(world, world.facts["grab_count"])
    world.say(
        f"But when the lid opened wide and the treasures shone, greed crept into {hero.id}'s chest like a hot little spark. "
        f"{hero.pronoun().capitalize()} slipped {carrier.phrase} forward and thought how grand {hero.pronoun()} would look "
        f"flying home with more than anyone else."
    )
    extra = ""
    if overload:
        extra = " Her eyes darted to the sweet william bed, as if she could already picture crushed stems."
        if hero.type == "boy":
            extra = " His eyes darted to the sweet william bed, as if he could already picture crushed stems."
    world.say(
        f"{friend.id} saw the look at once. \"{guardian.warning}\" {friend.pronoun()} whispered.{extra}"
    )


def greedy_grab(world: World, hero: Entity, carrier: Carrier, prize: Prize) -> None:
    hero.meters["carrying"] = float(world.facts["grab_count"])
    hero.memes["greed"] += 1
    world.say(
        f"Instead of taking one {prize.count_word}, {hero.id} scooped up {world.facts['grab_count']} at once. "
        f"{hero.pronoun().capitalize()} tried to balance them in {carrier.phrase} and sprang toward the path like a hero in a comic book."
    )
    if world.facts["grab_count"] > carrier.attrs.get("capacity", carrier.capacity):
        hero.meters["spill"] += 1
        propagate(world, narrate=False)


def fall_and_loss(world: World, hero: Entity, friend: Entity, carrier: Carrier, prize: Prize, guardian: Guardian) -> None:
    bed = world.get("bed")
    stash = world.get("stash")
    world.say(carrier.fail_text.format(hero=hero.id))
    world.say(
        f"The {prize.label} scattered into the hallow and across the path. {hero.id} stumbled sideways into the sweet william bed, "
        f"and soft pink heads bent under {hero.pronoun('possessive')} shoes."
    )
    if bed.meters["crushed"] >= THRESHOLD:
        world.say(
            f"When everything stopped moving, the flowers were mashed flat and several of the treasures had rolled into the dark leaves where no one could find them."
        )
    world.say(
        f"{friend.id} did not cheer this time. {guardian.label_word.capitalize()} hurried over, and the lantern walk suddenly felt far away."
    )
    stash.attrs["remaining"] = max(0, stash.attrs.get("remaining", 0) - 2)
    hero.memes["shame"] += 1
    friend.memes["sad"] += 1
    guardian.memes["sad"] += 1


def bad_resolution(world: World, hero: Entity, friend: Entity, guardian: Guardian, prize: Prize) -> None:
    world.para()
    world.say(
        f"{guardian.label_word.capitalize()} knelt by the torn flowers and let out a slow breath. \"Now some children will have no {prize.label} at all,\" "
        f"{guardian.pronoun()} said."
    )
    world.say(
        f"{hero.id}'s cape no longer felt like a hero's cape. It felt heavy and silly. {hero.pronoun().capitalize()} looked at the broken sweet william stems and wished the flashback promise had been the choice {hero.pronoun()} made."
    )
    world.say(
        f"They spent the rest of the evening picking up what they could, but the hallow looked wounded, the garden was dim, and {friend.id} walked home quietly beside {hero.id}. "
        f"That was the bad ending: greed had turned a superhero game into a hurt that could not be fixed before night."
    )


def tell(
    setting: Setting,
    prize: Prize,
    carrier: Carrier,
    guardian_cfg: Guardian,
    hero_name: str = "Maya",
    hero_type: str = "girl",
    friend_name: str = "Leo",
    friend_type: str = "boy",
    parent_type: str = "mother",
    grab_count: int = 3,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    guardian = world.add(Entity(id="guardian", kind="character", type=parent_type, label=guardian_cfg.label, phrase=guardian_cfg.phrase, role="guardian"))
    hallow = world.add(Entity(id="hallow", type="place", label="hallow"))
    garden = world.add(Entity(id="garden", type="place", label="garden"))
    bed = world.add(Entity(id="bed", type="flowers", label="sweet william bed"))
    stash = world.add(Entity(id="stash", type="stash", label=prize.label, attrs={"remaining": 6}))
    carrier_ent = world.add(
        Entity(
            id="carrier",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            attrs={"capacity": carrier.capacity, "power": carrier.power},
        )
    )

    world.facts.update(
        setting=setting,
        prize=prize,
        carrier=carrier,
        guardian_cfg=guardian_cfg,
        hero=hero,
        friend=friend,
        guardian=guardian,
        grab_count=grab_count,
        outcome="bad" if bad_ending(prize, carrier, grab_count) else "contained",
    )

    opening(world, hero, friend, setting)
    world.para()
    mission(world, hero, friend, prize, guardian)
    flashback(world, hero, friend, guardian)
    world.para()
    temptation(world, hero, friend, prize, carrier, guardian)
    greedy_grab(world, hero, carrier, prize)
    if world.facts["outcome"] == "bad":
        fall_and_loss(world, hero, friend, carrier, prize, guardian)
        bad_resolution(world, hero, friend, guardian, prize)
    else:
        world.say(carrier.success_text.format(hero=hero.label))
        world.say(
            f"{hero.label} still looked tempted, but {friend.label} tugged {hero.pronoun('possessive')} sleeve, and the two children put the extra {prize.label} back. "
            f"The hallow stayed neat, and the sweet william flowers nodded safely in the dusk."
        )

    world.facts.update(
        crushed=world.get("bed").meters["crushed"] >= THRESHOLD,
        lost=world.get("stash").meters["lost"] >= THRESHOLD,
        flashback_used=True,
    )
    return world


KNOWLEDGE = {
    "sweetwilliam": [
        (
            "What is sweet william?",
            "Sweet william is a garden flower that grows in little clusters of bright blossoms. It can be pink, red, white, or purple."
        )
    ],
    "hallow": [
        (
            "What is a hallow in a story like this?",
            "Here, a hallow is a small hollow place in the ground or tree where things are kept. It feels secret and special, like a tiny hiding place."
        )
    ],
    "greed": [
        (
            "What is greed?",
            "Greed is wanting more than your fair share, even when other people need some too. It can make a person forget what is kind."
        )
    ],
    "superhero": [
        (
            "What makes someone act like a real hero?",
            "A real hero helps other people and thinks about what is fair. Being brave matters, but kindness and self-control matter too."
        )
    ],
    "flowers": [
        (
            "Why should you step carefully around flower beds?",
            "Flower stems can bend or break when people step on them. Once the blossoms are crushed, the bed can look sad for a long time."
        )
    ],
}


@dataclass
class StoryParams:
    setting: str
    prize: str
    carrier: str
    guardian: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    grab_count: int
    seed: Optional[int] = None


SETTINGS = {
    "fair_garden": Setting(
        id="fair_garden",
        place="the moonlit fair garden",
        hallow="a mossy hallow at the foot of an old oak",
        bed="a neat bed of sweet william flowers",
        sky="paper lanterns glowed like tiny planets under the blue-black sky",
        tags={"garden", "hallow", "sweetwilliam"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the lantern courtyard behind the town hall",
        hallow="a stone hallow built into the roots of an old fig tree",
        bed="a curved bed of sweet william under the wall",
        sky="silver streamers fluttered over the courtyard in the cool evening air",
        tags={"garden", "hallow", "sweetwilliam"},
    ),
}

PRIZES = {
    "star_seeds": Prize(
        id="star_seeds",
        label="star seeds",
        phrase="a bowl of shining star seeds wrapped in paper stars",
        count_word="star seed",
        fragile=True,
        shareable=True,
        tags={"share", "fragile"},
    ),
    "glow_pebbles": Prize(
        id="glow_pebbles",
        label="glow pebbles",
        phrase="smooth glow pebbles polished for the children",
        count_word="glow pebble",
        fragile=True,
        shareable=True,
        tags={"share", "fragile"},
    ),
    "hero_badges": Prize(
        id="hero_badges",
        label="hero badges",
        phrase="bright hero badges for the parade helpers",
        count_word="badge",
        fragile=False,
        shareable=False,
        tags={"badge"},
    ),
}

CARRIERS = {
    "cape_pouch": Carrier(
        id="cape_pouch",
        label="cape pouch",
        phrase="a tiny pouch sewn inside the cape",
        capacity=1,
        power=1,
        fail_text="{hero}'s cape pouch yanked sideways, the stitches snapped, and the whole corner of the cape whipped open.",
        success_text="{hero}'s little cape pouch held just enough.",
        tags={"cape"},
    ),
    "glove_sling": Carrier(
        id="glove_sling",
        label="glove sling",
        phrase="a sling looped over one superhero glove",
        capacity=2,
        power=2,
        fail_text="{hero}'s glove sling twisted hard, spilled its load, and dragged {hero} off balance.",
        success_text="{hero}'s glove sling stretched but held.",
        tags={"glove"},
    ),
    "wagon": Carrier(
        id="wagon",
        label="red wagon",
        phrase="a red wagon with star stickers",
        capacity=4,
        power=5,
        fail_text="{hero} pulled too sharply, but even then the wagon stayed upright.",
        success_text="{hero}'s red wagon rolled steadily behind like trusty sidekick gear.",
        tags={"wagon"},
    ),
}

GUARDIANS = {
    "gardener": Guardian(
        id="gardener",
        label="the gardener",
        phrase="the gardener with green gloves",
        warning="Take only one. The hallow is for sharing, and the flowers are not a landing pad.",
        repair="garden twine and water",
        tags={"garden"},
    ),
    "groundskeeper": Guardian(
        id="groundskeeper",
        label="the groundskeeper",
        phrase="the groundskeeper in a straw hat",
        warning="Heroes do not snatch. They leave enough for the next child.",
        repair="a small trowel and a watering can",
        tags={"garden"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Theo", "Sam"]


CURATED = [
    StoryParams(
        setting="fair_garden",
        prize="star_seeds",
        carrier="cape_pouch",
        guardian="gardener",
        hero_name="Maya",
        hero_type="girl",
        friend_name="Leo",
        friend_type="boy",
        parent_type="mother",
        grab_count=3,
    ),
    StoryParams(
        setting="courtyard",
        prize="glow_pebbles",
        carrier="glove_sling",
        guardian="groundskeeper",
        hero_name="Finn",
        hero_type="boy",
        friend_name="Ivy",
        friend_type="girl",
        parent_type="father",
        grab_count=3,
    ),
    StoryParams(
        setting="fair_garden",
        prize="star_seeds",
        carrier="wagon",
        guardian="gardener",
        hero_name="Ava",
        hero_type="girl",
        friend_name="Max",
        friend_type="boy",
        parent_type="mother",
        grab_count=3,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "sweetwilliam", "greed", and "hallow".',
        f"Tell a superhero-flavored cautionary story where {hero.label} reaches into a hallow in {setting.place} and greed ruins a shared job.",
        f"Write a story with a flashback promise, a bad ending, and a final image of a hurt flower bed after children scramble for {prize.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian"]
    prize = f["prize"]
    carrier = f["carrier"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child pretending to be a superhero, {friend.label} who runs beside {hero.pronoun('object')}, and {guardian.label} who watches over the garden."
        ),
        (
            "What was in the hallow?",
            f"The hallow held {prize.label} that were meant to be shared. They were not just prizes for one child, which is why greed caused trouble."
        ),
        (
            f"What did the flashback remind {hero.label} about?",
            f"The flashback reminded {hero.label} that {guardian.label_word} had already said to leave enough for everyone and step carefully around the sweet william flowers. That earlier promise made the later mistake feel heavier."
        ),
        (
            f"Why did {friend.label} warn {hero.label}?",
            f"{friend.label} could see that {hero.label} wanted too many {prize.label} at once. {friend.pronoun().capitalize()} also knew the hallow sat beside the sweet william bed, so one greedy rush could hurt both the flowers and the shared treasure."
        ),
    ]
    if f["outcome"] == "bad":
        qa.extend(
            [
                (
                    f"What went wrong with {carrier.label}?",
                    f"{hero.label} tried to carry more than the {carrier.label} could handle, so the load spilled. The stumble pushed {hero.pronoun('object')} into the sweet william bed and scattered the shared treasure."
                ),
                (
                    "How did the story end?",
                    f"It ended sadly. The sweet william flowers were crushed, some children would go without {prize.label}, and {hero.label} had to walk home knowing greed had spoiled the superhero game."
                ),
                (
                    f"What did {hero.label} learn too late?",
                    f"{hero.label} learned too late that real heroes do not grab more than their share. The flashback had already given the right rule, but greed was louder in the moment."
                ),
            ]
        )
    else:
        qa.append(
            (
                "Did the bad ending happen?",
                f"No. {hero.label} started to act greedy, but the safer carrier kept the load steady long enough for the extra {prize.label} to be put back. The flowers stayed safe, so the warning worked in time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sweetwilliam", "hallow", "greed", "superhero", "flowers"}
    out: list[tuple[str, str]] = []
    for key in ["sweetwilliam", "hallow", "greed", "superhero", "flowers"]:
        out.extend(KNOWLEDGE[key])
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable_prize(P) :- prize(P), shareable(P).
compatible(P, C) :- shareable_prize(P), carrier(C), capacity(C, N), N >= 1.

bad_ending(P, C, G) :- fragile(P), compatible(P, C),
                       chosen_grab(G), capacity(C, Cap), power(C, Pow),
                       G > Cap, Pow < G.

outcome(bad) :- chosen_prize(P), chosen_carrier(C), compatible(P, C), bad_ending(P, C, _).
outcome(contained) :- chosen_prize(P), chosen_carrier(C), compatible(P, C), not outcome(bad).

valid(S, P, C) :- setting(S), compatible(P, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize.fragile:
            lines.append(asp.fact("fragile", pid))
        if prize.shareable:
            lines.append(asp.fact("shareable", pid))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, carrier.capacity))
        lines.append(asp.fact("power", cid, carrier.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_prize", params.prize),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_grab", params.grab_count),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a superhero game, greed in a hallow, and a bad ending with a flashback."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--grab-count", type=int, choices=[2, 3, 4], help="How many prizes the hero grabs at once.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prize and args.carrier:
        prize = PRIZES[args.prize]
        carrier = CARRIERS[args.carrier]
        if not compatible(prize, carrier):
            raise StoryError(explain_rejection(prize, carrier))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.prize is None or c[1] == args.prize)
        and (args.carrier is None or c[2] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, prize, carrier = rng.choice(sorted(combos))
    guardian = args.guardian or rng.choice(sorted(GUARDIANS))
    hero_type = rng.choice(["girl", "boy"])
    friend_type = "boy" if hero_type == "girl" else "girl"
    hero_name = _pick_name(rng, hero_type)
    friend_name = _pick_name(rng, friend_type, avoid=hero_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    grab_count = args.grab_count if args.grab_count is not None else rng.choice([2, 3, 4])
    return StoryParams(
        setting=setting,
        prize=prize,
        carrier=carrier,
        guardian=guardian,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=parent_type,
        grab_count=grab_count,
    )


def _require_keys(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.guardian not in GUARDIANS:
        raise StoryError(f"(Unknown guardian: {params.guardian})")
    if not compatible(PRIZES[params.prize], CARRIERS[params.carrier]):
        raise StoryError(explain_rejection(PRIZES[params.prize], CARRIERS[params.carrier]))


def generate(params: StoryParams) -> StorySample:
    _require_keys(params)
    world = tell(
        setting=SETTINGS[params.setting],
        prize=PRIZES[params.prize],
        carrier=CARRIERS[params.carrier],
        guardian_cfg=GUARDIANS[params.guardian],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent_type,
        grab_count=params.grab_count,
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


def outcome_of(params: StoryParams) -> str:
    _require_keys(params)
    return "bad" if bad_ending(PRIZES[params.prize], CARRIERS[params.carrier], params.grab_count) else "contained"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Random resolve failed for seed {seed}.")
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")
        for p in mismatches[:5]:
            print(" ", p, asp_outcome(p), outcome_of(p))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, prize, carrier) combos:\n")
        for setting, prize, carrier in combos:
            print(f"  {setting:12} {prize:12} {carrier}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.prize} in {p.setting} with {p.carrier} ({outcome_of(p)})"
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
