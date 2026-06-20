#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py
===============================================================================

A standalone story world for a tiny detective-story domain built from the seed
words "bread" and "rapids" with the features "Bad Ending" and "Curiosity".

Premise
-------
A curious child detective notices that a loaf of bread has gone missing near a
river. The clues are real, the river is fast, and the child's curiosity keeps
pulling the investigation closer to danger. In every valid story, the child
crosses a risky approach they should have left alone. Nobody dies, but the case
ends badly: the bread is lost to the rapids, the culprit escapes, and the child
learns that not every mystery should be chased to the edge.

The world enforces a reasonableness constraint:
- only some clue trails honestly lead toward the rapids;
- only some crossings are plausible in a child-facing story;
- if an explicit choice would not put the detective in meaningful danger, the
  story is refused.

The prose is state-driven: clues, warning, risk, curiosity, crossing, accident,
and loss all come from simulated world state and recorded facts.

Run it
------
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py --setting mill_path --clue crumbs --crossing stepping_stones
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py --crossing footbridge
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bread_rapids_bad_ending_curiosity_detective_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 6.0
CAREFUL_TRAITS = {"careful", "steady", "patient", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    opening: str
    bread_from: str
    water_view: str
    clue_ok: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    first_seen: str
    trail_text: str
    waterside_text: str
    toward_rapids: bool
    wet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Crossing:
    id: str
    label: str
    approach: str
    sense: int
    slip_risk: int
    plausible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    intro: str
    motive: str
    can_carry_bread: bool = True
    nimble: bool = True
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    river = world.get("river")
    if detective.meters["near_edge"] >= THRESHOLD and detective.meters["crossing"] >= THRESHOLD:
        sig = ("danger", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            river.meters["danger"] += 1
            detective.memes["fear"] += 1
            partner = world.get("partner")
            partner.memes["fear"] += 1
            out.append("__danger__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    bread = world.get("bread")
    culprit = world.get("culprit")
    if detective.meters["slip"] >= THRESHOLD:
        sig = ("loss", bread.id)
        if sig not in world.fired:
            world.fired.add(sig)
            bread.meters["lost"] += 1
            culprit.meters["escaped"] += 1
            world.get("river").meters["swept"] += 1
            detective.memes["shock"] += 1
            out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("danger", "physical", _r_danger),
    Rule("loss", "physical", _r_loss),
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


def clue_fits(setting: Setting, clue: Clue) -> bool:
    return clue.id in setting.clue_ok and clue.toward_rapids


def sensible_crossings() -> list[Crossing]:
    return [c for c in CROSSINGS.values() if c.sense >= SENSE_MIN and c.plausible]


def accident_happens(crossing: Crossing, trait: str) -> bool:
    caution = 2 if trait in CAREFUL_TRAITS else 0
    return crossing.slip_risk - caution >= 2


def predict_loss(world: World, crossing_id: str, trait: str) -> dict:
    sim = world.copy()
    _cross_and_reach(sim, CROSSINGS[crossing_id], trait, narrate=False)
    return {
        "danger": sim.get("river").meters["danger"],
        "lost": sim.get("bread").meters["lost"] >= THRESHOLD,
    }


def _cross_and_reach(world: World, crossing: Crossing, trait: str, narrate: bool = True) -> None:
    detective = world.get("detective")
    detective.meters["near_edge"] += 1
    detective.meters["crossing"] += 1
    detective.memes["curiosity"] += 1
    if accident_happens(crossing, trait):
        detective.meters["slip"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, detective: Entity, partner: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] = CURIOSITY_INIT
    detective.memes["pride"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"{setting.opening} {detective.id} liked to think like a detective, and {partner.id} was "
        f"the only one who always followed {detective.pronoun('object')} from clue to clue."
    )
    world.say(
        f"That morning a fresh loaf of bread disappeared from {setting.bread_from}, and at once the whole place "
        f"felt like the start of a small, serious case."
    )


def notice_clue(world: World, detective: Entity, partner: Entity, clue: Clue, culprit: Culprit) -> None:
    world.say(
        f"{detective.id} crouched low and found {clue.first_seen}. {partner.id} leaned in, while "
        f"{culprit.intro.lower()} made the mystery feel bigger instead of smaller."
    )
    world.say(
        f'"Look," {detective.id} whispered. "{clue.trail_text} That means somebody carried the bread this way."'
    )


def warn(world: World, partner: Entity, detective: Entity, setting: Setting, clue: Clue,
         crossing: Crossing, trait: str) -> None:
    pred = predict_loss(world, crossing.id, trait)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_loss"] = pred["lost"]
    partner.memes["caution"] += 1
    extra = ""
    if pred["lost"]:
        extra = " If they went closer, the case could tumble straight into trouble."
    world.say(
        f"{partner.id} looked past the clue trail to {setting.water_view}. "
        f'"The rapids are too loud and too fast," {partner.pronoun()} said. '
        f'"We should tell a grown-up instead of trying {crossing.label}."{extra}'
    )


def decide(world: World, detective: Entity, partner: Entity, crossing: Crossing) -> None:
    detective.memes["defiance"] += 1
    world.say(
        f"But curiosity pulled harder than caution. {detective.id} tapped {detective.pronoun('possessive')} chin, "
        f"gave the case a detective's squint, and chose {crossing.approach}."
    )
    if partner.memes["caution"] >= THRESHOLD:
        world.say(
            f'{partner.id} caught at {detective.pronoun("possessive")} sleeve and said, "Please don\'t." '
            f"Still, {detective.id} slipped free and hurried on."
        )


def cross(world: World, detective: Entity, partner: Entity, crossing: Crossing,
          clue: Clue, trait: str) -> None:
    _cross_and_reach(world, crossing, trait, narrate=False)
    world.say(
        f"On the far side of the reeds, {clue.waterside_text}. The clue trail had truly reached the rapids."
    )
    if world.get("river").meters["danger"] >= THRESHOLD:
        world.say(
            f"The water below did not sound like a game. It growled and slapped at the rocks, and even "
            f"{detective.id} felt a cold shiver of fear under all that curiosity."
        )
    if world.get("detective").meters["slip"] >= THRESHOLD:
        world.say(
            f"Then one foot slid. Stones clicked under {detective.pronoun('possessive')} shoe, "
            f"and the detective case lurched all at once toward the edge."
        )
    else:
        world.say(
            f"{detective.id} managed the crossing, but only by wobbling with both arms wide and forgetting every "
            f"careful rule that should have mattered."
        )


def discovery_and_loss(world: World, detective: Entity, partner: Entity, culprit: Culprit) -> None:
    bread = world.get("bread")
    if bread.meters["lost"] >= THRESHOLD:
        world.say(
            f"For one bright second {detective.id} saw the answer: {culprit.label} had dragged the bread onto a flat rock "
            f"to nibble in secret. Then the loaf tipped, bounced once, and vanished into the rapids before anyone could grab it."
        )
        world.say(
            f"{culprit.label.capitalize()} sprang away in a blur. The mystery was solved too late to save the bread."
        )
    else:
        world.say(
            f"{detective.id} finally spotted {culprit.label} beside the loaf, but the shout of surprise sent both culprit and bread "
            f"skittering into the rapids in the same breath."
        )


def ending(world: World, detective: Entity, partner: Entity, guardian: Entity, setting: Setting) -> None:
    detective.memes["regret"] += 1
    partner.memes["sadness"] += 1
    guardian.memes["concern"] += 1
    world.say(
        f"A moment later {guardian.label_word.capitalize()} came running, but there was nothing left to rescue except two wet, shaken children "
        f"and a story nobody liked telling."
    )
    world.say(
        f'{guardian.label_word.capitalize()} held them close and said, "A clue is not worth the rapids." '
        f"{detective.id} nodded, because the case had ended badly."
    )
    world.say(
        f"The bread was gone, the culprit was gone, and {setting.place} felt quieter than before. "
        f"After that, whenever a mystery pointed toward dangerous water, {detective.id} stopped calling it adventure."
    )


def tell(setting: Setting, clue: Clue, crossing: Crossing, culprit: Culprit,
         detective_name: str = "Nora", detective_gender: str = "girl",
         partner_name: str = "Ben", partner_gender: str = "boy",
         trait: str = "curious", guardian_type: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=detective_gender, label=detective_name,
                                 role="detective", traits=[trait], attrs={"name": detective_name}))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name,
                               role="partner", traits=["careful"], attrs={"name": partner_name}))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_type, label="the parent",
                                role="guardian"))
    world.add(Entity(id="bread", type="bread", label="the bread"))
    world.add(Entity(id="river", type="river", label="the rapids"))
    world.add(Entity(id="culprit", type="animal", label=culprit.label, role="culprit"))

    opening(world, detective, partner, setting)
    world.para()
    notice_clue(world, detective, partner, clue, culprit)
    warn(world, partner, detective, setting, clue, crossing, trait)
    decide(world, detective, partner, crossing)
    world.para()
    cross(world, detective, partner, crossing, clue, trait)
    discovery_and_loss(world, detective, partner, culprit)
    world.para()
    ending(world, detective, partner, guardian, setting)

    world.facts.update(
        setting=setting,
        clue=clue,
        crossing=crossing,
        culprit_cfg=culprit,
        detective=detective,
        partner=partner,
        guardian=guardian,
        detective_name=detective_name,
        partner_name=partner_name,
        bad_ending=True,
        bread_lost=world.get("bread").meters["lost"] >= THRESHOLD,
        culprit_escaped=world.get("culprit").meters["escaped"] >= THRESHOLD,
        dangerous=world.get("river").meters["danger"] >= THRESHOLD,
        slip=world.get("detective").meters["slip"] >= THRESHOLD,
        trait=trait,
    )
    return world


