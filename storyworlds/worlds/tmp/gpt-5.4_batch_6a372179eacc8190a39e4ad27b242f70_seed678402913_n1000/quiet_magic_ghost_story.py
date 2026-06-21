#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py
=====================================================

A small, gentle ghost-story world about a child who meets a quiet ghost and
uses a bit of magic to help.

The core premise is narrow on purpose:

* a child notices a quiet ghost in a hush-filled place
* the ghost is sad because a keepsake is lost in some fitting hiding spot
* the child uses a magical helper that can honestly solve that kind of problem
* if the help is quick and strong enough, the keepsake is found and the ghost rests
* if the child hesitates too long, the ghost is comforted but must wait a little longer

The world model tracks simple physical meters (chill, glow, hidden, found) and
emotional memes (fear, wonder, sadness, hope, calm, bravery). Prose is driven
from the simulated state, not from a single frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py --setting attic --goal locket --tool moon_lantern
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/quiet_magic_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opener: str
    hush: str
    glow_line: str
    hiding_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    lost_item: str
    item_phrase: str
    hiding_place: str
    spot_tag: str
    need_tag: str
    whisper: str
    release_image: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    use_text: str
    calm_text: str
    grants: set[str] = field(default_factory=set)
    power: int = 0
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ghost_chill(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if not ghost or not room or not child:
        return out
    if ghost.memes["sadness"] >= THRESHOLD:
        sig = ("ghost_chill",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["chill"] += 1
            child.memes["fear"] += 1
            out.append("__chill__")
    return out


def _r_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    tool = world.entities.get("tool")
    room = world.entities.get("room")
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not tool or not room or not child or not ghost:
        return out
    if tool.meters["active"] >= THRESHOLD:
        sig = ("magic_glow",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["glow"] += 1
            child.memes["bravery"] += 1
            child.memes["wonder"] += 1
            ghost.memes["hope"] += 1
            out.append("__glow__")
    return out


def _r_rest(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.entities.get("keepsake")
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if not keepsake or not ghost or not room or not child:
        return out
    if keepsake.meters["found"] >= THRESHOLD:
        sig = ("rest",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.memes["calm"] += 2
            ghost.memes["sadness"] = 0.0
            child.memes["fear"] = 0.0
            room.meters["chill"] = 0.0
            room.meters["peace"] += 1
            out.append("__rest__")
    return out


CAUSAL_RULES = [
    Rule(name="ghost_chill", tag="physical", apply=_r_ghost_chill),
    Rule(name="magic_glow", tag="magic", apply=_r_magic_glow),
    Rule(name="rest", tag="resolution", apply=_r_rest),
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


def valid_combo(setting: Setting, goal: Goal, tool: MagicTool) -> bool:
    return goal.spot_tag in setting.hiding_tags and goal.need_tag in tool.grants


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for gid, goal in GOALS.items():
            for tid, tool in TOOLS.items():
                if valid_combo(setting, goal, tool):
                    combos.append((sid, gid, tid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    setting = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    tool = TOOLS[params.tool]
    if not valid_combo(setting, goal, tool):
        raise StoryError(explain_rejection(setting, goal, tool))
    return "rested" if tool.power >= goal.difficulty + params.hesitation else "comforted"


def predict_outcome(setting: Setting, goal: Goal, tool: MagicTool, hesitation: int) -> str:
    probe = StoryParams(
        setting=setting.id,
        goal=goal.id,
        tool=tool.id,
        child_name="Nora",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="careful",
        hesitation=hesitation,
        seed=None,
    )
    return outcome_of(probe)


def introduce(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"One quiet evening, {child.id} stayed near {setting.place} while "
        f"{child.pronoun('possessive')} {elder.label_word} folded blankets downstairs."
    )
    world.say(setting.opener)
    world.say(setting.hush)


def first_sign(world: World, child: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then {child.id} noticed something strange: a small pale shape waited in the dimness, "
        f"almost as still as dust in moonlight."
    )
    world.say(setting.glow_line)


def reveal_ghost(world: World, child: Entity, ghost: Entity, goal: Goal) -> None:
    ghost.memes["sadness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"It was a little ghost, not rattling chains or roaring at all, only watching "
        f"{child.id} with wide, worried eyes."
    )
    world.say(
        f'"Please," the ghost whispered, so softly that {child.id} had to lean close. '
        f'"{goal.whisper}"'
    )
    if world.get("room").meters["chill"] >= THRESHOLD:
        world.say(
            f"The air turned cool enough to prickle {child.pronoun('possessive')} arms, "
            f"and for a moment {child.id} wanted to run."
        )


def decide_to_help(world: World, child: Entity, elder: Entity, tool_cfg: MagicTool) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"But the ghost sounded more lonely than scary, and {child.id} remembered what "
        f"{child.pronoun('possessive')} {elder.label_word} always said: quiet things are easier "
        f"to understand when you listen first."
    )
    world.say(
        f"On a nearby shelf sat {tool_cfg.phrase}, the sort of family magic that was used for "
        f"helping and never for showing off."
    )


def use_magic(world: World, child: Entity, tool: Entity, tool_cfg: MagicTool, goal: Goal) -> None:
    tool.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} picked up {tool_cfg.phrase} and {tool_cfg.use_text}."
    )
    if world.get("room").meters["glow"] >= THRESHOLD:
        world.say(
            f"A soft glow spread over the boards and boxes, and the little ghost stopped trembling."
        )
    world.say(tool_cfg.calm_text)


def search(world: World, child: Entity, ghost: Entity, goal: Goal, outcome: str) -> None:
    room = world.get("room")
    keepsake = world.get("keepsake")
    room.meters["searched"] += 1
    child.memes["focus"] += 1
    world.say(
        f"Together they followed the light toward {goal.hiding_place}."
    )
    if outcome == "rested":
        keepsake.meters["found"] += 1
        keepsake.meters["hidden"] = 0.0
        ghost.memes["hope"] += 1
        propagate(world, narrate=False)
        world.say(
            f"There, tucked away at last, lay {goal.item_phrase}."
        )
    else:
        ghost.memes["hope"] += 1
        ghost.memes["sadness"] = max(0.0, ghost.memes["sadness"] - 0.5)
        child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
        world.say(
            f"The glow reached the hiding place, but dawn was already thinning the shadows, "
            f"and the lost thing did not show itself fully."
        )


def resting_end(world: World, child: Entity, ghost: Entity, goal: Goal, elder: Entity) -> None:
    world.say(
        f'The ghost gave a small sigh that sounded like a curtain settling. '
        f'"Thank you," it said. "I can remember home now."'
    )
    world.say(goal.release_image)
    world.say(
        f"When {child.id} went downstairs at last, {child.pronoun('possessive')} {elder.label_word} "
        f"looked at {child.pronoun('object')} and smiled as if {elder.pronoun()} could see the warm "
        f"peace still shining around {child.pronoun('object')}."
    )


def comforted_end(world: World, child: Entity, ghost: Entity, goal: Goal, elder: Entity) -> None:
    room = world.get("room")
    room.meters["peace"] += 1
    ghost.memes["calm"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f'The ghost did not disappear, but its face softened. "You heard me," it whispered. '
        f'"That helps more than being alone."'
    )
    world.say(
        f"{child.id} promised to come back with {child.pronoun('possessive')} {elder.label_word} in the morning, "
        f"when careful hands could lift boxes and look properly."
    )
    world.say(
        f"The little ghost curled beside the window, quieter now, while the first gray light made "
        f"the room feel gentle instead of haunted."
    )


def tell(
    setting: Setting,
    goal: Goal,
    tool_cfg: MagicTool,
    child_name: str = "Nora",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    child_trait: str = "careful",
    hesitation: int = 0,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": child_trait},
            tags={child_trait},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label="little ghost",
            role="ghost",
            tags=set(goal.tags),
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="place",
            label=setting.place,
            tags=set(setting.tags),
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            type="magic",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            tags=set(tool_cfg.tags),
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=goal.lost_item,
            phrase=goal.item_phrase,
            tags=set(goal.tags),
        )
    )
    keepsake.meters["hidden"] = 1.0
    child.memes["bravery"] = 1.0 if child_trait in {"careful", "gentle", "patient"} else 0.0

    introduce(world, child, elder, setting)
    first_sign(world, child, setting)

    world.para()
    reveal_ghost(world, child, ghost, goal)
    decide_to_help(world, child, elder, tool_cfg)

    world.para()
    use_magic(world, child, tool, tool_cfg, goal)
    outcome = "rested" if tool_cfg.power >= goal.difficulty + hesitation else "comforted"
    if hesitation:
        world.say(
            f"{child.id} paused for a breath or two before searching, because brave hearts can still beat fast."
        )
    search(world, child, ghost, goal, outcome)

    world.para()
    if outcome == "rested":
        resting_end(world, child, ghost, goal, elder)
    else:
        comforted_end(world, child, ghost, goal, elder)

    world.facts.update(
        child=child,
        elder=elder,
        ghost=ghost,
        room=room,
        tool=tool,
        setting=setting,
        goal=goal,
        tool_cfg=tool_cfg,
        keepsake=keepsake,
        outcome=outcome,
        hesitation=hesitation,
        found=keepsake.meters["found"] >= THRESHOLD,
        peaceful=room.meters["peace"] >= THRESHOLD,
    )
    return world


THEMES_TEXT = "quiet ghost story"

SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic stairs",
        opener="Above the house, the attic beams held the dark like folded wings.",
        hush="Everything was quiet except the tiny creak of old wood and the faraway tick of the hall clock.",
        glow_line="A thread of silver light slid under a trunk and faded again.",
        hiding_tags={"trunk", "beam", "cloth"},
        tags={"attic", "house"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the long upstairs hallway",
        opener="The hallway stretched between the bedrooms with portraits watching from the walls.",
        hush="It was so quiet that even the curtains brushing the floor sounded important.",
        glow_line="A pale shimmer flickered near the umbrella stand and then hid behind the runner rug.",
        hiding_tags={"rug", "frame", "stand"},
        tags={"hallway", "house"},
    ),
    "nursery": Setting(
        id="nursery",
        place="the old nursery door",
        opener="At the end of the passage stood the old nursery, with moonlight laid across the floorboards.",
        hush="The room was quiet in the soft, held-breath way of places that remember songs.",
        glow_line="Near the rocking chair, something pearly blinked once and went still.",
        hiding_tags={"rocker", "toybox", "quilt"},
        tags={"nursery", "house"},
    ),
    "garden": Setting(
        id="garden",
        place="the back garden path",
        opener="Beyond the kitchen, the garden hedges made dark little rooms of leaves and shadow.",
        hush="The night was quiet there, except for dew sliding from one leaf to another.",
        glow_line="A faint blue glimmer floated beside the stone birdbath and drifted toward the ivy bench.",
        hiding_tags={"bench", "ivy", "flowerpot"},
        tags={"garden", "night"},
    ),
}

GOALS = {
    "locket": Goal(
        id="locket",
        lost_item="locket",
        item_phrase="a small silver locket with a faded ribbon tied around it",
        hiding_place="the crack behind an old trunk",
        spot_tag="trunk",
        need_tag="reveal_hidden",
        whisper="My locket is missing, and I cannot rest until I find it.",
        release_image="The ghost held up the locket, and its edges shone once like a star on water before the whole small spirit drifted upward and was gone.",
        difficulty=1,
        tags={"locket", "memory"},
    ),
    "music_box": Goal(
        id="music_box",
        lost_item="music box key",
        item_phrase="the tiny brass key to a music box",
        hiding_place="the folds of a quilt fallen beside the rocker",
        spot_tag="quilt",
        need_tag="hear_memory",
        whisper="The music stopped when the key was lost. I want to hear the song again.",
        release_image="As the key touched the ghost's hands, a lullaby hummed through the room, and the spirit thinned into moonlit mist with a happy smile.",
        difficulty=2,
        tags={"music", "memory"},
    ),
    "button": Goal(
        id="button",
        lost_item="pearl coat button",
        item_phrase="a round pearl button, smooth as a raindrop",
        hiding_place="the rolled edge of the hallway runner rug",
        spot_tag="rug",
        need_tag="reveal_hidden",
        whisper="My best coat lost its last button, and I have been searching ever since.",
        release_image="The pearl button gleamed in the child's palm, and the ghost gave a proud little nod before fading like breath from a windowpane.",
        difficulty=1,
        tags={"button", "coat"},
    ),
    "seed_packet": Goal(
        id="seed_packet",
        lost_item="seed packet",
        item_phrase="a paper packet with moonflower seeds still tucked inside",
        hiding_place="the damp shadow under the ivy bench",
        spot_tag="bench",
        need_tag="wake_growing",
        whisper="My moonflowers were never planted. I have been waiting for one more chance.",
        release_image="When the packet was lifted free, the garden breeze smelled suddenly sweet, and the ghost scattered into silver petals that seemed to bless every sleeping stem.",
        difficulty=2,
        tags={"garden", "flower"},
    ),
}

TOOLS = {
    "moon_lantern": MagicTool(
        id="moon_lantern",
        label="moon lantern",
        phrase="a moon lantern with cloudy glass",
        use_text="turned its little silver key until a round light bloomed inside",
        calm_text="The lantern made the shadows pull back without making the night feel broken.",
        grants={"reveal_hidden"},
        power=1,
        tags={"lantern", "light"},
    ),
    "hush_bell": MagicTool(
        id="hush_bell",
        label="hush bell",
        phrase="a hush bell no bigger than a plum",
        use_text="rang it once, very softly, until the air itself seemed to listen",
        calm_text="The sound did not ring loud; it spread like a promise, finding every lost corner where old music liked to hide.",
        grants={"hear_memory"},
        power=2,
        tags={"bell", "sound"},
    ),
    "star_chalk": MagicTool(
        id="star_chalk",
        label="star chalk",
        phrase="a stick of star chalk wrapped in blue paper",
        use_text="drew one shining circle on the floorboards and one by the wall",
        calm_text="Thin sparks ran along the chalk lines and pointed toward what had been forgotten.",
        grants={"reveal_hidden", "wake_growing"},
        power=2,
        tags={"chalk", "spell"},
    ),
    "dew_spoon": MagicTool(
        id="dew_spoon",
        label="dew spoon",
        phrase="a dew spoon hammered from old silver",
        use_text="touched it to a bead of dew and whispered the waking words",
        calm_text="Where the spoon shone, small sleeping things seemed to remember how to rise.",
        grants={"wake_growing"},
        power=2,
        tags={"garden_magic", "silver"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Clara", "Eva", "Mabel", "Ivy", "Lucy"]
BOY_NAMES = ["Theo", "Eli", "Simon", "Owen", "Leo", "Jude", "Noah", "Finn"]
TRAITS = ["careful", "gentle", "patient", "curious", "brave"]

KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story about a spirit or haunting. In gentle ghost stories, the ghost may be sad or lonely instead of mean."
        )
    ],
    "quiet": [
        (
            "Why can quiet places feel spooky?",
            "Quiet places make small sounds stand out more, so each creak or whisper feels important. That can make a place seem mysterious."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something impossible in ordinary life that happens inside the story world. It might make light, music, or hidden things appear."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so you can see in the dark. In stories, a magical lantern can also reveal things that were hidden."
        )
    ],
    "bell": [
        (
            "Why is a bell useful in a story about listening?",
            "A bell makes a clear sound that can call attention to something. A gentle bell can help characters notice what was quiet before."
        )
    ],
    "spell": [
        (
            "What is a spell?",
            "A spell is a magical act or set of words used to make something happen. Story characters often use spells to help, protect, or reveal."
        )
    ],
    "garden": [
        (
            "What do seeds need to grow?",
            "Seeds need the right mix of soil, water, and time. Some also need warmth and light before they can sprout."
        )
    ],
    "memory": [
        (
            "Why do keepsakes matter to people?",
            "Keepsakes help people remember someone, somewhere, or an important time. A small object can hold a big feeling."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "quiet", "magic", "lantern", "bell", "spell", "garden", "memory"]


@dataclass
class StoryParams:
    setting: str
    goal: str
    tool: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    hesitation: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="attic",
        goal="locket",
        tool="moon_lantern",
        child_name="Nora",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="careful",
        hesitation=0,
        seed=None,
    ),
    StoryParams(
        setting="nursery",
        goal="music_box",
        tool="hush_bell",
        child_name="Theo",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="gentle",
        hesitation=0,
        seed=None,
    ),
    StoryParams(
        setting="garden",
        goal="seed_packet",
        tool="dew_spoon",
        child_name="Ivy",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="patient",
        hesitation=1,
        seed=None,
    ),
    StoryParams(
        setting="hallway",
        goal="button",
        tool="star_chalk",
        child_name="Eli",
        child_gender="boy",
        elder_type="grandmother",
        child_trait="curious",
        hesitation=2,
        seed=None,
    ),
    StoryParams(
        setting="garden",
        goal="seed_packet",
        tool="star_chalk",
        child_name="Clara",
        child_gender="girl",
        elder_type="grandfather",
        child_trait="brave",
        hesitation=0,
        seed=None,
    ),
]


def explain_rejection(setting: Setting, goal: Goal, tool: MagicTool) -> str:
    if goal.spot_tag not in setting.hiding_tags:
        return (
            f"(No story: {goal.lost_item} is hidden in a kind of place this setting does not honestly have. "
            f"{setting.place.capitalize()} does not fit a {goal.spot_tag}-style hiding spot.)"
        )
    if goal.need_tag not in tool.grants:
        return (
            f"(No story: {tool.label} cannot solve this ghost's problem. "
            f"The goal needs magic of type '{goal.need_tag}', but {tool.label} grants "
            f"{sorted(tool.grants)}.)"
        )
    return "(No story: this combination does not make sense in the world.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    goal = f["goal"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "rested":
        return [
            'Write a quiet ghost story for a 3-to-5-year-old that includes the word "quiet" and uses a bit of magic to help a sad ghost.',
            f"Tell a gentle ghost story where {child.id} finds a lonely spirit near {setting.place} and uses {tool.phrase} to find a lost {goal.lost_item}.",
            f"Write a soft spooky story that ends peacefully after a child listens carefully and helps a ghost recover {goal.item_phrase}.",
        ]
    return [
        'Write a quiet ghost story for a 3-to-5-year-old that includes the word "quiet" and uses magic to comfort a ghost, even if the problem is not fully solved that night.',
        f"Tell a gentle ghost story where {child.id} meets a worried spirit near {setting.place} and uses {tool.phrase} to bring hope.",
        f"Write a child-facing spooky story where a ghost is less alone by the end because someone listens and promises to help in the morning.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    goal = f["goal"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who meets a small ghost, and {child.pronoun('possessive')} {elder.label_word} who is nearby in the house. The story follows how {child.id} chooses to help instead of running away."
        ),
        (
            "Why did the ghost seem scary at first?",
            f"The ghost made the air turn cold and strange, which made {child.id} nervous. But it spoke in a soft voice, so the fear changed into concern."
        ),
        (
            f"What did the ghost want?",
            f"The ghost wanted help finding {goal.item_phrase}. That lost keepsake was the reason it could not rest."
        ),
        (
            f"How did {child.id} try to help?",
            f"{child.id} used {tool.phrase} and followed its magic toward {goal.hiding_place}. The tool fit the ghost's problem, so it gave hope instead of making the room feel harsher."
        ),
    ]
    if outcome == "rested":
        qa.append(
            (
                "How was the problem solved?",
                f"The keepsake was found, and that let the ghost remember what it had been waiting for. Once the lost thing was back, the room stopped feeling cold and the ghost could finally rest."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully. The ghost thanked {child.id}, faded away, and left the place feeling warm and calm instead of haunted."
            )
        )
    else:
        qa.append(
            (
                "Was the ghost fully helped that night?",
                f"Not completely. The magic made the ghost calmer and less lonely, but the lost thing was still hidden when dawn came."
            )
        )
        qa.append(
            (
                "How did the ending still show a change?",
                f"The ghost was quieter and more peaceful because someone listened and promised to return with help. The room felt gentle by the end, which showed that fear had turned into kindness."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "quiet", "magic"}
    tool = f["tool_cfg"]
    goal = f["goal"]
    tags |= set(tool.tags)
    if "garden" in goal.tags or "garden" in f["setting"].tags:
        tags.add("garden")
    if "memory" in goal.tags or "music" in goal.tags or "locket" in goal.tags:
        tags.add("memory")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, T) :- setting(S), goal(G), tool(T), spot_tag(G, Spot), hiding(S, Spot), need_tag(G, Need), grants(T, Need).

rested :- chosen_goal(G), chosen_tool(T), difficulty(G, D), power(T, P), hesitation(H), P >= D + H.
comforted :- chosen_goal(G), chosen_tool(T), difficulty(G, D), power(T, P), hesitation(H), P < D + H.

outcome(rested) :- rested.
outcome(comforted) :- comforted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(setting.hiding_tags):
            lines.append(asp.fact("hiding", sid, tag))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("spot_tag", gid, goal.spot_tag))
        lines.append(asp.fact("need_tag", gid, goal.need_tag))
        lines.append(asp.fact("difficulty", gid, goal.difficulty))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, tool.power))
        for grant in sorted(tool.grants):
            lines.append(asp.fact("grants", tid, grant))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_goal", params.goal),
            asp.fact("chosen_tool", params.tool),
            asp.fact("hesitation", params.hesitation),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(100):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            if asp_outcome(params) != outcome_of(params):
                bad += 1
        except StoryError:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a quiet haunting, a bit of magic, and a child who helps."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("--hesitation", type=int, choices=[0, 1, 2], help="how long the child hesitates before searching")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.goal is not None and args.tool is not None:
        setting = SETTINGS[args.setting]
        goal = GOALS[args.goal]
        tool = TOOLS[args.tool]
        if not valid_combo(setting, goal, tool):
            raise StoryError(explain_rejection(setting, goal, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.goal is None or c[1] == args.goal)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, goal_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    hesitation = args.hesitation if args.hesitation is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        setting=setting_id,
        goal=goal_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        hesitation=hesitation,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    tool = TOOLS[params.tool]
    if not valid_combo(setting, goal, tool):
        raise StoryError(explain_rejection(setting, goal, tool))

    world = tell(
        setting=setting,
        goal=goal,
        tool_cfg=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        hesitation=params.hesitation,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, goal, tool) combos:\n")
        for setting, goal, tool in combos:
            print(f"  {setting:8} {goal:11} {tool}")
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
            header = f"### {p.child_name}: {p.goal} in {p.setting} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
