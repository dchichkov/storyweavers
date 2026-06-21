#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/indicator_trim_gerund_research_teamwork_cautionary_rhyming.py
========================================================================================

A standalone story world about two children making a wind indicator for a small
science project. The core caution is simple: a child should not climb a wobbly
perch alone to hang the project up high. The happy ending comes from teamwork
and asking for the right kind of help.

The seed words are included in-story:
- indicator
- trim-gerund
- research

The style aims for a gentle rhyming-story feel: concrete, child-facing, and
musical without becoming a rigid poem.
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    high_spot: str
    breeze: str
    height_need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Indicator:
    id: str
    label: str
    phrase: str
    make_text: str
    motion_text: str
    repair_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    wobble: int
    height: int
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "partner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    if perch is None or perch.meters["in_use"] < THRESHOLD or perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("project").meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_tear(world: World) -> list[str]:
    out: list[str] = []
    project = world.entities.get("project")
    if project is None or project.meters["risk"] < THRESHOLD:
        return out
    perch = world.entities.get("perch")
    if perch is None:
        return out
    if perch.meters["danger"] < THRESHOLD:
        return out
    sig = ("tear", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["torn"] += 1
    for kid in world.kids():
        kid.memes["sadness"] += 1
    out.append("__tear__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tear", tag="physical", apply=_r_tear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__wobble__":
                world.say("The perch gave a tiny wiggle and a worrying sway.")
            elif bit == "__tear__":
                world.say("One paper tail ripped with a sad little fray.")
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hang_severity(setting: Setting, perch: Perch) -> int:
    return setting.height_need + perch.wobble


def is_contained(response: Response, setting: Setting, perch: Perch) -> bool:
    return response.power >= hang_severity(setting, perch)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def valid_combo(setting: Setting, indicator: Indicator, perch: Perch) -> bool:
    _ = indicator
    return perch.height < setting.height_need


def explain_rejection(setting: Setting, indicator: Indicator, perch: Perch) -> str:
    _ = indicator
    return (
        f"(No story: {perch.phrase} is already tall enough for {setting.high_spot}, "
        f"so the children would not need the risky extra reach that creates the cautionary turn. "
        f"Pick a lower perch or a higher place.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_wobble(world: World, setting: Setting, perch: Perch) -> dict:
    sim = world.copy()
    project = sim.get("project")
    perch_ent = sim.get("perch")
    perch_ent.meters["in_use"] += 1
    perch_ent.meters["wobble"] += float(perch.wobble)
    if hang_severity(setting, perch) >= 3:
        perch_ent.meters["danger"] += 1
    project.meters["too_high"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("project").meters["risk"],
        "torn": sim.get("project").meters["torn"] >= THRESHOLD,
    }


def setup_story(world: World, a: Entity, b: Entity, parent: Entity,
                setting: Setting, indicator: Indicator) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} had a small school job to do that day, "
        f"with paper, string, and tape spread out in a bright little array."
    )
    world.say(
        f"They were making {indicator.phrase} for a bit of wind research, "
        f"to watch where the breeze liked to flutter and play."
    )
    world.say(
        f"On their folder were three funny words: indicator, trim-gerund, research. "
        f'"That middle one is a typo," laughed {b.id}. "It still gets to stay."'
    )
    world.say(
        f"Soon {indicator.make_text}, and even {parent.label_word} smiled at the clever display."
    )
    world.facts["seed_words"] = ["indicator", "trim-gerund", "research"]


def need_height(world: World, a: Entity, b: Entity, setting: Setting, indicator: Indicator) -> None:
    world.say(
        f"But to test the wind, they had to hang it on {setting.high_spot}, "
        f"where {setting.breeze} could tug it and turn it away."
    )
    world.say(
        f'{a.id} stretched up on tiptoe. "{setting.high_spot.capitalize()} is too high," '
        f'{a.pronoun()} said. "{indicator.label.capitalize()} needs a breezy place to sway."'
    )


def tempt(world: World, a: Entity, perch: Perch) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted {perch.phrase} nearby and grinned. '
        f'"I can climb that and hang it right now," {a.pronoun()} said. '
        f'"Quick as a blink, easy as play."'
    )


