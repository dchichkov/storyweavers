#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py
================================================================

A small adventure storyworld about two children on a tiny quest. One child keeps
repeating an unkind action until it starts to rile a guardian animal. The turn
comes when the children switch from pestering to kindness, and the ending image
shows whether kindness repaired the path in time.

Run it
------
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py --trail jungle --obstacle bramble_gate
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py --guardian goat --repeat tap_stick --kindness mend
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py --repeat drum --kindness apologize --repeat-count 3
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py --all
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rile_repetition_kindness_adventure.py --verify
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
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type


@dataclass
class Trail:
    id: str
    place: str
    goal: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    need: str
    mood_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guardian:
    id: str
    label: str
    phrase: str
    need: str
    riled_by: set[str] = field(default_factory=set)
    soothed_by: set[str] = field(default_factory=set)
    help_text: str = ""
    calm_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class RepeatAction:
    id: str
    kind: str
    line: str
    text: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessAct:
    id: str
    kind: str
    text: str
    power: int
    gift: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, trail: Trail) -> None:
        self.trail = trail
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
        clone = World(self.trail)
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


def _r_blocked(world: World) -> list[str]:
    guardian = world.get("guardian")
    obstacle = world.get("obstacle")
    if guardian.memes["irritation"] < THRESHOLD:
        return []
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] += 1
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return []


