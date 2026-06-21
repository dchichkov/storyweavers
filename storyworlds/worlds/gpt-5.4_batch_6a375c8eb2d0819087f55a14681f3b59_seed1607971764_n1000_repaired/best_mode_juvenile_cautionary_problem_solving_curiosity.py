#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py
=====================================================================================

A standalone story world for a small folk-tale domain about curiosity, caution,
and problem solving. A juvenile villager sees a bright thing caught in a risky
place and must learn the best mode for solving the problem: not with bare hands,
but with patience, help, and the right tool.

Run it
------
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py --hiding well --prize bucket
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py --tool net
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py --qa --json
    python storyworlds/worlds/gpt-5.4/best_mode_juvenile_cautionary_problem_solving_curiosity.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CAREFUL_TRAITS = {"careful", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "doe", "vixen"}
        male = {"boy", "father", "man", "buck", "fox", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    path: str
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HidingPlace:
    id: str
    label: str
    the: str
    danger: str
    scene: str
    reach_line: str
    mishap_text: str
    consequence: str
    hazard: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    glint: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    works_for: set[str] = field(default_factory=set)
    action: str = ""
    sense: int = 2
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


def careful_enough(trait: str) -> bool:
    return trait in CAREFUL_TRAITS


def tool_fits(hiding: HidingPlace, prize: Prize, tool: Tool) -> bool:
    return hiding.hazard in tool.handles and prize.id in tool.works_for and tool.sense >= SENSE_MIN


def best_tool_for(hiding: HidingPlace, prize: Prize) -> Tool:
    fits = [tool for tool in TOOLS.values() if tool_fits(hiding, prize, tool)]
    if not fits:
        raise StoryError("(No story: this prize cannot be recovered safely from that place with the available tools.)")
    return max(fits, key=lambda t: (t.sense, t.id))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hiding_id in sorted(setting.affords):
            hiding = HIDING_PLACES[hiding_id]
            for prize_id, prize in PRIZES.items():
                try:
                    best_tool_for(hiding, prize)
                except StoryError:
                    continue
                combos.append((setting_id, hiding_id, prize_id))
    return combos


def explain_tool_rejection(hiding: HidingPlace, prize: Prize, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it is known in the world, but it is not a sensible choice here. "
            f"The best mode is to use a steadier tool meant for the danger.)"
        )
    if hiding.hazard not in tool.handles:
        return (
            f"(No story: {tool.phrase} does not safely handle {hiding.the}. "
            f"Pick a tool that matches the danger there.)"
        )
    if prize.id not in tool.works_for:
        return (
            f"(No story: {tool.phrase} cannot catch or lift the {prize.label}. "
            f"Pick a tool shaped for that object.)"
        )
    return "(No story: that tool does not fit this problem.)"


def explain_combo_rejection(setting: Setting, hiding: HidingPlace, prize: Prize) -> str:
    if hiding.id not in setting.affords:
        return (
            f"(No story: {hiding.the} is not part of {setting.place}, so the tale has nowhere to happen.)"
        )
    return (
        f"(No story: there is no safe tool in this world for taking the {prize.label} from {hiding.the}. "
        f"The problem needs a believable solution.)"
    )


def opening(world: World, hero: Entity, elder: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"In the old days, when paths still listened to footsteps, there was {setting.place}. "
        f"{setting.opening}"
    )
    world.say(
        f"In that place lived {hero.id}, a juvenile {hero.attrs['animal']} with bright eyes and a quicker wonder than most."
    )
    world.say(
        f"The folk there often repeated {elder.id}'s saying: the best mode for following curiosity was with care, a clear head, and help close by."
    )


def discover(world: World, hero: Entity, hiding: HidingPlace, prize: Prize, setting: Setting) -> None:
    world.say(
        f"One evening {hero.id} followed {setting.path} and saw {prize.glint} in {hiding.the}. "
        f"It was {prize.phrase}, caught where little hands should not hurry."
    )
    world.say(
        f"{hero.pronoun().capitalize()} crept nearer, because curiosity can whisper louder than a bell."
    )


def temptation(world: World, hero: Entity, hiding: HidingPlace, prize: Prize) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"{hiding.scene} {hiding.reach_line} The sight of the {prize.label} tugged at {hero.pronoun('possessive')} thoughts."
    )