def warn(world: World, b: Entity, a: Entity, perch: Perch, setting: Setting, parent: Entity) -> None:
    pred = predict_wobble(world, setting, perch)
    b.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_torn"] = pred["torn"]
    tail = " It could wobble and make the paper tails tear away." if pred["torn"] else ""
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} hugged the project close and would not look away."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"Please don\'t climb {perch.label} alone," {b.pronoun()} said. '
        f'"It looks tippy, and {parent.label_word} would want a safer way."{tail}{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f"{a.id} looked at the paper tails, then down at the floor. "
        f"The brave-fast idea did not seem brave anymore."
    )
    world.say(
        f'"You are right," {a.pronoun()} said. "Let\'s ask {parent.label_word} first '
        f"and do this as a team, not a dare from before."'
    )


def defy(world: World, a: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I will be quick," {a.id} said, and climbed onto {perch.phrase}. '
        f"The room went hush-hush, still as a shore."
    )


def wobble_event(world: World, a: Entity, b: Entity, perch: Perch, setting: Setting) -> None:
    perch_ent = world.get("perch")
    project = world.get("project")
    perch_ent.meters["in_use"] += 1
    perch_ent.meters["wobble"] += float(perch.wobble)
    if hang_severity(setting, perch) >= 3:
        perch_ent.meters["danger"] += 1
    project.meters["too_high"] += 1
    propagate(world, narrate=True)
    if project.meters["torn"] >= THRESHOLD:
        world.say(
            f'"Oh!" cried {b.id}, as {indicator_name(world)} dipped low and one bright tail tore.'
        )
    else:
        world.say(
            f"{a.id}'s knees shook, and {perch.label} clicked on the floor with a nervous knock and a skittering score."
        )


def call_for_help(world: World, b: Entity, parent: Entity) -> None:
    b.memes["care"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}!" called {b.id}. "Please come help us before it wobbles more!"'
    )


def repair_and_rescue(world: World, parent: Entity, response: Response, indicator: Indicator) -> None:
    project = world.get("project")
    project.meters["risk"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came at once and {response.text}."
    )
    if project.meters["torn"] >= THRESHOLD:
        project.meters["torn"] = 0.0
        world.say(
            f"Then {parent.pronoun()} {indicator.repair_text}, smoothing the paper flat once more."
        )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and spoke in a calm little way. '
        f'"Good research needs careful hands. When something is high or wobbly, '
        f"we do not climb alone just because we are in a hurry to score."'
    )
    world.say(
        f'"We ask, we steady, we help each other," whispered {b.id}. '
        f'"That is what teamwork is for."'
    )
    world.say(
        f'"And that is what makes a safer day," said {a.id}, nodding by the door.'
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting, indicator: Indicator) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f"Soon {indicator.label} was hanging on {setting.high_spot} at last, "
        f"and {setting.breeze} made it twirl and pour."
    )
    world.say(
        f"{a.id} wrote the wind marks down while {b.id} watched the tails curl round and soar."
    )
    world.say(
        f"They finished their research side by side, and the little {indicator.label} spun safely evermore."
    )


def indicator_name(world: World) -> str:
    return world.facts["indicator"].label


