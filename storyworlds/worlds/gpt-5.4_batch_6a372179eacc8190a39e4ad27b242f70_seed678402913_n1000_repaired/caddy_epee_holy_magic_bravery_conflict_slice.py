#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/caddy_epee_holy_magic_bravery_conflict_slice.py
===========================================================================

A standalone story world for a small slice-of-life tale about a child at a
beginner fencing class. A rolling gear caddy holds masks and practice epees,
and a small holy keepsake tucked into the caddy gives the child a feeling of
gentle magic. The tension can be stage fright, a quarrel over an epee, or a
hurtful teasing moment. The resolution must be a sensible one for that conflict:
calming breaths, a coach demo, a spare epee, or a fair turn card.

The world model tracks physical meters like shaky hands and ready stance, and
emotional memes like fear, trust, embarrassment, and bravery. The prose comes
from simulated state, not slot-swapped templates. Every story includes the seed
words "caddy", "epee", and "holy", plus the features Magic, Bravery, and
Conflict, while staying in a child-facing slice-of-life register.
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
        female = {"girl", "woman", "mother", "coach_woman"}
        male = {"boy", "man", "father", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "coach_woman": "coach",
            "coach_man": "coach",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    room_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    kind: str
    opening: str
    risk: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    fix_for: set[str]
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HolyItem:
    id: str
    label: str
    phrase: str
    magic_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_to_shaky(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["fear"] >= THRESHOLD and hero.meters["shaky"] < THRESHOLD:
        sig = ("fear_to_shaky", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.meters["shaky"] += 1
    return []


def _r_conflict_to_distance(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["conflict"] >= THRESHOLD and hero.meters["distance"] < THRESHOLD:
        sig = ("conflict_to_distance", hero.id, friend.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.meters["distance"] += 1
        friend.meters["distance"] += 1
    return []


def _r_support_to_bravery(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["supported"] >= THRESHOLD and hero.memes["bravery"] < THRESHOLD:
        sig = ("support_to_bravery", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["bravery"] += 1
        if hero.meters["shaky"] >= THRESHOLD:
            hero.meters["shaky"] = 0.0
        hero.meters["ready"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fear_to_shaky", tag="body", apply=_r_fear_to_shaky),
    Rule(name="conflict_to_distance", tag="social", apply=_r_conflict_to_distance),
    Rule(name="support_to_bravery", tag="turn", apply=_r_support_to_bravery),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def support_fits(conflict: Conflict, support: Support) -> bool:
    return conflict.kind in support.fix_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for cid, conflict in CONFLICTS.items():
            for sup_id, support in SUPPORTS.items():
                if not support_fits(conflict, support):
                    continue
                for holy_id in HOLY_ITEMS:
                    combos.append((sid, cid, sup_id, holy_id))
    return combos


def explain_rejection(conflict: Conflict, support: Support) -> str:
    need = ", ".join(sorted(conflict.tags))
    fits = ", ".join(sorted(support.fix_for))
    return (
        f"(No story: {support.label} is not a sensible fix for {conflict.id}. "
        f"This conflict needs help for {conflict.kind} trouble, but that support "
        f"only fits [{fits}].)"
    )


def predict_outcome(conflict: Conflict, support: Support) -> dict:
    resolved = support_fits(conflict, support)
    return {
        "resolved": resolved,
        "brave": resolved,
    }


def introduce(world: World, hero: Entity, friend: Entity, coach: Entity,
              holy: HolyItem) -> None:
    caddy = world.get("caddy")
    world.say(
        f"After school, {hero.id} went with {hero.pronoun('possessive')} "
        f"{world.get('parent').label_word} to {world.setting.place} for beginner fencing."
    )
    world.say(
        f"{world.setting.room_detail} Near the wall stood a wheeled caddy full of masks, "
        f"gloves, and practice epees."
    )
    world.say(
        f"{friend.id} was already there, bouncing on {friend.pronoun('possessive')} toes, "
        f"and {coach.label_word} called everyone into a neat line."
    )
    world.say(
        f"In the side pocket of the caddy sat {holy.phrase}. To {hero.id}, it always felt "
        f"like a tiny holy promise that brave things could begin quietly."
    )
    caddy.meters["open"] += 1
    world.facts["holy_seen"] = True


def gear_up(world: World, hero: Entity) -> None:
    hero.meters["holding_epee"] += 1
    world.say(
        f"When it was {hero.id}'s turn to gear up, {hero.pronoun()} wrapped small fingers "
        f"around an epee with a silver guard and tried a careful salute."
    )


def spark_conflict(world: World, hero: Entity, friend: Entity, conflict: Conflict) -> None:
    hero.memes["conflict"] += 1
    if conflict.kind in {"nerves", "teasing"}:
        hero.memes["fear"] += 1
    if conflict.kind == "sharing":
        friend.memes["conflict"] += 1
    if conflict.id == "crowd_nerves":
        world.say(
            f"Then {coach_name(world)} said there would be a short open-house bout for the families. "
            f"{conflict.opening}"
        )
    elif conflict.id == "shared_epee":
        world.say(
            f"{conflict.opening} Both children reached for the straightest epee in the caddy at the same time."
        )
    elif conflict.id == "teasing_step":
        world.say(
            f"{conflict.opening} The words were small, but they stung."
        )
    propagate(world)
    if hero.meters["shaky"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s hand felt shaky around the epee, and the bright floor stripes suddenly seemed very long."
        )
    if hero.meters["distance"] >= THRESHOLD:
        world.say(
            f"{hero.id} and {friend.id} drifted a step apart, and the room felt less friendly than it had a minute before."
        )


def coach_name(world: World) -> str:
    return world.get("coach").label_word.capitalize()


def holy_magic(world: World, hero: Entity, holy: HolyItem) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"As {hero.id} looked toward the caddy, {holy.magic_text} It was only a little moment, "
        f"but it felt like magic all the same."
    )


def apply_support(world: World, hero: Entity, friend: Entity, support: Support) -> None:
    hero.meters["supported"] += 1
    if support.id == "breathing_count":
        world.say(
            f'{coach_name(world)} knelt beside {hero.id} and said, "{support.text}"'
        )
    elif support.id == "coach_demo":
        world.say(
            f'{coach_name(world)} stepped onto the strip and said, "{support.text}"'
        )
    elif support.id == "spare_epee":
        friend.memes["relief"] += 1
        hero.memes["relief"] += 1
        world.say(
            f'{coach_name(world)} opened the back of the caddy and said, "{support.text}"'
        )
    elif support.id == "turn_card":
        world.say(
            f'{coach_name(world)} lifted a small laminated turn card from the caddy and said, "{support.text}"'
        )
    if support.id in {"spare_epee", "turn_card"}:
        hero.memes["conflict"] = 0.0
        friend.memes["conflict"] = 0.0
        hero.meters["distance"] = 0.0
        hero.memes["trust"] += 1
        friend.memes["trust"] += 1
    else:
        hero.memes["fear"] = 0.0
        hero.memes["conflict"] = 0.0
    propagate(world)


def brave_act(world: World, hero: Entity, friend: Entity, conflict: Conflict, support: Support) -> None:
    if conflict.kind == "sharing":
        world.say(
            f"{hero.id} took a breath, looked at {friend.id}, and said, "
            f'"We can both have a turn." Saying it out loud was the bravest thing {hero.pronoun()} had done all afternoon.'
        )
    elif conflict.id == "teasing_step":
        world.say(
            f"{hero.id} lifted {hero.pronoun('possessive')} chin and tried the step again, slower and steadier this time."
        )
    else:
        world.say(
            f"{hero.id} planted both feet on the strip, gave one more salute, and did not hide behind the mask rack."
        )
    hero.memes["bravery"] += 1
    hero.meters["ready"] += 1
    if support.id == "coach_demo":
        hero.meters["learned_step"] += 1
    if support.id == "spare_epee":
        hero.meters["holding_epee"] += 1


def ending(world: World, hero: Entity, friend: Entity, conflict: Conflict, support: Support) -> None:
    if conflict.kind == "sharing":
        world.say(
            f"A minute later, one child fenced while the other counted touches, and then they swapped. "
            f"The caddy no longer looked like the start of a fight. It looked like ordinary class again."
        )
    else:
        world.say(
            f"When the bout began, the epee did not feel too heavy anymore. {hero.id} stepped, reached, and tapped "
            f"{friend.id}'s sleeve with a soft click that made {hero.pronoun('object')} grin inside the mask."
        )
    world.say(
        f"On the way home, {hero.id} glanced back at the caddy and its little holy keepsake. "
        f"The room was still just a room, but bravery had made it glow."
    )
    world.facts["resolved"] = True
    world.facts["support_used"] = support.id


def tell(setting: Setting, conflict: Conflict, support: Support, holy: HolyItem,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         parent_type: str, coach_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    coach = world.add(Entity(id="coach", kind="character", type=coach_type, label="the coach", role="coach"))
    caddy = world.add(Entity(id="caddy", kind="thing", type="caddy", label="caddy", phrase="a blue rolling caddy"))
    world.add(Entity(id="holy", kind="thing", type="holy_item", label=holy.label, phrase=holy.phrase))
    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name
    world.facts["setting"] = setting
    world.facts["conflict_cfg"] = conflict
    world.facts["support_cfg"] = support
    world.facts["holy_cfg"] = holy
    world.facts["hero_ent"] = hero
    world.facts["friend_ent"] = friend
    world.facts["parent_ent"] = parent
    world.facts["coach_ent"] = coach
    world.facts["caddy_ent"] = caddy
    world.facts["resolved"] = False

    introduce(world, hero, friend, coach, holy)
    gear_up(world, hero)

    world.para()
    spark_conflict(world, hero, friend, conflict)
    holy_magic(world, hero, holy)
    apply_support(world, hero, friend, support)

    world.para()
    brave_act(world, hero, friend, conflict, support)
    ending(world, hero, friend, conflict, support)
    return world


SETTINGS = {
    "parish_hall": Setting(
        id="parish_hall",
        place="the parish hall",
        room_detail="The wood floor shone under paper stars from last week's fair, and a quiet holy picture hung near the door.",
        tags={"hall", "church"},
    ),
    "school_gym": Setting(
        id="school_gym",
        place="the school gym",
        room_detail="Folded chairs waited by the wall, and the janitor had taped fresh fencing lines across the floor.",
        tags={"gym", "school"},
    ),
    "rec_room": Setting(
        id="rec_room",
        place="the neighborhood rec room",
        room_detail="The room smelled faintly of lemon soap, and the tall windows made even the practice strip look friendly.",
        tags={"rec", "community"},
    ),
}

CONFLICTS = {
    "crowd_nerves": Conflict(
        id="crowd_nerves",
        kind="nerves",
        opening="At once, a hot flutter moved through that small brave feeling. {hero} had wanted to fence, but not with grown-ups watching.",
        risk="The child may freeze and hide from the bout.",
        effect="fear",
        tags={"nerves", "crowd"},
    ),
    "shared_epee": Conflict(
        id="shared_epee",
        kind="sharing",
        opening="{hero} and {friend} had both been admiring the same epee for three whole minutes.",
        risk="A quarrel over gear can spoil practice.",
        effect="conflict",
        tags={"sharing", "gear"},
    ),
    "teasing_step": Conflict(
        id="teasing_step",
        kind="teasing",
        opening='When {hero} tried the first step-lunge, {friend} blurted, "That looked baby-slow."',
        risk="Embarrassment can make a child want to quit.",
        effect="fear",
        tags={"teasing", "hurt_feelings"},
    ),
}

SUPPORTS = {
    "breathing_count": Support(
        id="breathing_count",
        label="breathing count",
        fix_for={"nerves", "teasing"},
        text="Put one hand on your belly and count three slow breaths with me. Brave feet start with calm breaths.",
        qa_text="helped with three slow breaths",
        tags={"breathing", "calm"},
    ),
    "coach_demo": Support(
        id="coach_demo",
        label="coach demo",
        fix_for={"nerves", "teasing"},
        text="Watch my feet first. Small steps are strong steps, and learning slowly is how fencers get good.",
        qa_text="showed the move first and made the pace feel safe",
        tags={"coach", "learning"},
    ),
    "spare_epee": Support(
        id="spare_epee",
        label="spare epee",
        fix_for={"sharing"},
        text="Good news. The caddy has a second epee that fits this lesson just as well, so no one has to grab.",
        qa_text="took out a spare epee so the children could stop fighting",
        tags={"sharing", "gear"},
    ),
    "turn_card": Support(
        id="turn_card",
        label="turn card",
        fix_for={"sharing"},
        text="We will use the turn card. One child fences first, and the other goes next. Fair is stronger than fast hands.",
        qa_text="used a turn card to make the choice fair",
        tags={"sharing", "fairness"},
    ),
}

HOLY_ITEMS = {
    "holy_card": HolyItem(
        id="holy_card",
        label="holy card",
        phrase="a small holy card with a gold edge",
        magic_text="the gold edge of the holy card caught the light and sent a warm flicker over the caddy handle",
        tags={"holy", "card"},
    ),
    "holy_medal": HolyItem(
        id="holy_medal",
        label="holy medal",
        phrase="a tiny holy medal on a blue ribbon",
        magic_text="the holy medal gave one bright wink, as if it had heard a secret promise",
        tags={"holy", "medal"},
    ),
    "holy_bookmark": HolyItem(
        id="holy_bookmark",
        label="holy bookmark",
        phrase="a slim holy bookmark painted with a star",
        magic_text="the painted star on the holy bookmark gleamed so softly that the whole pocket seemed kind",
        tags={"holy", "bookmark"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ella", "June", "Ava", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Max", "Eli", "Noah", "Jack"]
TRAITS = ["careful", "hopeful", "quiet", "eager", "gentle", "steady"]


@dataclass
class StoryParams:
    setting: str
    conflict: str
    support: str
    holy_item: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    coach: str
    trait: str = "careful"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_name"]
    friend = f["friend_name"]
    conflict = f["conflict_cfg"]
    support = f["support_cfg"]
    holy = f["holy_cfg"]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "caddy", "epee", and "holy".',
        f"Tell a story about a child named {hero} at beginner fencing, where a small conflict appears and a coach helps with {support.label}.",
        f"Write a Magic, Bravery, and Conflict story set in an ordinary class, where {hero} and {friend} notice {holy.label} near a caddy and the brave choice solves {conflict.kind} trouble.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero_name"]
    friend = f["friend_name"]
    conflict = f["conflict_cfg"]
    support = f["support_cfg"]
    holy = f["holy_cfg"]
    setting = f["setting"]
    coach = f["coach_ent"]
    qa: list[tuple[str, str]] = [
        (
            "Where did the story happen?",
            f"It happened in {setting.place} during a beginner fencing class. The rolling caddy and the practice strip make the place feel ordinary and close to home.",
        ),
        (
            "What was in the caddy?",
            f"The caddy held masks, gloves, and practice epees, and it also had {holy.phrase} tucked into its side pocket. That holy keepsake is what gave the moment its tiny feeling of magic.",
        ),
        (
            f"What problem came up for {hero}?",
            _problem_answer(hero, friend, conflict),
        ),
        (
            f"How did the coach help {hero}?",
            f"The coach {support.qa_text}. That worked because it matched the real problem instead of just hurrying the child along.",
        ),
        (
            f"Why was {hero} brave?",
            _bravery_answer(hero, friend, conflict),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the class feeling calm again and the child ready to fence. The last image of the caddy and the holy keepsake shows that the room did not change much, but the child's heart did.",
            )
        )
    return qa


def _problem_answer(hero: str, friend: str, conflict: Conflict) -> str:
    if conflict.id == "crowd_nerves":
        return (
            f"{hero} wanted to fence, but became scared when families were going to watch. "
            f"The conflict was between wanting to be brave and wanting to hide."
        )
    if conflict.id == "shared_epee":
        return (
            f"{hero} and {friend} both wanted the same epee from the caddy, and the grabby moment started a quarrel. "
            f"The trouble was not the epee alone but the unfair feeling growing between them."
        )
    return (
        f"{hero} felt hurt when {friend} teased a slow fencing step. "
        f"The words were small, but they made the child feel shaky and close to quitting."
    )


def _bravery_answer(hero: str, friend: str, conflict: Conflict) -> str:
    if conflict.id == "shared_epee":
        return (
            f"{hero} was brave because {hero.lower()} stopped fighting for the epee and agreed to be fair. "
            f"Sharing kindly in the middle of conflict takes courage too."
        )
    if conflict.id == "teasing_step":
        return (
            f"{hero} was brave because {hero.lower()} tried the step again after feeling embarrassed. "
            f"Doing a hard thing in front of someone who hurt your feelings is a very real kind of courage."
        )
    return (
        f"{hero} was brave because {hero.lower()} stayed on the strip even after feeling nervous. "
        f"The child did not wait for fear to disappear completely and chose to begin anyway."
    )


KNOWLEDGE = {
    "caddy": [
        (
            "What is a caddy?",
            "A caddy is a holder or rolling container that keeps tools together so people can carry them where they are needed.",
        )
    ],
    "epee": [
        (
            "What is an epee?",
            "An epee is one kind of fencing sword used in the sport of fencing. In class, children use practice epees and learn careful rules.",
        )
    ],
    "holy": [
        (
            "What does holy mean?",
            "Holy means something is connected to prayer, worship, or a special feeling of blessing. A holy object is treated gently and with respect.",
        )
    ],
    "breathing": [
        (
            "Why do slow breaths help when you feel nervous?",
            "Slow breaths help your body calm down. When your body is calmer, your hands and feet can listen better."
        )
    ],
    "sharing": [
        (
            "What can you do if two children want the same thing?",
            "They can take turns, share, or ask a grown-up to help make it fair. Fair choices stop little conflicts from growing bigger."
        )
    ],
    "fencing": [
        (
            "What do children learn first in fencing?",
            "They learn how to stand safely, how to move their feet, and how to listen to the coach. Good fencing begins with control, not speed."
        )
    ],
    "teasing": [
        (
            "Why can teasing hurt?",
            "Teasing can make someone feel small or embarrassed, even if the words seem quick. Kind words help people keep trying."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right or hard thing even when you feel scared or shaky. It does not mean never feeling afraid."
        )
    ],
}
KNOWLEDGE_ORDER = ["caddy", "epee", "holy", "fencing", "breathing", "sharing", "teasing", "bravery"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    conflict = world.facts["conflict_cfg"]
    support = world.facts["support_cfg"]
    tags = {"caddy", "epee", "holy", "fencing", "bravery"}
    if support.id == "breathing_count":
        tags.add("breathing")
    if conflict.kind == "sharing":
        tags.add("sharing")
    if conflict.id == "teasing_step":
        tags.add("teasing")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="parish_hall",
        conflict="crowd_nerves",
        support="breathing_count",
        holy_item="holy_card",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        coach="coach_woman",
        trait="quiet",
    ),
    StoryParams(
        setting="school_gym",
        conflict="shared_epee",
        support="spare_epee",
        holy_item="holy_medal",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        coach="coach_man",
        trait="eager",
    ),
    StoryParams(
        setting="rec_room",
        conflict="teasing_step",
        support="coach_demo",
        holy_item="holy_bookmark",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="mother",
        coach="coach_woman",
        trait="steady",
    ),
    StoryParams(
        setting="parish_hall",
        conflict="shared_epee",
        support="turn_card",
        holy_item="holy_card",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        parent="father",
        coach="coach_man",
        trait="gentle",
    ),
]


ASP_RULES = r"""
valid(S, C, Sup, H) :- setting(S), conflict(C), support(Sup), holy_item(H), fits(C, Sup).

resolved(C, Sup) :- fits(C, Sup).
outcome(calm) :- resolved(C, Sup), chosen_conflict(C), chosen_support(Sup).
outcome(stuck) :- chosen_conflict(C), chosen_support(Sup), not resolved(C, Sup).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("kind", cid, conflict.kind))
    for sid, support in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        for kind in sorted(support.fix_for):
            lines.append(asp.fact("fits", _conflict_id_for_kind(kind), sid))
        if support.id in {"breathing_count", "coach_demo"}:
            lines.append(asp.fact("fits", "crowd_nerves", sid))
            lines.append(asp.fact("fits", "teasing_step", sid))
        if support.id in {"spare_epee", "turn_card"}:
            lines.append(asp.fact("fits", "shared_epee", sid))
    for hid in HOLY_ITEMS:
        lines.append(asp.fact("holy_item", hid))
    return "\n".join(sorted(set(lines)))


def _conflict_id_for_kind(kind: str) -> str:
    if kind == "sharing":
        return "shared_epee"
    if kind == "nerves":
        return "crowd_nerves"
    if kind == "teasing":
        return "teasing_step"
    return ""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_conflict", params.conflict),
            asp.fact("chosen_support", params.support),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "calm" if support_fits(CONFLICTS[params.conflict], SUPPORTS[params.support]) else "stuck"


def smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    if "caddy" not in sample.story.lower() or "epee" not in sample.story.lower() or "holy" not in sample.story.lower():
        raise StoryError("Smoke test failed: required seed words missing.")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))
    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome differences.")
    try:
        smoke_generate()
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a fencing class, a small holy spark, and a brave solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--holy-item", dest="holy_item", choices=HOLY_ITEMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--coach", choices=["coach_woman", "coach_man"])
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.conflict and args.support:
        conflict = CONFLICTS[args.conflict]
        support = SUPPORTS[args.support]
        if not support_fits(conflict, support):
            raise StoryError(explain_rejection(conflict, support))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.conflict is None or combo[1] == args.conflict)
        and (args.support is None or combo[2] == args.support)
        and (args.holy_item is None or combo[3] == args.holy_item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, conflict, support, holy_item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    coach = args.coach or rng.choice(["coach_woman", "coach_man"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        conflict=conflict,
        support=support,
        holy_item=holy_item,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        coach=coach,
        trait=trait,
    )


def _render_conflict_text(conflict: Conflict, hero_name: str, friend_name: str) -> Conflict:
    return Conflict(
        id=conflict.id,
        kind=conflict.kind,
        opening=conflict.opening.format(hero=hero_name, friend=friend_name),
        risk=conflict.risk,
        effect=conflict.effect,
        tags=set(conflict.tags),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {params.conflict}")
    if params.support not in SUPPORTS:
        raise StoryError(f"Unknown support: {params.support}")
    if params.holy_item not in HOLY_ITEMS:
        raise StoryError(f"Unknown holy item: {params.holy_item}")
    conflict = _render_conflict_text(CONFLICTS[params.conflict], params.hero_name, params.friend_name)
    support = SUPPORTS[params.support]
    if not support_fits(conflict, support):
        raise StoryError(explain_rejection(conflict, support))

    world = tell(
        setting=SETTINGS[params.setting],
        conflict=conflict,
        support=support,
        holy=HOLY_ITEMS[params.holy_item],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        coach_type=params.coach,
    )
    story = world.render().replace(" hero ", f" {params.hero_name} ").replace(" friend ", f" {params.friend_name} ")
    story = story.replace("hero", params.hero_name).replace("friend", params.friend_name)
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
        print(f"{len(combos)} compatible (setting, conflict, support, holy_item) combos:\n")
        for setting, conflict, support, holy_item in combos:
            print(f"  {setting:12} {conflict:13} {support:15} {holy_item}")
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
            header = f"### {p.hero_name}: {p.conflict} at {p.setting} ({p.support})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
