#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py
============================================================================

A standalone storyworld for a small, rhyming, child-facing domain:

A child has a delicious snack. A friend's hungry belly makes a funny rumbling
sound. The hero notices, chooses a kind response, and the ending image proves
that sharing or fetching help changed the world.

The world model tracks physical state (hunger, crumbs, portions) and emotional
state (embarrassment, kindness, joy, friendship). It refuses unkind or
unworkable combinations. The prose is rendered from simulated state rather than
from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py --place park --snack pie --response share_half
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py --place park --snack peach --response share_half
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/delicious_belly_humor_kindness_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt"} .get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    spare_snack: bool
    helper_type: str
    helper_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    adjective: str
    smell: str
    portions: int
    share_word: str
    spare_phrase: str
    crumb_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    kindness: int
    mode: str
    text: str
    qa_text: str
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


def _r_rumble(world: World) -> list[str]:
    out: list[str] = []
    friend = world.entities.get("friend")
    snack = world.entities.get("snack")
    if friend is None or snack is None:
        return out
    if friend.meters["hunger"] < THRESHOLD:
        return out
    if snack.meters["visible"] < THRESHOLD:
        return out
    sig = ("rumble", "friend")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.meters["belly_rumble"] += 1
    friend.memes["embarrassment"] += 1
    out.append("__rumble__")
    return out


def _r_guilt(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    snack = world.entities.get("snack")
    if hero is None or friend is None or snack is None:
        return out
    if friend.meters["belly_rumble"] < THRESHOLD:
        return out
    if snack.meters["portion_left"] < THRESHOLD:
        return out
    sig = ("guilt", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["notice"] += 1
    hero.memes["kindness_pull"] += 1
    out.append("__notice__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    friend = world.entities.get("friend")
    hero = world.entities.get("hero")
    if friend is None or hero is None:
        return out
    if friend.meters["full"] < THRESHOLD:
        return out
    sig = ("relief", "friend")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.meters["hunger"] = 0.0
    friend.meters["belly_rumble"] = 0.0
    friend.memes["embarrassment"] = 0.0
    friend.memes["joy"] += 1
    hero.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="rumble", tag="physical", apply=_r_rumble),
    Rule(name="guilt", tag="emotional", apply=_r_guilt),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
                produced.extend(sents)
    if narrate:
        for item in produced:
            if item == "__rumble__":
                friend = world.get("friend")
                world.say(
                    f"Then {friend.id}'s belly gave a comic wiggle and a tiny grumble-snore; "
                    f"it sounded like a sleepy drum upon the picnic floor."
                )
            elif item == "__notice__":
                hero = world.get("hero")
                world.say(
                    f"{hero.id} heard the funny tummy tune and did not laugh to tease; "
                    f"{hero.pronoun().capitalize()} felt a tug of kindness move as softly as the breeze."
                )
            elif item == "__relief__":
                friend = world.get("friend")
                world.say(
                    f"Soon the rumble faded from {friend.id}'s middle with a satisfied little sigh; "
                    f"the hungry face grew bright again, as clouds grow bright with sky."
                )
    return produced


def can_share(snack: Snack) -> bool:
    return snack.portions >= 2


def can_fetch_spare(setting: Setting) -> bool:
    return setting.spare_snack


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.kindness >= KINDNESS_MIN]


def response_works(setting: Setting, snack: Snack, response: Response) -> bool:
    if response.mode == "share_half":
        return can_share(snack)
    if response.mode == "fetch_spare":
        return can_fetch_spare(setting)
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            for response_id, response in RESPONSES.items():
                if response.kindness < KINDNESS_MIN:
                    continue
                if response_works(setting, snack, response):
                    combos.append((place_id, snack_id, response_id))
    return combos


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too unkind for this world "
        f"(kindness={response.kindness} < {KINDNESS_MIN}). Try one of: {better}.)"
    )


