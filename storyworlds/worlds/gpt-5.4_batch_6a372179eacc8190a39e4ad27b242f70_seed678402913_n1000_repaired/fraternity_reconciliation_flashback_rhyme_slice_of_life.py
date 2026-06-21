#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py
=====================================================================================

A standalone storyworld about two fraternity brothers getting ready for a small
house event, stumbling into a hurtful argument, remembering an earlier kind
moment, and repairing both the room and their friendship. The stories stay close
to slice-of-life scenes: a hallway, a table, a paper banner, a tray of snacks,
and a simple welcome rhyme.

Core shape
----------
- typed entities with physical meters and emotional memes
- a small reasonableness gate over mishaps, repairs, and apology styles
- a flashback beat driven by a memory cue in the simulated world
- a rhyme beat driven by the repaired welcome line
- an inline ASP twin for the constraint gate and outcome model

Run it
------
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py --qa
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py --json
python storyworlds/worlds/gpt-5.4/fraternity_reconciliation_flashback_rhyme_slice_of_life.py --verify
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "student_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    id: str
    event: str
    room: str
    table_item: str
    memory_item: str
    rhyme_a: str
    rhyme_b: str
    closing_image: str
    memory_boost: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    damage: str
    severity: int
    trigger_text: str
    hurt_text: str
    object_label: str
    repair_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    covers: set[str] = field(default_factory=set)
    power: int = 1
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Apology:
    id: str
    sense: int = 2
    warmth: int = 2
    text: str = ""
    follow_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    mishap: str
    repair: str
    apology: str
    brother1: str
    brother2: str
    house_name: str
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    decor = world.get("decor")
    if decor.meters["damaged"] < THRESHOLD:
        return out
    sig = ("damage", "decor")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.get("room")
    room.meters["readiness"] -= 1
    for eid in ("a", "b"):
        world.get(eid).memes["stress"] += 1
    out.append("__damage__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    cue = world.get("cue")
    if cue.meters["noticed"] < THRESHOLD:
        return out
    sig = ("flashback", "cue")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boost = int(world.facts.get("memory_boost", 1))
    for eid in ("a", "b"):
        world.get(eid).memes["memory"] += boost
        world.get(eid).memes["softness"] += 1
    out.append("__flashback__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("a")
    b = world.get("b")
    decor = world.get("decor")
    if a.memes["apologized"] < THRESHOLD:
        return out
    if decor.meters["fixed"] < THRESHOLD:
        return out
    sig = ("reconcile", "pair")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    soften = a.memes["memory"] + a.memes["care"] + a.memes["apology_warmth"]
    if soften >= world.facts["hurt_need"]:
        a.memes["warmth"] += 1
        b.memes["warmth"] += 1
        a.memes["hurt"] = 0.0
        b.memes["hurt"] = 0.0
        world.facts["outcome"] = "warm"
    else:
        a.memes["warmth"] += 0.5
        b.memes["warmth"] += 0.5
        b.memes["hurt"] = max(0.0, b.memes["hurt"] - 1.0)
        world.facts["outcome"] = "quiet"
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


SCENES = {
    "open_house": Scene(
        id="open_house",
        event="a welcome night for new students",
        room="the front hall",
        table_item="a pitcher of lemon water and a bowl of pretzels",
        memory_item="an old photo from last autumn's service day",
        rhyme_a="share",
        rhyme_b="care",
        closing_image="the front hall glowed softly while the first guests shook off the evening chill",
        memory_boost=2,
        tags={"fraternity", "welcome", "rhyme"},
    ),
    "study_table": Scene(
        id="study_table",
        event="a quiet study hour before exams",
        room="the long dining room",
        table_item="stacks of index cards and a plate of clementines",
        memory_item="a bent snapshot from the night they tutored first-years together",
        rhyme_a="read",
        rhyme_b="lead",
        closing_image="lamps shone on open notebooks as the house settled into a calm hum",
        memory_boost=1,
        tags={"fraternity", "study", "rhyme"},
    ),
    "soup_night": Scene(
        id="soup_night",
        event="a simple soup supper for the block",
        room="the kitchen doorway and the little side table nearby",
        table_item="a pot of tomato soup and a basket of bread",
        memory_item="a faded picture of them ladling soup in matching aprons",
        rhyme_a="bowl",
        rhyme_b="soul",
        closing_image="steam curled up from the soup while neighbors smiled in from the porch",
        memory_boost=2,
        tags={"fraternity", "meal", "rhyme"},
    ),
}

MISHAPS = {
    "torn_banner": Mishap(
        id="torn_banner",
        damage="tear",
        severity=2,
        trigger_text="When they both reached for the paper banner at once, one corner ripped with a sad little rrip.",
        hurt_text="Eli had lettered the middle line by hand, so the tear felt like someone had yanked right through his careful work.",
        object_label="paper banner",
        repair_need="tear",
        tags={"paper", "banner"},
    ),
    "smeared_paint": Mishap(
        id="smeared_paint",
        damage="smear",
        severity=2,
        trigger_text="A sleeve brushed the still-wet paint, and the bright letters dragged into a blue blur.",
        hurt_text="The blur landed across the line Theo had spent all afternoon spacing just right, and his face went tight at once.",
        object_label="painted sign",
        repair_need="smear",
        tags={"paint", "sign"},
    ),
    "fallen_letters": Mishap(
        id="fallen_letters",
        damage="loose",
        severity=1,
        trigger_text="The tape gave up, and a row of cutout letters slid down the wall and onto the floor.",
        hurt_text="Max had trimmed every curve with tiny scissors, so seeing the letters sag made him feel as if his effort had slipped with them.",
        object_label="lettered welcome sign",
        repair_need="loose",
        tags={"paper", "letters"},
    ),
}

REPAIRS = {
    "tape_patch": Repair(
        id="tape_patch",
        covers={"tear", "loose"},
        power=2,
        text="smoothed the ripped edge flat and patched the back with neat strips of tape",
        qa_text="patched the paper carefully with tape",
        tags={"tape", "paper"},
    ),
    "fresh_paint": Repair(
        id="fresh_paint",
        covers={"smear"},
        power=2,
        text="painted a clean card over the messy part and wrote the line again in steady strokes",
        qa_text="covered the smeared part and painted the line again",
        tags={"paint", "brush"},
    ),
    "glue_reset": Repair(
        id="glue_reset",
        covers={"loose"},
        power=1,
        text="set each fallen letter back in place with glue and pressed the corners down with patient thumbs",
        qa_text="glued the loose letters back in place",
        tags={"glue", "paper"},
    ),
}

APOLOGIES = {
    "plain_honest": Apology(
        id="plain_honest",
        sense=2,
        warmth=2,
        text='"I was in a hurry, and I made it worse. I am sorry,"',
        follow_text="The words were plain, but they landed where they needed to land.",
        qa_text="gave a plain, honest apology",
        tags={"apology"},
    ),
    "specific_memory": Apology(
        id="specific_memory",
        sense=3,
        warmth=3,
        text='"I forgot this mattered to you because you always care so much. I am sorry, and I want to fix it with you,"',
        follow_text="Because he named the hurt and offered his hands too, the apology felt warm instead of thin.",
        qa_text="gave a warm apology that named the hurt and offered help",
        tags={"apology", "memory"},
    ),
    "make_amends": Apology(
        id="make_amends",
        sense=3,
        warmth=2,
        text='"I messed up. Let me do the careful part this time while you tell me how you want it,"',
        follow_text="It sounded less like a speech and more like a promise to do better right away.",
        qa_text="apologized and immediately offered to make amends",
        tags={"apology", "repair"},
    ),
    "shrug_it_off": Apology(
        id="shrug_it_off",
        sense=1,
        warmth=0,
        text='"It is only paper. Forget it,"',
        follow_text="The words brushed the hurt aside instead of mending it.",
        qa_text="shrugged the problem off",
        tags={"bad_apology"},
    ),
}

BROTHER_NAMES = ["Eli", "Theo", "Max", "Jonah", "Miles", "Noah", "Owen", "Caleb", "Simon", "Luke"]
HOUSE_NAMES = ["Maple House", "River House", "Elm House", "Harbor House"]


def repair_can_fix(mishap: Mishap, repair: Repair) -> bool:
    return mishap.repair_need in repair.covers and repair.power >= mishap.severity


def sensible_apologies() -> list[Apology]:
    return [a for a in APOLOGIES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for mishap_id, mishap in MISHAPS.items():
            for repair_id, repair in REPAIRS.items():
                if not repair_can_fix(mishap, repair):
                    continue
                for apology_id, apology in APOLOGIES.items():
                    if apology.sense >= SENSE_MIN:
                        combos.append((scene_id, mishap_id, repair_id, apology_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    scene = SCENES[params.scene]
    mishap = MISHAPS[params.mishap]
    apology = APOLOGIES[params.apology]
    comfort = scene.memory_boost + apology.warmth + 1
    hurt_need = mishap.severity + 2
    return "warm" if comfort >= hurt_need else "quiet"


def explain_repair(mishap: Mishap, repair: Repair) -> str:
    wants = mishap.repair_need
    covers = ", ".join(sorted(repair.covers))
    return (
        f"(No story: {repair.id} is not a good fix for a {mishap.damage}. "
        f"This mishap needs help with {wants}, but that repair only covers {covers}.)"
    )


def explain_apology(apology_id: str) -> str:
    apology = APOLOGIES[apology_id]
    good = ", ".join(sorted(a.id for a in sensible_apologies()))
    return (
        f"(Refusing apology '{apology_id}': it is too dismissive for a reconciliation story "
        f"(sense={apology.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


def predict_reconciliation(scene: Scene, mishap: Mishap, apology: Apology) -> dict:
    comfort = scene.memory_boost + apology.warmth + 1
    hurt_need = mishap.severity + 2
    return {"comfort": comfort, "hurt_need": hurt_need, "warm": comfort >= hurt_need}


def setup_scene(world: World, scene: Scene, a: Entity, b: Entity) -> None:
    for eid in ("a", "b"):
        world.get(eid).memes["belonging"] += 1
    room = world.get("room")
    room.meters["readiness"] = 1
    world.say(
        f"After classes, {a.id} and {b.id} moved around {scene.room} of {world.facts['house_name']}, "
        f"their fraternity house, getting ready for {scene.event}."
    )
    world.say(
        f"On the table sat {scene.table_item}, and across the wall hung the welcome piece they were still finishing."
    )
    world.say(
        f'They had chosen a line that would end with a little rhyme: "{scene.rhyme_a} and {scene.rhyme_b}."'
    )


def spark_conflict(world: World, mishap: Mishap, a: Entity, b: Entity) -> None:
    decor = world.get("decor")
    decor.meters["damaged"] += 1
    b.memes["hurt"] += mishap.severity
    a.memes["regret"] += 1
    world.facts["hurt_need"] = mishap.severity + 2
    propagate(world, narrate=False)
    world.say(mishap.trigger_text)
    world.say(mishap.hurt_text)
    world.say(
        f'"Slow down," {b.id} said, too sharply. "{mishap.object_label.capitalize()} do not fix themselves."'
    )
    world.say(
        f"{a.id} opened his mouth to answer, but the room had already gone small and sore."
    )


def notice_memory_cue(world: World, scene: Scene, a: Entity, b: Entity) -> None:
    cue = world.get("cue")
    cue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {a.id} glanced at {scene.memory_item} by the shelf and stopped."
    )
    world.say(
        f"In the picture, he and {b.id} were shoulder to shoulder, both grinning over another crooked sign they had fixed together."
    )
    world.say(
        f"For a moment the hall felt like that earlier evening again: tired feet, sticky fingers, and both of them laughing when their first rhyme came out lopsided."
    )


def apologize(world: World, apology: Apology, a: Entity, b: Entity) -> None:
    a.memes["apologized"] += 1
    a.memes["apology_warmth"] += apology.warmth
    a.memes["care"] += 1
    world.say(f"{a.id} took a breath. {apology.text}")
    world.say(apology.follow_text)
    if b.memes["memory"] >= THRESHOLD:
        world.say(
            f"{b.id}'s shoulders came down a little. He was still hurt, but he was listening now."
        )


def do_repair(world: World, repair: Repair, a: Entity, b: Entity, scene: Scene) -> None:
    decor = world.get("decor")
    decor.meters["fixed"] += 1
    decor.meters["damaged"] = 0.0
    world.get("room").meters["readiness"] = 1
    world.say(
        f"Side by side again, they {repair.text}."
    )
    world.say(
        f'Soon the new line sat straight and clear: "{scene.rhyme_a} and {scene.rhyme_b}."'
    )
    propagate(world, narrate=False)


def ending(world: World, scene: Scene, a: Entity, b: Entity) -> None:
    outcome = world.facts.get("outcome", "quiet")
    if outcome == "warm":
        world.say(
            f'{b.id} read the line once, then gave a small smile. "{scene.rhyme_a.capitalize()} and {scene.rhyme_b}," he said. "That sounds like us again."'
        )
        world.say(
            f"{a.id} laughed softly, and this time {b.id} laughed too."
        )
    else:
        world.say(
            f'{b.id} touched the neat edge of the sign and nodded. "That is better," he said.'
        )
        world.say(
            f"The hurt was not all gone at once, but there was room for them to stand beside each other again."
        )
    world.say(
        f"When the first knock came at the door, {scene.closing_image}."
    )


def tell(
    scene: Scene,
    mishap: Mishap,
    repair: Repair,
    apology: Apology,
    brother1: str,
    brother2: str,
    house_name: str,
) -> World:
    world = World()
    a = world.add(Entity(id="a", kind="character", type="student_man", label=brother1, role="instigator"))
    b = world.add(Entity(id="b", kind="character", type="student_man", label=brother2, role="hurt"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=scene.room))
    decor = world.add(Entity(id="decor", kind="thing", type="decor", label=mishap.object_label))
    cue = world.add(Entity(id="cue", kind="thing", type="photo", label=scene.memory_item))
    a.id = brother1
    b.id = brother2
    world.entities["a"] = a
    world.entities["b"] = b
    world.entities[brother1] = world.entities.pop("a")
    world.entities[brother2] = world.entities.pop("b")
    world.entities["a"] = world.entities[brother1]
    world.entities["b"] = world.entities[brother2]

    world.facts.update(
        scene=scene,
        mishap=mishap,
        repair=repair,
        apology=apology,
        house_name=house_name,
        memory_boost=scene.memory_boost,
        hurt_need=mishap.severity + 2,
    )

    a = world.get("a")
    b = world.get("b")

    setup_scene(world, scene, a, b)
    world.para()
    spark_conflict(world, mishap, a, b)
    world.para()
    notice_memory_cue(world, scene, a, b)
    apologize(world, apology, a, b)
    do_repair(world, repair, a, b, scene)
    world.para()
    ending(world, scene, a, b)

    world.facts.update(
        brother1=a,
        brother2=b,
        room=room,
        decor=decor,
        cue=cue,
        reconciled=world.facts.get("outcome") in {"warm", "quiet"},
        rhyme=f"{scene.rhyme_a} and {scene.rhyme_b}",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    mishap = world.facts["mishap"]
    a = world.facts["brother1"]
    b = world.facts["brother2"]
    return [
        f'Write a slice-of-life story that includes the word "fraternity" and shows two house brothers fixing a small hurt before {scene.event}.',
        f"Tell a gentle reconciliation story where {a.id} and {b.id} damage a welcome display, pause for a flashback, and end by sharing a short rhyme.",
        f"Write a quiet everyday story set in a fraternity house, with a paper mishap, an honest apology, and a warm ending at the door.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    scene = world.facts["scene"]
    mishap = world.facts["mishap"]
    repair = world.facts["repair"]
    apology = world.facts["apology"]
    a = world.facts["brother1"]
    b = world.facts["brother2"]
    outcome = world.facts.get("outcome", "quiet")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two fraternity brothers, {a.id} and {b.id}, getting their house ready for {scene.event}. They start the story working together, even though that teamwork gets shaky for a while.",
        ),
        (
            "What went wrong?",
            f"{mishap.trigger_text} {mishap.hurt_text} The problem was small in size, but it mattered because the sign held careful work and shared pride.",
        ),
        (
            "What was the flashback about?",
            f"The flashback came when {a.id} noticed {scene.memory_item}. It reminded both brothers that they had fixed another crooked sign together before, so the memory softened the argument.",
        ),
        (
            f"How did {a.id} try to make things better?",
            f"{a.id} {apology.qa_text} and then he helped repair the display. The apology mattered because it named the hurt instead of pretending nothing had happened.",
        ),
        (
            "What rhyme did they keep on the sign?",
            f'They kept the line "{world.facts["rhyme"]}." The rhyme gave the finished sign a friendly sound and showed they were making something together again.',
        ),
    ]
    if outcome == "warm":
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly. Once the sign was fixed, {b.id} smiled and the two brothers laughed together again, and the first guests arrived to a room that felt ready and kind.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly but hopefully. The brothers were not instantly carefree, yet the repaired sign and the shared work made enough space for them to stand together when the first guests arrived.",
            )
        )
    qa.append(
        (
            f"How did they fix the {mishap.object_label}?",
            f"They {repair.qa_text}. Doing the careful repair together turned the apology into action, which helped the reconciliation feel real.",
        )
    )
    return qa


KNOWLEDGE = {
    "fraternity": [
        (
            "What is a fraternity house?",
            "A fraternity house is a home shared by college students who belong to the same group. They may study, eat, and host small events there together.",
        )
    ],
    "apology": [
        (
            "Why can an honest apology help?",
            "An honest apology helps because it shows you understand the hurt you caused. When you also try to fix the problem, the other person has a reason to trust your words.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look at an earlier moment. Writers use it to show how the past changes what a character feels right now.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme happens when words end with the same or a very similar sound, like share and care. Rhymes can make signs, songs, and poems easier to remember.",
        )
    ],
    "paper": [
        (
            "Why do paper signs tear easily?",
            "Paper is thin, so if two people pull it at once or tape it badly, it can rip. That is why careful hands matter when you make decorations.",
        )
    ],
    "paint": [
        (
            "Why does wet paint smear?",
            "Wet paint has not dried yet, so a sleeve or hand can drag it across the page. The color moves before it has time to stay in one place.",
        )
    ],
    "glue": [
        (
            "What does glue do?",
            "Glue helps light things stick together by drying tacky and firm. It works best when you press the pieces down and give them a little time.",
        )
    ],
    "tape": [
        (
            "What does tape do for torn paper?",
            "Tape can hold a torn edge together and keep the rip from spreading. It works especially well when the paper is smoothed flat first.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fraternity", "flashback", "rhyme", "apology", "paper", "paint", "glue", "tape"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fraternity", "flashback", "rhyme"} | set(world.facts["apology"].tags) | set(world.facts["mishap"].tags) | set(world.facts["repair"].tags)
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
    for key, ent in world.entities.items():
        if key not in {ent.id, "a", "b", "room", "decor", "cue"}:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {key:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome', '?')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="open_house",
        mishap="torn_banner",
        repair="tape_patch",
        apology="specific_memory",
        brother1="Eli",
        brother2="Theo",
        house_name="Maple House",
    ),
    StoryParams(
        scene="study_table",
        mishap="smeared_paint",
        repair="fresh_paint",
        apology="make_amends",
        brother1="Max",
        brother2="Jonah",
        house_name="River House",
    ),
    StoryParams(
        scene="soup_night",
        mishap="fallen_letters",
        repair="glue_reset",
        apology="plain_honest",
        brother1="Miles",
        brother2="Owen",
        house_name="Elm House",
    ),
    StoryParams(
        scene="open_house",
        mishap="fallen_letters",
        repair="tape_patch",
        apology="make_amends",
        brother1="Noah",
        brother2="Caleb",
        house_name="Harbor House",
    ),
]


ASP_RULES = r"""
sensible_apology(A) :- apology(A), sense(A, S), sense_min(M), S >= M.
fixes(R, M) :- repair(R), mishap(M), need(M, D), covers(R, D), power(R, P), severity(M, Sev), P >= Sev.
valid(S, M, R, A) :- scene(S), mishap(M), repair(R), apology(A), fixes(R, M), sensible_apology(A).

comfort(V) :- chosen_scene(S), memory_boost(S, B), chosen_apology(A), warmth(A, W), V = B + W + 1.
hurt_need(V) :- chosen_mishap(M), severity(M, Sev), V = Sev + 2.
warm :- comfort(C), hurt_need(H), C >= H.
outcome(warm) :- warm.
outcome(quiet) :- not warm.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        lines.append(asp.fact("memory_boost", scene_id, scene.memory_boost))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        lines.append(asp.fact("need", mishap_id, mishap.repair_need))
        lines.append(asp.fact("severity", mishap_id, mishap.severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("power", repair_id, repair.power))
        for cover in sorted(repair.covers):
            lines.append(asp.fact("covers", repair_id, cover))
    for apology_id, apology in APOLOGIES.items():
        lines.append(asp.fact("apology", apology_id))
        lines.append(asp.fact("sense", apology_id, apology.sense))
        lines.append(asp.fact("warmth", apology_id, apology.warmth))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_apologies() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_apology/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_apology"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_scene", params.scene),
            asp.fact("chosen_mishap", params.mishap),
            asp.fact("chosen_apology", params.apology),
        ]
    )
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

    clingo_ap = set(asp_sensible_apologies())
    python_ap = {a.id for a in sensible_apologies()}
    if clingo_ap == python_ap:
        print(f"OK: sensible apologies match ({sorted(clingo_ap)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible apologies: clingo={sorted(clingo_ap)} python={sorted(python_ap)}")

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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: generated story was empty.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: fraternity brothers repair a small hurt with a flashback and a rhyme."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--brother1")
    ap.add_argument("--brother2")
    ap.add_argument("--house-name", choices=HOUSE_NAMES)
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


def pick_two_names(rng: random.Random) -> tuple[str, str]:
    return tuple(rng.sample(BROTHER_NAMES, 2))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.apology and APOLOGIES[args.apology].sense < SENSE_MIN:
        raise StoryError(explain_apology(args.apology))
    if args.mishap and args.repair:
        mishap = MISHAPS[args.mishap]
        repair = REPAIRS[args.repair]
        if not repair_can_fix(mishap, repair):
            raise StoryError(explain_repair(mishap, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.mishap is None or combo[1] == args.mishap)
        and (args.repair is None or combo[2] == args.repair)
        and (args.apology is None or combo[3] == args.apology)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, mishap_id, repair_id, apology_id = rng.choice(sorted(combos))
    brother1 = args.brother1
    brother2 = args.brother2
    if brother1 and brother2 and brother1 == brother2:
        raise StoryError("(No story: brother1 and brother2 should be different names.)")
    if brother1 is None or brother2 is None:
        picked1, picked2 = pick_two_names(rng)
        brother1 = brother1 or picked1
        brother2 = brother2 or (picked2 if picked2 != brother1 else rng.choice([n for n in BROTHER_NAMES if n != brother1]))
    house_name = args.house_name or rng.choice(HOUSE_NAMES)
    return StoryParams(
        scene=scene_id,
        mishap=mishap_id,
        repair=repair_id,
        apology=apology_id,
        brother1=brother1,
        brother2=brother2,
        house_name=house_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {params.mishap})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(Unknown apology: {params.apology})")

    scene = SCENES[params.scene]
    mishap = MISHAPS[params.mishap]
    repair = REPAIRS[params.repair]
    apology = APOLOGIES[params.apology]
    if apology.sense < SENSE_MIN:
        raise StoryError(explain_apology(params.apology))
    if not repair_can_fix(mishap, repair):
        raise StoryError(explain_repair(mishap, repair))
    if params.brother1 == params.brother2:
        raise StoryError("(No story: the two brothers need different names.)")

    world = tell(
        scene=scene,
        mishap=mishap,
        repair=repair,
        apology=apology,
        brother1=params.brother1,
        brother2=params.brother2,
        house_name=params.house_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible_apology/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible apologies: {', '.join(asp_sensible_apologies())}\n")
        print(f"{len(combos)} compatible (scene, mishap, repair, apology) combos:\n")
        for scene_id, mishap_id, repair_id, apology_id in combos:
            print(f"  {scene_id:12} {mishap_id:14} {repair_id:12} {apology_id}")
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
            header = f"### {p.brother1} & {p.brother2}: {p.scene}, {p.mishap}, {p.repair}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
