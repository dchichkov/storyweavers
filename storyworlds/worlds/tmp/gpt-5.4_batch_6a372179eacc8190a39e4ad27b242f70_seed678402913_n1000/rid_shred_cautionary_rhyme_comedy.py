#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py
===============================================================

A standalone storyworld about a child who spots a loose thread on a costume or
show prop and tries to get rid of it with a cutting tool. In this tiny domain,
one clever-looking snip can make fabric shred, while a calm grown-up uses a
better fix and teaches the child to ask first.

The prose leans child-facing, cautionary, comic, and lightly rhymed.

Run it
------
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py --target cape
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py --repair safety_pin
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py --all
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/rid_shred_cautionary_rhyme_comedy.py --verify
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
NERVE_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "sensible", "tidy", "patient"}


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
    shreddable: bool = False
    makes_cut: bool = False
    repair_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    game: str
    rig: str
    dark_word: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    phrase: str
    loose_bit: str
    near: str
    spread: int
    shreddable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    lesson: str
    makes_cut: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    target: str
    tool: str
    repair: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 5
    relation: str = "friends"
    trust: int = 5
    seed: Optional[int] = None


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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_shred_spreads(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["ripped"] < THRESHOLD:
            continue
        sig = ("shred", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["shredded"] += 1
        ent.meters["floppy"] += 1
        for kid in world.kids():
            kid.memes["alarm"] += 1
        out.append("__shred__")
    return out


CAUSAL_RULES = [
    Rule(name="shred_spreads", tag="physical", apply=_r_shred_spreads),
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        game="a dragon parade",
        rig="A painted box was the castle, paper flames curled from the wall, and a little drum went boom-biddy-boom.",
        dark_word="parade",
        ending_image="the dragon swished past the cubbies with a neat tail and a silly grin",
        tags={"classroom", "parade"},
    ),
    "living_room": Setting(
        id="living_room",
        place="the living room",
        game="a royal cape race",
        rig="Two cushions were mountains, a laundry basket was the carriage, and a spoon tapped the table like a tiny brass band.",
        dark_word="race",
        ending_image="the cape fluttered by the sofa while everyone bowed and laughed",
        tags={"home", "cape"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        game="a puppet show",
        rig="A chair held the stage, a blanket made the roof, and three sock puppets waited for their grand hello.",
        dark_word="show",
        ending_image="the puppet curtain hung straight while the sock king squeaked, 'Encore!'",
        tags={"playroom", "puppet"},
    ),
}

TARGETS = {
    "cape": Target(
        id="cape",
        label="cape",
        the="the cape",
        phrase="a shiny red cape",
        loose_bit="a loose silver thread at the hem",
        near="the swishy hem",
        spread=2,
        shreddable=True,
        tags={"cape", "fabric"},
    ),
    "dragon_tail": Target(
        id="dragon_tail",
        label="dragon tail",
        the="the dragon tail",
        phrase="a green dragon tail made of felt scales",
        loose_bit="a wiggly felt strip near the tip",
        near="the felt scales",
        spread=3,
        shreddable=True,
        tags={"dragon", "fabric"},
    ),
    "puppet_curtain": Target(
        id="puppet_curtain",
        label="puppet curtain",
        the="the puppet curtain",
        phrase="a stripey puppet curtain",
        loose_bit="a dangling thread by the corner",
        near="the stripey edge",
        spread=2,
        shreddable=True,
        tags={"puppet", "fabric"},
    ),
    "wooden_sign": Target(
        id="wooden_sign",
        label="wooden sign",
        the="the wooden sign",
        phrase="a painted wooden sign",
        loose_bit="a tiny peeling paper scrap",
        near="the painted board",
        spread=1,
        shreddable=False,
        tags={"wood"},
    ),
}

TOOLS = {
    "scissors": Tool(
        id="scissors",
        label="scissors",
        phrase="the little scissors from the craft cup",
        sound="Snip!",
        lesson="scissors are for asking first, not for secret fixes",
        makes_cut=True,
        tags={"scissors", "ask_first"},
    ),
    "snips": Tool(
        id="snips",
        label="craft snips",
        phrase="the sharp craft snips by the glue sticks",
        sound="Clip!",
        lesson="craft snips need grown-up help",
        makes_cut=True,
        tags={"snips", "ask_first"},
    ),
    "shears": Tool(
        id="shears",
        label="pink shears",
        phrase="the zigzag pink shears on the shelf",
        sound="Zzzip!",
        lesson="special shears are not for sneaky fixing",
        makes_cut=True,
        tags={"shears", "ask_first"},
    ),
}

REPAIRS = {
    "quick_stitch": Repair(
        id="quick_stitch",
        sense=3,
        power=4,
        text="threaded a needle, turned the fabric flat, and stitched the torn part back together with three small loops",
        fail="threaded a needle and tried to stitch fast, but the tear had already run too far",
        qa_text="stitched the torn part back together with a needle and thread",
        tags={"sewing", "repair"},
    ),
    "patch_tape": Repair(
        id="patch_tape",
        sense=2,
        power=2,
        text="smoothed the cloth on the table and pressed a bright patch over the tear until it held",
        fail="pressed on a bright patch, but the tear kept opening whenever the fabric swished",
        qa_text="covered the tear with a strong patch",
        tags={"patch", "repair"},
    ),
    "safety_pin": Repair(
        id="safety_pin",
        sense=1,
        power=1,
        text="closed the gap with a safety pin",
        fail="tried one safety pin, but the cloth sagged and the rip widened beside it",
        qa_text="closed the gap with a safety pin",
        tags={"pin"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "sensible", "tidy", "patient", "curious", "cheerful"]

KNOWLEDGE = {
    "scissors": [
        (
            "Why should children ask before using scissors?",
            "Scissors can cut quickly, so a child can hurt fabric or fingers before they mean to. Asking a grown-up first helps the job stay safe and sensible.",
        )
    ],
    "snips": [
        (
            "What are craft snips?",
            "Craft snips are small sharp cutters used for making careful cuts. Because they are sharp, children should use them only with a grown-up's help.",
        )
    ],
    "shears": [
        (
            "What do pink shears do?",
            "Pink shears cut cloth in a zigzag edge. They are still sharp tools, so they are not toys or secret-fixing tools.",
        )
    ],
    "fabric": [
        (
            "What does it mean when cloth starts to shred?",
            "It means the fabric is splitting into little strips or fuzzy edges. Once cloth starts to shred, the tear can grow bigger with every tug.",
        )
    ],
    "repair": [
        (
            "Why is fixing fabric better than cutting at random?",
            "A proper fix holds the cloth together where it is weak. Random cutting can turn one small problem into a much bigger tear.",
        )
    ],
    "sewing": [
        (
            "What does sewing do?",
            "Sewing joins cloth with thread so the torn parts stay together. Small stitches can make a rip neat and strong again.",
        )
    ],
    "patch": [
        (
            "What is a patch?",
            "A patch is a piece of cloth or sticky fabric used to cover and strengthen a hole or tear. It helps stop a weak spot from opening wider.",
        )
    ],
    "ask_first": [
        (
            "What should you do if you find something torn or loose?",
            "Show a grown-up and ask for help before you pull or cut. A calm fix is usually better than a quick secret fix.",
        )
    ],
}
KNOWLEDGE_ORDER = ["scissors", "snips", "shears", "fabric", "repair", "sewing", "patch", "ask_first"]


def hazard_at_risk(tool: Tool, target: Target) -> bool:
    return tool.makes_cut and target.shreddable


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def rip_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_mended(repair: Repair, target: Target, delay: int) -> bool:
    return repair.power >= rip_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > NERVE_INIT


def predict_shred(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_snip(sim, sim.get(target_id), narrate=False)
    target = sim.get(target_id)
    return {
        "ripped": target.meters["ripped"] >= THRESHOLD,
        "shredded": target.meters["shredded"] >= THRESHOLD,
    }


def _do_snip(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["ripped"] += 1
    target.meters["frayed"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, setting: Setting, target: Target) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One busy afternoon in {setting.place}, {a.id} and {b.id} were getting ready for {setting.game}. "
        f"{setting.rig}"
    )
    world.say(
        f"Best of all, they had {target.phrase}, and it made the whole plan feel grand, bright, and a little absurd."
    )


def notice_loose_bit(world: World, a: Entity, target: Target) -> None:
    world.say(
        f"Then {a.id} spotted {target.loose_bit} on {target.the}. It bobbed and wobbled like it wanted a dance of its own."
    )


def tempt(world: World, a: Entity, tool: Tool) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"I can get rid of that in one tiny snip," {a.id} said. {a.pronoun().capitalize()} reached for {tool.phrase} with a grin that felt much bigger than the job.'
    )


def warn(world: World, b: Entity, a: Entity, target: Target, adult: Entity, tool: Tool) -> None:
    pred = predict_shred(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_rip"] = pred["ripped"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, wait. If you cut {target.the}, it might shred instead of staying neat. '
        f'Let\'s ask {adult.label_word} before {tool.label} turn a little thread into a bigger dread."'
    )


def defy(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It is only one thread," {a.id} said. {b.id} reached out too late, and {a.id} gave the tool a quick little wiggle.'
    )


def back_down(world: World, a: Entity, b: Entity, adult: Entity, tool: Tool) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f'{a.id} puffed up for one second, then saw how serious {b.id} looked and stopped. "All right," {a.pronoun()} sighed. '
        f'"We will not use {tool.label} like sneaky heroes."'
    )
    world.say(
        f"They carried the costume piece to {adult.label_word}, who smiled at their honesty before any trouble had a chance to start."
    )


def snip(world: World, target_ent: Entity, tool: Tool, target: Target) -> None:
    _do_snip(world, target_ent)
    world.say(
        f"{tool.sound} The first cut looked small. Then {target.near} gave a funny twitch, the cloth slipped sideways, and one neat edge turned into a wobble, a flap, and a shred."
    )


def alarm(world: World, a: Entity, b: Entity, target: Target, adult: Entity) -> None:
    world.say(
        f'"Oh no! {target.The}!" {a.id} yelped.'
    )
    world.say(
        f'"{adult.label_word.capitalize()}!" {b.id} called, because calling for help was quicker than pretending nothing had happened.'
    )


def mend(world: World, adult: Entity, repair: Repair, target_ent: Entity, target: Target, setting: Setting) -> None:
    target_ent.meters["ripped"] = 0.0
    target_ent.meters["shredded"] = 0.0
    target_ent.meters["fixed"] += 1
    body = repair.text.replace("{target}", target.label)
    world.say(
        f"{adult.label_word.capitalize()} came over, took one look, and did not shout. Instead {adult.pronoun()} {body}."
    )
    world.say(
        f'Soon {target.the} was tidy again. Everyone let out the same soft breath: "Phew."'
    )
    world.say(
        f"In this round, the rhyme was simple and true: ask for a fix, and the fun can stay with you."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity, tool: Tool) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["alarm"] = 0.0
        kid.memes["love"] += 1
    world.say(
        f'{adult.label_word.capitalize()} knelt beside them. "I am glad you called me," {adult.pronoun()} said. '
        f'"But remember: {tool.lesson}. When cloth looks loose, ask first instead of guessing."'
    )
    world.say(
        f'{a.id} nodded. {b.id} nodded too. They had wanted a fast trick, but now they understood the better pick.'
    )


def safe_finish(world: World, a: Entity, b: Entity, target: Target, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later, the game began at last. {setting.ending_image}."
    )
    world.say(
        f"{a.id} kept hands off loose threads after that, and {b.id} gave a proud little clap. What had changed was easy to see: less sneaky snip, more ask-and-be-free."
    )


def mend_fail(world: World, adult: Entity, repair: Repair, target_ent: Entity, target: Target) -> None:
    target_ent.meters["droopy"] += 1
    body = repair.fail.replace("{target}", target.label)
    world.say(
        f"{adult.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"{target.The} did not fall apart completely, but it hung lopsided and floppy, more plop than pop."
    )


def comic_consequence(world: World, a: Entity, b: Entity, adult: Entity, setting: Setting, target: Target) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["embarrassed"] += 1
    world.say(
        f"The show could not use {target.the} that day, so {adult.label_word} found a plain backup cloth and a cardboard sign that said OOPS in giant bubble letters."
    )
    world.say(
        f"When the game finally started, everyone laughed kindly. It was still funny, but {a.id} could tell one secret snip had turned a grand plan into a goofy delay."
    )
    world.say(
        f'After that, {a.id} said, "Next time I will ask before I try to get rid of a thread." That was the joke and the lesson together.'
    )


def tell(
    setting: Setting,
    target: Target,
    tool: Tool,
    repair: Repair,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    adult_type: str = "teacher",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 7,
    relation: str = "siblings",
    trust: int = 5,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the grown-up",
        )
    )
    world.add(Entity(id="tool", type="tool", label=tool.label, makes_cut=True, tags=set(tool.tags)))
    tgt = world.add(
        Entity(
            id="target",
            type="target",
            label=target.label,
            phrase=target.phrase,
            shreddable=target.shreddable,
            tags=set(target.tags),
        )
    )

    a.memes["bravery"] = NERVE_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, setting, target)
    notice_loose_bit(world, a, target)

    world.para()
    tempt(world, a, tool)
    warn(world, b, a, target, adult, tool)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, adult, tool)
        world.para()
        mend(world, adult, REPAIRS["quick_stitch"], tgt, target, setting)
        lesson(world, adult, a, b, tool)
        world.para()
        safe_finish(world, a, b, target, setting)
        severity = 0
        mended = True
    else:
        defy(world, a, b, tool)
        world.para()
        snip(world, tgt, tool, target)
        alarm(world, a, b, target, adult)
        severity = rip_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        mended = is_mended(repair, target, delay)

        world.para()
        if mended:
            mend(world, adult, repair, tgt, target, setting)
            lesson(world, adult, a, b, tool)
            world.para()
            safe_finish(world, a, b, target, setting)
        else:
            mend_fail(world, adult, repair, tgt, target)
            comic_consequence(world, a, b, adult, setting, target)

    outcome = "averted" if averted else ("mended" if mended else "droopy")
    world.facts.update(
        setting=setting,
        target_cfg=target,
        target=tgt,
        tool=tool,
        repair=repair,
        instigator=a,
        cautioner=b,
        adult=adult,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        predicted_rip=world.facts.get("predicted_rip", False),
        torn=tgt.meters["frayed"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_repairs():
        return combos
    for sid in SETTINGS:
        for tid, tgt in TARGETS.items():
            for tool_id, tool in TOOLS.items():
                if hazard_at_risk(tool, tgt):
                    combos.append((sid, tid, tool_id))
    return combos


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    target = f["target_cfg"]
    tool = f["tool"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a short cautionary comedy in light rhyme for a 3-to-5-year-old where children preparing {setting.game} find a loose thread and someone tries to get rid of it with {tool.label}. Include the words "rid" and "shred".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gently comic story where {a.id} wants to snip {target.the}, but {b.id} stops {a.pronoun('object')} before anything tears, and a grown-up fixes it properly.",
            'Write a rhyming cautionary story where a child learns that asking for help is better than a sneaky snip, ending with the costume safe and the game still on.',
        ]
    if outcome == "droopy":
        return [
            base,
            f"Tell a funny cautionary story where {a.id} cuts first, {target.the} starts to shred, and the grown-up fix is too weak, so the show goes on in a sillier way.",
            'Write a comic rhyme where one secret cut causes a goofy delay, and the child learns to ask before trying to fix cloth alone.',
        ]
    return [
        base,
        f"Tell a comic cautionary story where {a.id} ignores a warning, snips {target.the}, and a calm grown-up mends the problem before the game begins.",
        'Write a light rhyming story that turns one bad snip into a lesson about asking first, then ends with the costume repaired and everyone laughing.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    adult = f["adult"]
    target = f["target_cfg"]
    tool = f["tool"]
    repair = f["repair"]
    setting = f["setting"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and the {adult.label_word} who helped them. They were getting ready for {setting.game}.",
        ),
        (
            "What problem did the children notice?",
            f"They noticed {target.loose_bit} on {target.the}. It looked small, which is why {a.id} thought a quick secret fix would be easy.",
        ),
        (
            f"Why did {b.id} warn {a.id} not to cut {target.the}?",
            f"{b.id} warned that cutting a loose bit can make cloth shred instead of helping. The warning came from seeing that a tiny snip could turn one weak spot into a bigger tear.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} backed down and took {target.the} to the {adult.label_word} instead of cutting it. Because {a.id} listened in time, nothing ripped at all.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely and happily. The grown-up fixed {target.the} the proper way, and then the children could still enjoy {setting.game}.",
            )
        )
    elif f["outcome"] == "mended":
        qa.append(
            (
                f"What happened when {a.id} used {tool.label}?",
                f"The first cut looked small, but then {target.the} slipped and began to shred. A quick secret fix caused a bigger problem than the loose thread had caused.",
            )
        )
        qa.append(
            (
                f"How did the {adult.label_word} solve the problem?",
                f"The {adult.label_word} {repair.qa_text}. That calm repair worked because it held the weak fabric together instead of cutting more of it.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that {tool.lesson}. Asking first kept later fun possible, even after the mistake.",
            )
        )
    else:
        qa.append(
            (
                f"Did the first repair work well?",
                f"No. The grown-up tried to help, but the repair was too weak for the size of the tear, so {target.the} stayed droopy and could not be used properly.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The game still happened, but in a sillier delayed way with a backup cloth and a big OOPS sign. The funny ending still proved the lesson: one sneaky cut can spoil a plan.",
            )
        )
        qa.append(
            (
                f"What did {a.id} decide after that?",
                f"{a.id} decided to ask for help before trying to get rid of a loose thread again. The child had seen how fast one snip could make fabric shred.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["target_cfg"].tags)
    outcome = world.facts["outcome"]
    if outcome == "mended":
        tags |= set(world.facts["repair"].tags)
    elif outcome == "averted":
        tags |= {"repair", "sewing"}
    else:
        tags |= {"repair"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.shreddable:
            bits.append("shreddable=True")
        if e.makes_cut:
            bits.append("makes_cut=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        target="dragon_tail",
        tool="scissors",
        repair="quick_stitch",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        adult="teacher",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        setting="living_room",
        target="cape",
        tool="snips",
        repair="patch_tape",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        adult="mother",
        trait="curious",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        setting="playroom",
        target="puppet_curtain",
        tool="shears",
        repair="patch_tape",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        adult="father",
        trait="patient",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        setting="classroom",
        target="cape",
        tool="scissors",
        repair="quick_stitch",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Maya",
        cautioner_gender="girl",
        adult="teacher",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=8,
    ),
]


def explain_rejection(tool: Tool, target: Target) -> str:
    if not target.shreddable:
        return (
            f"(No story: {target.the} is not the kind of fabric that can really shred from {tool.label}. "
            f"Without a plausible tearing risk, there is no honest cautionary turn.)"
        )
    return "(No story: this combination has no plausible shredding hazard.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = " / ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense (sense={repair.sense} < {SENSE_MIN}). "
        f"Try a sturdier fix like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "mended" if is_mended(REPAIRS[params.repair], TARGETS[params.target], params.delay) else "droopy"


ASP_RULES = r"""
hazard(Tool, Target) :- makes_cut(Tool), shreddable(Target).
sensible(Repair) :- repair(Repair), sense(Repair, S), sense_min(M), S >= M.
valid(Setting, Target, Tool) :- setting(Setting), target(Target), tool(Tool), hazard(Tool, Target).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), nerve_init(N), A > N.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D).
repair_power(P) :- chosen_repair(R), power(R, P).
mended :- repair_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(mended) :- not averted, mended.
outcome(droopy) :- not averted, not mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("spread", tid, t.spread))
        if t.shreddable:
            lines.append(asp.fact("shreddable", tid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.makes_cut:
            lines.append(asp.fact("makes_cut", tool_id))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_repair", params.repair),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to get rid of a loose thread, and fabric may shred. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father", "teacher"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much the tear worsens before the grown-up fixes it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].shreddable:
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(tool, TARGETS[args.target]))
    if args.tool and args.target:
        tool = TOOLS[args.tool]
        target = TARGETS[args.target]
        if not hazard_at_risk(tool, target):
            raise StoryError(explain_rejection(tool, target))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, target, tool = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    adult = args.adult or rng.choice(["mother", "father", "teacher"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        setting=setting,
        target=target,
        tool=tool,
        repair=repair,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        adult=adult,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        target = TARGETS[params.target]
        tool = TOOLS[params.tool]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not hazard_at_risk(tool, target):
        raise StoryError(explain_rejection(tool, target))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        setting=setting,
        target=target,
        tool=tool,
        repair=repair,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        adult_type=params.adult,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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

    clingo_repairs = set(asp_sensible())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} python={sorted(python_repairs)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, target, tool) combos:\n")
        for setting, target, tool in combos:
            print(f"  {setting:12} {target:15} {tool}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.target} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
