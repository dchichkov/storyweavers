#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py
====================================================

A standalone story world for gentle fable-like tales about an awkward request,
a confusing bit of dialogue, and the better thing that happens when a small
animal speaks plainly at last.

The domain is intentionally narrow and state-driven:

- a small seeker wants something physically out of reach
- a possible helper is nearby
- the seeker speaks in an awkward way instead of asking directly
- the helper is confused, and silence grows
- the seeker either repairs the dialogue in time or misses the chance
- the ending proves what changed: the object is reached or left behind

The world prefers stories where the helper's body and ability actually fit the
problem, and where the repair move is sensible enough to belong in a child-facing
fable.

Run it
------
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py --place orchard --need branch_pear --helper crane
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py --repair joke
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py --all
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/awkward_dialogue_fable.py --qa --json
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
        female = {"hen", "goose", "turtle", "girl", "mother"}
        male = {"mouse", "rabbit", "goat", "crane", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    image: str = ""


@dataclass
class Need:
    id: str
    label: str
    object_label: str
    object_phrase: str
    requirement: str
    problem: str
    opening: str
    solved_line: str
    failure_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    type: str
    abilities: set[str] = field(default_factory=set)
    patience: int = 1
    help_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class AwkwardStyle:
    id: str
    label: str
    level: int
    opener: str
    follow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    power: int
    line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_confusion_to_silence(world: World) -> list[str]:
    seeker = world.entities.get("seeker")
    helper = world.entities.get("helper")
    if seeker is None or helper is None:
        return []
    if helper.memes["confusion"] < THRESHOLD:
        return []
    sig = ("silence",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["embarrassment"] += 1
    helper.memes["distance"] += 1
    world.facts["awkward_silence"] = True
    return ["__silence__"]


def _r_help_solves_need(world: World) -> list[str]:
    need = world.facts.get("need_cfg")
    obj = world.entities.get("object")
    helper = world.entities.get("helper")
    seeker = world.entities.get("seeker")
    if need is None or obj is None or helper is None or seeker is None:
        return []
    if helper.meters["helping"] < THRESHOLD:
        return []
    sig = ("solved", need.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obj.meters["reachable"] = 1.0
    seeker.meters["need_met"] = 1.0
    seeker.memes["relief"] += 1
    seeker.memes["gratitude"] += 1
    helper.memes["warmth"] += 1
    return [need.solved_line]


CAUSAL_RULES = [
    Rule(name="confusion_to_silence", tag="social", apply=_r_confusion_to_silence),
    Rule(name="help_solves_need", tag="physical", apply=_r_help_solves_need),
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


def need_feasible(place: Place, need: Need) -> bool:
    return need.id in place.affords


def helper_can_help(helper: HelperKind, need: Need) -> bool:
    return need.requirement in helper.abilities


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def tension_score(style: AwkwardStyle, delay: int) -> int:
    return style.level + delay


def can_repair(style: AwkwardStyle, helper: HelperKind, repair: Repair, delay: int) -> bool:
    return repair.power + helper.patience >= tension_score(style, delay) + 1


def predict_dialogue(place: Place, need: Need, helper_cfg: HelperKind,
                     style: AwkwardStyle, repair: Repair, delay: int) -> dict:
    return {
        "confused": style.level >= 1,
        "awkward": True,
        "solved": can_repair(style, helper_cfg, repair, delay),
    }


def introduce(world: World, seeker: Entity, need: Need) -> None:
    world.say(
        f"In {world.place.label}, {seeker.id} the {seeker.label} found {need.object_phrase}. "
        f"{need.opening}"
    )
    seeker.memes["desire"] += 1
    world.say(world.place.image)


def show_problem(world: World, seeker: Entity, need: Need) -> None:
    seeker.meters["need"] += 1
    world.say(
        f"{seeker.id} wanted {need.object_label}, but {need.problem}. "
        f"So {seeker.pronoun()} looked around for help."
    )


def meet_helper(world: World, helper: Entity, helper_cfg: HelperKind) -> None:
    world.say(
        f"Nearby stood {helper.id} the {helper_cfg.label}, {helper_cfg.phrase}."
    )


def awkward_attempt(world: World, seeker: Entity, helper: Entity, style: AwkwardStyle) -> None:
    seeker.memes["pride"] += 1
    helper.memes["confusion"] += 1
    world.say(
        f'{seeker.id} shuffled {seeker.pronoun("possessive")} feet and tried to speak without plainly asking. '
        f'"{style.opener}"'
    )
    world.say(f'"{style.follow}" answered {helper.id}.')
    propagate(world, narrate=False)
    if world.facts.get("awkward_silence"):
        world.say(
            "Then an awkward silence sat between them like a stone on the path."
        )


def second_pause(world: World, seeker: Entity, helper: Entity, delay: int) -> None:
    if delay <= 0:
        return
    seeker.memes["embarrassment"] += 1
    helper.memes["distance"] += 1
    world.say(
        f"{seeker.id} looked at the ground for one more breath instead of speaking. "
        f"{helper.id} began to turn away."
    )


def repair_dialogue(world: World, seeker: Entity, helper: Entity, repair: Repair) -> None:
    seeker.memes["courage"] += 1
    helper.memes["distance"] = 0.0
    world.say(f'"{repair.line}" said {seeker.id} at last.')
    world.say(
        f"{helper.id} stopped and listened with both ears."
    )


def helper_acts(world: World, seeker: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    helper.meters["helping"] += 1
    world.say(helper_cfg.help_text)
    propagate(world, narrate=True)


def gratitude(world: World, seeker: Entity, helper: Entity) -> None:
    world.say(
        f'"Thank you for helping me after I spoke so poorly," said {seeker.id}. '
        f'"Plain words are kinder than proud ones."'
    )
    world.say(
        f'"Plain words are easier to carry," said {helper.id}, and the two shared a small smile.'
    )


def missed_chance(world: World, seeker: Entity, helper: Entity, need: Need, repair: Repair) -> None:
    seeker.memes["regret"] += 1
    world.say(
        f'{seeker.id} tried to mend the moment with "{repair.line}," but the words came too late.'
    )
    world.say(
        f"{helper.id} had already gone on down the path, and {need.failure_line}"
    )


def close_moral(world: World, seeker: Entity, solved: bool) -> None:
    if solved:
        world.say(
            f"That evening, {seeker.id} ate with an easy heart and remembered that a humble mouth opens more doors than a proud one."
        )
    else:
        world.say(
            f"Before the sun dipped low, {seeker.id} learned a harder lesson: when need is true, speak it plainly before silence grows heavy."
        )


def tell(place: Place, need: Need, helper_cfg: HelperKind, style: AwkwardStyle,
         repair: Repair, seeker_name: str = "Milo", seeker_type: str = "mouse",
         helper_name: str = "Corin", delay: int = 0) -> World:
    world = World(place)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        label=seeker_type,
        role="seeker",
        traits=["small"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        traits=["steady"],
    ))
    obj = world.add(Entity(
        id="object",
        kind="thing",
        type="object",
        label=need.object_label,
        phrase=need.object_phrase,
        tags=set(need.tags),
    ))
    seeker.memes["hunger"] += 1
    world.facts.update(
        seeker=seeker,
        helper=helper,
        object=obj,
        place_cfg=place,
        need_cfg=need,
        helper_cfg=helper_cfg,
        style_cfg=style,
        repair_cfg=repair,
        delay=delay,
    )

    introduce(world, seeker, need)
    show_problem(world, seeker, need)
    meet_helper(world, helper, helper_cfg)

    world.para()
    awkward_attempt(world, seeker, helper, style)
    second_pause(world, seeker, helper, delay)

    solved = can_repair(style, helper_cfg, repair, delay)
    world.para()
    if solved:
        repair_dialogue(world, seeker, helper, repair)
        helper_acts(world, seeker, helper, helper_cfg)
        gratitude(world, seeker, helper)
    else:
        missed_chance(world, seeker, helper, need, repair)

    world.para()
    close_moral(world, seeker, solved)

    world.facts["outcome"] = "solved" if solved else "missed"
    world.facts["awkward"] = True
    world.facts["solved"] = solved
    return world


PLACES = {
    "orchard": Place(
        id="orchard",
        label="a quiet orchard",
        affords={"branch_pear"},
        image="The leaves whispered above him, and the late pears shone yellow in the sun.",
    ),
    "pond": Place(
        id="pond",
        label="a still pond",
        affords={"drifting_apple"},
        image="Round reeds leaned over the water, and the pond held the sky like a polished bowl.",
    ),
    "farmyard": Place(
        id="farmyard",
        label="a dusty farmyard",
        affords={"stuck_sack"},
        image="A cart stood near the shed, and the yard smelled of straw warmed by noon.",
    ),
}

NEEDS = {
    "branch_pear": Need(
        id="branch_pear",
        label="high pear",
        object_label="the pear",
        object_phrase="a ripe pear on the highest branch",
        requirement="reach_high",
        problem="it hung far above his paws",
        opening="The fruit looked sweet enough to make his mouth water.",
        solved_line="With one careful stretch, the pear came down at last.",
        failure_line="the pear stayed high in the leaves where his small paws could not reach it.",
        tags={"pear", "asking_help"},
    ),
    "drifting_apple": Need(
        id="drifting_apple",
        label="drifting apple",
        object_label="the apple",
        object_phrase="a red apple drifting just beyond the stepping stones",
        requirement="swim",
        problem="the water was deeper than his brave face admitted",
        opening="It rocked on the water as if it were teasing him.",
        solved_line="A gentle push sent the apple bobbing back to shore.",
        failure_line="the apple drifted farther from the bank until it was only a red dot on the pond.",
        tags={"apple", "asking_help", "water"},
    ),
    "stuck_sack": Need(
        id="stuck_sack",
        label="stuck grain sack",
        object_label="the little sack of grain",
        object_phrase="a little sack of grain wedged under a cart wheel",
        requirement="strength",
        problem="he could tug at it but could not pull it free",
        opening="It smelled of oats, and his stomach gave a hopeful little twist.",
        solved_line="One strong nudge rolled the wheel enough for the sack to slide free.",
        failure_line="the sack remained trapped under the wheel, close enough to smell but not to carry off.",
        tags={"grain", "asking_help"},
    ),
}

HELPERS = {
    "crane": HelperKind(
        id="crane",
        label="crane",
        phrase="tall and calm, with a beak that could reach where shorter folk could not",
        type="crane",
        abilities={"reach_high"},
        patience=2,
        help_text="The crane lifted his long neck, stretched his beak, and worked with slow care instead of hurry.",
        tags={"bird", "reach"},
    ),
    "turtle": HelperKind(
        id="turtle",
        label="turtle",
        phrase="steady as a little boat, with patient eyes and a sure shell",
        type="turtle",
        abilities={"swim"},
        patience=3,
        help_text="The turtle slid into the water, made one smooth circle, and nudged the prize toward the bank.",
        tags={"water", "swim"},
    ),
    "goat": HelperKind(
        id="goat",
        label="goat",
        phrase="broad-shouldered and practical, with hooves that planted firmly in the dirt",
        type="goat",
        abilities={"strength"},
        patience=1,
        help_text="The goat lowered his head, braced his hooves, and pushed with a tidy burst of strength.",
        tags={"farm", "strength"},
    ),
}

STYLES = {
    "hint": AwkwardStyle(
        id="hint",
        label="hinting",
        level=1,
        opener="That thing over there certainly looks lonely.",
        follow="Lonely things are not always asking for company",
        tags={"hint"},
    ),
    "brag": AwkwardStyle(
        id="brag",
        label="bragging",
        level=2,
        opener="I could fetch it myself, if I cared to show off.",
        follow="Then perhaps you do not need me at all",
        tags={"pride"},
    ),
    "mumble": AwkwardStyle(
        id="mumble",
        label="mumbling",
        level=2,
        opener="It is nothing. Only... well... never mind.",
        follow="If it is nothing, I shall not trouble it",
        tags={"silence"},
    ),
}

REPAIRS = {
    "honest": Repair(
        id="honest",
        label="honest ask",
        sense=3,
        power=2,
        line="Please help me. I wanted that, and I was too proud to ask plainly",
        qa_line="asked plainly for help and admitted his pride",
        tags={"honest_words"},
    ),
    "apology": Repair(
        id="apology",
        label="apology and ask",
        sense=3,
        power=3,
        line="I am sorry for my crooked words. Will you help me, please",
        qa_line="apologized for the awkward words and then asked clearly",
        tags={"honest_words", "apology"},
    ),
    "joke": Repair(
        id="joke",
        label="joking cover",
        sense=1,
        power=1,
        line="I was only making a joke, unless you happened to help anyway",
        qa_line="hid the request inside another joke",
        tags={"joke"},
    ),
}

SEEKERS = [
    ("Milo", "mouse"),
    ("Pip", "rabbit"),
    ("Nell", "hen"),
    ("Tavi", "mouse"),
    ("Runa", "goose"),
]


@dataclass
class StoryParams:
    place: str
    need: str
    helper: str
    style: str
    repair: str
    seeker_name: str
    seeker_type: str
    helper_name: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="orchard",
        need="branch_pear",
        helper="crane",
        style="hint",
        repair="honest",
        seeker_name="Milo",
        seeker_type="mouse",
        helper_name="Corin",
        delay=0,
    ),
    StoryParams(
        place="pond",
        need="drifting_apple",
        helper="turtle",
        style="mumble",
        repair="apology",
        seeker_name="Pip",
        seeker_type="rabbit",
        helper_name="Mira",
        delay=1,
    ),
    StoryParams(
        place="farmyard",
        need="stuck_sack",
        helper="goat",
        style="brag",
        repair="apology",
        seeker_name="Nell",
        seeker_type="hen",
        helper_name="Bram",
        delay=0,
    ),
    StoryParams(
        place="farmyard",
        need="stuck_sack",
        helper="goat",
        style="brag",
        repair="honest",
        seeker_name="Tavi",
        seeker_type="mouse",
        helper_name="Bram",
        delay=1,
    ),
]


KNOWLEDGE = {
    "asking_help": [
        (
            "Why is it better to ask for help plainly?",
            "Plain asking helps other people understand what you truly need. If you hide the need inside bragging or hints, they may feel confused instead of helpful.",
        )
    ],
    "honest_words": [
        (
            "What do honest words do in a conversation?",
            "Honest words make your meaning easier to hear. They can turn a tangled talk into a kind and useful one.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know your words or actions hurt or confused them. It can soften a hard moment and open the way to make things right.",
        )
    ],
    "water": [
        (
            "Why can a turtle help in water?",
            "A turtle is built for water, so swimming feels natural and steady. That makes a turtle a good helper when something drifts out of reach.",
        )
    ],
    "reach": [
        (
            "Why can a crane reach high places?",
            "A crane has long legs and a long neck and beak. Those body parts help it reach where a small animal cannot.",
        )
    ],
    "strength": [
        (
            "Why can a goat move heavy things better than a mouse can?",
            "A goat has a bigger body and stronger legs and shoulders. Strength matters when something is stuck and needs a hard push.",
        )
    ],
}
KNOWLEDGE_ORDER = ["asking_help", "honest_words", "apology", "water", "reach", "strength"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for need_id, need in NEEDS.items():
            if not need_feasible(place, need):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_can_help(helper, need):
                    combos.append((place_id, need_id, helper_id))
    return combos


def explain_rejection(place: Place, need: Need, helper: HelperKind) -> str:
    if not need_feasible(place, need):
        return (
            f"(No story: {need.object_label} does not belong in {place.label}. "
            f"That place does not afford this problem.)"
        )
    if not helper_can_help(helper, need):
        return (
            f"(No story: a {helper.label} cannot reasonably solve the problem of {need.object_label}. "
            f"Pick a helper whose body fits the task.)"
        )
    return "(No story: this combination is not reasonable.)"


def explain_repair(rid: str) -> str:
    rep = REPAIRS[rid]
    better = " / ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={rep.sense} < {SENSE_MIN}). Try a clearer repair such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "solved" if can_repair(STYLES[params.style], HELPERS[params.helper], REPAIRS[params.repair], params.delay) else "missed"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    need = f["need_cfg"]
    style = f["style_cfg"]
    repair = f["repair_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old that includes dialogue and the word "awkward". '
        f"The story should be about {seeker.id} needing help with {need.object_label}."
    )
    if outcome == "solved":
        return [
            base,
            f"Tell a gentle animal fable where {seeker.id} first speaks in an awkward, {style.label} way, "
            f"then {repair.qa_line}, and {helper.id} helps.",
            "Write a fable where a confusing conversation becomes clear and kind, and end with a simple moral about speaking plainly.",
        ]
    return [
        base,
        f"Tell a small fable where {seeker.id} hides a need behind awkward dialogue, but the chance for help slips away.",
        "Write a child-facing fable with talking animals, an awkward silence, and a closing moral about asking plainly before it is too late.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    need = f["need_cfg"]
    style = f["style_cfg"]
    repair = f["repair_cfg"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} the {seeker.label}, who needed help, and {helper.id} the {helper.label}, who heard the awkward talk.",
        ),
        (
            f"What problem did {seeker.id} have?",
            f"{seeker.id} wanted {need.object_label}, but {need.problem}. The trouble was physical, so {seeker.pronoun()} needed the right kind of helper.",
        ),
        (
            f"Why did the conversation become awkward?",
            f"{seeker.id} did not ask directly. Instead, {seeker.pronoun()} tried {style.label}, and that made {helper.id} confused instead of ready to help.",
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                f"How did {seeker.id} fix the awkward dialogue?",
                f"{seeker.id} {repair.qa_line}. That clear second try gave {helper.id} a simple job to answer instead of a puzzle to guess at.",
            )
        )
        qa.append(
            (
                f"How was the problem solved?",
                f"{helper.id} used the kind of help that fit the problem, and {need.object_label} became reachable. The ending shows that clear words led to useful action.",
            )
        )
        qa.append(
            (
                "What did the story teach?",
                "The story teaches that pride can tangle your words, but honest speech can untangle them. Asking plainly is brave because it lets kindness find you.",
            )
        )
    else:
        qa.append(
            (
                f"Did {helper.id} help in time?",
                f"No. {seeker.id} tried to repair the moment, but the chance had already thinned away, so {need.object_label} was left where it was. The missed ending came from delay after the confusing talk.",
            )
        )
        qa.append(
            (
                "What did the story teach?",
                "The story teaches that hidden needs are hard for others to carry. If you truly need help, plain words are wiser than awkward pride.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["need_cfg"].tags) | set(f["helper_cfg"].tags)
    tags |= set(f["repair_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} awkward={world.facts.get('awkward')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, N, H) :- place(P), need(N), helper(H), affords(P, N), requires(N, A), has_ability(H, A).
sensible_repair(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
tension(V) :- chosen_style(S), level(S, L), delay(D), V = L + D.
repair_strength(V) :- chosen_repair(R), power(R, P), chosen_helper(H), patience(H, T), V = P + T.

outcome(solved) :- repair_strength(RS), tension(T), RS >= T + 1.
outcome(missed) :- repair_strength(RS), tension(T), RS < T + 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, place in PLACES.items():
        for need in sorted(place.affords):
            lines.append(asp.fact("affords", pid, need))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("requires", nid, need.requirement))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("patience", hid, helper.patience))
        for ability in sorted(helper.abilities):
            lines.append(asp.fact("has_ability", hid, ability))
    for sid, style in STYLES.items():
        lines.append(asp.fact("style", sid))
        lines.append(asp.fact("level", sid, style.level))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_style", params.style),
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_repairs = {r.id for r in sensible_repairs()}
    asp_repairs = set(asp_sensible_repairs())
    if py_repairs == asp_repairs:
        print(f"OK: sensible repairs match ({sorted(py_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(asp_repairs)} python={sorted(py_repairs)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if params.repair not in REPAIRS:
            continue
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: awkward dialogue, a real need, and a plain-spoken repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra pause before the seeker tries to repair the moment")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    if args.place and args.need and args.helper:
        place = PLACES[args.place]
        need = NEEDS[args.need]
        helper = HELPERS[args.helper]
        if not (need_feasible(place, need) and helper_can_help(helper, need)):
            raise StoryError(explain_rejection(place, need, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.need is None or combo[1] == args.need)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, need, helper = rng.choice(sorted(combos))
    style = args.style or rng.choice(sorted(STYLES))
    repair = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    seeker_name, seeker_type = rng.choice(SEEKERS)
    helper_name = rng.choice(["Bram", "Mira", "Corin", "Luma", "Tollo"])
    return StoryParams(
        place=place,
        need=need,
        helper=helper,
        style=style,
        repair=repair,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        helper_name=helper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place '{params.place}'.)")
    if params.need not in NEEDS:
        raise StoryError(f"(Invalid need '{params.need}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper '{params.helper}'.)")
    if params.style not in STYLES:
        raise StoryError(f"(Invalid style '{params.style}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair '{params.repair}'.)")
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    if not need_feasible(PLACES[params.place], NEEDS[params.need]) or not helper_can_help(HELPERS[params.helper], NEEDS[params.need]):
        raise StoryError(explain_rejection(PLACES[params.place], NEEDS[params.need], HELPERS[params.helper]))

    world = tell(
        place=PLACES[params.place],
        need=NEEDS[params.need],
        helper_cfg=HELPERS[params.helper],
        style=STYLES[params.style],
        repair=REPAIRS[params.repair],
        seeker_name=params.seeker_name,
        seeker_type=params.seeker_type,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible_repair/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, need, helper) combos:\n")
        for place, need, helper in combos:
            print(f"  {place:10} {need:15} {helper}")
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
            header = f"### {p.seeker_name}: {p.need} at {p.place} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
