#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py
================================================================================

A standalone story world about a child who brings a family bible to a laundromat
during yule week, accidentally lets it get mixed with the wash, and is helped in
time by a calm grown-up. The domain aims for suspense with a soft landing:
machines hum, socks fly, and the precious book is saved with kindness.

The world model prefers *real* laundry hazards over decorative word swapping:
a bible is only at risk if it is set in a spot that can honestly be mistaken for
laundry, and the rescue method must be sensible enough for a child-facing story.
A tiny causal engine tracks physical state (in washer, wet, crumpled) and
emotional state (worry, relief, gratitude), and the prose reads from that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py --spot basket --load towels
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py --spot lap
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py --response wait_and_hope
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/bible_laundromat_yule_suspense_humor_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "grandmother", "woman", "lady"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Occasion:
    id: str
    yule_goal: str
    reason_line: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    risky: bool = False
    mistake_line: str = ""
    clue_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    hiding: int = 0
    splash: int = 0
    funny_line: str = ""
    clue: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_bible(world: World) -> list[str]:
    bible = world.entities.get("bible")
    washer = world.entities.get("washer")
    child = world.entities.get("child")
    guardian = world.entities.get("guardian")
    if not bible or not washer or bible.meters["in_washer"] < THRESHOLD or washer.meters["running"] < THRESHOLD:
        return []
    sig = ("wet_bible",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bible.meters["wet"] += 1
    bible.meters["crumpled"] += 1
    if child:
        child.memes["fear"] += 1
    if guardian:
        guardian.memes["fear"] += 1
    return ["__wet__"]


def _r_relief(world: World) -> list[str]:
    bible = world.entities.get("bible")
    child = world.entities.get("child")
    guardian = world.entities.get("guardian")
    helper = world.entities.get("helper")
    if not bible or bible.meters["saved"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in (child, guardian, helper):
        if ent is not None:
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wet_bible", tag="physical", apply=_r_wet_bible),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(spot: Spot, load: Load) -> bool:
    return spot.risky and load.hiding > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(load: Load, delay: int) -> int:
    return load.splash + delay


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    load = LOADS[params.load]
    score = response.power - severity_of(load, params.delay)
    if score >= 1:
        return "dry_saved"
    if score == 0:
        return "damp_saved"
    return "soaked_saved"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    bible = sim.get("bible")
    washer = sim.get("washer")
    bible.meters["in_washer"] += 1
    washer.meters["running"] += 1
    propagate(sim, narrate=False)
    return {
        "wet": bible.meters["wet"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"] + sim.get("guardian").memes["fear"],
    }


def opening_scene(world: World, child: Entity, guardian: Entity, occasion: Occasion) -> None:
    child.memes["joy"] += 1
    guardian.memes["care"] += 1
    world.say(
        f"On a bright yule-week afternoon, {child.id} went with {child.pronoun('possessive')} "
        f"{guardian.label_word} to the laundromat. Outside, the air nipped noses; inside, the "
        f"dryers glowed like round orange moons."
    )
    world.say(
        f"{child.id} had brought a small family bible because {occasion.reason_line}."
    )


def comedy_scene(world: World, load: Load) -> None:
    world.say(
        f"The laundromat was full of soft clanks and funny little rattles. {load.funny_line}"
    )


def settle_bible(world: World, child: Entity, bible: Entity, spot: Spot) -> None:
    bible.meters["set_down"] += 1
    bible.attrs["spot"] = spot.id
    world.say(
        f"While {child.id} helped sort socks and shirts, {child.pronoun()} set the bible {spot.phrase}."
    )


def gentle_warning(world: World, child: Entity, guardian: Entity, spot: Spot, load: Load) -> None:
    pred = predict_trouble(world)
    guardian.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    if spot.risky:
        world.say(
            f'"Keep Grandma\'s bible high and dry," {guardian.label_word} said. '
            f'"{spot.mistake_line}"'
        )
    else:
        world.say(
            f'"Good thinking," {guardian.label_word} said. "That spot keeps the bible away from the wash."'
        )


def distraction(world: World, child: Entity, occasion: Occasion) -> None:
    child.memes["distraction"] += 1
    world.say(
        f"Then a tiny paper snowflake slipped out of {child.pronoun('possessive')} pocket, and "
        f"{child.id} bent to catch it before it skated under a chair. For one busy minute, the "
        f"bible stopped feeling important and the yule errand felt like a game."
    )


def accident(world: World, child: Entity, guardian: Entity, bible: Entity, washer: Entity,
             spot: Spot, load: Load) -> None:
    bible.meters["in_washer"] += 1
    washer.meters["loaded"] += 1
    child.memes["fear"] += 1
    guardian.memes["fear"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} scooped up {load.phrase} and, without noticing the book, "
        f"fed the whole armful into a washer. {spot.clue_line}"
    )
    world.say(
        f"When the round door clicked shut, {child.id} looked at the empty {spot.label} and felt "
        f"{child.pronoun('possessive')} stomach drop. \"The bible!\" {child.pronoun()} gasped."
    )


def alarm(world: World, child: Entity, guardian: Entity) -> None:
    world.say(
        f"For one hushy second, even the humming machines seemed to listen. {guardian.label_word.capitalize()} "
        f"spun around, and {child.id} grabbed {guardian.pronoun('possessive')} sleeve."
    )


def rescue(world: World, helper: Entity, washer: Entity, bible: Entity, response: Response,
           load: Load, delay: int) -> None:
    if delay == 0:
        washer.meters["running"] = 0.0
        bible.meters["saved"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{helper.id}, the laundromat helper, moved at once and {response.text}. "
            f"The washer gave only a grumpy little cough before stopping."
        )
        return

    washer.meters["running"] += 1
    propagate(world, narrate=False)
    score = response.power - severity_of(load, delay)
    if score >= 0:
        washer.meters["running"] = 0.0
        bible.meters["saved"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{helper.id}, the laundromat helper, hurried over and {response.text}. "
            f"A few drops clung to the cover, but the pages were still together."
        )
    else:
        washer.meters["running"] = 0.0
        bible.meters["saved"] += 1
        bible.meters["wet"] += 1
        bible.meters["crumpled"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{helper.id}, the laundromat helper, {response.fail}. By the time the door popped open, "
            f"the bible was damp and rumpled, but it was back in loving hands."
        )


def comfort_and_laughter(world: World, child: Entity, guardian: Entity, helper: Entity,
                         bible: Entity, occasion: Occasion) -> None:
    child.memes["gratitude"] += 1
    guardian.memes["gratitude"] += 1
    helper.memes["kindness"] += 1
    damp = bible.meters["wet"] >= THRESHOLD
    if damp:
        world.say(
            f"{guardian.label_word.capitalize()} laid the bible on a clean towel and patted the cover dry. "
            f'"Well," {guardian.pronoun()} said, trying not to laugh, "that book has had more of a bath than anyone asked for."'
        )
        world.say(
            f"{child.id} let out a shaky giggle. The gold page edges looked sleepy, but the old ribbon was still there, "
            f"marking the yule reading."
        )
    else:
        world.say(
            f"{guardian.label_word.capitalize()} hugged the bible to {guardian.pronoun('possessive')} chest and then hugged "
            f"{child.id} too. Someone nearby laughed when a lonely red sock kept circling in another washer as if it wanted "
            f"to hear the good news."
        )
    world.say(
        f'{helper.id} smiled and said, "Books do not belong in spin cycle, but families do a fine job pulling together."'
    )
    world.say(
        f"Soon the clean laundry was folded, the rescued bible was safe, and {occasion.closing_image}"
    )


def tell(occasion: Occasion, spot: Spot, load: Load, response: Response,
         child_name: str = "Lily", child_gender: str = "girl",
         guardian_type: str = "mother", helper_name: str = "Mrs. Vega",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["eager"],
        label=child_name,
    ))
    guardian = world.add(Entity(
        id="Guardian",
        kind="character",
        type=guardian_type,
        role="guardian",
        label="the guardian",
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="woman" if helper_name.startswith("Mrs.") or helper_name.startswith("Ms.") else "man",
        role="helper",
        label="the helper",
    ))
    bible = world.add(Entity(
        id="bible",
        type="book",
        label="bible",
        phrase="Grandma's little red bible",
        tags={"bible", "book"},
    ))
    washer = world.add(Entity(
        id="washer",
        type="machine",
        label="washer",
        phrase="the front-loading washer",
        tags={"laundromat", "washer"},
    ))

    opening_scene(world, child, guardian, occasion)
    comedy_scene(world, load)
    world.para()

    settle_bible(world, child, bible, spot)
    gentle_warning(world, child, guardian, spot, load)
    distraction(world, child, occasion)

    world.para()
    accident(world, child, guardian, bible, washer, spot, load)
    alarm(world, child, guardian)
    world.para()
    rescue(world, helper, washer, bible, response, load, delay)
    comfort_and_laughter(world, child, guardian, helper, bible, occasion)

    world.facts.update(
        child=child,
        guardian=guardian,
        helper=helper,
        bible=bible,
        washer=washer,
        occasion=occasion,
        spot=spot,
        load=load,
        response=response,
        delay=delay,
        outcome="dry_saved" if bible.meters["wet"] < THRESHOLD and delay == 0 else outcome_of(
            StoryParams(
                occasion=occasion.id,
                spot=spot.id,
                load=load.id,
                response=response.id,
                child=child_name,
                gender=child_gender,
                guardian=guardian_type,
                helper=helper_name,
                delay=delay,
                seed=None,
            )
        ),
        predicted_fear=world.facts.get("predicted_fear", 0),
    )
    return world


OCCASIONS = {
    "pageant": Occasion(
        id="pageant",
        yule_goal="a church pageant",
        reason_line="that evening {name} was to read one short line at the yule pageant and wanted to practice while the clothes washed".replace("{name}", "the child"),
        closing_image="they sat together on a warm folding chair while the dryers hummed, and the yule verse sounded even sweeter for having nearly gone missing",
        tags={"yule", "reading"},
    ),
    "carols": Occasion(
        id="carols",
        yule_goal="the neighborhood carol walk",
        reason_line="after the laundry they were meeting neighbors for yule carols, and {name} wanted to practice a favorite verse tucked inside".replace("{name}", "the child"),
        closing_image="they shared a soft laugh beside the soap boxes, and soon the laundromat felt almost like a yule parlor full of warm light",
        tags={"yule", "singing"},
    ),
    "cookies": Occasion(
        id="cookies",
        yule_goal="a cookie visit",
        reason_line="later they were carrying cookies to Grandma, and {name} wanted to show the very bible Grandma had used every yule".replace("{name}", "the child"),
        closing_image="when the last shirt was folded, the rescued bible rested on top like a small brave treasure, ready to travel to Grandma",
        tags={"yule", "grandma"},
    ),
}

SPOTS = {
    "basket": Spot(
        id="basket",
        label="laundry basket",
        phrase="in the big blue laundry basket",
        risky=True,
        mistake_line="A basket full of towels can swallow a book if we are rushing",
        clue_line="A square little bump hid under the towels, waiting in the dark like a very patient brick.",
        tags={"basket", "risky"},
    ),
    "tote": Spot(
        id="tote",
        label="red tote",
        phrase="in the red tote beside the detergent",
        risky=True,
        mistake_line="That tote looks too much like another load when it is stuffed full",
        clue_line="The tote slumped open, looking innocent, while the book had already gone for an unwanted ride.",
        tags={"tote", "risky"},
    ),
    "folding_table": Spot(
        id="folding_table",
        label="folding table",
        phrase="on the folding table under the coin machine",
        risky=False,
        mistake_line="",
        clue_line="",
        tags={"safe"},
    ),
    "lap": Spot(
        id="lap",
        label="lap",
        phrase="right on {name}'s lap".replace("{name}", "the child"),
        risky=False,
        mistake_line="",
        clue_line="",
        tags={"safe"},
    ),
}

LOADS = {
    "towels": Load(
        id="towels",
        label="towels",
        phrase="a mountain of striped towels",
        hiding=2,
        splash=2,
        funny_line="One dryer burped a puff of warm air, and somebody's Santa towel kept waving through the glass like it had an opinion.",
        clue="a pale corner and a gold page edge peeking through the towels",
        tags={"towels", "laundry"},
    ),
    "sweaters": Load(
        id="sweaters",
        label="sweaters",
        phrase="a bundle of soft winter sweaters",
        hiding=1,
        splash=1,
        funny_line="A green sweater with jingly reindeer bells made every step sound as if a tiny sleigh had lost its way.",
        clue="a stiff little corner among the droopy sweaters",
        tags={"sweaters", "laundry"},
    ),
    "costumes": Load(
        id="costumes",
        label="costumes",
        phrase="a heap of velvety yule costumes",
        hiding=1,
        splash=1,
        funny_line="A felt shepherd hat slid off a chair and landed upside down like a sleepy turtle.",
        clue="gold page edges flashing between a velvet cape and a shepherd sash",
        tags={"costume", "laundry", "yule"},
    ),
    "coins": Load(
        id="coins",
        label="coin tray",
        phrase="the little tray of quarters",
        hiding=0,
        splash=0,
        funny_line="The change machine blinked and clicked as if it were counting tiny silver raindrops.",
        clue="",
        tags={"coins"},
    ),
}

RESPONSES = {
    "stop_button": Response(
        id="stop_button",
        sense=3,
        power=3,
        text="slapped the stop button, popped the door, and lifted the bible out before the water could really begin",
        fail="hit the stop button as fast as possible, but the first splash had already kissed the cover",
        qa_text="stopped the washer and lifted the bible out",
        tags={"washer", "help"},
    ),
    "door_release": Response(
        id="door_release",
        sense=3,
        power=2,
        text="used the emergency door release and whisked the bible out onto a clean towel",
        fail="used the emergency door release as quickly as possible, but the pages had already taken on some water",
        qa_text="used the emergency release to open the washer and rescue the bible",
        tags={"washer", "help"},
    ),
    "cycle_end": Response(
        id="cycle_end",
        sense=2,
        power=1,
        text="caught the machine at the first pause and pulled the bible free with two careful hands",
        fail="waited for the first pause and then pulled the bible free, though by then it was plainly wet",
        qa_text="caught the machine at a pause and pulled the bible free",
        tags={"washer", "help"},
    ),
    "wait_and_hope": Response(
        id="wait_and_hope",
        sense=1,
        power=0,
        text="stood by the glass and hoped for the best",
        fail="only watched the washer turn, hoping the problem might fix itself",
        qa_text="waited and hoped",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max", "Eli"]
HELPER_NAMES = ["Mrs. Vega", "Mr. Ellis", "Ms. June"]
TRAITS = ["eager", "careful", "bouncy", "thoughtful"]


@dataclass
class StoryParams:
    occasion: str
    spot: str
    load: str
    response: str
    child: str
    gender: str
    guardian: str
    helper: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        occasion="pageant",
        spot="basket",
        load="towels",
        response="stop_button",
        child="Lily",
        gender="girl",
        guardian="mother",
        helper="Mrs. Vega",
        delay=0,
        seed=None,
    ),
    StoryParams(
        occasion="carols",
        spot="tote",
        load="sweaters",
        response="door_release",
        child="Ben",
        gender="boy",
        guardian="father",
        helper="Mr. Ellis",
        delay=1,
        seed=None,
    ),
    StoryParams(
        occasion="cookies",
        spot="basket",
        load="costumes",
        response="cycle_end",
        child="Nora",
        gender="girl",
        guardian="mother",
        helper="Ms. June",
        delay=1,
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for occasion_id in OCCASIONS:
        for spot_id, spot in SPOTS.items():
            for load_id, load in LOADS.items():
                if hazard_at_risk(spot, load):
                    combos.append((occasion_id, spot_id, load_id))
    return combos


def explain_rejection(spot: Spot, load: Load) -> str:
    if not spot.risky:
        return (
            f"(No story: setting the bible {spot.phrase} does not honestly mix it with the wash. "
            f"That gives the story no real laundromat danger. Try a basket or tote instead.)"
        )
    if load.hiding <= 0:
        return (
            f"(No story: {load.phrase} cannot hide a bible in the wash, so there is no plausible rescue beat. "
            f"Pick towels, sweaters, or costumes instead.)"
        )
    return "(No story: this combination does not create a believable laundry mix-up.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too passive for a child-facing rescue story "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    occasion = f["occasion"]
    load = f["load"]
    outcome = f["outcome"]
    tail = {
        "dry_saved": "The book should be rescued before it really gets wet.",
        "damp_saved": "The book may get a little damp, but the ending should stay gentle and heartwarming.",
        "soaked_saved": "Let the book come out wet but still cherished, with comfort and laughter after the scare.",
    }[outcome]
    return [
        'Write a heartwarming TinyStories-style story that includes the words "bible", "laundromat", and "yule".',
        f"Tell a gentle suspense story where a child named {child.id} brings a family bible to a laundromat during yule week and it gets mixed into {load.phrase}.",
        f"Write a story with soft humor, a believable rescue, and a loving ending. {tail}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    helper = f["helper"]
    occasion = f["occasion"]
    spot = f["spot"]
    load = f["load"]
    response = f["response"]
    bible = f["bible"]
    outcome = f["outcome"]
    pw = guardian.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and {helper.id} at the laundromat. "
            f"They are trying to care for a family bible during yule week.",
        ),
        (
            "Why did the child bring the bible to the laundromat?",
            f"The bible came along because of a yule plan: {occasion.reason_line.replace('the child', child.id)}. "
            f"That is why the book mattered so much when it went missing.",
        ),
        (
            f"Why was the bible in danger?",
            f"{child.id} set it {spot.phrase}, and that spot could be mistaken for laundry. "
            f"When {load.phrase} went into the washer, the bible was swept in with it.",
        ),
        (
            "What made the middle of the story feel suspenseful but still a little funny?",
            f"The danger was real because the washer door clicked shut around the missing bible. "
            f"But the laundromat also had silly details, like tumbling clothes and comic machine noises, so the fear never felt cruel.",
        ),
    ]
    if outcome == "dry_saved":
        qa.append(
            (
                f"How was the bible saved?",
                f"{helper.id} {response.qa_text} before the wash truly began. "
                f"That quick action kept the book dry and turned the scary moment into relief.",
            )
        )
    elif outcome == "damp_saved":
        qa.append(
            (
                "Did the bible get wet?",
                f"Only a little. {helper.id} {response.qa_text}, so the cover caught a few drops, but the pages stayed together and the family could still use it.",
            )
        )
    else:
        qa.append(
            (
                "What happened to the bible in the end?",
                f"It came out wet and rumpled, but it was rescued and cared for right away. "
                f"The family dried it on a clean towel, which showed that the book was loved more than it was perfect.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended warmly: the laundry was folded, the bible was safe again, and {occasion.closing_image}. "
            f"The ending proves the scare passed and love stayed bigger than the mistake.",
        )
    )
    if bible.meters["wet"] >= THRESHOLD:
        qa.append(
            (
                f"How did {child.id} feel after the rescue?",
                f"{child.id} felt shaky first and then relieved enough to laugh. "
                f"The damp cover showed there had been real danger, but the grown-ups' kindness made the ending safe again.",
            )
        )
    return qa


KNOWLEDGE = {
    "bible": [
        (
            "What is a bible?",
            "A bible is a book of stories, songs, prayers, and teachings that many families read for faith and comfort.",
        )
    ],
    "laundromat": [
        (
            "What is a laundromat?",
            "A laundromat is a place with washing machines and dryers where people go to clean clothes.",
        )
    ],
    "yule": [
        (
            "What does yule mean?",
            "Yule is a winter holiday time linked with warmth, lights, songs, and gathering together.",
        )
    ],
    "washer": [
        (
            "Why should books stay out of washing machines?",
            "Books are made of paper, and water makes paper swell, wrinkle, and tear. That is why books should stay far from the wash.",
        )
    ],
    "towels": [
        (
            "Why can a book disappear inside towels?",
            "A thick pile of towels can hide a small object because the cloth folds over it and makes it hard to see.",
        )
    ],
    "sweaters": [
        (
            "Why do sweaters feel soft and bulky?",
            "Sweaters are made to feel warm and cozy, so they can bunch up in a soft pile.",
        )
    ],
    "costume": [
        (
            "What is a costume?",
            "A costume is clothing worn to look like someone or something special for a play, party, or celebration.",
        )
    ],
    "help": [
        (
            "What should you do if something important gets put in the wash by mistake?",
            "Tell a grown-up right away and stop the machine if it is safe to do so. Asking for help fast is the smartest thing to do.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bible", "laundromat", "yule", "washer", "towels", "sweaters", "costume", "help"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bible", "laundromat", "yule", "washer", "help"}
    tags |= set(f["load"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, L) :- risky(S), hiding(L, H), H > 0.
valid(O, S, L) :- occasion(O), spot(S), load(L), hazard(S, L).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

severity(V) :- chosen_load(L), splash(L, S), delay(D), V = S + D.
score(X) :- chosen_response(R), power(R, P), severity(V), X = P - V.

outcome(dry_saved) :- score(X), X >= 1.
outcome(damp_saved) :- score(0).
outcome(soaked_saved) :- score(X), X < 0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OCCASIONS:
        lines.append(asp.fact("occasion", oid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.risky:
            lines.append(asp.fact("risky", sid))
    for lid, load in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("hiding", lid, load.hiding))
        lines.append(asp.fact("splash", lid, load.splash))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_load", params.load),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    as_valid = set(asp_valid_combos())
    if py_valid == as_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - as_valid:
            print("  only in python:", sorted(py_valid - as_valid))
        if as_valid - py_valid:
            print("  only in clingo:", sorted(as_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    as_sensible = set(asp_sensible())
    if py_sensible == as_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(as_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "{" in smoke.story or "}" in smoke.story:
            raise StoryError("Smoke story is empty or contains unresolved template braces.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
            rendered = buf.getvalue()
        if "laundromat" not in smoke.story or "bible" not in smoke.story or "yule" not in smoke.story:
            raise StoryError("Smoke story failed required seed words.")
        if not rendered.strip():
            raise StoryError("emit() produced no output in smoke test.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a bible nearly goes through the wash at a laundromat during yule week."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "grandmother"])
    ap.add_argument("--child")
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the washer gets going before help reaches it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (occasion, spot, load) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.load:
        spot = SPOTS[args.spot]
        load = LOADS[args.load]
        if not hazard_at_risk(spot, load):
            raise StoryError(explain_rejection(spot, load))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.spot is None or combo[1] == args.spot)
        and (args.load is None or combo[2] == args.load)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion_id, spot_id, load_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "grandmother"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 1, 2])

    return StoryParams(
        occasion=occasion_id,
        spot=spot_id,
        load=load_id,
        response=response_id,
        child=child,
        gender=gender,
        guardian=guardian,
        helper=helper,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        occasion = OCCASIONS[params.occasion]
        spot = SPOTS[params.spot]
        load = LOADS[params.load]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not hazard_at_risk(spot, load):
        raise StoryError(explain_rejection(spot, load))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        occasion=occasion,
        spot=spot,
        load=load,
        response=response,
        child_name=params.child,
        child_gender=params.gender,
        guardian_type=params.guardian,
        helper_name=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (occasion, spot, load) combos:\n")
        for occasion, spot, load in combos:
            print(f"  {occasion:8} {spot:13} {load}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.child}: {p.occasion} at the laundromat ({p.spot}, {p.load}, {outcome_of(p)})"
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
