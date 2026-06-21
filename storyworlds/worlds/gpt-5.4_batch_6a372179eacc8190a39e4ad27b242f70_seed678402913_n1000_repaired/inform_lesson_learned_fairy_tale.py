#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py
==============================================================

A standalone storyworld for a small fairy-tale domain about noticing trouble,
trying to handle it alone, then learning to inform the right grown-up so the
whole village can help sensibly.

The core lesson is simple and child-facing:
when something important is going wrong, telling a trusted grown-up quickly is
wise and brave.

Run it
------
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --place moon_orchard --issue lantern_chain
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --helper spider_tailor
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/inform_lesson_learned_fairy_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "queen", "grandmother", "mother", "woman"}
        male = {"boy", "fairy_boy", "king", "grandfather", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return self.attrs.get("title_word", self.type.replace("_", " "))


@dataclass
class Place:
    id: str
    label: str
    scene: str
    festival: str
    afford_issues: set[str] = field(default_factory=set)
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Issue:
    id: str
    label: str
    phrase: str
    sign: str
    object_label: str
    severity: int
    need_skill: str
    solo_try: str
    worsen: str
    fix_need: str
    late_cost: str
    afford_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    skill: str
    power: int
    entrance: str
    fix_text: str
    qa_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    issue: str
    helper: str
    child_name: str
    child_type: str
    elder_type: str
    delay: int = 0
    trait: str = "eager"
    seed: Optional[int] = None


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_damaged_issue(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    place = world.entities.get("place")
    issue = world.entities.get("issue")
    if not child or not place or not issue:
        return out
    if issue.meters["damage"] < THRESHOLD:
        return out
    sig = ("issue_risk", issue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    place.meters["festival_risk"] += 1
    out.append("__risk__")
    return out


def _r_solo_strain(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    issue = world.entities.get("issue")
    if not child or not issue:
        return out
    if child.meters["solo_try"] < THRESHOLD:
        return out
    sig = ("solo_strain", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    issue.meters["damage"] += 1
    out.append("__strain__")
    return out


CAUSAL_RULES = [
    Rule(name="damaged_issue", tag="physical", apply=_r_damaged_issue),
    Rule(name="solo_strain", tag="emotional", apply=_r_solo_strain),
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
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "mushroom_hollow": Place(
        id="mushroom_hollow",
        label="Mushroom Hollow",
        scene="where red-capped roofs glowed under fern leaves",
        festival="the Twilight Lantern Dance",
        afford_issues={"lantern_chain", "petal_bridge", "fountain_gate"},
        ending_image="The lanterns swayed above the round little doors like patient stars.",
        tags={"fairy_village", "lanterns"},
    ),
    "moon_orchard": Place(
        id="moon_orchard",
        label="Moon Orchard",
        scene="where silver pears chimed softly in the dusk breeze",
        festival="the Moon-Pear Supper",
        afford_issues={"lantern_chain", "petal_bridge"},
        ending_image="The moon shone on the orchard paths until every pear looked polished with milk.",
        tags={"orchard", "moon"},
    ),
    "thistle_green": Place(
        id="thistle_green",
        label="Thistle Green",
        scene="where clover lanes curled between bright thistle towers",
        festival="the Dewdrop Welcome Feast",
        afford_issues={"petal_bridge", "fountain_gate"},
        ending_image="Dew sat on every blade of grass like a row of tiny glass beads.",
        tags={"meadow", "dew"},
    ),
}

ISSUES = {
    "lantern_chain": Issue(
        id="lantern_chain",
        label="lantern chain",
        phrase="a silver lantern chain",
        sign="one side of the lantern chain had come loose and the hanging lamps were tilting",
        object_label="lanterns",
        severity=2,
        need_skill="mending",
        solo_try="reached up on tiptoe and tugged at the silver chain",
        worsen="but the chain slipped harder and the lanterns knocked together with a worried clink",
        fix_need="the lamps needed careful mending before the festival could begin",
        late_cost="the first dance had to wait while everyone stood in the darkening square",
        afford_places={"mushroom_hollow", "moon_orchard"},
        tags={"lanterns", "festival", "repair"},
    ),
    "petal_bridge": Issue(
        id="petal_bridge",
        label="petal bridge",
        phrase="the petal bridge over the brook",
        sign="the petal bridge was sagging, and one silk rail had frayed nearly through",
        object_label="bridge",
        severity=3,
        need_skill="weaving",
        solo_try="pressed both hands against the soft bridge and tried to push it straight again",
        worsen="but the wet petals bent lower and a few drifted into the brook",
        fix_need="the bridge needed strong weaving before families could cross safely",
        late_cost="families had to take the long muddy path and arrived late to the feast",
        afford_places={"mushroom_hollow", "moon_orchard", "thistle_green"},
        tags={"bridge", "brook", "safety"},
    ),
    "fountain_gate": Issue(
        id="fountain_gate",
        label="fountain gate",
        phrase="the little gate on the singing fountain",
        sign="the fountain gate was stuck open and the water was spilling too fast into the moss beds",
        object_label="fountain",
        severity=2,
        need_skill="watercraft",
        solo_try="leaned all her weight against the gate handle to force it shut",
        worsen="but the handle only splashed her sleeve and the water rushed louder",
        fix_need="the fountain needed a steady water-worker to set its flow right",
        late_cost="the moss table for the feast had to be moved away from the spreading puddles",
        afford_places={"mushroom_hollow", "thistle_green"},
        tags={"water", "fountain", "garden"},
    ),
}

HELPERS = {
    "spider_tailor": HelperCfg(
        id="spider_tailor",
        label="Spider Tailor",
        phrase="the Spider Tailor",
        skill="mending",
        power=2,
        entrance="came gliding down on a neat silver thread",
        fix_text="knotted the chain with shining silk and steadied each tiny lamp until they hung quiet and straight",
        qa_fix="mended the chain with silk so the lanterns could hang safely again",
        tags={"spider", "mending", "silk"},
    ),
    "wren_weaver": HelperCfg(
        id="wren_weaver",
        label="Wren Weaver",
        phrase="the Wren Weaver",
        skill="weaving",
        power=3,
        entrance="fluttered down with reeds tucked under one wing",
        fix_text="wove new reeds and petals through the bridge until it lifted firm above the brook again",
        qa_fix="rewove the bridge so families could cross safely again",
        tags={"bird", "weaving", "bridge"},
    ),
    "newt_keeper": HelperCfg(
        id="newt_keeper",
        label="Newt Keeper",
        phrase="the Newt Keeper",
        skill="watercraft",
        power=2,
        entrance="hurried up with a shell key hanging from a ribbon belt",
        fix_text="set the gate notch by notch until the fountain sang softly instead of roaring",
        qa_fix="used a shell key to set the fountain gate and slow the water",
        tags={"newt", "water", "fountain"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tansy", "Poppy", "Nella", "Fern", "Iris", "Wren"]
BOY_NAMES = ["Pip", "Rowan", "Bram", "Nico", "Ash", "Elm", "Tobin", "Finn"]
TRAITS = ["eager", "bright", "kind", "quick", "curious", "hopeful"]


def issue_at_place(place_id: str, issue_id: str) -> bool:
    return issue_id in PLACES[place_id].afford_issues and place_id in ISSUES[issue_id].afford_places


def helper_fits(issue_id: str, helper_id: str) -> bool:
    return ISSUES[issue_id].need_skill == HELPERS[helper_id].skill


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for issue_id in ISSUES:
            if not issue_at_place(place_id, issue_id):
                continue
            for helper_id in HELPERS:
                if helper_fits(issue_id, helper_id):
                    combos.append((place_id, issue_id, helper_id))
    return combos


def issue_pressure(issue: Issue, delay: int) -> int:
    return issue.severity + delay


def is_saved(issue: Issue, helper: HelperCfg, delay: int) -> bool:
    return helper.power >= issue_pressure(issue, delay)


def predict_if_silent(world: World, delay: int) -> dict:
    sim = world.copy()
    issue = sim.get("issue")
    place = sim.get("place")
    issue.meters["damage"] += 1
    for _ in range(delay):
        issue.meters["damage"] += 1
    propagate(sim, narrate=False)
    return {
        "festival_risk": place.meters["festival_risk"] + max(0, delay),
        "damage": issue.meters["damage"],
    }


def introduce(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f"In {world.place.label}, {world.place.scene}, there lived a little fairy named {child.id}."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved helping {elder.title_word} get ready for {world.place.festival}, "
        f"because on that evening the whole village shone as if a star had bent down to listen."
    )


def festival_setup(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"That day, {child.id} skipped along the path with both hands full of berry ribbons and bright plans."
    )


def notice_issue(world: World, child: Entity, issue_cfg: Issue) -> None:
    issue = world.get("issue")
    issue.meters["damage"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But near the village square, {child.id} stopped short. {issue_cfg.sign}."
    )
    world.say(
        f"If no one fixed it, {issue_cfg.fix_need}."
    )


def decide_alone(world: World, child: Entity, elder: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f'{child.id} whispered, "If I mend it myself, {elder.title_word} will be so pleased."'
    )
    world.say(
        f"For one little moment, {child.pronoun()} did not run to inform {elder.title_word} at all."
    )


def solo_attempt(world: World, child: Entity, issue_cfg: Issue) -> None:
    child.meters["solo_try"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} {issue_cfg.solo_try}, {issue_cfg.worsen}."
    )
    world.say(
        f"At once, {child.pronoun('possessive')} brave feeling turned small and shaky."
    )


def realize_need(world: World, child: Entity, elder: Entity) -> None:
    child.memes["insight"] += 1
    world.say(
        f"Then {child.id} understood something important: keeping quiet was not the same as being helpful."
    )
    world.say(
        f'{child.pronoun().capitalize()} gathered a deep breath, ran as fast as dew-light feet could go, and cried, '
        f'"Please wait! I must inform {elder.title_word}!"'
    )


def inform_elder(world: World, child: Entity, elder: Entity, issue_cfg: Issue) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"{child.id} found {elder.title_word} by the bunting table and told the whole truth about {issue_cfg.phrase}."
    )
    world.say(
        f"{elder.title_word.capitalize()} listened at once and gave a gentle nod instead of a scold."
    )


def summon_helper(world: World, elder: Entity, helper_cfg: HelperCfg) -> None:
    world.say(
        f'"You did the right thing by telling me," {elder.title_word} said. Then {elder.pronoun()} called for {helper_cfg.phrase}, '
        f"who {helper_cfg.entrance}."
    )


def repair_success(world: World, child: Entity, elder: Entity, helper_cfg: HelperCfg, issue_cfg: Issue) -> None:
    issue = world.get("issue")
    place = world.get("place")
    issue.meters["damage"] = 0.0
    place.meters["festival_risk"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper_cfg.label} {helper_cfg.fix_text}."
    )
    world.say(
        f"Soon the trouble was over, and {world.place.festival} began with music, light, and many thankful smiles."
    )
    world.say(
        f'{elder.title_word.capitalize()} squeezed {child.id}\'s hand and said, "The wisest helpers inform others before small troubles grow big."'
    )


def repair_late(world: World, child: Entity, elder: Entity, helper_cfg: HelperCfg, issue_cfg: Issue) -> None:
    issue = world.get("issue")
    place = world.get("place")
    issue.meters["damage"] = 0.0
    place.meters["festival_risk"] = 1.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper_cfg.label} {helper_cfg.fix_text}."
    )
    world.say(
        f"But because help had come late, {issue_cfg.late_cost}."
    )
    world.say(
        f'Still, when the first cheerful song finally rose, {elder.title_word} told {child.id}, '
        f'"Next time, inform me sooner. Truth told early is a kind of magic too."'
    )


def ending_image(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After that, whenever {child.id} saw a knot, crack, or splash that seemed too big for small hands, {child.pronoun()} told a grown fairy right away."
    )
    world.say(world.place.ending_image)


def tell(
    place_cfg: Place,
    issue_cfg: Issue,
    helper_cfg: HelperCfg,
    child_name: str = "Lina",
    child_type: str = "fairy_girl",
    elder_type: str = "queen",
    delay: int = 0,
    trait: str = "eager",
) -> World:
    world = World(place_cfg)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"display_name": child_name, "title_word": child_name},
        tags={"child"},
    ))
    elder_title = {"queen": "Queen Moss", "grandmother": "Grandmother Willow"}[elder_type]
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_title,
        phrase=elder_title,
        role="elder",
        attrs={"title_word": elder_title},
        tags={"adult"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    issue = world.add(Entity(
        id="issue",
        kind="thing",
        type="issue",
        label=issue_cfg.label,
        phrase=issue_cfg.phrase,
        role="issue",
        tags=set(issue_cfg.tags),
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place_cfg.label,
        phrase=place_cfg.label,
        role="place",
        tags=set(place_cfg.tags),
    ))

    child.attrs["display_name"] = child_name
    child.attrs["trait"] = trait

    introduce(world, child, elder)
    festival_setup(world, child)

    world.para()
    notice_issue(world, child, issue_cfg)
    decide_alone(world, child, elder)
    solo_attempt(world, child, issue_cfg)

    if delay > 0:
        issue.meters["damage"] += float(delay)
        place.meters["festival_risk"] += float(delay)
        child.memes["worry"] += float(delay)
        world.say(
            f"For a few precious minutes, the trouble kept growing while {child.id} stood frozen, wishing the answer would arrive by itself."
        )

    world.para()
    realize_need(world, child, elder)
    inform_elder(world, child, elder, issue_cfg)
    summon_helper(world, elder, helper_cfg)

    saved = is_saved(issue_cfg, helper_cfg, delay)
    world.para()
    if saved:
        repair_success(world, child, elder, helper_cfg, issue_cfg)
    else:
        repair_late(world, child, elder, helper_cfg, issue_cfg)

    world.para()
    ending_image(world, child)

    outcome = "saved" if saved else "late"
    world.facts.update(
        child=child,
        elder=elder,
        helper=helper,
        place_cfg=place_cfg,
        issue_cfg=issue_cfg,
        helper_cfg=helper_cfg,
        delay=delay,
        outcome=outcome,
        informed=True,
        lesson=True,
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def child_noun(child: Entity) -> str:
    return "fairy girl" if child.type == "fairy_girl" else "fairy boy"


KNOWLEDGE = {
    "fairy_village": [
        ("What is a fairy village in a fairy tale?",
         "A fairy village is a make-believe little community where tiny people live among flowers, leaves, and hidden doors. Fairy tales use it to make ordinary things feel enchanted.")
    ],
    "lanterns": [
        ("Why are lanterns useful at a celebration?",
         "Lanterns give gentle light when the sky grows dim. They help people see and make a celebration feel warm and special.")
    ],
    "bridge": [
        ("Why should you tell a grown-up if a bridge looks broken?",
         "A broken bridge can be unsafe to cross. Telling a grown-up quickly helps keep everyone safe before someone gets hurt.")
    ],
    "water": [
        ("Why can too much water be a problem?",
         "Water helps things grow, but too much water can flood a place and make a mess. That is why people sometimes need to guide or stop it.")
    ],
    "mending": [
        ("What does mending mean?",
         "Mending means fixing something that is torn, loose, or broken so it can be used again. Careful hands often do mending.")
    ],
    "weaving": [
        ("What is weaving?",
         "Weaving is making something by crossing soft pieces over and under each other. It can turn reeds, thread, or petals into something strong.")
    ],
    "inform": [
        ("What does inform mean?",
         "Inform means to tell someone important information. In a story, it often means speaking up so the right person can help.")
    ],
    "lesson": [
        ("What lesson does this fairy tale teach?",
         "It teaches that telling the truth early and asking the right person for help is wise. Small troubles are easier to fix before they grow.")
    ],
}
KNOWLEDGE_ORDER = ["inform", "lesson", "fairy_village", "lanterns", "bridge", "water", "mending", "weaving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    issue_cfg = f["issue_cfg"]
    place_cfg = f["place_cfg"]
    return [
        f'Write a gentle fairy tale for a 3-to-5-year-old that includes the word "inform" and teaches a lesson learned.',
        f"Tell a fairy-tale story about {display_name(child)}, a little {child_noun(child)}, who sees trouble with {issue_cfg.phrase} in {place_cfg.label} and must decide whether to inform {elder.title_word}.",
        f"Write a short lesson-learned story where a child first tries to solve a village problem alone, then learns that informing a trusted grown-up early is the wiser kind of bravery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    issue_cfg = f["issue_cfg"]
    helper_cfg = f["helper_cfg"]
    place_cfg = f["place_cfg"]
    child_name = display_name(child)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a little {child_noun(child)}, in {place_cfg.label}. {elder.title_word} and {helper_cfg.label} help shape what happens next."
        ),
        (
            f"What problem did {child_name} discover?",
            f"{child_name} discovered that {issue_cfg.sign}. That mattered because {issue_cfg.fix_need}."
        ),
        (
            f"Why did {child_name} not inform {elder.title_word} right away?",
            f"{child_name} wanted to be helpful and hoped to fix the trouble alone first. But wanting to look capable made {child.pronoun('object')} stay quiet for too long."
        ),
        (
            f"What made {child_name} decide to inform {elder.title_word} after all?",
            f"The problem became worse when {child_name} tried to handle it alone, and that frightened {child.pronoun('object')}. Then {child.pronoun()} understood that telling the truth quickly was the wiser way to help."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append((
            f"How was the problem fixed?",
            f"{helper_cfg.label} {helper_cfg.qa_fix}. Because {child_name} finally informed {elder.title_word}, the right helper arrived in time."
        ))
        qa.append((
            "How did the story end?",
            f"The festival was saved, and the village could celebrate happily. The ending shows that speaking up early can protect everyone else's joy."
        ))
    else:
        qa.append((
            f"Was everything saved in time?",
            f"Not completely. {helper_cfg.label} fixed the real problem, but help came late, so {issue_cfg.late_cost}."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child_name} learned that silence can let a small problem grow. Informing a trusted grown-up early is wiser than trying to hide the trouble and struggle alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"inform", "lesson", "fairy_village"}
    issue_id = f["issue_cfg"].id
    helper_skill = f["helper_cfg"].skill
    if issue_id == "lantern_chain":
        tags.add("lanterns")
    if issue_id == "petal_bridge":
        tags.add("bridge")
        tags.add("weaving")
    if issue_id == "fountain_gate":
        tags.add("water")
    if helper_skill == "mending":
        tags.add("mending")
    if helper_skill == "weaving":
        tags.add("weaving")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="mushroom_hollow",
        issue="lantern_chain",
        helper="spider_tailor",
        child_name="Lina",
        child_type="fairy_girl",
        elder_type="queen",
        delay=0,
        trait="eager",
    ),
    StoryParams(
        place="moon_orchard",
        issue="petal_bridge",
        helper="wren_weaver",
        child_name="Pip",
        child_type="fairy_boy",
        elder_type="grandmother",
        delay=0,
        trait="quick",
    ),
    StoryParams(
        place="thistle_green",
        issue="fountain_gate",
        helper="newt_keeper",
        child_name="Fern",
        child_type="fairy_girl",
        elder_type="queen",
        delay=1,
        trait="curious",
    ),
    StoryParams(
        place="mushroom_hollow",
        issue="petal_bridge",
        helper="wren_weaver",
        child_name="Bram",
        child_type="fairy_boy",
        elder_type="grandmother",
        delay=1,
        trait="bright",
    ),
]


def explain_rejection(place_id: str, issue_id: str, helper_id: str) -> str:
    if place_id and issue_id and not issue_at_place(place_id, issue_id):
        return (
            f"(No story: {ISSUES[issue_id].phrase} does not belong in {PLACES[place_id].label}. "
            f"Pick a place where that sort of trouble could reasonably happen.)"
        )
    if issue_id and helper_id and not helper_fits(issue_id, helper_id):
        return (
            f"(No story: {HELPERS[helper_id].label} does not fix {ISSUES[issue_id].label}. "
            f"This world only allows helpers whose skill truly matches the problem.)"
        )
    return "(No story: this combination does not make sense in the fairy village.)"


ASP_RULES = r"""
issue_at_place(P, I) :- place(P), issue(I), affords(P, I), allowed_in(I, P).
helper_fits(I, H) :- issue(I), helper(H), needs(I, S), skill(H, S).
valid(P, I, H) :- issue_at_place(P, I), helper_fits(I, H).

pressure(V) :- chosen_issue(I), base_severity(I, S), delay(D), V = S + D.
saved :- chosen_issue(I), chosen_helper(H), power(H, P), pressure(V), P >= V.
outcome(saved) :- saved.
outcome(late) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for issue_id in sorted(place.afford_issues):
            lines.append(asp.fact("affords", place_id, issue_id))
    for issue_id, issue in ISSUES.items():
        lines.append(asp.fact("issue", issue_id))
        lines.append(asp.fact("base_severity", issue_id, issue.severity))
        lines.append(asp.fact("needs", issue_id, issue.need_skill))
        for place_id in sorted(issue.afford_places):
            lines.append(asp.fact("allowed_in", issue_id, place_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill", helper_id, helper.skill))
        lines.append(asp.fact("power", helper_id, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_issue", params.issue),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    issue = ISSUES[params.issue]
    helper = HELPERS[params.helper]
    return "saved" if is_saved(issue, helper, params.delay) else "late"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale storyworld about learning to inform a trusted grown-up when something important is wrong."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["fairy_girl", "fairy_boy"])
    ap.add_argument("--elder-type", choices=["queen", "grandmother"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the child hesitates before telling the elder")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.issue and not issue_at_place(args.place, args.issue):
        raise StoryError(explain_rejection(args.place, args.issue, args.helper or ""))
    if args.issue and args.helper and not helper_fits(args.issue, args.helper):
        raise StoryError(explain_rejection(args.place or "", args.issue, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.issue is None or combo[1] == args.issue)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, issue_id, helper_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["fairy_girl", "fairy_boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_type == "fairy_girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["queen", "grandmother"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        issue=issue_id,
        helper=helper_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        delay=delay,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.issue not in ISSUES:
        raise StoryError(f"(Unknown issue: {params.issue})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not issue_at_place(params.place, params.issue):
        raise StoryError(explain_rejection(params.place, params.issue, params.helper))
    if not helper_fits(params.issue, params.helper):
        raise StoryError(explain_rejection(params.place, params.issue, params.helper))

    world = tell(
        place_cfg=PLACES[params.place],
        issue_cfg=ISSUES[params.issue],
        helper_cfg=HELPERS[params.helper],
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        delay=params.delay,
        trait=params.trait,
    )
    child = world.facts["child"]
    story_text = world.render().replace("child", display_name(child))
    return StorySample(
        params=params,
        story=story_text,
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
        print(f"OK: valid_combos parity holds ({len(clingo_set)} combos).")
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
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, issue, helper) combos:\n")
        for place_id, issue_id, helper_id in combos:
            print(f"  {place_id:16} {issue_id:14} {helper_id}")
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
            header = f"### {p.child_name}: {p.issue} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
