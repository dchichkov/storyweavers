#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py
============================================================

A small storyworld for a gentle folk-tale shaped story about kindness in a
Jewish seaside village. A child on an errand sees a gull in need, pauses to
help, and later receives help in return.

The domain is intentionally narrow and state-driven:

- a village child carries something important along the shore
- a gull has one concrete need
- the child can help in one fitting way
- the delay creates a problem: the way home grows hard
- the gull's return kindness resolves the problem
- the ending image proves that kindness changed the day

Run it
------
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py --json
    python storyworlds/worlds/gpt-5.4/jewish_gull_kindness_folk_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Village:
    id: str
    place: str
    shore: str
    prayer_house: str
    market: str
    weather: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Errand:
    id: str
    carry: str
    basket_item: str
    recipient: str
    reason: str
    care_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GullNeed:
    id: str
    scene: str
    trouble_noun: str
    help_verb: str
    help_result: str
    fear_line: str
    reward_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ReturnProblem:
    id: str
    cause: str
    image: str
    child_problem: str
    gull_help: str
    ending: str
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


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    gull = world.get("gull")
    child = world.get("child")
    if gull.meters["helped"] < THRESHOLD:
        return out
    sig = ("gratitude",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gull.memes["trust"] += 1
    gull.memes["gratitude"] += 1
    child.memes["kindness"] += 1
    out.append("__gratitude__")
    return out


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    path = world.get("path")
    if child.meters["delayed"] < THRESHOLD:
        return out
    sig = ("delay",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["hard"] += 1
    child.memes["worry"] += 1
    out.append("__delay__")
    return out


def _r_return_kindness(world: World) -> list[str]:
    out: list[str] = []
    gull = world.get("gull")
    child = world.get("child")
    path = world.get("path")
    if gull.memes["gratitude"] < THRESHOLD or path.meters["hard"] < THRESHOLD:
        return out
    sig = ("return_kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gull.meters["guiding"] += 1
    path.meters["hard"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    out.append("__return__")
    return out


CAUSAL_RULES = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="delay", tag="physical", apply=_r_delay),
    Rule(name="return_kindness", tag="social", apply=_r_return_kindness),
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


VILLAGES = {
    "harbor": Village(
        id="harbor",
        place="a small jewish village by the sea",
        shore="the stony harbor shore",
        prayer_house="the whitewashed prayer house",
        market="the fish market",
        weather="a pearl-gray morning wind",
        closing_image="the lamps of the village looked warm as honey",
        tags={"jewish", "village", "sea"},
    ),
    "cliffs": Village(
        id="cliffs",
        place="a jewish village tucked beneath chalk cliffs",
        shore="the narrow strip of beach below the cliffs",
        prayer_house="the little prayer house with blue shutters",
        market="the lower market by the quay",
        weather="a bright salt wind",
        closing_image="the windows of the village shone like little stars",
        tags={"jewish", "village", "sea"},
    ),
    "cove": Village(
        id="cove",
        place="a jewish village beside a quiet cove",
        shore="the curved shore of the cove",
        prayer_house="the old stone prayer house",
        market="the lane of baskets and nets",
        weather="a soft morning breeze that smelled of salt",
        closing_image="the cove lay still as a polished bowl",
        tags={"jewish", "village", "sea"},
    ),
}

ERRANDS = {
    "bread": Errand(
        id="bread",
        carry="a small loaf of braided challah wrapped in cloth",
        basket_item="the braided loaf",
        recipient="an old neighbor",
        reason="before the evening meal",
        care_line="Bread carried for another person should arrive whole and warm.",
        tags={"bread", "kindness", "shabbat"},
    ),
    "soup": Errand(
        id="soup",
        carry="a covered crock of lentil soup",
        basket_item="the soup crock",
        recipient="the village teacher",
        reason="while the soup was still hot",
        care_line="Hot soup for a tired person should not be splashed or spilled.",
        tags={"soup", "kindness"},
    ),
    "candle": Errand(
        id="candle",
        carry="two Sabbath candles tucked safely in a basket",
        basket_item="the candles",
        recipient="a widow at the end of the lane",
        reason="before sunset",
        care_line="Candles meant for peace should be carried carefully.",
        tags={"candles", "kindness", "shabbat"},
    ),
}

GULL_NEEDS = {
    "tangled": GullNeed(
        id="tangled",
        scene="A young gull was hopping in circles with a bit of fishing line wound around one leg.",
        trouble_noun="the twisted line",
        help_verb="knelt in the wet stones and gently unwound the line",
        help_result="The gull gave one startled flap, then stood still and free.",
        fear_line="The gull's bright eye looked frightened, but it did not peck.",
        reward_hint="a free creature remembers the hand that frees it",
        tags={"gull", "rescue", "line"},
    ),
    "hungry": GullNeed(
        id="hungry",
        scene="A thin gull stood by an overturned basket, too weak to snatch even a crumb.",
        trouble_noun="its empty belly",
        help_verb="broke off a little of the food and laid the pieces on a flat stone",
        help_result="The gull swallowed the bites quickly, and strength came back into its wings.",
        fear_line="The gull watched every crumb as if it could hardly believe its luck.",
        reward_hint="even a hungry bird can carry gratitude in its heart",
        tags={"gull", "hunger", "food"},
    ),
    "parched": GullNeed(
        id="parched",
        scene="A gull with a dusty beak stood near the boats where even the puddles had dried white with salt.",
        trouble_noun="its thirst",
        help_verb="poured a little fresh water into a shell-shaped hollow in the rock",
        help_result="The gull drank, lifted its head, and cried once into the wind.",
        fear_line="Its beak opened and closed with the tired patience of a thirsty thing.",
        reward_hint="a drink given at the right moment can become a blessing",
        tags={"gull", "thirst", "water"},
    ),
}

RETURN_PROBLEMS = {
    "fog": ReturnProblem(
        id="fog",
        cause="While the child was helping, sea fog rolled in and blurred every lane and roof.",
        image="Soon the path home was no more than a pale ribbon in the gray.",
        child_problem="The child could not see which turning led back to the village.",
        gull_help="Then the gull rose, circled once, and flew ahead from post to post, crying until the child followed the right way home.",
        ending="At the gate, the gull wheeled above the roof and vanished into the mist.",
        tags={"fog", "lost", "guidance"},
    ),
    "tide": ReturnProblem(
        id="tide",
        cause="While the child was helping, the tide crept over the low stones and covered the easy way back.",
        image="Soon the old stepping path lay under shining water.",
        child_problem="The child could not cross without soaking the gift basket.",
        gull_help="Then the gull fluttered to a higher ridge of rocks and called again and again, showing a dry path the child had never noticed.",
        ending="At the top of the ridge, the gull spread its wings like a blessing and sailed away.",
        tags={"tide", "guidance", "shore"},
    ),
    "wind": ReturnProblem(
        id="wind",
        cause="While the child was helping, the wind freshened and sent market papers and spray spinning across the lane.",
        image="Soon the basket cloth tugged and snapped like a little sail.",
        child_problem="The child could not keep the basket steady and find the sheltered lane at the same time.",
        gull_help="Then the gull flew low along the wall where the wind was weakest, and the child followed that quiet strip all the way back.",
        ending="By the last doorway, the gull perched once, nodded its white head, and lifted into the sky.",
        tags={"wind", "guidance", "lane"},
    ),
}


def need_matches_help(need_id: str, errand_id: str) -> bool:
    if need_id == "tangled":
        return True
    if need_id == "hungry":
        return errand_id == "bread"
    if need_id == "parched":
        return errand_id in {"soup", "bread"}
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for village_id in VILLAGES:
        for errand_id in ERRANDS:
            for need_id in GULL_NEEDS:
                if not need_matches_help(need_id, errand_id):
                    continue
                for problem_id in RETURN_PROBLEMS:
                    combos.append((village_id, errand_id, need_id, problem_id))
    return combos


@dataclass
class StoryParams:
    village: str
    errand: str
    gull_need: str
    return_problem: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Miriam", "Leah", "Rivka", "Hannah", "Tova", "Sara", "Esther", "Nina"]
BOY_NAMES = ["Yonah", "Ariel", "David", "Ezra", "Noam", "Lev", "Asher", "Micah"]
TRAITS = ["gentle", "patient", "quick-footed", "thoughtful", "bright-eyed", "careful"]


def explain_rejection(errand_id: str, need_id: str) -> str:
    errand = ERRANDS[errand_id]
    need = GULL_NEEDS[need_id]
    if need_id == "hungry":
        return (
            f"(No story: a hungry gull needs food, but {errand.basket_item} cannot be shared "
            f"in a sensible way here. Pick the bread errand if you want the child to feed the gull.)"
        )
    if need_id == "parched":
        return (
            f"(No story: a thirsty gull needs fresh water, and this errand does not give the child "
            f"a reasonable way to offer it. Pick bread or soup instead.)"
        )
    return (
        f"(No story: this errand does not fit the gull's need for {need.trouble_noun}. "
        f"Choose a help that a child could honestly give.)"
    )


def predict_return_help(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["delayed"] += 1
    sim.facts["return_problem"] = RETURN_PROBLEMS[problem_id]
    propagate(sim, narrate=False)
    return {
        "path_hard": sim.get("path").meters["hard"] >= THRESHOLD,
        "guided": sim.get("gull").meters["guiding"] >= THRESHOLD,
    }


def introduce(world: World, village: Village, child: Entity, elder: Entity, errand: Errand) -> None:
    world.say(
        f"In {village.place}, where gulls wheeled over the roofs and the sea muttered against the stones, "
        f"there lived a {child.traits[0]} child named {child.id}."
    )
    world.say(
        f"One morning, {child.id}'s {elder.label_word} placed {errand.carry} into {child.pronoun('possessive')} hands "
        f"and asked {child.pronoun('object')} to carry it to {errand.recipient} {errand.reason}."
    )
    world.say(
        f'"Walk carefully," said the {elder.label_word}. "{errand.care_line}"'
    )


def cross_shore(world: World, village: Village, child: Entity, errand: Errand) -> None:
    child.memes["duty"] += 1
    world.say(
        f"{child.id} walked by {village.shore}, for that was the shortest road to {village.market}. "
        f"{village.weather} tugged at the basket cloth."
    )
    world.say(
        f"In the basket rested {errand.basket_item}, and {child.id} meant to arrive on time."
    )


def spot_gull(world: World, child: Entity, need: GullNeed) -> None:
    world.say(need.scene)
    world.say(need.fear_line)
    child.memes["pity"] += 1


def choose_kindness(world: World, child: Entity, need: GullNeed) -> None:
    world.say(
        f"{child.id} stopped. The village road called one way, and kindness called the other."
    )
    world.say(
        f"So {child.pronoun()} {need.help_verb}."
    )
    gull = world.get("gull")
    gull.meters["helped"] += 1
    child.meters["delayed"] += 1
    propagate(world, narrate=False)
    world.say(need.help_result)


def elder_warning_echo(world: World, child: Entity, need: GullNeed) -> None:
    gull = world.get("gull")
    if gull.memes["gratitude"] >= THRESHOLD:
        world.say(
            f"The gull looked at {child.id} with one bright black eye, as if memorizing the face of its helper."
        )
    world.say(
        f"{child.id} almost hurried on at once, but a folk-tale hush seemed to fall over the shore."
    )


def trouble_rises(world: World, problem: ReturnProblem, child: Entity) -> None:
    world.say(problem.cause)
    world.say(problem.image)
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} held the basket close. {problem.child_problem}"
        )


def gull_returns_kindness(world: World, problem: ReturnProblem, child: Entity) -> None:
    gull = world.get("gull")
    if gull.meters["guiding"] < THRESHOLD:
        raise StoryError("(Internal story error: the gull never learned how to guide the child home.)")
    world.say(problem.gull_help)
    world.say(
        f"{child.id} followed without arguing, and before long the right door and lane rose up from the weather as plainly as a promise."
    )


def deliver_errand(world: World, elder: Entity, errand: Errand, child: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["belonging"] += 1
    world.say(
        f"The gift reached {errand.recipient} safely at last, and not a bit of it had been spoiled."
    )
    world.say(
        f"When {child.id} told the tale that evening, the {elder.label_word} smiled and said, "
        f'"In this world, kindness is never lost. It only circles wide before it comes home."'
    )


def ending_image(world: World, village: Village, problem: ReturnProblem, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(problem.ending)
    world.say(
        f"Then {child.id} looked back toward the sea. {village.closing_image}, and in the crying of the distant gulls "
        f"{child.pronoun()} heard the day answer itself."
    )


def tell(
    village: Village,
    errand: Errand,
    need: GullNeed,
    problem: ReturnProblem,
    child_name: str,
    child_gender: str,
    elder_type: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[child_trait],
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            tags={"family"},
        )
    )
    gull = world.add(
        Entity(
            id="gull",
            kind="character",
            type="bird",
            role="gull",
            label="the gull",
            tags={"gull"},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label="basket",
            phrase=errand.carry,
            tags=set(errand.tags),
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="thing",
            type="path",
            label="shore path",
            tags=set(problem.tags),
        )
    )

    introduce(world, village, child, elder, errand)
    cross_shore(world, village, child, errand)

    world.para()
    spot_gull(world, child, need)
    choose_kindness(world, child, need)
    elder_warning_echo(world, child, need)

    world.para()
    trouble_rises(world, problem, child)
    gull_returns_kindness(world, problem, child)

    world.para()
    deliver_errand(world, elder, errand, child)
    ending_image(world, village, problem, child)

    world.facts.update(
        village=village,
        errand=errand,
        gull_need=need,
        return_problem=problem,
        child=child,
        elder=elder,
        gull=gull,
        basket=basket,
        path=path,
        delayed=child.meters["delayed"] >= THRESHOLD,
        helped=gull.meters["helped"] >= THRESHOLD,
        guided=gull.meters["guiding"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "jewish": [
        (
            "What does Jewish mean?",
            "Jewish describes the people, traditions, and faith connected with Judaism. A Jewish family may keep special days, prayers, foods, and customs."
        )
    ],
    "gull": [
        (
            "What is a gull?",
            "A gull is a seabird with strong wings that often lives near beaches, boats, and harbors. It watches the shore carefully for food and safe places to land."
        )
    ],
    "challah": [
        (
            "What is challah?",
            "Challah is a braided bread often eaten on the Sabbath and on special Jewish days. It is soft, golden, and meant to be shared at the table."
        )
    ],
    "candles": [
        (
            "Why do people light Sabbath candles?",
            "Many Jewish families light Sabbath candles to welcome the peaceful holy time. The candles help mark that the ordinary week is pausing."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing another creature's need and choosing to help. A kind act can be small, but it can still change someone's whole day."
        )
    ],
    "fog": [
        (
            "Why is fog hard to walk through?",
            "Fog hides faraway things and blurs the shape of roads and houses. That makes it easy to lose the right path."
        )
    ],
    "tide": [
        (
            "What is the tide?",
            "The tide is the sea moving higher and lower along the shore. When it rises, safe stones and paths can disappear under water."
        )
    ],
    "wind": [
        (
            "Why can strong wind make carrying things hard?",
            "Strong wind tugs at cloth and baskets and can push spray into your face. That makes it harder to walk carefully and keep things steady."
        )
    ],
}
KNOWLEDGE_ORDER = ["jewish", "gull", "challah", "candles", "kindness", "fog", "tide", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    errand = f["errand"]
    need = f["gull_need"]
    problem = f["return_problem"]
    village = f["village"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "jewish" and "gull" and centers on kindness.',
        f"Tell a gentle folk tale set in {village.place} where a child named {child.id} pauses on an errand to help a gull in trouble and is helped in return.",
        f"Write a story where {child.id} is carrying {errand.carry}, helps a gull with {need.trouble_noun}, and later finds the way home through {problem.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    errand = f["errand"]
    need = f["gull_need"]
    problem = f["return_problem"]
    village = f["village"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child from {village.place}, and a gull by the shore. It is also about {child.id}'s {elder.label_word}, who sends {child.pronoun('object')} on a careful errand."
        ),
        (
            f"What was {child.id} carrying?",
            f"{child.pronoun().capitalize()} was carrying {errand.carry} to {errand.recipient}. The basket mattered because it was a gift meant to arrive safely and on time."
        ),
        (
            "What trouble did the gull have?",
            f"The gull was suffering from {need.trouble_noun}. {child.id} could see the need with {child.pronoun('possessive')} own eyes, so the choice to help became real and urgent."
        ),
        (
            f"How did {child.id} show kindness?",
            f"{child.id} stopped the errand for a moment and {need.help_verb}. That cost time, but it relieved the gull's trouble right away."
        ),
    ]
    if f.get("delayed"):
        qa.append(
            (
                f"What problem came after {child.id} helped the gull?",
                f"After {child.id} stopped to help, {problem.cause.lower()} {problem.child_problem} The new problem came from the delay, not from bad behavior, which makes the story feel like a folk-tale test of kindness."
            )
        )
    if f.get("guided"):
        qa.append(
            (
                "How did the gull repay the kindness?",
                f"The gull returned and guided {child.id} home. {problem.gull_help} That made the ending feel earned, because the child first helped the bird when there was nothing to gain."
            )
        )
    qa.append(
        (
            "What lesson did the elder give at the end?",
            'The elder says that kindness is never lost and comes home again. That means a good deed can travel outward and later return as help, comfort, or blessing.'
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"jewish", "gull", "kindness"}
    errand = f["errand"]
    problem = f["return_problem"]
    if "shabbat" in errand.tags or errand.id == "bread":
        tags.add("challah")
    if errand.id == "candle":
        tags.add("candles")
    tags |= set(problem.tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        village="harbor",
        errand="bread",
        gull_need="hungry",
        return_problem="fog",
        child_name="Miriam",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="gentle",
    ),
    StoryParams(
        village="cliffs",
        errand="soup",
        gull_need="parched",
        return_problem="wind",
        child_name="Ezra",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="thoughtful",
    ),
    StoryParams(
        village="cove",
        errand="candle",
        gull_need="tangled",
        return_problem="tide",
        child_name="Leah",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="careful",
    ),
    StoryParams(
        village="harbor",
        errand="bread",
        gull_need="tangled",
        return_problem="wind",
        child_name="Ariel",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="patient",
    ),
]


ASP_RULES = r"""
valid(V, E, N, P) :- village(V), errand(E), need(N), problem(P), compatible(E, N).

guided(E, N, P) :- compatible(E, N), problem(P).
outcome(returned_kindness) :- chosen_errand(E), chosen_need(N), chosen_problem(P), guided(E, N, P).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for village_id in VILLAGES:
        lines.append(asp.fact("village", village_id))
    for errand_id in ERRANDS:
        lines.append(asp.fact("errand", errand_id))
    for need_id in GULL_NEEDS:
        lines.append(asp.fact("need", need_id))
    for problem_id in RETURN_PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for errand_id in ERRANDS:
        for need_id in GULL_NEEDS:
            if need_matches_help(need_id, errand_id):
                lines.append(asp.fact("compatible", errand_id, need_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_errand", params.errand),
            asp.fact("chosen_need", params.gull_need),
            asp.fact("chosen_problem", params.return_problem),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not need_matches_help(params.gull_need, params.errand):
        return "invalid"
    return "returned_kindness"


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
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Verify smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a Jewish seaside folk tale of kindness and a grateful gull."
    )
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--gull-need", dest="gull_need", choices=GULL_NEEDS)
    ap.add_argument("--return-problem", dest="return_problem", choices=RETURN_PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", dest="elder_type", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.errand and args.gull_need and not need_matches_help(args.gull_need, args.errand):
        raise StoryError(explain_rejection(args.errand, args.gull_need))

    combos = [
        combo
        for combo in valid_combos()
        if (args.village is None or combo[0] == args.village)
        and (args.errand is None or combo[1] == args.errand)
        and (args.gull_need is None or combo[2] == args.gull_need)
        and (args.return_problem is None or combo[3] == args.return_problem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    village_id, errand_id, need_id, problem_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    return StoryParams(
        village=village_id,
        errand=errand_id,
        gull_need=need_id,
        return_problem=problem_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        village = VILLAGES[params.village]
        errand = ERRANDS[params.errand]
        need = GULL_NEEDS[params.gull_need]
        problem = RETURN_PROBLEMS[params.return_problem]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not need_matches_help(params.gull_need, params.errand):
        raise StoryError(explain_rejection(params.errand, params.gull_need))

    world = tell(
        village=village,
        errand=errand,
        need=need,
        problem=problem,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
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
        print(asp_program(show="#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (village, errand, need, problem) combos:\n")
        for village_id, errand_id, need_id, problem_id in combos:
            print(f"  {village_id:8} {errand_id:7} {need_id:8} {problem_id}")
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
            header = (
                f"### {p.child_name}: {p.errand} errand, {p.gull_need} gull, "
                f"{p.return_problem} on the way home"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
