#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py
============================================================================

A standalone storyworld for a small fable domain built from the seed words
"ghastly", "net", and "noodle", with Quest and Foreshadowing as core story
instruments.

The world models a little animal setting out on a quest to carry one long noodle
to someone waiting at the far side of a watery place. Along the way, an old net
stands in the path. A wiser companion notices signs and warns what will happen
if the hero hurries. Sometimes the warning is enough. Sometimes the net snags
the hero and the noodle, and the chosen method either saves the quest or turns
it into a humbler lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py
    python storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py --all
    python storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py --qa
    python storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py --trace
    python storyworlds/worlds/gpt-5.4/ghastly_net_noodle_quest_foreshadowing_fable.py --verify
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
CAUTIOUS_TRAITS = {"careful", "patient", "wise", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    label: str
    path_word: str
    water: str
    destination: str
    ending_image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    item: str
    item_phrase: str
    recipient: str
    need: str
    thanks: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    kind: str
    look: str
    foreshadow: str
    snag_text: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    works_on: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    success: str = ""
    fail: str = ""
    qa_text: str = ""
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_snag_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    guide = world.entities.get("guide")
    if hero is None:
        return []
    if hero.meters["tangled"] < THRESHOLD:
        return []
    sig = ("snag_fear", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    if guide is not None:
        guide.memes["concern"] += 1
    return []


def _r_lost_quest(world: World) -> list[str]:
    noodle = world.entities.get("noodle")
    if noodle is None:
        return []
    if noodle.meters["lost"] < THRESHOLD:
        return []
    sig = ("lost_quest", noodle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["sadness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="snag_fear", tag="emotional", apply=_r_snag_fear),
    Rule(name="lost_quest", tag="quest", apply=_r_lost_quest),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_in_setting(setting: Setting, hazard: Hazard) -> bool:
    return hazard.id in setting.affords


def response_works(response: Response, hazard: Hazard) -> bool:
    return hazard.kind in response.works_on


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hazard_id in sorted(setting.affords):
            hazard = HAZARDS[hazard_id]
            for response in sensible_responses():
                if response_works(response, hazard):
                    combos.append((setting_id, hazard_id, response.id))
    return combos


def would_avert(guide_age: int, hero_age: int, trait: str) -> bool:
    return guide_age > hero_age and trait in CAUTIOUS_TRAITS


def is_recovered(response: Response, hazard: Hazard) -> bool:
    return response_works(response, hazard) and response.power >= hazard.severity


def predict_snag(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    noodle = sim.get("noodle")
    hero.meters["tangled"] += 1
    noodle.meters["snagged"] += 1
    if hazard.severity >= 3:
        noodle.meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "tangled": hero.meters["tangled"] >= THRESHOLD,
        "lost": noodle.meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    world.say(
        f"In the soft hour before sunrise, {hero.id} the {hero.type} set out on a quest. "
        f"{hero.pronoun('subject').capitalize()} carried {quest.item_phrase} for {quest.recipient}, "
        f"who {quest.need}."
    )
    world.say(
        f"Beside {hero.pronoun('object')} walked {guide.id} the {guide.type}, "
        f"a friend known for {guide.traits[0]} steps and a listening heart."
    )


def announce_path(world: World, setting: Setting) -> None:
    world.say(
        f"The road led through {setting.label}, where {setting.water} lay still and "
        f"{setting.path_word} wound toward {setting.destination}."
    )


def foreshadow(world: World, hero: Entity, guide: Entity, hazard: Hazard) -> None:
    pred = predict_snag(world, hazard)
    guide.memes["caution"] += 1
    world.facts["predicted_tangled"] = pred["tangled"]
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f"Soon they came to {hazard.look}. It looked so ghastly in the gray light "
        f"that even the reeds seemed to whisper around it."
    )
    world.say(
        f'{guide.id} paused and said, "{hazard.foreshadow} A quick foot may laugh first, '
        f'but a careless foot often cries last."'
    )


def tempt(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"But {hero.id} thought of {quest.recipient} waiting at the far side with an empty bowl. "
        f'"If I hurry, this noodle will still be warm," {hero.pronoun("subject")} said.'
    )


def heed_warning(world: World, hero: Entity, guide: Entity, response: Response, quest: Quest) -> None:
    hero.memes["humility"] += 1
    hero.memes["wisdom"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"{hero.id} looked again at the old net and heard the scrape of its knots in the wind. "
        f"The sound was enough to cool {hero.pronoun('possessive')} hurry."
    )
    world.say(
        f"Together the two travelers {response.success}. Soon they were past the danger, "
        f"and {quest.item_phrase} still rested safe in {hero.pronoun('possessive')} paws."
    )


def rush_into_net(world: World, hero: Entity, guide: Entity, hazard: Hazard) -> None:
    noodle = world.get("noodle")
    hero.meters["tangled"] += 1
    noodle.meters["snagged"] += 1
    if hazard.severity >= 3:
        noodle.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} darted ahead before {guide.id} could catch {hero.pronoun('object')}. "
        f"{hazard.snag_text}"
    )


def rescue_success(world: World, hero: Entity, guide: Entity, response: Response, quest: Quest) -> None:
    noodle = world.get("noodle")
    hero.meters["tangled"] = 0.0
    noodle.meters["snagged"] = 0.0
    noodle.meters["lost"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"{guide.id} did not scold. {guide.pronoun('subject').capitalize()} {response.success}, "
        f"and the trapped noodle slipped free without breaking."
    )
    world.say(
        f"{hero.id} stood still at last and felt how much stronger calm hands were than hasty ones."
    )


def rescue_fail(world: World, hero: Entity, guide: Entity, response: Response, quest: Quest) -> None:
    noodle = world.get("noodle")
    hero.meters["tangled"] = 0.0
    noodle.meters["snagged"] += 1
    noodle.meters["lost"] = 1.0
    propagate(world, narrate=False)
    hero.memes["wisdom"] += 1
    world.say(
        f"{guide.id} tried to help and {response.fail}. The poor noodle fell with a plop into the dark water "
        f"and drifted away beneath the reeds."
    )
    world.say(
        f"{hero.id} was safe, but the quest could not be finished in the proud way {hero.pronoun('subject')} had imagined."
    )


def arrival_success(world: World, hero: Entity, guide: Entity, setting: Setting, quest: Quest) -> None:
    hero.meters["arrived"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"When they reached {setting.destination}, {quest.recipient} smiled at the sight of the long noodle. "
        f'"{quest.thanks}"'
    )
    world.say(
        f"They shared the meal beside {setting.ending_image}, and {hero.id} noticed that the world looked gentler "
        f"when one walked through it with care."
    )


def arrival_humble(world: World, hero: Entity, guide: Entity, setting: Setting, quest: Quest) -> None:
    hero.meters["arrived"] += 1
    hero.memes["joy"] += 0.5
    world.say(
        f"When they reached {setting.destination}, {quest.recipient} saw the empty paws and asked no sharp question."
    )
    world.say(
        f'{guide.id} told the truth, and {quest.recipient} only nodded. "Then we shall share plain broth today and keep the lesson for tomorrow."'
    )
    world.say(
        f"They ate a simple meal beside {setting.ending_image}, and even without the noodle, the place felt fuller for the honesty brought there."
    )


def close_moral(world: World, quest: Quest) -> None:
    world.say(quest.moral)


def tell(
    setting: Setting,
    quest: Quest,
    hazard: Hazard,
    response: Response,
    hero_name: str = "Pip",
    hero_type: str = "mouse",
    guide_name: str = "Moss",
    guide_type: str = "turtle",
    trait: str = "wise",
    hero_age: int = 4,
    guide_age: int = 6,
    hero_gender: str = "boy",
    guide_gender: str = "girl",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=["eager"],
            attrs={"gender": hero_gender},
            tags={"quest"},
        )
    )
    guide = world.add(
        Entity(
            id=guide_name,
            kind="character",
            type=guide_type,
            role="guide",
            traits=[trait],
            attrs={"gender": guide_gender},
            tags={"guide"},
        )
    )
    noodle = world.add(
        Entity(
            id="noodle",
            kind="thing",
            type="food",
            label="noodle",
            phrase=quest.item_phrase,
            tags={"noodle"},
        )
    )

    world.para()
    introduce(world, hero, guide, quest)
    announce_path(world, setting)

    world.para()
    foreshadow(world, hero, guide, hazard)
    tempt(world, hero, quest)

    averted = would_avert(guide_age=guide_age, hero_age=hero_age, trait=trait)
    contained = False

    world.para()
    if averted:
        heed_warning(world, hero, guide, response, quest)
        contained = True
    else:
        rush_into_net(world, hero, guide, hazard)
        if is_recovered(response, hazard):
            rescue_success(world, hero, guide, response, quest)
            contained = True
        else:
            rescue_fail(world, hero, guide, response, quest)
            contained = False

    world.para()
    if contained:
        arrival_success(world, hero, guide, setting, quest)
    else:
        arrival_humble(world, hero, guide, setting, quest)
    close_moral(world, quest)

    outcome = "averted" if averted else ("recovered" if contained else "spilled")
    world.facts.update(
        hero=hero,
        guide=guide,
        noodle=noodle,
        setting=setting,
        quest=quest,
        hazard=hazard,
        response=response,
        outcome=outcome,
        delivered=contained,
        guide_age=guide_age,
        hero_age=hero_age,
        trait=trait,
        tangled=hero.meters["tangled"] >= THRESHOLD or outcome != "averted",
        noodle_lost=noodle.meters["lost"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "reed_marsh": Setting(
        id="reed_marsh",
        label="the reed marsh",
        path_word="a thin mud path",
        water="green water under leaning reeds",
        destination="the Willow Stone",
        ending_image="the Willow Stone where dragonflies stitched blue thread through the air",
        affords={"fishing_net", "rope_net"},
    ),
    "misty_bank": Setting(
        id="misty_bank",
        label="the misty riverbank",
        path_word="a pebbled bank",
        water="slow water under a shawl of mist",
        destination="the old ferry post",
        ending_image="the old ferry post while the mist thinned into silver ribbons",
        affords={"fishing_net", "thorn_net"},
    ),
    "moon_pond": Setting(
        id="moon_pond",
        label="the pond of moon reeds",
        path_word="a stepping trail of flat stones",
        water="black water that held the sky like a mirror",
        destination="the heron's lantern stump",
        ending_image="the lantern stump with moonlight trembling on the pond",
        affords={"rope_net", "root_net"},
    ),
}

QUESTS = {
    "supper": Quest(
        id="supper",
        item="noodle",
        item_phrase="one long noodle curled in a little leaf bowl",
        recipient="Grandmother Crane",
        need="was waiting for breakfast after a weak night",
        thanks="You have brought both breakfast and good sense across the water.",
        moral="So the marsh taught them this: on any quest, a patient step carries more than a proud leap.",
        tags={"food", "care"},
    ),
    "offering": Quest(
        id="offering",
        item="noodle",
        item_phrase="a festival noodle tied with a parsley ribbon",
        recipient="the Shrine Tortoise",
        need="kept the morning feast and could not leave the shrine",
        thanks="A gift arrives sweetest when it arrives with care.",
        moral="And that is why the old creatures say: a careful messenger honors the gift before the gift is given.",
        tags={"festival", "gift"},
    ),
    "comfort": Quest(
        id="comfort",
        item="noodle",
        item_phrase="a warm noodle floating in a covered bowl",
        recipient="Little Wren",
        need="had lost heart after a stormy night",
        thanks="Warm food helps, but a wiser heart helps too.",
        moral="Thus the little travelers learned that haste may start a journey, but patience finishes it.",
        tags={"comfort", "food"},
    ),
}

HAZARDS = {
    "fishing_net": Hazard(
        id="fishing_net",
        label="old fishing net",
        kind="hanging",
        look="an old fishing net draped between two bent reeds",
        foreshadow="See how that net lifts and falls? It is waiting for whatever rushes beneath it.",
        snag_text="The old fishing net dropped around his shoulders, and its wet knots caught the leaf bowl too.",
        severity=2,
        tags={"net", "water"},
    ),
    "rope_net": Hazard(
        id="rope_net",
        label="rope net",
        kind="hanging",
        look="a rope net stretched over the narrowest part of the path",
        foreshadow="A rope net is like a silent question: if you answer too fast, it ties you to your mistake.",
        snag_text="The rope net bounced, twisted, and wrapped around his feet while the noodle swung wildly above the puddles.",
        severity=2,
        tags={"net", "rope"},
    ),
    "root_net": Hazard(
        id="root_net",
        label="root net",
        kind="ground",
        look="a mesh of roots spread across the stones like a ghastly brown net",
        foreshadow="Roots that lie quiet by day still love to catch hasty toes.",
        snag_text="His foot slipped into the root net, and the bowl tipped so sharply that the noodle nearly slid away.",
        severity=1,
        tags={"net", "roots"},
    ),
    "thorn_net": Hazard(
        id="thorn_net",
        label="thorn net",
        kind="snagging",
        look="a thorny net of brambles hanging low over the bank",
        foreshadow="Thorns never shout before they bite. They wait for pride to do the shouting for them.",
        snag_text="The thorn net snatched the bowl, tore the leaf rim, and flung the noodle toward the river with a splash.",
        severity=3,
        tags={"net", "thorns"},
    ),
}

RESPONSES = {
    "willow_pole": Response(
        id="willow_pole",
        label="willow pole",
        works_on={"hanging"},
        sense=3,
        power=2,
        success="used a long willow pole to lift the net high and guide the way through",
        fail="poked upward with a willow pole, but the snare clung too tightly and only shook the noodle loose",
        qa_text="used a long willow pole to lift the net safely",
        tags={"pole", "net"},
    ),
    "shell_knife": Response(
        id="shell_knife",
        label="shell knife",
        works_on={"hanging", "ground", "snagging"},
        sense=3,
        power=3,
        success="took out a small shell knife and cut a neat, safe opening through the knots",
        fail="cut at the snare with a shell knife, but too late to keep the noodle from falling away",
        qa_text="cut a safe opening with a small shell knife",
        tags={"knife", "net"},
    ),
    "patient_paws": Response(
        id="patient_paws",
        label="patient paws",
        works_on={"ground"},
        sense=2,
        power=1,
        success="knelt down and patiently unwove the roots one loop at a time",
        fail="pulled at the tangle with patient paws, but the snare was too cruel and the noodle slipped into the water",
        qa_text="patiently unwove the tangle one loop at a time",
        tags={"careful", "net"},
    ),
    "hard_tug": Response(
        id="hard_tug",
        label="hard tug",
        works_on={"hanging", "ground", "snagging"},
        sense=1,
        power=1,
        success="gave the snare one hard yank",
        fail="gave the snare one hard yank, which only made the bowl jerk and spill",
        qa_text="gave the snare one hard yank",
        tags={"rough", "net"},
    ),
}

NAME_PAIRS = [
    ("Pip", "mouse", "boy", "Moss", "turtle", "girl"),
    ("Nia", "otter", "girl", "Brindle", "fox", "boy"),
    ("Tavi", "sparrow", "boy", "Fern", "hare", "girl"),
    ("Mira", "vole", "girl", "Rowan", "badger", "boy"),
]

TRAITS = ["careful", "patient", "wise", "steady", "curious", "quick"]
AGES = [3, 4, 5, 6, 7]


@dataclass
class StoryParams:
    setting: str
    quest: str
    hazard: str
    response: str
    hero_name: str
    hero_type: str
    hero_gender: str
    guide_name: str
    guide_type: str
    guide_gender: str
    trait: str
    hero_age: int
    guide_age: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "quest": [(
        "What is a quest?",
        "A quest is a journey with a purpose. Someone sets out because something important needs to be done."
    )],
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story gives a small hint about something that will happen later. It helps the reader feel the danger before it arrives."
    )],
    "net": [(
        "What is a net?",
        "A net is a woven mesh of rope, string, or thread. It can catch things because it has many little holes and knots."
    )],
    "noodle": [(
        "What is a noodle?",
        "A noodle is a long strip of cooked dough. It is soft, bendy, and often eaten in soup or a bowl."
    )],
    "patience": [(
        "Why can patience help on a hard job?",
        "Patience helps because slow, careful hands notice problems before they get bigger. When you stop rushing, you make fewer mistakes."
    )],
    "thorns": [(
        "Why are thorns tricky?",
        "Thorns are sharp points on some plants. They can snag cloth, fur, or skin when you push past too fast."
    )],
    "roots": [(
        "Why can roots trip someone?",
        "Roots can stick up across the ground and catch a foot. If you do not look where you step, you can stumble."
    )],
    "pole": [(
        "What can a pole be used for?",
        "A long pole can lift, reach, or move something from a safer distance. It helps when your hands should not go too close."
    )],
    "knife": [(
        "What is a knife for?",
        "A knife is a cutting tool. In stories like this one, a wise grown creature uses it carefully to cut what is tangled."
    )],
}
KNOWLEDGE_ORDER = ["quest", "foreshadowing", "net", "noodle", "patience", "thorns", "roots", "pole", "knife"]