def call_for_help(world: World, hero: Entity, elder: Entity, hiding: HidingPlace) -> None:
    hero.memes["wisdom"] += 1
    hero.memes["fear"] += 0.5
    world.say(
        f"{hero.id} remembered the village saying, stepped back from {hiding.the}, and called for {elder.id} instead."
    )
    world.say(
        f'"Curiosity is good," {hero.pronoun()} murmured, "but I do not want {hiding.consequence}."'
    )


def rash_reach(world: World, hero: Entity, hiding: HidingPlace) -> None:
    hero.meters["mishap"] += 1
    hero.memes["fear"] += 1
    hero.memes["regret"] += 1
    world.say(
        f"But {hero.id} forgot the saying for one small moment and reached in bare-handed."
    )
    world.say(hiding.mishap_text)


def elder_arrives(world: World, elder: Entity, hero: Entity, tool: Tool) -> None:
    elder.memes["care"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"At that very turn of the tale, {elder.id} came along carrying {tool.phrase}."
    )
    world.say(
        f'{elder.id} did not scold at once. "{hero.id}," {elder.pronoun()} said, "a sharp wish needs a wiser hand."'
    )


def solve_problem(world: World, elder: Entity, hero: Entity, hiding: HidingPlace, prize: Prize, tool: Tool) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["recovered"] += 1
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"Then {elder.id} showed {hero.pronoun('object')} the right way. {elder.pronoun().capitalize()} {tool.action}, and soon the {prize.label} was safe on the grass."
    )
    world.say(
        f'"That," said {elder.id}, "is the best mode: first understand the trouble, then choose the tool that fits it."'
    )


def lesson(world: World, elder: Entity, hero: Entity, hiding: HidingPlace, prize: Prize) -> None:
    hero.memes["lesson"] += 1
    elder.memes["care"] += 1
    if hero.meters["mishap"] >= THRESHOLD:
        world.say(
            f"{hero.id} looked at {hero.pronoun('possessive')} sore hand and nodded. {hero.pronoun().capitalize()} had learned that {hiding.consequence} can begin with only one hasty reach."
        )
    else:
        world.say(
            f"{hero.id} looked from {hiding.the} to the {prize.label} and nodded. {hero.pronoun().capitalize()} had learned that stepping back can be as brave as stepping forward."
        )
    world.say(
        f"Together they carried the {prize.label} home, and from then on {hero.id} treated every mystery as a problem to be solved, not a trap to leap into."
    )


def ending_image(world: World, hero: Entity, elder: Entity, tool: Tool, prize: Prize) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Later, whenever some bright little riddle flashed in moss or water, {hero.id} went first for a grown hand or {tool.label}, and only then for the prize."
    )
    world.say(
        f"So the tale was told: a juvenile heart may be quick, but wisdom makes it steady, and that is why the village remembered {hero.id} and the {prize.label} for many seasons."
    )


