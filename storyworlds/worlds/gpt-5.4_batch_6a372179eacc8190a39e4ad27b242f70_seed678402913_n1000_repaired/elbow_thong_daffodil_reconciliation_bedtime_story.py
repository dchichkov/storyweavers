#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py
==============================================================================

A small bedtime-story world about two children, a sleepy elbow bump, one
daffodil by the bed, and a quiet reconciliation before sleep.

The seed words are always present in the rendered story:
- elbow
- thong
- daffodil

The central shape is stable:
a flower is carried in for bedtime, a careless elbow upsets it, hurt feelings
rise, and the children make peace by fixing the problem together.

Run it
------
    python storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py --bump hard --repair refill
    python storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/elbow_thong_daffodil_reconciliation_bedtime_story.py --verify
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
class Setting:
    id: str
    place: str
    opening: str
    bed_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Holder:
    id: str
    label: str
    phrase: str
    low: bool
    spill_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bump:
    id: str
    adjective: str
    line: str
    bends_stem: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    fixes_bent: bool
    needs_low_holder: bool
    ending: str
    qa_phrase: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child_a", "child_b"}]

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


def _r_sadness(world: World) -> list[str]:
    flower = world.get("flower")
    holder = world.get("holder")
    room = world.get("room")
    if flower.meters["bent"] < THRESHOLD and holder.meters["spilled"] < THRESHOLD:
        return []
    if ("sadness",) in world.fired:
        return []
    world.fired.add(("sadness",))
    for kid in world.kids():
        kid.memes["sad"] += 1
        kid.memes["blame"] += 1
    room.memes["tension"] += 1
    return []


def _r_peace(world: World) -> list[str]:
    a = world.get("a")
    b = world.get("b")
    room = world.get("room")
    if a.memes["sorry"] < THRESHOLD:
        return []
    if a.meters["helping"] < THRESHOLD or b.meters["helping"] < THRESHOLD:
        return []
    if ("peace",) in world.fired:
        return []
    world.fired.add(("peace",))
    a.memes["blame"] = 0.0
    b.memes["blame"] = 0.0
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    room.memes["tension"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="sadness", tag="social", apply=_r_sadness),
    Rule(name="peace", tag="social", apply=_r_peace),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        now = len(world.fired)
        if not changed:
            newer = len(world.fired)
            if newer != now:
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a small bedroom in a quiet cottage",
        opening="The moon had already climbed above the window, and the room was full of sleepy silver light.",
        bed_image="the patchwork quilt",
        tags={"bed", "night"},
    ),
    "attic": Setting(
        id="attic",
        place="an attic room with sloping walls",
        opening="Rain whispered on the roof, and the attic room felt tucked away like a pocket.",
        bed_image="the soft white coverlet",
        tags={"bed", "night", "rain"},
    ),
    "balcony_room": Setting(
        id="balcony_room",
        place="a little room beside a balcony garden",
        opening="The last warm air from outside drifted in through the curtain, carrying a garden smell.",
        bed_image="the striped blanket",
        tags={"bed", "night", "garden"},
    ),
}

HOLDERS = {
    "teacup": Holder(
        id="teacup",
        label="teacup",
        phrase="a tiny blue teacup",
        low=True,
        spill_sound="plip",
        tags={"cup"},
    ),
    "jam_jar": Holder(
        id="jam_jar",
        label="jam jar",
        phrase="a clear jam jar",
        low=False,
        spill_sound="clink",
        tags={"jar"},
    ),
    "bedside_vase": Holder(
        id="bedside_vase",
        label="little vase",
        phrase="a little white vase",
        low=False,
        spill_sound="tink",
        tags={"vase"},
    ),
}

BUMPS = {
    "gentle": Bump(
        id="gentle",
        adjective="little",
        line="just enough to wobble the water over the rim",
        bends_stem=False,
        tags={"spill"},
    ),
    "hard": Bump(
        id="hard",
        adjective="sleepy sideways",
        line="hard enough to knock the flower against the rim and bend its stem",
        bends_stem=True,
        tags={"spill", "bend"},
    ),
}