def tell(setting: Setting, indicator: Indicator, perch: Perch, response: Response,
         instigator: str = "Nia", instigator_gender: str = "girl",
         partner: str = "Ben", partner_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         instigator_age: int = 6, partner_age: int = 4,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["eager"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=partner,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    project = world.add(Entity(
        id="project",
        type="project",
        label=indicator.label,
        phrase=indicator.phrase,
        tags=set(indicator.tags),
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        phrase=perch.phrase,
        tags=set(perch.tags),
    ))
    world.add(Entity(id="place", type="place", label=setting.place, phrase=setting.place))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    setup_story(world, a, b, parent, setting, indicator)
    need_height(world, a, b, setting, indicator)

    world.para()
    tempt(world, a, perch)
    warn(world, b, a, perch, setting, parent)

    averted = would_avert(relation, instigator_age, partner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        repair_and_rescue(world, parent, response, indicator)
        world.para()
        lesson(world, parent, a, b)
        world.para()
        ending(world, a, b, setting, indicator)
    else:
        defy(world, a, perch)
        world.para()
        wobble_event(world, a, b, perch, setting)
        call_for_help(world, b, parent)
        contained = is_contained(response, setting, perch)
        world.para()
        if contained:
            repair_and_rescue(world, parent, response, indicator)
            world.para()
            lesson(world, parent, a, b)
            world.para()
            ending(world, a, b, setting, indicator)
        else:
            world.say(
                f"{parent.label_word.capitalize()} {response.fail}, but the project was still too high and too shaky for that first try."
            )
            world.say(
                f"So everyone climbed down, moved the wobbling {perch.label} away, and started over with slower hands and careful eyes nearby."
            )
            world.para()
            lesson(world, parent, a, b)
            world.para()
            repair_and_rescue(world, parent, RESPONSES["adult_ladder"], indicator)
            ending(world, a, b, setting, indicator)
    outcome = "averted" if averted else ("contained" if is_contained(response, setting, perch) else "reset")
    world.facts.update(
        setting=setting,
        indicator=indicator,
        perch_cfg=perch,
        response=response,
        instigator=a,
        partner=b,
        parent=parent,
        outcome=outcome,
        relation=relation,
        severity=hang_severity(setting, perch),
        torn_before_fix=project.meters["torn"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    indicator: str
    perch: str
    response: str
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    instigator_age: int = 6
    partner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        high_spot="the bean-pole hook",
        breeze="the garden breeze",
        height_need=3,
        tags={"garden", "wind"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        high_spot="the porch beam",
        breeze="the porch breeze",
        height_need=3,
        tags={"porch", "wind"},
    ),
    "fence": Setting(
        id="fence",
        place="the backyard",
        high_spot="the tall fence nail",
        breeze="the backyard breeze",
        height_need=2,
        tags={"yard", "wind"},
    ),
}

INDICATORS = {
    "windsock": Indicator(
        id="windsock",
        label="windsock",
        phrase="a bright paper windsock",
        make_text="they trimmed paper streamers, tied string in a ring, and made a bright indicator that loved to sway",
        motion_text="streamers fluttered east and west",
        repair_text="pressed the ripped streamer smooth and taped on a fresh blue tail",
        tags={"indicator", "wind", "paper"},
    ),
    "pinwheel": Indicator(
        id="pinwheel",
        label="pinwheel",
        phrase="a shiny pinwheel indicator",
        make_text="they folded silver paper and fixed a little spinner that flashed in the day",
        motion_text="the wheel blinked and spun",
        repair_text="straightened one bent petal and pinned the spinner tight again",
        tags={"indicator", "wind", "paper"},
    ),
    "ribbon_vane": Indicator(
        id="ribbon_vane",
        label="ribbon vane",
        phrase="a ribbon vane indicator",
        make_text="they tied long ribbons to a stick and made a soft little indicator for the air to obey",
        motion_text="the ribbons streamed in one bright line",
        repair_text="knotted on a new ribbon and tied the loose end neat again",
        tags={"indicator", "wind", "ribbon"},
    ),
}

PERCHES = {
    "chair": Perch(
        id="chair",
        label="the kitchen chair",
        phrase="the kitchen chair",
        wobble=2,
        height=1,
        tags={"chair", "wobble"},
    ),
    "stool": Perch(
        id="stool",
        label="the little step stool",
        phrase="the little step stool",
        wobble=1,
        height=1,
        tags={"stool", "step"},
    ),
    "boxes": Perch(
        id="boxes",
        label="the stacked boxes",
        phrase="the stacked boxes",
        wobble=3,
        height=1,
        tags={"boxes", "wobble"},
    ),
}

RESPONSES = {
    "adult_ladder": Response(
        id="adult_ladder",
        sense=3,
        power=5,
        text="brought a sturdy ladder, held it firm, and helped them lift the project up the right way",
        fail="reached up from the floor and tried to snag the string with one hand",
        qa_text="used a sturdy ladder and held it firm while helping hang the indicator",
        tags={"ladder", "teamwork"},
    ),
    "team_hold": Response(
        id="team_hold",
        sense=3,
        power=3,
        text="had one child hold the base while the grown-up steadied the project and guided the string onto the hook",
        fail="had one child hold the base while reaching up, but it still was not enough height to finish safely",
        qa_text="worked as a team, with one person steadying the base and another guiding the string onto the hook",
        tags={"teamwork", "steady"},
    ),
    "long_pole": Response(
        id="long_pole",
        sense=2,
        power=2,
        text="used a long garden pole to lift the string loop while everyone stood safely on the ground",
        fail="tried a long pole from the floor, but the loop slipped away each time",
        qa_text="used a long pole from the ground to lift the loop into place",
        tags={"tool", "steady"},
    ),
    "solo_reach": Response(
        id="solo_reach",
        sense=1,
        power=1,
        text="let the child stretch alone and trusted the wobble to stop on its own",
        fail="kept trying alone, even while the perch wiggled",
        qa_text="kept trying alone",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Mina", "Ava", "Zoe", "Tara", "Maya", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Owen", "Max", "Eli", "Theo", "Sam", "Finn"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, indicator in INDICATORS.items():
            for pid, perch in PERCHES.items():
                if valid_combo(setting, indicator, perch):
                    combos.append((sid, iid, pid))
    return combos


KNOWLEDGE = {
    "indicator": [
        (
            "What is an indicator?",
            "An indicator is something that shows you a change or gives you a clue. A wind indicator shows which way the air is moving.",
        )
    ],
    "research": [
        (
            "What is research?",
            "Research means looking closely, testing, and learning from what you find. It helps you answer a question in a careful way.",
        )
    ],
    "wind": [
        (
            "How can you tell which way the wind is blowing?",
            "You can watch a windsock, ribbons, leaves, or a pinwheel. They move in the breeze and give you a clue about the wind.",
        )
    ],
    "ladder": [
        (
            "Why is a sturdy ladder safer than climbing a wobbly chair?",
            "A sturdy ladder is made for reaching high places and staying steady. A chair can tip or slide when someone climbs on it.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people helping one another to do a job well. One person can watch, one can steady, and together they can stay safer.",
        )
    ],
    "paper": [
        (
            "Why can paper projects tear easily?",
            "Paper bends and rips more easily than wood or metal. If it gets tugged or shaken, the edges can tear.",
        )
    ],
}
KNOWLEDGE_ORDER = ["indicator", "research", "wind", "ladder", "teamwork", "paper"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    setting = f["setting"]
    indicator = f["indicator"]
    perch = f["perch_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words '
        f'"indicator," "trim-gerund," and "research," and is about teamwork and caution.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {a.id} wants to climb {perch.label}, but {b.id} warns {a.pronoun('object')} and they ask for help instead.",
            f"Write a rhyming science story set in {setting.place} where children use teamwork to hang a {indicator.label} safely without any accident.",
        ]
    return [
        base,
        f"Tell a cautionary rhyming story set in {setting.place} where {a.id} tries to hang a {indicator.label} from {perch.label}, something wobbles, and a grown-up helps them finish safely.",
        f"Write a child-facing teamwork story where a risky quick idea turns into a careful shared plan for a wind-research project.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    parent = f["parent"]
    setting = f["setting"]
    indicator = f["indicator"]
    perch = f["perch_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, working on a wind-research project together. {parent.label_word.capitalize()} comes to help when the job gets too high and wobbly.",
        ),
        (
            "What were the children making?",
            f"They were making {indicator.phrase} for research about the wind. The indicator would show what the breeze was doing once it hung up high.",
        ),
        (
            "Why did they need to put it up high?",
            f"They wanted to hang it on {setting.high_spot}, where the breeze could catch it. A higher place would let the indicator move clearly and show the wind better.",
        ),
        (
            f"Why did {b.id} warn {a.id} not to climb {perch.label} alone?",
            f"{b.id} thought {perch.label} looked wobbly and unsafe. The project was also high enough that a shaky climb could make the indicator tear or make someone slip.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} listened and stopped before climbing. That changed the story from a risky quick try into a teamwork plan with help from {parent.label_word}.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the climbing started?",
                f"The perch wobbled, and the moment turned scary. That wobble showed why the warning mattered and why they needed a safer method.",
            )
        )
    qa.append(
        (
            f"How did {parent.label_word} help fix the problem?",
            f"{parent.label_word.capitalize()} {response.qa_text}. The grown-up help turned the job into a steadier teamwork task instead of a risky solo reach.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The children finished their research side by side, and the {indicator.label} moved safely in the breeze. The ending proves they learned to slow down, ask for help, and work together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"indicator", "research", "wind", "teamwork"}
    tags |= set(f["indicator"].tags)
    tags |= set(f["response"].tags)
    if f["perch_cfg"].wobble >= 2:
        tags.add("ladder")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        indicator="windsock",
        perch="chair",
        response="adult_ladder",
        instigator="Nia",
        instigator_gender="girl",
        partner="Ben",
        partner_gender="boy",
        parent="mother",
        trait="careful",
        instigator_age=5,
        partner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        setting="porch",
        indicator="pinwheel",
        perch="stool",
        response="team_hold",
        instigator="Leo",
        instigator_gender="boy",
        partner="Maya",
        partner_gender="girl",
        parent="father",
        trait="steady",
        instigator_age=6,
        partner_age=6,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        setting="garden",
        indicator="ribbon_vane",
        perch="boxes",
        response="long_pole",
        instigator="Ava",
        instigator_gender="girl",
        partner="Finn",
        partner_gender="boy",
        parent="mother",
        trait="cautious",
        instigator_age=7,
        partner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        setting="fence",
        indicator="windsock",
        perch="chair",
        response="team_hold",
        instigator="Theo",
        instigator_gender="boy",
        partner="Nora",
        partner_gender="girl",
        parent="father",
        trait="thoughtful",
        instigator_age=6,
        partner_age=5,
        relation="friends",
        trust=6,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.partner_age, params.trait):
        return "averted"
    contained = is_contained(
        RESPONSES[params.response],
        SETTINGS[params.setting],
        PERCHES[params.perch],
    )
    return "contained" if contained else "reset"


ASP_RULES = r"""
valid(S, I, P) :- setting(S), indicator(I), perch(P), height_need(S, HN), perch_height(P, PH), PH < HN.

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- cautious_now(T), trait(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), instigator_age(IA), partner_age(PA), PA > IA.
bonus(3) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

severity(HN + W) :- chosen_setting(S), height_need(S, HN), chosen_perch(P), wobble(P, W).
resp_power(PW) :- chosen_response(R), power(R, PW).
contained :- resp_power(PW), severity(SV), PW >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(reset) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("height_need", sid, setting.height_need))
    for iid in INDICATORS:
        lines.append(asp.fact("indicator", iid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("wobble", pid, perch.wobble))
        lines.append(asp.fact("perch_height", pid, perch.height))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: children making a wind indicator learn to choose teamwork over a risky climb."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--indicator", choices=INDICATORS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.indicator and args.perch:
        setting = SETTINGS[args.setting]
        indicator = INDICATORS[args.indicator]
        perch = PERCHES[args.perch]
        if not valid_combo(setting, indicator, perch):
            raise StoryError(explain_rejection(setting, indicator, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.indicator is None or combo[1] == args.indicator)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, indicator_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 8)
    return StoryParams(
        setting=setting_id,
        indicator=indicator_id,
        perch=perch_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        instigator_age=instigator_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.indicator not in INDICATORS:
        raise StoryError(f"(Unknown indicator: {params.indicator})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    setting = SETTINGS[params.setting]
    indicator = INDICATORS[params.indicator]
    perch = PERCHES[params.perch]
    response = RESPONSES[params.response]
    if not valid_combo(setting, indicator, perch):
        raise StoryError(explain_rejection(setting, indicator, perch))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        indicator=indicator,
        perch=perch,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
        instigator_age=params.instigator_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # pragma: no cover - defensive in verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, indicator, perch) combos:\n")
        for setting, indicator, perch in combos:
            print(f"  {setting:8} {indicator:12} {perch}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.partner}: {p.indicator} at {p.setting} "
                f"using {p.perch} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
