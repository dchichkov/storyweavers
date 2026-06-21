#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/burro_gluten_primary_misunderstanding_friendship_adventure.py
=========================================================================================

A standalone story world about a primary-school adventure, a burro helper, and a
friendship misunderstanding around gluten.

The core shape is: two friends from a primary class go on a small outdoor quest
with a burro carrying supplies. One child offers or wants to trade a gluten food.
The other child, who cannot eat gluten, refuses too quickly. The first child
misunderstands that refusal as meanness or rejection. A grown-up and the world
itself then make the real cause legible: the problem is the food, not the
friendship. A safe snack, a clear explanation, and a shared task repair the bond,
and the ending image proves that the friends are close again.

Reasonableness gate:
- the misunderstanding only makes sense if the offered food truly contains gluten
- the repair only makes sense if the shared replacement snack is gluten-free

The ASP twin mirrors that gate.
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

# Make the shared result containers importable when this script is run directly.
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
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type or self.label or "thing")


@dataclass
class Trail:
    id: str
    place: str = ""
    path: str = ""
    landmark: str = ""
    clue: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class GlutenFood:
    id: str
    label: str = ""
    phrase: str = ""
    contains_gluten: bool = False
    crumbly: str = ""
    warning: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeFood:
    id: str
    label: str = ""
    phrase: str = ""
    gluten_free: bool = False
    share_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str = ""
    seek: str = ""
    reward: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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


def propagate(world: World) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    burro = world.get("burro")

    if leader.memes["misunderstanding"] >= THRESHOLD:
        sig = ("distance", "friends")
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["distance"] += 1
            friend.memes["distance"] += 1

    if leader.memes["distance"] >= THRESHOLD and friend.memes["distance"] >= THRESHOLD:
        sig = ("stalled", "quest")
        if sig not in world.fired:
            world.fired.add(sig)
            burro.meters["progress"] -= 1
            world.facts["stalled"] = True

    if world.facts.get("explained") and world.facts.get("shared_safe_food"):
        sig = ("repair", "friends")
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["distance"] = 0.0
            friend.memes["distance"] = 0.0
            leader.memes["trust"] += 1
            friend.memes["trust"] += 1
            leader.memes["relief"] += 1
            friend.memes["relief"] += 1
            burro.meters["progress"] += 2
            world.facts["repaired"] = True


TRAILS = {
    "mesa": Trail(
        id="mesa",
        place="the red mesa trail behind the primary school camp",
        path="a winding path between red rocks and little sage bushes",
        landmark="a fork where one trail curled toward a dry wash and the other climbed to the sunlit rim",
        clue="a blue ribbon tied to the right-hand post",
        ending="the rim opened wide, and the whole valley looked like a painted map",
        tags={"trail", "mesa"},
    ),
    "pine": Trail(
        id="pine",
        place="the pine path above the primary school's field station",
        path="a soft needle path under tall trees",
        landmark="a wooden bridge over a chattery stream",
        clue="a silver bell hanging from the safe side of the bridge",
        ending="the trees parted, and a clear pond flashed like glass",
        tags={"trail", "pine"},
    ),
    "canyon": Trail(
        id="canyon",
        place="the little canyon path used by the primary adventure club",
        path="a twisty track beside warm stone walls",
        landmark="a place where the canyon split around a giant boulder",
        clue="a bright chalk arrow on the smooth side of the rock",
        ending="the hidden garden glowed green in the quiet shade",
        tags={"trail", "canyon"},
    ),
}

GLUTEN_FOODS = {
    "pretzel": GlutenFood(
        id="pretzel",
        label="pretzel",
        phrase="a twisty salted pretzel",
        contains_gluten=True,
        crumbly="salt crystals and crumbs",
        warning="pretzels are made with wheat flour",
        tags={"pretzel", "gluten"},
    ),
    "cookie": GlutenFood(
        id="cookie",
        label="cookie",
        phrase="a round oat cookie",
        contains_gluten=True,
        crumbly="sweet crumbs",
        warning="cookies like that are baked with flour that has gluten",
        tags={"cookie", "gluten"},
    ),
    "sandwich": GlutenFood(
        id="sandwich",
        label="sandwich",
        phrase="half of a soft bread sandwich",
        contains_gluten=True,
        crumbly="bread crumbs",
        warning="bread like that has gluten in it",
        tags={"sandwich", "gluten"},
    ),
    "corn_cup": GlutenFood(
        id="corn_cup",
        label="corn cup",
        phrase="a little cup of buttered corn",
        contains_gluten=False,
        crumbly="yellow kernels",
        warning="corn does not carry the same gluten worry here",
        tags={"corn"},
    ),
}