def explain_rejection(setting: Setting, snack: Snack, response: Response) -> str:
    if response.mode == "share_half" and not can_share(snack):
        return (
            f"(No story: {snack.phrase} is a one-person snack here, so there is "
            f"no honest half to share. Pick a snack with at least two portions, "
            f"or choose a place where a spare snack can be fetched.)"
        )
    if response.mode == "fetch_spare" and not can_fetch_spare(setting):
        return (
            f"(No story: at {setting.place}, there is no nearby basket or helper "
            f"with a spare snack, so fetching one would not be reasonable.)"
        )
    return "(No story: this combination does not solve the hungry-belly problem.)"


def predict_relief(setting: Setting, snack: Snack, response: Response) -> dict:
    return {
        "works": response_works(setting, snack, response),
        "share_possible": can_share(snack),
        "spare_possible": can_fetch_spare(setting),
    }


def opening(world: World, hero: Entity, friend: Entity, snack_cfg: Snack) -> None:
    setting = world.setting
    snack = world.get("snack")
    snack.meters["visible"] = 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {setting.place}, where {setting.scene}, {hero.id} and {friend.id} spread a blanket bright; "
        f"the morning looked so merry that the grass itself seemed light."
    )
    world.say(
        f"{hero.id} unpacked {snack_cfg.phrase}, a delicious little treat; "
        f"its {snack_cfg.smell} curled through the air and danced around their feet."
    )


def play(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"They tapped two cups like silver bells and made a marching beat; "
        f"they giggled when an apple rolled and bumped the blanket seat."
    )


def hunger_turn(world: World, friend: Entity) -> None:
    friend.meters["hunger"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{friend.id} pressed both hands upon {friend.pronoun('possessive')} middle, cheeks a rosy red. "
        f'"I forgot my lunch," {friend.pronoun()} whispered. "My belly wants some bread."'
    )


def gentle_question(world: World, hero: Entity, friend: Entity, setting: Setting, snack: Snack, response: Response) -> None:
    pred = predict_relief(setting, snack, response)
    world.facts["predicted_works"] = pred["works"]
    world.facts["predicted_share_possible"] = pred["share_possible"]
    world.facts["predicted_spare_possible"] = pred["spare_possible"]
    if response.mode == "share_half":
        world.say(
            f'{hero.id} looked at the {snack.label} and then at {friend.id}\'s face. '
            f'"A snack tastes best in friendly bites; let\'s make a sharing space."'
        )
    else:
        helper = world.get("helper")
        world.say(
            f'{hero.id} looked toward {helper.label} by the basket near the tree. '
            f'"If I cannot split enough from mine, maybe {helper.label_word} can help with glee."'
        )


def do_share(world: World, hero: Entity, friend: Entity, snack_cfg: Snack) -> None:
    snack = world.get("snack")
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    snack.meters["portion_left"] = float(snack_cfg.portions - 1)
    snack.meters["shared_piece"] += 1
    snack.meters["crumbs"] += 1
    friend.meters["full"] += 1
    world.say(
        f"So {hero.id} broke the {snack_cfg.label} with careful, patient art; "
        f"{hero.pronoun().capitalize()} gave {friend.id} {snack_cfg.share_word}, the sweetest kindest part."
    )
    world.say(
        f"A crumb hopped to {hero.id}'s nose and made them both say, \"Hee-hee!\" "
        f"The joke was small and silly, and the sharing felt just right to see."
    )
    propagate(world, narrate=True)


def do_fetch(world: World, hero: Entity, friend: Entity, snack_cfg: Snack) -> None:
    helper = world.get("helper")
    basket = world.get("basket")
    hero.memes["kindness"] += 1
    helper.memes["care"] += 1
    basket.meters["spares_left"] -= 1
    friend.meters["full"] += 1
    world.say(
        f"So {hero.id} skipped to {helper.label}, who stood beside the basket there. "
        f"{helper.label_word.capitalize()} found {snack_cfg.spare_phrase} and tucked it in with care."
    )
    world.say(
        f"When {friend.id} took the extra bite, {friend.pronoun('possessive')} eyes grew wide and bright; "
        f'"This is delicious!" {friend.pronoun()} laughed. "My belly feels all right!"'
    )
    propagate(world, narrate=True)


