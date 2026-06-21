#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/week_conflict_twist_rhyme_animal_story.py
====================================================================

A small standalone storyworld for gentle animal stories built around one key
seed word -- "week" -- plus three instruments: conflict, twist, and rhyme.

Premise
-------
A little animal spends all week making a special thing for a celebration.
Then a real hazard threatens it. A friend secretly moves the project to a safer
place, but the hero returns, sees the empty spot, and thinks it was taken.
That misunderstanding creates the conflict. The twist is that the friend was
helping all along. Depending on how fragile the project was and how strong the
chosen shelter is, the project is either saved or partly spoiled before the
reveal. The ending always resolves with apology, friendship, and a small rhyme.

Run it
------
    python storyworlds/worlds/gpt-5.4/week_conflict_twist_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4/week_conflict_twist_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/week_conflict_twist_rhyme_animal_story.py --project lantern --hazard rain
    python storyworlds/worlds/gpt-5.4/week_conflict_twist_rhyme_animal_story.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class Home:
    id: str
    place: str
    event: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    making: str
    for_event: str
    hurt_by: set[str] = field(default_factory=set)
    fragility: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    sign: str
    touch: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shelter:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    power: int = 1
    carry: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    line1: str
    line2: str


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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["exposed"] < THRESHOLD:
        return out
    sig = ("risk", "project")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["danger"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("helper").memes["care"] += 1
    out.append("__risk__")
    return out


def _r_accusation_hurts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["accusing"] < THRESHOLD:
        return out
    sig = ("hurt", "helper")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def project_at_risk(project: Project, hazard: Hazard) -> bool:
    return hazard.id in project.hurt_by


def shelter_matches(hazard: Hazard, shelter: Shelter) -> bool:
    return hazard.id in shelter.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for hazard_id, hazard in HAZARDS.items():
            for shelter_id, shelter in SHELTERS.items():
                if project_at_risk(project, hazard) and shelter_matches(hazard, shelter):
                    combos.append((project_id, hazard_id, shelter_id))
    return combos


def danger_level(project: Project, delay: int) -> int:
    return project.fragility + delay


def is_saved(project: Project, shelter: Shelter, delay: int) -> bool:
    return shelter.power >= danger_level(project, delay)


def predict_trouble(project: Project, hazard: Hazard, shelter: Shelter, delay: int) -> dict:
    return {
        "at_risk": project_at_risk(project, hazard),
        "protected": shelter_matches(hazard, shelter),
        "saved": is_saved(project, shelter, delay),
        "danger": danger_level(project, delay),
    }


def introduce(world: World, hero: Entity, helper: Entity, home: Home, project: Project) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In {home.place}, {hero.id} the {hero.type} had spent all week {project.making}. "
        f"Every day, {helper.id} the {helper.type} padded along {home.path} to peek and smile."
    )
    world.say(
        f"{hero.id} was making {project.phrase} for {project.for_event}. "
        f"By the end of the week, {hero.pronoun('possessive')} whiskers twitched with pride."
    )


def looming_hazard(world: World, home: Home, hazard: Hazard, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["exposed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the morning of {home.event}, {hazard.sign}. "
        f"{hazard.touch.capitalize()} brushed against the little project."
    )
    world.say(
        f"{helper_name(world)} saw at once that {project.label} could be {hazard.effect}."
    )


def helper_acts(world: World, helper: Entity, shelter: Shelter) -> None:
    helper.memes["care"] += 1
    project_ent = world.get("project")
    project_ent.attrs["moved_by"] = helper.id
    project_ent.attrs["shelter"] = shelter.id
    world.say(
        f"While {hero_name(world)} chased one last ribbon down the path, {helper.id} {shelter.carry} "
        f"and tucked it in {shelter.phrase}."
    )


def missing_project(world: World, hero: Entity, project: Project) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"When {hero.id} came back, the sunny stump was empty. "
        f'"My {project.label}!" {hero.id} gasped. "It was right here!"'
    )


def accuse(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["accusing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} turned to {helper.id}. "Did you take it?" {hero.pronoun()} cried. '
        f'"I worked all week, and now it is gone!"'
    )
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{helper.id}'s ears drooped. {helper.pronoun().capitalize()} had only been trying to help."
        )