def tell(
    setting: Setting,
    hiding: HidingPlace,
    prize: Prize,
    tool: Tool,
    *,
    hero_name: str = "Pip",
    hero_type: str = "girl",
    animal: str = "hedgehog",
    trait: str = "careful",
    elder_name: str = "Aunt Brindle",
    elder_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=[trait],
            attrs={"animal": animal},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            attrs={"animal": "badger"},
        )
    )
    prize_ent = world.add(
        Entity(
            id="prize",
            kind="thing",
            type="prize",
            label=prize.label,
            attrs={"config": prize.id},
        )
    )
    hazard_ent = world.add(
        Entity(
            id="hiding",
            kind="thing",
            type="place",
            label=hiding.label,
            attrs={"hazard": hiding.hazard},
        )
    )

    hero.memes["curiosity"] = 1.0
    hero.memes["caution"] = 1.0 if careful_enough(trait) else 0.0
    hero.meters["mishap"] = 0.0
    prize_ent.meters["recovered"] = 0.0
    hazard_ent.meters["risk"] = 1.0

    opening(world, hero, elder, setting)
    discover(world, hero, hiding, prize, setting)

    world.para()
    temptation(world, hero, hiding, prize)

    if careful_enough(trait):
        call_for_help(world, hero, elder, hiding)
    else:
        rash_reach(world, hero, hiding)

    world.para()
    elder_arrives(world, elder, hero, tool)
    solve_problem(world, elder, hero, hiding, prize, tool)
    lesson(world, elder, hero, hiding, prize)

    world.para()
    ending_image(world, hero, elder, tool, prize)

    outcome = "averted" if careful_enough(trait) else "mishap_resolved"
    world.facts.update(
        hero=hero,
        elder=elder,
        prize_cfg=prize,
        hiding_cfg=hiding,
        setting=setting,
        tool=tool,
        outcome=outcome,
        mishap=hero.meters["mishap"] >= THRESHOLD,
        recovered=prize_ent.meters["recovered"] >= THRESHOLD,
        animal=animal,
    )
    return world


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        place="the orchard at Mossbell Hollow",
        opening="Apple boughs leaned over the lane, and even the crows sounded as if they knew old stories.",
        path="the root-path under the apple trees",
        affords={"thorn_bush", "well"},
    ),
    "reedbank": Setting(
        id="reedbank",
        place="the reed-bank of Lantern Mere",
        opening="The reeds bowed and whispered, and the water kept the sky folded inside it.",
        path="the narrow bank where the reeds parted",
        affords={"pond_edge", "thorn_bush"},
    ),
    "millyard": Setting(
        id="millyard",
        place="the old mill-yard beyond Willow Gate",
        opening="The wheel slept by day, and the stones held a cool hush as if giants had once worked there.",
        path="the worn path by the old stones",
        affords={"well", "pond_edge"},
    ),
}