SETTINGS = {
    "mill_path": Setting(
        "mill_path",
        "the old mill path",
        "By the old mill path, the day smelled of wet wood and river spray.",
        "a windowsill outside the baker's back door",
        "white water flashing between black stones",
        clue_ok={"crumbs", "feather"},
        tags={"river", "bread"},
    ),
    "market_bank": Setting(
        "market_bank",
        "the market bank",
        "Near the market bank, voices and wagon wheels hummed above the river.",
        "a stall beside a basket of apples",
        "the rapids foaming under the low bank",
        clue_ok={"crumbs", "pawprints"},
        tags={"river", "bread"},
    ),
    "willow_bend": Setting(
        "willow_bend",
        "willow bend",
        "At willow bend, green branches bowed over the path and the river muttered below.",
        "a picnic cloth spread under a willow tree",
        "the rapids racing past the roots",
        clue_ok={"pawprints", "feather"},
        tags={"river", "bread"},
    ),
}

CLUES = {
    "crumbs": Clue(
        "crumbs",
        "crumbs",
        "a neat line of bread crumbs on the dirt",
        "the crumbs kept skipping ahead in a broken little trail",
        "there were crumbs caught in the moss at the very lip of the bank",
        toward_rapids=True,
        wet=False,
        tags={"bread", "clue"},
    ),
    "pawprints": Clue(
        "pawprints",
        "paw prints",
        "small wet paw prints with flour dust in them",
        "the paw prints pointed toward the water as if the thief had hurried",
        "the prints ended on a slick rock beside the rapids",
        toward_rapids=True,
        wet=True,
        tags={"animal", "clue"},
    ),
    "feather": Clue(
        "feather",
        "a feather",
        "a gray feather stuck to a torn corner of crust",
        "the feather and crust pieces led toward the loudest water",
        "a last feather trembled in a bush hanging over the rapids",
        toward_rapids=True,
        wet=False,
        tags={"bird", "clue"},
    ),
    "string": Clue(
        "string",
        "a bit of string",
        "a piece of market string caught on a nail",
        "the string trailed only to an empty crate and nowhere else",
        "there was no real sign by the water at all",
        toward_rapids=False,
        wet=False,
        tags={"false_clue"},
    ),
}