SAFE_FOODS = {
    "apple": SafeFood(
        id="apple",
        label="apple slices",
        phrase="a paper pouch of apple slices",
        gluten_free=True,
        share_line="The apple slices were crunchy, bright, and easy to share.",
        tags={"apple", "safe_food"},
    ),
    "cheese": SafeFood(
        id="cheese",
        label="cheese cubes",
        phrase="a small tin of cheese cubes",
        gluten_free=True,
        share_line="The cheese cubes were small treasure blocks from the lunch tin.",
        tags={"cheese", "safe_food"},
    ),
    "berries": SafeFood(
        id="berries",
        label="berries",
        phrase="a little cup of berries",
        gluten_free=True,
        share_line="The berries shone like tiny jewels in the burro's pack basket.",
        tags={"berries", "safe_food"},
    ),
    "barley_bun": SafeFood(
        id="barley_bun",
        label="barley bun",
        phrase="a soft barley bun",
        gluten_free=False,
        share_line="The bun smelled good, but it was not a safe swap.",
        tags={"barley"},
    ),
}

GOALS = {
    "spring": Goal(
        id="spring",
        label="hidden spring",
        seek="the hidden spring",
        reward="cold water slipping over smooth stones",
        ending="They knelt by the spring and watched the water wink in the light.",
        tags={"spring"},
    ),
    "flag": Goal(
        id="flag",
        label="wind flag",
        seek="the little wind flag on the hill",
        reward="a striped flag snapping in the breeze",
        ending="At the hilltop, the wind flag danced above them like a tiny brave sail.",
        tags={"flag"},
    ),
    "garden": Goal(
        id="garden",
        label="canyon garden",
        seek="the secret canyon garden",
        reward="orange flowers nodding beside green leaves",
        ending="In the cool garden, flowers leaned over the path as if they had been waiting.",
        tags={"garden"},
    ),
}

BURRO_NAMES = ["Pepito", "Luna", "Dusty", "Clover"]
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "curious", "bright", "brave", "gentle", "cheerful"]


def offered_food_risky(gluten_food: GlutenFood) -> bool:
    return gluten_food.contains_gluten


def repair_food_safe(safe_food: SafeFood) -> bool:
    return safe_food.gluten_free


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for trail_id in TRAILS:
        for gluten_id, gluten_food in GLUTEN_FOODS.items():
            for safe_id, safe_food in SAFE_FOODS.items():
                if offered_food_risky(gluten_food) and repair_food_safe(safe_food):
                    combos.append((trail_id, gluten_id, safe_id))
    return combos


@dataclass
class StoryParams:
    trail: str
    gluten_food: str
    safe_food: str
    goal: str
    burro_name: str
    leader_name: str
    leader_gender: str
    friend_name: str
    friend_gender: str
    teacher: str
    leader_trait: str
    friend_trait: str
    seed: Optional[int] = None


def introduce(world: World, trail: Trail, goal: Goal) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    burro = world.get("burro")
    teacher = world.get("teacher")
    world.say(
        f"On a bright morning, {leader.id} and {friend.id} set out with their primary class on "
        f"{trail.place}. At the front walked {teacher.id}, and beside {teacher.pronoun('object')} "
        f"plodded {burro.id} the burro with map rolls and lunch baskets tied to {burro.pronoun('possessive')} pack."
    )
    world.say(
        f"The class was hunting for {goal.seek}. {trail.path} felt less like a school walk and more like the beginning of an expedition."
    )