def _r_open(world: World) -> list[str]:
    guardian = world.get("guardian")
    obstacle = world.get("obstacle")
    if guardian.memes["trust"] < THRESHOLD or guardian.memes["kindness_seen"] < THRESHOLD:
        return []
    sig = ("open", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["open"] += 1
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked", tag="social", apply=_r_blocked),
    Rule(name="open", tag="social", apply=_r_open),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
        current = tuple(sorted(world.fired))
        if getattr(propagate, "_last", None) != current:
            changed = changed or False
        propagate._last = current  # type: ignore[attr-defined]
    if narrate:
        for line in produced:
            world.say(line)
    return produced


TRAILS = {
    "jungle": Trail(
        id="jungle",
        place="the whispering jungle trail",
        goal="the bright map-stone at the old arch",
        detail="Vines hung like green ropes, and every leaf looked as if it might hide a clue.",
        affords={"rope_bridge", "bramble_gate"},
    ),
    "cliff": Trail(
        id="cliff",
        place="the windy cliff path",
        goal="the golden flag on the lookout hill",
        detail="Below them the sea flashed silver, and above them gulls wheeled like tiny kites.",
        affords={"rope_bridge"},
    ),
    "marsh": Trail(
        id="marsh",
        place="the lantern marsh path",
        goal="the shell compass by the willow island",
        detail="Thin reeds leaned over the water, and the mud shone like brown glass.",
        affords={"river_stones"},
    ),
}

OBSTACLES = {
    "rope_bridge": Obstacle(
        id="rope_bridge",
        label="rope bridge",
        phrase="a rope bridge that swayed over a deep crack in the ground",
        need="guide_bridge",
        mood_line="The bridge shivered softly whenever the wind pushed at it.",
        tags={"bridge", "crossing"},
    ),
    "bramble_gate": Obstacle(
        id="bramble_gate",
        label="bramble gate",
        phrase="a wall of brambles tangled across the path",
        need="trim_brambles",
        mood_line="The thorns hooked together so tightly that even sunlight had trouble getting through.",
        tags={"brambles", "path"},
    ),
    "river_stones": Obstacle(
        id="river_stones",
        label="river stones",
        phrase="a line of wet stepping-stones in a quick little river",
        need="ferry_stream",
        mood_line="Water skipped around the stones and made them look slippery as fish backs.",
        tags={"river", "crossing"},
    ),
}

GUARDIANS = {
    "raven": Guardian(
        id="raven",
        label="raven",
        phrase="a black raven with clever eyes",
        need="guide_bridge",
        riled_by={"noisy"},
        soothed_by={"words", "gift"},
        help_text="hopped onto the first rope and called from plank to plank until the safest way across was clear",
        calm_text="The raven tipped its head, listening instead of glaring.",
        tags={"raven", "bird"},
    ),
    "goat": Guardian(
        id="goat",
        label="goat",
        phrase="a shaggy mountain goat with strong horns",
        need="trim_brambles",
        riled_by={"teasing"},
        soothed_by={"gift", "help"},
        help_text="lowered its horns and neatly snapped a doorway through the thorny wall",
        calm_text="The goat stamped once, then let out a breath and stopped snorting.",
        tags={"goat", "animal"},
    ),
    "otter": Guardian(
        id="otter",
        label="otter",
        phrase="a river otter with bright whiskers",
        need="ferry_stream",
        riled_by={"splashy", "teasing"},
        soothed_by={"help", "words"},
        help_text="slid into the water and nudged a broad fallen branch into place like a little bridge",
        calm_text="The otter floated on its back for a moment, no longer looking cross.",
        tags={"otter", "river"},
    ),
}

REPEATS = {
    "chant": RepeatAction(
        id="chant",
        kind="noisy",
        line='"Move, move, move!"',
        text="kept chanting at the guardian",
        power=1,
        tags={"repeat", "noise"},
    ),
    "drum": RepeatAction(
        id="drum",
        kind="noisy",
        line='"Boom-bap, boom-bap, hurry up!"',
        text="beat a toy drum again and again",
        power=2,
        tags={"repeat", "noise"},
    ),
    "tap_stick": RepeatAction(
        id="tap_stick",
        kind="teasing",
        line='"Tap, tap, come on!"',
        text="kept tapping a stick nearby to pester the guardian",
        power=1,
        tags={"repeat", "teasing"},
    ),
    "splash": RepeatAction(
        id="splash",
        kind="splashy",
        line='"Splash-splash, hurry!"',
        text="splashed the water over and over near the guardian",
        power=1,
        tags={"repeat", "water"},
    ),
}

KINDNESS = {
    "apologize": KindnessAct(
        id="apologize",
        kind="words",
        text='said, "I am sorry. I was trying to rush you instead of being kind."',
        power=1,
        tags={"kindness", "apology"},
    ),
    "share_berries": KindnessAct(
        id="share_berries",
        kind="gift",
        text="offered the guardian a handful of shiny berries from the trail bag",
        power=2,
        gift="berries",
        tags={"kindness", "gift", "berries"},
    ),
    "mend": KindnessAct(
        id="mend",
        kind="help",
        text="knelt down and fixed the little mess that had been made nearby before asking for help",
        power=2,
        tags={"kindness", "help"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Zoe", "Tara"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Noah", "Ben", "Leo"]
TRAITS = ["eager", "bold", "careful", "curious", "kind", "steady"]


def valid_pair(obstacle: Obstacle, guardian: Guardian, repeat_act: RepeatAction, kindness: KindnessAct) -> bool:
    if guardian.need != obstacle.need:
        return False
    if repeat_act.kind not in guardian.riled_by:
        return False
    if kindness.kind not in guardian.soothed_by:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for trail_id, trail in TRAILS.items():
        for obstacle_id in sorted(trail.affords):
            obstacle = OBSTACLES[obstacle_id]
            for guardian_id, guardian in GUARDIANS.items():
                for repeat_id, repeat_act in REPEATS.items():
                    for kind_id, kind_act in KINDNESS.items():
                        if valid_pair(obstacle, guardian, repeat_act, kind_act):
                            combos.append((trail_id, obstacle_id, guardian_id, repeat_id, kind_id))
    return combos


def irritation_total(repeat_act: RepeatAction, repeat_count: int) -> int:
    return repeat_act.power * repeat_count


def kindness_total(kindness: KindnessAct, helper_trait: str) -> int:
    bonus = 1 if helper_trait in {"kind", "careful", "steady"} else 0
    return kindness.power + bonus


def success_outcome(params: "StoryParams") -> str:
    repeat_act = REPEATS[params.repeat]
    kind_act = KINDNESS[params.kindness]
    total_ritation = irritation_total(repeat_act, params.repeat_count)
    total_kindness = kindness_total(kind_act, params.friend_trait)
    return "helped" if total_kindness >= total_ritation else "turn_back"


def predict_outcome(world: World, params: "StoryParams") -> dict:
    sim = world.copy()
    guardian = sim.get("guardian")
    obstacle = sim.get("obstacle")
    guardian.memes["irritation"] += irritation_total(REPEATS[params.repeat], params.repeat_count)
    propagate(sim, narrate=False)
    predicted_blocked = obstacle.meters["blocked"] >= THRESHOLD
    guardian.memes["kindness_seen"] += kindness_total(KINDNESS[params.kindness], params.friend_trait)
    guardian.memes["trust"] += 1 if KINډNESS[params.kindness].kind in GUARDIANS[params.guardian].soothed_by else 0
    propagate(sim, narrate=False)
    return {
        "blocked": predicted_blocked,
        "opens": obstacle.meters["open"] >= THRESHOLD and kindness_total(KINDNESS[params.kindness], params.friend_trait) >= irritation_total(REPEATS[params.repeat], params.repeat_count),
    }


def introduce(world: World, hero: Entity, friend: Entity, trail: Trail) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {friend.id} set out along {trail.place} on a small adventure. "
        f"They were looking for {trail.goal}."
    )
    world.say(trail.detail)


def meet_obstacle(world: World, obstacle: Obstacle, guardian: Guardian) -> None:
    world.say(
        f"Before long they found {obstacle.phrase}. {obstacle.mood_line} "
        f"Right in the middle waited {guardian.phrase}."
    )


def hurry_repeat(world: World, hero: Entity, guardian: Entity, repeat_act: RepeatAction, repeat_count: int) -> None:
    hero.memes["impatience"] += 1
    repetitions = "Again and again" if repeat_count > 1 else "At once"
    guardian_name = guardian.label_word
    world.say(
        f'{hero.id} wanted to reach the treasure quickly. {repetitions}, {hero.pronoun()} {repeat_act.text}. '
        f'{repeat_act.line}'
    )
    guardian.memes["irritation"] += irritation_total(repeat_act, repeat_count)
    hero.memes["guilt"] += 1 if repeat_count >= 2 else 0
    propagate(world, narrate=False)
    if guardian.memes["irritation"] >= THRESHOLD:
        world.say(
            f"That was enough to rile the {guardian_name}. It fluffed up, made a sharp sound, "
            f"and stood in the way."
        )


def friend_warns(world: World, friend: Entity, hero: Entity, guardian: Entity) -> None:
    world.say(
        f'{friend.id} touched {hero.id}\'s sleeve. "Rushing is not the same as being brave," '
        f'{friend.pronoun()} said. "If we keep pestering the {guardian.label_word}, it will only get more upset."'
    )


def kind_turn(world: World, friend: Entity, hero: Entity, guardian: Entity, kindness: KindnessAct, helper_trait: str) -> None:
    friend.memes["kindness"] += 1
    hero.memes["listening"] += 1
    world.say(
        f"Then {hero.id} stopped. {friend.id}, who was especially {helper_trait}, showed a kinder plan."
    )
    world.say(f"{hero.id} {kindness.text}")
    guardian.memes["kindness_seen"] += kindness_total(kindness, helper_trait)
    if kindness.kind in guardian.attrs.get("soothed_by", set()):
        guardian.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(GUARDIANS[guardian.id].calm_text)


def cross_success(world: World, hero: Entity, friend: Entity, guardian: Guardian, obstacle: Obstacle, trail: Trail) -> None:
    world.say(
        f"Now the {guardian.label} {guardian.help_text}. The path opened, and the children crossed without hurrying or shoving."
    )
    world.say(
        f"On the far side they found {trail.goal}, glowing softly as if the adventure itself had smiled at them. "
        f"{hero.id} grinned and promised, this time for real, to ask kindly before asking twice."
    )


def turn_back_gently(world: World, hero: Entity, friend: Entity, guardian: Guardian, obstacle: Obstacle, trail: Trail) -> None:
    world.say(
        f"The {guardian.label} was calmer, but not calm enough to help with the {obstacle.label} yet. "
        f"So {hero.id} and {friend.id} did not push past."
    )
    world.say(
        f"They left their small kindness behind and walked home under the evening sky, planning to come back another day with gentler hearts. "
        f"Even without the treasure, the adventure had taught them something worth carrying."
    )


def tell(params: "StoryParams") -> World:
    trail = TRAILS[params.trail]
    obstacle = OBSTACLES[params.obstacle]
    guardian_cfg = GUARDIANS[params.guardian]
    repeat_act = REPEATS[params.repeat]
    kindness = KINDNESS[params.kindness]

    world = World(trail=trail)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero", traits=[params.hero_trait]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender, role="friend", traits=[params.friend_trait]))
    guardian = world.add(
        Entity(
            id=params.guardian,
            kind="character",
            type="animal",
            role="guardian",
            label=guardian_cfg.label,
            attrs={"soothed_by": set(guardian_cfg.soothed_by)},
            tags=set(guardian_cfg.tags),
        )
    )
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, role="obstacle", tags=set(obstacle.tags)))

    introduce(world, hero, friend, trail)
    world.para()
    meet_obstacle(world, obstacle, guardian_cfg)
    hurry_repeat(world, hero, guardian, repeat_act, params.repeat_count)
    friend_warns(world, friend, hero, guardian)
    world.para()
    kind_turn(world, friend, hero, guardian, kindness, params.friend_trait)

    total_irritation = irritation_total(repeat_act, params.repeat_count)
    total_kindness = kindness_total(kindness, params.friend_trait)
    world.facts["irritation"] = total_irritation
    world.facts["kindness_strength"] = total_kindness

    if total_kindness >= total_irritation:
        obstacle_ent.meters["open"] = 1.0
        cross_success(world, hero, friend, guardian_cfg, obstacle, trail)
        outcome = "helped"
    else:
        obstacle_ent.meters["blocked"] = 1.0
        turn_back_gently(world, hero, friend, guardian_cfg, obstacle, trail)
        outcome = "turn_back"

    world.facts.update(
        hero=hero,
        friend=friend,
        guardian=guardian,
        guardian_cfg=guardian_cfg,
        obstacle=obstacle_ent,
        obstacle_cfg=obstacle,
        trail=trail,
        repeat_cfg=repeat_act,
        kindness_cfg=kindness,
        outcome=outcome,
        reached_goal=outcome == "helped",
    )
    return world