CROSSINGS = {
    "stepping_stones": Crossing(
        "stepping_stones",
        "the stepping stones",
        "the stepping stones, shiny with spray",
        2,
        3,
        plausible=True,
        tags={"stones", "rapids"},
    ),
    "fallen_log": Crossing(
        "fallen_log",
        "the fallen log",
        "a fallen log laid across a narrow, noisy channel",
        2,
        4,
        plausible=True,
        tags={"log", "rapids"},
    ),
    "muddy_bank": Crossing(
        "muddy_bank",
        "the muddy bank",
        "the muddy bank where the reeds bent over the drop",
        2,
        2,
        plausible=True,
        tags={"mud", "rapids"},
    ),
    "footbridge": Crossing(
        "footbridge",
        "the footbridge",
        "the sturdy footbridge with a rail",
        1,
        0,
        plausible=True,
        tags={"bridge"},
    ),
}

CULPRITS = {
    "otter": Culprit(
        "otter",
        "an otter",
        "An otter-shaped ripple moved once in the reeds",
        "it had stolen the loaf because warm bread smelled better than fish that morning",
        tags={"otter", "animal"},
    ),
    "crow": Culprit(
        "crow",
        "a crow",
        "A dark wing flashed once above the path",
        "it had tugged the loaf away in proud little jerks",
        tags={"crow", "bird"},
    ),
    "dog": Culprit(
        "dog",
        "a stray dog",
        "A wagging shadow slipped behind a cart and vanished",
        "it had snatched the bread because the crust smelled rich and buttery",
        tags={"dog", "animal"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam"]
TRAITS = ["curious", "bold", "careful", "steady", "patient", "sensible"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            if not clue_fits(setting, clue):
                continue
            for xid, crossing in CROSSINGS.items():
                if crossing.sense < SENSE_MIN:
                    continue
                if xid == "footbridge":
                    continue
                for uid, culprit in CULPRITS.items():
                    if culprit.can_carry_bread:
                        combos.append((sid, cid, xid, uid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    crossing: str
    culprit: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bread": [(
        "What is bread?",
        "Bread is a baked food made from dough. People eat it plain or with meals, and animals sometimes try to steal it because it smells good."
    )],
    "rapids": [(
        "What are rapids?",
        "Rapids are fast, rough parts of a river where water rushes around rocks. They are loud, strong, and dangerous to play near."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. Detectives look for clues to understand what happened."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective notices details and tries to solve a mystery. A good detective is curious, but also careful."
    )],
    "otter": [(
        "What is an otter?",
        "An otter is a river animal with thick fur and quick paws. It can swim very well and move fast near water."
    )],
    "crow": [(
        "What is a crow?",
        "A crow is a clever black bird. It notices shiny things and can carry small pieces of food away."
    )],
    "dog": [(
        "Why might a dog steal bread?",
        "A dog may grab bread because it smells tasty. Dogs often follow their noses when food is nearby."
    )],
    "bridge": [(
        "Why is a bridge safer than slippery stones?",
        "A bridge gives you a flat place to walk and often has a rail to hold. Slippery stones near fast water can make you fall."
    )],
    "rapids_safety": [(
        "What should you do if a clue leads to dangerous water?",
        "Stop and tell a grown-up right away. Solving a mystery is never more important than staying safe."
    )],
}
KNOWLEDGE_ORDER = [
    "bread", "rapids", "clue", "detective", "otter", "crow", "dog", "bridge", "rapids_safety"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dn = f["detective_name"]
    pn = f["partner_name"]
    clue = f["clue"]
    crossing = f["crossing"]
    culprit = f["culprit_cfg"]
    return [
        'Write a detective story for a 3-to-5-year-old that includes the words "bread" and "rapids" and ends badly because curiosity goes too far.',
        f"Tell a child-facing mystery where {dn} follows {clue.label} toward the rapids, ignores {pn}'s warning, and loses the case.",
        f"Write a short detective story with a sad ending: the clue trail leads across {crossing.label}, the thief is really {culprit.label}, and the bread is swept away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dn = f["detective_name"]
    pn = f["partner_name"]
    clue = f["clue"]
    crossing = f["crossing"]
    culprit = f["culprit_cfg"]
    setting = f["setting"]
    guardian = f["guardian"]
    trait = f["trait"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {dn}, a child who likes to act like a detective, and {pn}, the friend who tries to be careful. The mystery begins when some bread goes missing near the river."
        ),
        (
            "What clue started the case?",
            f"The case began with {clue.first_seen}. That clue made {dn} believe someone had carried the bread toward the water."
        ),
        (
            f"Why did {pn} warn {dn} to stop?",
            f"{pn} warned {dn} because the clue trail led toward the rapids, and the rapids were dangerous. The warning mattered because {crossing.label} was not a safe way for children to keep investigating."
        ),
        (
            f"Why did {dn} keep going anyway?",
            f"{dn} kept going because {trait} curiosity felt stronger than caution. {dn} wanted to solve the mystery before telling a grown-up, and that choice pushed the case into danger."
        ),
    ]
    if f["slip"]:
        qa.append((
            f"What happened when {dn} went closer to the rapids?",
            f"{dn} slipped while trying {crossing.label}. That mistake let the case rush out of control just when the answer was finally in sight."
        ))
    if f["bread_lost"]:
        qa.append((
            "How did the mystery end?",
            f"It ended badly: {culprit.label} was the thief, but the bread was swept away into the rapids before anyone could save it. So the detective solved the mystery too late to fix the problem."
        ))
    qa.append((
        f"What did {guardian.label_word} teach at the end?",
        f'{guardian.label_word.capitalize()} taught that a clue is not worth the rapids. The ending shows that curiosity without caution can turn a mystery into a loss.'
    ))
    qa.append((
        "What changed by the last paragraph?",
        f"At first the missing bread felt like an exciting detective case. By the end, the river had taken the bread, the culprit was gone, and the children understood that dangerous places should stop an investigation."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bread", "rapids", "clue", "detective", "rapids_safety"}
    culprit = world.facts["culprit_cfg"].id
    if culprit == "otter":
        tags.add("otter")
    elif culprit == "crow":
        tags.add("crow")
    elif culprit == "dog":
        tags.add("dog")
    if world.facts["crossing"].id == "footbridge":
        tags.add("bridge")
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
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mill_path", "crumbs", "stepping_stones", "otter", "Nora", "girl", "Ben", "boy", "mother", "curious"),
    StoryParams("market_bank", "pawprints", "muddy_bank", "dog", "Max", "boy", "Lily", "girl", "father", "bold"),
    StoryParams("willow_bend", "feather", "fallen_log", "crow", "Ava", "girl", "Theo", "boy", "mother", "careful"),
]


def explain_rejection(setting: Optional[Setting], clue: Optional[Clue], crossing: Optional[Crossing]) -> str:
    if clue and not clue.toward_rapids:
        return (
            f"(No story: {clue.label} does not truly lead to the rapids, so there is no honest reason for the detective to risk the river.)"
        )
    if setting and clue and clue.id not in setting.clue_ok:
        return (
            f"(No story: {clue.label} is not a believable clue at {setting.place}. Pick a clue that fits the place.)"
        )
    if crossing and crossing.sense < SENSE_MIN:
        return (
            f"(No story: {crossing.label} is too safe for this bad-ending river mystery. The story needs a risky approach, not an easy crossing.)"
        )
    if crossing and crossing.id == "footbridge":
        return (
            "(No story: the footbridge is too safe and sturdy, so it does not support the intended bad ending. Pick a risky way nearer the edge.)"
        )
    return "(No story: these options do not create a believable dangerous detective case.)"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
clue_fits(S, C) :- setting(S), clue(C), allowed_clue(S, C), toward_rapids(C).
sensible_crossing(X) :- crossing(X), sense(X, V), sense_min(M), V >= M.
risky_crossing(X) :- sensible_crossing(X), not too_safe(X).
valid(S, C, X, U) :- setting(S), clue_fits(S, C), culprit(U), can_carry_bread(U),
                     risky_crossing(X).

% --- accident model --------------------------------------------------------
careful_trait(T) :- trait(T), is_careful(T).
caution_bonus(2) :- careful_trait(_).
caution_bonus(0) :- not careful_trait(_).
accident :- chosen_crossing(X), slip_risk(X, R), caution_bonus(B), R - B >= 2.
outcome(lost_case) :- accident.
outcome(lost_case) :- not accident.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(s.clue_ok):
            lines.append(asp.fact("allowed_clue", sid, cid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.toward_rapids:
            lines.append(asp.fact("toward_rapids", cid))
    for xid, x in CROSSINGS.items():
        lines.append(asp.fact("crossing", xid))
        lines.append(asp.fact("sense", xid, x.sense))
        lines.append(asp.fact("slip_risk", xid, x.slip_risk))
        if xid == "footbridge":
            lines.append(asp.fact("too_safe", xid))
    for uid, u in CULPRITS.items():
        lines.append(asp.fact("culprit", uid))
        if u.can_carry_bread:
            lines.append(asp.fact("can_carry_bread", uid))
    for t in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", t))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_crossing", params.crossing),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "lost_case"


def asp_verify() -> int:
    rc = 0
    c_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if c_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "bread" not in sample.story.lower() or "rapids" not in sample.story.lower():
            raise StoryError("Smoke test story did not render the required domain words.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child detective, a missing loaf of bread, and dangerous rapids."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.clue:
        s, c = SETTINGS[args.setting], CLUES[args.clue]
        if not clue_fits(s, c):
            raise StoryError(explain_rejection(s, c, None))
    if args.crossing:
        x = CROSSINGS[args.crossing]
        if x.sense < SENSE_MIN or x.id == "footbridge":
            raise StoryError(explain_rejection(None, None, x))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.crossing is None or c[2] == args.crossing)
              and (args.culprit is None or c[3] == args.culprit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, clue, crossing, culprit = rng.choice(sorted(combos))
    detective, dg = _pick_kid(rng)
    partner, pg = _pick_kid(rng, avoid=detective)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, crossing, culprit, detective, dg, partner, pg, guardian, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        CROSSINGS[params.crossing],
        CULPRITS[params.culprit],
        params.detective,
        params.detective_gender,
        params.partner,
        params.partner_gender,
        params.trait,
        params.guardian,
    )

    # Replace internal ids with display names in the rendered story.
    story = world.render().replace("detective", params.detective).replace("partner", params.partner)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, crossing, culprit) combos:\n")
        for setting, clue, crossing, culprit in combos:
            print(f"  {setting:12} {clue:10} {crossing:16} {culprit}")
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
            header = f"### {p.detective}: {p.clue} at {p.setting} via {p.crossing} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