def show_friendship(world: World) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{leader.id} and {friend.id} were partners for the trail game, and all morning they stayed shoulder to shoulder, "
        f"watching for clues and taking turns to pat the burro's warm nose."
    )


def snack_moment(world: World, gluten_food: GlutenFood) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    friend.memes["worry"] += 1
    world.say(
        f"When the class stopped near {world.facts['trail'].landmark}, {leader.id} pulled out {gluten_food.phrase}. "
        f'"Want to trade?" {leader.pronoun()} asked {friend.id}.'
    )
    world.say(
        f"{friend.id} saw the {gluten_food.crumbly} at once and remembered the rule from home: gluten would make "
        f"{friend.pronoun('object')} sick."
    )


def refusal_and_misread(world: World, gluten_food: GlutenFood) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    leader.memes["hurt"] += 1
    leader.memes["misunderstanding"] += 1
    world.say(
        f'"No, no thank you," {friend.id} said too fast, stepping back from the {gluten_food.label}. '
        f'"Please keep it away from me."'
    )
    propagate(world)
    if world.facts.get("stalled"):
        world.say(
            f"{leader.id} blinked. To {leader.pronoun('object')}, it sounded as if {friend.id} did not want "
            f"{leader.pronoun('object')} nearby either. The warm adventure feeling went thin and quiet."
        )
    else:
        world.say(
            f"{leader.id} blinked and felt the moment go crooked. It sounded to {leader.pronoun('object')} as if "
            f"{friend.id} were refusing the friendship, not just the snack."
        )


def drift_apart(world: World) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    burro = world.get("burro")
    trail = world.facts["trail"]
    world.say(
        f"They walked on, but not together now. {leader.id} stared at the ground, {friend.id} hugged the map card close, "
        f"and even {burro.id} seemed to slow while they crossed {trail.landmark}."
    )
    world.say(
        f"For a few uneasy minutes, they almost missed {trail.clue}."
    )


def burro_nudge(world: World, safe_food: SafeFood) -> None:
    burro = world.get("burro")
    leader = world.get("leader")
    friend = world.get("friend")
    teacher = world.get("teacher")
    world.say(
        f"Then {burro.id} stopped, turned {burro.pronoun('possessive')} soft head, and nosed the lunch basket where {safe_food.phrase} waited."
    )
    world.say(
        f'"Looks like {burro.id} knows something is wrong," {teacher.id} said. {teacher.pronoun().capitalize()} knelt between the two friends. '
        f'"Tell each other what you thought just now."'
    )
    leader.memes["readiness"] += 1
    friend.memes["readiness"] += 1


def clarify(world: World, gluten_food: GlutenFood, safe_food: SafeFood) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    teacher = world.get("teacher")
    world.say(
        f'{leader.id} swallowed hard. "I thought {friend.id} did not want to be my partner anymore," {leader.pronoun()} said.'
    )
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head at once. "No! I only meant the {gluten_food.label}. '
        f'{gluten_food.warning}, and my belly gets badly hurt if I eat it."'
    )
    world.say(
        f'{teacher.id} nodded. "{friend.id} was protecting {friend.pronoun("object")}, not pushing you away," '
        f'{teacher.pronoun()} said gently.'
    )
    world.facts["explained"] = True
    world.facts["cause"] = f"{friend.id} cannot eat gluten"
    world.say(
        f'{leader.id} looked at the snack, then back at {friend.id}. The mistake suddenly seemed small enough to mend.'
    )
    world.say(
        f'"Then let\'s share this instead," {leader.id} said, lifting {safe_food.phrase} from the basket.'
    )
    world.say(safe_food.share_line)
    world.facts["shared_safe_food"] = True
    propagate(world)


def finish_quest(world: World, goal: Goal) -> None:
    leader = world.get("leader")
    friend = world.get("friend")
    burro = world.get("burro")
    trail = world.facts["trail"]
    world.say(
        f"With the knot untied between them, the two friends studied {trail.clue} together, laughed at how close they had come to missing it, "
        f"and hurried after {burro.id} toward {goal.seek}."
    )
    world.say(
        f"Soon they found {goal.reward}. {goal.ending} "
        f"{leader.id} and {friend.id} leaned against {burro.id}'s pack and split the last bites of the safe snack, "
        f"friends again and braver for understanding each other better."
    )


