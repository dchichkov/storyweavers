#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py
================================================================

A standalone story world for a tiny ghost-story quest: a child hears of a sad
specter in an old place, chooses whether to be brave enough to investigate, and
finds the missing keepsake that lets the ghost rest. The story is built from a
small simulated world with physical meters and emotional memes, a
constraint-checked reasonableness gate, and an inline ASP twin for verification.

The design aim is not "any spooky paragraph with nouns swapped", but one small,
plausible domain:

- a haunted place with a real reason to feel eerie
- a ghostly clue that can honestly describe what is wrong
- a helper tool that makes searching possible in the dark
- a quest target that can truly be lost in that place
- a calm resolution where the specter is no longer lonely

Run it
------
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --haunt attic --lost_key music_box_key
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --haunt pond --lost_key letter
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --trace --seed 77
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --asp
    python storyworlds/worlds/gpt-5.4/specter_describe_quest_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Haunt:
    id: str
    label: str
    phrase: str
    dark_spot: str
    hiding_spot: str
    search_verb: str
    eerie_detail: str
    indoors: bool = True
    damp: bool = False
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
class LostKey:
    id: str
    label: str
    phrase: str
    owner_story: str
    use_story: str
    tiny: bool = True
    harmed_by_water: bool = False
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
class Guide:
    id: str
    title: str
    opening: str
    request: str
    peace_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    gives_light: bool = False
    reaches_cracks: bool = False
    water_safe: bool = False
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
class Temper:
    id: str
    label: str
    kindness: int
    scare: int
    opening_line: str
    after_help: str
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


