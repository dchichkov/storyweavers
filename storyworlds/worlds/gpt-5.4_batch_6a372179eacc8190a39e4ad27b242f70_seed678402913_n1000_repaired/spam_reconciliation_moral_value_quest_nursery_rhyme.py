#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py
=================================================================================

A small nursery-rhyme-style story world about a child on a quest for a real note
hidden among spam flyers. The world enforces a simple common-sense gate:
the setting must plausibly support the mix-up, and the cause must plausibly hide
a paper note. Stories always move through premise, misunderstanding, quest,
reconciliation, and a moral ending image.

Run it
------
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py --all --qa
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py --trace
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py --json
python storyworlds/worlds/gpt-5.4/spam_reconciliation_moral_value_quest_nursery_rhyme.py --verify
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
KIND_MIN = 2


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
        female = {"girl", "mother", "hen", "goose", "ewe"}
        male = {"boy", "father", "rooster", "gander", "ram"}
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
    lane: str
    landmark: str
    rhyme_close: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    seek: str
    note_name: str
    invitation: str
    goal_place: str
    ending_image: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpamKind:
    id: str
    label: str
    phrase: str
    rhyme_noise: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    sense: int
    move_line: str
    hide_spot: str
    find_line: str
    apology_reason: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    basket = world.entities.get("basket")
    if not hero or not friend or not basket:
        return out
    if basket.meters["spam_full"] < THRESHOLD:
        return out
    if hero.memes["blame"] < THRESHOLD:
        return out
    sig = ("confusion", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sad"] += 1
    friend.memes["sad"] += 1
    out.append("__confusion__")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return out
    sig = ("reconcile", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    hero.memes["sad"] = 0.0
    friend.memes["sad"] = 0.0
    out.append("__reconciliation__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="confusion", tag="social", apply=_r_confusion),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
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


def cause_fits(setting: Setting, cause: Cause) -> bool:
    return cause.id in setting.allows and cause.sense >= KIND_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for qid in QUESTS:
            for spid in SPAM_KINDS:
                for cid, cause in CAUSES.items():
                    if cause_fits(setting, cause):
                        combos.append((sid, qid, spid, cid))
    return combos


def predict_loss(setting: Setting, cause: Cause, spam: SpamKind) -> dict:
    basket = Entity(id="basket", type="basket")
    basket.meters["spam_full"] += 1
    note = Entity(id="note", type="note")
    if cause_fits(setting, cause):
        note.meters["lost"] += 1
    return {
        "lost": note.meters["lost"] >= THRESHOLD,
        "crowded": basket.meters["spam_full"] >= THRESHOLD,
        "spam_label": spam.label,
    }


def explain_rejection(setting: Setting, cause: Cause) -> str:
    if cause.sense < KIND_MIN:
        return (
            f"(No story: '{cause.id}' is known to the world but refused because it "
            f"does not feel kind and sensible enough for this nursery-rhyme domain.)"
        )
    return (
        f"(No story: {cause.label} does not fit {setting.place}. Pick a cause that "
        f"the setting really allows.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, quest: Quest, spam: SpamKind) -> None:
    hero.memes["hope"] += 1
    friend.memes["love"] += 1
    world.say(
        f"In {world.setting.lane}, where cobbles gleam, little {hero.id} skipped in a dream. "
        f"{friend.id} had promised {quest.invitation}, tucked in a note for a tiny questing station."
    )
    world.say(
        f"But by the gate sat a wobbling basket, brimmed with {spam.phrase}; "
        f"'{spam.label}, spam, what a scram!' sang the papers in a papery clatter."
    )


def arrive_spam(world: World, hero: Entity, spam: SpamKind) -> None:
    basket = world.get("basket")
    basket.meters["spam_full"] += 1
    hero.memes["annoyance"] += 1
    world.say(
        f"They rustled and hustled with {spam.rhyme_noise}, and {hero.id} frowned at the jumbling noise."
    )


def mix_up(world: World, hero: Entity, friend: Entity, quest: Quest, cause: Cause) -> None:
    note = world.get("note")
    note.meters["real"] += 1
    note.meters["lost"] += 1
    world.facts["hide_spot"] = cause.hide_spot
    world.say(
        f"While {hero.id} blinked, {cause.move_line} "
        f"The true little note for {quest.seek} slipped away from the top of the pile."
    )
    hero.memes["worry"] += 1
    friend.memes["hope"] += 1


def misjudge(world: World, hero: Entity, friend: Entity, spam: SpamKind) -> None:
    hero.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh dear," sighed {hero.id}, "did {friend.id} send only {spam.label}? '
        f'Was the basket all bother and no kind reply?"'
    )
    world.say(
        f"The lane felt less bright, and the rhyme lost its ring, for quick blame can sting like a nettle in spring."
    )


def choose_quest(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["resolve"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Then {helper.id} came by with a lantern-like grin. "
        f'"Before we feel cross, let us look well within. '
        f'We will search for the {quest.note_name} from hedge-top to eaves, '
        f'for true things hide softly like moths under leaves."'
    )


def search(world: World, hero: Entity, helper: Entity, quest: Quest, cause: Cause) -> None:
    hero.meters["steps"] += 1
    helper.meters["steps"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"So off went the pair on their gentle-foot quest, past {world.setting.landmark} and the old robin's nest. "
        f"They peeped in the pail and they peered by the post, asking where the lost whisper had drifted the most."
    )
    world.say(cause.find_line)
    note = world.get("note")
    note.meters["found"] += 1
    note.meters["lost"] = 0.0


def learn_truth(world: World, hero: Entity, friend: Entity, quest: Quest, cause: Cause) -> None:
    hero.memes["understanding"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"There it was at {cause.hide_spot}: the note with the curl, inviting dear {hero.id} to help with {quest.seek}. "
        f"It had not been meanness and not been a trick; it was only {cause.apology_reason} that hid it so quick."
    )


def reconcile(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    hero.memes["apology"] += 1
    friend.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Soon {friend.id} came hurrying down the lane bend. "{hero.id}," said {friend.pronoun()}, "I am still your friend." '
        f'"And I am yours too," said {hero.id}, "for I blamed in a rush. Next time I will ask before letting my kind thoughts hush."'
    )
    world.say(
        f"{helper.id} nodded softly. In quarrels made small, a kind question can often untangle them all."
    )


def finish_quest(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then off went the two to {quest.goal_place}, keeping time with a skip and a smile on each face. "
        f"They won {quest.reward}, and better than treasure, they mended their friendship in full nursery measure."
    )
    world.say(
        f"And there by {world.setting.rhyme_close}, {quest.ending_image}. "
        f"So remember, dear hearts, when a muddle seems vast: ask kindly, seek truly, and friendship will last."
    )


def tell(
    setting: Setting,
    quest: Quest,
    spam: SpamKind,
    cause: Cause,
    hero_name: str = "Molly",
    hero_type: str = "girl",
    friend_name: str = "Pip",
    friend_type: str = "boy",
    helper_name: str = "Nell",
    helper_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    basket = world.add(Entity(id="basket", type="basket", label="basket"))
    note = world.add(Entity(id="note", type="note", label=quest.note_name))

    introduce(world, hero, friend, quest, spam)
    arrive_spam(world, hero, spam)

    world.para()
    mix_up(world, hero, friend, quest, cause)
    misjudge(world, hero, friend, spam)

    world.para()
    choose_quest(world, hero, helper, quest)
    search(world, hero, helper, quest, cause)
    learn_truth(world, hero, friend, quest, cause)

    world.para()
    reconcile(world, hero, friend, helper)
    finish_quest(world, hero, friend, quest)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        parent=parent,
        basket=basket,
        note=note,
        setting=setting,
        quest=quest,
        spam=spam,
        cause=cause,
        misunderstanding=hero.memes["blame"] >= THRESHOLD,
        reconciled=hero.memes["love"] >= THRESHOLD and friend.memes["love"] >= THRESHOLD,
        found_note=note.meters["found"] >= THRESHOLD,
        moral="ask kindly before blaming",
    )
    return world


KNOWLEDGE = {
    "spam": [
        (
            "What is spam?",
            "Spam is unwanted messages or papers that crowd up the things you really want to read. It can make it harder to notice an important note."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special trip with a purpose. You go looking for something important or trying to do something brave and good."
        )
    ],
    "friendship": [
        (
            "How can friends make up after a misunderstanding?",
            "Friends can talk honestly, say sorry, and listen to each other. Kind words help hurt feelings settle down."
        )
    ],
    "kindness": [
        (
            "Why is it good to ask kindly before blaming someone?",
            "Asking kindly gives you a chance to learn the truth. Blaming too fast can hurt someone who did not mean any harm."
        )
    ],
    "wind": [
        (
            "What can wind do to loose paper?",
            "Wind can lift and carry light paper away. That is why notes and flyers can blow into odd little places."
        )
    ],
    "goat": [
        (
            "Why do animals sometimes carry off paper or cloth?",
            "Animals may tug at loose things because they are curious. They do not understand that the item matters to someone."
        )
    ],
    "rain": [
        (
            "Why do wet papers stick together?",
            "When paper gets wet, it turns soft and clingy. Sheets can stick and hide one another."
        )
    ],
}
KNOWLEDGE_ORDER = ["spam", "quest", "friendship", "kindness", "wind", "goat", "rain"]


SETTINGS = {
    "cottage_lane": Setting(
        id="cottage_lane",
        place="the cottage lane",
        lane="Cottage Lane",
        landmark="the mossy gate",
        rhyme_close="the bluebell stone",
        allows={"wind", "rain_puddle"},
        tags={"village"},
    ),
    "market_square": Setting(
        id="market_square",
        place="the market square",
        lane="Market Square",
        landmark="the bun stall",
        rhyme_close="the clock post",
        allows={"wind"},
        tags={"market"},
    ),
    "farm_path": Setting(
        id="farm_path",
        place="the farm path",
        lane="Farm Path",
        landmark="the red cart",
        rhyme_close="the clover trough",
        allows={"wind", "goat"},
        tags={"farm"},
    ),
}

QUESTS = {
    "bell_ribbon": Quest(
        id="bell_ribbon",
        seek="the bell ribbon for the spring parade",
        note_name="bell-ribbon note",
        invitation="a note about the bell ribbon for the spring parade",
        goal_place="the little bell tree",
        ending_image="they tied the ribbon high, and the bell sang silver over the lane",
        reward="a bright brass bell",
        tags={"quest"},
    ),
    "seed_map": Quest(
        id="seed_map",
        seek="the seed map for the moonlit garden",
        note_name="seed-map note",
        invitation="a note about the seed map for the moonlit garden",
        goal_place="the moonlit garden bed",
        ending_image="they pressed the seeds in rows, and little moons of water shone beside them",
        reward="a pocketful of sweet pea seeds",
        tags={"quest"},
    ),
    "cake_key": Quest(
        id="cake_key",
        seek="the cake key for the fair-day cupboard",
        note_name="cake-key note",
        invitation="a note about the cake key for the fair-day cupboard",
        goal_place="the fair-day cupboard",
        ending_image="they turned the tiny key, and cinnamon smell curled warmly through the air",
        reward="a sugared bun",
        tags={"quest"},
    ),
}

SPAM_KINDS = {
    "flyers": SpamKind(
        id="flyers",
        label="spam flyers",
        phrase="a heap of spam flyers",
        rhyme_noise="flip-flap, flap-flip",
        tags={"spam"},
    ),
    "coupons": SpamKind(
        id="coupons",
        label="spam coupons",
        phrase="a stack of spam coupons",
        rhyme_noise="snip-snap, snap-snip",
        tags={"spam"},
    ),
    "posters": SpamKind(
        id="posters",
        label="spam posters",
        phrase="a bundle of spam posters",
        rhyme_noise="whish-wash, wash-whish",
        tags={"spam"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="a gust of wind",
        sense=3,
        move_line="a merry gust of wind whisked the basket brim and fluttered one true page under a loose step.",
        hide_spot="the loose step by the gate",
        find_line="At last a paper corner winked from under the loose step by the gate.",
        apology_reason="the wind's quick whisk",
        allows={"cottage_lane", "market_square", "farm_path"},
        tags={"wind"},
    ),
    "rain_puddle": Cause(
        id="rain_puddle",
        label="a rain puddle",
        sense=2,
        move_line="a bead of rain slid through the pile, and two damp papers kissed together before the true note slipped beside the pail.",
        hide_spot="the pail beside the puddle",
        find_line="By the pail beside the puddle, two stuck papers peeled apart, and the little note was hiding there.",
        apology_reason="rain making the pages cling together",
        allows={"cottage_lane"},
        tags={"rain"},
    ),
    "goat": Cause(
        id="goat",
        label="a nosy goat",
        sense=2,
        move_line="a nosy goat nibbled at the corner of the pile and trotted off with the true note tucked under its chin before dropping it in the clover.",
        hide_spot="the clover by the trough",
        find_line="A scrap peeked from the clover by the trough where the goat had dropped it.",
        apology_reason="the goat's curious tug",
        allows={"farm_path"},
        tags={"goat"},
    ),
    "rude_prank": Cause(
        id="rude_prank",
        label="a rude prank",
        sense=1,
        move_line="someone mean hid the note on purpose.",
        hide_spot="a mean hiding place",
        find_line="The note turned up where a prankster had shoved it.",
        apology_reason="a prank",
        allows={"market_square"},
        tags=set(),
    ),
}


@dataclass
class StoryParams:
    setting: str
    quest: str
    spam: str
    cause: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    helper_name: str
    helper_type: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="cottage_lane",
        quest="bell_ribbon",
        spam="flyers",
        cause="wind",
        hero_name="Molly",
        hero_type="girl",
        friend_name="Pip",
        friend_type="boy",
        helper_name="Nell",
        helper_type="girl",
        parent="mother",
    ),
    StoryParams(
        setting="farm_path",
        quest="seed_map",
        spam="coupons",
        cause="goat",
        hero_name="Toby",
        hero_type="boy",
        friend_name="Wren",
        friend_type="girl",
        helper_name="Bess",
        helper_type="girl",
        parent="father",
    ),
    StoryParams(
        setting="cottage_lane",
        quest="cake_key",
        spam="posters",
        cause="rain_puddle",
        hero_name="Daisy",
        hero_type="girl",
        friend_name="Kit",
        friend_type="boy",
        helper_name="Moss",
        helper_type="boy",
        parent="mother",
    ),
    StoryParams(
        setting="market_square",
        quest="seed_map",
        spam="flyers",
        cause="wind",
        hero_name="Robin",
        hero_type="boy",
        friend_name="May",
        friend_type="girl",
        helper_name="Dot",
        helper_type="girl",
        parent="father",
    ),
]


GIRL_NAMES = ["Molly", "Nell", "Daisy", "May", "Wren", "Dot", "Elsie", "Poppy"]
BOY_NAMES = ["Pip", "Toby", "Kit", "Moss", "Robin", "Jem", "Ned", "Ollie"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    spam = f["spam"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "{spam.label.split()[0]}" and has a child go on a quest.',
        f"Tell a rhyming story where {hero.id} thinks {friend.id} sent only {spam.label}, but a search reveals the truth and the friends make up.",
        f'Write a gentle moral tale with reconciliation where a lost invitation is hidden among {spam.label} and the ending teaches children to ask kindly before blaming.',
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "boy" and friend.type == "boy":
        return "two friends"
    if hero.type == "girl" and friend.type == "girl":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    quest = f["quest"]
    spam = f["spam"]
    cause = f["cause"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, {hero.id} and {friend.id}, with {helper.id} helping on the way. They are trying to find the real note for {quest.seek}."
        ),
        (
            f"What problem did {hero.id} face?",
            f"{hero.id} wanted the true note from {friend.id}, but the basket was crowded with {spam.label}. The important note was hidden, so {hero.id} first thought only junk had come."
        ),
        (
            f"Why did {hero.id} feel hurt at first?",
            f"{hero.id} saw the pile of {spam.label} and blamed {friend.id} too quickly. That made the lane feel sad because the truth had not been checked yet."
        ),
        (
            "What was the quest in the story?",
            f"The quest was to search the lane and find the missing {quest.note_name}. {helper.id} suggested looking carefully instead of staying cross."
        ),
    ]
    if f.get("found_note"):
        qa.append(
            (
                "How did they find the real note?",
                f"They searched past {world.setting.landmark} and kept looking in the little places where paper might drift. Then they found it at {cause.hide_spot}, where {cause.apology_reason} had hidden it."
            )
        )
    if f.get("reconciled"):
        qa.append(
            (
                "How did the friends make up?",
                f"{hero.id} said sorry for blaming in a rush, and {friend.id} answered with forgiveness. They spoke kindly to each other, so the misunderstanding could settle and their friendship could feel warm again."
            )
        )
        qa.append(
            (
                "What moral did the story teach?",
                f"It taught that children should ask kindly before blaming someone. Looking for the truth helped {hero.id} fix the mistake and keep the friendship."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"quest", "friendship", "kindness"}
    tags |= set(world.facts["spam"].tags)
    tags |= set(world.facts["cause"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
setting_allows(S, C) :- allows(S, C), cause(C).
valid(S, Q, Sp, C) :- setting(S), quest(Q), spam(Sp), cause(C), setting_allows(S, C), sensible(C).

misunderstanding :- chosen_cause(C), sensible(C).
found_note :- chosen_cause(C), setting_allows(chosen_setting, C), sensible(C).
reconciled :- found_note.

outcome(reconciled) :- reconciled.
outcome(lost) :- not reconciled.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.allows):
            lines.append(asp.fact("allows", sid, cid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for spid in SPAM_KINDS:
        lines.append(asp.fact("spam", spid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.sense >= KIND_MIN:
            lines.append(asp.fact("sensible", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    chosen_setting_fact = ""
    if "chosen_setting(" not in extra:
        chosen_setting_fact = "chosen_setting(dummy).\n"
    return f"{asp_facts()}\n{ASP_RULES}\n{chosen_setting_fact}{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_cause", params.cause),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not cause_fits(SETTINGS[params.setting], CAUSES[params.cause]):
        return "lost"
    return "reconciled"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: missing QA or prompts.")


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a quest note hidden among spam, a misunderstanding, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--spam", choices=SPAM_KINDS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause:
        setting = SETTINGS[args.setting]
        cause = CAUSES[args.cause]
        if not cause_fits(setting, cause):
            raise StoryError(explain_rejection(setting, cause))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.quest is None or c[1] == args.quest)
        and (args.spam is None or c[2] == args.spam)
        and (args.cause is None or c[3] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, quest_id, spam_id, cause_id = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    friend_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["girl", "boy"])
    used: set[str] = set()
    hero_name = _pick_name(rng, hero_type, used)
    used.add(hero_name)
    friend_name = _pick_name(rng, friend_type, used)
    used.add(friend_name)
    helper_name = _pick_name(rng, helper_type, used)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        quest=quest_id,
        spam=spam_id,
        cause=cause_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Invalid quest: {params.quest})")
    if params.spam not in SPAM_KINDS:
        raise StoryError(f"(Invalid spam kind: {params.spam})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Invalid parent: {params.parent})")
    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    if not cause_fits(setting, cause):
        raise StoryError(explain_rejection(setting, cause))

    world = tell(
        setting=setting,
        quest=QUESTS[params.quest],
        spam=SPAM_KINDS[params.spam],
        cause=cause,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (setting, quest, spam, cause) combos:\n")
        for setting, quest, spam, cause in combos:
            print(f"  {setting:13} {quest:12} {spam:8} {cause}")
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
            header = f"### {p.hero_name}: {p.quest} in {p.setting} ({p.spam}, {p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