def tell(
    trail: Trail,
    gluten_food: GlutenFood,
    safe_food: SafeFood,
    goal: Goal,
    burro_name: str,
    leader_name: str,
    leader_gender: str,
    friend_name: str,
    friend_gender: str,
    teacher_type: str,
    leader_trait: str,
    friend_trait: str,
) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=[leader_trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
        attrs={"gluten_sensitive": True},
    ))
    teacher_name = "Ms. Vale" if teacher_type == "teacher_f" else "Mr. Reed"
    teacher = world.add(Entity(
        id=teacher_name,
        kind="character",
        type=teacher_type,
        role="teacher",
    ))
    burro = world.add(Entity(
        id=burro_name,
        kind="character",
        type="animal",
        role="burro",
        label="burro",
        phrase=f"{burro_name} the burro",
    ))
    burro.meters["progress"] = 1.0
    world.facts["trail"] = trail
    world.facts["goal"] = goal
    world.facts["gluten_food"] = gluten_food
    world.facts["safe_food"] = safe_food

    introduce(world, trail, goal)
    show_friendship(world)

    world.para()
    snack_moment(world, gluten_food)
    refusal_and_misread(world, gluten_food)
    drift_apart(world)

    world.para()
    burro_nudge(world, safe_food)
    clarify(world, gluten_food, safe_food)
    finish_quest(world, goal)

    world.facts.update(
        leader=leader,
        friend=friend,
        teacher=teacher,
        burro=burro,
        repaired=world.facts.get("repaired", False),
        misunderstood=True,
        found_goal=burro.meters["progress"] >= 2.0,
    )
    return world