REPAIRS = {
    "refill": Repair(
        id="refill",
        label="refill",
        phrase="wiped the puddle, filled the holder with fresh water, and stood the daffodil up again",
        fixes_bent=False,
        needs_low_holder=False,
        ending="The daffodil stood straight beside the bed again, and its yellow face looked as calm as the moon.",
        qa_phrase="They wiped up the spill and refilled the holder with fresh water.",
        tags={"water"},
    ),
    "trim_reseat": Repair(
        id="trim_reseat",
        label="trim and reseat",
        phrase="asked for help trimming the bent stem, then settled the shorter daffodil back into the little holder",
        fixes_bent=True,
        needs_low_holder=True,
        ending="The daffodil sat shorter in its cup, but it still glowed like a small yellow lamp beside the pillow.",
        qa_phrase="They asked for help trimming the bent stem and set the shorter flower back in the holder.",
        tags={"water", "trim"},
    ),
    "float": Repair(
        id="float",
        label="float in water",
        phrase="poured clean water into the shallow holder and let the daffodil bloom float there like a tiny boat",
        fixes_bent=True,
        needs_low_holder=True,
        ending="The daffodil floated in the cup, and the moon made a bright ring around it on the bedside table.",
        qa_phrase="They changed the plan and let the flower float in fresh water in the shallow holder.",
        tags={"water", "float"},
    ),
}


