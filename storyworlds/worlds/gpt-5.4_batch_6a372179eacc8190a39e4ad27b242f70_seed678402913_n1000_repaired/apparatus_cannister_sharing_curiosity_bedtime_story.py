#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py
=================================================================================

A standalone storyworld about two sleepy children, one bedtime apparatus, and a
small cannister full of matching star pieces. The heart of the domain is
curiosity turning into conflict, and conflict turning into sharing.

The world model keeps track of:
- physical state: whether the cannister is opened, whether the apparatus is set up,
  whose turn it is, whether the room has become calm and sleepy
- emotional state: curiosity, jealousy, trust, joy, and calm

Reasonableness constraint
-------------------------
Not every cannister belongs with every apparatus. A moon viewer cannot use a
cannister of shadow-animal picture reels, and a lantern slide projector cannot
use loose glow pebbles. The world refuses such mismatches because then the
cannister would not honestly matter to the story.

The sharing plan must also fit the object:
- "turns" works for any single-user apparatus
- "pick_slips" only works when the cannister contains separate slips/disks/reels
  that children can choose in turn
- "side_by_side" only works for the apparatus marked as roomy enough for both
  children to huddle around at once

Run it
------
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py --apparatus star_tube --cannister star_slips
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py --apparatus moon_viewer --cannister shadow_reels
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/apparatus_cannister_sharing_curiosity_bedtime_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    place: str
    bedtime_image: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Apparatus:
    id: str
    label: str
    phrase: str
    verb: str
    glow_line: str
    closeness: str
    together_ok: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cannister:
    id: str
    label: str
    phrase: str
    contents: str
    discover: str
    compatible_with: set[str] = field(default_factory=set)
    pickable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingPlan:
    id: str
    label: str
    needs_pickable: bool = False
    needs_together_ok: bool = False
    intro: str = ""
    middle: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room_cfg = room
        self.entities: dict[str, Entity] = {}
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"first", "second"}]


ROOMS = {
    "bedroom": Room(
        id="bedroom",
        place="the bedroom",
        bedtime_image="the blankets made a small hill under their chins",
        sound="the curtains barely moved in the night breeze",
        tags={"bedroom", "night"},
    ),
    "nursery": Room(
        id="nursery",
        place="the nursery",
        bedtime_image="their pillows looked like little white clouds",
        sound="the rocking chair gave one soft creak",
        tags={"nursery", "night"},
    ),
    "attic_room": Room(
        id="attic_room",
        place="the attic room",
        bedtime_image="the sloping ceiling made the room feel like a tucked-in tent",
        sound="rain whispered on the roof",
        tags={"attic", "night", "rain"},
    ),
}

APPARATUS = {
    "star_tube": Apparatus(
        id="star_tube",
        label="apparatus",
        phrase="a cardboard star-viewing apparatus",
        verb="peek through the little star tube",
        glow_line="silver stars trembled on the ceiling",
        closeness="they had to kneel close to see where the stars landed",
        together_ok=True,
        tags={"apparatus", "stars", "bedtime"},
    ),
    "moon_viewer": Apparatus(
        id="moon_viewer",
        label="apparatus",
        phrase="a moon-viewing apparatus with a round blue lens",
        verb="look through the moon viewer",
        glow_line="a pale moon shape drifted across the wall",
        closeness="only one child could fit an eye to the lens at a time",
        together_ok=False,
        tags={"apparatus", "moon", "bedtime"},
    ),
    "shadow_lantern": Apparatus(
        id="shadow_lantern",
        label="apparatus",
        phrase="a bedside shadow apparatus with a tiny lamp inside",
        verb="turn the shadow lantern toward the wall",
        glow_line="soft shapes floated over the wallpaper",
        closeness="the wall beside the bed became their quiet screen",
        together_ok=True,
        tags={"apparatus", "light", "bedtime"},
    ),
}

CANNISTERS = {
    "star_slips": Cannister(
        id="star_slips",
        label="cannister",
        phrase="a small tin cannister of silver star slips",
        contents="silver star slips",
        discover="Inside were curled silver slips cut with tiny stars and moons.",
        compatible_with={"star_tube", "moon_viewer"},
        pickable=True,
        tags={"cannister", "stars", "paper"},
    ),
    "glow_pebbles": Cannister(
        id="glow_pebbles",
        label="cannister",
        phrase="a round cannister of glow pebbles",
        contents="glow pebbles",
        discover="Inside were smooth glow pebbles, cool and green as little moons.",
        compatible_with={"star_tube"},
        pickable=True,
        tags={"cannister", "glow", "stones"},
    ),
    "shadow_reels": Cannister(
        id="shadow_reels",
        label="cannister",
        phrase="a brass cannister of picture reels",
        contents="picture reels",
        discover="Inside were tiny picture reels with rabbits, trees, and sleepy stars punched through them.",
        compatible_with={"shadow_lantern"},
        pickable=True,
        tags={"cannister", "reels", "pictures"},
    ),
}