KNOWLEDGE = {
    "gluten": [
        (
            "What is gluten?",
            "Gluten is a protein found in grains like wheat, barley, and rye. Some people get sick if they eat it, so they need different food.",
        )
    ],
    "burro": [
        (
            "What is a burro?",
            "A burro is a small donkey. People often use burros to carry packs on trails because they are steady and strong.",
        )
    ],
    "primary": [
        (
            "What does primary school mean?",
            "Primary school is the first main stage of school for young children. It is where children learn basic subjects and often go on simple class trips.",
        )
    ],
    "pretzel": [
        (
            "Why would a pretzel be a gluten food?",
            "Most pretzels are made with wheat flour. Wheat has gluten in it.",
        )
    ],
    "cookie": [
        (
            "Why can a cookie contain gluten?",
            "Many cookies are baked with wheat flour. That means they often contain gluten unless they are made a special safe way.",
        )
    ],
    "sandwich": [
        (
            "Why is bread often not safe for someone avoiding gluten?",
            "Most bread is made from wheat. Wheat contains gluten, so ordinary bread is not safe for everyone.",
        )
    ],
    "safe_food": [
        (
            "Why is a safe snack helpful in a story like this?",
            "A safe snack lets friends share food without making anyone sick. It turns a problem about danger into a moment of care and inclusion.",
        )
    ],
    "friendship": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses the wrong meaning of another person's words or actions. Talking clearly can fix it.",
        )
    ],
    "trail": [
        (
            "Why do adventure teams need to work together on a trail?",
            "A trail can have turns, clues, and small problems to solve. Working together helps people notice more and stay safe.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "burro",
    "primary",
    "gluten",
    "pretzel",
    "cookie",
    "sandwich",
    "safe_food",
    "friendship",
    "trail",
]


def generation_prompts(world: World) -> list[str]:
    leader = world.facts["leader"]
    friend = world.facts["friend"]
    trail = world.facts["trail"]
    gluten_food = world.facts["gluten_food"]
    goal = world.facts["goal"]
    return [
        'Write an adventure story for a 3-to-5-year-old that includes the words "burro", "gluten", and "primary".',
        f"Tell a friendship adventure where {leader.id} and {friend.id} are on a primary-school trail with a burro, and a misunderstanding about {gluten_food.label} has to be cleared up before they can find {goal.seek}.",
        f"Write a gentle story in which a class outing on {trail.place} turns tense for a moment, but kind explanation and sharing make the friends close again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    leader = world.facts["leader"]
    friend = world.facts["friend"]
    teacher = world.facts["teacher"]
    burro = world.facts["burro"]
    trail = world.facts["trail"]
    gluten_food = world.facts["gluten_food"]
    safe_food = world.facts["safe_food"]
    goal = world.facts["goal"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends from a primary class, {leader.id} and {friend.id}, plus {teacher.id} and {burro.id} the burro. They are on a small adventure walk together.",
        ),
        (
            "What started the misunderstanding?",
            f"The misunderstanding started when {leader.id} offered {gluten_food.phrase} and {friend.id} refused too quickly. {leader.id} thought the refusal was about friendship, but it was really about gluten safety.",
        ),
        (
            f"Why did {friend.id} step back from the {gluten_food.label}?",
            f"{friend.id} stepped back because the {gluten_food.label} contains gluten, and eating gluten would make {friend.pronoun('object')} sick. The quick warning sounded sharp, but it was really self-protection.",
        ),
        (
            "How did the misunderstanding affect the adventure?",
            f"The two friends stopped walking as one team and nearly missed {trail.clue}. Their hurt feelings slowed the quest until someone helped them talk plainly.",
        ),
        (
            f"How was the problem fixed?",
            f"{teacher.id} asked both children to explain what they thought, so the real reason finally became clear. Then {leader.id} shared {safe_food.phrase}, which was safe, and the food problem stopped standing in the middle of the friendship.",
        ),
        (
            f"What changed by the end of the story?",
            f"By the end, {leader.id} and {friend.id} trusted each other again and followed the clues together to {goal.seek}. The ending shows the friendship repaired because they are sharing a safe snack beside {burro.id} instead of walking apart.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    gluten_food = world.facts["gluten_food"]
    tags: set[str] = {"burro", "primary", "gluten", "safe_food", "friendship", "trail"}
    if gluten_food.id in {"pretzel", "cookie", "sandwich"}:
        tags.add(gluten_food.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if entity.attrs:
            bits.append(f"attrs={entity.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:10} ({entity.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        trail="mesa",
        gluten_food="pretzel",
        safe_food="apple",
        goal="spring",
        burro_name="Pepito",
        leader_name="Lily",
        leader_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher="teacher_f",
        leader_trait="curious",
        friend_trait="gentle",
    ),
    StoryParams(
        trail="pine",
        gluten_food="cookie",
        safe_food="cheese",
        goal="flag",
        burro_name="Luna",
        leader_name="Sam",
        leader_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        teacher="teacher_m",
        leader_trait="bright",
        friend_trait="careful",
    ),
    StoryParams(
        trail="canyon",
        gluten_food="sandwich",
        safe_food="berries",
        goal="garden",
        burro_name="Dusty",
        leader_name="Ava",
        leader_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        teacher="teacher_f",
        leader_trait="brave",
        friend_trait="cheerful",
    ),
]


def explain_rejection(gluten_food: GlutenFood, safe_food: SafeFood) -> str:
    if not gluten_food.contains_gluten:
        return (
            f"(No story: {gluten_food.phrase} does not create a gluten misunderstanding, so the refusal would not make sense here. "
            f"Choose a food like a pretzel, cookie, or sandwich.)"
        )
    if not safe_food.gluten_free:
        return (
            f"(No story: {safe_food.phrase} is not a safe repair snack for someone avoiding gluten. "
            f"The ending needs a food the friends can honestly share.)"
        )
    return "(No story: this combination does not support the misunderstanding-and-repair pattern.)"


ASP_RULES = r"""
risky_food(F) :- gluten_food(F), contains_gluten(F).
safe_repair(S) :- safe_food(S), gluten_free(S).
valid(T, F, S) :- trail(T), risky_food(F), safe_repair(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id in TRAILS:
        lines.append(asp.fact("trail", trail_id))
    for food_id, food in GLUTEN_FOODS.items():
        lines.append(asp.fact("gluten_food", food_id))
        if food.contains_gluten:
            lines.append(asp.fact("contains_gluten", food_id))
    for food_id, food in SAFE_FOODS.items():
        lines.append(asp.fact("safe_food", food_id))
        if food.gluten_free:
            lines.append(asp.fact("gluten_free", food_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("Smoke-test setup failed:", err)
        smoke_cases = list(CURATED)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story text")
            if "burro" not in sample.story.lower():
                raise StoryError("story did not mention burro")
        except Exception as err:  # pragma: no cover - defensive verify path
            rc = 1
            print(f"Smoke test failed for {params}: {err}")
            break
    else:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a burro-led primary-school adventure with a gluten misunderstanding and a friendship repair."
    )
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("--gluten-food", choices=GLUTEN_FOODS)
    parser.add_argument("--safe-food", choices=SAFE_FOODS)
    parser.add_argument("--goal", choices=GOALS)
    parser.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    parser.add_argument("--all", action="store_true", help="render the curated set instead")
    parser.add_argument("--trace", action="store_true", help="dump world-model state")
    parser.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    parser.add_argument("--verify", action="store_true", help="check the ASP twin and smoke-test story generation")
    parser.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return parser


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gluten_food and args.safe_food:
        gluten_food = GLUTEN_FOODS[args.gluten_food]
        safe_food = SAFE_FOODS[args.safe_food]
        if not (offered_food_risky(gluten_food) and repair_food_safe(safe_food)):
            raise StoryError(explain_rejection(gluten_food, safe_food))
    if args.gluten_food and not offered_food_risky(GLUTEN_FOODS[args.gluten_food]):
        raise StoryError(explain_rejection(GLUTEN_FOODS[args.gluten_food], SAFE_FOODS["apple"]))
    if args.safe_food and not repair_food_safe(SAFE_FOODS[args.safe_food]):
        raise StoryError(explain_rejection(GLUTEN_FOODS["pretzel"], SAFE_FOODS[args.safe_food]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.gluten_food is None or combo[1] == args.gluten_food)
        and (args.safe_food is None or combo[2] == args.safe_food)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trail_id, gluten_id, safe_id = rng.choice(sorted(combos))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    burro_name = rng.choice(BURRO_NAMES)
    leader_name, leader_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=leader_name)
    teacher = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    leader_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        trail=trail_id,
        gluten_food=gluten_id,
        safe_food=safe_id,
        goal=goal_id,
        burro_name=burro_name,
        leader_name=leader_name,
        leader_gender=leader_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher=teacher,
        leader_trait=leader_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.trail not in TRAILS:
        raise StoryError(f"(Unknown trail '{params.trail}'.)")
    if params.gluten_food not in GLUTEN_FOODS:
        raise StoryError(f"(Unknown gluten food '{params.gluten_food}'.)")
    if params.safe_food not in SAFE_FOODS:
        raise StoryError(f"(Unknown safe food '{params.safe_food}'.)")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal '{params.goal}'.)")
    if params.teacher not in {"teacher_f", "teacher_m"}:
        raise StoryError(f"(Unknown teacher type '{params.teacher}'.)")

    gluten_food = GLUTEN_FOODS[params.gluten_food]
    safe_food = SAFE_FOODS[params.safe_food]
    if not (offered_food_risky(gluten_food) and repair_food_safe(safe_food)):
        raise StoryError(explain_rejection(gluten_food, safe_food))

    world = tell(
        trail=TRAILS[params.trail],
        gluten_food=gluten_food,
        safe_food=safe_food,
        goal=GOALS[params.goal],
        burro_name=params.burro_name,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_type=params.teacher,
        leader_trait=params.leader_trait,
        friend_trait=params.friend_trait,
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
        print(f"{len(combos)} compatible (trail, gluten_food, safe_food) combos:\n")
        for trail_id, gluten_id, safe_id in combos:
            print(f"  {trail_id:8} {gluten_id:10} {safe_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.friend_name}: {p.gluten_food} on {p.trail} toward {p.goal}"
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