HIDING_PLACES = {
    "thorn_bush": HidingPlace(
        id="thorn_bush",
        label="thorn bush",
        the="the thorn bush",
        danger="thorns",
        scene="Its branches hooked together like little claws, and every twig seemed to say wait",
        reach_line="One could see the object plainly, but not touch it without paying in scratches.",
        mishap_text="The thorns kissed across the fingers at once, and {name} sprang back with a gasp. A tiny sting was enough to teach how sharp foolishness can be.".replace("{name}", "the child"),
        consequence="to let the thorns bite deeper",
        hazard="thorn",
        tags={"thorn", "curiosity"},
    ),
    "well": HidingPlace(
        id="well",
        label="old well",
        the="the old well",
        danger="depth",
        scene="Stone circled the dark opening, and the echo under it sounded deeper than evening",
        reach_line="The object could be seen below, but the rim was no place for a hasty lean.",
        mishap_text="The stones shifted dust beneath the small feet, and the child lurched at the rim before scrambling back. Even one frightened heartbeat showed how near a fall can live.",
        consequence="to tumble where the dark was deeper than bravery",
        hazard="depth",
        tags={"well", "curiosity"},
    ),
    "pond_edge": HidingPlace(
        id="pond_edge",
        label="pond edge",
        the="the pond edge",
        danger="slipping water",
        scene="Mud gleamed there like polished soap, and the water lapped with a quiet, tricky tongue",
        reach_line="The object floated near enough to invite a grab, yet far enough to pull a child into a slip.",
        mishap_text="One foot slid in the slick mud, and the child sat down with a splash at the edge. Cold water up the legs can cool a hot mistake very quickly.",
        consequence="to slide into the cold water",
        hazard="water",
        tags={"pond", "curiosity"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        id="ribbon",
        label="ribbon spool",
        phrase="a little ribbon spool from the weaving basket",
        glint="a bright twist of red",
        tags={"ribbon"},
    ),
    "bucket": Prize(
        id="bucket",
        label="copper bucket",
        phrase="a small copper bucket with a bent handle",
        glint="a copper flash",
        tags={"bucket"},
    ),
    "lantern": Prize(
        id="lantern",
        label="toy lantern",
        phrase="a toy lantern with blue glass",
        glint="a blue wink",
        tags={"lantern"},
    ),
}

TOOLS = {
    "forked_branch": Tool(
        id="forked_branch",
        label="forked branch",
        phrase="a forked branch",
        handles={"thorn"},
        works_for={"ribbon"},
        action="slid the forked branch under the ribbon spool and lifted it free without touching a single thorn",
        sense=3,
        tags={"branch_tool", "thorn"},
    ),
    "hook_rope": Tool(
        id="hook_rope",
        label="rope with a hook",
        phrase="a rope with a little hook tied to its end",
        handles={"depth"},
        works_for={"bucket"},
        action="lowered the hook with patient hands, caught the bucket's bent handle, and drew it up slow and steady",
        sense=3,
        tags={"hook", "well"},
    ),
    "reed_net": Tool(
        id="reed_net",
        label="reed net",
        phrase="a light reed net on a long pole",
        handles={"water"},
        works_for={"lantern"},
        action="reached the reed net across the water and scooped the toy lantern in one smooth lift",
        sense=3,
        tags={"net", "pond"},
    ),
    "bare_hand": Tool(
        id="bare_hand",
        label="bare hand",
        phrase="a bare hand",
        handles=set(),
        works_for=set(),
        action="reached with empty fingers",
        sense=1,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Pip", "Tansy", "Mira", "Nell", "Wren", "Luma"]
BOY_NAMES = ["Pip", "Rowan", "Bram", "Toll", "Ash", "Nico"]
ANIMALS = ["hedgehog", "rabbit", "fox", "goat", "mole", "otter"]
TRAITS = ["careful", "patient", "thoughtful", "bold", "hasty", "restless"]
ELDERS = ["Aunt Brindle", "Old Fen", "Mother Hazel", "Uncle Rowan"]


@dataclass
class StoryParams:
    setting: str
    hiding: str
    prize: str
    tool: str
    hero_name: str
    hero_type: str
    animal: str
    trait: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "thorn": [
        (
            "Why are thorn bushes hard to reach into safely?",
            "Thorn bushes have sharp points that can scratch skin quickly. Something that looks close inside them can still hurt you when you grab for it.",
        )
    ],
    "well": [
        (
            "Why is an old well dangerous?",
            "An old well is deep, and its stone rim can be slippery or uneven. Leaning over it without help can lead to a bad fall.",
        )
    ],
    "pond": [
        (
            "Why can a pond edge be slippery?",
            "Mud by a pond is often smooth and wet, so feet can slide on it. That is why a child can slip even when the water looks calm.",
        )
    ],
    "hook": [
        (
            "What is a hook on a rope good for?",
            "A hook on a rope can catch a handle and pull something up from deep below. It lets you reach without leaning your body into danger.",
        )
    ],
    "net": [
        (
            "What is a net good for near water?",
            "A net can scoop something floating on water without needing you to step into the slippery edge. It helps you reach farther and stay safer.",
        )
    ],
    "branch_tool": [
        (
            "How can a forked branch help with thorns?",
            "A forked branch can lift or nudge something caught in thorns while your hands stay back. It makes space between your skin and the sharp points.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity good or bad?",
            "Curiosity is good because it makes you want to learn and look closely. It becomes dangerous only when you rush into a problem without thinking.",
        )
    ],
    "ask_help": [
        (
            "Why is asking for help a smart choice?",
            "Asking for help brings a bigger plan and often the right tool. It can turn a risky problem into a safe one.",
        )
    ],
}
KNOWLEDGE_ORDER = ["curiosity", "thorn", "well", "pond", "branch_tool", "hook", "net", "ask_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hiding = f["hiding_cfg"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the words "best", "mode", and "juvenile". The tale should show curiosity leading to caution when a child sees a {prize.label} in {hiding.the}.',
            f"Tell a folk-style story where a juvenile {f['animal']} named {hero.id} wants to reach into {hiding.the}, but remembers a village saying and asks for help instead.",
            "Write a gentle cautionary story about problem solving, where the child steps back from danger and learns that the best mode for curiosity is patience.",
        ]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "best", "mode", and "juvenile". The tale should show curiosity causing a small mistake before a wise elder solves the problem.',
        f"Tell a cautionary folk tale where a juvenile {f['animal']} named {hero.id} reaches toward {hiding.the} to get a {prize.label}, then learns to use the right tool.",
        "Write a simple story about problem solving and curiosity, where a child makes one hasty move, then learns the best mode is to understand the trouble and ask for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    hiding = f["hiding_cfg"]
    prize = f["prize_cfg"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a juvenile {f['animal']}, and {elder.id}, the wise elder who helped. The tale follows what happened when curiosity led {hero.pronoun('object')} close to danger.",
        ),
        (
            f"What did {hero.id} find?",
            f"{hero.id} found {prize.phrase} in {hiding.the}. The bright sight made {hero.pronoun('object')} want to hurry closer and take it at once.",
        ),
        (
            f"Why was {hiding.the} dangerous?",
            f"{hiding.The} was dangerous because of {hiding.danger}. The place invited a quick reach, but it could hurt a child who moved too fast.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {hero.id} do before touching the {prize.label}?",
                f"{hero.id} stepped back and called for {elder.id} instead of reaching in. That choice solved the problem before the danger could hurt {hero.pronoun('object')}.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} reached in too quickly?",
                f"{hero.id} had a small mishap at {hiding.the}. The scare taught {hero.pronoun('object')} that one hasty move can start real trouble very fast.",
            )
        )
    qa.append(
        (
            f"How did {elder.id} solve the problem?",
            f"{elder.id} used {tool.phrase} to get the {prize.label} safely. {elder.pronoun().capitalize()} first matched the tool to the danger, and that is why the problem could be solved without more harm.",
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{hero.id} learned that curiosity should be guided by care. The best mode was to understand the danger, choose the right tool, and ask for help instead of grabbing blindly.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"curiosity", "ask_help"} | set(f["hiding_cfg"].tags) | set(f["tool"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard",
        hiding="thorn_bush",
        prize="ribbon",
        tool="forked_branch",
        hero_name="Tansy",
        hero_type="girl",
        animal="rabbit",
        trait="careful",
        elder_name="Aunt Brindle",
        elder_type="mother",
    ),
    StoryParams(
        setting="millyard",
        hiding="well",
        prize="bucket",
        tool="hook_rope",
        hero_name="Bram",
        hero_type="boy",
        animal="goat",
        trait="bold",
        elder_name="Old Fen",
        elder_type="father",
    ),
    StoryParams(
        setting="reedbank",
        hiding="pond_edge",
        prize="lantern",
        tool="reed_net",
        hero_name="Mira",
        hero_type="girl",
        animal="otter",
        trait="restless",
        elder_name="Mother Hazel",
        elder_type="mother",
    ),
    StoryParams(
        setting="orchard",
        hiding="well",
        prize="bucket",
        tool="hook_rope",
        hero_name="Ash",
        hero_type="boy",
        animal="fox",
        trait="patient",
        elder_name="Uncle Rowan",
        elder_type="father",
    ),
]


ASP_RULES = r"""
% compatibility gate
valid(S,H,P) :- setting(S), affords(S,H), hiding(H), prize(P), has_safe_tool(H,P).
has_safe_tool(H,P) :- tool(T), sensible(T), handles(T,HZ), hazard(H,HZ), works_for(T,P).

sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

% outcome model
careful_now :- chosen_trait(Tr), careful_trait(Tr).
outcome(averted) :- careful_now.
outcome(mishap_resolved) :- not careful_now.

best_tool(H,P,T) :- tool(T), sensible(T), handles(T,HZ), hazard(H,HZ), works_for(T,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for hid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, hid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("hazard", hid, hiding.hazard))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        for hz in sorted(tool.handles):
            lines.append(asp.fact("handles", tid, hz))
        for pid in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_trait", params.trait)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_best_tools() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show best_tool/3."))
    return sorted(set(asp.atoms(model, "best_tool")))


def outcome_of(params: StoryParams) -> str:
    return "averted" if careful_enough(params.trait) else "mishap_resolved"


def smoke_emit(sample: StorySample) -> None:
    if not sample.story or "best mode" not in sample.story:
        raise StoryError("Smoke test failed: story did not render the expected folk-tale lesson.")
    if sample.world is None:
        raise StoryError("Smoke test failed: sample has no world model.")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for curated case: {params}")
            break
    else:
        print(f"OK: outcome model matches Python on {len(CURATED)} curated cases.")

    best_from_asp = {(h, p, t) for (h, p, t) in asp_best_tools()}
    for hiding_id, hiding in HIDING_PLACES.items():
        for prize_id, prize in PRIZES.items():
            try:
                tool = best_tool_for(hiding, prize)
            except StoryError:
                continue
            if (hiding_id, prize_id, tool.id) not in best_from_asp:
                rc = 1
                print(f"MISMATCH in tool reasoning for {(hiding_id, prize_id)}.")
                break
    if rc == 0:
        print("OK: ASP tool facts cover Python's best-tool choices.")

    try:
        sample = generate(CURATED[0])
        smoke_emit(sample)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a juvenile grows curious, danger appears, and the right tool solves the problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder-name", choices=ELDERS)
    ap.add_argument("--elder-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and safe tools from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hiding and args.prize and args.tool:
        hiding = HIDING_PLACES[args.hiding]
        prize = PRIZES[args.prize]
        tool = TOOLS[args.tool]
        if not tool_fits(hiding, prize, tool):
            raise StoryError(explain_tool_rejection(hiding, prize, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        setting_id = args.setting or next(iter(SETTINGS))
        hiding_id = args.hiding or next(iter(HIDING_PLACES))
        prize_id = args.prize or next(iter(PRIZES))
        raise StoryError(
            explain_combo_rejection(SETTINGS[setting_id], HIDING_PLACES[hiding_id], PRIZES[prize_id])
        )

    setting_id, hiding_id, prize_id = rng.choice(sorted(combos))
    hiding = HIDING_PLACES[hiding_id]
    prize = PRIZES[prize_id]
    if args.tool is not None:
        tool = TOOLS[args.tool]
        if not tool_fits(hiding, prize, tool):
            raise StoryError(explain_tool_rejection(hiding, prize, tool))
        tool_id = args.tool
    else:
        tool_id = best_tool_for(hiding, prize).id

    hero_type = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    elder_name = args.elder_name or rng.choice(ELDERS)
    elder_type = args.elder_type or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        hiding=hiding_id,
        prize=prize_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        animal=animal,
        trait=trait,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    setting = SETTINGS[params.setting]
    hiding = HIDING_PLACES[params.hiding]
    prize = PRIZES[params.prize]
    tool = TOOLS[params.tool]

    if params.hiding not in setting.affords:
        raise StoryError(explain_combo_rejection(setting, hiding, prize))
    if not tool_fits(hiding, prize, tool):
        raise StoryError(explain_tool_rejection(hiding, prize, tool))

    world = tell(
        setting=setting,
        hiding=hiding,
        prize=prize,
        tool=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        animal=params.animal,
        trait=params.trait,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/3.\n#show best_tool/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        tools = asp_best_tools()
        print(f"{len(combos)} valid (setting, hiding, prize) combos:\n")
        for setting_id, hiding_id, prize_id in combos:
            matching = sorted(t for (h, p, t) in tools if h == hiding_id and p == prize_id)
            print(f"  {setting_id:8} {hiding_id:11} {prize_id:8}  [{', '.join(matching)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.prize} in {p.hiding} ({p.setting}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