PLANS = {
    "turns": SharingPlan(
        id="turns",
        label="take turns",
        intro="Their parent said they could count to ten for one child, then ten for the other.",
        middle="That way each child could have a real turn without snatching.",
        ending="Soon the turns felt gentle instead of sharp, like rocking back and forth.",
        tags={"sharing", "turns"},
    ),
    "pick_slips": SharingPlan(
        id="pick_slips",
        label="pick from the cannister in turn",
        needs_pickable=True,
        intro="Their parent set the open cannister between them and said each child could choose one piece, then pass the cannister on.",
        middle="The choosing mattered as much as the looking, so nobody felt left out.",
        ending="Each new piece became a small gift from one child to the other.",
        tags={"sharing", "choosing", "cannister"},
    ),
    "side_by_side": SharingPlan(
        id="side_by_side",
        label="curl up side by side",
        needs_together_ok=True,
        intro="Their parent tucked them shoulder to shoulder and showed them how to use the apparatus together.",
        middle="Instead of fighting over the first turn, they made one warm little nest around the light.",
        ending="They watched the shapes move as if the room itself were breathing slowly with them.",
        tags={"sharing", "together"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Eva", "Ruby", "Anna", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Eli", "Sam", "Finn", "Noah"]
TRAITS = ["curious", "gentle", "sleepy", "bright-eyed", "quiet", "thoughtful"]


def compatible(apparatus: Apparatus, cannister: Cannister) -> bool:
    return apparatus.id in cannister.compatible_with


def plan_fits(apparatus: Apparatus, cannister: Cannister, plan: SharingPlan) -> bool:
    if plan.needs_pickable and not cannister.pickable:
        return False
    if plan.needs_together_ok and not apparatus.together_ok:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for app_id, apparatus in APPARATUS.items():
        for can_id, cannister in CANNISTERS.items():
            if not compatible(apparatus, cannister):
                continue
            for plan_id, plan in PLANS.items():
                if plan_fits(apparatus, cannister, plan):
                    combos.append((app_id, can_id, plan_id))
    return combos


def explain_rejection(apparatus: Apparatus, cannister: Cannister, plan: Optional[SharingPlan] = None) -> str:
    if not compatible(apparatus, cannister):
        return (
            f"(No story: {cannister.phrase} does not match {apparatus.phrase}. "
            f"In this world, the cannister must hold pieces the apparatus can actually use.)"
        )
    if plan is not None and not plan_fits(apparatus, cannister, plan):
        if plan.needs_together_ok and not apparatus.together_ok:
            return (
                f"(No story: {apparatus.phrase} is too cramped for the '{plan.id}' sharing plan. "
                f"Choose a plan with turns, or an apparatus that lets both children huddle together.)"
            )
        if plan.needs_pickable and not cannister.pickable:
            return (
                f"(No story: the '{plan.id}' plan needs a cannister with separate pieces children can choose in turn.)"
            )
    return "(No story: that combination does not fit this tiny bedtime world.)"


def introduce(world: World, a: Entity, b: Entity, parent: Entity, room: Room) -> None:
    for kid in (a, b):
        kid.memes["calm"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"In {room.place}, {room.sound}, and {room.bedtime_image}. "
        f"{a.id} and {b.id} were supposed to be settling down, but bedtime always made them ask one more question."
    )
    world.say(
        f"Their {parent.label_word} came in smiling, carrying something wrapped in a soft cloth."
    )


def bring_gift(world: World, parent: Entity, apparatus: Apparatus, cannister: Cannister) -> None:
    tool = world.get("tool")
    jar = world.get("jar")
    tool.meters["present"] += 1
    jar.meters["present"] += 1
    world.say(
        f'From the cloth came {apparatus.phrase} and {cannister.phrase}. '
        f'"A little bedtime surprise," their {parent.label_word} whispered.'
    )


def wonder(world: World, a: Entity, b: Entity, apparatus: Apparatus, cannister: Cannister) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"{a.id} touched the {apparatus.label} with one careful finger. "
        f"{b.id} leaned closer to the cannister and asked what could possibly be inside."
    )
    world.say(
        f"The room felt fuller just because there was something new to discover."
    )


def open_cannister(world: World, a: Entity, b: Entity, cannister: Cannister) -> None:
    jar = world.get("jar")
    jar.meters["opened"] += 1
    for kid in (a, b):
        kid.memes["wonder"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"The lid gave a tiny pop. {cannister.discover}"
    )


def setup_apparatus(world: World, parent: Entity, apparatus: Apparatus) -> None:
    tool = world.get("tool")
    tool.meters["ready"] += 1
    world.say(
        f"Their {parent.label_word} showed them how to {apparatus.verb}. Soon {apparatus.glow_line}, "
        f"and {apparatus.closeness}."
    )


def both_reach(world: World, a: Entity, b: Entity) -> None:
    a.memes["want_first"] += 1
    b.memes["want_first"] += 1
    a.memes["jealousy"] += 1
    b.memes["jealousy"] += 1
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(
        f"For one quick moment, both children reached at once. {a.id} wanted the first try, and so did {b.id}."
    )
    world.say(
        f"The warm room suddenly felt smaller, the way a room does when two people want the same thing at the same time."
    )


def soothe_and_plan(world: World, parent: Entity, plan: SharingPlan) -> None:
    world.say(
        f'Their {parent.label_word} did not scold. {parent.pronoun().capitalize()} sat on the edge of the bed and said, '
        f'"Curious hearts can still be kind hearts."'
    )
    world.say(plan.intro)
    world.say(plan.middle)


def apply_plan(world: World, a: Entity, b: Entity, apparatus: Apparatus, cannister: Cannister, plan: SharingPlan) -> None:
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    for kid in (a, b):
        kid.memes["trust"] += 1
        kid.memes["joy"] += 1
        kid.memes["sharing"] += 1
        kid.memes["calm"] += 1

    if plan.id == "turns":
        world.facts["used_together"] = False
        world.say(
            f"{a.id} went first and then handed the apparatus over without being asked twice. "
            f"After that, {b.id} took a turn and smiled instead of grabbing."
        )
    elif plan.id == "pick_slips":
        world.facts["used_together"] = False
        world.say(
            f"{a.id} chose one piece from the cannister and passed it over. Then {b.id} chose the next. "
            f"Each child waited to see what picture or sparkle the other would pick."
        )
    else:
        world.facts["used_together"] = True
        world.say(
            f"{a.id} and {b.id} curled up shoulder to shoulder and used the apparatus together, whispering every new shape they noticed."
        )

    world.say(plan.ending)
    if cannister.id == "shadow_reels":
        world.say("One reel showed a rabbit under a tree, and both children laughed very softly so the bedtime feeling would not break.")
    elif cannister.id == "glow_pebbles":
        world.say("The glow pebbles made small green stars that seemed to drift right over their blankets.")
    else:
        world.say("The silver slips sent neat little stars over the ceiling, as if the dark had learned to sparkle.")


def sleepy_ending(world: World, a: Entity, b: Entity, parent: Entity, room: Room) -> None:
    room_ent = world.get("room")
    room_ent.meters["sleepy"] += 1
    for kid in (a, b):
        kid.memes["sleepy"] += 1
    world.say(
        f'At last their {parent.label_word} closed the cannister, set the apparatus on the table, and pulled the blankets up. '
        f'{a.id} and {b.id} were still curious, but now the curiosity felt soft.'
    )
    if world.facts.get("used_together"):
        world.say(
            f"They fell quiet side by side, watching the last faint shape fade from the wall."
        )
    else:
        world.say(
            f"They each kept one remembered picture in mind and took it with them into sleep."
        )
    world.say(
        f"In a little while, {room.sound}, and the room became peaceful again."
    )


def tell(
    room: Room,
    apparatus: Apparatus,
    cannister: Cannister,
    plan: SharingPlan,
    first_name: str,
    first_gender: str,
    second_name: str,
    second_gender: str,
    parent_type: str,
    trait_a: str,
    trait_b: str,
) -> World:
    world = World(room)
    a = world.add(Entity(id=first_name, kind="character", type=first_gender, role="first", attrs={"trait": trait_a}))
    b = world.add(Entity(id=second_name, kind="character", type=second_gender, role="second", attrs={"trait": trait_b}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="room", type="room", label=room.place, tags=set(room.tags)))
    world.add(Entity(id="tool", type="apparatus", label=apparatus.label, phrase=apparatus.phrase, tags=set(apparatus.tags)))
    world.add(Entity(id="jar", type="cannister", label=cannister.label, phrase=cannister.phrase, tags=set(cannister.tags)))

    introduce(world, a, b, parent, room)
    bring_gift(world, parent, apparatus, cannister)
    wonder(world, a, b, apparatus, cannister)

    world.para()
    open_cannister(world, a, b, cannister)
    setup_apparatus(world, parent, apparatus)
    both_reach(world, a, b)

    world.para()
    soothe_and_plan(world, parent, plan)
    apply_plan(world, a, b, apparatus, cannister, plan)

    world.para()
    sleepy_ending(world, a, b, parent, room)

    world.facts.update(
        room=room,
        apparatus=apparatus,
        cannister=cannister,
        plan=plan,
        first=a,
        second=b,
        parent=parent,
        conflict_happened=True,
        curiosity_high=a.memes["curiosity"] + b.memes["curiosity"] >= 4,
        sharing_happened=a.memes["sharing"] >= THRESHOLD and b.memes["sharing"] >= THRESHOLD,
        room_sleepy=world.get("room").meters["sleepy"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    room: str
    apparatus: str
    cannister: str
    plan: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    parent: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "apparatus": [
        (
            "What is an apparatus?",
            "An apparatus is a tool or device made to do a special job. In this story, it is a bedtime tool for making shapes or lights to look at.",
        )
    ],
    "cannister": [
        (
            "What is a cannister?",
            "A cannister is a small container with a lid that holds things inside. You open it to find what has been kept safe or tidy.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful when two children want one thing?",
            "Sharing helps both children feel seen and included. It turns grabbing into waiting, and waiting makes room for kindness.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know or see more. It can lead to wonderful discoveries when it stays gentle.",
        )
    ],
    "bedtime": [
        (
            "Why do quiet routines help at bedtime?",
            "Quiet routines help bodies and minds slow down. When a room becomes calm, it is easier to feel sleepy and safe.",
        )
    ],
    "stars": [
        (
            "Why do children like star shapes at night?",
            "Star shapes feel bright but gentle in the dark. They make nighttime seem cozy instead of empty.",
        )
    ],
    "moon": [
        (
            "Why does the moon seem calm at bedtime?",
            "The moon moves slowly and gives soft light. That peaceful feeling matches the quiet of bedtime.",
        )
    ],
}
KNOWLEDGE_ORDER = ["apparatus", "cannister", "sharing", "curiosity", "bedtime", "stars", "moon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    apparatus = f["apparatus"]
    cannister = f["cannister"]
    plan = f["plan"]
    a = f["first"]
    b = f["second"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "apparatus" and "cannister".',
        f"Tell a gentle story where {a.id} and {b.id} become curious about a bedtime apparatus and a small cannister, then learn to share.",
        f"Write a sleepy story in which two children both want to use one special object, but a calm grown-up helps them {plan.label}. Include a peaceful ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["first"]
    b = f["second"]
    parent = f["parent"]
    apparatus = f["apparatus"]
    cannister = f["cannister"]
    plan = f["plan"]
    room = f["room"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id} at bedtime, with their {parent.label_word} nearby. The story follows how their curiosity about the apparatus and the cannister changes into sharing.",
        ),
        (
            "Why were the children so curious?",
            f"They were curious because their {parent.label_word} brought in {apparatus.phrase} and {cannister.phrase}, and both objects felt new and mysterious. Opening the cannister and seeing what was inside made them even more eager to explore.",
        ),
        (
            "What was inside the cannister?",
            f"Inside the cannister were {cannister.contents}. Those pieces mattered because they matched the apparatus and gave the children something real to discover together.",
        ),
        (
            "What problem happened in the middle of the story?",
            f"Both children wanted the first turn with the apparatus at the same time. Their curiosity was good, but it turned sharp for a moment because each child wanted the special experience first.",
        ),
        (
            "How was the problem solved?",
            f"Their {parent.label_word} helped them {plan.label}. That plan worked because it gave both children a place in the game, so the wanting stopped feeling like a fight.",
        ),
        (
            "How did the story end?",
            f"It ended quietly in {room.place}, with the cannister closed, the apparatus resting on the table, and the room feeling peaceful again. The ending shows that sharing helped bedtime become calm instead of cross.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"apparatus", "cannister", "sharing", "curiosity", "bedtime"}
    app_id = world.facts["apparatus"].id
    if app_id == "star_tube":
        tags.add("stars")
    if app_id == "moon_viewer":
        tags.add("moon")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="bedroom",
        apparatus="star_tube",
        cannister="star_slips",
        plan="pick_slips",
        first_name="Lila",
        first_gender="girl",
        second_name="Owen",
        second_gender="boy",
        parent="mother",
        trait_a="curious",
        trait_b="gentle",
    ),
    StoryParams(
        room="nursery",
        apparatus="moon_viewer",
        cannister="star_slips",
        plan="turns",
        first_name="Milo",
        first_gender="boy",
        second_name="Nora",
        second_gender="girl",
        parent="father",
        trait_a="bright-eyed",
        trait_b="thoughtful",
    ),
    StoryParams(
        room="attic_room",
        apparatus="shadow_lantern",
        cannister="shadow_reels",
        plan="side_by_side",
        first_name="Tess",
        first_gender="girl",
        second_name="Ben",
        second_gender="boy",
        parent="mother",
        trait_a="quiet",
        trait_b="curious",
    ),
]


ASP_RULES = r"""
compatible(A, C) :- cannister_matches(C, A).

plan_fits(P, A, C) :- plan(P), apparatus(A), cannister(C),
                      not need_pickable(P), not need_together(P).
plan_fits(P, A, C) :- plan(P), apparatus(A), cannister(C),
                      need_pickable(P), pickable(C), not need_together(P).
plan_fits(P, A, C) :- plan(P), apparatus(A), cannister(C),
                      not need_pickable(P), need_together(P), together_ok(A).
plan_fits(P, A, C) :- plan(P), apparatus(A), cannister(C),
                      need_pickable(P), pickable(C), need_together(P), together_ok(A).

valid(A, C, P) :- compatible(A, C), plan_fits(P, A, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for app_id, apparatus in APPARATUS.items():
        lines.append(asp.fact("apparatus", app_id))
        if apparatus.together_ok:
            lines.append(asp.fact("together_ok", app_id))
    for can_id, cannister in CANNISTERS.items():
        lines.append(asp.fact("cannister", can_id))
        if cannister.pickable:
            lines.append(asp.fact("pickable", can_id))
        for app_id in sorted(cannister.compatible_with):
            lines.append(asp.fact("cannister_matches", can_id, app_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        if plan.needs_pickable:
            lines.append(asp.fact("need_pickable", plan_id))
        if plan.needs_together_ok:
            lines.append(asp.fact("need_together", plan_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in [0, 1, 7]:
        try:
            params = resolve_params(parser.parse_args(["--seed", str(seed)]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story from random resolve.")
        except Exception as err:
            rc = 1
            print(f"RANDOM SMOKE TEST FAILED (seed={seed}): {err}")
            break
    else:
        print("OK: random resolve/generate smoke tests succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime curiosity, one apparatus, one cannister, and learning to share."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--apparatus", choices=APPARATUS)
    ap.add_argument("--cannister", choices=CANNISTERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (apparatus, cannister, plan) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.apparatus and args.cannister:
        apparatus = APPARATUS[args.apparatus]
        cannister = CANNISTERS[args.cannister]
        plan = PLANS[args.plan] if args.plan else None
        if not compatible(apparatus, cannister):
            raise StoryError(explain_rejection(apparatus, cannister, plan))
        if plan is not None and not plan_fits(apparatus, cannister, plan):
            raise StoryError(explain_rejection(apparatus, cannister, plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.apparatus is None or combo[0] == args.apparatus)
        and (args.cannister is None or combo[1] == args.cannister)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    app_id, can_id, plan_id = rng.choice(sorted(combos))
    first_name, first_gender = pick_child(rng)
    second_name, second_gender = pick_child(rng, avoid=first_name)
    return StoryParams(
        room=args.room or rng.choice(sorted(ROOMS)),
        apparatus=app_id,
        cannister=can_id,
        plan=plan_id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Invalid room: {params.room})")
    if params.apparatus not in APPARATUS:
        raise StoryError(f"(Invalid apparatus: {params.apparatus})")
    if params.cannister not in CANNISTERS:
        raise StoryError(f"(Invalid cannister: {params.cannister})")
    if params.plan not in PLANS:
        raise StoryError(f"(Invalid plan: {params.plan})")
    apparatus = APPARATUS[params.apparatus]
    cannister = CANNISTERS[params.cannister]
    plan = PLANS[params.plan]
    if not compatible(apparatus, cannister) or not plan_fits(apparatus, cannister, plan):
        raise StoryError(explain_rejection(apparatus, cannister, plan))

    world = tell(
        room=ROOMS[params.room],
        apparatus=apparatus,
        cannister=cannister,
        plan=plan,
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        parent_type=params.parent,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (apparatus, cannister, plan) combos:\n")
        for apparatus, cannister, plan in combos:
            print(f"  {apparatus:14} {cannister:13} {plan}")
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
            header = f"### {p.first_name} & {p.second_name}: {p.apparatus} + {p.cannister} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