def _r_fear(world: World) -> list[str]:
    hero = world.get("hero")
    specter = world.get("specter")
    haunt = world.get("haunt")
    if specter.meters["manifest"] < THRESHOLD:
        return []
    sig = ("fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += specter.attrs.get("scare", 1)
    haunt.meters["chill"] += 1
    return ["__fear__"]


def _r_clue(world: World) -> list[str]:
    specter = world.get("specter")
    if specter.meters["heard"] < THRESHOLD:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    specter.memes["hope"] += 1
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    return ["__clue__"]


def _r_search_success(world: World) -> list[str]:
    hero = world.get("hero")
    specter = world.get("specter")
    item = world.get("item")
    if hero.meters["searched"] < THRESHOLD:
        return []
    if not world.facts.get("tool_works", False):
        return []
    sig = ("found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["found"] += 1
    specter.memes["hope"] += 1
    hero.memes["confidence"] += 1
    return ["__found__"]


def _r_peace(world: World) -> list[str]:
    specter = world.get("specter")
    item = world.get("item")
    if specter.meters["reunited"] < THRESHOLD or item.meters["found"] < THRESHOLD:
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    specter.meters["rest"] += 1
    specter.memes["lonely"] = 0.0
    specter.memes["gratitude"] += 1
    hero = world.get("hero")
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="clue", tag="quest", apply=_r_clue),
    Rule(name="search_success", tag="physical", apply=_r_search_success),
    Rule(name="peace", tag="resolution", apply=_r_peace),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tool_can_find(tool: Tool, haunt: Haunt, lost_key: LostKey) -> bool:
    if haunt.damp and lost_key.harmed_by_water:
        return tool.water_safe
    if lost_key.tiny:
        return tool.gives_light or tool.reaches_cracks
    return True


def can_comfort(temper: Temper) -> bool:
    return temper.kindness >= KINDNESS_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for haunt_id, haunt in HAUNTS.items():
        for lost_id, lost in LOST_KEYS.items():
            for tool_id, tool in TOOLS.items():
                if not tool_can_find(tool, haunt, lost):
                    continue
                for temper_id, temper in TEMPERS.items():
                    if can_comfort(temper):
                        combos.append((haunt_id, lost_id, tool_id, temper_id))
    return combos


def explain_combo_rejection(haunt: Haunt, lost_key: LostKey, tool: Tool, temper: Temper) -> str:
    if not can_comfort(temper):
        return (
            f"(No story: the specter's temper is too harsh for this tiny ghost story. "
            f"A child can meet something eerie, but the spirit must still be gentle "
            f"enough to ask for help and accept kindness.)"
        )
    if haunt.damp and lost_key.harmed_by_water and not tool.water_safe:
        return (
            f"(No story: {lost_key.phrase} would have to be searched for in wet water, "
            f"so the helper tool must be safe to use there. Try a water-safe tool.)"
        )
    if lost_key.tiny and not (tool.gives_light or tool.reaches_cracks):
        return (
            f"(No story: {lost_key.phrase} is too easy to miss in {haunt.phrase}. "
            f"The tool has to help the child see into dark corners or narrow cracks.)"
        )
    return "(No story: this combination does not make a reasonable quest.)"


def predict_search(haunt: Haunt, lost_key: LostKey, tool: Tool) -> dict:
    sim = World()
    hero = sim.add(Entity(id="hero", kind="character", type="girl", role="hero"))
    specter = sim.add(Entity(id="specter", kind="character", type="ghost", role="specter"))
    item = sim.add(Entity(id="item", type="keepsake", label=lost_key.label))
    sim.add(Entity(id="haunt", type="place", label=haunt.label))
    sim.facts["tool_works"] = tool_can_find(tool, haunt, lost_key)
    hero.meters["searched"] += 1
    specter.meters["reunited"] += 1
    propagate(sim, narrate=False)
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "rest": specter.meters["rest"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, elder: Entity, haunt: Haunt) -> None:
    hero.memes["calm"] += 1
    world.say(
        f"On a windy evening, {hero.id} walked with {hero.pronoun('possessive')} "
        f"{elder.label_word} past {haunt.phrase}. {haunt.eerie_detail}"
    )
    world.say(
        f"People in the lane liked to whisper that a specter drifted there after dark, "
        f"but no one stayed long enough to describe what it wanted."
    )


def rumor(world: World, elder: Entity, guide: Guide, haunt: Haunt) -> None:
    world.say(
        f'{elder.label_word.capitalize()} squeezed {elder.pronoun("possessive")} lantern handle and said, '
        f'"Long ago, {guide.owner_story} in {haunt.label}. {guide.opening}"'
    )


def appear(world: World, hero: Entity, specter: Entity, temper: Temper, haunt: Haunt) -> None:
    specter.meters["manifest"] += 1
    specter.attrs["scare"] = temper.scare
    specter.memes["lonely"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As they reached {haunt.dark_spot}, a pale shape rose out of the shadows. "
        f"The specter shimmered like moonlight on glass."
    )
    world.say(
        f'{temper.opening_line} For a moment, {hero.id} could only listen to the creak of the old boards and the tiny thump of {hero.pronoun("possessive")} heart.'
    )


def choose_listen(world: World, hero: Entity, temper: Temper) -> bool:
    courage = hero.memes["bravery"] + hero.memes["kindness"]
    return temper.scare < courage + 1


def listen(world: World, hero: Entity, specter: Entity, guide: Guide, lost_key: LostKey) -> None:
    specter.meters["heard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} swallowed, stepped closer, and said, "
        f'"If you can describe what is wrong, I will try to help."'
    )
    world.say(
        f'The specter bowed its dim head. "{guide.request} I cannot rest without {lost_key.phrase}," it whispered.'
    )


def flee(world: World, hero: Entity, elder: Entity, specter: Entity, haunt: Haunt) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} grabbed {elder.label_word}'s sleeve and hurried back down the path. "
        f"The wind moaned through {haunt.label}, and nobody learned what the specter needed."
    )
    world.say(
        f"That night, {hero.id} lay awake wishing {hero.pronoun()} had been brave enough to listen."
    )


def quest_plan(world: World, hero: Entity, elder: Entity, tool: Tool, haunt: Haunt) -> None:
    world.say(
        f'{elder.label_word.capitalize()} did not laugh or scold. "{tool.use_line}," '
        f'{elder.pronoun()} said, handing {hero.pronoun("object")} {tool.phrase}.'
    )
    world.say(
        f"Together they began a quiet quest through {haunt.hiding_spot}, looking carefully instead of running away."
    )