def closing(world: World, hero: Entity, friend: Entity, response: Response) -> None:
    if response.mode == "share_half":
        world.say(
            f"Then side by side they chewed and smiled beneath the leaves above; "
            f"one tasty snack became, somehow, a bigger thing called love."
        )
    else:
        helper = world.get("helper")
        world.say(
            f"Then {helper.label_word} poured them minty tea and watched them grin and munch; "
            f"the blanket held more laughter than the basket held at lunch."
        )
    world.say(
        f"And when the breeze went bobbing by, it seemed to hum this telling: "
        f"a kindly heart can feed a friend and quiet a rumbling belly."
    )


def tell(
    setting: Setting,
    snack_cfg: Snack,
    response: Response,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    friend_name: str = "Omar",
    friend_gender: str = "boy",
    helper_name: str = "Auntie May",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=setting.helper_type,
            label=helper_name,
            phrase=helper_name,
            role="helper",
        )
    )
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label="basket", phrase="a wicker basket"))
    basket.meters["spares_left"] = 1.0 if setting.spare_snack else 0.0
    snack = world.add(Entity(id="snack", kind="thing", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase))
    snack.meters["portion_left"] = float(snack_cfg.portions)

    opening(world, hero, friend, snack_cfg)
    play(world, hero, friend)

    world.para()
    hunger_turn(world, friend)
    gentle_question(world, hero, friend, setting, snack_cfg, response)

    world.para()
    if response.mode == "share_half":
        do_share(world, hero, friend, snack_cfg)
    else:
        do_fetch(world, hero, friend, snack_cfg)
    closing(world, hero, friend, response)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        basket=basket,
        setting=setting,
        snack_cfg=snack_cfg,
        snack=snack,
        response=response,
        hungry_at_start=True,
        relieved=friend.meters["full"] >= THRESHOLD,
        shared=response.mode == "share_half",
        fetched=response.mode == "fetch_spare",
        crumbs=snack.meters["crumbs"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    snack: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "park": Setting(
        id="park",
        place="the park",
        scene="daisies nodded and a duck waddled past in polite delight",
        spare_snack=False,
        helper_type="aunt",
        helper_title="aunt",
        tags={"park", "picnic"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard",
        scene="pear trees swayed and patchy shade made stripes of gold and light",
        spare_snack=True,
        helper_type="aunt",
        helper_title="aunt",
        tags={"orchard", "basket"},
    ),
    "porch": Setting(
        id="porch",
        place="the sunny porch",
        scene="wind chimes clinked and geraniums leaned red and round and bright",
        spare_snack=True,
        helper_type="mother",
        helper_title="mom",
        tags={"porch", "basket"},
    ),
}

SNACKS = {
    "pie": Snack(
        id="pie",
        label="pie",
        phrase="a little honey pie",
        adjective="golden",
        smell="warm cinnamon smell",
        portions=2,
        share_word="half a flaky wedge",
        spare_phrase="another little honey pie",
        crumb_word="flaky crumb",
        tags={"pie", "food"},
    ),
    "muffins": Snack(
        id="muffins",
        label="muffins",
        phrase="two berry muffins",
        adjective="round",
        smell="sweet berry smell",
        portions=2,
        share_word="one plump muffin",
        spare_phrase="one more berry muffin",
        crumb_word="blue crumb",
        tags={"muffin", "food"},
    ),
    "sandwich": Snack(
        id="sandwich",
        label="sandwich",
        phrase="a jam sandwich cut in triangles",
        adjective="jammy",
        smell="strawberry smell",
        portions=2,
        share_word="one neat triangle",
        spare_phrase="an extra jam roll",
        crumb_word="soft crumb",
        tags={"sandwich", "food"},
    ),
    "peach": Snack(
        id="peach",
        label="peach",
        phrase="one ripe peach",
        adjective="juicy",
        smell="sunny peach smell",
        portions=1,
        share_word="half a peach slice",
        spare_phrase="a buttery bun",
        crumb_word="sticky drop",
        tags={"peach", "fruit"},
    ),
}

RESPONSES = {
    "share_half": Response(
        id="share_half",
        kindness=3,
        mode="share_half",
        text="share the snack",
        qa_text="shared the snack by giving part of it away",
        tags={"sharing", "kindness"},
    ),
    "fetch_spare": Response(
        id="fetch_spare",
        kindness=3,
        mode="fetch_spare",
        text="fetch a spare snack",
        qa_text="asked a nearby grown-up for a spare snack",
        tags={"help", "kindness"},
    ),
    "tease": Response(
        id="tease",
        kindness=0,
        mode="tease",
        text="tease the hungry friend",
        qa_text="laughed at the hungry friend instead of helping",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Mina", "Ava", "Zuri", "Ella", "Tess", "Nora"]
BOY_NAMES = ["Omar", "Theo", "Ben", "Milo", "Eli", "Noah", "Sam", "Finn"]
HELPER_NAMES = ["Auntie May", "Mama June", "Auntie Rose", "Dad Ben"]


KNOWLEDGE = {
    "hunger": [
        (
            "Why can a belly rumble when someone is hungry?",
            "A hungry belly can make little gurgling sounds because the stomach and intestines keep moving even when they are waiting for food. The noises are normal, even if they sound funny."
        )
    ],
    "sharing": [
        (
            "Why does sharing food feel kind?",
            "Sharing food helps someone else feel better, and it shows you noticed their need. Kindness often makes both people feel happier."
        )
    ],
    "help": [
        (
            "When should a child ask a grown-up for help with food?",
            "A child should ask a grown-up for help when there is not enough food to solve the problem alone or when they need permission. A nearby grown-up can help fairly and safely."
        )
    ],
    "pie": [
        (
            "What is a pie?",
            "A pie is a baked food with a crust around a sweet or savory filling. It can smell delicious when it is warm."
        )
    ],
    "muffin": [
        (
            "What is a muffin?",
            "A muffin is a small baked cake-like bread that can have fruit inside. It is easy to hold in your hand."
        )
    ],
    "sandwich": [
        (
            "What is a sandwich?",
            "A sandwich is food between pieces of bread. It is often packed for lunch because it is easy to carry."
        )
    ],
    "fruit": [
        (
            "What makes a peach juicy?",
            "A peach is full of water and sweet fruit flesh, so when you bite it the juice can come out. That is why ripe peaches can be messy and tasty at the same time."
        )
    ],
}
KNOWLEDGE_ORDER = ["hunger", "sharing", "help", "pie", "muffin", "sandwich", "fruit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    snack_cfg = f["snack_cfg"]
    response = f["response"]
    if response.mode == "share_half":
        angle = "shares the delicious snack"
    else:
        angle = "asks a grown-up for another snack"
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            f'"delicious" and "belly", uses gentle humor, and ends with kindness.'
        ),
        (
            f"Tell a rhyming picnic story where {hero.id} notices {friend.id}'s hungry belly and "
            f"{angle}."
        ),
        (
            f"Write a child-facing story with a funny tummy rumble, a kind choice, and a warm ending image around {snack_cfg.label}."
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    snack_cfg = f["snack_cfg"]
    response = f["response"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} having a snack time together in {setting.place}. A nearby grown-up, {helper.label}, is part of the world too."
        ),
        (
            f"Why did {friend.id}'s belly make a funny sound?",
            f"{friend.id} had forgotten lunch and was hungry, so {friend.pronoun('possessive')} belly began to rumble. The funny sound is the story's gentle joke, but it also shows a real need."
        ),
        (
            f"What made the snack seem delicious?",
            f"The {snack_cfg.label} smelled of {snack_cfg.smell}, and that sweet smell drifted through the air. The smell made the food sound tempting just when {friend.id} was hungry."
        ),
    ]
    if response.mode == "share_half":
        qa.append(
            (
                f"How did {hero.id} help {friend.id}?",
                f"{hero.id} shared the {snack_cfg.label} and gave {friend.id} {snack_cfg.share_word}. That kind choice turned one treat into a meal for two and quieted the rumbling belly."
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first there was hunger and a little embarrassment, but by the end there was relief, laughter, and friendship. The ending proves the change because the two children are eating together and smiling."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} solve the problem when one snack was not enough to share?",
                f"{hero.id} asked {helper.label} for help, and a spare snack came from the basket. That was kind because {hero.pronoun()} noticed the problem and found a real way to fix it."
            )
        )
        qa.append(
            (
                f"Why was asking {helper.label_word} a good idea?",
                f"It was a good idea because there was a nearby grown-up with extra food ready. Asking for help let {friend.id} eat enough instead of pretending the problem did not matter."
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"hunger"}
    response = f["response"]
    snack_cfg = f["snack_cfg"]
    if response.mode == "share_half":
        tags.add("sharing")
    if response.mode == "fetch_spare":
        tags.add("help")
    tags |= set(snack_cfg.tags)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(R) :- response(R), kindness(R, K), kindness_min(M), K >= M.

works(Place, Snack, share_half) :-
    setting(Place), snack(Snack), portions(Snack, P), P >= 2.

works(Place, Snack, fetch_spare) :-
    setting(Place), snack(Snack), has_spare(Place).

valid(Place, Snack, Response) :-
    setting(Place), snack(Snack), response(Response),
    reasonable(Response), works(Place, Snack, Response).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        if setting.spare_snack:
            lines.append(asp.fact("has_spare", place_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("portions", snack_id, snack.portions))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("kindness", response_id, response.kindness))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show reasonable/1."))
    return sorted(r for (r,) in asp.atoms(model, "reasonable"))


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "delicious" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include 'delicious'.")
    if "belly" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include 'belly'.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
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

    try:
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        place="park",
        snack="pie",
        response="share_half",
        hero_name="Nia",
        hero_gender="girl",
        friend_name="Omar",
        friend_gender="boy",
        helper_name="Auntie May",
    ),
    StoryParams(
        place="orchard",
        snack="peach",
        response="fetch_spare",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        helper_name="Auntie Rose",
    ),
    StoryParams(
        place="porch",
        snack="sandwich",
        response="share_half",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_name="Mama June",
    ),
    StoryParams(
        place="porch",
        snack="peach",
        response="fetch_spare",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Tess",
        friend_gender="girl",
        helper_name="Mama June",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a delicious snack, a funny hungry belly, and a kind solution."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--helper-name")
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


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].kindness < KINDNESS_MIN:
        raise StoryError(explain_response(args.response))

    if args.place and args.snack and args.response:
        setting = SETTINGS[args.place]
        snack = SNACKS[args.snack]
        response = RESPONSES[args.response]
        if not response_works(setting, snack, response):
            raise StoryError(explain_rejection(setting, snack, response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.snack is None or combo[1] == args.snack)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, snack_id, response_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place_id,
        snack=snack_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.place]
    snack = SNACKS[params.snack]
    response = RESPONSES[params.response]

    if response.kindness < KINDNESS_MIN:
        raise StoryError(explain_response(params.response))
    if not response_works(setting, snack, response):
        raise StoryError(explain_rejection(setting, snack, response))

    world = tell(
        setting=setting,
        snack_cfg=snack,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_name=params.helper_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show reasonable/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snack, response) combos:\n")
        for place_id, snack_id, response_id in combos:
            print(f"  {place_id:8} {snack_id:10} {response_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.snack} at {p.place} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