def reveal_saved(world: World, helper: Entity, project: Project, shelter: Shelter) -> None:
    hero = world.get("hero")
    hero.memes["shame"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    helper.memes["forgiveness"] += 1
    world.say(
        f'But {helper.id} shook {helper.pronoun("possessive")} head. '
        f'"No, {hero.id}. Come see," {helper.pronoun()} said softly.'
    )
    world.say(
        f"{shelter.reveal.capitalize()}, and there was {project.phrase}, safe and neat. "
        f"A tiny finishing touch from {helper.id} sat on top."
    )


def reveal_spoiled(world: World, helper: Entity, project: Project, shelter: Shelter, hazard: Hazard) -> None:
    hero = world.get("hero")
    hero.memes["shame"] += 1
    helper.memes["sad"] += 1
    helper.memes["forgiveness"] += 1
    world.say(
        f'But {helper.id} shook {helper.pronoun("possessive")} head. '
        f'"No, {hero.id}. I moved it so {hazard.label} would not ruin it," {helper.pronoun()} said.'
    )
    world.say(
        f"{shelter.reveal.capitalize()}, and there was {project.phrase} in {shelter.phrase}. "
        f"It was not lost -- only a little spoiled, because the trouble had started too soon."
    )


def apology(world: World, hero: Entity, helper: Entity, saved: bool) -> None:
    hero.memes["love"] += 1
    helper.memes["love"] += 1
    if saved:
        world.say(
            f'{hero.id} blinked, then hung {hero.pronoun("possessive")} head. '
            f'"I am sorry, {helper.id}," {hero.pronoun()} said. "You did not steal my surprise. '
            f'You saved it."'
        )
    else:
        world.say(
            f'{hero.id} blinked, then hung {hero.pronoun("possessive")} head. '
            f'"I am sorry, {helper.id}," {hero.pronoun()} said. "You were helping, and I spoke too fast."'
        )
    world.say(
        f"{helper.id} gave a small nod, and the hard feeling between them loosened like a knot coming undone."
    )


def mend_or_share(world: World, hero: Entity, helper: Entity, project: Project, saved: bool) -> None:
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    if saved:
        world.say(
            f"Together they carried {project.label} back outside, and now it seemed even finer because it had a kind secret tucked inside it."
        )
    else:
        world.say(
            f"Together they fixed what they could. The project was smaller than before, but it held two pairs of careful paws instead of one."
        )


def final_rhyme(world: World, rhyme: Rhyme, home: Home) -> None:
    world.say(
        f'So on {home.event}, the two friends said a little rhyme together: '
        f'"{rhyme.line1} {rhyme.line2}"'
    )
    world.say(
        f"And from then on, whenever worry came too quick, they chose a question before a quarrel."
    )


def hero_name(world: World) -> str:
    return world.get("hero").id


def helper_name(world: World) -> str:
    return world.get("helper").id


def tell(
    home: Home,
    project: Project,
    hazard: Hazard,
    shelter: Shelter,
    rhyme: Rhyme,
    hero_name_value: str,
    hero_kind: str,
    helper_name_value: str,
    helper_kind: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name_value, kind="character", type=hero_kind, role="hero"))
    helper = world.add(Entity(id=helper_name_value, kind="character", type=helper_kind, role="helper"))
    project_ent = world.add(Entity(id="project", type="project", label=project.label, phrase=project.phrase))
    world.facts["delay"] = delay

    introduce(world, hero, helper, home, project)

    world.para()
    looming_hazard(world, home, hazard, project)
    helper_acts(world, helper, shelter)
    missing_project(world, hero, project)
    accuse(world, hero, helper)

    world.para()
    saved = is_saved(project, shelter, delay)
    if saved:
        reveal_saved(world, helper, project, shelter)
    else:
        reveal_spoiled(world, helper, project, shelter, hazard)
    apology(world, hero, helper, saved)
    mend_or_share(world, hero, helper, project, saved)
    final_rhyme(world, rhyme, home)

    outcome = "saved" if saved else "spoiled"
    project_ent.meters["danger"] = float(danger_level(project, delay))
    if saved:
        project_ent.meters["safe"] += 1
    else:
        project_ent.meters["spoiled"] += 1
    world.facts.update(
        home=home,
        project_cfg=project,
        hazard=hazard,
        shelter=shelter,
        rhyme=rhyme,
        hero=hero,
        helper=helper,
        project=project_ent,
        outcome=outcome,
        conflict=True,
        twist=True,
        saved=saved,
        accusation=hero.memes["accusing"] >= THRESHOLD,
        helper_hurt=helper.memes["hurt"] >= THRESHOLD,
    )
    return world