def search(world: World, hero: Entity, haunt: Haunt, lost_key: LostKey, tool: Tool) -> None:
    hero.meters["searched"] += 1
    world.facts["tool_works"] = tool_can_find(tool, haunt, lost_key)
    propagate(world, narrate=False)
    if world.facts["tool_works"]:
        world.say(
            f"{hero.id} used the {tool.label} to search {haunt.hiding_spot}. At last, something small gave a soft glint in the dark."
        )
    else:
        world.say(
            f"{hero.id} searched and searched, but the {tool.label} was no help in that place. The dark corners kept their secret."
        )


def find_item(world: World, hero: Entity, lost_key: LostKey) -> None:
    if world.get("item").meters["found"] >= THRESHOLD:
        world.say(
            f"It was {lost_key.phrase}. {hero.id} lifted it gently, as if even a tiny keepsake could remember being missed."
        )


def return_item(world: World, hero: Entity, specter: Entity, guide: Guide, lost_key: LostKey) -> None:
    if world.get("item").meters["found"] < THRESHOLD:
        return
    specter.meters["reunited"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} held out {lost_key.phrase}. "Is this yours?" {hero.pronoun()} asked.'
    )
    world.say(
        f'The specter touched it with a shining hand. "{guide.after_help}" it sighed.'
    )


def peace(world: World, guide: Guide) -> None:
    specter = world.get("specter")
    if specter.meters["rest"] >= THRESHOLD:
        world.say(
            f"{guide.peace_image} The room no longer felt haunted. It felt remembered."
        )


def afterglow(world: World, hero: Entity, elder: Entity, tool: Tool) -> None:
    specter = world.get("specter")
    if specter.meters["rest"] >= THRESHOLD:
        world.say(
            f"On the walk home, {hero.id} was still quiet, but not from fear. {hero.pronoun().capitalize()} had learned that some ghost stories end with kindness."
        )
        world.say(
            f'{elder.label_word.capitalize()} smiled and said, "Now when people ask about the specter, you can describe the truth."'
        )
    else:
        world.say(
            f"On the walk home, the night seemed longer than before, and the old place kept its sorrow."
        )


