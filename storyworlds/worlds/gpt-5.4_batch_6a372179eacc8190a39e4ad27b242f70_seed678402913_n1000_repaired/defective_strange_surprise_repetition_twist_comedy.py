#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py
================================================================================

A small story world about a child, a very silly toy, and a defect that turns
into a comic surprise. The toy behaves in a strange, repetitive way; everyone
thinks the show is ruined; then the repeated mishap reveals the very thing the
family was missing.

Run it
------
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py --toy robot --defect reverse_gear --surprise hat_box
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py --surprise bell_basket
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py --all
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/defective_strange_surprise_repetition_twist_comedy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
REPEAT_COUNT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    motion: str
    sound: str
    opening: str
    ending: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Defect:
    id: str
    label: str
    strange_line: str
    repeat_line: str
    reveal_trigger: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    hiding_place: str
    reveal_text: str
    ending_use: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Room:
    id: str
    label: str
    scene: str
    show_goal: str


@dataclass
class StoryParams:
    toy: str
    defect: str
    surprise: str
    room: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
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

    def record(self, tag: str) -> None:
        self.history.append(tag)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_reveal(world: World) -> list[str]:
    toy = world.get("toy")
    surprise = world.get("surprise")
    out: list[str] = []
    if toy.meters["repeat_count"] < REPEAT_COUNT:
        return out
    if surprise.meters["found"] >= THRESHOLD:
        return out
    sig = ("reveal", world.facts["defect"].id, world.facts["surprise"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    surprise.meters["found"] += 1
    toy.memes["pride"] += 1
    world.get("child").memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    world.get("parent").memes["relief"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule(name="reveal_surprise", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


TOYS = {
    "robot": Toy(
        id="robot",
        label="robot trumpeter",
        phrase="a shiny robot trumpeter",
        motion="rolled across the floor",
        sound="toot",
        opening="Its little silver hat winked in the light.",
        ending="The robot puffed out its tiny trumpet as if it knew it had saved the show.",
        supports={"reverse_gear", "jumpy_spring"},
        tags={"toy", "robot", "windup"},
    ),
    "duck": Toy(
        id="duck",
        label="duck bandleader",
        phrase="a yellow duck bandleader",
        motion="waddled proudly",
        sound="quack",
        opening="Its painted beak looked ready to boss the whole room around.",
        ending="The duck marched at the front like the smallest, noisiest parade captain in town.",
        supports={"reverse_gear", "spinny_wheel"},
        tags={"toy", "duck", "windup"},
    ),
    "monkey": Toy(
        id="monkey",
        label="monkey drummer",
        phrase="a fuzzy monkey drummer",
        motion="banged its drum and bobbed",
        sound="rat-a-tat",
        opening="Its round drum was almost bigger than its belly.",
        ending="The monkey drummed so proudly that everybody bowed to it at the end.",
        supports={"jumpy_spring", "spinny_wheel"},
        tags={"toy", "monkey", "windup"},
    ),
}

DEFECTS = {
    "reverse_gear": Defect(
        id="reverse_gear",
        label="reverse gear",
        strange_line="Instead of going forward, the toy scooted backward with a very serious face.",
        repeat_line='Back it went again: "{sound}! {sound}! {sound}!"',
        reveal_trigger="under_sofa",
        fix="turned a tiny gear the right way with a butter-knife handle",
        tags={"defective", "gears", "backward"},
    ),
    "jumpy_spring": Defect(
        id="jumpy_spring",
        label="jumpy spring",
        strange_line="The toy gave a strange hop, as if its spring had swallowed a hiccup.",
        repeat_line='Hop, bump, "{sound}!" Hop, bump, "{sound}!"',
        reveal_trigger="table_shake",
        fix="settled the jumpy spring back into its little notch",
        tags={"defective", "spring", "bouncy"},
    ),
    "spinny_wheel": Defect(
        id="spinny_wheel",
        label="spinny wheel",
        strange_line="One wheel stuck, and the toy spun in a very strange little circle.",
        repeat_line='Round and round it went: "{sound}! {sound}!"',
        reveal_trigger="curtain_tug",
        fix="picked a bit of ribbon from the wheel and freed it",
        tags={"defective", "wheel", "spinning"},
    ),
}

SURPRISES = {
    "hat_box": Surprise(
        id="hat_box",
        label="hat box",
        phrase="the missing party-hat box",
        hiding_place="under the sofa",
        reveal_text="A round box slid out from under the sofa and bumped the wall. Inside were the missing paper hats.",
        ending_use="Everyone put on a silly paper hat at once.",
        trigger="under_sofa",
        tags={"surprise", "hat", "party"},
    ),
    "bell_basket": Surprise(
        id="bell_basket",
        label="bell basket",
        phrase="the lost basket of ankle bells",
        hiding_place="on the side table",
        reveal_text="The table wiggled, and a little basket tipped over. Out spilled the lost ankle bells with a bright jingle.",
        ending_use="Soon there were bells on wrists, knees, and even one looped over the toy's neck.",
        trigger="table_shake",
        tags={"surprise", "bells", "music"},
    ),
    "ribbon_bundle": Surprise(
        id="ribbon_bundle",
        label="ribbon bundle",
        phrase="the missing rainbow ribbon bundle",
        hiding_place="behind the curtain",
        reveal_text="The curtain twitched, and a bundle of rainbow ribbons flopped down like a sleepy bird.",
        ending_use="The ribbons were tied to spoons, chairs, and the toy itself until the whole room looked ready to laugh.",
        trigger="curtain_tug",
        tags={"surprise", "ribbon", "decorations"},
    ),
}

ROOMS = {
    "living_room": Room(
        id="living_room",
        label="living room",
        scene="The cushions had been lined up like seats for a grand tiny theater.",
        show_goal="a ridiculous family parade",
    ),
    "kitchen": Room(
        id="kitchen",
        label="kitchen",
        scene="The bright floor shone like a stage, and wooden spoons waited in a jar like extra musicians.",
        show_goal="a supper-time marching show",
    ),
    "playroom": Room(
        id="playroom",
        label="playroom",
        scene="Blocks stood in rows like a patient audience waiting for something silly to happen.",
        show_goal="the funniest toy concert of the week",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["cheerful", "curious", "giggly", "dramatic", "hopeful", "bouncy"]


def valid_combo(toy_id: str, defect_id: str, surprise_id: str) -> bool:
    if toy_id not in TOYS or defect_id not in DEFECTS or surprise_id not in SURPRISES:
        return False
    toy = TOYS[toy_id]
    defect = DEFECTS[defect_id]
    surprise = SURPRISES[surprise_id]
    return defect_id in toy.supports and defect.reveal_trigger == surprise.trigger


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for toy_id in sorted(TOYS):
        for defect_id in sorted(DEFECTS):
            for surprise_id in sorted(SURPRISES):
                if valid_combo(toy_id, defect_id, surprise_id):
                    out.append((toy_id, defect_id, surprise_id))
    return out


def explain_rejection(toy_id: str, defect_id: str, surprise_id: str) -> str:
    if toy_id not in TOYS:
        return f"(No story: unknown toy '{toy_id}'.)"
    if defect_id not in DEFECTS:
        return f"(No story: unknown defect '{defect_id}'.)"
    if surprise_id not in SURPRISES:
        return f"(No story: unknown surprise '{surprise_id}'.)"
    toy = TOYS[toy_id]
    defect = DEFECTS[defect_id]
    surprise = SURPRISES[surprise_id]
    if defect_id not in toy.supports:
        supported = ", ".join(sorted(toy.supports))
        return (
            f"(No story: {toy.label} is not a reasonable match for {defect.label}. "
            f"That toy only supports: {supported}.)"
        )
    return (
        f"(No story: {defect.label} would reveal something from {defect.reveal_trigger}, "
        f"but {surprise.phrase} is hidden at {surprise.hiding_place}. "
        f"The twist has to follow from the toy's actual mishap.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def introduce(world: World, child: Entity, helper: Entity, parent: Entity, room: Room) -> None:
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} were in the {room.label} with "
        f"{room.show_goal} in mind. {room.scene}"
    )
    world.say(
        f"{child.id} was a {world.facts['trait']} {child.type} who believed almost any ordinary day "
        f"could be improved by a drumroll."
    )
    world.say(
        f'{helper.id} agreed. "{room.show_goal.capitalize()}!" {helper.id} said, as if that settled everything.'
    )
    world.say(
        f"{child.id}'s {parent.label_word} smiled from nearby and promised to watch the whole performance."
    )


def give_toy(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["wound"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Then {child.id}'s {parent.label_word} set down {toy.phrase}. {toy.opening}"
    )
    world.say(
        f'{child.id} clapped. "This will be perfect for our show," {child.pronoun()} said.'
    )


def start_show(world: World, child: Entity, helper: Entity, toy: Toy) -> None:
    world.say(
        f"{child.id} wound the toy, set it on the floor, and everyone leaned in."
    )
    world.say(
        f"At first it {toy.motion}, exactly as a little parade toy ought to do."
    )
    helper.memes["hope"] += 1
    child.memes["hope"] += 1


def first_strange_beat(world: World, child: Entity, helper: Entity, toy: Toy, defect: Defect) -> None:
    world.get("toy").meters["defective"] += 1
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"But then something defective inside clicked the wrong way. {defect.strange_line}"
    )
    world.say(
        f'{helper.id} blinked. "That is strange," {helper.pronoun()} said.'
    )
    world.record("defect_seen")


def repeat_mishap(world: World, child: Entity, helper: Entity, toy: Toy, defect: Defect, idx: int) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["repeat_count"] += 1
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    child.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    line = defect.repeat_line.format(sound=toy.sound)
    if idx == 1:
        world.say(f"{line} Everyone stared.")
    elif idx == 2:
        world.say(f"{line} {child.id} put both hands over {child.pronoun('possessive')} mouth and began to giggle.")
    else:
        world.say(f"{line} By now even the grown-up was trying not to laugh.")
    world.record(f"repeat_{idx}")
    propagate(world, narrate=False)


def reveal_surprise(world: World, parent: Entity, surprise: Surprise) -> None:
    world.say(
        f"Then came the surprise. {surprise.reveal_text}"
    )
    world.say(
        f'{parent.label_word.capitalize()} laughed first. "So that is where it was!" {parent.pronoun()} said.'
    )
    world.record("surprise_found")


def twist(world: World, child: Entity, helper: Entity, toy: Toy, defect: Defect, surprise: Surprise) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"For one moment, {child.id} had thought the show was spoiled by a broken toy."
    )
    world.say(
        f"Instead, the very same strange mistake had found {surprise.phrase}. That was the twist, and it was too funny not to cheer."
    )
    world.record("twist")


def fix_toy(world: World, parent: Entity, defect: Defect) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["fixed"] += 1
    parent.memes["care"] += 1
    world.say(
        f"After the laughing slowed down, {parent.label_word} knelt beside the toy and {defect.fix}."
    )
    world.say(
        f"The next time it moved, it behaved much better, though everyone agreed it had been more memorable before."
    )
    world.record("fixed")


def finale(world: World, child: Entity, helper: Entity, toy: Toy, surprise: Surprise) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{surprise.ending_use} Soon the room was full of marching feet, silly noises, and the kind of laughing that makes people wobble."
    )
    world.say(
        f"{toy.ending} {child.id} bowed, {helper.id} bowed lower, and even the once-defective toy seemed pleased with itself."
    )
    world.say(
        "Nobody called it ruined anymore. They called it the funniest rehearsal helper in the house."
    )
    world.record("ending")


def tell(
    room: Room,
    toy_cfg: Toy,
    defect_cfg: Defect,
    surprise_cfg: Surprise,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=toy_cfg.label, phrase=toy_cfg.phrase, tags=set(toy_cfg.tags)))
    surprise = world.add(Entity(id="surprise", kind="thing", type="surprise", label=surprise_cfg.label, phrase=surprise_cfg.phrase, tags=set(surprise_cfg.tags)))

    world.facts.update(
        room=room,
        toy_cfg=toy_cfg,
        defect=defect_cfg,
        surprise=surprise_cfg,
        trait=trait,
        child=child,
        helper=helper,
        parent=parent,
        toy=toy,
        surprise_ent=surprise,
    )

    introduce(world, child, helper, parent, room)
    world.para()
    give_toy(world, child, parent, toy_cfg)
    start_show(world, child, helper, toy_cfg)
    first_strange_beat(world, child, helper, toy_cfg, defect_cfg)
    for idx in range(1, REPEAT_COUNT + 1):
        repeat_mishap(world, child, helper, toy_cfg, defect_cfg, idx)
    if surprise.meters["found"] < THRESHOLD:
        raise StoryError("(Internal story failure: the repeated defect did not reveal the promised surprise.)")
    world.para()
    reveal_surprise(world, parent, surprise_cfg)
    twist(world, child, helper, toy_cfg, defect_cfg, surprise_cfg)
    world.para()
    fix_toy(world, parent, defect_cfg)
    finale(world, child, helper, toy_cfg, surprise_cfg)

    world.facts.update(
        child_name=child_name,
        helper_name=helper_name,
        repeated=REPEAT_COUNT,
        found=surprise.meters["found"] >= THRESHOLD,
        fixed=toy.meters["fixed"] >= THRESHOLD,
        outcome="twist_found_and_fixed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    toy = world.facts["toy_cfg"]
    defect = world.facts["defect"]
    surprise = world.facts["surprise"]
    room = world.facts["room"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "defective" and "strange," plus surprise, repetition, and a twist.',
        f"Tell a comedy where {child.label} and {helper.label} plan a tiny show in the {room.label}, but a {toy.label} has a defective {defect.label} and keeps doing the same odd thing until it reveals {surprise.phrase}.",
        f'Write a child-facing story where a toy seems broken at first, repeats a silly mistake three times, and then turns out to be the reason a missing item is found.',
    ]


KNOWLEDGE = {
    "windup": [
        (
            "What is a wind-up toy?",
            "A wind-up toy is a toy with a little spring inside. When you turn it and let go, the spring helps the toy move."
        )
    ],
    "gears": [
        (
            "What do gears do in a toy?",
            "Gears are little turning parts inside some toys. They help the toy's movement go the way it is supposed to go."
        )
    ],
    "spring": [
        (
            "What does a spring do in a toy?",
            "A spring stores a bit of push when you wind it. Then it lets that push out to make the toy move."
        )
    ],
    "defective": [
        (
            "What does defective mean?",
            "Defective means something is not working the right way. It might still move, but it does the wrong thing."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something unexpected that happens. You did not know it was coming until it suddenly appeared."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long strip of soft cloth or shiny material. People use ribbons to decorate gifts, clothes, or rooms."
        )
    ],
    "bells": [
        (
            "What are ankle bells?",
            "Ankle bells are little bells tied on with a strap or string. They jingle when you move."
        )
    ],
    "party": [
        (
            "Why do people wear party hats?",
            "People wear party hats because they look silly and festive. The hats help make a celebration feel extra special."
        )
    ],
}

KNOWLEDGE_ORDER = ["windup", "gears", "spring", "defective", "surprise", "party", "bells", "ribbon"]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    toy = world.facts["toy_cfg"]
    defect = world.facts["defect"]
    surprise = world.facts["surprise"]
    room = world.facts["room"]
    repeated = world.facts["repeated"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {helper.label}, and {child.label}'s {parent.label_word}. They are trying to put on {room.show_goal} with a toy."
        ),
        (
            f"What was strange about the {toy.label}?",
            f"It had a defective {defect.label}, so it stopped behaving the normal way. Instead, it kept making the same silly mistake over and over."
        ),
        (
            "What kept repeating?",
            f"The toy repeated its odd move {repeated} times, with the same funny {toy.sound} sounds each time. That repetition made everyone first stare and then laugh."
        ),
        (
            "What was the surprise and the twist?",
            f"The surprise was that {surprise.phrase} suddenly appeared. The twist was that the very defect that seemed to ruin the show was the thing that helped find it."
        ),
        (
            f"Why did everyone stop calling the toy ruined?",
            f"They stopped because the toy's strange mistake ended up helping the family. After that, the defect felt funny and useful before the grown-up fixed it."
        ),
    ]
    if world.facts["fixed"]:
        qa.append(
            (
                f"How did {child.label}'s {parent.label_word} help at the end?",
                f"{parent.label_word.capitalize()} fixed the toy by dealing with the {defect.label}. That let the toy behave better while everyone still remembered its funny surprise trick."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"windup", "defective", "surprise"}
    defect = world.facts["defect"]
    surprise = world.facts["surprise"]
    tags |= set(defect.tags)
    if surprise.id == "hat_box":
        tags.add("party")
    if surprise.id == "bell_basket":
        tags.add("bells")
    if surprise.id == "ribbon_bundle":
        tags.add("ribbon")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    lines.append(f"  fired_rules={sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        toy="robot",
        defect="reverse_gear",
        surprise="hat_box",
        room="living_room",
        child="Lily",
        child_gender="girl",
        helper="Tom",
        helper_gender="boy",
        parent="mother",
        trait="dramatic",
    ),
    StoryParams(
        toy="monkey",
        defect="jumpy_spring",
        surprise="bell_basket",
        room="kitchen",
        child="Ben",
        child_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        trait="giggly",
    ),
    StoryParams(
        toy="duck",
        defect="spinny_wheel",
        surprise="ribbon_bundle",
        room="playroom",
        child="Ava",
        child_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        trait="cheerful",
    ),
]


ASP_RULES = r"""
compatible(T, D) :- toy(T), defect(D), supports(T, D).
reveals(D, S)    :- defect(D), surprise(S), defect_trigger(D, X), surprise_trigger(S, X).
valid(T, D, S)   :- compatible(T, D), reveals(D, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        for defect_id in sorted(toy.supports):
            lines.append(asp.fact("supports", toy_id, defect_id))
    for defect_id, defect in DEFECTS.items():
        lines.append(asp.fact("defect", defect_id))
        lines.append(asp.fact("defect_trigger", defect_id, defect.reveal_trigger))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("surprise_trigger", surprise_id, surprise.trigger))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedic story world about a strange defective toy whose repeated mishap causes a surprise twist."
    )
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--defect", choices=sorted(DEFECTS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy and args.defect and args.surprise and not valid_combo(args.toy, args.defect, args.surprise):
        raise StoryError(explain_rejection(args.toy, args.defect, args.surprise))

    combos = [
        combo for combo in valid_combos()
        if (args.toy is None or combo[0] == args.toy)
        and (args.defect is None or combo[1] == args.defect)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        if args.toy and args.defect and args.surprise:
            raise StoryError(explain_rejection(args.toy, args.defect, args.surprise))
        raise StoryError("(No valid combination matches the given options.)")

    toy_id, defect_id, surprise_id = rng.choice(sorted(combos))
    room_id = args.room or rng.choice(sorted(ROOMS))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["boy", "girl"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        toy=toy_id,
        defect=defect_id,
        surprise=surprise_id,
        room=room_id,
        child=child_name,
        child_gender=child_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.toy not in TOYS:
        raise StoryError(f"(No story: unknown toy '{params.toy}'.)")
    if params.defect not in DEFECTS:
        raise StoryError(f"(No story: unknown defect '{params.defect}'.)")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(No story: unknown surprise '{params.surprise}'.)")
    if params.room not in ROOMS:
        raise StoryError(f"(No story: unknown room '{params.room}'.)")
    if not valid_combo(params.toy, params.defect, params.surprise):
        raise StoryError(explain_rejection(params.toy, params.defect, params.surprise))

    world = tell(
        room=ROOMS[params.room],
        toy_cfg=TOYS[params.toy],
        defect_cfg=DEFECTS[params.defect],
        surprise_cfg=SURPRISES[params.surprise],
        child_name=params.child,
        child_gender=params.child_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
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
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo - py:
            print("  only in clingo:", sorted(clingo - py))
        if py - clingo:
            print("  only in python:", sorted(py - clingo))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "defective" not in sample.story or "strange" not in sample.story:
            raise StoryError("(Smoke test failed: story text is empty or missing required seed words.)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if "### smoke" not in buf.getvalue():
            raise StoryError("(Smoke test failed: emit() produced no output.)")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if sample.world is None or sample.world.facts.get("outcome") != "twist_found_and_fixed":
            raise StoryError("(Random smoke test failed: missing expected world outcome.)")
        print("OK: random resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (toy, defect, surprise) combos:\n")
        for toy_id, defect_id, surprise_id in combos:
            print(f"  {toy_id:8} {defect_id:13} {surprise_id}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.helper}: {p.toy} / {p.defect} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