@dataclass
class StoryParams:
    trail: str
    obstacle: str
    guardian: str
    repeat: str
    kindness: str
    repeat_count: int
    hero_name: str
    hero_gender: str
    hero_trait: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        trail="jungle",
        obstacle="bramble_gate",
        guardian="goat",
        repeat="tap_stick",
        kindness="mend",
        repeat_count=1,
        hero_name="Mira",
        hero_gender="girl",
        hero_trait="eager",
        friend_name="Finn",
        friend_gender="boy",
        friend_trait="kind",
    ),
    StoryParams(
        trail="cliff",
        obstacle="rope_bridge",
        guardian="raven",
        repeat="chant",
        kindness="share_berries",
        repeat_count=2,
        hero_name="Owen",
        hero_gender="boy",
        hero_trait="bold",
        friend_name="Lina",
        friend_gender="girl",
        friend_trait="steady",
    ),
    StoryParams(
        trail="marsh",
        obstacle="river_stones",
        guardian="otter",
        repeat="splash",
        kindness="apologize",
        repeat_count=1,
        hero_name="Nora",
        hero_gender="girl",
        hero_trait="curious",
        friend_name="Ben",
        friend_gender="boy",
        friend_trait="careful",
    ),
    StoryParams(
        trail="cliff",
        obstacle="rope_bridge",
        guardian="raven",
        repeat="drum",
        kindness="apologize",
        repeat_count=3,
        hero_name="Eli",
        hero_gender="boy",
        hero_trait="eager",
        friend_name="Tara",
        friend_gender="girl",
        friend_trait="bold",
    ),
]