def repair_works(holder: Holder, bump: Bump, repair: Repair) -> bool:
    if bump.bends_stem and not repair.fixes_bent:
        return False
    if repair.needs_low_holder and not holder.low:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for holder_id, holder in HOLDERS.items():
            for bump_id, bump in BUMPS.items():
                for repair_id, repair in REPAIRS.items():
                    if repair_works(holder, bump, repair):
                        combos.append((setting_id, holder_id, bump_id, repair_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    repair = REPAIRS[params.repair]
    return {
        "refill": "upright_again",
        "trim_reseat": "short_but_safe",
        "float": "floating_glow",
    }[repair.id]


def explain_rejection(holder: Holder, bump: Bump, repair: Repair) -> str:
    if bump.bends_stem and not repair.fixes_bent:
        return (
            f"(No story: a {bump.adjective} elbow bump bends the daffodil's stem, "
            f"so simply refilling the {holder.label} would not honestly fix it. "
            f"Choose a repair that can handle a bent flower.)"
        )
    if repair.needs_low_holder and not holder.low:
        return (
            f"(No story: {repair.label} only makes sense with a shallow holder, "
            f"but {holder.phrase} is too tall for that bedtime fix. Pick the teacup "
            f"or choose a different repair.)"
        )
    return "(No story: that repair does not fit the damage.)"


@dataclass
class StoryParams:
    setting: str
    holder: str
    bump: str
    repair: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    relationship: str
    seed: Optional[int] = None


def introduce(world: World, setting: Setting, a: Entity, b: Entity, holder: Holder) -> None:
    world.say(setting.opening)
    world.say(
        f"In {setting.place}, {a.id} and {b.id} were almost ready for sleep. "
        f"They had brought in one fresh daffodil from the evening garden and set it in {holder.phrase} on the bedside table."
    )
    world.say(
        f"{a.id} had already climbed onto {setting.bed_image}, but {b.id} was still wearing one red thong sandal and one bare foot, as if bedtime had caught {b.pronoun('object')} halfway between outside and in."
    )


def settle_in(world: World, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["cozy"] += 1
    world.say(
        f'"Let it sleep in here with us," {b.id} whispered, touching the daffodil very gently.'
    )
    world.say(
        f"{a.id} nodded and scooted over to make room for the storybook."
    )


def elbow_bump(world: World, a: Entity, b: Entity, bump: Bump, holder: Holder) -> None:
    flower = world.get("flower")
    hold = world.get("holder")
    b.memes["careless"] += 1
    hold.meters["spilled"] += 1
    if bump.bends_stem:
        flower.meters["bent"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {b.id} reached across the blanket, {b.pronoun('possessive')} elbow gave a {bump.adjective} bump to the {holder.label} -- {bump.line}."
    )
    if bump.bends_stem:
        world.say(
            f"Water splashed onto the table, and the daffodil bowed sideways with its stem bent in a tired green curve."
        )
    else:
        world.say(
            f"{holder.spill_sound.capitalize()} went the water on the wood, and the daffodil drooped until its face nearly touched the table."
        )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    world.say(f'"You bumped it," {a.id} said, and {a.pronoun()} sounded close to tears.')
    world.say(
        f'"I didn\'t mean to," {b.id} whispered back. Then, because being sorry and scared can come out wrong, {b.pronoun()} added, "You were sitting too close."'
    )
    world.say(
        f"That made {a.id} draw the blanket to {a.pronoun('possessive')} chin. The room no longer felt sleepy. It felt small."
    )


def soften(world: World, a: Entity, b: Entity) -> None:
    flower = world.get("flower")
    b.memes["sorry"] += 1
    a.memes["hurt"] += 1
    if flower.meters["bent"] >= THRESHOLD:
        see = "the bent stem"
    else:
        see = "the shining puddle and the drooping flower"
    world.say(
        f"For a few breaths they only looked at {see}. Then {b.id}'s face changed."
    )
    world.say(
        f'"I am sorry," {b.id} said. "My elbow did it, and I should not have blamed you."'
    )
    world.say(
        f"{a.id} blinked, then let the blanket fall a little. Being spoken to kindly made the hurt in {a.pronoun('possessive')} chest loosen."
    )


def repair_scene(world: World, a: Entity, b: Entity, holder: Holder, repair: Repair, parent: Entity) -> None:
    flower = world.get("flower")
    hold = world.get("holder")
    a.meters["helping"] += 1
    b.meters["helping"] += 1
    if repair.id == "refill":
        hold.meters["spilled"] = 0.0
        flower.meters["bent"] = 0.0
        flower.meters["upright"] += 1
        world.say(
            f'Together they {repair.phrase}. {a.id} held the stem steady while {b.id} fetched the water.'
        )
    elif repair.id == "trim_reseat":
        hold.meters["spilled"] = 0.0
        flower.meters["bent"] = 0.0
        flower.meters["upright"] += 1
        flower.meters["short"] += 1
        world.say(
            f'{parent.label_word.capitalize()} came in at the soft sound of voices, listened, and helped them for one moment. They {repair.phrase}.'
        )
    else:
        hold.meters["spilled"] = 0.0
        flower.meters["bent"] = 0.0
        flower.meters["floating"] += 1
        world.say(
            f'Together they {repair.phrase}. {a.id} smiled first, and then {b.id} smiled too.'
        )
    propagate(world, narrate=False)
    world.say(
        f'When the flower was safe again, {a.id} reached out. "{b.id}, come sit by me," {a.pronoun()} said.'
    )
    if world.get("room").memes["tension"] < THRESHOLD:
        world.say(
            f"{b.id} slipped off the lonely thong sandal at last and climbed into bed, and the quarrel went away as quietly as a shadow."
        )


def bedtime_end(world: World, setting: Setting, a: Entity, b: Entity, repair: Repair) -> None:
    world.say(
        f"{repair.ending}"
    )
    rel = "sisters" if a.type == "girl" and b.type == "girl" else "brothers" if a.type == "boy" and b.type == "boy" else "siblings"
    world.say(
        f"Soon the two {rel} were shoulder to shoulder under the covers, listening to the night grow softer."
    )
    world.say(
        "By the time their eyes closed, the room was gentle again, because the flower had been mended and so had their hearts."
    )


def tell(
    setting: Setting,
    holder: Holder,
    bump: Bump,
    repair: Repair,
    child_a: str,
    child_a_gender: str,
    child_b: str,
    child_b_gender: str,
    parent_type: str,
    relationship: str,
) -> World:
    world = World()
    a = world.add(Entity(id="a", kind="character", type=child_a_gender, label=child_a, role="child_a"))
    b = world.add(Entity(id="b", kind="character", type=child_b_gender, label=child_b, role="child_b"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label="room"))
    flower = world.add(Entity(id="flower", type="flower", label="daffodil", phrase="the daffodil"))
    hold = world.add(Entity(id="holder", type="holder", label=holder.label, phrase=holder.phrase))
    world.facts["display_names"] = {"a": child_a, "b": child_b}
    world.facts["relationship"] = relationship

    introduce(world, setting, a, b, holder)
    settle_in(world, a, b)

    world.para()
    elbow_bump(world, a, b, bump, holder)
    quarrel(world, a, b)

    world.para()
    soften(world, a, b)
    repair_scene(world, a, b, holder, repair, parent)

    world.para()
    bedtime_end(world, setting, a, b, repair)

    world.facts.update(
        setting=setting,
        holder_cfg=holder,
        bump_cfg=bump,
        repair_cfg=repair,
        a=a,
        b=b,
        parent=parent,
        flower=flower,
        holder=hold,
        upset=True,
        reconciled=room.memes["tension"] < THRESHOLD and a.memes["peace"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                holder=holder.id,
                bump=bump.id,
                repair=repair.id,
                child_a=child_a,
                child_a_gender=child_a_gender,
                child_b=child_b,
                child_b_gender=child_b_gender,
                parent=parent_type,
                relationship=relationship,
            )
        ),
    )
    return world


GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ava", "Lucy", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Ben", "Sam", "Noah", "Eli", "Max"]


def display_name(world: World, key: str) -> str:
    return world.facts["display_names"][key]


KNOWLEDGE = {
    "daffodil": [
        (
            "What is a daffodil?",
            "A daffodil is a yellow spring flower with a soft trumpet-shaped middle. It grows on a green stem and needs water to stay fresh.",
        )
    ],
    "elbow": [
        (
            "What is an elbow?",
            "An elbow is the part in the middle of your arm where it bends. It helps your arm fold and reach.",
        )
    ],
    "thong": [
        (
            "What is a thong sandal?",
            "A thong sandal is a flat sandal with a small strap that sits between the toes. Some families also call it a flip-flop.",
        )
    ],
    "apology": [
        (
            "Why does saying sorry help after a quarrel?",
            "A real apology shows that you know you caused hurt and want to make things better. Kind words help the other person feel safe enough to forgive.",
        )
    ],
    "water": [
        (
            "Why do cut flowers need water?",
            "Cut flowers cannot drink through roots anymore, so they need water in a cup or vase to help them stay fresh. Without water, they droop quickly.",
        )
    ],
    "trim": [
        (
            "Why might a grown-up trim a bent flower stem?",
            "Trimming removes the damaged part so the flower can sit neatly in water again. A shorter stem can still be beautiful in a small cup.",
        )
    ],
    "float": [
        (
            "Can a flower bloom float in water?",
            "Yes, some blooms can float in a shallow bowl of water for a pretty little while. It is a gentle way to enjoy a flower when the stem is damaged.",
        )
    ],
}
KNOWLEDGE_ORDER = ["daffodil", "elbow", "thong", "apology", "water", "trim", "float"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = display_name(world, "a")
    b = display_name(world, "b")
    holder = f["holder_cfg"]
    repair = f["repair_cfg"]
    return [
        'Write a gentle bedtime story for a 3-to-5-year-old that includes the words "elbow", "thong", and "daffodil", and ends in reconciliation.',
        f"Tell a sleepy story where {b} bumps a {holder.label} with an elbow, hurts {a}'s feelings, and then makes peace by helping fix the daffodil.",
        f"Write a cozy night story about a small quarrel over a flower by the bed, with an apology, {repair.label}, and a calm ending under the blankets.",
    ]


def pair_noun(a: Entity, b: Entity, relationship: str) -> str:
    if relationship == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a_ent, b_ent = f["a"], f["b"]
    a = display_name(world, "a")
    b = display_name(world, "b")
    holder = f["holder_cfg"]
    bump = f["bump_cfg"]
    repair = f["repair_cfg"]
    pair = pair_noun(a_ent, b_ent, f["relationship"])
    out = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a} and {b}, getting ready for bed with one daffodil on the bedside table. The story follows their small quarrel and the peace they make before sleep.",
        ),
        (
            "What happened to the daffodil?",
            f"{b}'s elbow bumped the {holder.label}, and water spilled around the daffodil. The bump was {bump.adjective}, so the flower drooped{', and its stem bent' if bump.bends_stem else ''}.",
        ),
        (
            f"Why were {a} and {b} upset with each other?",
            f"They were upset because the daffodil by the bed was spoiled, and both children felt hurt in the surprise of the moment. {a} blamed {b} for the elbow bump, and {b} made things worse by blaming back before calming down.",
        ),
        (
            f"How did {b} begin to fix the quarrel?",
            f"{b} began by saying sorry and admitting that the elbow bump was {b.pronoun('possessive') if False else 'their'} fault."
            if False
            else f"{b} began by saying sorry and admitting that the elbow bump was {b}'s fault. That honest apology softened the room before they even touched the flower."
        ),
        (
            "How did they fix the flower?",
            f"{repair.qa_phrase} They worked together, so the repair also became the way they made peace with each other.",
        ),
        (
            "How did the story end?",
            f"It ended quietly, with the children back together under the covers and the daffodil safe beside the bed. The ending image shows that both the flower and their friendship were mended before sleep.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"daffodil", "elbow", "thong", "apology"} | set(f["repair_cfg"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(sig[0] for sig in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        holder="teacup",
        bump="gentle",
        repair="refill",
        child_a="Lila",
        child_a_gender="girl",
        child_b="Mina",
        child_b_gender="girl",
        parent="mother",
        relationship="siblings",
    ),
    StoryParams(
        setting="attic",
        holder="teacup",
        bump="hard",
        repair="trim_reseat",
        child_a="Owen",
        child_a_gender="boy",
        child_b="Finn",
        child_b_gender="boy",
        parent="father",
        relationship="siblings",
    ),
    StoryParams(
        setting="balcony_room",
        holder="teacup",
        bump="hard",
        repair="float",
        child_a="Maya",
        child_a_gender="girl",
        child_b="Theo",
        child_b_gender="boy",
        parent="mother",
        relationship="siblings",
    ),
    StoryParams(
        setting="cottage",
        holder="jam_jar",
        bump="gentle",
        repair="refill",
        child_a="Ava",
        child_a_gender="girl",
        child_b="Ben",
        child_b_gender="boy",
        parent="father",
        relationship="siblings",
    ),
]