def tell(
    haunt: Haunt,
    lost_key: LostKey,
    guide: Guide,
    tool: Tool,
    temper: Temper,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "mother",
    trait: str = "gentle",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the grown-up",
        role="elder",
    ))
    specter = world.add(Entity(
        id="specter",
        kind="character",
        type="ghost",
        label="specter",
        role="specter",
        attrs={"scare": temper.scare},
    ))
    item = world.add(Entity(
        id="item",
        type="keepsake",
        label=lost_key.label,
        attrs={"tiny": lost_key.tiny, "harmed_by_water": lost_key.harmed_by_water},
    ))
    place = world.add(Entity(
        id="haunt",
        type="place",
        label=haunt.label,
        attrs={"damp": haunt.damp},
    ))
    helper = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={
            "gives_light": tool.gives_light,
            "reaches_cracks": tool.reaches_cracks,
            "water_safe": tool.water_safe,
        },
    ))

    hero.memes["bravery"] = 4.0 if trait in {"brave", "curious"} else 3.0
    hero.memes["kindness"] = 4.0 if trait in {"gentle", "kind"} else 2.0
    hero.memes["fear"] = 0.0
    specter.memes["lonely"] = 1.0
    world.facts["tool_works"] = tool_can_find(tool, haunt, lost_key)

    opening(world, hero, elder, haunt)
    rumor(world, elder, guide, haunt)

    world.para()
    appear(world, hero, specter, temper, haunt)

    if not choose_listen(world, hero, temper):
        flee(world, hero, elder, specter, haunt)
        outcome = "unresolved"
    else:
        listen(world, hero, specter, guide, lost_key)
        world.para()
        quest_plan(world, hero, elder, tool, haunt)
        search(world, hero, haunt, lost_key, tool)
        find_item(world, hero, lost_key)

        if world.get("item").meters["found"] >= THRESHOLD:
            world.para()
            return_item(world, hero, specter, guide, lost_key)
            peace(world, guide)
            outcome = "rest"
        else:
            world.para()
            world.say(
                f"They had to leave before dawn without {lost_key.phrase}. The specter faded with a sad nod, and the quest was not finished."
            )
            outcome = "search_failed"

    world.para()
    afterglow(world, hero, elder, tool)

    world.facts.update(
        hero=hero,
        elder=elder,
        specter=specter,
        haunt_cfg=haunt,
        lost_cfg=lost_key,
        guide_cfg=guide,
        tool_cfg=tool,
        temper_cfg=temper,
        item=item,
        helper=helper,
        chose_listen=outcome != "unresolved",
        found=item.meters["found"] >= THRESHOLD,
        rest=specter.meters["rest"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


HAUNTS = {
    "attic": Haunt(
        id="attic",
        label="the old attic",
        phrase="the old attic above Aunt May's house",
        dark_spot="the slanting rafters",
        hiding_spot="between dusty trunks and the farthest beams",
        search_verb="crawl",
        eerie_detail="Rain tapped the roof, and every hanging cobweb swayed as if someone had just brushed past.",
        indoors=True,
        damp=False,
        tags={"attic", "dark"},
    ),
    "cemetery_gate": Haunt(
        id="cemetery_gate",
        label="the cemetery gate",
        phrase="the mossy gate of the village cemetery",
        dark_spot="the broken iron arch",
        hiding_spot="among wet stones and ivy",
        search_verb="kneel",
        eerie_detail="Mist gathered low over the grass until the path looked like a silver ribbon floating in the dark.",
        indoors=False,
        damp=False,
        tags={"cemetery", "mist"},
    ),
    "pond": Haunt(
        id="pond",
        label="the willow pond",
        phrase="the willow pond behind the orchard",
        dark_spot="the black water under the drooping branches",
        hiding_spot="along the muddy edge and under the roots",
        search_verb="reach",
        eerie_detail="The pond barely moved, yet pale rings kept widening across it as if invisible fingers touched the water.",
        indoors=False,
        damp=True,
        tags={"pond", "water"},
    ),
}

LOST_KEYS = {
    "music_box_key": LostKey(
        id="music_box_key",
        label="music-box key",
        phrase="the tiny music-box key",
        owner_story="a lonely child once hid a silver music box",
        use_story="it could wake a sweet tune",
        tiny=True,
        harmed_by_water=False,
        tags={"key", "music_box"},
    ),
    "locket": LostKey(
        id="locket",
        label="locket",
        phrase="the little heart-shaped locket",
        owner_story="a bride once carried a little locket close to her heart",
        use_story="it held a painted face inside",
        tiny=True,
        harmed_by_water=False,
        tags={"locket", "memory"},
    ),
    "letter": LostKey(
        id="letter",
        label="letter",
        phrase="the folded letter",
        owner_story="a young sailor once left behind one last letter",
        use_story="it carried goodbye words never read",
        tiny=False,
        harmed_by_water=True,
        tags={"letter", "memory"},
    ),
}

GUIDES = {
    "child": Guide(
        id="child",
        title="child",
        opening="Since then, a small ghost has searched for the thing it lost.",
        request="Please help me finish my old errand",
        peace_image="The pale shape thinned into a soft pearl light and drifted upward like the last bit of fog at sunrise.",
        tags={"child_ghost"},
    ),
    "bride": Guide(
        id="bride",
        title="bride",
        opening="Since then, a quiet bride-like spirit has wandered there, never able to stop looking behind her.",
        request="Please help me find what my hands were holding",
        peace_image="The specter smiled, and its veil of mist folded into moonlight that slipped away between the trees.",
        tags={"bride_ghost"},
    ),
    "sailor": Guide(
        id="sailor",
        title="sailor",
        opening="Since then, a homesick spirit has come back whenever the wind sounds like distant waves.",
        request="Please help me deliver what I could not keep safe",
        peace_image="The ghost's outline brightened once, like a lantern seen far away at sea, and then it was gone.",
        tags={"sailor_ghost"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a warm brass lantern",
        use_line="Take this lantern and keep close to me",
        gives_light=True,
        reaches_cracks=False,
        water_safe=False,
        tags={"lantern", "light"},
    ),
    "mirror": Tool(
        id="mirror",
        label="hand mirror",
        phrase="a little hand mirror",
        use_line="Use this mirror to catch moonlight in the tight places",
        gives_light=False,
        reaches_cracks=True,
        water_safe=False,
        tags={"mirror", "light"},
    ),
    "reed_hook": Tool(
        id="reed_hook",
        label="reed hook",
        phrase="a long reed hook",
        use_line="Use this hook to lift branches and stir the reeds",
        gives_light=False,
        reaches_cracks=True,
        water_safe=True,
        tags={"pond_tool"},
    ),
    "boat_lamp": Tool(
        id="boat_lamp",
        label="boat lamp",
        phrase="a glass-covered boat lamp",
        use_line="This boat lamp can shine even by the wet bank",
        gives_light=True,
        reaches_cracks=False,
        water_safe=True,
        tags={"lamp", "water_safe"},
    ),
}

TEMPERS = {
    "mournful": Temper(
        id="mournful",
        label="mournful",
        kindness=3,
        scare=2,
        opening_line='"Do not run," said a voice as soft as falling dust.',
        after_help="Thank you. Now the waiting can end",
        tags={"gentle"},
    ),
    "wistful": Temper(
        id="wistful",
        label="wistful",
        kindness=3,
        scare=1,
        opening_line='"Please stay," sighed the specter, not angrily but as if it had been alone for a very long time.',
        after_help="You have given back more than an object. You have given back peace",
        tags={"gentle"},
    ),
    "shrill": Temper(
        id="shrill",
        label="shrill",
        kindness=1,
        scare=4,
        opening_line='"Mine!" cried the specter in a sharp echo that rattled every window.',
        after_help="At last",
        tags={"harsh"},
    ),
}

HERO_NAMES = ["Mira", "Nell", "Ruby", "Ivy", "Jonah", "Eli", "Tess", "Ada", "Finn", "Lena"]
TRAITS = ["gentle", "curious", "brave", "kind", "quiet"]
PARENTS = ["mother", "father"]


@dataclass
class StoryParams:
    haunt: str
    lost_key: str
    guide: str
    tool: str
    temper: str
    hero_name: str
    hero_gender: str
    elder: str
    trait: str
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
    "specter": [(
        "What is a specter?",
        "A specter is another word for a ghost, especially a ghost that looks pale or shadowy. In stories, a specter often seems scary at first but may really be sad or lonely."
    )],
    "ghost_story": [(
        "What makes a story a ghost story?",
        "A ghost story usually has a haunted place, an eerie feeling, and a spirit or mystery from the past. It often begins with fear and ends when someone learns the truth."
    )],
    "attic": [(
        "Why can an attic feel spooky?",
        "An attic is often dark, dusty, and full of old things, so small sounds can seem much bigger there. That makes it a good place for secrets in a ghost story."
    )],
    "cemetery": [(
        "Why do ghost stories use cemeteries?",
        "Cemeteries remind people of the past and of people who are gone, so they can feel quiet and mysterious. In stories, that quietness makes every sound feel important."
    )],
    "pond": [(
        "Why is a pond spooky at night?",
        "Water at night can hide things and reflect odd shapes, so it is easy to imagine shadows moving there. That makes a pond feel mysterious in a ghost story."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern makes a steady light you can carry into dark places. In stories, that light often helps a character search carefully instead of stumbling in fear."
    )],
    "mirror": [(
        "How can a mirror help in the dark?",
        "A mirror can catch and bounce light into small spaces. That makes it useful for peeking into corners without putting your whole hand there."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a journey or search for something important. In stories, the hero usually has to be brave, keep going, and solve a problem before the quest is done."
    )],
    "letter": [(
        "Why can a lost letter matter in a story?",
        "A letter can hold words that someone needed to say. Finding it can solve a mystery or help feelings that were left unfinished."
    )],
    "locket": [(
        "What is a locket?",
        "A locket is a small piece of jewelry that opens and often holds a picture or tiny memory inside. That makes it a strong keepsake in a story."
    )],
    "music_box": [(
        "What is a music box?",
        "A music box is a little box that plays a tune when it is wound up. Because it keeps a favorite sound inside, it can feel special and full of memory."
    )],
}
KNOWLEDGE_ORDER = [
    "specter",
    "ghost_story",
    "quest",
    "attic",
    "cemetery",
    "pond",
    "lantern",
    "mirror",
    "letter",
    "locket",
    "music_box",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    haunt = f["haunt_cfg"]
    lost_key = f["lost_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "rest":
        return [
            f'Write a child-friendly ghost story that includes the words "specter" and "describe", where a child goes on a quest in {haunt.label} to find {lost_key.phrase}.',
            f"Tell a spooky-but-gentle quest story in which a ghost can describe its problem, a child listens instead of running away, and {tool.phrase} helps solve the mystery.",
            f"Write a ghost story with an eerie beginning, a search through {haunt.phrase}, and a peaceful ending after a specter is helped.",
        ]
    if outcome == "search_failed":
        return [
            f'Write a ghost story that includes "specter" and "describe", where a child bravely begins a quest in {haunt.label} but cannot finish it that night.',
            f"Tell a story where a ghost describes what it lost, the child searches with {tool.phrase}, but the mystery remains unsolved by dawn.",
            f"Write a spooky, sad quest tale about trying to help a specter and not quite succeeding yet.",
        ]
    return [
        f'Write a ghost story that uses the words "specter" and "describe", where a child meets a spirit in {haunt.label} but is too frightened to hear the whole quest.',
        "Tell a story where fear wins at first, and a child goes home still wondering what the ghost wanted.",
        "Write a gentle ghost story about a mystery left unsolved because no one stayed to listen.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    haunt = f["haunt_cfg"]
    lost_key = f["lost_cfg"]
    tool = f["tool_cfg"]
    specter = f["specter"]
    guide = f["guide_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} {elder.label_word}, and a lonely specter in {haunt.label}. The story follows them through a small ghostly quest."
        ),
        (
            "Where did the story happen?",
            f"It happened at {haunt.phrase}. The place felt eerie because {haunt.eerie_detail.lower()}"
        ),
        (
            "What did the specter want?",
            f"The specter wanted help finding {lost_key.phrase}. It could finally describe its trouble, so the child knew the ghost was sad, not just scary."
        ),
    ]
    if outcome == "unresolved":
        qa.append((
            f"Why did {hero.id} run away?",
            f"{hero.id} was frightened when the specter appeared and spoke out of the dark. The ghost felt too sudden and strange, so {hero.pronoun()} left before hearing the full request."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the mystery still unsolved. {hero.id} went home wishing {hero.pronoun()} had listened longer."
        ))
    elif outcome == "search_failed":
        qa.append((
            f"How did {hero.id} try to help the specter?",
            f"{hero.id} listened, started the quest, and searched with {tool.phrase}. That was brave, but the search still failed because the hiding place kept its secret."
        ))
        qa.append((
            "Did the ghost find peace?",
            f"No, not yet. The specter was grateful to be heard, but without {lost_key.phrase}, it could not fully rest."
        ))
    else:
        qa.append((
            f"How did {hero.id} find {lost_key.phrase}?",
            f"{hero.id} searched {haunt.hiding_spot} with {tool.phrase}. The tool helped make the hidden thing visible or reachable, which is why the quest succeeded."
        ))
        qa.append((
            "Why did the specter disappear at the end?",
            f"The specter disappeared because it was reunited with {lost_key.phrase} and could finally rest. Once the old problem was solved, the haunted place no longer had to hold it there."
        ))
        qa.append((
            f"What changed in {hero.id} by the end?",
            f"{hero.id} began the story afraid of the ghostly shape. By the end, {hero.pronoun()} understood that listening and kindness can change fear into courage."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"specter", "ghost_story", "quest"}
    haunt = f["haunt_cfg"]
    tool = f["tool_cfg"]
    lost_key = f["lost_cfg"]
    if "attic" in haunt.tags:
        tags.add("attic")
    if "cemetery" in haunt.tags:
        tags.add("cemetery")
    if "pond" in haunt.tags:
        tags.add("pond")
    if tool.id == "lantern" or tool.id == "boat_lamp":
        tags.add("lantern")
    if tool.id == "mirror":
        tags.add("mirror")
    if lost_key.id == "letter":
        tags.add("letter")
    if lost_key.id == "locket":
        tags.add("locket")
    if lost_key.id == "music_box_key":
        tags.add("music_box")
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
        shown_attrs = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k in {'tool_works', 'outcome', 'found', 'rest', 'chose_listen'}} }")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        haunt="attic",
        lost_key="music_box_key",
        guide="child",
        tool="lantern",
        temper="wistful",
        hero_name="Mira",
        hero_gender="girl",
        elder="mother",
        trait="gentle",
    ),
    StoryParams(
        haunt="cemetery_gate",
        lost_key="locket",
        guide="bride",
        tool="mirror",
        temper="mournful",
        hero_name="Finn",
        hero_gender="boy",
        elder="father",
        trait="curious",
    ),
    StoryParams(
        haunt="pond",
        lost_key="letter",
        guide="sailor",
        tool="boat_lamp",
        temper="wistful",
        hero_name="Nell",
        hero_gender="girl",
        elder="mother",
        trait="brave",
    ),
    StoryParams(
        haunt="attic",
        lost_key="music_box_key",
        guide="child",
        tool="mirror",
        temper="shrill",
        hero_name="Eli",
        hero_gender="boy",
        elder="father",
        trait="quiet",
    ),
    StoryParams(
        haunt="pond",
        lost_key="letter",
        guide="sailor",
        tool="lantern",
        temper="mournful",
        hero_name="Ruby",
        hero_gender="girl",
        elder="mother",
        trait="kind",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.haunt not in HAUNTS or params.lost_key not in LOST_KEYS or params.tool not in TOOLS or params.temper not in TEMPERS:
        return "invalid"
    haunt = HAUNTS[params.haunt]
    lost_key = LOST_KEYS[params.lost_key]
    tool = TOOLS[params.tool]
    temper = TEMPERS[params.temper]
    bravery = 4.0 if params.trait in {"brave", "curious"} else 3.0
    kindness = 4.0 if params.trait in {"gentle", "kind"} else 2.0
    if temper.scare >= bravery + kindness + 1:
        return "unresolved"
    return "rest" if tool_can_find(tool, haunt, lost_key) else "search_failed"


ASP_RULES = r"""
valid(H, L, T, P) :- haunt(H), lost_key(L), tool(T), temper(P), tool_works(H, L, T), kind_temper(P).

tool_works(H, L, T) :- tiny(L), gives_light(T).
tool_works(H, L, T) :- tiny(L), reaches_cracks(T).
tool_works(H, L, T) :- not tiny(L), not damp(H).
tool_works(H, L, T) :- not tiny(L), damp(H), not harmed_by_water(L).
tool_works(H, L, T) :- damp(H), harmed_by_water(L), water_safe(T).

bravery(4) :- trait(curious).
bravery(4) :- trait(brave).
bravery(3) :- trait(T), T != curious, T != brave.

kindness(4) :- trait(gentle).
kindness(4) :- trait(kind).
kindness(2) :- trait(T), T != gentle, T != kind.

courage(C) :- bravery(B), kindness(K), C = B + K.
choose_listen :- courage(C), chosen_temper(P), scare(P, S), S < C + 1.
found :- chosen_haunt(H), chosen_lost(L), chosen_tool(T), tool_works(H, L, T).
outcome(unresolved) :- not choose_listen.
outcome(search_failed) :- choose_listen, not found.
outcome(rest) :- choose_listen, found.

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, haunt in HAUNTS.items():
        lines.append(asp.fact("haunt", hid))
        if haunt.damp:
            lines.append(asp.fact("damp", hid))
    for lid, lost in LOST_KEYS.items():
        lines.append(asp.fact("lost_key", lid))
        if lost.tiny:
            lines.append(asp.fact("tiny", lid))
        if lost.harmed_by_water:
            lines.append(asp.fact("harmed_by_water", lid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.gives_light:
            lines.append(asp.fact("gives_light", tid))
        if tool.reaches_cracks:
            lines.append(asp.fact("reaches_cracks", tid))
        if tool.water_safe:
            lines.append(asp.fact("water_safe", tid))
    for pid, temper in TEMPERS.items():
        lines.append(asp.fact("temper", pid))
        lines.append(asp.fact("scare", pid, temper.scare))
        if temper.kindness >= KINDNESS_MIN:
            lines.append(asp.fact("kind_temper", pid))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("trait_name", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_haunt", params.haunt),
        asp.fact("chosen_lost", params.lost_key),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_temper", params.temper),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
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
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches.append((params, py, cl))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")
        for params, py, cl in mismatches[:5]:
            print(" ", params, py, cl)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a specter, and a small ghostly quest."
    )
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--lost_key", choices=LOST_KEYS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--temper", choices=TEMPERS)
    ap.add_argument("--hero_name")
    ap.add_argument("--hero_gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.haunt and args.lost_key and args.tool and args.temper:
        haunt = HAUNTS[args.haunt]
        lost_key = LOST_KEYS[args.lost_key]
        tool = TOOLS[args.tool]
        temper = TEMPERS[args.temper]
        if not (tool_can_find(tool, haunt, lost_key) and can_comfort(temper)):
            raise StoryError(explain_combo_rejection(haunt, lost_key, tool, temper))

    combos = [
        c for c in valid_combos()
        if (args.haunt is None or c[0] == args.haunt)
        and (args.lost_key is None or c[1] == args.lost_key)
        and (args.tool is None or c[2] == args.tool)
        and (args.temper is None or c[3] == args.temper)
    ]
    if not combos:
        if args.haunt and args.lost_key and args.tool and args.temper:
            raise StoryError(
                explain_combo_rejection(
                    HAUNTS[args.haunt],
                    LOST_KEYS[args.lost_key],
                    TOOLS[args.tool],
                    TEMPERS[args.temper],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    haunt, lost_key, tool, temper = rng.choice(sorted(combos))
    guide = args.guide
    if guide is None:
        if lost_key == "music_box_key":
            guide = "child"
        elif lost_key == "locket":
            guide = "bride"
        else:
            guide = "sailor"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        haunt=haunt,
        lost_key=lost_key,
        guide=guide,
        tool=tool,
        temper=temper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        name for name, registry in [
            ("haunt", HAUNTS),
            ("lost_key", LOST_KEYS),
            ("guide", GUIDES),
            ("tool", TOOLS),
            ("temper", TEMPERS),
        ]
        if getattr(params, name) not in registry
    ]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")

    haunt = HAUNTS[params.haunt]
    lost_key = LOST_KEYS[params.lost_key]
    guide = GUIDES[params.guide]
    tool = TOOLS[params.tool]
    temper = TEMPERS[params.temper]

    if not (tool_can_find(tool, haunt, lost_key) and can_comfort(temper)):
        raise StoryError(explain_combo_rejection(haunt, lost_key, tool, temper))

    world = tell(
        haunt=haunt,
        lost_key=lost_key,
        guide=guide,
        tool=tool,
        temper=temper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (haunt, lost_key, tool, temper) combos:\n")
        for haunt, lost_key, tool, temper in combos:
            print(f"  {haunt:14} {lost_key:14} {tool:10} {temper}")
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
            header = f"### {p.hero_name}: {p.haunt}, {p.lost_key}, {p.tool}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