KNOWLEDGE = {
    "rile": [
        (
            "What does rile mean?",
            "To rile someone means to make them upset or annoyed. If you keep bothering a creature again and again, you can rile it."
        )
    ],
    "kindness": [
        (
            "Why can kindness help when someone is upset?",
            "Kindness shows that you want to make things better instead of making them worse. A calm apology or a helpful action can help another person or animal feel safe again."
        )
    ],
    "repetition": [
        (
            "Why can repeating an unkind thing make a problem bigger?",
            "When you do the same unkind thing over and over, the other person has to feel it over and over too. That can make them more upset each time instead of less."
        )
    ],
    "bridge": [
        (
            "Why should you cross a rope bridge carefully?",
            "A rope bridge can sway and wobble. Going slowly and paying attention helps you keep your balance."
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants that tangle together. Their sharp thorns can catch on clothes and skin."
        )
    ],
    "river": [
        (
            "Why are wet stones slippery?",
            "Water makes the tops of stones slick. That means your feet can slide if you rush."
        )
    ],
    "raven": [
        (
            "What is a raven?",
            "A raven is a large black bird with a strong beak and a clever mind. Ravens notice sounds and movement very quickly."
        )
    ],
    "goat": [
        (
            "Why are goats good climbers?",
            "Goats have strong legs and careful feet. They are good at moving over rough ground."
        )
    ],
    "otter": [
        (
            "What is an otter?",
            "An otter is a playful river animal that swims very well. It uses its body and tail to move smoothly through water."
        )
    ],
}
KNOWLEDGE_ORDER = ["rile", "kindness", "repetition", "bridge", "brambles", "river", "raven", "goat", "otter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian_cfg"]
    obstacle = f["obstacle_cfg"]
    repeat_cfg = f["repeat_cfg"]
    kindness_cfg = f["kindness_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a gentle adventure story for a 3-to-5-year-old that uses the word "rile".',
        f"Tell an adventure about {hero.id} and {friend.id}, who meet a {guardian.label} guarding a {obstacle.label} after one child keeps repeating an unkind thing.",
        f"Write a story where repetition causes trouble, but kindness changes the mood and decides what happens next on the trail.",
    ]
    if outcome == "helped":
        prompts.append(
            f"End with the children reaching {f['trail'].goal} after {hero.id} stops trying to hurry the {guardian.label} and chooses {kindness_cfg.kind} instead."
        )
    else:
        prompts.append(
            f"End with the children turning back wisely after {repeat_cfg.text} makes the {guardian.label} too upset to help that day."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian_cfg"]
    obstacle = f["obstacle_cfg"]
    trail = f["trail"]
    repeat_cfg = f["repeat_cfg"]
    kindness_cfg = f["kindness_cfg"]
    outcome = f["outcome"]
    irritation = f["irritation"]
    kindness_strength = f["kindness_strength"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children on an adventure trail. They meet a {guardian.label} beside a {obstacle.label} on the way to {trail.goal}."
        ),
        (
            "What problem stopped them on the trail?",
            f"They came to {obstacle.phrase} with the {guardian.label} in the middle of it. The obstacle mattered because it stood between them and their goal."
        ),
        (
            f"How did {hero.id} rile the {guardian.label}?",
            f"{hero.id} kept repeating an unkind action instead of waiting kindly. That repetition made the {guardian.label} more upset each time, so it blocked the way rather than helping."
        ),
        (
            f"What did {friend.id} do when things went wrong?",
            f"{friend.id} warned that pestering the {guardian.label} would only make the trouble bigger. Then {friend.pronoun().capitalize()} helped turn the moment toward kindness instead of hurry."
        ),
        (
            "How did kindness change the adventure?",
            f"The children switched from bothering the guardian to a kinder action: {kindness_cfg.text}. That gave the guardian a reason to listen again, because kindness can repair trust after impatience has hurt it."
        ),
    ]
    if outcome == "helped":
        qa.append(
            (
                "Why did the guardian help them in the end?",
                f"The kindness was strong enough to calm the upset the children had caused. After being riled, the {guardian.label} saw a real change in their behavior and helped them past the {obstacle.label}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the path opening and the children reaching {trail.goal}. The ending image shows that they got farther once they stopped rushing and acted with kindness."
            )
        )
    else:
        qa.append(
            (
                "Did they reach the treasure?",
                f"No, not that day. The children were kinder at the end, but the {guardian.label} was still too upset to help with the {obstacle.label}, so they chose to turn back safely."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that repeating an unkind thing can make a problem grow faster than you expect. They also learned that kindness matters even when it does not fix everything right away."
            )
        )
    qa.append(
        (
            "Was the kind action stronger than the upset?",
            f"The repeated pestering built up {irritation} part{'s' if irritation != 1 else ''} of upset, while the kindness brought {kindness_strength} part{'s' if kindness_strength != 1 else ''} of repair. That balance is what decided the ending."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rile", "kindness", "repetition"}
    tags |= set(f["guardian_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    if "crossing" in tags:
        tags.add("bridge")
        tags.add("river")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if entity.role:
            parts.append(f"role={entity.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in entity.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_invalid(trail_id: str, obstacle_id: str, guardian_id: str, repeat_id: str, kindness_id: str) -> str:
    trail = TRAILS[trail_id]
    obstacle = OBSTACLES[obstacle_id]
    guardian = GUARDIANS[guardian_id]
    repeat_act = REPEATS[repeat_id]
    kindness = KINDNESS[kindness_id]
    if obstacle_id not in trail.affords:
        return f"(No story: {trail.place} does not contain a {obstacle.label} adventure.)"
    if guardian.need != obstacle.need:
        return f"(No story: the {guardian.label} cannot help with a {obstacle.label}; that obstacle needs a different kind of guardian.)"
    if repeat_act.kind not in guardian.riled_by:
        return f"(No story: {repeat_act.id} would not truly rile the {guardian.label} in this world, so the conflict would be weak.)"
    if kindness.kind not in guardian.soothed_by:
        return f"(No story: {kindness.id} is not the sort of kindness this {guardian.label} understands best here.)"
    return "(No story: the chosen elements do not make a reasonable adventure.)"


ASP_RULES = r"""
trail_has(T, O) :- trail(T), affords(T, O).
fits_guardian(O, G) :- obstacle(O), guardian(G), needs(O, N), helps(G, N).
riles(G, R) :- guardian(G), repeat(R), riled_by(G, K), repeat_kind(R, K).
soothes(G, Kd) :- guardian(G), kindness(Kd), soothed_by(G, K), kindness_kind(Kd, K).

valid(T, O, G, R, Kd) :- trail_has(T, O), fits_guardian(O, G), riles(G, R), soothes(G, Kd).

kindness_bonus(1) :- helper_trait(T), bonus_trait(T).
kindness_bonus(0) :- helper_trait(T), not bonus_trait(T).

irritation(V) :- chosen_repeat(R), repeat_power(R, P), repeat_count(C), V = P * C.
repair(V) :- chosen_kindness(Kd), kindness_power(Kd, P), kindness_bonus(B), V = P + B.

outcome(helped) :- irritation(I), repair(R), R >= I.
outcome(turn_back) :- irritation(I), repair(R), R < I.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id, trail in TRAILS.items():
        lines.append(asp.fact("trail", trail_id))
        for obstacle_id in sorted(trail.affords):
            lines.append(asp.fact("affords", trail_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for guardian_id, guardian in GUARDIANS.items():
        lines.append(asp.fact("guardian", guardian_id))
        lines.append(asp.fact("helps", guardian_id, guardian.need))
        for kind in sorted(guardian.riled_by):
            lines.append(asp.fact("riled_by", guardian_id, kind))
        for kind in sorted(guardian.soothed_by):
            lines.append(asp.fact("soothed_by", guardian_id, kind))
    for repeat_id, repeat_act in REPEATS.items():
        lines.append(asp.fact("repeat", repeat_id))
        lines.append(asp.fact("repeat_kind", repeat_id, repeat_act.kind))
        lines.append(asp.fact("repeat_power", repeat_id, repeat_act.power))
    for kindness_id, kindness in KINDNESS.items():
        lines.append(asp.fact("kindness", kindness_id))
        lines.append(asp.fact("kindness_kind", kindness_id, kindness.kind))
        lines.append(asp.fact("kindness_power", kindness_id, kindness.power))
    for trait in sorted(TRAITS):
        if trait in {"kind", "careful", "steady"}:
            lines.append(asp.fact("bonus_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_repeat", params.repeat),
            asp.fact("chosen_kindness", params.kindness),
            asp.fact("repeat_count", params.repeat_count),
            asp.fact("helper_trait", params.friend_trait),
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
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            case = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        case.seed = seed
        cases.append(case)

    mismatches = 0
    for case in cases:
        if asp_outcome(case) != success_outcome(case):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a tiny adventure where repeated pestering can rile a guardian, and kindness decides the ending."
    )
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--repeat", choices=REPEATS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--repeat-count", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = {
        "trail": args.trail,
        "obstacle": args.obstacle,
        "guardian": args.guardian,
        "repeat": args.repeat,
        "kindness": args.kindness,
    }

    if all(value is not None for value in explicit.values()):
        if not valid_pair(OBSTACLES[args.obstacle], GUARDIANS[args.guardian], REPEATS[args.repeat], KINDNESS[args.kindness]):
            raise StoryError(explain_invalid(args.trail, args.obstacle, args.guardian, args.repeat, args.kindness))
        if args.obstacle not in TRAILS[args.trail].affords:
            raise StoryError(explain_invalid(args.trail, args.obstacle, args.guardian, args.repeat, args.kindness))

    combos = [
        combo for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.guardian is None or combo[2] == args.guardian)
        and (args.repeat is None or combo[3] == args.repeat)
        and (args.kindness is None or combo[4] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trail_id, obstacle_id, guardian_id, repeat_id, kindness_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)

    candidate_counts = [args.repeat_count] if args.repeat_count is not None else [1, 2]
    repeat_count = rng.choice(candidate_counts)
    if args.repeat_count is None:
        good_counts = [count for count in candidate_counts if kindness_total(KINDNESS[kindness_id], friend_trait) >= irritation_total(REPEATS[repeat_id], count)]
        if good_counts:
            repeat_count = rng.choice(good_counts)

    return StoryParams(
        trail=trail_id,
        obstacle=obstacle_id,
        guardian=guardian_id,
        repeat=repeat_id,
        kindness=kindness_id,
        repeat_count=repeat_count,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (
        ("trail", TRAILS),
        ("obstacle", OBSTACLES),
        ("guardian", GUARDIANS),
        ("repeat", REPEATS),
        ("kindness", KINDNESS),
    ):
        key = getattr(params, field_name)
        if key not in table:
            raise StoryError(f"(Invalid parameter: {field_name}={key!r})")
    if params.obstacle not in TRAILS[params.trail].affords:
        raise StoryError(explain_invalid(params.trail, params.obstacle, params.guardian, params.repeat, params.kindness))
    if not valid_pair(OBSTACLES[params.obstacle], GUARDIANS[params.guardian], REPEATS[params.repeat], KINDNESS[params.kindness]):
        raise StoryError(explain_invalid(params.trail, params.obstacle, params.guardian, params.repeat, params.kindness))
    if params.repeat_count not in {1, 2, 3}:
        raise StoryError("(Invalid parameter: repeat_count must be 1, 2, or 3.)")

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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trail, obstacle, guardian, repeat, kindness) combos:\n")
        for trail_id, obstacle_id, guardian_id, repeat_id, kindness_id in combos:
            print(f"  {trail_id:7} {obstacle_id:13} {guardian_id:7} {repeat_id:10} {kindness_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.guardian} at {p.obstacle} ({success_outcome(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