ASP_RULES = r"""
valid(S, H, B, R) :- setting(S), holder(H), bump(B), repair(R), compatible(H, B, R).

compatible(H, B, R) :- holder(H), bump(B), repair(R),
                       not bends(B), not needs_low(R).
compatible(H, B, R) :- holder(H), bump(B), repair(R),
                       not bends(B), needs_low(R), low(H).
compatible(H, B, R) :- holder(H), bump(B), repair(R),
                       bends(B), fixes_bent(R), not needs_low(R).
compatible(H, B, R) :- holder(H), bump(B), repair(R),
                       bends(B), fixes_bent(R), needs_low(R), low(H).

outcome(upright_again) :- chosen_repair(refill).
outcome(short_but_safe) :- chosen_repair(trim_reseat).
outcome(floating_glow) :- chosen_repair(float).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, holder in HOLDERS.items():
        lines.append(asp.fact("holder", hid))
        if holder.low:
            lines.append(asp.fact("low", hid))
    for bid, bump in BUMPS.items():
        lines.append(asp.fact("bump", bid))
        if bump.bends_stem:
            lines.append(asp.fact("bends", bid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        if repair.fixes_bent:
            lines.append(asp.fact("fixes_bent", rid))
        if repair.needs_low_holder:
            lines.append(asp.fact("needs_low", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_repair", params.repair)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("FAILED: default resolve_params raised:", err)

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
            raise StoryError("smoke test generated empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"FAILED: smoke generation crashed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a daffodil, a sleepy elbow bump, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--holder", choices=HOLDERS)
    ap.add_argument("--bump", choices=BUMPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.holder and args.bump and args.repair:
        holder = HOLDERS[args.holder]
        bump = BUMPS[args.bump]
        repair = REPAIRS[args.repair]
        if not repair_works(holder, bump, repair):
            raise StoryError(explain_rejection(holder, bump, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.holder is None or combo[1] == args.holder)
        and (args.bump is None or combo[2] == args.bump)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        if args.holder and args.bump and args.repair:
            raise StoryError(explain_rejection(HOLDERS[args.holder], BUMPS[args.bump], REPAIRS[args.repair]))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, holder_id, bump_id, repair_id = rng.choice(sorted(combos))
    a_name, a_gender = pick_child(rng)
    b_name, b_gender = pick_child(rng, avoid=a_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        holder=holder_id,
        bump=bump_id,
        repair=repair_id,
        child_a=a_name,
        child_a_gender=a_gender,
        child_b=b_name,
        child_b_gender=b_gender,
        parent=parent,
        relationship="siblings",
    )


def ensure_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.holder not in HOLDERS:
        raise StoryError(f"(No story: unknown holder '{params.holder}'.)")
    if params.bump not in BUMPS:
        raise StoryError(f"(No story: unknown bump '{params.bump}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")
    if not repair_works(HOLDERS[params.holder], BUMPS[params.bump], REPAIRS[params.repair]):
        raise StoryError(explain_rejection(HOLDERS[params.holder], BUMPS[params.bump], REPAIRS[params.repair]))


def generate(params: StoryParams) -> StorySample:
    ensure_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        holder=HOLDERS[params.holder],
        bump=BUMPS[params.bump],
        repair=REPAIRS[params.repair],
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        parent_type=params.parent,
        relationship=params.relationship,
    )

    story = world.render()
    a_name = display_name(world, "a")
    b_name = display_name(world, "b")
    story = story.replace("a", a_name, 1) if False else story
    # Replace internal ids only in the rendered prose.
    story = story.replace("a's", f"{a_name}'s")
    story = story.replace("b's", f"{b_name}'s")
    story = story.replace(" a ", f" {a_name} ")
    story = story.replace(" b ", f" {b_name} ")
    story = story.replace('"a,', f'"{a_name},')
    story = story.replace('"b,', f'"{b_name},')
    story = story.replace('"a"', f'"{a_name}"')
    story = story.replace('"b"', f'"{b_name}"')
    story = story.replace(" a.", f" {a_name}.")
    story = story.replace(" b.", f" {b_name}.")
    story = story.replace(" a)", f" {a_name})")
    story = story.replace(" b)", f" {b_name})")
    story = story.replace(" a]", f" {a_name}]")
    story = story.replace(" b]", f" {b_name}]")
    story = story.replace(" a,", f" {a_name},")
    story = story.replace(" b,", f" {b_name},")
    story = story.replace(" a?", f" {a_name}?")
    story = story.replace(" b?", f" {b_name}?")
    story = story.replace(" a!", f" {a_name}!")
    story = story.replace(" b!", f" {b_name}!")
    story = story.replace(" a;", f" {a_name};")
    story = story.replace(" b;", f" {b_name};")
    story = story.replace(" a:", f" {a_name}:")
    story = story.replace(" b:", f" {b_name}:")
    story = story.replace("\na ", f"\n{a_name} ")
    story = story.replace("\nb ", f"\n{b_name} ")
    story = story.replace(" A ", f" {a_name} ")
    story = story.replace(" B ", f" {b_name} ")

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
        print(f"{len(combos)} compatible (setting, holder, bump, repair) combos:\n")
        for setting_id, holder_id, bump_id, repair_id in combos:
            print(f"  {setting_id:13} {holder_id:12} {bump_id:7} {repair_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} & {p.child_b}: {p.bump} bump, {p.repair} ending"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
