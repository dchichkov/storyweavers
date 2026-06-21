#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py
=======================================================================

A standalone storyworld for a tiny child-facing detective domain: a young
detective and a partner investigate a missing club treasure, follow clues to a
scary hiding place, and choose a retrieval tool that actually fits the case.

The world deliberately supports both:
- a bright recovery ending, and
- a softened bad ending, where the treasure is truly lost but the brave search,
  honest report, and shared notebook page soften the sadness.

Run it
------
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py --hideout drain --thing map
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py --hideout branch --tool flashlight
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/soften_bad_ending_bravery_detective_story.py --verify
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
class LostThing:
    id: str
    label: str
    phrase: str
    tag: str
    vulnerable_to: set[str] = field(default_factory=set)
    clue: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    need: str
    accepts: set[str] = field(default_factory=set)
    challenge: int = 1
    scary: bool = True
    clue_line: str = ""
    danger_line: str = ""
    success_line: str = ""
    failure_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    power: int = 1
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


def _r_scary_place(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    place = world.entities.get("place")
    if not detective or not place:
        return out
    if place.meters["entered"] < THRESHOLD or not place.attrs.get("scary", False):
        return out
    sig = ("scary", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["fear"] += 1
    if detective.memes["bravery"] >= THRESHOLD:
        detective.memes["courage"] += 1
    out.append("__scary__")
    return out


def _r_ruin(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("thing")
    place = world.entities.get("place")
    if not item or not place:
        return out
    if item.meters["exposed"] < THRESHOLD:
        return out
    risk = place.attrs.get("need", "")
    if risk not in item.attrs.get("vulnerable_to", set()):
        return out
    if world.facts.get("delay", 0) <= 0:
        return out
    sig = ("ruin", item.id, risk)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["ruined"] += 1
    out.append("__ruined__")
    return out


CAUSAL_RULES = [
    Rule(name="scary_place", tag="emotional", apply=_r_scary_place),
    Rule(name="ruin", tag="physical", apply=_r_ruin),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(x for x in sent if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


LOST_THINGS = {
    "map": LostThing(
        id="map",
        label="map",
        phrase="a folded treasure map drawn in blue crayon",
        tag="flat",
        vulnerable_to={"wet"},
        clue="A blue corner was stuck to the ground like a clue flag.",
        tags={"map", "paper", "detective"},
    ),
    "badge": LostThing(
        id="badge",
        label="badge",
        phrase="a shiny brass detective badge",
        tag="shiny",
        vulnerable_to=set(),
        clue="A bright scrape on the wood flashed when it caught the light.",
        tags={"badge", "metal", "detective"},
    ),
    "ribbon": LostThing(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon from the detective notebook",
        tag="soft",
        vulnerable_to={"wet", "thorn"},
        clue="A red thread trembled on a splinter like a tiny waving finger.",
        tags={"ribbon", "cloth", "detective"},
    ),
    "marble": LostThing(
        id="marble",
        label="marble",
        phrase="a green glass clue marble",
        tag="rolling",
        vulnerable_to=set(),
        clue="A round mark in the dust looked exactly the size of the marble.",
        tags={"marble", "glass", "detective"},
    ),
}

HIDEOUTS = {
    "shed": Hideout(
        id="shed",
        label="old shed",
        phrase="the old garden shed",
        need="dark",
        accepts={"rolling", "shiny"},
        challenge=1,
        scary=True,
        clue_line="The trail ended at the old shed, where the door stood a little open.",
        danger_line="Inside, everything looked black and close, and the quiet creaked around them.",
        success_line="The beam found the missing thing tucked behind a paint can.",
        failure_line="By the time they looked behind the paint cans, the thing had slipped through a crack in the back wall and was gone.",
        tags={"shed", "dark", "detective"},
    ),
    "branch": Hideout(
        id="branch",
        label="apple branch",
        phrase="the high apple branch by the fence",
        need="high",
        accepts={"shiny", "soft"},
        challenge=2,
        scary=True,
        clue_line="A feather and a flash of color pointed up toward the high apple branch.",
        danger_line="It was not monster-scary, but it was high enough to make small knees feel hollow.",
        success_line="With care, they lifted the missing thing down from a fork in the branch.",
        failure_line="A gust shook the branch, and the thing sailed over the fence before they could reach it.",
        tags={"branch", "high", "detective", "bird"},
    ),
    "bramble": Hideout(
        id="bramble",
        label="bramble arch",
        phrase="the bramble arch behind the bench",
        need="thorn",
        accepts={"soft", "rolling"},
        challenge=2,
        scary=True,
        clue_line="The clues led to a low bramble arch where little thorns held scraps and leaves.",
        danger_line="The tunnel was small and scratchy, and every stem seemed to reach for their sleeves.",
        success_line="Careful hands teased the missing thing free without tearing it.",
        failure_line="The thorns had already tugged the thing deeper in, until it could no longer be reached.",
        tags={"bramble", "thorn", "detective", "garden"},
    ),
    "drain": Hideout(
        id="drain",
        label="storm drain",
        phrase="the stone storm drain by the curb",
        need="wet",
        accepts={"flat", "rolling"},
        challenge=3,
        scary=True,
        clue_line="A wet trail ran to the storm drain, where water talked in a low glug-glug voice.",
        danger_line="The dark opening looked hungry, and the water made every second matter.",
        success_line="They hooked the missing thing before the current could pull it away.",
        failure_line="The water had already carried the thing too far to reach.",
        tags={"drain", "wet", "detective", "water"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        handles={"dark"},
        power=2,
        tags={"flashlight", "light"},
    ),
    "stepstool": Tool(
        id="stepstool",
        label="step stool",
        phrase="a sturdy step stool",
        handles={"high"},
        power=2,
        tags={"stepstool", "height"},
    ),
    "gloves": Tool(
        id="gloves",
        label="garden gloves",
        phrase="a pair of garden gloves",
        handles={"thorn"},
        power=2,
        tags={"gloves", "garden"},
    ),
    "hook": Tool(
        id="hook",
        label="hook pole",
        phrase="a long hook pole",
        handles={"wet"},
        power=3,
        tags={"hook", "water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "steady", "kind", "observant", "patient", "bold"]


def valid_combo(thing: LostThing, hideout: Hideout, tool: Tool) -> bool:
    return thing.tag in hideout.accepts and hideout.need in tool.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hideout_id, hideout in HIDEOUTS.items():
        for thing_id, thing in LOST_THINGS.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(thing, hideout, tool):
                    combos.append((hideout_id, thing_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    hideout: str
    thing: str
    tool: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hideout="shed",
        thing="badge",
        tool="flashlight",
        detective_name="Lily",
        detective_gender="girl",
        partner_name="Tom",
        partner_gender="boy",
        parent="mother",
        trait="observant",
        delay=0,
    ),
    StoryParams(
        hideout="branch",
        thing="ribbon",
        tool="stepstool",
        detective_name="Ben",
        detective_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        hideout="drain",
        thing="map",
        tool="hook",
        detective_name="Zoe",
        detective_gender="girl",
        partner_name="Sam",
        partner_gender="boy",
        parent="mother",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        hideout="bramble",
        thing="ribbon",
        tool="gloves",
        detective_name="Max",
        detective_gender="boy",
        partner_name="Ella",
        partner_gender="girl",
        parent="father",
        trait="bold",
        delay=2,
    ),
    StoryParams(
        hideout="drain",
        thing="marble",
        tool="hook",
        detective_name="Anna",
        detective_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        parent="mother",
        trait="patient",
        delay=0,
    ),
]


def explain_rejection(hideout: Hideout, thing: LostThing, tool: Tool) -> str:
    if thing.tag not in hideout.accepts:
        return (
            f"(No story: {thing.phrase} does not fit a clue trail to {hideout.phrase}. "
            f"That hideout usually takes a {', '.join(sorted(hideout.accepts))} item.)"
        )
    if hideout.need not in tool.handles:
        return (
            f"(No story: {tool.label} does not solve the problem at {hideout.phrase}. "
            f"That hiding place needs help for {hideout.need}.)"
        )
    return "(No story: this case does not make sense.)"


def outcome_of(params: StoryParams) -> str:
    hideout = HIDEOUTS[params.hideout]
    tool = TOOLS[params.tool]
    thing = LOST_THINGS[params.thing]
    score = tool.power - (hideout.challenge + params.delay)
    if score >= 0 and not (params.delay > 0 and hideout.need in thing.vulnerable_to):
        return "recovered"
    return "lost"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def introduce(world: World, detective: Entity, partner: Entity, thing: LostThing) -> None:
    detective.memes["joy"] += 1
    world.say(
        f"{detective.id} and {partner.id} had made a detective club with a notebook, a magnifying glass, "
        f"and one special case treasure: {thing.phrase}."
    )
    world.say(
        f"That afternoon, the treasure was gone, and both children stopped very still as if a mystery had walked into the yard."
    )


def first_clue(world: World, detective: Entity, partner: Entity, thing: LostThing, hideout: Hideout) -> None:
    world.say(
        f'"Detectives notice small things," {detective.id} whispered. {thing.clue}'
    )
    world.say(hideout.clue_line)
    partner.memes["worry"] += 1


def fear_and_choice(world: World, detective: Entity, partner: Entity, hideout: Hideout, tool: Tool) -> None:
    world.say(
        f"{partner.id} looked at {hideout.phrase} and moved a little closer to {detective.id}. {hideout.danger_line}"
    )
    world.say(
        f'{partner.id} said, "We can still be detectives and say when something feels scary."'
    )
    detective.memes["bravery"] += 1
    world.say(
        f"{detective.id} nodded, even though {detective.pronoun('possessive')} stomach fluttered. "
        f"Then {detective.pronoun()} took {tool.phrase} and decided to keep going carefully."
    )


def enter_hideout(world: World, detective: Entity, hideout: Hideout, thing: LostThing, delay: int) -> None:
    place = world.get("place")
    item = world.get("thing")
    place.meters["entered"] += 1
    item.meters["exposed"] += 1
    world.facts["delay"] = delay
    propagate(world, narrate=False)
    if detective.memes["fear"] >= THRESHOLD:
        world.say(
            f"The case felt bigger now, but {detective.id} kept moving one brave step at a time."
        )


def recover_ending(world: World, detective: Entity, partner: Entity, parent: Entity,
                   hideout: Hideout, thing: LostThing) -> None:
    item = world.get("thing")
    item.meters["recovered"] += 1
    detective.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(hideout.success_line)
    world.say(
        f'"Case solved," {partner.id} breathed. The missing {thing.label} was back in {detective.id}\'s hands, '
        f"and the whole yard seemed less spooky than before."
    )
    world.para()
    world.say(
        f"When they showed it to {parent.label_word}, {parent.pronoun()} smiled and said their brave careful thinking had cracked the case."
    )
    world.say(
        f"That evening, the detective notebook lay open on the table with a neat new title: The Case of the Missing {thing.label.capitalize()}, solved by brave detectives."
    )


def softened_bad_ending(world: World, detective: Entity, partner: Entity, parent: Entity,
                        hideout: Hideout, thing: LostThing) -> None:
    item = world.get("thing")
    item.meters["lost"] += 1
    detective.memes["sadness"] += 1
    partner.memes["sadness"] += 1
    world.say(hideout.failure_line)
    if item.meters["ruined"] >= THRESHOLD:
        world.say(
            f"What they found was only a spoiled scrap and the answer to the mystery. The {thing.label} could not be saved now."
        )
    else:
        world.say(
            f"They learned where the {thing.label} had gone, but they could not bring it back."
        )
    world.para()
    world.say(
        f"{detective.id} swallowed hard and told {parent.label_word} the truth anyway. "
        f"{parent.label_word.capitalize()} knelt beside both children and said brave detectives do not hide bad news."
    )
    world.say(
        f"That did not turn the ending happy, but it did soften it. They wrote the whole case in their notebook, "
        f"and beside the last line {partner.id} drew a small steady star for bravery."
    )


def tell(params: StoryParams) -> World:
    hideout = HIDEOUTS[params.hideout]
    thing = LOST_THINGS[params.thing]
    tool = TOOLS[params.tool]

    world = World()
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_gender,
        label=params.detective_name,
        phrase=params.detective_name,
        role="detective",
        attrs={"name": params.detective_name, "trait": params.trait},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=params.partner_gender,
        label=params.partner_name,
        phrase=params.partner_name,
        role="partner",
        attrs={"name": params.partner_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=hideout.label,
        phrase=hideout.phrase,
        attrs={"need": hideout.need, "scary": hideout.scary},
        tags=set(hideout.tags),
    ))
    item = world.add(Entity(
        id="thing",
        kind="thing",
        type="treasure",
        label=thing.label,
        phrase=thing.phrase,
        attrs={"tag": thing.tag, "vulnerable_to": set(thing.vulnerable_to)},
        tags=set(thing.tags),
    ))
    gear = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        attrs={"handles": set(tool.handles), "power": tool.power},
        tags=set(tool.tags),
    ))

    introduce(world, detective, partner, thing)
    first_clue(world, detective, partner, thing, hideout)

    world.para()
    fear_and_choice(world, detective, partner, hideout, tool)
    enter_hideout(world, detective, hideout, thing, params.delay)

    world.para()
    if outcome_of(params) == "recovered":
        recover_ending(world, detective, partner, parent, hideout, thing)
    else:
        softened_bad_ending(world, detective, partner, parent, hideout, thing)

    world.facts.update(
        detective=detective,
        partner=partner,
        parent=parent,
        hideout=hideout,
        thing_cfg=thing,
        thing=item,
        tool=tool,
        outcome=outcome_of(params),
        bravery=detective.memes["bravery"] >= THRESHOLD,
        fear=detective.memes["fear"] >= THRESHOLD,
        ruined=item.meters["ruined"] >= THRESHOLD,
        delay=params.delay,
    )
    return world


KNOWLEDGE = {
    "detective": [
        ("What does a detective do?", "A detective looks for clues, asks careful questions, and tries to figure out what happened.")
    ],
    "paper": [
        ("Why can paper be ruined by water?", "Paper soaks water up quickly. When it gets very wet, it can tear, wrinkle, or lose the writing on it.")
    ],
    "metal": [
        ("Why does shiny metal catch a bird's eye?", "Bright metal flashes in the light, so some birds notice it quickly and may peck at it or carry it off.")
    ],
    "cloth": [
        ("Why can cloth get caught on thorns?", "Cloth has soft threads. Thorns can hook those threads and hold on tight.")
    ],
    "glass": [
        ("Why can a marble roll away so fast?", "A marble is round and smooth, so it can roll with just a little push or slope.")
    ],
    "dark": [
        ("Why is a flashlight useful in a dark place?", "A flashlight helps you see where things are. Seeing clearly makes it easier to move carefully and find clues.")
    ],
    "high": [
        ("Why should a grown-up help with something high up?", "High places can be hard to reach safely. A grown-up can help steady things and stop falls.")
    ],
    "thorn": [
        ("Why do garden gloves help near brambles?", "Garden gloves protect your hands from scratches and tiny pokes, so you can work more safely.")
    ],
    "wet": [
        ("Why is a hook pole useful near water?", "A long hook lets you reach from a safer distance. That way you do not need to lean too close to the water.")
    ],
}
KNOWLEDGE_ORDER = ["detective", "paper", "metal", "cloth", "glass", "dark", "high", "thorn", "wet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    p = f["partner"]
    hideout = f["hideout"]
    thing = f["thing_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a gentle detective story for a 3-to-5-year-old that includes the word "soften" and a brave child searching for a missing {thing.label}.',
            f"Tell a detective story where {d.label} and {p.label} follow clues to {hideout.phrase}, act bravely, but the case ends sadly because the missing {thing.label} cannot be saved.",
            f"Write a child-facing mystery with bravery and a softened bad ending: the detectives solve the case but still lose the treasure."
        ]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "soften" and a brave search for a missing {thing.label}.',
        f"Tell a mystery where {d.label} and {p.label} follow clues to {hideout.phrase} and solve the case by acting brave and careful.",
        f"Write a simple detective story in which a scary hiding place seems less frightening once the children work together and solve the case."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d = f["detective"]
    p = f["partner"]
    parent = f["parent"]
    hideout = f["hideout"]
    thing = f["thing_cfg"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two child detectives, {d.label} and {p.label}. They are trying to solve the mystery of a missing {thing.label}."
        ),
        (
            f"Where did the clues lead?",
            f"The clues led to {hideout.phrase}. That place felt scary, which is why the case asked for bravery as well as careful thinking."
        ),
        (
            f"What tool did the detective use, and why?",
            f"{d.label} used {tool.phrase}. That tool fit the hiding place, so it gave the children a sensible way to keep searching."
        ),
    ]
    if f["outcome"] == "recovered":
        qa.append((
            f"How did {d.label} show bravery?",
            f"{d.label} felt scared when the case led to {hideout.phrase}, but kept going carefully anyway. That is brave because bravery means acting with care even when your stomach feels fluttery."
        ))
        qa.append((
            f"How did the story end?",
            f"The detectives recovered the missing {thing.label} and solved the case. At the end, the notebook title showed that the scary place had become a solved mystery instead of a fear."
        ))
    else:
        answer = (
            f"The ending was sad because the missing {thing.label} could not be brought back from {hideout.phrase}. "
            f"But the children still solved the mystery and told {parent.label_word} the truth, which helped soften the bad ending."
        )
        if f["ruined"]:
            answer += " The delay mattered because that kind of place could damage the lost thing before they reached it."
        qa.append((
            "Why is this a softened bad ending?",
            answer
        ))
        qa.append((
            f"How did {d.label} show bravery even though the case ended badly?",
            f"{d.label} went on with the search while feeling afraid, and then told the truth when the treasure was gone. The bravery changed what the loss meant, because the children ended the case honestly and together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", f["hideout"].need}
    thing = f["thing_cfg"]
    if "paper" in thing.tags:
        tags.add("paper")
    if "metal" in thing.tags:
        tags.add("metal")
    if "cloth" in thing.tags:
        tags.add("cloth")
    if "glass" in thing.tags:
        tags.add("glass")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_place(H, T) :- hideout(H), tool(T), needs(H, N), handles(T, N).
fits_item(H, I)  :- hideout(H), thing(I), accepts(H, Tag), item_tag(I, Tag).
valid(H, I, T)   :- fits_place(H, T), fits_item(H, I).

bad_risk         :- chosen_hideout(H), chosen_thing(I), delay(D), D > 0,
                    needs(H, N), vulnerable(I, N).
strong_enough    :- chosen_hideout(H), chosen_tool(T), delay(D),
                    power(T, P), challenge(H, C), P >= C + D.
outcome(recovered) :- valid_case, strong_enough, not bad_risk.
outcome(lost)      :- valid_case, not outcome(recovered).
valid_case         :- valid(H, I, T), chosen_hideout(H), chosen_thing(I), chosen_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("needs", hid, hideout.need))
        lines.append(asp.fact("challenge", hid, hideout.challenge))
        for tag in sorted(hideout.accepts):
            lines.append(asp.fact("accepts", hid, tag))
    for tid, thing in LOST_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("item_tag", tid, thing.tag))
        for risk in sorted(thing.vulnerable_to):
            lines.append(asp.fact("vulnerable", tid, risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for need in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, need))
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
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_thing", params.thing),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params crashed on seed {seed}")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: brave child detectives solve a missing-treasure mystery, sometimes with a softened bad ending."
    )
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--thing", choices=LOST_THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the children arrive")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hideout and args.thing and args.tool:
        hideout = HIDEOUTS[args.hideout]
        thing = LOST_THINGS[args.thing]
        tool = TOOLS[args.tool]
        if not valid_combo(thing, hideout, tool):
            raise StoryError(explain_rejection(hideout, thing, tool))

    combos = [
        c for c in valid_combos()
        if (args.hideout is None or c[0] == args.hideout)
        and (args.thing is None or c[1] == args.thing)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        if args.hideout and args.thing and args.tool:
            raise StoryError(explain_rejection(HIDEOUTS[args.hideout], LOST_THINGS[args.thing], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    hideout, thing, tool = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        hideout=hideout,
        thing=thing,
        tool=tool,
        detective_name=detective_name,
        detective_gender=detective_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"Unknown hideout: {params.hideout}")
    if params.thing not in LOST_THINGS:
        raise StoryError(f"Unknown thing: {params.thing}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"Unknown parent type: {params.parent}")
    if not valid_combo(LOST_THINGS[params.thing], HIDEOUTS[params.hideout], TOOLS[params.tool]):
        raise StoryError(explain_rejection(HIDEOUTS[params.hideout], LOST_THINGS[params.thing], TOOLS[params.tool]))

    world = tell(params)
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
        print(f"{len(combos)} compatible (hideout, thing, tool) combos:\n")
        for hideout, thing, tool in combos:
            print(f"  {hideout:8} {thing:8} {tool}")
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
            header = f"### {p.detective_name} & {p.partner_name}: {p.thing} at {p.hideout} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
