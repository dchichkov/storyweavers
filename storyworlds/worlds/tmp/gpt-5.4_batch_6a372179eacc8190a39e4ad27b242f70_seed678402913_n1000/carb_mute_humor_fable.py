#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py
===================================================

A standalone story world for a humorous little fable domain: an animal with an
important speaking job wolfs down a dry carb snack, goes nearly mute at the
worst moment, and must accept a sensible fix or improvise a funny silent ending.

The world model is small on purpose:

* a speaker has a duty on a stage-like setting
* a dry, carb-heavy snack raises crumbs/thirst and risks a lost voice
* a helper notices the risk and suggests a remedy
* a remedy may restore the voice in time, or fail and force a comic silent turn

The prose is driven by simulated state rather than slot-filling. The Q&A sets are
generated from world facts, not by scraping the rendered English.

Run it
------
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py --stage market --snack pretzel
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py --snack soup
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py --response whistle_louder
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py --all
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/carb_mute_humor_fable.py --verify
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
CARB_MIN = 2


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
        female = {"hen", "goose", "duck", "sheep", "woman", "mother"}
        male = {"rooster", "crow", "goat", "tortoise", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Stage:
    id: str
    place: str
    duty: str
    crowd: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    bite_text: str
    crumbs_text: str
    carb_score: int
    dryness: int
    dry: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    power: int
    action_text: str
    fail_text: str
    qa_text: str
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


def _r_stuck_voice(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    if speaker.meters["crumbs"] < THRESHOLD or speaker.meters["announce_attempt"] < THRESHOLD:
        return out
    sig = ("stuck_voice",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    speaker.meters["voice_trouble"] += 1
    speaker.meters["voice"] = 0.0
    speaker.memes["embarrassment"] += 1
    helper = world.get("helper")
    helper.memes["concern"] += 1
    out.append("__mute__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    if speaker.meters["crumbs"] >= THRESHOLD or speaker.meters["sipped"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    speaker.meters["voice"] = 1.0
    speaker.memes["relief"] += 1
    out.append("__voice_back__")
    return out


CAUSAL_RULES = [
    Rule(name="stuck_voice", tag="physical", apply=_r_stuck_voice),
    Rule(name="relief", tag="physical", apply=_r_relief),
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


def snack_hazard(snack: Snack) -> bool:
    return snack.dry and snack.carb_score >= CARB_MIN and snack.dryness >= 1


def sensible_responses() -> list[Remedy]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(snack: Snack, delay: int) -> int:
    return snack.dryness + delay


def restores_voice(remedy: Remedy, snack: Snack, delay: int) -> bool:
    return remedy.power >= severity_of(snack, delay)


def predict_trouble(world: World, snack: Snack) -> dict:
    sim = world.copy()
    eater = sim.get("speaker")
    eater.meters["crumbs"] += snack.dryness
    eater.meters["thirst"] += 1
    eater.meters["announce_attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "mute": sim.get("speaker").meters["voice"] < THRESHOLD,
        "crumbs": sim.get("speaker").meters["crumbs"],
    }


def introduce(world: World, speaker: Entity, helper: Entity, stage: Stage) -> None:
    speaker.memes["pride"] += 1
    helper.memes["friendliness"] += 1
    world.say(
        f"In {stage.place}, {speaker.id} the {speaker.type} had a very important job: "
        f"{stage.duty}."
    )
    world.say(
        f"{stage.crowd.capitalize()} watched, because everyone knew {speaker.id} loved an audience "
        f"almost as much as breakfast."
    )
    world.say(
        f"Beside the stage stood {helper.id} the {helper.type}, who noticed trouble almost as quickly "
        f"as crumbs."
    )


def boast(world: World, speaker: Entity, stage: Stage) -> None:
    speaker.memes["bragging"] += 1
    world.say(
        f'"Stand back," {speaker.id} said. "When I speak, {stage.image}."'
    )


def snack_temptation(world: World, speaker: Entity, helper: Entity, snack: Snack) -> None:
    pred = predict_trouble(world, snack)
    world.facts["predicted_mute"] = pred["mute"]
    speaker.memes["greed"] += 1
    world.say(
        f"Then {speaker.id} spotted {snack.phrase} on a nearby barrel and forgot all about pacing "
        f"and breathing."
    )
    world.say(
        f"He gobbled {snack.bite_text}. {helper.id} blinked and said, "
        f'"That is a lot of carb for one speech."'
    )
    if pred["mute"]:
        world.say(
            f'"If you swallow that much dry food at once," {helper.id} warned, '
            f'"your grand speech may turn mute before it even begins."'
        )


def gulp(world: World, speaker: Entity, snack: Snack) -> None:
    speaker.meters["crumbs"] += snack.dryness
    speaker.meters["thirst"] += 1
    speaker.meters["fullness"] += 1
    world.say(snack.crumbs_text)


def attempt_announcement(world: World, speaker: Entity, stage: Stage) -> None:
    speaker.meters["announce_attempt"] += 1
    propagate(world, narrate=False)
    if speaker.meters["voice"] < THRESHOLD:
        world.say(
            f"{speaker.id} hopped to the front, lifted {speaker.pronoun('possessive')} chest, and tried "
            f"to {stage.duty}. What came out was a tiny scratchy squeak."
        )
        world.say(
            f"The crowd leaned in. {speaker.id} tried again, but the proud little speaker stood almost mute, "
            f"with only a puff of crumbs to show for the effort."
        )
    else:
        world.say(
            f"{speaker.id} opened {speaker.pronoun('possessive')} beak and the words came out bright and clear."
        )


def offer_help(world: World, helper: Entity, remedy: Remedy) -> None:
    helper.memes["helpfulness"] += 1
    world.say(
        f'{helper.id} did not laugh at first. "{remedy.action_text}," {helper.pronoun()} said. '
        f'"A dry mouth is a silly enemy, but it is still an enemy."'
    )


def apply_remedy(world: World, speaker: Entity, helper: Entity, stage: Stage, snack: Snack, remedy: Remedy, delay: int) -> None:
    speaker.meters["waited"] += delay
    if restores_voice(remedy, snack, delay):
        speaker.meters["crumbs"] = 0.0
        speaker.meters["sipped"] += 1
        propagate(world, narrate=False)
        speaker.memes["gratitude"] += 1
        world.say(
            f"{speaker.id} obeyed at last. Soon the crumbs were gone, the throat felt smooth again, "
            f"and {speaker.pronoun('possessive')} voice came back just in time."
        )
        world.say(
            f'This time {speaker.pronoun()} spoke slowly, and the first clear words made the crowd chuckle: '
            f'"Next time, I shall chew before I command."'
        )
        world.say(
            f"Then {speaker.id} finished {stage.duty}, and {stage.crowd} clapped while {helper.id} tried not to look too smug."
        )
    else:
        speaker.meters["crumbs"] = max(1.0, float(snack.dryness - remedy.power))
        speaker.meters["sipped"] += 1
        propagate(world, narrate=False)
        speaker.memes["humility"] += 1
        world.say(
            f"{speaker.id} tried the remedy, but {remedy.fail_text}."
        )
        world.say(
            f"So {helper.id} rang a little bell for attention while {speaker.id} acted {stage.duty} with wings, "
            f"beak, and wild eyebrows."
        )
        world.say(
            f"The crowd laughed so hard that even the speaker had to laugh silently. No one forgot the announcement, "
            f"though, because a mute mime proved stranger than any speech."
        )


def ending_moral(world: World, speaker: Entity, helper: Entity, outcome: str) -> None:
    if outcome == "restored":
        world.say(
            f"Afterward, {speaker.id} thanked {helper.id} and saved the last crumbs for later. "
            f"From then on, {speaker.pronoun()} never mistook haste for greatness."
        )
    else:
        world.say(
            f"Afterward, {speaker.id} bowed, still crumb-dusted and wiser. "
            f"From then on, {speaker.pronoun()} ate first, spoke second, and kept a cup nearby."
        )


def tell(stage: Stage, snack: Snack, remedy: Remedy, speaker_name: str = "Rufus",
         speaker_type: str = "rooster", helper_name: str = "Moss", helper_type: str = "goat",
         delay: int = 0) -> World:
    world = World()
    speaker = world.add(Entity(
        id=speaker_name,
        kind="character",
        type=speaker_type,
        role="speaker",
        label=speaker_type,
        traits=["proud", "hungry"],
        tags={"speaker"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_type,
        traits=["calm", "watchful"],
        tags={"helper"},
    ))
    world.add(Entity(id="stage", type="place", label=stage.place, role="stage"))
    speaker.meters["voice"] = 1.0

    introduce(world, speaker, helper, stage)
    boast(world, speaker, stage)

    world.para()
    snack_temptation(world, speaker, helper, snack)
    gulp(world, speaker, snack)
    attempt_announcement(world, speaker, stage)

    world.para()
    offer_help(world, helper, remedy)
    apply_remedy(world, speaker, helper, stage, snack, remedy, delay)

    world.para()
    outcome = "restored" if speaker.meters["voice"] >= THRESHOLD else "mime"
    ending_moral(world, speaker, helper, outcome)

    world.facts.update(
        stage=stage,
        snack=snack,
        remedy=remedy,
        speaker=speaker,
        helper=helper,
        delay=delay,
        outcome=outcome,
        severity=severity_of(snack, delay),
        muted=speaker.meters["voice"] < THRESHOLD,
    )
    return world


STAGES = {
    "farm": Stage(
        id="farm",
        place="a sunny farmyard",
        duty="crow the morning awake",
        crowd="the hens, the sheep, and one sleepy cow",
        image="the gates seem to rattle with respect",
        tags={"farm", "announcement"},
    ),
    "market": Stage(
        id="market",
        place="the village market",
        duty="announce the noon pie contest",
        crowd="the bakers, the shoppers, and a pig with flour on his nose",
        image="even the cabbages seem to listen",
        tags={"market", "announcement"},
    ),
    "fair": Stage(
        id="fair",
        place="the riverside fair",
        duty="open the boat parade",
        crowd="the ducks, the otters, and a mayor in a straw hat",
        image="the flags seem to flutter in applause",
        tags={"fair", "announcement"},
    ),
}

SNACKS = {
    "bun": Snack(
        id="bun",
        label="bun",
        phrase="a warm wheat bun",
        bite_text="three enormous bites of the bun without a sip in between",
        crumbs_text="At once, soft crumbs pasted themselves to tongue and beak as if they meant to build a nest there.",
        carb_score=3,
        dryness=2,
        dry=True,
        tags={"bread", "carb"},
    ),
    "pretzel": Snack(
        id="pretzel",
        label="pretzel",
        phrase="a twisty pretzel bigger than his own foot",
        bite_text="big crackly mouthfuls of the pretzel",
        crumbs_text="Salt and crumbs flew everywhere, and the last dry bite seemed to steal the water right out of the air.",
        carb_score=3,
        dryness=3,
        dry=True,
        tags={"pretzel", "carb"},
    ),
    "cracker_stack": Snack(
        id="cracker_stack",
        label="cracker stack",
        phrase="a tall stack of seed crackers",
        bite_text="the top half of the cracker stack in a show-off crunch",
        crumbs_text="The crackers shattered into a dusty cloud, and soon every important word felt stuck behind a wall of crumbs.",
        carb_score=2,
        dryness=2,
        dry=True,
        tags={"cracker", "carb"},
    ),
    "soup": Snack(
        id="soup",
        label="soup",
        phrase="a bowl of vegetable soup",
        bite_text="the soup with eager slurps",
        crumbs_text="The soup slid down politely and left no crumbs at all.",
        carb_score=0,
        dryness=0,
        dry=False,
        tags={"soup"},
    ),
}

RESPONSES = {
    "water_sip": Remedy(
        id="water_sip",
        label="cool water",
        sense=3,
        power=3,
        action_text="take small sips of cool water and wait one honest minute",
        fail_text="the crumbs loosened a little, but the voice was still too scratchy for a proper announcement",
        qa_text="gave the speaker cool water and a short pause",
        tags={"water", "voice"},
    ),
    "tea_pause": Remedy(
        id="tea_pause",
        label="warm mint tea",
        sense=3,
        power=4,
        action_text="sip warm mint tea and stop showing off long enough to breathe",
        fail_text="the warm tea helped, yet the speaker had delayed too long and the voice still rasped",
        qa_text="offered warm mint tea and a calm pause",
        tags={"tea", "voice"},
    ),
    "apple_slice": Remedy(
        id="apple_slice",
        label="apple slices",
        sense=2,
        power=2,
        action_text="chew a few juicy apple slices slowly",
        fail_text="the apple helped the mouth, but not enough to clear the crumbs in time",
        qa_text="offered juicy apple slices and told the speaker to chew slowly",
        tags={"apple", "voice"},
    ),
    "whistle_louder": Remedy(
        id="whistle_louder",
        label="a loud whistle",
        sense=1,
        power=0,
        action_text="whistle even louder than before",
        fail_text="a whistle could not moisten a dry throat at all",
        qa_text="told the speaker to whistle louder",
        tags={"silly"},
    ),
}

SPEAKERS = [
    ("Rufus", "rooster"),
    ("Cora", "crow"),
    ("Gilda", "goose"),
]

HELPERS = [
    ("Moss", "goat"),
    ("Pip", "tortoise"),
    ("Tilda", "duck"),
]


@dataclass
class StoryParams:
    stage: str
    snack: str
    response: str
    speaker_name: str
    speaker_type: str
    helper_name: str
    helper_type: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "carb": [
        (
            "What is a carb?",
            "Carb is a short way to talk about carbohydrates, which are the part of foods like bread and crackers that give energy. Dry carb foods can also make your mouth feel dry if you eat them too fast."
        )
    ],
    "bread": [
        (
            "Why can bread make your mouth feel dry?",
            "Bread can soak up the moisture in your mouth, especially if you take big bites and do not sip any water. That can make speaking feel harder for a moment."
        )
    ],
    "pretzel": [
        (
            "Why are pretzels crumbly and salty?",
            "Pretzels are baked until dry, and the salt on them can make your mouth feel thirsty. That is why people often want a drink with them."
        )
    ],
    "cracker": [
        (
            "Why do crackers make crumbs?",
            "Crackers are dry and crisp, so they break into little pieces when you bite them. Those crumbs can stick in your mouth."
        )
    ],
    "water": [
        (
            "Why does water help a dry throat?",
            "Water adds moisture and washes crumbs down. A wetter throat makes it easier to speak clearly."
        )
    ],
    "tea": [
        (
            "Why can warm tea feel soothing?",
            "Warm tea can make a scratchy throat feel calmer and less tight. It also adds moisture, which helps the voice."
        )
    ],
    "apple": [
        (
            "Why can juicy fruit help a dry mouth?",
            "Juicy fruit has water in it, so it can make your mouth less dry. Chewing slowly also gives your throat time to settle."
        )
    ],
    "voice": [
        (
            "Why can talking fail if your mouth is too dry?",
            "Your voice needs air and a throat that can move smoothly. If your mouth and throat are dry or full of crumbs, words can come out scratchy or not at all."
        )
    ],
    "announcement": [
        (
            "What is an announcement?",
            "An announcement is when someone tells a group important news out loud. It works best when the speaker talks clearly and calmly."
        )
    ],
}


KNOWLEDGE_ORDER = ["carb", "bread", "pretzel", "cracker", "water", "tea", "apple", "voice", "announcement"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for snack_id, snack in SNACKS.items():
        if not snack_hazard(snack):
            continue
        for response_id, response in RESPONSES.items():
            if response.sense >= SENSE_MIN:
                combos.append((snack_id, response_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    speaker = f["speaker"]
    helper = f["helper"]
    stage = f["stage"]
    snack = f["snack"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    if outcome == "restored":
        return [
            f'Write a funny animal fable for a 3-to-5-year-old that includes the words "carb" and "mute".',
            f"Tell a gentle fable where {speaker.id} the {speaker.type} must {stage.duty}, but eats {snack.phrase} too quickly and nearly goes mute until {helper.id} helps.",
            f"Write a humorous story with a lesson about pride, crumbs, and patience, ending with {remedy.label} fixing the problem."
        ]
    return [
        f'Write a funny animal fable for a 3-to-5-year-old that includes the words "carb" and "mute".',
        f"Tell a humorous fable where {speaker.id} the {speaker.type} must {stage.duty}, but a dry snack steals the voice and the hero must finish in a silly silent way.",
        f"Write a child-facing fable about a boastful animal whose big speech fails, so a friend helps turn the mistake into a laugh."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    speaker = f["speaker"]
    helper = f["helper"]
    stage = f["stage"]
    snack = f["snack"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {speaker.id} the {speaker.type}, who had to {stage.duty}, and {helper.id} the {helper.type}, who watched and helped."
        ),
        (
            f"What problem did {speaker.id} have?",
            f"{speaker.id} ate {snack.phrase} too fast before speaking, so crumbs and dryness made the voice fail. That is why the grand announcement came out scratchy instead of strong."
        ),
        (
            f"Why did {helper.id} warn {speaker.id}?",
            f"{helper.id} could see that the snack was dry and heavy with carb, so it was likely to make speaking hard. The warning came before the speech because the helper noticed the risk in time."
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                f"How did {helper.id} fix the problem?",
                f"{helper.id} {remedy.qa_text}. That gave the throat moisture and a little time, so {speaker.id}'s voice returned before the duty was lost."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily and a little foolishly: {speaker.id} finally {stage.duty}, and the crowd laughed at the joke about chewing first. The ending shows that patience worked better than showing off."
            )
        )
    else:
        qa.append(
            (
                f"Could {speaker.id} speak clearly in time?",
                f"No. Even after {helper.id} {remedy.qa_text}, the voice stayed too rough for a proper speech. So the pair turned the problem into a funny silent performance instead."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a comic silent announcement. {helper.id} helped the crowd understand while {speaker.id} acted everything out, proving that a foolish mistake can still teach a wise lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"carb", "voice", "announcement"}
    snack = world.facts["snack"]
    remedy = world.facts["remedy"]
    tags |= set(snack.tags)
    tags |= set(remedy.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        stage="farm",
        snack="bun",
        response="water_sip",
        speaker_name="Rufus",
        speaker_type="rooster",
        helper_name="Moss",
        helper_type="goat",
        delay=0,
    ),
    StoryParams(
        stage="market",
        snack="pretzel",
        response="tea_pause",
        speaker_name="Cora",
        speaker_type="crow",
        helper_name="Pip",
        helper_type="tortoise",
        delay=0,
    ),
    StoryParams(
        stage="fair",
        snack="cracker_stack",
        response="apple_slice",
        speaker_name="Gilda",
        speaker_type="goose",
        helper_name="Tilda",
        helper_type="duck",
        delay=1,
    ),
]


def explain_rejection(snack: Snack) -> str:
    if not snack.dry:
        return (
            f"(No story: {snack.phrase} is not dry, so it would not plausibly make the speaker go mute. "
            f"Pick a dry carb snack like a bun, a pretzel, or crackers.)"
        )
    if snack.carb_score < CARB_MIN:
        return (
            f"(No story: {snack.phrase} is not carb-heavy enough for this fable's crumb-and-throat problem.)"
        )
    return "(No story: this snack does not create the right speaking hazard.)"


def explain_response(rid: str) -> str:
    remedy = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try a remedy that actually adds moisture or calm, such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    remedy = RESPONSES[params.response]
    snack = SNACKS[params.snack]
    return "restored" if restores_voice(remedy, snack, params.delay) else "mime"


ASP_RULES = r"""
hazard(S) :- snack(S), dry(S), carb_score(S, C), carb_min(M), C >= M, dryness(S, D), D >= 1.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, R) :- hazard(S), sensible(R).

severity(D + L) :- chosen_snack(S), dryness(S, D), delay(L).
strong_enough :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(restored) :- strong_enough.
outcome(mime) :- not strong_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in STAGES:
        lines.append(asp.fact("stage", sid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.dry:
            lines.append(asp.fact("dry", sid))
        lines.append(asp.fact("carb_score", sid, snack.carb_score))
        lines.append(asp.fact("dryness", sid, snack.dryness))
    for rid, remedy in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("carb_min", CARB_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_snack", params.snack),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while sampling seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome predictions differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a boastful animal, a dry carb snack, and a nearly mute speech."
    )
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the speaker waits before taking help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid snack/response combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack is not None:
        snack = SNACKS[args.snack]
        if not snack_hazard(snack):
            raise StoryError(explain_rejection(snack))
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        pair for pair in valid_combos()
        if (args.snack is None or pair[0] == args.snack)
        and (args.response is None or pair[1] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, response_id = rng.choice(sorted(combos))
    stage_id = args.stage or rng.choice(sorted(STAGES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    speaker_name, speaker_type = rng.choice(SPEAKERS)
    helper_name, helper_type = rng.choice(HELPERS)
    if helper_name == speaker_name:
        helper_name, helper_type = HELPERS[0]
    return StoryParams(
        stage=stage_id,
        snack=snack_id,
        response=response_id,
        speaker_name=speaker_name,
        speaker_type=speaker_type,
        helper_name=helper_name,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stage not in STAGES:
        raise StoryError(f"(Unknown stage: {params.stage})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    snack = SNACKS[params.snack]
    remedy = RESPONSES[params.response]
    if not snack_hazard(snack):
        raise StoryError(explain_rejection(snack))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        stage=STAGES[params.stage],
        snack=snack,
        remedy=remedy,
        speaker_name=params.speaker_name,
        speaker_type=params.speaker_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, response) combos:\n")
        for snack, response in combos:
            print(f"  {snack:14} {response}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.speaker_name}: {p.snack} at {p.stage} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
