#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py
========================================================

A standalone storyworld for a small fairy-tale sea domain with a **flashback**:
a child of the reef loses a treasured thing near a moray's home, pauses on the
edge of a hasty choice, remembers an earlier lesson, and then solves the problem
with patience and respect.

The world model is intentionally small and concrete:

- a reef place has darkness and a narrow shell-crack
- a lost item has a size and a sparkle
- a light tool must make the crack visible
- a respectful approach can calm the moray
- the flashback changes the present action

Reasonableness gate:
- the item must plausibly fit into the crack at that place
- the chosen light must be bright enough for that dark place
- explicit rude approaches are known to the world but refused by default

Run it
------
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py --place whisper_cleft --item moon_ribbon
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py --tool mirror_shell
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py --approach hook_it_out
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/moray_flashback_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "mergirl", "queen"}
        male = {"boy", "father", "grandfather", "merboy", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    opening: str
    around: str
    dark_line: str
    slot_size: int
    darkness: int
    current: int
    tags: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    size: int
    sparkle: int
    ending_image: str
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
class LightTool:
    id: str
    label: str
    phrase: str
    light: int
    glow_line: str
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
class Approach:
    id: str
    label: str
    sense: int
    calm_score: int
    intro: str
    speak: str
    help_line: str
    qa_help: str
    tags: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str = ""
    item: str = ""
    tool: str = ""
    approach: str = ""
    hero: str = ""
    hero_type: str = "mergirl"
    friend: str = ""
    friend_type: str = "merboy"
    elder: str = "grandmother"
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


def _r_startled_hides(world: World) -> list[str]:
    out: list[str] = []
    moray = world.get("moray")
    item = world.get("item")
    hero = world.get("hero")
    if moray.meters["startled"] >= THRESHOLD:
        sig = ("startled_hides",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["deeper"] += 1
            hero.memes["fear"] += 1
            out.append("__startled__")
    return out


def _r_calm_trust(world: World) -> list[str]:
    out: list[str] = []
    moray = world.get("moray")
    hero = world.get("hero")
    if moray.meters["calm"] >= THRESHOLD and hero.memes["kindness"] >= THRESHOLD:
        sig = ("calm_trust",)
        if sig not in world.fired:
            world.fired.add(sig)
            moray.memes["trust"] += 1
            out.append("__trust__")
    return out


def _r_trust_reveals(world: World) -> list[str]:
    out: list[str] = []
    moray = world.get("moray")
    item = world.get("item")
    if moray.memes["trust"] >= THRESHOLD:
        sig = ("trust_reveals",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["found"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="startled_hides", tag="physical", apply=_r_startled_hides),
    Rule(name="calm_trust", tag="social", apply=_r_calm_trust),
    Rule(name="trust_reveals", tag="physical", apply=_r_trust_reveals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "whisper_cleft": Place(
        id="whisper_cleft",
        label="Whisper Cleft",
        opening="a long crack in a moon-pale reef wall",
        around="silver anemones and ferny sea fans",
        dark_line="The cleft was dark enough to swallow the gleam of a coin.",
        slot_size=2,
        darkness=2,
        current=1,
        tags={"reef", "dark"},
    ),
    "shell_arch": Place(
        id="shell_arch",
        label="Shell Arch",
        opening="a crooked hollow beneath a shell arch",
        around="lace-soft coral and drifting bubbles",
        dark_line="Under the arch, the shadows lay folded like velvet.",
        slot_size=2,
        darkness=1,
        current=1,
        tags={"reef", "shell"},
    ),
    "midnight_grotto": Place(
        id="midnight_grotto",
        label="Midnight Grotto",
        opening="a narrow grotto between black rocks",
        around="blue lanternweed and slow cold currents",
        dark_line="Even at noon, the grotto kept a pocket of night inside it.",
        slot_size=3,
        darkness=3,
        current=2,
        tags={"grotto", "dark"},
    ),
}

ITEMS = {
    "moon_ribbon": LostItem(
        id="moon_ribbon",
        label="moon ribbon",
        phrase="a moon ribbon woven from silver eelgrass",
        size=1,
        sparkle=2,
        ending_image="the ribbon streaming behind her like a little path of moonlight",
        tags={"ribbon", "treasure"},
    ),
    "pearl_crown": LostItem(
        id="pearl_crown",
        label="pearl crown",
        phrase="a tiny pearl crown no bigger than a shell cup",
        size=2,
        sparkle=3,
        ending_image="the pearl crown shining softly above her brow",
        tags={"crown", "treasure"},
    ),
    "star_key": LostItem(
        id="star_key",
        label="star key",
        phrase="a star-shaped key of pale gold",
        size=1,
        sparkle=1,
        ending_image="the little key winking at her from her palm",
        tags={"key", "treasure"},
    ),
}

TOOLS = {
    "glow_pearl": LightTool(
        id="glow_pearl",
        label="glow-pearl",
        phrase="a glow-pearl cupped in both hands",
        light=2,
        glow_line="Its light floated out in a gentle milk-white circle.",
        tags={"light", "pearl"},
    ),
    "lantern_kelp": LightTool(
        id="lantern_kelp",
        label="lantern kelp",
        phrase="a braid of lantern kelp",
        light=3,
        glow_line="The little bulbs along the kelp stem glimmered green and gold.",
        tags={"light", "kelp"},
    ),
    "mirror_shell": LightTool(
        id="mirror_shell",
        label="mirror shell",
        phrase="a polished mirror shell",
        light=1,
        glow_line="It caught only the thinnest trembling strip of light.",
        tags={"light", "shell"},
    ),
}

APPROACHES = {
    "greet_and_wait": Approach(
        id="greet_and_wait",
        label="greet and wait",
        sense=3,
        calm_score=2,
        intro="drew back from the crack and folded her hands instead of snatching",
        speak='"Good moray, I have come for what slipped by mistake. I will wait until you are ready."',
        help_line="After a long, still moment, the moray eased its striped head from the dark, looked at the shining object, and nudged it toward the light with careful teeth.",
        qa_help="The moray moved the lost thing toward the opening after the child greeted it and waited.",
        tags={"patience", "moray"},
    ),
    "share_sea_grapes": Approach(
        id="share_sea_grapes",
        label="share sea grapes",
        sense=3,
        calm_score=3,
        intro="set a little bunch of sea grapes beside the opening as a peace-offering",
        speak='"These are for you, keeper of the cleft. May I have back what the tide carried in?"',
        help_line="The moray tasted the sea grapes, blinked its bright bead eyes, and then pushed the treasure out as if it understood every word.",
        qa_help="The moray accepted the sea grapes and then pushed the lost thing back out.",
        tags={"gift", "food", "moray"},
    ),
    "sing_softly": Approach(
        id="sing_softly",
        label="sing softly",
        sense=2,
        calm_score=2,
        intro="lifted her chin and sang the small tide-song her elder used to sing",
        speak='"Sleep, little current. Rest, little stone. No one here comes to steal a home."',
        help_line="The notes drifted through the water like silver thread. The moray uncoiled, calm as sea grass, and with one slow turn of its head sent the treasure rolling into view.",
        qa_help="The soft song calmed the moray, and it rolled the lost thing back into view.",
        tags={"song", "moray"},
    ),
    "hook_it_out": Approach(
        id="hook_it_out",
        label="hook it out",
        sense=1,
        calm_score=0,
        intro="raised a hook of driftbone to yank the treasure out in one quick jerk",
        speak='"I will be fast,"',
        help_line="The moray snapped its jaws in fright and the treasure vanished deeper into the crack.",
        qa_help="The rude reach frightened the moray and made the treasure slip farther in.",
        tags={"rude", "hook"},
    ),
}

GIRL_NAMES = ["Coral", "Mira", "Lina", "Pearl", "Neri", "Sela", "Tavi", "Noma"]
BOY_NAMES = ["Finn", "Tide", "Rowan", "Maro", "Kelp", "Ivo", "Nilo", "Bram"]


def item_fits(place: Place, item: LostItem) -> bool:
    return item.size <= place.slot_size


def tool_can_see(place: Place, tool: LightTool) -> bool:
    return tool.light >= place.darkness


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if item_fits(place, item) and tool_can_see(place, tool):
                    combos.append((place_id, item_id, tool_id))
    return combos


def explain_rejection(place: Place, item: LostItem, tool: LightTool) -> str:
    if not item_fits(place, item):
        return (
            f"(No story: {item.phrase} is too large to have slipped into {place.opening}. "
            f"Pick a smaller lost thing or a wider hiding place.)"
        )
    if not tool_can_see(place, tool):
        return (
            f"(No story: {tool.label} is too dim for {place.label}. "
            f"The child must be able to see into the dark place at least a little.)"
        )
    return "(No story: this combination does not make a plausible lost-treasure problem.)"


def explain_approach(aid: str) -> str:
    approach = APPROACHES[aid]
    better = ", ".join(sorted(a.id for a in sensible_approaches()))
    return (
        f"(Refusing approach '{aid}': it is too rude and foolish for this world "
        f"(sense={approach.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if params.approach == "share_sea_grapes":
        return "gifted"
    if params.approach == "sing_softly":
        return "sung"
    return "waited"


def introduce(world: World, hero: Entity, friend: Entity, item: LostItem) -> None:
    world.say(
        f"In the green-glass kingdom under the sea, where bubbles climbed like pearls "
        f"and the moon wrote silver ladders on the waves above, there lived a young reef-child named {hero.id}."
    )
    world.say(
        f"{hero.id} and {friend.id} spent their mornings among shells and sea flowers, "
        f"and on that day {hero.id} wore {item.phrase} as proudly as any princess in an old tale."
    )


def lose_treasure(world: World, hero: Entity, friend: Entity, place: Place, item: LostItem) -> None:
    treasure = world.get("item")
    treasure.meters["lost"] = 1.0
    world.say(
        f"They raced one another past {place.around} until a playful swirl of water tugged at {hero.id}. "
        f"Off slipped the {item.label}, and down it twirled into {place.opening} at {place.label}."
    )
    world.say(place.dark_line)
    world.say(
        f"Then two bright eyes opened inside the dark. A moray lived there, striped as old ribbon and still as a secret."
    )


def quick_idea(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["hurry"] += 1
    world.say(
        f'{friend.id} leaned close and whispered, "Be quick. Reach in before the moray can curl around it."'
    )


def flashback(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"But just as {hero.id} drew a breath, a memory opened in {hero.pronoun('possessive')} mind like a shell."
    )
    world.say(
        f"Last spring, {elder.label_word} had found a young moray tangled in a drifting fishing thread. "
        f"Instead of calling it a monster, {elder.pronoun()} had cut the thread away and let the creature slide back into the rocks."
    )
    world.say(
        f'"Remember," {elder.pronoun()} had said then, "a moray shows sharp teeth when it is frightened. '
        f'Be gentle first, and the sea may answer gently too."'
    )


def bring_light(world: World, hero: Entity, tool: LightTool, place: Place, item: LostItem) -> None:
    hero.meters["holding_light"] = 1.0
    world.say(
        f"{hero.id} lifted {tool.phrase}. {tool.glow_line} In that patient light, {hero.pronoun('possessive')} {item.label} could be seen caught near the front of the crack."
    )


def choose_kindness(world: World, hero: Entity, approach: Approach) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"So {hero.id} {approach.intro}. Then {hero.pronoun()} said, {approach.speak}"
    )


def moray_helps(world: World, hero: Entity, moray: Entity, approach: Approach, item: LostItem) -> None:
    moray.meters["calm"] += 1
    propagate(world, narrate=False)
    world.say(approach.help_line)
    world.say(
        f"{hero.id} gathered up the {item.label} with slow careful fingers and bowed to the moray instead of splashing away."
    )


def ending(world: World, hero: Entity, friend: Entity, item: LostItem) -> None:
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f'{friend.id} stared, then smiled a little shyly. "I thought the moray would only bite," {friend.pronoun()} said.'
    )
    world.say(
        f'"Perhaps when we are scared, we all look fiercer than we mean to," {hero.id} answered.'
    )
    world.say(
        f"And they swam home more slowly than before, {item.ending_image}, while behind them the moray watched from its doorway like an old keeper of wise dark places."
    )


def tell(
    place: Place,
    item_cfg: LostItem,
    tool: LightTool,
    approach: Approach,
    hero_name: str = "Coral",
    hero_type: str = "mergirl",
    friend_name: str = "Finn",
    friend_type: str = "merboy",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, role="friend", label=friend_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, role="elder", label=elder_type))
    moray = world.add(Entity(id="moray", kind="character", type="moray", role="guardian", label="the moray"))
    item = world.add(Entity(id="item", kind="thing", type="treasure", role="item", label=item_cfg.label))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", role="place", label=place.label))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="light", role="tool", label=tool.label))

    place_ent.meters["darkness"] = float(place.darkness)
    place_ent.meters["current"] = float(place.current)
    tool_ent.meters["light"] = float(tool.light)
    item.meters["size"] = float(item_cfg.size)
    item.meters["sparkle"] = float(item_cfg.sparkle)
    moray.meters["calm"] = 0.0
    moray.meters["startled"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["memory"] = 0.0

    introduce(world, hero, friend, item_cfg)
    lose_treasure(world, hero, friend, place, item_cfg)

    world.para()
    quick_idea(world, hero, friend)
    flashback(world, hero, elder)
    bring_light(world, hero, tool, place, item_cfg)

    world.para()
    choose_kindness(world, hero, approach)
    moray_helps(world, hero, moray, approach, item_cfg)

    world.para()
    ending(world, hero, friend, item_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        moray=moray,
        item_cfg=item_cfg,
        place_cfg=place,
        tool_cfg=tool,
        approach_cfg=approach,
        flashback_used=hero.memes["memory"] >= THRESHOLD,
        item_found=item.meters["found"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                item=item_cfg.id,
                tool=tool.id,
                approach=approach.id,
                hero=hero_name,
                hero_type=hero_type,
                friend=friend_name,
                friend_type=friend_type,
                elder=elder_type,
            )
        ),
    )
    return world


KNOWLEDGE = {
    "moray": [
        (
            "What is a moray?",
            "A moray is a kind of eel that lives in holes and cracks in reefs. It has a long body and sharp teeth, but it usually wants a safe home more than a fight.",
        )
    ],
    "reef": [
        (
            "What is a reef?",
            "A reef is a place under the sea full of rocks or coral where many sea creatures live. It has lots of little hiding places and narrow cracks.",
        )
    ],
    "light": [
        (
            "Why do you need light in a dark crack under the sea?",
            "You need light so you can see where things are and keep your hands away from danger. Good light helps you move slowly instead of grabbing in a rush.",
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting calmly instead of trying to get everything at once. Sometimes patience helps a scared creature feel safe.",
        )
    ],
    "gift": [
        (
            "What is a peace-offering?",
            "A peace-offering is a small gift that shows you are coming kindly, not to fight. It can help begin a gentle meeting.",
        )
    ],
    "song": [
        (
            "Why can a soft song help in a story?",
            "A soft song can slow the mood and make everyone calmer. In fairy tales, songs often show gentleness and courage together.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something that happened earlier. That memory helps the character understand what to do now.",
        )
    ],
    "treasure": [
        (
            "Why do small treasures slip into cracks so easily?",
            "Small shiny things can slide and roll when water moves them. Once they reach a narrow crack, they can be hard to reach safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["moray", "reef", "light", "patience", "gift", "song", "flashback", "treasure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    approach = f["approach_cfg"]
    hero = f["hero"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "moray" and uses a flashback.',
        f"Tell a gentle undersea fairy tale where {hero.label} loses {item.phrase} near {place.label}, remembers an elder's lesson, and uses {tool.label} to choose a kinder way.",
        f"Write a small story with a flashback where a child meets a moray in a dark reef place and solves the trouble by {approach.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    approach = f["approach_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young child of the reef, and {friend.label}, who was with {hero.pronoun('object')} when the trouble began. A moray in {place.label} becomes important too.",
        ),
        (
            f"What went wrong at {place.label}?",
            f"{hero.label}'s {item.label} slipped away and twirled into {place.opening}. That mattered because a moray was living there, so reaching in carelessly could frighten it.",
        ),
        (
            "What is the flashback about?",
            f"The flashback is about {elder.label_word} freeing a young moray from fishing thread and teaching that frightened creatures need gentleness first. That memory changes what {hero.label} does in the present.",
        ),
        (
            f"Why did {hero.label} use {tool.label}?",
            f"{hero.label} used {tool.label} to see into the dark crack instead of grabbing blindly. The light made the lost thing visible and helped {hero.pronoun('object')} move slowly and safely.",
        ),
        (
            f"How did {hero.label} get the {item.label} back?",
            f"{hero.label} chose to {approach.label}. {approach.qa_help} Because {hero.pronoun()} acted kindly after remembering the flashback, the danger turned into trust.",
        ),
        (
            "How did the story end?",
            f"It ended with the children swimming home gently instead of racing away in fear. The last image shows that something changed: {item.ending_image}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    approach = f["approach_cfg"]
    tags = {"moray", "reef", "light", "flashback", "treasure", "patience"}
    if "gift" in approach.tags or "food" in approach.tags:
        tags.add("gift")
    if "song" in approach.tags:
        tags.add("song")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="whisper_cleft",
        item="moon_ribbon",
        tool="glow_pearl",
        approach="greet_and_wait",
        hero="Coral",
        hero_type="mergirl",
        friend="Finn",
        friend_type="merboy",
        elder="grandmother",
    ),
    StoryParams(
        place="shell_arch",
        item="pearl_crown",
        tool="glow_pearl",
        approach="share_sea_grapes",
        hero="Mira",
        hero_type="mergirl",
        friend="Tide",
        friend_type="merboy",
        elder="grandmother",
    ),
    StoryParams(
        place="midnight_grotto",
        item="star_key",
        tool="lantern_kelp",
        approach="sing_softly",
        hero="Lina",
        hero_type="mergirl",
        friend="Rowan",
        friend_type="merboy",
        elder="grandmother",
    ),
    StoryParams(
        place="midnight_grotto",
        item="pearl_crown",
        tool="lantern_kelp",
        approach="share_sea_grapes",
        hero="Pearl",
        hero_type="mergirl",
        friend="Maro",
        friend_type="merboy",
        elder="grandmother",
    ),
]


ASP_RULES = r"""
fits(I,P) :- item(I), place(P), item_size(I,S), slot_size(P,K), S <= K.
visible(P,T) :- place(P), tool(T), darkness(P,D), light(T,L), L >= D.
valid(P,I,T) :- fits(I,P), visible(P,T).

sensible(A) :- approach(A), sense(A,S), sense_min(M), S >= M.

outcome(gifted) :- chosen_approach(share_sea_grapes), sensible(share_sea_grapes), flashback.
outcome(sung)   :- chosen_approach(sing_softly), sensible(sing_softly), flashback.
outcome(waited) :- chosen_approach(greet_and_wait), sensible(greet_and_wait), flashback.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("slot_size", pid, place.slot_size))
        lines.append(asp.fact("darkness", pid, place.darkness))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_size", iid, item.size))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("light", tid, tool.light))
    for aid, approach in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("sense", aid, approach.sense))
        lines.append(asp.fact("calm_score", aid, approach.calm_score))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_approach", params.approach),
            asp.fact("flashback"),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {a.id for a in sensible_approaches()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible approaches match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible approaches: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a reef child, a moray, and a flashback-guided choice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["mergirl", "merboy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["mergirl", "merboy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, kind: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if kind == "mergirl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.tool:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not (item_fits(place, item) and tool_can_see(place, tool)):
            raise StoryError(explain_rejection(place, item, tool))
    if args.approach and APPROACHES[args.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach(args.approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, tool_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    hero_type = args.hero_type or rng.choice(["mergirl", "merboy"])
    friend_type = args.friend_type or ("merboy" if hero_type == "mergirl" else "mergirl")
    hero = args.hero or _pick_name(rng, hero_type)
    friend = args.friend or _pick_name(rng, friend_type, avoid=hero)
    elder = args.elder or "grandmother"

    return StoryParams(
        place=place_id,
        item=item_id,
        tool=tool_id,
        approach=approach_id,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    approach = APPROACHES[params.approach]

    if not item_fits(place, item) or not tool_can_see(place, tool):
        raise StoryError(explain_rejection(place, item, tool))
    if approach.sense < SENSE_MIN:
        raise StoryError(explain_approach(params.approach))

    world = tell(
        place=place,
        item_cfg=item,
        tool=tool,
        approach=approach,
        hero_name=params.hero,
        hero_type=params.hero_type,
        friend_name=params.friend,
        friend_type=params.friend_type,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        approaches = asp_sensible()
        print(f"sensible approaches: {', '.join(approaches)}\n")
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place, item, tool in combos:
            print(f"  {place:16} {item:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.item} at {p.place} with {p.tool} ({p.approach})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
