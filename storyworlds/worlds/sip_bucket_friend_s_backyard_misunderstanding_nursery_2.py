#!/usr/bin/env python3
"""
storyworlds/worlds/sip_bucket_friend_s_backyard_misunderstanding_nursery_2.py
=============================================================================

A small nursery-rhyme-style misunderstanding world.

Source tale kept internal for modeling:
    A visiting child takes a sip from a striped cup in a friend's backyard.
    Because the sip happens beside a working bucket, the friend briefly thinks
    the child drank from the bucket instead. The child shows what really
    happened, the bucket goes back to its proper chore, and the ending image
    proves the worry has changed into trust.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SOURCE_TALE = (
    "A child visits a friend's backyard, sips from a striped cup beside a work "
    "bucket, the friend worries the sip came from the bucket, and a simple "
    "proof clears the mix-up before the bucket is used for its real job."
)


@dataclass(frozen=True)
class Backyard:
    key: str
    phrase: str
    opening_image: str
    sound: str
    ending_image: str


@dataclass(frozen=True)
class Drink:
    key: str
    phrase: str
    cup_phrase: str
    flavor_line: str
    aroma_line: str
    tags: frozenset[str]


@dataclass(frozen=True)
class Bucket:
    key: str
    phrase: str
    purpose: str
    contents: str
    warning: str
    ending_action: str
    allowed_backyards: frozenset[str]
    allowed_mixups: frozenset[str]


@dataclass(frozen=True)
class Misunderstanding:
    key: str
    cue: str
    cue_line: str
    reason: str
    alarm_line: str


@dataclass(frozen=True)
class Repair:
    key: str
    phrase: str
    clears: frozenset[str]
    requires_tags: frozenset[str]
    action: str
    proof: str


@dataclass
class StoryParams:
    backyard: str
    drink: str
    bucket: str
    mixup: str
    repair: str
    hero: str
    friend: str
    gender: str
    trait: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    backyard: Backyard
    drink: Drink
    bucket: Bucket
    mixup: Misunderstanding
    repair: Repair
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows: list[str] = ["--- world model state ---"]
        rows.append(f"  source_tale: {SOURCE_TALE}")
        rows.append(f"  backyard: {self.backyard.key} ({self.backyard.phrase})")
        rows.append(f"  drink: {self.drink.key} ({self.drink.phrase})")
        rows.append(f"  bucket: {self.bucket.key} ({self.bucket.phrase})")
        rows.append(f"  mixup: {self.mixup.key} ({self.mixup.cue})")
        rows.append(f"  repair: {self.repair.key} ({self.repair.phrase})")
        rows.append(f"  facts: {self.facts}")
        rows.append(f"  fired: {self.fired}")
        for ent in self.entities.values():
            traits = ", ".join(ent.traits) if ent.traits else "none"
            rows.append(
                f"  {ent.id:<12} ({ent.kind:<8}) role={ent.role:<8} "
                f"traits=[{traits}] meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        return "\n".join(rows)


BACKYARDS: dict[str, Backyard] = {
    "daisy_patch": Backyard(
        key="daisy_patch",
        phrase="the daisy patch behind the swing",
        opening_image="daisies bobbed beside the fence",
        sound="the swing ropes clicked in the breeze",
        ending_image="the daisies nodded like tiny bells",
    ),
    "plum_path": Backyard(
        key="plum_path",
        phrase="the plum-tree path by the sandbox",
        opening_image="round plums bumped softly in the leaves",
        sound="a wooden spinner clacked on the porch rail",
        ending_image="two ripe plums shone like purple marbles",
    ),
    "bean_gate": Backyard(
        key="bean_gate",
        phrase="the bean-vine gate near the stepping stones",
        opening_image="bean blossoms fluttered over the path",
        sound="the garden hose made a sleepy hush",
        ending_image="bean blossoms trembled like little flags",
    ),
}

DRINKS: dict[str, Drink] = {
    "mint_tea": Drink(
        key="mint_tea",
        phrase="mint-apple tea",
        cup_phrase="a red-striped cup",
        flavor_line="The sip was soft and sweet, with mint skipping up like a song.",
        aroma_line="The cup smelled green and sweet, just like mint leaves in the sun.",
        tags=frozenset({"fragrant", "pourable"}),
    ),
    "berry_lemonade": Drink(
        key="berry_lemonade",
        phrase="berry lemonade",
        cup_phrase="a yellow-striped cup",
        flavor_line="The berry sip danced on the tongue with a bright, lemony tickle.",
        aroma_line="The cup smelled of berries and lemon peel, bright as a picnic.",
        tags=frozenset({"fragrant", "pourable", "bright_drop"}),
    ),
    "pear_milk": Drink(
        key="pear_milk",
        phrase="cool pear milk",
        cup_phrase="a blue-striped cup",
        flavor_line="The sip was cool and mild, like a pear cloud in a little cup.",
        aroma_line="The cup smelled mostly creamy and calm, with only a faint pear note.",
        tags=frozenset({"pourable"}),
    ),
}

BUCKETS: dict[str, Bucket] = {
    "tulip_bucket": Bucket(
        key="tulip_bucket",
        phrase="the tin tulip bucket",
        purpose="water the tulips",
        contents="cool flower water",
        warning="That bucket water was meant for roots, not for tongues.",
        ending_action="Then they tipped the bucket in a silver arc around the thirsty tulips.",
        allowed_backyards=frozenset({"daisy_patch", "bean_gate"}),
        allowed_mixups=frozenset({"missing_cup", "heard_sip", "lip_drop"}),
    ),
    "chalk_bucket": Bucket(
        key="chalk_bucket",
        phrase="the chalk-rinse bucket",
        purpose="rinse chalk from the stepping stones",
        contents="swirly blue rinse water",
        warning="That swirly rinse water was for chalky stones, not for drinking.",
        ending_action="Then they swished the bucket water over the bright chalk squares till the stones gleamed.",
        allowed_backyards=frozenset({"plum_path", "bean_gate"}),
        allowed_mixups=frozenset({"missing_cup", "heard_sip", "lip_drop"}),
    ),
    "berry_bucket": Bucket(
        key="berry_bucket",
        phrase="the berry-wash bucket",
        purpose="wash dusty plums",
        contents="pink plum-wash water",
        warning="That pink wash was only for fruit, not for any child's sip.",
        ending_action="Then they used the bucket to rinse the plums till each one shone.",
        allowed_backyards=frozenset({"daisy_patch", "plum_path"}),
        allowed_mixups=frozenset({"missing_cup", "heard_sip", "lip_drop"}),
    ),
}

MIXUPS: dict[str, Misunderstanding] = {
    "missing_cup": Misunderstanding(
        key="missing_cup",
        cue="missing_cup",
        cue_line="The bucket handle hid the little cup from the first quick glance.",
        reason="the true cup was tucked behind the bucket handle for a blink",
        alarm_line="Did you sip from the bucket?",
    ),
    "heard_sip": Misunderstanding(
        key="heard_sip",
        cue="heard_sip",
        cue_line="The tiny sip and the bucket's clink happened in the very same beat.",
        reason="the sip sound and the bucket clink arrived together",
        alarm_line="Oh! Was that a bucket sip?",
    ),
    "lip_drop": Misunderstanding(
        key="lip_drop",
        cue="lip_drop",
        cue_line="A bright little drop stayed on the lip right after the sip.",
        reason="that shining drop looked like a splash from the bucket",
        alarm_line="Wait! Did the bucket splash into your mouth?",
    ),
}

REPAIRS: dict[str, Repair] = {
    "lift_cup": Repair(
        key="lift_cup",
        phrase="lift the striped cup",
        clears=frozenset({"missing_cup", "lip_drop"}),
        requires_tags=frozenset(),
        action="{hero} lifted {cup} above the bucket handle and gave the straw a tiny wiggle.",
        proof="{friend} could see the true sip at once, and the worry began to shrink.",
    ),
    "share_sniff": Repair(
        key="share_sniff",
        phrase="share the sweet smell",
        clears=frozenset({"heard_sip"}),
        requires_tags=frozenset({"fragrant"}),
        action="{hero} held the cup near {friend} and said, 'Smell my drink before you think.'",
        proof="The sweet smell made the answer plain: the sip came from the cup, not the bucket.",
    ),
    "pour_fresh_pair": Repair(
        key="pour_fresh_pair",
        phrase="pour two fresh cups",
        clears=frozenset({"missing_cup", "heard_sip", "lip_drop"}),
        requires_tags=frozenset({"pourable"}),
        action="{hero} fetched the little pitcher and poured two fresh cups beside the bucket, one for each child.",
        proof="When {friend} watched the drink splash into the striped cups, the mix-up untied itself.",
    ),
}

HERO_NAMES = {
    "girl": ("Mina", "Lila", "Nora", "Tess"),
    "boy": ("Owen", "Eli", "Jude", "Max"),
}
FRIEND_NAMES = ("Pip", "Kit", "Rue", "Bo")
TRAITS = ("careful", "bouncy", "gentle", "bright-eyed")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def _pick_friend(hero: str, rng: random.Random) -> str:
    choices = [name for name in FRIEND_NAMES if name != hero]
    return rng.choice(choices)


def valid_combo(
    backyard_key: str,
    drink_key: str,
    bucket_key: str,
    mixup_key: str,
    repair_key: str,
) -> bool:
    if (
        backyard_key not in BACKYARDS
        or drink_key not in DRINKS
        or bucket_key not in BUCKETS
        or mixup_key not in MIXUPS
        or repair_key not in REPAIRS
    ):
        return False
    drink = DRINKS[drink_key]
    bucket = BUCKETS[bucket_key]
    mixup = MIXUPS[mixup_key]
    repair = REPAIRS[repair_key]
    return (
        backyard_key in bucket.allowed_backyards
        and mixup_key in bucket.allowed_mixups
        and mixup.cue in repair.clears
        and repair.requires_tags.issubset(drink.tags)
    )


def invalid_reason(
    backyard_key: str,
    drink_key: str,
    bucket_key: str,
    mixup_key: str,
    repair_key: str,
) -> str:
    if backyard_key not in BACKYARDS:
        return f"No story: unknown backyard {backyard_key!r}."
    if drink_key not in DRINKS:
        return f"No story: unknown drink {drink_key!r}."
    if bucket_key not in BUCKETS:
        return f"No story: unknown bucket {bucket_key!r}."
    if mixup_key not in MIXUPS:
        return f"No story: unknown misunderstanding {mixup_key!r}."
    if repair_key not in REPAIRS:
        return f"No story: unknown repair {repair_key!r}."

    backyard = BACKYARDS[backyard_key]
    drink = DRINKS[drink_key]
    bucket = BUCKETS[bucket_key]
    mixup = MIXUPS[mixup_key]
    repair = REPAIRS[repair_key]

    if backyard_key not in bucket.allowed_backyards:
        return (
            f"No story: {bucket.phrase} does not belong in {backyard.phrase}. "
            f"It is only plausible in {', '.join(sorted(bucket.allowed_backyards))}."
        )
    if mixup_key not in bucket.allowed_mixups:
        return (
            f"No story: {mixup.key} is not a plausible mistake around {bucket.phrase}."
        )
    if mixup.cue not in repair.clears:
        return (
            f"No story: {repair.phrase} does not clear the {mixup.cue.replace('_', ' ')} cue."
        )
    if not repair.requires_tags.issubset(drink.tags):
        missing = ", ".join(sorted(repair.requires_tags - drink.tags))
        return (
            f"No story: {repair.phrase} needs drink tags [{missing}], but {drink.phrase} "
            "does not provide that proof."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for backyard_key in sorted(BACKYARDS):
        for drink_key in sorted(DRINKS):
            for bucket_key in sorted(BUCKETS):
                for mixup_key in sorted(MIXUPS):
                    for repair_key in sorted(REPAIRS):
                        if valid_combo(
                            backyard_key, drink_key, bucket_key, mixup_key, repair_key
                        ):
                            combos.append(
                                (backyard_key, drink_key, bucket_key, mixup_key, repair_key)
                            )
    return combos


def _params_from_combo(
    args: argparse.Namespace | None,
    combo: tuple[str, str, str, str, str],
    index: int = 0,
) -> StoryParams:
    base_seed = 1 if args is None else args.seed
    rng = random.Random(base_seed + index)
    gender = "girl" if args is None or args.gender is None else args.gender
    if args is not None and args.gender is None:
        gender = rng.choice(("girl", "boy"))
    hero = None if args is None else args.hero
    friend = None if args is None else args.friend
    trait = None if args is None else args.trait
    hero_name = hero or _pick_hero(gender, rng)
    friend_name = friend or _pick_friend(hero_name, rng)
    chosen_trait = trait or rng.choice(TRAITS)
    return StoryParams(
        backyard=combo[0],
        drink=combo[1],
        bucket=combo[2],
        mixup=combo[3],
        repair=combo[4],
        hero=hero_name,
        friend=friend_name,
        gender=gender,
        trait=chosen_trait,
        seed=base_seed + index,
    )


def build_world(params: StoryParams) -> World:
    backyard = BACKYARDS[params.backyard]
    drink = DRINKS[params.drink]
    bucket = BUCKETS[params.bucket]
    mixup = MIXUPS[params.mixup]
    repair = REPAIRS[params.repair]

    world = World(
        params=params,
        backyard=backyard,
        drink=drink,
        bucket=bucket,
        mixup=mixup,
        repair=repair,
    )
    world.add(
        Entity(
            id=params.hero,
            kind=params.gender,
            label="guest child",
            traits=[params.trait],
            role="guest",
            meters=defaultdict(float, {"height_m": 1.08, "steps_taken": 0.0}),
            memes=defaultdict(float, {"curiosity": 0.8, "calm": 0.6}),
        )
    )
    world.add(
        Entity(
            id=params.friend,
            kind="child",
            label="friend",
            traits=["watchful", "kind"],
            role="host",
            meters=defaultdict(float, {"height_m": 1.1}),
            memes=defaultdict(float, {"trust": 0.9, "worry": 0.0}),
        )
    )
    world.add(
        Entity(
            id="cup",
            kind="cup",
            label=drink.cup_phrase,
            traits=["striped"],
            role="drink_source",
            meters=defaultdict(float, {"fullness": 0.9, "sips_taken": 0.0, "visible": 0.0}),
            memes=defaultdict(float),
        )
    )
    world.add(
        Entity(
            id="bucket",
            kind="bucket",
            label=bucket.phrase,
            traits=["round", "working"],
            role="yard_tool",
            meters=defaultdict(float, {"fullness": 0.85, "used_for_chore": 0.0}),
            memes=defaultdict(float),
        )
    )
    world.add(
        Entity(
            id="pitcher",
            kind="pitcher",
            label="little pitcher",
            traits=["small"],
            role="drink_supply",
            meters=defaultdict(float, {"fullness": 0.75}),
            memes=defaultdict(float),
        )
    )
    world.facts.update(
        {
            "setting_owner": params.friend,
            "setting_place": backyard.phrase,
            "bucket_job": bucket.purpose,
            "bucket_contents": bucket.contents,
            "actual_sip_source": "cup",
            "believed_sip_source": "bucket",
            "mixup_status": "not_started",
            "repair_status": "not_started",
            "lesson": "ask before assuming",
            "seed": str(params.seed),
        }
    )
    return world


def _introduce(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    bucket = world.get("bucket")
    cup = world.get("cup")
    hero.meters["steps_taken"] += 4
    cup.meters["visible"] = 1.0 if world.mixup.key != "missing_cup" else 0.2
    world.say(
        f"Once upon a backyard bright, {hero.id} came to {friend.id}'s place for play. "
        f"In {friend.id}'s backyard, by {world.backyard.phrase}, {world.backyard.opening_image} and {world.backyard.sound}."
    )
    world.say(
        f"{hero.id} carried {world.drink.cup_phrase} of {world.drink.phrase}, while {bucket.label} sat on the ground to {world.bucket.purpose}. "
        f"It held {world.bucket.contents}, and everyone knew that bucket was a work bucket."
    )
    world.fired.append("introduced")


def _take_sip(world: World) -> None:
    hero = world.get(world.params.hero)
    cup = world.get("cup")
    cup.meters["sips_taken"] += 1.0
    cup.meters["fullness"] -= 0.18
    hero.memes["delight"] += 0.8
    world.say(
        f"{hero.id} took a little sip, tip-tip, from the striped cup. {world.drink.flavor_line}"
    )
    world.fired.append("sip_taken")


def _misread(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    bucket = world.get("bucket")
    world.facts["mixup_status"] = "active"
    friend.memes["worry"] += 1.2
    hero.memes["confusion"] += 0.7
    bucket.meters["fullness"] = bucket.meters["fullness"]
    if world.mixup.key == "lip_drop":
        hero.meters["lip_drop"] += 1.0
    world.para()
    world.say(
        f"But then a mix-up began. {world.mixup.cue_line} "
        f"'{world.mixup.alarm_line}' asked {friend.id} with a jump."
    )
    world.say(
        f"{friend.id} thought the sip had come from the bucket, because {world.mixup.reason}. "
        f"{world.bucket.warning}"
    )
    world.fired.append("misunderstanding_started")


def _repair(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    cup = world.get("cup")
    pitcher = world.get("pitcher")
    world.facts["repair_status"] = "active"
    if world.repair.key == "lift_cup":
        cup.meters["visible"] = 1.0
    if world.repair.key == "pour_fresh_pair":
        cup.meters["fullness"] += 0.12
        pitcher.meters["fullness"] -= 0.18
        cup.meters["visible"] = 1.0
    if world.repair.key == "share_sniff":
        cup.meters["visible"] = 0.9
    friend.memes["worry"] = max(0.0, friend.memes["worry"] - 1.0)
    friend.memes["relief"] += 1.1
    hero.memes["trust"] += 0.9
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 0.5)
    world.para()
    world.say(
        world.repair.action.format(
            hero=hero.id,
            friend=friend.id,
            cup=world.drink.cup_phrase,
            drink=world.drink.phrase,
        )
    )
    if world.repair.key == "share_sniff":
        world.say(world.drink.aroma_line)
    world.say(
        world.repair.proof.format(
            hero=hero.id,
            friend=friend.id,
            cup=world.drink.cup_phrase,
            drink=world.drink.phrase,
        )
    )
    world.facts["mixup_status"] = "cleared"
    world.facts["repair_status"] = "done"
    world.facts["realized_sip_source"] = "cup"
    world.fired.append("misunderstanding_cleared")


def _ending(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    bucket = world.get("bucket")
    bucket.meters["used_for_chore"] = 1.0
    bucket.meters["fullness"] = max(0.0, bucket.meters["fullness"] - 0.35)
    friend.memes["trust"] += 0.5
    hero.memes["delight"] += 0.4
    world.para()
    world.say(
        f"{world.bucket.ending_action} {hero.id} and {friend.id} tapped their cups together with a soft little click."
    )
    world.say(
        f"The worry was gone, the sip was understood, and {world.backyard.ending_image}. "
        f"In that yard, the bucket did its chore and the children kept their sweet cup cheer."
    )
    world.fired.append("ending_image")


def play_story(world: World) -> World:
    _introduce(world)
    _take_sip(world)
    _misread(world)
    _repair(world)
    _ending(world)
    return world


def _prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme-style story set in a friend's backyard.",
        "Include a sip from a real cup, a nearby bucket, and a misunderstanding about where the sip came from.",
        "Let the ending image prove that the worry has changed into trust and proper bucket use.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    return [
        QAItem(
            "Where does the story happen?",
            f"The story happens in {friend.id}'s backyard, by {world.backyard.phrase}. The setting matters because the bucket is there for a yard chore, not as a drinking cup.",
        ),
        QAItem(
            f"What misunderstanding did {friend.id} have?",
            f"{friend.id} thought {hero.id} had sipped from {world.bucket.phrase}. "
            f"That mistake began because {world.mixup.reason}, even though the true sip came from {world.drink.cup_phrase}.",
        ),
        QAItem(
            "What was the bucket really for?",
            f"The bucket was there to {world.bucket.purpose}. Its {world.bucket.contents} belonged to the yard chore, which is why the friend worried in the first place.",
        ),
        QAItem(
            f"How was the mix-up cleared?",
            f"The children cleared it by choosing to {world.repair.phrase}. That worked because it answered the exact clue that started the misunderstanding and showed the sip's real source.",
        ),
        QAItem(
            "What proves the story changed by the end?",
            f"By the end, the bucket is used for its proper job and the children tap their cups together. That ending image shows the fear has turned back into trust and play.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    items = [
        QAItem(
            "Why can a bucket cause a misunderstanding in this story?",
            "The bucket sits right beside the children and holds something important for the yard. When a sip happens at the same moment, a quick glance or quick sound can point to the wrong object.",
        ),
        QAItem(
            "Why does showing the right object help so much?",
            "A misunderstanding shrinks when the children can point to the real source instead of only arguing about it. In this story, a cup, a smell, or a fresh pour gives visible proof.",
        ),
        QAItem(
            "Why is the ending tied to the bucket's real chore?",
            "The bucket should return to its physical job so the ending is visible, not only explained. Using the bucket properly proves everyone now agrees about what it is for.",
        ),
    ]
    if "fragrant" in world.drink.tags:
        items.append(
            QAItem(
                "Why can smell work as evidence here?",
                "Some drinks carry a strong sweet smell that yard water does not have. That makes the nose a fair witness when the ears heard the wrong thing.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(
        params.backyard, params.drink, params.bucket, params.mixup, params.repair
    ):
        raise StoryError(
            invalid_reason(
                params.backyard,
                params.drink,
                params.bucket,
                params.mixup,
                params.repair,
            )
        )
    world = play_story(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(BY,D,B,M,R) :-
    backyard(BY), drink(D), bucket(B), mixup(M), repair(R),
    bucket_allowed_backyard(B,BY),
    bucket_allows_mixup(B,M),
    mixup_cue(M,C),
    repair_clears(R,C),
    not missing_drink_tag(D,R).

missing_drink_tag(D,R) :-
    drink(D),
    repair_requires_tag(R,T),
    not drink_tag(D,T).

ok :- chosen(BY,D,B,M,R), valid(BY,D,B,M,R).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for backyard_key in sorted(BACKYARDS):
        rows.append(fact("backyard", backyard_key))
    for drink_key, drink in DRINKS.items():
        rows.append(fact("drink", drink_key))
        for tag in sorted(drink.tags):
            rows.append(fact("drink_tag", drink_key, tag))
    for bucket_key, bucket in BUCKETS.items():
        rows.append(fact("bucket", bucket_key))
        for backyard_key in sorted(bucket.allowed_backyards):
            rows.append(fact("bucket_allowed_backyard", bucket_key, backyard_key))
        for mixup_key in sorted(bucket.allowed_mixups):
            rows.append(fact("bucket_allows_mixup", bucket_key, mixup_key))
    for mixup_key, mixup in MIXUPS.items():
        rows.append(fact("mixup", mixup_key))
        rows.append(fact("mixup_cue", mixup_key, mixup.cue))
    for repair_key, repair in REPAIRS.items():
        rows.append(fact("repair", repair_key))
        for cue in sorted(repair.clears):
            rows.append(fact("repair_clears", repair_key, cue))
        for tag in sorted(repair.requires_tags):
            rows.append(fact("repair_requires_tag", repair_key, tag))
    if params is not None:
        rows.append(
            fact(
                "chosen",
                params.backyard,
                params.drink,
                params.bucket,
                params.mixup,
                params.repair,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for combo in atoms(model, "valid"):
            combos.add(tuple(combo))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )

    for index, combo in enumerate(sorted(python_combos)):
        params = _params_from_combo(None, combo, index)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError(f"Verification failed: empty story for combo {combo}.")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"Verification failed: weak QA surface for combo {combo}.")
        if not asp_verify(params):
            raise StoryError(f"Verification failed: ASP did not accept chosen combo {combo}.")
    return f"OK: Python and ASP gates agree for {len(python_combos)} combos, and every combo generates a story."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a nursery-rhyme misunderstanding story about a sip and a bucket."
    )
    parser.add_argument("--backyard", choices=tuple(BACKYARDS), default=None)
    parser.add_argument("--drink", choices=tuple(DRINKS), default=None)
    parser.add_argument("--bucket", choices=tuple(BUCKETS), default=None)
    parser.add_argument("--mixup", choices=tuple(MIXUPS), default=None)
    parser.add_argument("--repair", choices=tuple(REPAIRS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--gender", choices=("girl", "boy"), default=None)
    parser.add_argument("--trait", choices=TRAITS, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.backyard is None or combo[0] == args.backyard)
        and (args.drink is None or combo[1] == args.drink)
        and (args.bucket is None or combo[2] == args.bucket)
        and (args.mixup is None or combo[3] == args.mixup)
        and (args.repair is None or combo[4] == args.repair)
    ]
    if not filtered:
        if (
            args.backyard is not None
            and args.drink is not None
            and args.bucket is not None
            and args.mixup is not None
            and args.repair is not None
        ):
            raise StoryError(
                invalid_reason(
                    args.backyard,
                    args.drink,
                    args.bucket,
                    args.mixup,
                    args.repair,
                )
            )
        raise StoryError(
            "No story: the chosen filters do not overlap in a plausible backyard misunderstanding."
        )
    combo = rng.choice(filtered)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for idx, prompt in enumerate(sample.prompts, 1):
        print(f"{idx}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            samples = [
                generate(_params_from_combo(args, combo, index + 1))
                for index, combo in enumerate(combos)
            ]
            if args.json:
                payload = [sample.to_dict() for sample in samples]
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                return 0
            for index, sample in enumerate(samples, 1):
                combo = combos[index - 1]
                emit(
                    sample,
                    args,
                    header=f"### {' / '.join(combo)}",
                )
                if index != len(samples):
                    print("\n" + "=" * 72 + "\n")
            return 0
        total = max(1, args.n)
        if args.json and total > 1:
            samples = [generate(resolve_params(args, index)) for index in range(total)]
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        for index in range(total):
            sample = generate(resolve_params(args, index))
            header = f"### variant {index + 1}" if total > 1 and not args.json else None
            emit(sample, args, header=header)
            if index != total - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