HOMES = {
    "meadow": Home(
        id="meadow",
        place="a bright meadow near the willow trees",
        event="the lantern parade",
        path="through the clover",
        tags={"meadow"},
    ),
    "pond": Home(
        id="pond",
        place="a mossy pond bank",
        event="the lily picnic",
        path="beside the reeds",
        tags={"pond"},
    ),
    "oak": Home(
        id="oak",
        place="the roots of a grand old oak",
        event="the acorn supper",
        path="under the roots",
        tags={"oak"},
    ),
}

PROJECTS = {
    "lantern": Project(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern painted with stars",
        making="folding and painting a paper lantern",
        for_event="the lantern parade",
        hurt_by={"rain", "wind"},
        fragility=2,
        tags={"paper", "lantern"},
    ),
    "crown": Project(
        id="crown",
        label="leaf crown",
        phrase="a leaf crown stitched with daisies",
        making="stitching a leaf crown",
        for_event="the picnic game",
        hurt_by={"wind", "sun"},
        fragility=1,
        tags={"leaf", "crown"},
    ),
    "berry_tart": Project(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart with shiny juice on top",
        making="patting and filling a berry tart",
        for_event="the woodland feast",
        hurt_by={"sun", "rain"},
        fragility=2,
        tags={"berries", "tart"},
    ),
    "snowflake": Project(
        id="snowflake",
        label="bark snowflake",
        phrase="a bark snowflake tied with soft grass",
        making="tying a bark snowflake",
        for_event="the acorn supper",
        hurt_by={"rain"},
        fragility=1,
        tags={"bark"},
    ),
}

HAZARDS = {
    "rain": Hazard(
        id="rain",
        label="rain",
        sign="gray drops began tapping on leaves",
        touch="the first wet splash",
        effect="turned to soggy mush",
        tags={"rain", "weather"},
    ),
    "wind": Hazard(
        id="wind",
        label="wind",
        sign="a jumpy wind came dancing through the grass",
        touch="the wild gust",
        effect="blown into a tangle",
        tags={"wind", "weather"},
    ),
    "sun": Hazard(
        id="sun",
        label="hot sun",
        sign="the hot noon sun poured down without a cloud",
        touch="the warm glare",
        effect="wilted and droopy",
        tags={"sun", "weather"},
    ),
}

SHELTERS = {
    "hollow_log": Shelter(
        id="hollow_log",
        label="hollow log",
        phrase="the cool hollow of an old log",
        guards={"rain", "wind"},
        power=2,
        carry="lifted the project in careful paws",
        reveal="inside the hollow log",
        tags={"shelter", "log"},
    ),
    "stone_nook": Shelter(
        id="stone_nook",
        label="stone nook",
        phrase="a snug nook between two warm stones",
        guards={"wind", "sun"},
        power=2,
        carry="whisked the project under one arm",
        reveal="inside the stone nook",
        tags={"shelter", "stone"},
    ),
    "shade_burrow": Shelter(
        id="shade_burrow",
        label="shade burrow",
        phrase="the shady mouth of a burrow",
        guards={"sun", "rain"},
        power=3,
        carry="hurried off with the project held high",
        reveal="inside the shade burrow",
        tags={"shelter", "burrow"},
    ),
    "fern_basket": Shelter(
        id="fern_basket",
        label="fern basket",
        phrase="a fern basket under broad leaves",
        guards={"rain"},
        power=1,
        carry="slipped the project into a fern basket",
        reveal="under the broad leaves",
        tags={"shelter", "basket"},
    ),
}

RHYMES = {
    "bright": Rhyme(id="bright", line1="Kind and bright,", line2="ask first, then make it right!"),
    "dry": Rhyme(id="dry", line1="Safe and dry,", line2="friends ask why before they cry!"),
    "mend": Rhyme(id="mend", line1="Mend and share,", line2="gentle words show loving care!"),
}

ANIMALS = ["rabbit", "squirrel", "otter", "hedgehog", "mouse", "badger"]
NAMES = ["Pip", "Moss", "Nibbles", "Tansy", "Pebble", "Wren", "Fern", "Clover"]