CURATED = [
    StoryParams(
        setting="reed_marsh",
        quest="supper",
        hazard="fishing_net",
        response="willow_pole",
        hero_name="Pip",
        hero_type="mouse",
        hero_gender="boy",
        guide_name="Moss",
        guide_type="turtle",
        guide_gender="girl",
        trait="wise",
        hero_age=4,
        guide_age=6,
    ),
    StoryParams(
        setting="moon_pond",
        quest="comfort",
        hazard="root_net",
        response="patient_paws",
        hero_name="Mira",
        hero_type="vole",
        hero_gender="girl",
        guide_name="Rowan",
        guide_type="badger",
        guide_gender="boy",
        trait="careful",
        hero_age=5,
        guide_age=7,
    ),
    StoryParams(
        setting="misty_bank",
        quest="offering",
        hazard="thorn_net",
        response="shell_knife",
        hero_name="Tavi",
        hero_type="sparrow",
        hero_gender="boy",
        guide_name="Fern",
        guide_type="hare",
        guide_gender="girl",
        trait="curious",
        hero_age=6,
        guide_age=5,
    ),
    StoryParams(
        setting="misty_bank",
        quest="supper",
        hazard="thorn_net",
        response="patient_paws",
        hero_name="Nia",
        hero_type="otter",
        hero_gender="girl",
        guide_name="Brindle",
        guide_type="fox",
        guide_gender="boy",
        trait="quick",
        hero_age=6,
        guide_age=5,
    ),
    StoryParams(
        setting="moon_pond",
        quest="offering",
        hazard="rope_net",
        response="willow_pole",
        hero_name="Pip",
        hero_type="mouse",
        hero_gender="boy",
        guide_name="Moss",
        guide_type="turtle",
        guide_gender="girl",
        trait="steady",
        hero_age=3,
        guide_age=7,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    quest = f["quest"]
    setting = f["setting"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    base = (
        f'Write a child-friendly fable about a quest through {setting.label} that includes the words '
        f'"ghastly", "net", and "noodle", and uses foreshadowing before the trouble begins.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a fable where {guide.id} notices a warning sign, speaks carefully, and {hero.id} listens before the {hazard.label} can catch anyone.",
            f"Write a gentle quest story in which {hero.id} carries a noodle to {quest.recipient}, heeds foreshadowing, and reaches the end wiser than before.",
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell a quest fable where {hero.id} rushes, the {hazard.label} catches the noodle, and {guide.id} saves the day with a calm, sensible method.",
            f"Write a fable with a scary middle turn and a peaceful ending image, showing that patience rescues both the traveler and the quest.",
        ]
    return [
        base,
        f"Tell a cautionary fable where {hero.id} ignores the warning, loses the noodle to the {hazard.label}, and learns humility on the way to {quest.recipient}.",
        f"Write a sad-but-gentle quest story that uses foreshadowing honestly and ends with a moral about haste and patience.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    quest = f["quest"]
    setting = f["setting"]
    hazard = f["hazard"]
    response = f["response"]
    outcome = f["outcome"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {guide.id} the {guide.type}, and the noodle they carried on a quest. "
            f"The quest mattered because {quest.recipient} was waiting at {setting.destination}."
        ),
        (
            "What was the quest?",
            f"{hero.id} was carrying {quest.item_phrase} to {quest.recipient}. "
            f"The journey mattered because {quest.recipient} {quest.need}."
        ),
        (
            "How did the story use foreshadowing?",
            f"{guide.id} warned that the {hazard.label} would catch anyone who rushed. "
            f"That warning came before the trouble, so it foreshadowed what the net was about to do."
        ),
    ]
    if outcome == "averted":
        items.append((
            f"Why did {hero.id} slow down?",
            f"{hero.id} heard the scrape of the old net and remembered {guide.id}'s warning. "
            f"That small fearful sound turned pride into caution before any harm happened."
        ))
        items.append((
            f"How did they get past the net?",
            f"{guide.id} {response.qa_text}. "
            f"Because they moved carefully, the noodle stayed safe and the quest stayed whole."
        ))
    elif outcome == "recovered":
        items.append((
            f"What happened when {hero.id} hurried?",
            f"The {hazard.label} tangled {hero.id} and caught the noodle too. "
            f"The trouble happened because {hero.pronoun('subject')} rushed after hearing a clear warning."
        ))
        items.append((
            f"How was the quest saved?",
            f"{guide.id} {response.qa_text}. "
            f"That calm choice freed both traveler and noodle, so they could still reach {quest.recipient}."
        ))
    else:
        items.append((
            f"Was the noodle delivered?",
            f"No. The noodle was lost after the net snagged it and the rescue was not strong enough. "
            f"{hero.id} still reached {quest.recipient}, but only with the truth and the lesson."
        ))
        items.append((
            "How did the story end?",
            f"It ended with a simple shared meal instead of the planned noodle gift. "
            f"The ending proves what changed because pride gave way to honesty and patience."
        ))
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"quest", "foreshadowing", "net", "noodle", "patience"}
    hazard = f["hazard"]
    response = f["response"]
    if "thorns" in hazard.tags:
        tags.add("thorns")
    if "roots" in hazard.tags:
        tags.add("roots")
    if response.id == "willow_pole":
        tags.add("pole")
    if response.id == "shell_knife":
        tags.add("knife")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
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


def explain_rejection(setting_id: str, hazard_id: str, response_id: str) -> str:
    setting = SETTINGS[setting_id]
    hazard = HAZARDS[hazard_id]
    response = RESPONSES[response_id]
    if hazard.id not in setting.affords:
        return (
            f"(No story: {hazard.label} does not belong in {setting.label}. "
            f"Choose a hazard that naturally fits that path.)"
        )
    if response.sense < SENSE_MIN:
        return (
            f"(No story: '{response.label}' is too rough to be the world's sensible fix "
            f"(sense={response.sense} < {SENSE_MIN}). Choose a calmer method.)"
        )
    if not response_works(response, hazard):
        return (
            f"(No story: {response.label} does not reasonably solve a {hazard.label}. "
            f"The method must match the kind of net in the path.)"
        )
    return "(No story: that combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(guide_age=params.guide_age, hero_age=params.hero_age, trait=params.trait):
        return "averted"
    response = RESPONSES[params.response]
    hazard = HAZARDS[params.hazard]
    return "recovered" if is_recovered(response, hazard) else "spilled"


ASP_RULES = r"""
valid(S, H, R) :- setting(S), hazard(H), response(R),
                  affords(S, H), sensible(R), works_on(R, K), kind(H, K).

cautious(T) :- trait(T), cautious_trait(T).
guide_older :- guide_age(GA), hero_age(HA), GA > HA.
averted :- guide_older, cautious(T), trait(T).

recovered :- chosen_response(R), chosen_hazard(H),
             works_on(R, K), kind(H, K),
             power(R, P), severity(H, S), P >= S.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(spilled) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("kind", hid, hazard.kind))
        lines.append(asp.fact("severity", hid, hazard.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for kind in sorted(response.works_on):
            lines.append(asp.fact("works_on", rid, kind))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.")
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
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("hero_age", params.hero_age),
        asp.fact("guide_age", params.guide_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    cases = list(CURATED)
    for seed in range(100):
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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable quest with a ghastly net and a noodle."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.response:
        if (args.setting, args.hazard, args.response) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.hazard, args.response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        setting_id = args.setting or next(iter(SETTINGS))
        hazard_id = args.hazard or next(iter(HAZARDS))
        raise StoryError(explain_rejection(setting_id, hazard_id, args.response))
    if args.setting and args.hazard and args.hazard not in SETTINGS[args.setting].affords:
        response_id = args.response or next(r.id for r in sensible_responses())
        raise StoryError(explain_rejection(args.setting, args.hazard, response_id))
    if args.hazard and args.response and not response_works(RESPONSES[args.response], HAZARDS[args.hazard]):
        setting_id = args.setting or next(s for s, setting in SETTINGS.items() if args.hazard in setting.affords)
        raise StoryError(explain_rejection(setting_id, args.hazard, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hazard_id, response_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    hero_name, hero_type, hero_gender, guide_name, guide_type, guide_gender = rng.choice(NAME_PAIRS)
    trait = rng.choice(TRAITS)
    hero_age, guide_age = rng.sample(AGES, 2)
    return StoryParams(
        setting=setting_id,
        quest=quest_id,
        hazard=hazard_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_gender=hero_gender,
        guide_name=guide_name,
        guide_type=guide_type,
        guide_gender=guide_gender,
        trait=trait,
        hero_age=hero_age,
        guide_age=guide_age,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        (params.setting, SETTINGS),
        (params.quest, QUESTS),
        (params.hazard, HAZARDS),
        (params.response, RESPONSES),
    ):
        if key not in table:
            raise StoryError("(No story: one of the requested options is unknown.)")

    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]

    if (params.setting, params.hazard, params.response) not in valid_combos():
        raise StoryError(explain_rejection(params.setting, params.hazard, params.response))

    world = tell(
        setting=setting,
        quest=quest,
        hazard=hazard,
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        trait=params.trait,
        hero_age=params.hero_age,
        guide_age=params.guide_age,
        hero_gender=params.hero_gender,
        guide_gender=params.guide_gender,
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
        print(f"{len(combos)} compatible (setting, hazard, response) combos:\n")
        for setting_id, hazard_id, response_id in combos:
            print(f"  {setting_id:12} {hazard_id:12} {response_id}")
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
            header = (
                f"### {p.hero_name} and {p.guide_name}: {p.quest} through {p.setting} "
                f"({p.hazard}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