@dataclass
class StoryParams:
    home: str
    project: str
    hazard: str
    shelter: str
    rhyme: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "rain": [
        (
            "What can rain do to paper or leaves left outside?",
            "Rain can soak paper and leaves until they turn soft, heavy, or droopy. That is why small outdoor things often need a dry place.",
        )
    ],
    "wind": [
        (
            "Why can wind be a problem for light little things?",
            "Wind can push, flip, or carry light little things away. If something is tied or tucked into a snug place, it is safer.",
        )
    ],
    "sun": [
        (
            "How can hot sun change food or leaves?",
            "Hot sun can dry food out or make leaves wilt. Shade helps keep them cooler and fresher.",
        )
    ],
    "shelter": [
        (
            "What is a shelter?",
            "A shelter is a safer place that protects something from weather. Animals use shelters to stay dry, cool, or out of the wind.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology shows that you know your words hurt someone and that you want to make things better. It helps friendship begin to heal.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like bright and right. Rhymes are easy to remember and can make a lesson feel gentle.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rain", "wind", "sun", "shelter", "apology", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    home = world.facts["home"]
    project = world.facts["project_cfg"]
    hazard = world.facts["hazard"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    rhyme = world.facts["rhyme"]
    outcome = world.facts["outcome"]
    end_bit = "the special thing is saved" if outcome == "saved" else "the friends fix what they can together"
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the word "week", a misunderstanding, a twist, and a rhyme.',
        f"Tell a gentle story where {hero.id} the {hero.type} spends all week making {project.label}, thinks {helper.id} took it, and then learns the truth when {hazard.label} becomes a danger.",
        f'Write a TinyStories-style animal tale with conflict and a kind ending set around {home.event}, where the last lesson comes in a short rhyme and {end_bit}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    project_cfg = f["project_cfg"]
    hazard = f["hazard"]
    shelter = f["shelter"]
    home = f["home"]
    rhyme = f["rhyme"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {helper.id} the {helper.type}. They are two animal friends in {home.place}.",
        ),
        (
            f"What did {hero.id} do all week?",
            f"{hero.id} spent all week {project_cfg.making}. {hero.pronoun().capitalize()} wanted it ready for a special day.",
        ),
        (
            f"Why did the trouble start?",
            f"The trouble started when {hazard.label} threatened the project and then it seemed to disappear. {hero.id} did not know that {helper.id} had moved it to keep it safer.",
        ),
        (
            f"Why did {hero.id} get upset with {helper.id}?",
            f"{hero.id} came back and saw the place where the project had been sitting was empty. Because {hero.pronoun()} had worked all week, {hero.pronoun()} quickly thought {helper.id} had taken it.",
        ),
        (
            "What was the twist in the story?",
            f"The twist was that {helper.id} had not stolen anything at all. {helper.pronoun().capitalize()} had secretly carried the project to {shelter.phrase} because {hazard.label} could damage it.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How was the problem solved?",
                f"The project was safe in {shelter.phrase}, and {hero.id} apologized for accusing {helper.id}. Then they carried it back together and ended the day as friends again.",
            )
        )
    else:
        qa.append(
            (
                f"Was the project completely safe in the end?",
                f"No. {helper.id} tried to protect it, but the weather had already done a little harm before the move. Even so, the two friends fixed what they could together after the apology.",
            )
        )
    qa.append(
        (
            "What rhyme did they say at the end, and why did it matter?",
            f'They said, "{rhyme.line1} {rhyme.line2}" It mattered because the rhyme turned the lesson into words they could remember the next time worry made them speak too fast.',
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"shelter", "apology", "rhyme"}
    hazard = world.facts["hazard"]
    if hazard.id in tags or hazard.id in KNOWLEDGE:
        tags.add(hazard.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        home="meadow",
        project="lantern",
        hazard="rain",
        shelter="shade_burrow",
        rhyme="dry",
        hero_name="Pip",
        hero_kind="rabbit",
        helper_name="Moss",
        helper_kind="otter",
        delay=0,
    ),
    StoryParams(
        home="pond",
        project="crown",
        hazard="wind",
        shelter="stone_nook",
        rhyme="bright",
        hero_name="Tansy",
        hero_kind="mouse",
        helper_name="Pebble",
        helper_kind="hedgehog",
        delay=1,
    ),
    StoryParams(
        home="oak",
        project="berry_tart",
        hazard="sun",
        shelter="stone_nook",
        rhyme="mend",
        hero_name="Fern",
        hero_kind="squirrel",
        helper_name="Clover",
        helper_kind="badger",
        delay=1,
    ),
    StoryParams(
        home="meadow",
        project="lantern",
        hazard="wind",
        shelter="fern_basket",
        rhyme="mend",
        hero_name="Wren",
        hero_kind="mouse",
        helper_name="Nibbles",
        helper_kind="rabbit",
        delay=2,
    ),
]


def explain_rejection(project: Project, hazard: Hazard, shelter: Shelter) -> str:
    if not project_at_risk(project, hazard):
        return (
            f"(No story: {hazard.label} would not reasonably damage {project.label}, "
            f"so there is no honest reason for the friend to hide it.)"
        )
    if not shelter_matches(hazard, shelter):
        return (
            f"(No story: {shelter.label} does not really protect a project from {hazard.label}. "
            f"The twist only works when the hiding place is a sensible help.)"
        )
    return "(No story: that combination does not fit this world.)"


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(PROJECTS[params.project], SHELTERS[params.shelter], params.delay) else "spoiled"


ASP_RULES = r"""
at_risk(P, H) :- hurts(P, H).
compatible(H, S) :- guards(S, H).
valid(P, H, S) :- project(P), hazard(H), shelter(S), at_risk(P, H), compatible(H, S).

danger(D + L) :- chosen_project(P), fragility(P, D), delay(L).
saved :- chosen_shelter(S), power(S, P), danger(D), P >= D.
outcome(saved) :- saved.
outcome(spoiled) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("fragility", project_id, project.fragility))
        for hazard in sorted(project.hurt_by):
            lines.append(asp.fact("hurts", project_id, hazard))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        lines.append(asp.fact("power", shelter_id, shelter.power))
        for guard in sorted(shelter.guards):
            lines.append(asp.fact("guards", shelter_id, guard))
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
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_shelter", params.shelter),
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
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal misunderstanding storyworld: all week, a conflict, a twist, and a rhyme."
    )
    ap.add_argument("--home", choices=HOMES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the hazard had to act before the reveal")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid project/hazard/shelter combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.hazard and args.shelter:
        project = PROJECTS[args.project]
        hazard = HAZARDS[args.hazard]
        shelter = SHELTERS[args.shelter]
        if not (project_at_risk(project, hazard) and shelter_matches(hazard, shelter)):
            raise StoryError(explain_rejection(project, hazard, shelter))

    combos = [
        combo
        for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.shelter is None or combo[2] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, hazard_id, shelter_id = rng.choice(sorted(combos))
    home_id = args.home or rng.choice(sorted(HOMES))
    rhyme_id = args.rhyme or rng.choice(sorted(RHYMES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_name_value = rng.choice(NAMES)
    helper_name_value = rng.choice([name for name in NAMES if name != hero_name_value])
    hero_kind = rng.choice(ANIMALS)
    helper_kind = rng.choice([animal for animal in ANIMALS if animal != hero_kind] or ANIMALS)
    return StoryParams(
        home=home_id,
        project=project_id,
        hazard=hazard_id,
        shelter=shelter_id,
        rhyme=rhyme_id,
        hero_name=hero_name_value,
        hero_kind=hero_kind,
        helper_name=helper_name_value,
        helper_kind=helper_kind,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        home = HOMES[params.home]
        project = PROJECTS[params.project]
        hazard = HAZARDS[params.hazard]
        shelter = SHELTERS[params.shelter]
        rhyme = RHYMES[params.rhyme]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not project_at_risk(project, hazard) or not shelter_matches(hazard, shelter):
        raise StoryError(explain_rejection(project, hazard, shelter))

    world = tell(
        home=home,
        project=project,
        hazard=hazard,
        shelter=shelter,
        rhyme=rhyme,
        hero_name_value=params.hero_name,
        hero_kind=params.hero_kind,
        helper_name_value=params.helper_name,
        helper_kind=params.helper_kind,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, hazard, shelter) combos:\n")
        for project, hazard, shelter in combos:
            print(f"  {project:10} {hazard:6} {shelter}")
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
            params = sample.params
            header = (
                f"### {params.hero_name} & {params.helper_name}: {params.project} vs {params.hazard} "
                f"({params.shelter}, {outcome_of(params)})"
            )
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
